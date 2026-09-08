"""
Tests for ml/feature_engineering.py.

Uses small synthetic crime records. Does not touch the production
database.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from ml.feature_engineering import (
    CATEGORICAL_FEATURES,
    NUMERICAL_FEATURES,
    ALL_INPUT_FEATURES,
    CrimeFeatureEngineer,
    build_features,
    _extract_coordinates,
    _extract_date_features,
    _extract_severity_score,
    _records_to_dataframe,
)


# ------------------------------------------------------------------ #
# Helpers
# ------------------------------------------------------------------ #


def _base_record(**overrides):
    """A complete, valid crime record."""
    record = {
        "crime_type": "Murder",
        "district": "Vellore",
        "location_name": "Katpadi",
        "latitude": 13.043505,
        "longitude": 79.240410,
        "severity_score": 5,
        "crime_date": "2025-06-12",
    }
    record.update(overrides)
    return record


# ------------------------------------------------------------------ #
# Unit tests for internal helpers
# ------------------------------------------------------------------ #


class TestExtractCoordinates:
    def test_valid_coordinates_preserved(self):
        result = _extract_coordinates({"latitude": 13.0, "longitude": 79.0})
        assert result == {"latitude": 13.0, "longitude": 79.0}

    def test_none_when_missing(self):
        result = _extract_coordinates({})
        assert result == {"latitude": None, "longitude": None}

    def test_null_latitude(self):
        result = _extract_coordinates({"latitude": None, "longitude": 79.0})
        assert result["latitude"] is None
        assert result["longitude"] == 79.0

    def test_non_numeric_coordinates_become_none(self):
        result = _extract_coordinates({"latitude": "abc", "longitude": "xyz"})
        assert result == {"latitude": None, "longitude": None}

    def test_invalid_latitude_clamped_to_none(self):
        result = _extract_coordinates({"latitude": 999.0, "longitude": 79.0})
        assert result["latitude"] is None
        assert result["longitude"] == 79.0

    def test_invalid_longitude_clamped_to_none(self):
        result = _extract_coordinates({"latitude": 13.0, "longitude": -999.0})
        assert result["latitude"] == 13.0
        assert result["longitude"] is None

    def test_boundary_latitude_valid(self):
        result = _extract_coordinates({"latitude": 90.0, "longitude": 0.0})
        assert result["latitude"] == 90.0

    def test_boundary_longitude_valid(self):
        result = _extract_coordinates({"latitude": 0.0, "longitude": 180.0})
        assert result["longitude"] == 180.0


class TestExtractSeverityScore:
    def test_valid_integer_preserved(self):
        assert _extract_severity_score({"severity_score": 5}) == 5

    def test_string_integer_coerced(self):
        assert _extract_severity_score({"severity_score": "8"}) == 8

    def test_none_returns_none(self):
        assert _extract_severity_score({}) is None

    def test_non_numeric_returns_none(self):
        assert _extract_severity_score({"severity_score": "high"}) is None

    def test_float_coerced_to_int(self):
        assert _extract_severity_score({"severity_score": 7.0}) == 7


class TestExtractDateFeatures:
    def test_valid_date_extracts_month_and_weekday(self):
        result = _extract_date_features({"crime_date": "2025-06-12"})
        assert result["crime_month"] == 6
        assert result["crime_day_of_week"] == 3  # Thursday

    def test_missing_date_returns_none(self):
        result = _extract_date_features({})
        assert result == {"crime_month": None, "crime_day_of_week": None}

    def test_invalid_date_returns_none(self):
        result = _extract_date_features({"crime_date": "not-a-date"})
        assert result == {"crime_month": None, "crime_day_of_week": None}

    def test_iso_datetime_parsed(self):
        result = _extract_date_features({"crime_date": "2025-06-12T10:30:00"})
        assert result["crime_month"] == 6
        assert result["crime_day_of_week"] == 3

    def test_rfc1123_date_parsed(self):
        result = _extract_date_features(
            {"crime_date": "Thu, 12 Jun 2025 10:30:00 GMT"}
        )
        assert result["crime_month"] == 6
        assert result["crime_day_of_week"] == 3


class TestRecordsToDataFrame:
    def test_output_shape_matches_features(self):
        records = [_base_record()]
        df = _records_to_dataframe(records)
        assert list(df.columns) == ALL_INPUT_FEATURES
        assert len(df) == 1

    def test_non_dict_record_skipped(self):
        records = [_base_record(), "not-a-dict", None]
        df = _records_to_dataframe(records)
        assert len(df) == 1

    def test_input_records_not_modified(self):
        record = _base_record()
        original_keys = set(record.keys())
        _records_to_dataframe([record])
        assert set(record.keys()) == original_keys

    def test_nulls_preserved_as_nan(self):
        record = _base_record(latitude=None, longitude=None, severity_score=None, crime_date=None)
        df = _records_to_dataframe([record])
        assert pd.isna(df.loc[0, "latitude"])
        assert pd.isna(df.loc[0, "longitude"])
        assert pd.isna(df.loc[0, "severity_score"])
        assert pd.isna(df.loc[0, "crime_month"])
        assert pd.isna(df.loc[0, "crime_day_of_week"])


# ------------------------------------------------------------------ #
# Unit tests for build_features
# ------------------------------------------------------------------ #


class TestBuildFeatures:
    def test_valid_record_produces_dataframe(self):
        df = build_features([_base_record()])
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 1

    def test_numerical_features_present(self):
        df = build_features([_base_record()])
        for feature in NUMERICAL_FEATURES:
            assert feature in df.columns

    def test_categorical_columns_encoded(self):
        df = build_features([_base_record()])
        assert "crime_type_Murder" in df.columns
        assert "district_Vellore" in df.columns
        assert "location_name_Katpadi" in df.columns

    def test_no_raw_string_categorical_columns(self):
        df = build_features([_base_record()])
        for feature in CATEGORICAL_FEATURES:
            assert feature not in df.columns

    def test_multiple_crime_types_create_multiple_columns(self):
        records = [_base_record(crime_type="Murder"), _base_record(crime_type="Theft")]
        df = build_features(records)
        assert "crime_type_Murder" in df.columns
        assert "crime_type_Theft" in df.columns
        assert len(df) == 2

    def test_missing_coordinates_do_not_crash(self):
        records = [_base_record(latitude=None, longitude=None)]
        df = build_features(records)
        assert len(df) == 1

    def test_invalid_coordinates_do_not_crash(self):
        records = [_base_record(latitude=999.0, longitude=999.0)]
        df = build_features(records)
        assert len(df) == 1

    def test_missing_severity_score_does_not_crash(self):
        records = [_base_record(severity_score=None)]
        df = build_features(records)
        assert len(df) == 1
        assert pd.isna(df.loc[0, "severity_score"])

    def test_invalid_date_does_not_crash(self):
        records = [_base_record(crime_date="not-a-date")]
        df = build_features(records)
        assert len(df) == 1
        assert pd.isna(df.loc[0, "crime_month"])
        assert pd.isna(df.loc[0, "crime_day_of_week"])

    def test_input_records_not_modified(self):
        record = _base_record()
        original_keys = set(record.keys())
        build_features([record])
        assert set(record.keys()) == original_keys

    def test_empty_records_returns_empty_dataframe(self):
        df = build_features([])
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0


# ------------------------------------------------------------------ #
# Unit tests for CrimeFeatureEngineer
# ------------------------------------------------------------------ #


class TestCrimeFeatureEngineer:
    def test_fit_transform_returns_array(self):
        engineer = CrimeFeatureEngineer()
        records = [_base_record()]
        X = engineer.fit_transform(records)
        assert isinstance(X, np.ndarray)
        assert X.shape == (1, len(engineer.get_feature_names()))

    def test_feature_names_populated_after_fit(self):
        engineer = CrimeFeatureEngineer()
        engineer.fit([_base_record()])
        names = engineer.get_feature_names()
        assert len(names) > 0
        assert "latitude" in names
        assert "longitude" in names
        assert "severity_score" in names
        assert "crime_month" in names
        assert "crime_day_of_week" in names
        assert "crime_type_Murder" in names

    def test_transform_after_fit(self):
        engineer = CrimeFeatureEngineer()
        train = [_base_record(crime_type="Murder"), _base_record(crime_type="Theft")]
        engineer.fit(train)

        test_records = [_base_record(crime_type="Murder")]
        X = engineer.transform(test_records)

        assert X.shape == (1, len(engineer.get_feature_names()))

    def test_transform_requires_fit(self):
        engineer = CrimeFeatureEngineer()
        with pytest.raises(RuntimeError):
            engineer.transform([_base_record()])

    def test_fit_requires_non_empty(self):
        engineer = CrimeFeatureEngineer()
        with pytest.raises(ValueError):
            engineer.fit([])

    def test_get_feature_names_requires_fit(self):
        engineer = CrimeFeatureEngineer()
        with pytest.raises(RuntimeError):
            engineer.get_feature_names()

    def test_empty_transform_returns_empty_array(self):
        engineer = CrimeFeatureEngineer()
        engineer.fit([_base_record()])
        X = engineer.transform([])
        assert X.shape == (0, len(engineer.get_feature_names()))

    def test_unknown_category_does_not_crash(self):
        engineer = CrimeFeatureEngineer()
        train = [_base_record(crime_type="Murder")]
        engineer.fit(train)

        test_records = [_base_record(crime_type="UnknownType")]
        X = engineer.transform(test_records)

        assert X.shape == (1, len(engineer.get_feature_names()))

    def test_missing_coordinates_handled(self):
        engineer = CrimeFeatureEngineer()
        records = [_base_record(latitude=None, longitude=None)]
        engineer.fit(records)
        X = engineer.transform(records)
        assert X.shape == (1, len(engineer.get_feature_names()))

    def test_invalid_coordinates_handled(self):
        engineer = CrimeFeatureEngineer()
        records = [_base_record(latitude=999.0, longitude=999.0)]
        engineer.fit(records)
        X = engineer.transform(records)
        assert X.shape == (1, len(engineer.get_feature_names()))

    def test_missing_severity_score_handled(self):
        engineer = CrimeFeatureEngineer()
        records = [_base_record(severity_score=None)]
        engineer.fit(records)
        X = engineer.transform(records)
        assert X.shape == (1, len(engineer.get_feature_names()))

    def test_invalid_date_does_not_crash(self):
        engineer = CrimeFeatureEngineer()
        records = [_base_record(crime_date="not-a-date")]
        engineer.fit(records)
        X = engineer.transform(records)
        assert X.shape == (1, len(engineer.get_feature_names()))

    def test_repeated_fit_produces_consistent_structure(self):
        engineer = CrimeFeatureEngineer()
        records = [_base_record(), _base_record(crime_type="Theft")]
        engineer.fit(records)

        X1 = engineer.transform(records)
        names1 = engineer.get_feature_names()

        engineer2 = CrimeFeatureEngineer()
        engineer2.fit(records)
        X2 = engineer2.transform(records)
        names2 = engineer2.get_feature_names()

        assert X1.shape == X2.shape
        assert names1 == names2

    def test_output_is_numeric(self):
        engineer = CrimeFeatureEngineer()
        records = [_base_record()]
        X = engineer.fit_transform(records)
        assert X.dtype in (np.float32, np.float64, np.int64, np.int32)

    def test_input_records_not_modified(self):
        record = _base_record()
        original_keys = set(record.keys())
        engineer = CrimeFeatureEngineer()
        engineer.fit_transform([record])
        assert set(record.keys()) == original_keys

    def test_multiple_locations_encoded(self):
        engineer = CrimeFeatureEngineer()
        records = [
            _base_record(location_name="Katpadi"),
            _base_record(location_name="Vellore"),
            _base_record(location_name="Pallikonda"),
        ]
        engineer.fit(records)
        names = engineer.get_feature_names()
        assert "location_name_Katpadi" in names
        assert "location_name_Vellore" in names
        assert "location_name_Pallikonda" in names
