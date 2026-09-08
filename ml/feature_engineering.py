"""
Feature engineering for crime risk classification.

Converts raw Crime records into ML-ready numerical features
without coupling to Flask or the production database.

Numerical features:
    latitude, longitude, severity_score, crime_month, crime_day_of_week

Categorical features:
    crime_type, district, location_name

Missing-data strategy:
    * Missing/invalid coordinates are left as NaN and imputed
      with the training median during fit.
    * Missing severity_score is left as NaN and imputed with
      the training median during fit.
    * Missing/invalid dates yield NaN month/day_of_week and are
      imputed with the training median during fit.
    * Missing categoricals are imputed with the most frequent
      training value and one-hot encoded; unknown categories at
      inference time are ignored (all-zero vector).

This module does NOT train any classifier and does NOT fabricate
training labels.
"""

from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


NUMERICAL_FEATURES = [
    "latitude",
    "longitude",
    "severity_score",
    "crime_month",
    "crime_day_of_week",
]

CATEGORICAL_FEATURES = [
    "crime_type",
    "district",
    "location_name",
]

ALL_INPUT_FEATURES = NUMERICAL_FEATURES + CATEGORICAL_FEATURES


def _parse_date(raw: Any) -> Optional[pd.Timestamp]:
    """Parse a date string into a pandas Timestamp, or None on failure."""
    if raw is None:
        return None

    text = str(raw).strip()

    if not text:
        return None

    try:
        parsed = pd.to_datetime(text, errors="coerce")

        if parsed is None or pd.isna(parsed):
            return None

        return parsed
    except Exception:
        return None


def _safe_float(value: Any) -> Optional[float]:
    """Convert a value to float, returning None on failure."""
    if value is None:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _extract_coordinates(record: Dict[str, Any]) -> Dict[str, Optional[float]]:
    """Extract latitude/longitude and validate their geographic ranges."""
    latitude = _safe_float(record.get("latitude"))
    longitude = _safe_float(record.get("longitude"))

    if latitude is not None and not -90.0 <= latitude <= 90.0:
        latitude = None

    if longitude is not None and not -180.0 <= longitude <= 180.0:
        longitude = None

    return {
        "latitude": latitude,
        "longitude": longitude,
    }


def _extract_severity_score(record: Dict[str, Any]) -> Optional[int]:
    """Extract severity_score as an integer, or None if missing/invalid."""
    value = record.get("severity_score")

    if value is None:
        return None

    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _extract_date_features(record: Dict[str, Any]) -> Dict[str, Optional[int]]:
    """Extract month and day_of_week from crime_date."""
    parsed = _parse_date(record.get("crime_date"))

    if parsed is None:
        return {
            "crime_month": None,
            "crime_day_of_week": None,
        }

    return {
        "crime_month": int(parsed.month),
        "crime_day_of_week": int(parsed.weekday()),
    }


def _records_to_dataframe(records: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Convert a list of Crime dicts into a DataFrame with engineered
    feature columns. Input records are not modified.
    """
    rows = []

    for record in records:
        if not isinstance(record, dict):
            continue

        row = {}

        row.update(_extract_coordinates(record))
        row["severity_score"] = _extract_severity_score(record)
        row.update(_extract_date_features(record))
        row["crime_type"] = record.get("crime_type")
        row["district"] = record.get("district")
        row["location_name"] = record.get("location_name")

        rows.append(row)

    return pd.DataFrame(rows, columns=ALL_INPUT_FEATURES)


class CrimeFeatureEngineer:
    """
    Sklearn-compatible feature engineer for crime records.

    Provides fit/transform semantics so training data can fit the
    preprocessing state and inference data can be transformed with
    the same encoders/imputers.

    Example:
        engineer = CrimeFeatureEngineer()
        X_train = engineer.fit_transform(train_records)
        X_test = engineer.transform(test_records)
        names = engineer.get_feature_names()
    """

    def __init__(self) -> None:
        self._preprocessor: Optional[ColumnTransformer] = None
        self._feature_names: Optional[List[str]] = None
        self._fitted: bool = False

    def _build_preprocessor(self) -> ColumnTransformer:
        """Construct an unfitted sklearn ColumnTransformer."""
        numerical_pipeline = SimpleImputer(strategy="median")

        categorical_pipeline = Pipeline(
            steps=[
                ("imputer", SimpleImputer(strategy="most_frequent")),
                (
                    "onehot",
                    OneHotEncoder(
                        handle_unknown="ignore",
                        sparse_output=False,
                    ),
                ),
            ]
        )

        return ColumnTransformer(
            transformers=[
                ("num", numerical_pipeline, NUMERICAL_FEATURES),
                ("cat", categorical_pipeline, CATEGORICAL_FEATURES),
            ],
            remainder="drop",
        )

    def fit(self, records: List[Dict[str, Any]]) -> "CrimeFeatureEngineer":
        """
        Fit preprocessing state on crime records.

        Args:
            records: Non-empty list of Crime dicts.

        Returns:
            self
        """
        if not records:
            raise ValueError("Cannot fit on empty records")

        df = _records_to_dataframe(records)
        self._preprocessor = self._build_preprocessor()
        self._preprocessor.fit(df[ALL_INPUT_FEATURES])
        self._fitted = True
        self._feature_names = self._get_feature_names()

        return self

    def transform(self, records: List[Dict[str, Any]]) -> np.ndarray:
        """
        Transform crime records into a numeric feature matrix.

        Args:
            records: List of Crime dicts.

        Returns:
            numpy.ndarray of shape (n_records, n_features)
        """
        if not self._fitted:
            raise RuntimeError("fit() must be called before transform()")

        if not records:
            return np.empty((0, len(self._feature_names)))

        df = _records_to_dataframe(records)
        return self._preprocessor.transform(df[ALL_INPUT_FEATURES])

    def fit_transform(self, records: List[Dict[str, Any]]) -> np.ndarray:
        """
        Fit preprocessing and transform records in one step.

        Args:
            records: Non-empty list of Crime dicts.

        Returns:
            numpy.ndarray of shape (n_records, n_features)
        """
        self.fit(records)
        return self.transform(records)

    def get_feature_names(self) -> List[str]:
        """Return ordered feature names produced by transform."""
        if not self._fitted:
            raise RuntimeError("fit() must be called before get_feature_names()")

        return list(self._feature_names)

    def _get_feature_names(self) -> List[str]:
        """Build deterministic feature names from the fitted transformer."""
        raw_names = self._preprocessor.get_feature_names_out()

        names = []

        for raw in raw_names:
            name = str(raw)

            if name.startswith("num__"):
                names.append(name[len("num__"):])
            elif name.startswith("cat__"):
                names.append(name[len("cat__"):])
            else:
                names.append(name)

        return names


def build_features(records: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Quick one-shot feature builder for prototyping.

    Produces a DataFrame with numerical columns plus one-hot encoded
    categorical columns. Missing categoricals are dropped by
    get_dummies; missing numericals remain as NaN.

    For production training/prediction pipelines, prefer
    ``CrimeFeatureEngineer`` because it preserves fit state across
    train/test splits.

    Args:
        records: List of Crime dicts.

    Returns:
        pd.DataFrame with engineered features.
    """
    df = _records_to_dataframe(records)

    for feature in CATEGORICAL_FEATURES:
        dummies = pd.get_dummies(df[feature], prefix=feature, dummy_na=False)
        df = pd.concat([df.drop(columns=[feature]), dummies], axis=1)

    return df
