"""
Tests for backend/services/statistics_service.py.
"""

import pytest

from services.statistics_service import (
    _extract_month,
    build_statistics,
)


class TestExtractMonth:
    """Month extraction from crime_date strings."""

    def test_iso_date(self):
        assert _extract_month("2025-03-11") == "2025-03"

    def test_iso_month_only(self):
        assert _extract_month("2025-03") == "2025-03"

    def test_dd_month_yyyy_lowercase(self):
        assert _extract_month("31 July 2026") == "2026-07"

    def test_dd_month_yyyy_capitalized(self):
        assert _extract_month("17 May 2026") == "2026-05"

    def test_dd_month_yyyy_march(self):
        assert _extract_month("15 March 2025") == "2025-03"

    def test_dd_mon_yyyy_abbreviated(self):
        assert _extract_month("01 Jan 2024") == "2024-01"

    def test_invalid_date_returns_unknown(self):
        assert _extract_month("not-a-date") == "Unknown"

    def test_empty_string_returns_unknown(self):
        assert _extract_month("") == "Unknown"

    def test_none_returns_unknown(self):
        assert _extract_month(None) == "Unknown"

    def test_whitespace_only_returns_unknown(self):
        assert _extract_month("   ") == "Unknown"

    def test_single_digit_day_with_padded_month(self):
        assert _extract_month("1 August 2025") == "2025-08"


class TestBuildStatistics:
    """Aggregate statistics from crime records."""

    def test_empty_records(self):
        result = build_statistics([])
        assert result["total_crimes"] == 0
        assert result["by_type"] == {}
        assert result["by_severity"] == {}
        assert result["by_area"] == {}
        assert result["by_month"] == {}

    def test_basic_counts(self):
        crimes = [
            {
                "crime_type": "Theft",
                "severity": "Low",
                "location_name": "Katpadi",
                "crime_date": "2025-03-11",
            },
            {
                "crime_type": "Theft",
                "severity": "Medium",
                "location_name": "Katpadi",
                "crime_date": "2025-03-12",
            },
            {
                "crime_type": "Assault",
                "severity": "High",
                "location_name": "Vellore",
                "crime_date": "2025-04-01",
            },
        ]
        result = build_statistics(crimes)

        assert result["total_crimes"] == 3
        assert result["by_type"]["Theft"] == 2
        assert result["by_type"]["Assault"] == 1
        assert result["by_severity"]["Low"] == 1
        assert result["by_severity"]["Medium"] == 1
        assert result["by_severity"]["High"] == 1
        assert result["by_area"]["Katpadi"] == 2
        assert result["by_area"]["Vellore"] == 1
        assert result["by_month"]["2025-03"] == 2
        assert result["by_month"]["2025-04"] == 1

    def test_non_iso_dates_are_parsed(self):
        crimes = [
            {
                "crime_type": "Theft",
                "severity": "Low",
                "location_name": "Vellore",
                "crime_date": "31 July 2026",
            },
            {
                "crime_type": "Assault",
                "severity": "High",
                "location_name": "Vellore",
                "crime_date": "17 May 2026",
            },
        ]
        result = build_statistics(crimes)

        assert result["by_month"]["2026-07"] == 1
        assert result["by_month"]["2026-05"] == 1

    def test_invalid_dates_become_unknown(self):
        crimes = [
            {
                "crime_type": "Theft",
                "severity": "Low",
                "location_name": "Vellore",
                "crime_date": "not-a-date",
            }
        ]
        result = build_statistics(crimes)

        assert result["by_month"]["Unknown"] == 1

    def test_missing_fields_default_to_unknown(self):
        crimes = [
            {
                "crime_type": "Theft",
                "severity": None,
                "location_name": None,
                "crime_date": None,
            }
        ]
        result = build_statistics(crimes)

        assert result["by_severity"]["Unknown"] == 1
        assert result["by_area"]["Unknown"] == 1
        assert result["by_month"]["Unknown"] == 1

    def test_month_sorting_keeps_unknown_last(self):
        crimes = [
            {
                "crime_type": "Theft",
                "severity": "Low",
                "location_name": "Vellore",
                "crime_date": "2025-01-01",
            },
            {
                "crime_type": "Assault",
                "severity": "High",
                "location_name": "Vellore",
                "crime_date": "invalid",
            },
        ]
        result = build_statistics(crimes)

        keys = list(result["by_month"].keys())
        assert keys[-1] == "Unknown"
        assert keys[0] == "2025-01"
