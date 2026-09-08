"""
Tests for ml/risk_classifier.py.

Uses small synthetic feature matrices and labels.
Does not touch the production database.
"""

from __future__ import annotations

import os
import tempfile

import numpy as np
import pytest

from ml.feature_engineering import (
    ALL_INPUT_FEATURES,
    CrimeFeatureEngineer,
    build_features,
)
from ml.risk_classifier import (
    RiskClassifier,
    evaluate_classifier,
    train_test_split_data,
)


# ------------------------------------------------------------------ #
# Helpers
# ------------------------------------------------------------------ #


def _base_record(**overrides):
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


def _records_and_labels(n=20, seed=42):
    rng = np.random.default_rng(seed)
    records = []
    labels = []
    crime_types = ["Murder", "Theft", "Assault", "Burglary", "Fraud"]
    districts = ["Vellore", "Katpadi", "Pallikonda", "Gudiyatham", "Ranipet"]
    locations = ["Main Road", "Market", "Station", "Temple", "Bus Stand"]

    for i in range(n):
        records.append(
            _base_record(
                crime_type=crime_types[i % len(crime_types)],
                district=districts[i % len(districts)],
                location_name=locations[i % len(locations)],
                latitude=13.0 + rng.uniform(-0.1, 0.1),
                longitude=79.0 + rng.uniform(-0.1, 0.1),
                severity_score=int(rng.integers(1, 11)),
                crime_date=f"2025-{(i % 12) + 1:02d}-{(i % 28) + 1:02d}",
            )
        )
        labels.append("High" if i % 2 == 0 else "Low")

    return records, labels


def _engineered_features(records):
    engineer = CrimeFeatureEngineer()
    X = engineer.fit_transform(records)
    return X, engineer


# ------------------------------------------------------------------ #
# Training and prediction
# ------------------------------------------------------------------ #


class TestRiskClassifierTraining:
    def test_valid_training_with_two_classes(self):
        records, labels = _records_and_labels(n=20)
        X, _ = _engineered_features(records)

        classifier = RiskClassifier(random_state=42)
        classifier.fit(X, labels)

        assert classifier._fitted is True

    def test_prediction_works(self):
        records, labels = _records_and_labels(n=20)
        X, _ = _engineered_features(records)

        classifier = RiskClassifier(random_state=42)
        classifier.fit(X, labels)

        preds = classifier.predict(X)
        assert len(preds) == len(labels)
        assert set(preds).issubset({"High", "Low"})

    def test_predict_proba_works(self):
        records, labels = _records_and_labels(n=20)
        X, _ = _engineered_features(records)

        classifier = RiskClassifier(random_state=42)
        classifier.fit(X, labels)

        proba = classifier.predict_proba(X)
        assert proba.shape == (len(labels), 2)
        assert np.allclose(proba.sum(axis=1), 1.0)

    def test_score_returns_accuracy(self):
        records, labels = _records_and_labels(n=20)
        X, _ = _engineered_features(records)

        classifier = RiskClassifier(random_state=42)
        classifier.fit(X, labels)

        acc = classifier.score(X, labels)
        assert 0.0 <= acc <= 1.0

    def test_deterministic_random_state(self):
        records, labels = _records_and_labels(n=20)
        X, _ = _engineered_features(records)

        classifier1 = RiskClassifier(random_state=42)
        classifier1.fit(X, labels)
        preds1 = classifier1.predict(X)

        classifier2 = RiskClassifier(random_state=42)
        classifier2.fit(X, labels)
        preds2 = classifier2.predict(X)

        np.testing.assert_array_equal(preds1, preds2)

    def test_accepts_feature_engineering_output(self):
        records, labels = _records_and_labels(n=10)
        X, engineer = _engineered_features(records)

        classifier = RiskClassifier(random_state=42)
        classifier.fit(X, labels)

        new_records = [_base_record(crime_type="Theft")]
        X_new = engineer.transform(new_records)
        preds = classifier.predict(X_new)

        assert len(preds) == 1

    def test_input_data_not_unexpectedly_modified(self):
        records, labels = _records_and_labels(n=5)
        X, _ = _engineered_features(records)
        original_labels = list(labels)

        classifier = RiskClassifier(random_state=42)
        classifier.fit(X, labels)

        assert list(labels) == original_labels


# ------------------------------------------------------------------ #
# Input validation
# ------------------------------------------------------------------ #


