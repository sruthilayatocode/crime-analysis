"""
Dataset validation module for the Crime Analysis project.

This module is the quality gate of the data pipeline. It reads cleaned
datasets from ``data/processed/`` and performs comprehensive validation
to ensure the data is accurate, consistent, and suitable for downstream
processing (geocoding, feature engineering, and machine learning).

Validation covers:
    - Required column presence
    - Data type correctness
    - Geographic coordinate boundaries
    - Calendar date validity
    - Time format compliance
    - Crime category membership
    - Duplicate record detection
    - Missing value reporting

The module performs NO data cleaning, NO modification, NO machine
learning, NO geocoding, and NO database operations.

Usage:
    python -m scripts.dataset_builder.validate_data

Or programmatically:
    from scripts.dataset_builder.validate_data import DataValidator
    validator = DataValidator()
    report = validator.run("data/processed/vellore_crime_clean.csv")
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field, asdict
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
    "crime_id",
    "crime_type",
    "date",
    "time",
    "area",
    "latitude",
    "longitude",
    "severity",
)
"""Columns that must be present in every validated dataset."""

VALID_SEVERITY_LEVELS: Tuple[str, ...] = (
    "low",
    "medium",
    "high",
    "critical",
)
"""Allowed values for the severity column."""

DEFAULT_CRIME_CATEGORIES: Tuple[str, ...] = (
    "theft",
    "robbery",
    "burglary",
    "assault",
    "murder",
    "kidnapping",
    "fraud",
    "cyber_crime",
    "vehicle_theft",
    "drug_offence",
    "domestic_violence",
    "harassment",
    "chain_snatching",
    "vandalism",
    "other",
)
"""Default list of recognised crime categories."""

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class ValidationError:
    """
    A single validation error or warning.

    Attributes:
        field: The column or field that failed validation.
        message: Human-readable description of the issue.
        row_index: Optional row index where the error occurred.
        value: The actual value that failed validation, if available.
    """

    field: str
    message: str
    row_index: Optional[int] = None
    value: Optional[object] = None

    def to_dict(self) -> Dict[str, object]:
        """Return a JSON-serialisable dictionary."""
        return {
            "field": self.field,
            "message": self.message,
            "row_index": self.row_index,
            "value": str(self.value) if self.value is not None else None,
        }


@dataclass
class ValidationReport:
    """
    Summary report generated after a validation run.

    Attributes:
        dataset_name: Name of the dataset that was validated.
        records_checked: Total number of records examined.
        errors: List of validation errors found.
        warnings: List of validation warnings found.
        validation_status: Overall status (``PASSED``, ``FAILED``, or
            ``WARNING``).
        generated_at: UTC timestamp when the report was generated.
    """

    dataset_name: str = ""
    records_checked: int = 0
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[ValidationError] = field(default_factory=list)
    validation_status: str = "PASSED"
    generated_at: str = ""

    def __post_init__(self) -> None:
        """Auto-set the timestamp if not provided."""
        if not self.generated_at:
            self.generated_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, object]:
        """Return a JSON-serialisable dictionary."""
        return {
            "dataset_name": self.dataset_name,
            "records_checked": self.records_checked,
            "errors": [e.to_dict() for e in self.errors],
            "warnings": [w.to_dict() for w in self.warnings],
            "validation_status": self.validation_status,
            "generated_at": self.generated_at,
        }

    def log_summary(self) -> None:
        """Log the validation report summary at INFO level."""
        logger.info("Validation report for '%s':", self.dataset_name)
        logger.info("  Records checked:     %d", self.records_checked)
        logger.info("  Errors:              %d", len(self.errors))
        logger.info("  Warnings:            %d", len(self.warnings))
        logger.info("  Overall status:      %s", self.validation_status)


# ---------------------------------------------------------------------------
# Validator
# ---------------------------------------------------------------------------


class DataValidator:
    """
    Validates cleaned crime datasets for correctness and consistency.

    The validation workflow follows this sequence:

        1. Load the dataset from ``data/processed/``.
        2. Check that all required columns exist.
        3. Validate data types for key columns.
        4. Verify latitude/longitude are within geographic bounds.
        5. Check that date values are valid calendar dates.
        6. Validate time column conforms to ``HH:MM:SS``.
        7. Verify crime_type belongs to recognised categories.
        8. Detect duplicate crime_id values.
        9. Report any remaining missing values.
        10. Generate and persist a validation report.
    """

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------

    def __init__(
        self,
        processed_dir: Optional[str] = None,
        log_dir: Optional[str] = None,
        crime_categories: Optional[Tuple[str, ...]] = None,
        severity_levels: Optional[Tuple[str, ...]] = None,
        allow_future_dates: bool = False,
    ) -> None:
        """
        Initialise the DataValidator.

        Args:
            processed_dir: Directory containing processed datasets.
                Defaults to ``data/processed`` relative to the project root.
            log_dir: Directory for validation reports. Defaults to ``logs``.
            crime_categories: Tuple of recognised crime category values.
                Defaults to ``DEFAULT_CRIME_CATEGORIES``.
            severity_levels: Tuple of valid severity values.
                Defaults to ``VALID_SEVERITY_LEVELS``.
            allow_future_dates: If True, dates in the future are allowed.
                Defaults to False.
        """
        # Resolve project root
        self._project_root: Path = Path(__file__).resolve().parents[2]

        # Directories
        if processed_dir:
            self._processed_dir: Path = Path(processed_dir).resolve()
        else:
            self._processed_dir = self._project_root / "data" / "processed"

        if log_dir:
            self._log_dir: Path = Path(log_dir).resolve()
        else:
            self._log_dir = self._project_root / "logs"

        # Ensure target directories exist
        self._log_dir.mkdir(parents=True, exist_ok=True)

        # Validation parameters
        self._crime_categories: Tuple[str, ...] = (
            crime_categories if crime_categories is not None else DEFAULT_CRIME_CATEGORIES
        )
        self._severity_levels: Tuple[str, ...] = (
            severity_levels if severity_levels is not None else VALID_SEVERITY_LEVELS
        )
        self._allow_future_dates: bool = allow_future_dates

        # Internal state
        self._report: ValidationReport = ValidationReport()
        self._dataframe: Optional[pd.DataFrame] = None

        logger.info(
            "DataValidator initialised. Processed: %s, Logs: %s, Categories: %d",
            self._processed_dir,
            self._log_dir,
            len(self._crime_categories),
        )

    # ------------------------------------------------------------------
    # Dataset loading
    # ------------------------------------------------------------------

    def load_dataset(self, file_path: str) -> pd.DataFrame:
        """
        Load a processed dataset from a CSV file.

        Args:
            file_path: Path to the processed CSV file.

        Returns:
            A pandas DataFrame containing the loaded data.

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the file format is not supported.
        """
        path: Path = Path(file_path).resolve()

        if not path.is_file():
            raise FileNotFoundError(f"Dataset not found: {path}")

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
                f"Unsupported format '{extension}'. "
                f"Supported: .csv, .xlsx, .xls, .json"
            )

        self._dataframe = df
        self._report.dataset_name = path.name
        self._report.records_checked = len(df)

        logger.info("Loaded %d rows, %d columns.", len(df), len(df.columns))
        return df

    # ------------------------------------------------------------------
    # Required column validation
    # ------------------------------------------------------------------

    def validate_required_columns(self) -> List[ValidationError]:
        """
        Verify that all required columns exist in the dataset.

        Returns:
            A list of ValidationError objects for any missing columns.
            An empty list means all required columns are present.

        Raises:
            RuntimeError: If no dataset has been loaded.
        """
        if self._dataframe is None:
            raise RuntimeError("No dataset loaded. Call load_dataset() first.")

        errors: List[ValidationError] = []

        for col in REQUIRED_COLUMNS:
            if col not in self._dataframe.columns:
                error = ValidationError(
                    field=col,
                    message=f"Required column '{col}' is missing from the dataset.",
                )
                errors.append(error)
                logger.error("Missing required column: '%s'", col)

        if not errors:
            logger.info(
                "All %d required columns are present.", len(REQUIRED_COLUMNS)
            )

        self._report.errors.extend(errors)
        return errors

    # ------------------------------------------------------------------
    # Data type validation
    # ------------------------------------------------------------------

    def validate_data_types(self) -> List[ValidationError]:
        """
        Check that key columns have the expected data types.

        Expected types:
            - latitude: float
            - longitude: float
            - date: datetime (coercible)
            - crime_type: string (object)
            - severity: string (object)
            - crime_id: string (object) or integer

        Returns:
            A list of ValidationError objects for type mismatches.
        """
        if self._dataframe is None:
            raise RuntimeError("No dataset loaded. Call load_dataset() first.")

        errors: List[ValidationError] = []
        type_checks: Dict[str, str] = {
            "latitude": "float",
            "longitude": "float",
            "crime_type": "string",
            "severity": "string",
        }

        for col, expected_type in type_checks.items():
            if col not in self._dataframe.columns:
                continue

            actual_dtype: str = str(self._dataframe[col].dtype)

            if expected_type == "float" and "float" not in actual_dtype:
                # Check if it can be safely cast to float
                non_null = self._dataframe[col].dropna()
                if len(non_null) > 0:
                    try:
                        non_null.astype(float)
                    except (ValueError, TypeError):
                        error = ValidationError(
                            field=col,
                            message=(
                                f"Expected numeric type for '{col}', "
                                f"got '{actual_dtype}'. Some values cannot be "
                                f"converted to float."
                            ),
                        )
                        errors.append(error)
                        logger.error("Type mismatch: '%s' is %s (expected float)", col, actual_dtype)

            elif expected_type == "string":
                # pandas object or string dtype is acceptable
                if "object" not in actual_dtype and "string" not in actual_dtype:
                    logger.warning(
                        "Column '%s' has dtype '%s' (expected string). "
                        "This may cause issues downstream.",
                        col,
                        actual_dtype,
                    )

        # Date column: check it can be parsed to datetime
        if "date" in self._dataframe.columns:
            date_sample = self._dataframe["date"].dropna().head(100)
            if len(date_sample) > 0:
                try:
                    pd.to_datetime(date_sample, errors="coerce")
                except (ValueError, TypeError) as exc:
                    error = ValidationError(
                        field="date",
                        message=f"Date column could not be parsed: {exc}",
                    )
                    errors.append(error)
                    logger.error("Date parsing failed: %s", exc)

        # Crime ID: should be non-null and ideally unique (checked elsewhere)
        if "crime_id" in self._dataframe.columns:
            non_null_ids = self._dataframe["crime_id"].dropna()
            if len(non_null_ids) > 0:
                # Check if crime_id has mixed types
                type_counts = non_null_ids.apply(type).value_counts()
                if len(type_counts) > 1:
                    logger.warning(
                        "Column 'crime_id' has mixed types: %s. "
                        "Consider standardising to string.",
                        dict(type_counts),
                    )

        self._report.errors.extend(errors)
        if not errors:
            logger.info("Data type validation passed for all checked columns.")

        return errors

    # ------------------------------------------------------------------
    # Coordinate validation
    # ------------------------------------------------------------------

    def validate_coordinates(self) -> List[ValidationError]:
        """
        Validate that latitude and longitude values are within geographic bounds.

        Rules:
            - Latitude must be between -90 and 90.
            - Longitude must be between -180 and 180.

        Returns:
            A list of ValidationError objects for invalid coordinates.
        """
        if self._dataframe is None:
            raise RuntimeError("No dataset loaded. Call load_dataset() first.")

        errors: List[ValidationError] = []

        for col, lower, upper, label in [
            ("latitude", -90.0, 90.0, "Latitude"),
            ("longitude", -180.0, 180.0, "Longitude"),
        ]:
            if col not in self._dataframe.columns:
                continue

            # Drop NA values before comparison
            valid_mask = self._dataframe[col].notna()
            out_of_bounds = (
                ~self._dataframe[col].between(lower, upper) & valid_mask
            )
            invalid_indices = self._dataframe.index[out_of_bounds].tolist()

            for idx in invalid_indices:
                error = ValidationError(
                    field=col,
                    message=(
                        f"{label} value {self._dataframe.loc[idx, col]} "
                        f"is out of range [{lower}, {upper}]."
                    ),
                    row_index=int(idx),
                    value=self._dataframe.loc[idx, col],
                )
                errors.append(error)

            if invalid_indices:
                logger.warning(
                    "'%s': %d value(s) out of bounds [%.1f, %.1f].",
                    col,
                    len(invalid_indices),
                    lower,
                    upper,
                )
            else:
                logger.info("'%s': all values within bounds.", col)

        self._report.errors.extend(errors)
        return errors

    # ------------------------------------------------------------------
    # Date validation
    # ------------------------------------------------------------------

    def validate_dates(self) -> List[ValidationError]:
        """
        Validate date column values.

        Checks performed:
            - Values can be parsed as valid calendar dates.
            - No impossible dates (e.g. 31 February).
            - No future dates (unless ``allow_future_dates`` is True).

        Returns:
            A list of ValidationError objects for invalid dates.
        """
        if self._dataframe is None:
            raise RuntimeError("No dataset loaded. Call load_dataset() first.")

        errors: List[ValidationError] = []

        if "date" not in self._dataframe.columns:
            logger.warning("Column 'date' not found. Skipping date validation.")
            return errors

        # Parse dates, coercing errors to NaT
        parsed_dates = pd.to_datetime(
            self._dataframe["date"], errors="coerce", infer_datetime_format=True
        )

        now: datetime = datetime.now()

        for idx, (original, parsed) in enumerate(
            zip(self._dataframe["date"], parsed_dates)
        ):
            if pd.isna(original) or (isinstance(original, str) and original.strip() == ""):
                # Missing values are reported separately
                continue

            if pd.isna(parsed):
                error = ValidationError(
                    field="date",
                    message=(
                        f"Value '{original}' could not be parsed as a "
                        f"valid calendar date."
                    ),
                    row_index=idx,
                    value=original,
                )
                errors.append(error)
                logger.debug("Unparseable date at row %d: '%s'", idx, original)
                continue

            if not self._allow_future_dates and parsed > pd.Timestamp(now):
                error = ValidationError(
                    field="date",
                    message=(
                        f"Date '{parsed.date()}' is in the future "
                        f"(current time: {now.date()})."
                    ),
                    row_index=idx,
                    value=str(parsed.date()),
                )
                errors.append(error)
                logger.debug("Future date at row %d: %s", idx, parsed.date())

        if not errors:
            logger.info("Date validation passed. All dates are valid.")

        self._report.errors.extend(errors)
        return errors

    # ------------------------------------------------------------------
    # Time validation
    # ------------------------------------------------------------------

    def validate_time(self) -> List[ValidationError]:
        """
        Validate that the time column conforms to HH:MM:SS format.

        Acceptable formats before validation:
            - ``HH:MM:SS`` (24-hour with seconds)
            - ``HH:MM`` (24-hour without seconds, auto-appended)

        Returns:
            A list of ValidationError objects for invalid time values.
        """
        if self._dataframe is None:
            raise RuntimeError("No dataset loaded. Call load_dataset() first.")

        errors: List[ValidationError] = []

        if "time" not in self._dataframe.columns:
            logger.warning("Column 'time' not found. Skipping time validation.")
            return errors

        for idx, value in enumerate(self._dataframe["time"]):
            if pd.isna(value) or (isinstance(value, str) and value.strip() == ""):
                continue

            time_str: str = str(value).strip()

            # Try HH:MM:SS
            try:
                datetime.strptime(time_str, "%H:%M:%S")
                continue
            except (ValueError, TypeError):
                pass

            # Try HH:MM
            try:
                datetime.strptime(time_str, "%H:%M")
                continue
            except (ValueError, TypeError):
                pass

            # Try HHMMSS (6-digit compact)
            try:
                padded = time_str.zfill(6)
                datetime.strptime(padded, "%H%M%S")
                continue
            except (ValueError, TypeError):
                pass

            error = ValidationError(
                field="time",
                message=(
                    f"Value '{time_str}' does not match expected "
                    f"time format HH:MM:SS."
                ),
                row_index=idx,
                value=time_str,
            )
            errors.append(error)
            logger.debug("Invalid time at row %d: '%s'", idx, time_str)

        if not errors:
            logger.info("Time validation passed. All times are valid.")

        self._report.errors.extend(errors)
        return errors

    # ------------------------------------------------------------------
    # Category validation
    # ------------------------------------------------------------------

    def validate_categories(self) -> List[ValidationError]:
        """
        Verify that crime_type values belong to recognised categories.

        The comparison is case-insensitive. Values not in the predefined
        list are flagged as errors.

        Returns:
            A list of ValidationError objects for unrecognised categories.
        """
        if self._dataframe is None:
            raise RuntimeError("No dataset loaded. Call load_dataset() first.")

        errors: List[ValidationError] = []

        if "crime_type" not in self._dataframe.columns:
            logger.warning("Column 'crime_type' not found. Skipping category validation.")
            return errors

        # Build a lookup set (lowercase for case-insensitive comparison)
        category_lookup: set = {c.lower() for c in self._crime_categories}

        for idx, value in enumerate(self._dataframe["crime_type"]):
            if pd.isna(value) or (isinstance(value, str) and value.strip() == ""):
                continue

            category_str: str = str(value).strip().lower()

            if category_str not in category_lookup:
                error = ValidationError(
                    field="crime_type",
                    message=(
                        f"'{value}' is not a recognised crime category. "
                        f"Valid categories: {', '.join(self._crime_categories)}"
                    ),
                    row_index=idx,
                    value=value,
                )
                errors.append(error)
                logger.debug("Unknown category at row %d: '%s'", idx, value)

        if not errors:
            logger.info(
                "Category validation passed. All values are recognised."
            )

        self._report.errors.extend(errors)
        return errors

    # ------------------------------------------------------------------
    # Duplicate validation
    # ------------------------------------------------------------------

    def validate_duplicates(self) -> List[ValidationError]:
        """
        Identify duplicate crime_id values in the dataset.

        Returns:
            A list of ValidationError objects for duplicate IDs.
        """
        if self._dataframe is None:
            raise RuntimeError("No dataset loaded. Call load_dataset() first.")

        errors: List[ValidationError] = []

        if "crime_id" not in self._dataframe.columns:
            logger.warning("Column 'crime_id' not found. Skipping duplicate validation.")
            return errors

        # Find duplicated crime_id values (keep all occurrences)
        duplicated_mask = self._dataframe.duplicated(subset=["crime_id"], keep=False)
        duplicated_ids = self._dataframe.loc[duplicated_mask, "crime_id"]

        # Group duplicates for reporting
        dup_groups = duplicated_ids.value_counts()
        dup_groups = dup_groups[dup_groups > 1]

        for crime_id_val, count in dup_groups.items():
            # Find all row indices for this duplicate
            indices = self._dataframe.index[
                self._dataframe["crime_id"] == crime_id_val
            ].tolist()

            error = ValidationError(
                field="crime_id",
                message=(
                    f"Duplicate crime_id '{crime_id_val}' found "
                    f"in {count} rows: {indices}."
                ),
                value=str(crime_id_val),
            )
            errors.append(error)
            logger.warning(
                "Duplicate crime_id '%s' appears %d times.", crime_id_val, count
            )

        if not errors:
            logger.info("Duplicate validation passed. No duplicate crime_id values.")

        self._report.errors.extend(errors)
        return errors

    # ------------------------------------------------------------------
    # Missing value validation
    # ------------------------------------------------------------------

    def validate_missing_values(self) -> List[ValidationError]:
        """
        Report columns that still contain missing (null) values.

        This method does NOT fill or modify missing values — it only
        reports them.

        Returns:
            A list of ValidationError objects (as warnings) for columns
            with remaining missing values.
        """
        if self._dataframe is None:
            raise RuntimeError("No dataset loaded. Call load_dataset() first.")

        warnings: List[ValidationError] = []

        for col in self._dataframe.columns:
            missing_count: int = int(self._dataframe[col].isna().sum())
            if missing_count > 0:
                total: int = len(self._dataframe)
                pct: float = round(100.0 * missing_count / total, 2)

                warning = ValidationError(
                    field=col,
                    message=(
                        f"Column '{col}' has {missing_count} missing "
                        f"value(s) ({pct}% of {total} rows)."
                    ),
                )
                warnings.append(warning)
                logger.warning(
                    "Missing values: '%s' — %d / %d (%.2f%%)",
                    col,
                    missing_count,
                    total,
                    pct,
                )

        if not warnings:
            logger.info("No missing values found in any column.")

        self._report.warnings.extend(warnings)
        return warnings

    # ------------------------------------------------------------------
    # Report generation
    # ------------------------------------------------------------------

    def generate_validation_report(self) -> ValidationReport:
        """
        Finalise the validation report and persist it to the logs directory.

        The report is saved as a JSON file named
        ``validation_report_{dataset_name}_{timestamp}.json``.

        Returns:
            The fully populated ValidationReport instance.
        """
        # Determine overall status
        if self._report.errors:
            self._report.validation_status = "FAILED"
        elif self._report.warnings:
            self._report.validation_status = "WARNING"
        else:
            self._report.validation_status = "PASSED"

        # Persist to logs
        timestamp: str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        safe_name: str = self._report.dataset_name.replace(".", "_")
        report_filename: str = f"validation_report_{safe_name}_{timestamp}.json"
        report_path: Path = self._log_dir / report_filename

        with report_path.open("w", encoding="utf-8") as fh:
            json.dump(self._report.to_dict(), fh, indent=2, ensure_ascii=False)

        self._report.log_summary()
        logger.info("Validation report saved: %s", report_path)

        return self._report

    # ------------------------------------------------------------------
    # Main workflow
    # ------------------------------------------------------------------

    def run(self, input_file: str) -> ValidationReport:
        """
        Execute the complete validation workflow.

        Steps:
            1. Load the dataset.
            2. Validate required columns.
            3. Validate data types.
            4. Validate coordinates.
            5. Validate dates.
            6. Validate time format.
            7. Validate crime categories.
            8. Detect duplicates.
            9. Report missing values.
            10. Generate and persist the validation report.

        Args:
            input_file: Path to the processed dataset to validate.

        Returns:
            A ValidationReport with all errors, warnings, and status.
        """
        logger.info("=" * 60)
        logger.info("Validation run started for: %s", input_file)
        logger.info("=" * 60)

        # Reset report for this run
        self._report = ValidationReport()

        # Step 1: Load
        self.load_dataset(input_file)

        # Step 2: Required columns
        logger.info("--- Step 1/9: Required columns ---")
        self.validate_required_columns()

        # Step 3: Data types
        logger.info("--- Step 2/9: Data types ---")
        self.validate_data_types()

        # Step 4: Coordinates
        logger.info("--- Step 3/9: Coordinates ---")
        self.validate_coordinates()

        # Step 5: Dates
        logger.info("--- Step 4/9: Dates ---")
        self.validate_dates()

        # Step 6: Time format
        logger.info("--- Step 5/9: Time format ---")
        self.validate_time()

        # Step 7: Categories
        logger.info("--- Step 6/9: Crime categories ---")
        self.validate_categories()

        # Step 8: Duplicates
        logger.info("--- Step 7/9: Duplicates ---")
        self.validate_duplicates()

        # Step 9: Missing values
        logger.info("--- Step 8/9: Missing values ---")
        self.validate_missing_values()

        # Step 10: Report
        logger.info("--- Step 9/9: Generating report ---")
        report: ValidationReport = self.generate_validation_report()

        logger.info("=" * 60)
        logger.info("Validation complete. Status: %s", report.validation_status)
        logger.info("=" * 60)

        return report


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """
    CLI entry point for the data validator.

    Configures console logging, creates a DataValidator, and runs
    validation on a default processed dataset.

    Usage:
        python -m scripts.dataset_builder.validate_data
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[logging.StreamHandler()],
    )

    # Default input: look for the first CSV in data/processed/
    project_root: Path = Path(__file__).resolve().parents[2]
    processed_dir: Path = project_root / "data" / "processed"

    csv_files: List[Path] = list(processed_dir.glob("*.csv"))
    if csv_files:
        input_file: str = str(csv_files[0])
    else:
        logger.warning("No CSV found in data/processed/. Using placeholder.")
        input_file = str(processed_dir / "vellore_crime_clean.csv")

    validator: DataValidator = DataValidator()
    report: ValidationReport = validator.run(input_file)

    print(f"\nValidation complete for '{report.dataset_name}'.")
    print(f"  Status:  {report.validation_status}")
    print(f"  Errors:  {len(report.errors)}")
    print(f"  Warnings: {len(report.warnings)}")
    print(f"  Records:  {report.records_checked}")


if __name__ == "__main__":
    main()