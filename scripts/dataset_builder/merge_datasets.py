"""
Dataset merging module for the Crime Analysis project.

This module is the aggregation gate of the data pipeline. It reads validated
datasets from ``data/processed/`` and merges them into a single master dataset
saved to ``data/final/``.

Key capabilities:
    - Automatic discovery of datasets (CSV, Excel, JSON) in the processed
      directory.
    - Schema validation to detect missing columns, extra columns, and
      incorrect ordering across datasets.
    - Schema normalisation so all datasets share a consistent column set
      and order.
    - Vertical (append) merge with deduplication based on ``crime_id``.
    - Detailed merge statistics logged and persisted as a report.
    - Designed to support adding new datasets without changing existing
      logic—just place a validated file in ``data/processed/``.

Usage:
    python -m scripts.dataset_builder.merge_datasets

Or programmatically:
    from scripts.dataset_builder.merge_datasets import DatasetMerger
    merger = DatasetMerger()
    report = merger.run()
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import pandas as pd

# ---------------------------------------------------------------------------
# Logger
# ---------------------------------------------------------------------------

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SUPPORTED_EXTENSIONS: Tuple[str, ...] = (
    ".csv",
    ".xlsx",
    ".xls",
    ".json",
)
"""File extensions recognised as dataset inputs."""

DEFAULT_SCHEMA_ORDER: Tuple[str, ...] = (
    "crime_id",
    "crime_type",
    "date",
    "time",
    "area",
    "latitude",
    "longitude",
    "severity",
)
"""Canonical column ordering enforced during schema normalisation."""

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class MergeStatistics:
    """
    Statistics collected during a merge operation.

    Attributes:
        datasets_found: Number of datasets discovered in the processed
            directory.
        datasets_merged: Number of datasets that were successfully merged.
        rows_before: Total row count across all datasets before
            deduplication.
        rows_after: Row count in the master dataset after deduplication.
        duplicates_removed: Number of duplicate ``crime_id`` records
            removed.
        execution_time: Total wall-clock time of the merge run in seconds.
    """

    datasets_found: int = 0
    datasets_merged: int = 0
    rows_before: int = 0
    rows_after: int = 0
    duplicates_removed: int = 0
    execution_time: float = 0.0

    def to_dict(self) -> Dict[str, object]:
        """Return a JSON-serialisable dictionary."""
        return {
            "datasets_found": self.datasets_found,
            "datasets_merged": self.datasets_merged,
            "rows_before": self.rows_before,
            "rows_after": self.rows_after,
            "duplicates_removed": self.duplicates_removed,
            "execution_time_seconds": round(self.execution_time, 4),
        }


@dataclass
class SchemaIssue:
    """
    A single schema anomaly discovered during schema validation.

    Attributes:
        dataset_name: Name of the file where the issue was found.
        issue_type: One of ``missing_column``, ``extra_column``, or
            ``incorrect_order``.
        column: The column name involved.
        message: Human-readable description of the issue.
    """

    dataset_name: str
    issue_type: str
    column: str
    message: str

    def to_dict(self) -> Dict[str, object]:
        """Return a JSON-serialisable dictionary."""
        return {
            "dataset_name": self.dataset_name,
            "issue_type": self.issue_type,
            "column": self.column,
            "message": self.message,
        }


# ---------------------------------------------------------------------------
# Merger
# ---------------------------------------------------------------------------


class DatasetMerger:
    """
    Merges multiple validated crime datasets into a single master dataset.

    The merge workflow follows this sequence:

        1. Discover datasets in ``data/processed/``.
        2. Load each dataset using its file extension.
        3. Validate schemas for consistency across datasets.
        4. Normalise schemas to a canonical column set and order.
        5. Vertically merge all datasets.
        6. Deduplicate based on ``crime_id`` (keeping the first occurrence).
        7. Save the master dataset to ``data/final/``.
        8. Save a merge report to ``logs/``.
        9. Return merge statistics.

    The class is designed to be extensible: new datasets can be added by
    simply placing a validated file in the processed directory. No code
    changes are required.
    """

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------

    def __init__(
        self,
        processed_dir: Optional[str] = None,
        final_dir: Optional[str] = None,
        log_dir: Optional[str] = None,
        schema_order: Optional[Tuple[str, ...]] = None,
    ) -> None:
        """
        Initialise the DatasetMerger.

        Args:
            processed_dir: Directory containing processed datasets.
                Defaults to ``data/processed`` relative to the project root.
            final_dir: Directory where the master dataset will be saved.
                Defaults to ``data/final`` relative to the project root.
            log_dir: Directory for merge reports. Defaults to ``logs``
                relative to the project root.
            schema_order: Canonical column ordering for normalisation.
                Defaults to ``DEFAULT_SCHEMA_ORDER``.
        """
        # Resolve project root
        self._project_root: Path = Path(__file__).resolve().parents[2]

        # Directories
        if processed_dir:
            self._processed_dir = Path(processed_dir).resolve()
        else:
            self._processed_dir = self._project_root / "data" / "processed"

        if final_dir:
            self._final_dir = Path(final_dir).resolve()
        else:
            self._final_dir = self._project_root / "data" / "final"

        if log_dir:
            self._log_dir = Path(log_dir).resolve()
        else:
            self._log_dir = self._project_root / "logs"

        # Ensure target directories exist
        self._final_dir.mkdir(parents=True, exist_ok=True)
        self._log_dir.mkdir(parents=True, exist_ok=True)

        # Schema configuration
        self._schema_order: Tuple[str, ...] = (
            schema_order if schema_order is not None else DEFAULT_SCHEMA_ORDER
        )

        # Internal state
        self._datasets: List[pd.DataFrame] = []
        self._dataset_names: List[str] = []
        self._schema_issues: List[SchemaIssue] = []
        self._statistics: MergeStatistics = MergeStatistics()

        logger.info(
            "DatasetMerger initialised. "
            "Processed: %s, Final: %s, Logs: %s, Schema columns: %d",
            self._processed_dir,
            self._final_dir,
            self._log_dir,
            len(self._schema_order),
        )

    # ------------------------------------------------------------------
    # Dataset discovery
    # ------------------------------------------------------------------

    def discover_datasets(self) -> List[Dict[str, Any]]:
        """
        Scan the processed directory for available datasets.

        This method searches for files with recognised extensions
        (``.csv``, ``.xlsx``, ``.xls``, ``.json``) in the processed data
        directory. Hidden files (names starting with ``.``) are excluded.

        Returns:
            A list of dictionaries, each containing:
            - ``path``: Absolute file path.
            - ``name``: File name (e.g. ``vellore_crime_clean.csv``).
            - ``stem``: File name without extension
              (e.g. ``vellore_crime_clean``).
            - ``extension``: File extension (e.g. ``.csv``).

        Raises:
            RuntimeError: If no supported datasets are found.
        """
        logger.info("Discovering datasets in: %s", self._processed_dir)

        datasets: List[Dict[str, Any]] = []

        for ext in SUPPORTED_EXTENSIONS:
            for file_path in sorted(self._processed_dir.glob(f"*{ext}")):
                # Skip hidden files
                if file_path.name.startswith("."):
                    logger.debug("Skipping hidden file: %s", file_path.name)
                    continue

                dataset_info: Dict[str, Any] = {
                    "path": str(file_path),
                    "name": file_path.name,
                    "stem": file_path.stem,
                    "extension": ext,
                }
                datasets.append(dataset_info)
                logger.debug("Found dataset: %s", file_path.name)

        if not datasets:
            logger.warning(
                "No supported datasets found in %s. "
                "Expected formats: %s",
                self._processed_dir,
                ", ".join(SUPPORTED_EXTENSIONS),
            )
        else:
            logger.info("Discovered %d dataset(s).", len(datasets))

        return datasets

    # ------------------------------------------------------------------
    # Dataset loading
    # ------------------------------------------------------------------

    def load_dataset(self, file_path: str) -> pd.DataFrame:
        """
        Load a dataset from the given path based on its file extension.

        Supported formats:
            - CSV (``.csv``) via ``pd.read_csv``.
            - Excel (``.xlsx``, ``.xls``) via ``pd.read_excel``.
            - JSON (``.json``) via ``pd.read_json``.

        Args:
            file_path: Absolute or relative path to the dataset file.

        Returns:
            A pandas DataFrame containing the loaded data.

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the file extension is not supported or the
                file cannot be parsed.
        """
        path: Path = Path(file_path).resolve()

        if not path.is_file():
            raise FileNotFoundError(f"Dataset file not found: {path}")

        extension: str = path.suffix.lower()
        logger.info("Loading dataset: %s (format: %s)", path, extension)

        try:
            if extension == ".csv":
                df: pd.DataFrame = pd.read_csv(
                    path, encoding="utf-8", low_memory=False
                )
            elif extension in (".xlsx", ".xls"):
                df = pd.read_excel(path, engine="openpyxl")
            elif extension == ".json":
                df = pd.read_json(path, encoding="utf-8")
            else:
                raise ValueError(
                    f"Unsupported file extension '{extension}'. "
                    f"Supported extensions: {', '.join(SUPPORTED_EXTENSIONS)}"
                )
        except Exception as exc:
            raise ValueError(
                f"Failed to parse dataset '{path.name}': {exc}"
            ) from exc

        logger.info(
            "Loaded %d rows, %d columns from '%s'.",
            len(df),
            len(df.columns),
            path.name,
        )
        return df

    # ------------------------------------------------------------------
    # Schema validation
    # ------------------------------------------------------------------

    def validate_schema(self, df: pd.DataFrame, dataset_name: str) -> List[SchemaIssue]:
        """
        Compare a dataset's columns against the canonical schema.

        Three categories of issues are detected:
            1. **Missing columns**: Required columns from the canonical
               schema that are absent in the dataset.
            2. **Extra columns**: Columns present in the dataset but not
               part of the canonical schema.
            3. **Incorrect ordering**: Columns that exist but appear in a
               different order than the canonical schema.

        Issues are reported as warnings and do **not** immediately fail
        the merge. Missing columns will be added as null during
        normalisation; extra columns will be retained for downstream
        flexibility.

        Args:
            df: The DataFrame to validate.
            dataset_name: A human-readable name for the dataset (used in
                issue reporting).

        Returns:
            A list of ``SchemaIssue`` objects describing all anomalies
            found. An empty list indicates perfect schema alignment.
        """
        issues: List[SchemaIssue] = []
        actual_columns: List[str] = list(df.columns)
        actual_set: Set[str] = set(actual_columns)
        expected_set: Set[str] = set(self._schema_order)

        # 1. Detect missing columns
        for col in self._schema_order:
            if col not in actual_set:
                issue = SchemaIssue(
                    dataset_name=dataset_name,
                    issue_type="missing_column",
                    column=col,
                    message=(
                        f"Column '{col}' is missing from dataset "
                        f"'{dataset_name}'. It will be added with null "
                        f"values during normalisation."
                    ),
                )
                issues.append(issue)
                logger.warning(
                    "Schema issue [%s]: Missing column '%s' in '%s'.",
                    "missing_column",
                    col,
                    dataset_name,
                )

        # 2. Detect extra columns
        for col in actual_columns:
            if col not in expected_set:
                issue = SchemaIssue(
                    dataset_name=dataset_name,
                    issue_type="extra_column",
                    column=col,
                    message=(
                        f"Column '{col}' is present in dataset "
                        f"'{dataset_name}' but is not part of the canonical "
                        f"schema. It will be retained in the merged output."
                    ),
                )
                issues.append(issue)
                logger.info(
                    "Schema note [%s]: Extra column '%s' in '%s'.",
                    "extra_column",
                    col,
                    dataset_name,
                )

        # 3. Detect incorrect ordering (only among columns that exist)
        existing_expected = [c for c in self._schema_order if c in actual_set]
        existing_actual = [c for c in actual_columns if c in existing_expected]

        if existing_expected and existing_actual != existing_expected:
            issue = SchemaIssue(
                dataset_name=dataset_name,
                issue_type="incorrect_order",
                column=", ".join(existing_expected),
                message=(
                    f"Dataset '{dataset_name}' has columns in a different "
                    f"order than the canonical schema. Columns will be "
                    f"reordered during normalisation."
                ),
            )
            issues.append(issue)
            logger.info(
                "Schema note [%s]: Column ordering mismatch in '%s'. "
                "Will reorder during normalisation.",
                "incorrect_order",
                dataset_name,
            )

        if not issues:
            logger.info(
                "Schema validation passed for '%s'. All columns match.",
                dataset_name,
            )
        else:
            logger.info(
                "Schema validation for '%s' found %d issue(s).",
                dataset_name,
                len(issues),
            )

        return issues

    # ------------------------------------------------------------------
    # Schema normalisation
    # ------------------------------------------------------------------

    def normalize_schema(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalise a DataFrame's schema to match the canonical column set
        and order.

        Operations performed:
            - Add any missing canonical columns filled with ``None``/``NaN``.
            - Reorder columns to match ``self._schema_order``.
            - Retain any extra columns (appended after the canonical
              columns) so that no data is silently dropped.

        Args:
            df: The DataFrame to normalise.

        Returns:
            A new DataFrame with a consistent schema.
        """
        df_normalized: pd.DataFrame = df.copy()

        # Add missing columns with null values
        for col in self._schema_order:
            if col not in df_normalized.columns:
                df_normalized[col] = None

        # Identify extra columns not in the canonical schema
        extra_columns: List[str] = [
            col for col in df_normalized.columns if col not in self._schema_order
        ]

        # Reorder: canonical columns first, then extra columns
        ordered_columns: List[str] = list(self._schema_order) + extra_columns
        df_normalized = df_normalized[ordered_columns]

        logger.debug(
            "Schema normalised: %d canonical + %d extra columns.",
            len(self._schema_order),
            len(extra_columns),
        )

        return df_normalized

    # ------------------------------------------------------------------
    # Merge
    # ------------------------------------------------------------------

    def merge(self) -> pd.DataFrame:
        """
        Merge all loaded, normalised datasets into a single DataFrame.

        The merge is performed as a vertical append (``pd.concat``) of all
        datasets. After concatenation, duplicate ``crime_id`` records are
        removed — the **first** occurrence of each ``crime_id`` is kept.

        Returns:
            A deduplicated DataFrame containing all records from every
            dataset.

        Raises:
            RuntimeError: If no datasets have been loaded.
        """
        if not self._datasets:
            raise RuntimeError(
                "No datasets available for merge. "
                "Call load_dataset() and normalise_schema() first."
            )

        logger.info(
            "Merging %d dataset(s) with vertical concatenation.",
            len(self._datasets),
        )

        # Count rows before merge
        rows_before: int = sum(len(df) for df in self._datasets)
        self._statistics.rows_before = rows_before
        logger.info("Total rows before merge: %d", rows_before)

        # Concatenate all DataFrames
        master_df: pd.DataFrame = pd.concat(
            self._datasets, ignore_index=True, sort=False
        )
        logger.info(
            "Concatenation complete. Combined rows: %d", len(master_df)
        )

        # Deduplicate based on crime_id
        if "crime_id" in master_df.columns:
            rows_before_dedup: int = len(master_df)
            master_df = master_df.drop_duplicates(
                subset=["crime_id"], keep="first"
            )
            duplicates_removed: int = rows_before_dedup - len(master_df)
            self._statistics.duplicates_removed = duplicates_removed

            if duplicates_removed > 0:
                logger.info(
                    "Removed %d duplicate crime_id record(s).",
                    duplicates_removed,
                )
            else:
                logger.info("No duplicate crime_id records found.")
        else:
            logger.warning(
                "Column 'crime_id' not found. Skipping deduplication."
            )

        self._statistics.rows_after = len(master_df)
        logger.info("Rows after merge and deduplication: %d", len(master_df))

        return master_df

    # ------------------------------------------------------------------
    # Merge statistics
    # ------------------------------------------------------------------

    def generate_merge_statistics(self) -> MergeStatistics:
        """
        Finalise and return the merge statistics.

        This method is called automatically at the end of ``run()``,
        but can also be invoked manually after a custom merge workflow.

        Returns:
            A fully populated ``MergeStatistics`` instance.
        """
        logger.info(
            "Merge statistics: "
            "datasets_found=%d, datasets_merged=%d, "
            "rows_before=%d, rows_after=%d, "
            "duplicates_removed=%d, execution_time=%.4fs",
            self._statistics.datasets_found,
            self._statistics.datasets_merged,
            self._statistics.rows_before,
            self._statistics.rows_after,
            self._statistics.duplicates_removed,
            self._statistics.execution_time,
        )
        return self._statistics

    # ------------------------------------------------------------------
    # Save master dataset
    # ------------------------------------------------------------------

    def save_master_dataset(self, master_df: pd.DataFrame) -> Path:
        """
        Save the merged master dataset to ``data/final/master_crime_dataset.csv``.

        The file is written in UTF-8 encoding with Unix-style line
        endings for cross-platform compatibility.

        Args:
            master_df: The merged DataFrame to persist.

        Returns:
            The path to the saved CSV file.

        Raises:
            IOError: If the file could not be written.
        """
        output_path: Path = self._final_dir / "master_crime_dataset.csv"

        logger.info("Saving master dataset: %s", output_path)

        try:
            master_df.to_csv(
                output_path,
                index=False,
                encoding="utf-8",
                line_terminator="\n",
            )
        except OSError as exc:
            logger.error("Failed to save master dataset: %s", exc)
            raise IOError(
                f"Could not write master dataset to {output_path}: {exc}"
            ) from exc

        file_size_mb: float = output_path.stat().st_size / (1024 * 1024)
        logger.info(
            "Master dataset saved successfully. "
            "Rows: %d, Columns: %d, Size: %.2f MB",
            len(master_df),
            len(master_df.columns),
            file_size_mb,
        )

        return output_path

    # ------------------------------------------------------------------
    # Save merge report
    # ------------------------------------------------------------------

    def save_merge_report(
        self,
        master_df: pd.DataFrame,
        schema_issues: List[SchemaIssue],
        statistics: MergeStatistics,
    ) -> Path:
        """
        Save a comprehensive merge report to the log directory.

        The report is a JSON file named
        ``merge_report_{timestamp}.json`` containing:

            - General metadata (timestamp, project root).
            - Dataset details (names, row counts).
            - Schema validation results (issues per dataset).
            - Merge statistics.

        Args:
            master_df: The final merged DataFrame (used to extract per-dataset
                metadata if available).
            schema_issues: List of all schema issues detected across
                datasets.
            statistics: The merge statistics to include in the report.
            dataset_details: Optional list of per-dataset summary dicts.

        Returns:
            The path to the saved report file.
        """
        timestamp: str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        report_filename: str = f"merge_report_{timestamp}.json"
        report_path: Path = self._log_dir / report_filename

        # Build per-dataset summary
        dataset_details: List[Dict[str, object]] = []
        for name, df in zip(self._dataset_names, self._datasets):
            dataset_details.append(
                {
                    "dataset_name": name,
                    "rows": len(df),
                    "columns": len(df.columns),
                    "column_list": list(df.columns),
                }
            )

        report: Dict[str, object] = {
            "report_type": "merge_report",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "project_root": str(self._project_root),
            "processed_directory": str(self._processed_dir),
            "final_directory": str(self._final_dir),
            "datasets": dataset_details,
            "schema_issues": [issue.to_dict() for issue in schema_issues],
            "statistics": statistics.to_dict(),
            "master_dataset_columns": list(master_df.columns),
            "master_dataset_row_count": len(master_df),
        }

        logger.info("Saving merge report: %s", report_path)

        try:
            with report_path.open("w", encoding="utf-8") as fh:
                json.dump(report, fh, indent=2, ensure_ascii=False)
        except OSError as exc:
            logger.error("Failed to save merge report: %s", exc)
            raise IOError(
                f"Could not write merge report to {report_path}: {exc}"
            ) from exc

        logger.info("Merge report saved: %s", report_path)
        return report_path

    # ------------------------------------------------------------------
    # Main workflow
    # ------------------------------------------------------------------

    def run(self) -> MergeStatistics:
        """
        Execute the complete merge workflow.

        Steps:
            1. Discover datasets in ``data/processed/``.
            2. Load each discovered dataset.
            3. Validate schemas for all datasets.
            4. Normalise schemas to a consistent format.
            5. Vertically merge all datasets with deduplication.
            6. Save the master dataset to ``data/final/``.
            7. Save a merge report to ``logs/``.
            8. Return merge statistics.

        Returns:
            A ``MergeStatistics`` dataclass with detailed metrics about
            the merge operation.

        Raises:
            RuntimeError: If no datasets are found in the processed
                directory.
        """
        logger.info("=" * 60)
        logger.info("Merge workflow started")
        logger.info("=" * 60)

        start_time: float = time.perf_counter()

        # Reset internal state for this run
        self._datasets = []
        self._dataset_names = []
        self._schema_issues = []
        self._statistics = MergeStatistics()

        # Step 1: Discover datasets
        logger.info("--- Step 1/7: Discovering datasets ---")
        discovered: List[Dict[str, Any]] = self.discover_datasets()
        self._statistics.datasets_found = len(discovered)

        if not discovered:
            logger.error("No datasets found. Aborting merge.")
            raise RuntimeError(
                f"No supported datasets found in '{self._processed_dir}'. "
                f"Place validated CSV, Excel, or JSON files in this "
                f"directory and re-run."
            )

        # Step 2: Load datasets
        logger.info("--- Step 2/7: Loading datasets ---")
        for ds in discovered:
            try:
                df: pd.DataFrame = self.load_dataset(ds["path"])
                self._datasets.append(df)
                self._dataset_names.append(ds["name"])
            except (FileNotFoundError, ValueError) as exc:
                logger.error(
                    "Failed to load dataset '%s': %s. Skipping.",
                    ds["name"],
                    exc,
                )
                continue

        if not self._datasets:
            raise RuntimeError(
                "No datasets could be loaded. Aborting merge."
            )

        self._statistics.datasets_merged = len(self._datasets)
        logger.info(
            "Successfully loaded %d / %d dataset(s).",
            len(self._datasets),
            len(discovered),
        )

        # Step 3: Validate schemas
        logger.info("--- Step 3/7: Validating schemas ---")
        all_schema_issues: List[SchemaIssue] = []
        for name, df in zip(self._dataset_names, self._datasets):
            issues: List[SchemaIssue] = self.validate_schema(df, name)
            all_schema_issues.extend(issues)
        self._schema_issues = all_schema_issues

        if all_schema_issues:
            logger.info(
                "Schema validation complete. Found %d issue(s) across "
                "%d dataset(s).",
                len(all_schema_issues),
                len(self._datasets),
            )
        else:
            logger.info(
                "Schema validation complete. All %d dataset(s) match "
                "the canonical schema exactly.",
                len(self._datasets),
            )

        # Step 4: Normalise schemas
        logger.info("--- Step 4/7: Normalising schemas ---")
        normalised_datasets: List[pd.DataFrame] = []
        for i, df in enumerate(self._datasets):
            normalised_df: pd.DataFrame = self.normalize_schema(df)
            normalised_datasets.append(normalised_df)
            logger.debug(
                "Normalised '%s': %d columns.",
                self._dataset_names[i],
                len(normalised_df.columns),
            )
        self._datasets = normalised_datasets

        # Step 5: Merge datasets
        logger.info("--- Step 5/7: Merging datasets ---")
        master_df: pd.DataFrame = self.merge()

        # Step 6: Save master dataset
        logger.info("--- Step 6/7: Saving master dataset ---")
        self.save_master_dataset(master_df)

        # Step 7: Save merge report
        logger.info("--- Step 7/7: Saving merge report ---")
        self._statistics.execution_time = time.perf_counter() - start_time
        self.save_merge_report(master_df, all_schema_issues, self._statistics)

        # Final
        self.generate_merge_statistics()

        logger.info("=" * 60)
        logger.info("Merge workflow completed successfully")
        logger.info("=" * 60)

        return self._statistics


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """
    CLI entry point for the dataset merger.

    Configures console logging, creates a DatasetMerger, and executes the
    complete merge workflow. Merge statistics are printed to stdout after
    completion.

    Usage:
        python -m scripts.dataset_builder.merge_datasets
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[logging.StreamHandler()],
    )

    logger.info("DatasetMerger CLI entry point invoked.")

    try:
        merger: DatasetMerger = DatasetMerger()
        stats: MergeStatistics = merger.run()

        print("\n" + "=" * 60)
        print("MERGE COMPLETE")
        print("=" * 60)
        print(f"  Datasets found:      {stats.datasets_found}")
        print(f"  Datasets merged:     {stats.datasets_merged}")
        print(f"  Rows before merge:   {stats.rows_before}")
        print(f"  Rows after merge:    {stats.rows_after}")
        print(f"  Duplicates removed:  {stats.duplicates_removed}")
        print(f"  Execution time:      {stats.execution_time:.4f}s")
        print("=" * 60)
    except (RuntimeError, IOError) as exc:
        logger.error("Merge workflow failed: %s", exc)
        print(f"\nERROR: Merge workflow failed. {exc}")
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()