class TestRiskClassifierValidation:
    def test_X_y_length_mismatch_raises(self):
        X = np.zeros((5, 2))
        y = np.array(["A", "B", "C"])

        classifier = RiskClassifier(random_state=42)
        with pytest.raises(ValueError, match="length mismatch"):
            classifier.fit(X, y)

    def test_missing_labels_raises(self):
        X = np.zeros((5, 2))
        y = None

        classifier = RiskClassifier(random_state=42)
        with pytest.raises(ValueError, match="y is empty"):
            classifier.fit(X, y)

    def test_single_class_training_raises(self):
        X = np.zeros((5, 2))
        y = np.array(["A", "A", "A", "A", "A"])

        classifier = RiskClassifier(random_state=42)
        with pytest.raises(ValueError, match="at least 2 classes"):
            classifier.fit(X, y)

    def test_empty_X_raises(self):
        X = np.empty((0, 2))
        y = np.array([])

        classifier = RiskClassifier(random_state=42)
        with pytest.raises(ValueError, match="X is empty"):
            classifier.fit(X, y)

    def test_predict_before_fit_raises(self):
        classifier = RiskClassifier(random_state=42)
        X = np.zeros((2, 2))

        with pytest.raises(RuntimeError, match="fit"):
            classifier.predict(X)

    def test_score_before_fit_raises(self):
        classifier = RiskClassifier(random_state=42)
        X = np.zeros((2, 2))
        y = np.array(["A", "B"])

        with pytest.raises(RuntimeError, match="fit"):
            classifier.score(X, y)

    def test_predict_wrong_feature_count_raises(self):
        records, labels = _records_and_labels(n=10)
        X, _ = _engineered_features(records)

        classifier = RiskClassifier(random_state=42)
        classifier.fit(X, labels)

        X_bad = np.zeros((2, 3))
        with pytest.raises(ValueError, match="features, expected"):
            classifier.predict(X_bad)

    def test_classes_before_fit_raises(self):
        classifier = RiskClassifier(random_state=42)
        with pytest.raises(RuntimeError, match="fit"):
            classifier.classes()


# ------------------------------------------------------------------ #
# Save / load
# ------------------------------------------------------------------ #


class TestRiskClassifierSaveLoad:
    def test_save_and_load(self):
        records, labels = _records_and_labels(n=20)
        X, _ = _engineered_features(records)

        classifier = RiskClassifier(random_state=42)
        classifier.fit(X, labels)
        preds_before = classifier.predict(X)

        with tempfile.NamedTemporaryFile(suffix=".joblib", delete=False) as f:
            path = f.name

        try:
            classifier.save(path)
            loaded = RiskClassifier.load(path)

            assert loaded._fitted is True
            np.testing.assert_array_equal(loaded.classes(), classifier.classes())
            preds_after = loaded.predict(X)
            np.testing.assert_array_equal(preds_before, preds_after)
        finally:
            os.remove(path)

    def test_save_unfitted_raises(self):
        classifier = RiskClassifier(random_state=42)
        with tempfile.NamedTemporaryFile(suffix=".joblib", delete=False) as f:
            path = f.name

        try:
            with pytest.raises(RuntimeError, match="Cannot save an unfitted"):
                classifier.save(path)
        finally:
            os.remove(path)


# ------------------------------------------------------------------ #
# Evaluation
# ------------------------------------------------------------------ #


class TestEvaluateClassifier:
    def test_evaluation_returns_expected_metrics(self):
        records, labels = _records_and_labels(n=30)
        X, _ = _engineered_features(records)

        classifier = RiskClassifier(random_state=42)
        classifier.fit(X, labels)

        results = evaluate_classifier(classifier, X, labels)

        assert "accuracy" in results
        assert "classification_report" in results
        assert "confusion_matrix" in results
        assert "labels" in results
        assert 0.0 <= results["accuracy"] <= 1.0
        assert len(results["confusion_matrix"]) == len(results["labels"])


# ------------------------------------------------------------------ #
# Train/test split
# ------------------------------------------------------------------ #


class TestTrainTestSplit:
    def test_split_shapes(self):
        X = np.random.default_rng(42).random((20, 2))
        y = np.array(["A", "B"] * 10)

        X_train, X_test, y_train, y_test = train_test_split_data(
            X, y, test_size=0.3, random_state=42
        )

        assert len(X_train) + len(X_test) == 20
        assert len(y_train) + len(y_test) == 20

    def test_too_small_dataset_raises(self):
        X = np.zeros((1, 2))
        y = np.array(["A"])

        with pytest.raises(ValueError, match="too small to split"):
            train_test_split_data(X, y)

    def test_invalid_test_size_raises(self):
        X = np.zeros((5, 2))
        y = np.array(["A", "B", "A", "B", "A"])

        with pytest.raises(ValueError, match="test_size must be in"):
            train_test_split_data(X, y, test_size=1.5)

    def test_stratification_fails_on_single_sample_class(self):
        X = np.zeros((4, 2))
        y = np.array(["A", "A", "A", "B"])

        with pytest.raises(ValueError, match="fewer than 2 samples"):
            train_test_split_data(X, y, stratify=True)

    def test_deterministic_random_state(self):
        X = np.random.default_rng(42).random((20, 2))
        y = np.array(["A", "B"] * 10)

        split1 = train_test_split_data(X, y, test_size=0.3, random_state=42)
        split2 = train_test_split_data(X, y, test_size=0.3, random_state=42)

        for arr1, arr2 in zip(split1, split2):
            np.testing.assert_array_equal(arr1, arr2)


# ------------------------------------------------------------------ #
# Feature leakage protection
# ------------------------------------------------------------------ #


class TestFeatureLeakageProtection:
    def test_risk_level_not_in_feature_engineering_output(self):
        records = [_base_record(risk_level="High")]
        df = build_features(records)
        assert "risk_level" not in df.columns

    def test_severity_score_in_feature_engineering_by_design(self):
        records = [_base_record(severity_score=5)]
        df = build_features(records)
        assert "severity_score" in df.columns

    def test_input_records_not_modified_by_feature_engineering(self):
        record = _base_record(risk_level="High")
        original_keys = set(record.keys())
        build_features([record])
        assert set(record.keys()) == original_keys
