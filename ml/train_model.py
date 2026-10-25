"""
Train machine learning models for crime risk classification and hotspot scoring.

This module loads crime records from the CrimeSense SQLite database, performs
preprocessing and feature engineering (strictly excluding severity_score to
prevent target leakage), evaluates baseline vs. candidate classifiers on an
80/20 stratified holdout split, and serializes the model and metadata.
"""

from __future__ import annotations

import json
import os
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import joblib
import numpy as np
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import train_test_split

# Ensure project root is in sys.path
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from ml.feature_engineering import CrimeFeatureEngineer


def get_default_db_path() -> str:
    """Resolve active SQLite database path."""
    candidates = [
        _PROJECT_ROOT / "backend" / "instance" / "crimesense.db",
        _PROJECT_ROOT / "backend" / "crimesense.db",
        _PROJECT_ROOT / "crime_analysis.db",
    ]
    for c in candidates:
        if c.exists():
            return str(c)
    return str(candidates[0])


def load_training_data(db_path: Optional[str] = None) -> Tuple[List[Dict[str, Any]], List[str]]:
    """
    Load crime records from the SQLite database.

    Args:
        db_path: Optional path to SQLite file.

    Returns:
        tuple: (records, labels) where records is a list of dicts and labels
               is a list of string risk categories.
    """
    path = db_path or get_default_db_path()
    if not os.path.exists(path):
        raise FileNotFoundError(f"Database not found at {path}")

    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id, crime_type, description, latitude, longitude,
               location_name, crime_date, district, risk_level
        FROM crimes
        WHERE risk_level IS NOT NULL AND TRIM(risk_level) != ''
        """
    )
    rows = cur.fetchall()
    conn.close()

    records: List[Dict[str, Any]] = []
    labels: List[str] = []

    for row in rows:
        r_dict = dict(row)
        target = str(r_dict.pop("risk_level")).strip()
        # Normalize target to Title case (Critical, High, Medium, Low)
        target = target.capitalize()
        # Strictly ensure severity_score is omitted to prevent target leakage
        r_dict.pop("severity_score", None)
        records.append(r_dict)
        labels.append(target)

    return records, labels


def train_model(
    records: List[Dict[str, Any]],
    labels: List[str],
    model_type: str = "logistic_regression",
    params: Optional[Dict[str, Any]] = None,
    random_state: int = 42,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Train and evaluate a crime risk classifier.

    Args:
        records: List of incident feature dicts.
        labels: Corresponding ground-truth risk categories.
        model_type: 'logistic_regression' or 'random_forest'.
        params: Optional dict of model hyperparameters.
        random_state: Seed for reproducibility.

    Returns:
        tuple: (model_bundle, evaluation_metrics)
    """
    if len(records) != len(labels) or len(records) == 0:
        raise ValueError("Records and labels must be non-empty and of equal length.")

    # 1. Stratified train/test split (80% train, 20% test)
    train_idx, test_idx = train_test_split(
        np.arange(len(records)),
        test_size=0.20,
        stratify=labels,
        random_state=random_state,
    )

    train_records = [records[i] for i in train_idx]
    test_records = [records[i] for i in test_idx]
    y_train = [labels[i] for i in train_idx]
    y_test = [labels[i] for i in test_idx]

    # 2. Fit feature engineer strictly on training data
    engineer = CrimeFeatureEngineer()
    X_train = engineer.fit_transform(train_records)
    X_test = engineer.transform(test_records)

    classes = sorted(list(set(labels)))

    # 3. Train Baseline: DummyClassifier (most frequent class)
    dummy = DummyClassifier(strategy="most_frequent")
    dummy.fit(X_train, y_train)
    dummy_preds = dummy.predict(X_test)
    baseline_acc = float(accuracy_score(y_test, dummy_preds))
    baseline_f1 = float(f1_score(y_test, dummy_preds, average="macro", zero_division=0))

    # 4. Train Candidate Models
    lr_params = {"max_iter": 1000, "random_state": random_state}
    if params and model_type == "logistic_regression":
        lr_params.update(params)
    lr_model = LogisticRegression(**lr_params)
    lr_model.fit(X_train, y_train)
    lr_preds = lr_model.predict(X_test)
    lr_acc = float(accuracy_score(y_test, lr_preds))
    lr_f1 = float(f1_score(y_test, lr_preds, average="macro", zero_division=0))
    lr_wf1 = float(f1_score(y_test, lr_preds, average="weighted", zero_division=0))

    rf_params = {"n_estimators": 100, "random_state": random_state, "class_weight": "balanced"}
    if params and model_type == "random_forest":
        rf_params.update(params)
    rf_model = RandomForestClassifier(**rf_params)
    rf_model.fit(X_train, y_train)
    rf_preds = rf_model.predict(X_test)
    rf_acc = float(accuracy_score(y_test, rf_preds))
    rf_f1 = float(f1_score(y_test, rf_preds, average="macro", zero_division=0))
    rf_wf1 = float(f1_score(y_test, rf_preds, average="weighted", zero_division=0))

    # 5. Select Best Candidate Model
    if model_type == "random_forest" or (model_type != "logistic_regression" and rf_f1 > lr_f1):
        chosen_model = rf_model
        chosen_preds = rf_preds
        chosen_name = "RandomForestClassifier"
    else:
        chosen_model = lr_model
        chosen_preds = lr_preds
        chosen_name = "LogisticRegression"

    # 6. Detailed Evaluation Metrics
    report_dict = classification_report(y_test, chosen_preds, output_dict=True, zero_division=0)
    conf_matrix = confusion_matrix(y_test, chosen_preds, labels=classes).tolist()

    per_class_metrics = {}
    for c in classes:
        if c in report_dict:
            per_class_metrics[c] = {
                "precision": round(float(report_dict[c]["precision"]), 4),
                "recall": round(float(report_dict[c]["recall"]), 4),
                "f1": round(float(report_dict[c]["f1-score"]), 4),
                "support": int(report_dict[c]["support"]),
            }

    eval_metrics = {
        "model_name": chosen_name,
        "version": "1.0.0",
        "total_records": len(records),
        "train_samples": len(train_records),
        "test_samples": len(test_records),
        "classes": classes,
        "target_variable": "risk_level",
        "leakage_prevention": "severity_score explicitly excluded",
        "features_engineered": engineer.get_feature_names(),
        "baseline_metrics": {
            "model": "DummyClassifier(strategy='most_frequent')",
            "accuracy": round(baseline_acc, 4),
            "macro_f1": round(baseline_f1, 4),
        },
        "logistic_regression_metrics": {
            "accuracy": round(lr_acc, 4),
            "macro_f1": round(lr_f1, 4),
            "weighted_f1": round(lr_wf1, 4),
        },
        "random_forest_metrics": {
            "accuracy": round(rf_acc, 4),
            "macro_f1": round(rf_f1, 4),
            "weighted_f1": round(rf_wf1, 4),
        },
        "selected_model_metrics": {
            "accuracy": round(float(accuracy_score(y_test, chosen_preds)), 4),
            "balanced_accuracy": round(float(balanced_accuracy_score(y_test, chosen_preds)), 4),
            "macro_f1": round(float(f1_score(y_test, chosen_preds, average="macro", zero_division=0)), 4),
            "weighted_f1": round(float(f1_score(y_test, chosen_preds, average="weighted", zero_division=0)), 4),
            "macro_precision": round(float(precision_score(y_test, chosen_preds, average="macro", zero_division=0)), 4),
            "macro_recall": round(float(recall_score(y_test, chosen_preds, average="macro", zero_division=0)), 4),
            "per_class": per_class_metrics,
            "confusion_matrix": conf_matrix,
        },
        "limitations": (
            "Model trained on 685 geocoded Tamil Nadu crime reports primarily from Vellore district. "
            "Evaluation performed on a 20% stratified holdout split (137 test samples). "
            "Classes exhibit natural imbalance ('Low' constitutes ~46.7% of events). "
            "Hotspot detection should use DBSCAN spatial clustering rather than supervised forecasting."
        ),
    }

    bundle = {
        "feature_engineer": engineer,
        "classifier": chosen_model,
        "classes": classes,
        "version": "1.0.0",
        "model_name": chosen_name,
    }

    return bundle, eval_metrics


