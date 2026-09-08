"""
Tests for ml/temporal_analysis.py.

Uses small synthetic records. Does not touch the production
database.
"""

from __future__ import annotations

import pytest

from ml.temporal_analysis import (
    analyze_temporal_patterns,
    get_day_of_week_counts,
    get_monthly_crime_counts,
    get_yearly_crime_counts,
)


# ------------------------------------------------------------------ #
# Helpers
# ------------------------------------------------------------------ #


def _record(date, crime_type="Theft"):
    return {
        "crime_type": crime_type,
        "crime_date": date,
    }


# ------------------------------------------------------------------ #
# Unit tests for analyze_temporal_patterns
# ------------------------------------------------------------------ #


class TestAnalyzeTemporalPatterns:
    def test_empty_records(self):
        result = analyze_temporal_patterns([])
        assert result["total_records"] == 0
        assert result["valid_dates"] == 0
        assert result["invalid_dates"] == 0
        assert result["monthly_counts"] == {}

    def test_valid_dates_counted(self):
        records = [
            _record("2025-01-15"),
            _record("2025-01-20"),
            _record("2025-02-10"),
        ]
        result = analyze_temporal_patterns(records)
        assert result["valid_dates"] == 3
        assert result["invalid_dates"] == 0
        assert result["monthly_counts"]["2025-01"] == 2
        assert result["monthly_counts"]["2025-02"] == 1

    def test_invalid_dates_excluded(self):
        records = [
            _record("2025-01-15"),
            _record("not-a-date"),
            _record(""),
            _record(None),
        ]
        result = analyze_temporal_patterns(records)
        assert result["valid_dates"] == 1
        assert result["invalid_dates"] == 3

    def test_excluded_dates_count(self):
        records = [_record("bad-date")]
        result = analyze_temporal_patterns(records)
        assert result["excluded_dates"] == 1

    def test_date_range_detected(self):
        records = [
            _record("2025-01-15"),
            _record("2025-06-20"),
        ]
        result = analyze_temporal_patterns(records)
        assert result["date_range"] == {
            "start": "2025-01-15",
            "end": "2025-06-20",
        }

    def test_yearly_counts(self):
        records = [
            _record("2024-03-10"),
            _record("2024-07-15"),
            _record("2025-01-05"),
        ]
        result = analyze_temporal_patterns(records)
        assert result["yearly_counts"]["2024"] == 2
        assert result["yearly_counts"]["2025"] == 1

    def test_day_of_week_counts(self):
        records = [
            _record("2025-01-05"),  # Sunday
            _record("2025-01-06"),  # Monday
            _record("2025-01-05"),  # Sunday again
        ]
        result = analyze_temporal_patterns(records)
        assert result["day_of_week_counts"]["Sunday"] == 2
        assert result["day_of_week_counts"]["Monday"] == 1

    def test_crime_type_monthly(self):
        records = [
            _record("2025-01-15", crime_type="Murder"),
            _record("2025-01-20", crime_type="Theft"),
            _record("2025-01-25", crime_type="Murder"),
        ]
        result = analyze_temporal_patterns(records)
        assert result["crime_type_monthly"]["Murder"]["2025-01"] == 2
        assert result["crime_type_monthly"]["Theft"]["2025-01"] == 1

    def test_custom_date_field(self):
        records = [
            {"custom_date": "2025-03-10"},
        ]
        result = analyze_temporal_patterns(records, date_field="custom_date")
        assert result["valid_dates"] == 1
        assert result["monthly_counts"]["2025-03"] == 1

    def test_limitations_present(self):
        result = analyze_temporal_patterns([_record("2025-01-01")])
        assert "publication-date" in result["limitations"]
        assert "not verified" in result["limitations"]

    def test_missing_date_field(self):
        records = [{"crime_type": "Theft"}]
        result = analyze_temporal_patterns(records)
        assert result["valid_dates"] == 0
        assert result["invalid_dates"] == 1


# ------------------------------------------------------------------ #
# Unit tests for convenience wrappers
# ------------------------------------------------------------------ #


class TestConvenienceWrappers:
    def test_get_monthly_crime_counts(self):
        records = [
            _record("2025-01-15"),
            _record("2025-01-20"),
        ]
        result = get_monthly_crime_counts(records)
        assert result["2025-01"] == 2

    def test_get_yearly_crime_counts(self):
        records = [
            _record("2024-06-15"),
            _record("2025-06-15"),
        ]
        result = get_yearly_crime_counts(records)
        assert result["2024"] == 1
        assert result["2025"] == 1

    def test_get_day_of_week_counts(self):
        records = [
            _record("2025-01-05"),  # Sunday
        ]
        result = get_day_of_week_counts(records)
        assert result["Sunday"] == 1
