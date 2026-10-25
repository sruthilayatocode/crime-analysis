"""
Risk classifier for crime records.

Wraps a scikit-learn classifier and exposes a clean, reusable API
that operates on feature matrices produced by
``ml.feature_engineering.CrimeFeatureEngineer``.

Label source and leakage protection
-----------------------------------
- The production ``Crime.risk_level`` column is populated from
  ``config/crime_severity_config.json`` based on ``crime_type``.
  It is NOT independently learned from geographic or temporal
  features.
- Do NOT pass ``risk_level`` or ``severity_score`` as input
  features when ``risk_level`` is the target.
- This module does NOT modify or overwrite production labels.

Algorithm
---------
LogisticRegression with default regularization is used as the
baseline because the dataset is small, the classes are
non-overlapping in principle, and the model must remain
simple and explainable.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional, Tuple, Union

import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
)
from sklearn.model_selection import train_test_split


class RiskClassifier:
    """
    Thin sklearn-compatible wrapper for crime risk classification.

    Public API:
        fit(X, y)
        predict(X)
        predict_proba(X)
        score(X, y)
        save(path)
        load(path) -> RiskClassifier
    """

    def __init__(
        self,
        random_state: int = 42,
        max_iter: int = 1000,
    ) -> None:
        self.random_state = random_state
        self.max_iter = max_iter
        self._model = LogisticRegression(
            max_iter=max_iter,
            random_state=random_state,
        )
        self._classes: Optional[np.ndarray] = None
        self._fitted: bool = False

    def _validate_X_y(
        self,
        X: Any,
        y: Any,
    ) -> Tuple[np.ndarray, np.ndarray]:
        if not hasattr(X, "__len__"):
            raise TypeError("X must be array-like")

        n_samples = len(X)

        if n_samples == 0:
            raise ValueError("X is empty")

        if y is None or (hasattr(y, "__len__") and len(y) == 0):
            raise ValueError("y is empty")

        if len(y) != n_samples:
            raise ValueError(
                f"X and y length mismatch: {n_samples} != {len(y)}"
            )

        y_arr = np.asarray(y)

        unique_classes = np.unique(y_arr)

        if len(unique_classes) < 2:
            raise ValueError(
                "y must contain at least 2 classes for training, "
                f"got {len(unique_classes)} class(es): {unique_classes.tolist()}"
            )

        return np.asarray(X), y_arr

    def fit(
        self,
        X: Any,
        y: Any,
    ) -> "RiskClassifier":
        X_arr, y_arr = self._validate_X_y(X, y)

        self._model.fit(X_arr, y_arr)
        self._classes = self._model.classes_
        self._fitted = True

        return self

    def predict(self, X: Any) -> np.ndarray:
        if not self._fitted:
            raise RuntimeError("fit() must be called before predict()")

        X_arr = np.asarray(X)

        if X_arr.shape[1:] != (self._model.n_features_in_,):
            if len(X_arr) == 0:
                return np.array([], dtype=self._classes.dtype)
            raise ValueError(
                f"X has {X_arr.shape[1]} features, expected "
                f"{self._model.n_features_in_}"
            )

        return self._model.predict(X_arr)

    def predict_proba(self, X: Any) -> np.ndarray:
        if not self._fitted:
            raise RuntimeError("fit() must be called before predict_proba()")

        X_arr = np.asarray(X)

        if X_arr.shape[1:] != (self._model.n_features_in_,):
            if len(X_arr) == 0:
                return np.empty((0, len(self._classes)))
            raise ValueError(
                f"X has {X_arr.shape[1]} features, expected "
                f"{self._model.n_features_in_}"
            )

        return self._model.predict_proba(X_arr)

    def score(self, X: Any, y: Any) -> float:
        if not self._fitted:
            raise RuntimeError("fit() must be called before score()")

        y_pred = self.predict(X)
        y_true = np.asarray(y)

        if len(y_true) == 0:
            raise ValueError("y is empty")

        return float(accuracy_score(y_true, y_pred))

    def classes(self) -> np.ndarray:
        if not self._fitted:
            raise RuntimeError("fit() must be called before classes()")
        return self._classes

    def save(self, path: Union[str, os.PathLike]) -> None:
        if not self._fitted:
            raise RuntimeError("Cannot save an unfitted classifier")

        payload = {
            "model": self._model,
            "random_state": self.random_state,
            "max_iter": self.max_iter,
        }
        joblib.dump(payload, path)

    @classmethod
    def load(cls, path: Union[str, os.PathLike]) -> "RiskClassifier":
        payload = joblib.load(path)

        instance = cls(
            random_state=payload["random_state"],
            max_iter=payload["max_iter"],
        )
        instance._model = payload["model"]
        instance._classes = instance._model.classes_
        instance._fitted = True

        return instance


def evaluate_classifier(
    classifier: RiskClassifier,
    X: Any,
    y: Any,
    target_names: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Return basic evaluation metrics for a fitted classifier.

    Returns a dict with:
        accuracy
        classification_report (string)
        confusion_matrix (numpy array)
    """
    y_pred = classifier.predict(X)
    y_true = np.asarray(y)

    report = classification_report(
        y_true,
        y_pred,
        target_names=target_names,
        zero_division=0,
        output_dict=True,
    )

    cm = confusion_matrix(y_true, y_pred, labels=classifier.classes())

    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "classification_report": report,
        "confusion_matrix": cm.tolist(),
        "labels": classifier.classes().tolist(),
    }


def train_test_split_data(
    X: Any,
    y: Any,
    test_size: float = 0.2,
    random_state: int = 42,
    stratify: bool = True,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Split feature matrix and labels into train and test sets.

    Uses stratification when possible. Fails clearly if stratification
    is requested but there are too few samples per class.
    """
    if not 0.0 < test_size < 1.0:
        raise ValueError(f"test_size must be in (0, 1), got {test_size}")

    X_arr, y_arr = np.asarray(X), np.asarray(y)

    if len(X_arr) < 2:
        raise ValueError("Dataset is too small to split")

    classes, counts = np.unique(y_arr, return_counts=True)

    if stratify and np.any(counts < 2):
        raise ValueError(
            "Stratification requested but at least one class has fewer "
            f"than 2 samples: {dict(zip(classes.tolist(), counts.tolist()))}. "
            "Use stratify=False or collect more data."
        )

    return train_test_split(
        X_arr,
        y_arr,
        test_size=test_size,
        random_state=random_state,
        stratify=y_arr if stratify else None,
    )
