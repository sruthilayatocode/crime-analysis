"""
Make predictions using trained crime risk and hotspot models.

This module provides inference functions for loading the trained model
and generating risk classification and hotspot scoring for incident data.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np

# Ensure project root is on sys.path for joblib unpickling
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

_DEFAULT_MODEL_PATH = os.path.join(
    os.path.dirname(__file__), "models", "crime_risk_model.joblib"
)

_CACHED_MODEL: Optional[Dict[str, Any]] = None


def load_model(model_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load a trained model bundle from disk.

    Args:
        model_path: Optional path to serialized model file.
                    Defaults to ml/models/crime_risk_model.joblib.

    Returns:
        dict: Deserialized model bundle containing feature_engineer,
              classifier, classes, version, and model_name.

    Raises:
        FileNotFoundError: If the model file cannot be found.
        RuntimeError: If model deserialization fails.
    """
    global _CACHED_MODEL

    path = model_path or _DEFAULT_MODEL_PATH
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Trained model artifact not found at {path}. "
            "Please run 'python ml/train_model.py' to generate the model artifact."
        )

    try:
        import joblib
        bundle = joblib.load(path)
        if not isinstance(bundle, dict) or "classifier" not in bundle:
            raise ValueError(f"Invalid model artifact structure in {path}")
        _CACHED_MODEL = bundle
        return bundle
    except Exception as exc:
        raise RuntimeError(f"Failed to load model from {path}: {exc}") from exc


def get_model() -> Dict[str, Any]:
    """Return the cached model bundle, loading it if not yet loaded."""
    global _CACHED_MODEL
    if _CACHED_MODEL is None:
        _CACHED_MODEL = load_model()
    return _CACHED_MODEL


_RISK_SCORE_MAP = {
    "CRITICAL": 0.95,
    "HIGH": 0.75,
    "MEDIUM": 0.50,
    "LOW": 0.25,
}


def predict_risk(
    features: Dict[str, Any],
    model: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Predict the crime risk level and score for a single incident or location.

    Args:
        features: Dictionary containing incident features (e.g. crime_type,
                  latitude, longitude, district, location_name, crime_date).
        model: Optional pre-loaded model bundle. If None, uses cached model.

    Returns:
        dict: Structured prediction containing:
            - predicted_risk_level (str): 'Critical', 'High', 'Medium', or 'Low'
            - risk_score (float): Continuous score in [0.0, 1.0]
            - confidence (float): Probability associated with predicted class
            - probabilities (dict): Probability distribution across all classes
            - model_name (str): Identifier of the inference model
            - version (str): Model version string
    """
    bundle = model or get_model()
    engineer = bundle["feature_engineer"]
    classifier = bundle["classifier"]
    classes = bundle.get("classes", ["Critical", "High", "Low", "Medium"])

    # Clean input: exclude target / leakage fields if passed accidentally
    clean_record = {k: v for k, v in features.items() if k not in ("risk_level", "severity_score")}

    X = engineer.transform([clean_record])

    pred_raw = classifier.predict(X)[0]
    predicted_class = str(pred_raw)

    probabilities = {}
    confidence = 1.0
    if hasattr(classifier, "predict_proba"):
        try:
            probas = classifier.predict_proba(X)[0]
            cls_list = list(getattr(classifier, "classes_", classes))
            probabilities = {
                str(cls_name): round(float(prob), 4)
                for cls_name, prob in zip(cls_list, probas)
            }
            if predicted_class in probabilities:
                confidence = probabilities[predicted_class]
        except Exception:
            probabilities = {predicted_class: 1.0}

    risk_score = _RISK_SCORE_MAP.get(predicted_class.upper(), 0.50)

    return {
        "predicted_risk_level": predicted_class,
        "risk_score": float(risk_score),
        "confidence": float(round(confidence, 4)),
        "probabilities": probabilities,
        "model_name": bundle.get("model_name", "RiskClassifier"),
        "version": bundle.get("version", "1.0.0"),
    }


def predict_hotspot(model: Any, features: Any) -> float:
    """
    Predict the crime hotspot risk score for a location.

    Args:
        model: Loaded model bundle or classifier.
        features: Feature dict or vector.

    Returns:
        float: Predicted risk score between 0.0 and 1.0.
    """
    if isinstance(features, dict):
        res = predict_risk(features, model=model if isinstance(model, dict) else None)
        return res["risk_score"]

    # If already a vector/array
    if isinstance(model, dict):
        clf = model["classifier"]
    else:
        clf = model

    X = np.asarray(features)
    if X.ndim == 1:
        X = X.reshape(1, -1)

    pred = clf.predict(X)[0]
    return _RISK_SCORE_MAP.get(str(pred).upper(), 0.50)


def predict_batch(
    model: Any,
    features_batch: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Predict risk scores and levels for a batch of incident records.

    Args:
        model: Loaded model bundle or None to use default.
        features_batch: List of feature dictionaries.

    Returns:
        list of dict: List of prediction results.
    """
    bundle = model if isinstance(model, dict) else get_model()
    return [predict_risk(f, model=bundle) for f in features_batch]


def predict_with_confidence(model: Any, features: Any) -> Dict[str, Any]:
    """
    Predict risk score with confidence and detailed breakdown.

    Args:
        model: Loaded model bundle.
        features: Feature dict or vector.

    Returns:
        dict with 'score', 'confidence', and 'risk_level' keys.
    """
    if isinstance(features, dict):
        res = predict_risk(features, model=model if isinstance(model, dict) else None)
        return {
            "score": res["risk_score"],
            "confidence": res["confidence"],
            "risk_level": res["predicted_risk_level"],
            "probabilities": res["probabilities"],
        }

    # Vector input fallback
    score = predict_hotspot(model, features)
    return {
        "score": score,
        "confidence": 1.0,
        "risk_level": "Medium" if score == 0.5 else ("High" if score > 0.5 else "Low"),
    }


def main() -> None:
    """Entry point demonstration for prediction pipeline."""
    sample_incident = {
        "crime_type": "Theft",
        "district": "Vellore",
        "location_name": "Katpadi",
        "latitude": 12.9806,
        "longitude": 79.1368,
        "crime_date": "2026-10-25 10:00:00",
    }
    print("Testing ML Risk Prediction on sample incident:")
    print("Input:", sample_incident)
    result = predict_risk(sample_incident)
    print("\nResult:")
    for k, v in result.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()