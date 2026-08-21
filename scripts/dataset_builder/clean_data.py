"""
Data cleaning module for the Crime Analysis project.

This module is the second stage of the data pipeline. It reads raw datasets
from ``data/raw/`` and outputs cleaned, standardised datasets to
``data/processed/``.

Cleaning operations include:
    - Removing duplicate records
    - Handling missing values using configurable strategies
    - Standardising column names to snake_case
    - Converting date and time columns to uniform formats
    - Trimming and normalising text columns
    - Validating that required columns are present

The module performs NO machine learning, NO feature engineering,
NO geocoding, and NO database operations.

Usage:
    python -m scripts.dataset_builder.clean_data

Or programmatically:
    from scripts.dataset_builder.clean_data import DataCleaner
    cleaner = DataCleaner()
    cleaner.run()
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

# ---------------------------------------------------------------------------
# Logger
# ---------------------------------------------------------------------------

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

REQUIRED_COLUMNS: Tuple[str, ...] = (
    "incident_id",
    "source",
    "crime_category",
    "incident_date",
    "latitude",
    "longitude",
    "city",
    "state",
)

"""Columns that must be present in every dataset after cleaning."""

DEFAULT_DATE_FORMAT: str = "%Y-%m-%d"
"""Target format for all date columns after standardisation."""

DEFAULT_TIME_FORMAT: str = "%H:%M:%S"
"""Target format for all time columns after standardisation."""

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class CleaningReport:
    """
    Summary report generated after a cleaning run.

    Attributes:
        original_rows: Number of rows in the raw input dataset.
        final_rows: Number of rows in the cleaned output dataset.
        duplicates_removed: Number of duplicate rows removed.
        missing_values_fixed: Number of missing values that were handled.
        processing_time: Duration of the cleaning run in seconds.
        output_file: Path to the saved cleaned dataset.
    """

    original_rows: int = 0
    final_rows: int = 0
    duplicates_removed: int = 0
    missing_values_fixed: int = 0
    processing_time: float = 0.0
    output_file: str = ""

    def to_dict(self) -> Dict[str, object]:
        """Return a JSON-serialisable dictionary of this report."""
        return asdict(self)

    def log_summary(self) -> None:
        """Log the cleaning report at INFO level."""
        logger.info("Cleaning report:")
        logger.info("  Original rows:        %d", self.original_rows)
        logger.info("  Final rows:           %d", self.final_rows)
        logger.info("  Duplicates removed:   %d", self.duplicates_removed)
        logger.info("  Missing values fixed: %d", self.missing_values_fixed)
        logger.info("  Processing time:      %.2f seconds", self.processing_time)
        logger.info("  Output file:          %s", self.output_file)


# ---------------------------------------------------------------------------
# Cleaner
# ---------------------------------------------------------------------------


class DataCleaner:
    """
    Reads raw crime datasets and produces cleaned, standardised output.

    The cleaning workflow is as follows:

        1. Load a raw dataset from ``data/raw/``.
        2. Validate that required columns exist.
        3. Remove duplicate rows.
        4. Handle missing values using configurable per-column strategies.
        5. Standardise column names to lowercase snake_case.
        6. Convert date columns to ``YYYY-MM-DD`` format.
        7. Convert time columns to ``HH:MM:SS`` format.
        8. Clean text columns (trim whitespace, normalise case).
        9. Save the cleaned dataset to ``data/processed/``.
        10. Generate and persist a cleaning report to ``logs/``.
    """

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------

    def __init__(
        self,
        raw_dir: Optional[str] = None,
        processed_dir: Optional[str] = None,
        log_dir: Optional[str] = None,
        missing_strategies: Optional[Dict[str, str]] = None,
        date_columns: Optional[List[str]] = None,
        time_columns: Optional[List[str]] = None,
        text_columns: Optional[List[str]] = None,
    ) -> None:
        """
        Initialise the DataCleaner.

        Args:
            raw_dir: Directory containing raw input files. Defaults to
                ``data/raw`` relative to the project root.
            processed_dir: Directory for cleaned output files. Defaults to
                ``data/processed``.
            log_dir: Directory for log output and cleaning reports.
                Defaults to ``logs``.
            missing_strategies: Per-column missing value strategies.
                Keys are column names, values are one of ``"drop"``,
                ``"fill_mean"``, ``"fill_median"``, ``"fill_mode"``,
                or ``"fill_value"``. Columns not listed use ``"drop"``.
            date_columns: List of column names containing date values.
                Defaults to ``["incident_date"]``.
            time_columns: List of column names containing time values.
                Defaults to ``["incident_time"]``.
            text_columns: List of column names to clean as text.
                Defaults to ``["address", "city", "district", "state",
                "landmark"]``.
        """
        # Resolve the project root
        self._project_root: Path = Path(__file__).resolve().parents[2]

        # Directories
        if raw_dir:
            self._raw_dir: Path = Path(raw_dir).resolve()
        else:
            self._raw_dir = self._project_root / "data" / "raw"

        if processed_dir:
            self._processed_dir: Path = Path(processed_dir).resolve()
        else:
            self._processed_dir = self._project_root / "data" / "processed"

        if log_dir:
            self._log_dir: Path = Path(log_dir).resolve()
        else:
            self._log_dir = self._project_root / "logs"

        # Ensure output directories exist
        self._processed_dir.mkdir(parents=True, exist_ok=True)
        self._log_dir.mkdir(parents=True, exist_ok=True)

        # Missing value strategies (column -> strategy)
        self._missing_strategies: Dict[str, str] = missing_strategies or {}

        # Column groups
        self._date_columns: List[str] = date_columns or ["incident_date"]
        self._time_columns: List[str] = time_columns or ["incident_time"]
        self._text_columns: List[str] = text_columns or [
            "address",
            "city",
            "district",
            "state",
            "landmark",
        ]

        # Internal state
        self._report: CleaningReport = CleaningReport()
        self._dataframe: Optional[pd.DataFrame] = None

        logger.info(
            "DataCleaner initialised. Raw: %s, Processed: %s, Logs: %s",
            self._raw_dir,
            self._processed_dir,
            self._log_dir,
        )

    # ------------------------------------------------------------------
    # Dataset loading
    # ------------------------------------------------------------------

    def load_dataset(self, file_path: str) -> pd.DataFrame:
        """
        Load a dataset from a CSV, Excel, or JSON file.

        The file format is inferred from the file extension.

        Args:
            file_path: Path to the input file (relative or absolute).

        Returns:
            A pandas DataFrame containing the loaded data.

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the file format is not supported.
        """
        path: Path = Path(file_path).resolve()

        if not path.is_file():
            raise FileNotFoundError(f"Input file not found: {path}")

        extension: str = path.suffix.lower()
        logger.info("Loading dataset: %s (format: %s)", path, extension)

        if extension == ".csv":
            df: pd.DataFrame = pd.read_csv(path, encoding="utf-8", low_memory=False)
        elif extension in (".xlsx", ".xls"):
            df = pd.read_excel(path, engine="openpyxl")
        elif extension == ".json":
            df = pd.read_json(path, encoding="utf-8")
        else:
            raise ValueError(
                f"Unsupported file format '{extension}'. "
                f"Supported formats: .csv, .xlsx, .xls, .json"
            )

        logger.info("Loaded %d rows and %d columns.", len(df), len(df.columns))
        self._dataframe = df
        return df

    # ------------------------------------------------------------------
    # Duplicate removal
    # ------------------------------------------------------------------

    def remove_duplicates(self, subset: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Remove duplicate rows from the dataset.

        If *subset* is provided, only those columns are used for
        duplicate detection. Otherwise, all columns are compared.

        Args:
            subset: Optional list of column names to consider for
                duplicate detection.

        Returns:
            DataFrame with duplicates removed.
        """
        if self._dataframe is None:
            raise RuntimeError("No dataset loaded. Call load_dataset() first.")

        before: int = len(self._dataframe)
        self._dataframe = self._dataframe.drop_duplicates(subset=subset, keep="first")
        after: int = len(self._dataframe)
        removed: int = before - after

        self._report.duplicates_removed += removed
        logger.info("Removed %d duplicate row(s). Rows: %d -> %d", removed, before, after)

        return self._dataframe

    # ------------------------------------------------------------------
    # Missing value handling
    # ------------------------------------------------------------------

    def handle_missing_values(self) -> pd.DataFrame:
        """
        Handle missing values using the configured per-column strategies.

        For each column in the dataset, the strategy is looked up in
        ``self._missing_strategies``. If no strategy is configured for
        a column, the default is ``"drop"`` (drop rows with any missing
        value in that column).

        Supported strategies:
            - ``"drop"``: Drop rows with missing values in this column.
            - ``"fill_mean"``: Fill with the column mean (numeric only).
            - ``"fill_median"``: Fill with the column median (numeric only).
            - ``"fill_mode"``: Fill with the most frequent value.
            - ``"fill_value"``: Fill with the string ``"Unknown"``.

        Returns:
            DataFrame with missing values handled.
        """
        if self._dataframe is None:
            raise RuntimeError("No dataset loaded. Call load_dataset() first.")

        total_fixed: int = 0

        for column in self._dataframe.columns:
            missing_count: int = int(self._dataframe[column].isna().sum())
            if missing_count == 0:
                continue

            strategy: str = self._missing_strategies.get(column, "drop")
            logger.debug(
                "Column '%s': %d missing value(s). Strategy: %s",
                column,
                missing_count,
                strategy,
            )

            if strategy == "drop":
                before_drop: int = len(self._dataframe)
                self._dataframe = self._dataframe.dropna(subset=[column])
                dropped: int = before_drop - len(self._dataframe)
                total_fixed += dropped
                logger.debug("  Dropped %d row(s) with missing '%s'.", dropped, column)

            elif strategy == "fill_mean":
                if pd.api.types.is_numeric_dtype(self._dataframe[column]):
                    mean_val: float = float(self._dataframe[column].mean())
                    self._dataframe[column] = self._dataframe[column].fillna(mean_val)
                    total_fixed += missing_count
                    logger.debug("  Filled with mean: %.4f", mean_val)
                else:
                    logger.warning(
                        "Column '%s' is not numeric. Skipping fill_mean.", column
                    )

            elif strategy == "fill_median":
                if pd.api.types.is_numeric_dtype(self._dataframe[column]):
                    median_val: float = float(self._dataframe[column].median())
                    self._dataframe[column] = self._dataframe[column].fillna(median_val)
                    total_fixed += missing_count
                    logger.debug("  Filled with median: %.4f", median_val)
                else:
                    logger.warning(
                        "Column '%s' is not numeric. Skipping fill_median.", column
                    )

            elif strategy == "fill_mode":
                mode_series = self._dataframe[column].mode(dropna=True)
                if not mode_series.empty:
                    mode_val = mode_series.iloc[0]
                    self._dataframe[column] = self._dataframe[column].fillna(mode_val)
                    total_fixed += missing_count
                    logger.debug("  Filled with mode: %s", mode_val)
                else:
                    logger.warning(
                        "Column '%s' has no mode (all null). Skipping.", column
                    )

            elif strategy == "fill_value":
                self._dataframe[column] = self._dataframe[column].fillna("Unknown")
                total_fixed += missing_count
                logger.debug("  Filled with 'Unknown'.")

            else:
                logger.warning(
                    "Unknown strategy '%s' for column '%s'. Using 'drop'.",
                    strategy,
                    column,
                )
                before_drop = len(self._dataframe)
                self._dataframe = self._dataframe.dropna(subset=[column])
                total_fixed += before_drop - len(self._dataframe)

        self._report.missing_values_fixed += total_fixed
        logger.info(
            "Missing value handling complete. %d value(s) fixed.", total_fixed
        )

        return self._dataframe

    # ------------------------------------------------------------------
    # Column name standardisation
    # ------------------------------------------------------------------

    def standardize_column_names(self) -> pd.DataFrame:
        """
        Convert all column names to lowercase snake_case.

        Transformations applied:
            - Convert to lowercase.
            - Replace spaces and hyphens with underscores.
            - Remove any characters that are not alphanumeric or underscores.
            - Strip leading/trailing underscores.

        Returns:
            DataFrame with standardised column names.
        """
        if self._dataframe is None:
            raise RuntimeError("No dataset loaded. Call load_dataset() first.")

        rename_map: Dict[str, str] = {}

        for col in self._dataframe.columns:
            original: str = str(col)
            cleaned: str = original.lower()
            cleaned = cleaned.replace(" ", "_").replace("-", "_")
            cleaned = "".join(c for c in cleaned if c.isalnum() or c == "_")
            cleaned = cleaned.strip("_")

            if cleaned != original:
                rename_map[original] = cleaned

        if rename_map:
            self._dataframe = self._dataframe.rename(columns=rename_map)
            logger.info(
                "Standardised %d column name(s): %s",
                len(rename_map),
                rename_map,
            )
        else:
            logger.info("All column names already standardised.")

        return self._dataframe

    # ------------------------------------------------------------------
    # Date standardisation
    # ------------------------------------------------------------------

    def standardize_date_formats(self) -> pd.DataFrame:
        """
        Convert date columns to a uniform ``YYYY-MM-DD`` format.

        Only columns listed in ``self._date_columns`` are processed.
        Values that cannot be parsed are set to ``pd.NaT`` and logged.

        Returns:
            DataFrame with standardised date columns.
        """
        if self._dataframe is None:
            raise RuntimeError("No dataset loaded. Call load_dataset() first.")

        for col in self._date_columns:
            if col not in self._dataframe.columns:
                logger.warning("Date column '%s' not found in dataset. Skipping.", col)
                continue

            before_count: int = int(self._dataframe[col].isna().sum())

            # Attempt to parse with inferred format, then coerce errors to NaT
            self._dataframe[col] = pd.to_datetime(
                self._dataframe[col], errors="coerce", infer_datetime_format=True
            )

            # Format as YYYY-MM-DD string; NaT becomes None
            self._dataframe[col] = self._dataframe[col].apply(
                lambda x: x.strftime(DEFAULT_DATE_FORMAT) if pd.notna(x) else None
            )

            after_count: int = int(self._dataframe[col].isna().sum())
            newly_unparsed: int = after_count - before_count

            if newly_unparsed > 0:
                logger.warning(
                    "Column '%s': %d value(s) could not be parsed as dates.",
                    col,
                    newly_unparsed,
                )

            logger.info(
                "Standardised date column '%s'. Unparseable: %d",
                col,
                newly_unparsed,
            )

        return self._dataframe

    # ------------------------------------------------------------------
    # Time standardisation
    # ------------------------------------------------------------------

    def standardize_time_formats(self) -> pd.DataFrame:
        """
        Convert time columns to a uniform ``HH:MM:SS`` format.

        Only columns listed in ``self._time_columns`` are processed.
        Values that cannot be parsed are set to ``"00:00:00"`` and logged.

        Returns:
            DataFrame with standardised time columns.
        """
        if self._dataframe is None:
            raise RuntimeError("No dataset loaded. Call load_dataset() first.")

        for col in self._time_columns:
            if col not in self._dataframe.columns:
                logger.warning("Time column '%s' not found in dataset. Skipping.", col)
                continue

            unparseable: int = 0

            def _parse_time(value: object) -> Optional[str]:
                """Try to parse a single time value into HH:MM:SS."""
                if value is None or (isinstance(value, str) and value.strip() == ""):
                    return None

                try:
                    # Try parsing with seconds
                    parsed = datetime.strptime(str(value).strip(), "%H:%M:%S")
                    return parsed.strftime(DEFAULT_TIME_FORMAT)
                except (ValueError, TypeError):
                    pass

                try:
                    # Try parsing without seconds (HH:MM)
                    parsed = datetime.strptime(str(value).strip(), "%H:%M")
                    return parsed.strftime(DEFAULT_TIME_FORMAT)
                except (ValueError, TypeError):
                    pass

                try:
                    # Try parsing as HHMMSS (6-digit integer)
                    cleaned: str = str(value).strip().zfill(6)
                    parsed = datetime.strptime(cleaned, "%H%M%S")
                    return parsed.strftime(DEFAULT_TIME_FORMAT)
                except (ValueError, TypeError):
                    pass

                # If all attempts fail, log and return default
                nonlocal unparseable
                unparseable += 1
                return "00:00:00"

            self._dataframe[col] = self._dataframe[col].apply(_parse_time)

            if unparseable > 0:
                logger.warning(
                    "Column '%s': %d value(s) could not be parsed. Set to 00:00:00.",
                    col,
                    unparseable,
                )

            logger.info("Standardised time column '%s'.", col)

        return self._dataframe

    # ------------------------------------------------------------------
    # Text column cleaning
    # ------------------------------------------------------------------

    def clean_text_columns(self) -> pd.DataFrame:
        """
        Clean text columns by trimming whitespace and normalising case.

        Operations applied to each column in ``self._text_columns``:
            - Strip leading and trailing whitespace.
            - Replace multiple internal spaces with a single space.
            - Capitalise the first letter of each word (title case).

        Returns:
            DataFrame with cleaned text columns.
        """
        if self._dataframe is None:
            raise RuntimeError("No dataset loaded. Call load_dataset() first.")

        for col in self._text_columns:
            if col not in self._dataframe.columns:
                logger.debug("Text column '%s' not found. Skipping.", col)
                continue

            def _clean_text(value: object) -> Optional[str]:
                """Clean a single text value."""
                if value is None or (isinstance(value, str) and value.strip() == ""):
                    return None

                text: str = str(value).strip()
                # Replace multiple spaces with a single space
                text = " ".join(text.split())
                # Title case for readability
                text = text.title()

                return text

            self._dataframe[col] = self._dataframe[col].apply(_clean_text)
            logger.debug("Cleaned text column '%s'.", col)

        logger.info("Text cleaning complete for %d column(s).", len(self._text_columns))
        return self._dataframe

    # ------------------------------------------------------------------
    # Required column validation
    # ------------------------------------------------------------------

    def validate_required_columns(self) -> None:
        """
        Verify that all required columns are present in the dataset.

        Required columns are defined in ``REQUIRED_COLUMNS``.

        Raises:
            ValueError: If any required column is missing, listing all
            missing column names in the error message.
        """
        if self._dataframe is None:
            raise RuntimeError("No dataset loaded. Call load_dataset() first.")

        missing: List[str] = [
            col for col in REQUIRED_COLUMNS if col not in self._dataframe.columns
        ]

        if missing:
            raise ValueError(
                f"Dataset is missing {len(missing)} required column(s): {missing}. "
                f"Required columns: {list(REQUIRED_COLUMNS)}"
            )

        logger.info(
            "All %d required columns are present.", len(REQUIRED_COLUMNS)
        )

    # ------------------------------------------------------------------
    # Save cleaned dataset
    # ------------------------------------------------------------------

    def save_clean_dataset(self, output_filename: str) -> str:
        """
        Save the cleaned dataset to ``data/processed/`` as a CSV file.

        Args:
            output_filename: Name for the output file (e.g.
                ``"vellore_crime_clean.csv"``).

        Returns:
            Absolute path to the saved file.

        Raises:
            RuntimeError: If no dataset has been loaded/cleaned.
        """
        if self._dataframe is None:
            raise RuntimeError("No dataset to save. Call load_dataset() first.")

        output_path: Path = (self._processed_dir / output_filename).resolve()

        self._dataframe.to_csv(output_path, index=False, encoding="utf-8")

        logger.info(
            "Saved cleaned dataset: %s (%d rows, %d columns)",
            output_path,
            len(self._dataframe),
            len(self._dataframe.columns),
        )

        self._report.output_file = str(output_path)
        return str(output_path)

    # ------------------------------------------------------------------
    # Cleaning report
    # ------------------------------------------------------------------

    def generate_cleaning_report(self) -> CleaningReport:
        """
        Generate and persist a cleaning report to the logs directory.

        The report is saved as a JSON file named
        ``cleaning_report_{timestamp}.json``.

        Returns:
            The CleaningReport dataclass instance with all metrics.
        """
        timestamp: str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        report_filename: str = f"cleaning_report_{timestamp}.json"
        report_path: Path = self._log_dir / report_filename

        with report_path.open("w", encoding="utf-8") as fh:
            json.dump(self._report.to_dict(), fh, indent=2, ensure_ascii=False)

        self._report.log_summary()
        logger.info("Cleaning report saved: %s", report_path)

        return self._report

    # ------------------------------------------------------------------
    # Main workflow
    # ------------------------------------------------------------------

    def run(
        self,
        input_file: str,
        output_filename: str = "crime_data_clean.csv",
    ) -> CleaningReport:
        """
        Execute the complete cleaning workflow.

        Steps:
            1. Load the raw dataset.
            2. Validate required columns.
            3. Remove duplicate rows.
            4. Handle missing values.
            5. Standardise column names.
            6. Standardise date formats.
            7. Standardise time formats.
            8. Clean text columns.
            9. Save the cleaned dataset.
            10. Generate and return the cleaning report.

        Args:
            input_file: Path to the raw input file (relative or absolute).
            output_filename: Name for the cleaned output file. Defaults to
                ``"crime_data_clean.csv"``.

        Returns:
            A CleaningReport instance with metrics from the run.
        """
        start_time: datetime = datetime.now()

        logger.info("=" * 60)
        logger.info("Data cleaning run started at %s", start_time.isoformat())
        logger.info("=" * 60)

        # Step 1: Load
        df: pd.DataFrame = self.load_dataset(input_file)
        self._report.original_rows = len(df)

        # Step 2: Validate required columns
        self.validate_required_columns()

        # Step 3: Remove duplicates
        self.remove_duplicates()

        # Step 4: Handle missing values
        self.handle_missing_values()

        # Step 5: Standardise column names
        self.standardize_column_names()

        # Step 6: Standardise date formats
        self.standardize_date_formats()

        # Step 7: Standardise time formats
        self.standardize_time_formats()

        # Step 8: Clean text columns
        self.clean_text_columns()

        # Step 9: Save
        self.save_clean_dataset(output_filename)

        # Finalise report
        self._report.final_rows = len(self._dataframe)
        end_time: datetime = datetime.now()
        self._report.processing_time = (end_time - start_time).total_seconds()

        # Step 10: Generate report
        self.generate_cleaning_report()

        logger.info("=" * 60)
        logger.info("Data cleaning run completed in %.2f seconds.", self._report.processing_time)
        logger.info("=" * 60)

        return self._report


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """
    CLI entry point for the data cleaner.

    Configures console logging, creates a DataCleaner, and runs the
    cleaning workflow on a default input file.

    Usage:
        python -m scripts.dataset_builder.clean_data
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[logging.StreamHandler()],
    )

    # Default input: look for the first CSV in data/raw/ subdirectories
    project_root: Path = Path(__file__).resolve().parents[2]
    raw_dir: Path = project_root / "data" / "raw"

    input_file: Optional[str] = None
    for subdir in raw_dir.iterdir():
        if subdir.is_dir():
            csv_files: List[Path] = list(subdir.glob("*.csv"))
            if csv_files:
                input_file = str(csv_files[0])
                break

    if input_file is None:
        logger.warning("No CSV file found in data/raw/. Using placeholder path.")
        input_file = str(raw_dir / "vellore_crime_raw.csv")

    cleaner: DataCleaner = DataCleaner()
    report: CleaningReport = cleaner.run(input_file=input_file)

    print(f"\nCleaning complete. Report saved to logs/.")
    print(f"  Original rows: {report.original_rows}")
    print(f"  Final rows:    {report.final_rows}")
    print(f"  Output file:   {report.output_file}")


if __name__ == "__main__":
    main()