def evaluate_model(model: Any, X_test: Any, y_test: Any) -> Dict[str, float]:
    """
    Evaluate a trained model on test data.

    Args:
        model: Trained model object.
        X_test: Test feature matrix.
        y_test: Test labels.

    Returns:
        dict: Evaluation metrics (accuracy, macro_f1, weighted_f1).
    """
    preds = model.predict(X_test)
    return {
        "accuracy": round(float(accuracy_score(y_test, preds)), 4),
        "macro_f1": round(float(f1_score(y_test, preds, average="macro", zero_division=0)), 4),
        "weighted_f1": round(float(f1_score(y_test, preds, average="weighted", zero_division=0)), 4),
    }


def save_model(
    bundle: Dict[str, Any],
    output_path: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Serialize and save trained model bundle and metadata.

    Args:
        bundle: Model bundle containing feature_engineer, classifier, etc.
        output_path: Path to .joblib file.
        metadata: Optional metadata dictionary to write to JSON.

    Returns:
        str: Absolute path to the saved model file.
    """
    path = output_path or os.path.join(
        os.path.dirname(__file__), "models", "crime_risk_model.joblib"
    )
    os.makedirs(os.path.dirname(path), exist_ok=True)

    joblib.dump(bundle, path)

    if metadata:
        meta_path = os.path.join(os.path.dirname(path), "model_metadata.json")
        metadata["trained_at"] = datetime.now(timezone.utc).isoformat()
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

    return path


def main() -> None:
    """Entry point for model training pipeline."""
    print("=" * 65)
    print("CRIMESENSE ML TRAINING PIPELINE")
    print("=" * 65)

    db_path = get_default_db_path()
    print(f"[Data] Loading records from SQLite: {db_path}")
    records, labels = load_training_data(db_path)
    print(f"[Data] Total records loaded: {len(records)}")

    from collections import Counter
    print(f"[Data] Class distribution: {dict(Counter(labels))}")

    print("\n[Training] Fitting models (LogisticRegression & RandomForest)...")
    bundle, metrics = train_model(records, labels, model_type="logistic_regression")

    print(f"\n[Results] Model Selected: {metrics['model_name']}")
    print(f"  Baseline Accuracy (Dummy): {metrics['baseline_metrics']['accuracy']:.4f}")
    print(f"  Logistic Regression Accuracy: {metrics['logistic_regression_metrics']['accuracy']:.4f} (Macro F1: {metrics['logistic_regression_metrics']['macro_f1']:.4f})")
    print(f"  Random Forest Accuracy:       {metrics['random_forest_metrics']['accuracy']:.4f} (Macro F1: {metrics['random_forest_metrics']['macro_f1']:.4f})")
    print(f"  Selected Model Test Accuracy: {metrics['selected_model_metrics']['accuracy']:.4f}")
    print(f"  Selected Model Macro F1:      {metrics['selected_model_metrics']['macro_f1']:.4f}")
    print(f"  Selected Model Weighted F1:   {metrics['selected_model_metrics']['weighted_f1']:.4f}")

    out_file = save_model(bundle, metadata=metrics)
    print(f"\n[Persistence] Serialized model saved to: {out_file}")
    print(f"[Persistence] Metadata written to: {os.path.join(os.path.dirname(out_file), 'model_metadata.json')}")
    print("=" * 65)


if __name__ == "__main__":
    main()