"""
Tests for ml/crime_pattern_analysis.py.

Uses small synthetic records. Does not touch the production
database.
"""

from __future__ import annotations

import pytest

from ml.crime_pattern_analysis import (
    analyze_crime_patterns,
    get_crime_type_distribution,
    get_risk_level_distribution,
    get_severity_distribution,
)


# ------------------------------------------------------------------ #
# Helpers
# ------------------------------------------------------------------ #


def _record(**overrides):
    base = {
        "crime_type": "Theft",
        "severity_score": 5,
        "risk_level": "Medium",
        "location_name": "Vellore",
        "district": "Vellore",
    }
    base.update(overrides)
    return base


# ------------------------------------------------------------------ #
# Unit tests for analyze_crime_patterns
# ------------------------------------------------------------------ #


class TestAnalyzeCrimePatterns:
    def test_empty_records(self):
        result = analyze_crime_patterns([])
        assert result["total_records"] == 0
        assert result["crime_type_distribution"] == {}

    def test_crime_type_distribution(self):
        records = [
            _record(crime_type="Murder"),
            _record(crime_type="Murder"),
            _record(crime_type="Theft"),
        ]
        result = analyze_crime_patterns(records)
        assert result["crime_type_distribution"]["Murder"] == 2
        assert result["crime_type_distribution"]["Theft"] == 1

    def test_severity_distribution(self):
        records = [
            _record(severity_score=10),
            _record(severity_score=10),
            _record(severity_score=5),
        ]
        result = analyze_crime_patterns(records)
        assert result["severity_score_distribution"][10] == 2
        assert result["severity_score_distribution"][5] == 1

    def test_risk_level_distribution(self):
        records = [
            _record(risk_level="Critical"),
            _record(risk_level="High"),
            _record(risk_level="Critical"),
        ]
        result = analyze_crime_patterns(records)
        assert result["risk_level_distribution"]["Critical"] == 2
        assert result["risk_level_distribution"]["High"] == 1

    def test_location_distribution(self):
        records = [
            _record(location_name="A"),
            _record(location_name="A"),
            _record(location_name="B"),
        ]
        result = analyze_crime_patterns(records)
        assert result["location_distribution"]["A"] == 2
        assert result["location_distribution"]["B"] == 1

    def test_district_distribution(self):
        records = [
            _record(district="Vellore"),
            _record(district="Katpadi"),
            _record(district="Vellore"),
        ]
        result = analyze_crime_patterns(records)
        assert result["district_distribution"]["Vellore"] == 2
        assert result["district_distribution"]["Katpadi"] == 1

    def test_dominant_crime_types(self):
        records = [
            _record(crime_type="Murder"),
            _record(crime_type="Theft"),
            _record(crime_type="Murder"),
        ]
        result = analyze_crime_patterns(records)
        assert result["dominant_crime_types"][0]["crime_type"] == "Murder"
        assert result["dominant_crime_types"][0]["count"] == 2

    def test_missing_fields_ignored(self):
        records = [
            {"crime_type": "Theft"},
            {"crime_type": "Murder", "severity_score": None, "risk_level": None},
        ]
        result = analyze_crime_patterns(records)
        assert result["crime_type_distribution"]["Theft"] == 1
        assert result["crime_type_distribution"]["Murder"] == 1
        assert result["severity_score_distribution"] == {}
        assert result["risk_level_distribution"] == {}

    def test_limitations_present(self):
        result = analyze_crime_patterns([_record()])
        assert "rule-derived" in result["limitations"]

    def test_total_records_matches_input(self):
        records = [_record() for _ in range(7)]
        result = analyze_crime_patterns(records)
        assert result["total_records"] == 7


# ------------------------------------------------------------------ #
# Unit tests for convenience wrappers
# ------------------------------------------------------------------ #


class TestConvenienceWrappers:
    def test_get_crime_type_distribution(self):
        records = [_record(crime_type="Murder"), _record(crime_type="Theft")]
        result = get_crime_type_distribution(records)
        assert result["Murder"] == 1
        assert result["Theft"] == 1

    def test_get_severity_distribution(self):
        records = [_record(severity_score=10), _record(severity_score=5)]
        result = get_severity_distribution(records)
        assert result[10] == 1
        assert result[5] == 1

    def test_get_risk_level_distribution(self):
        records = [_record(risk_level="High"), _record(risk_level="Low")]
        result = get_risk_level_distribution(records)
        assert result["High"] == 1
        assert result["Low"] == 1
