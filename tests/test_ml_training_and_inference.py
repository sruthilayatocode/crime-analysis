"""
Automated unit and integration tests for Machine Learning Training and Inference pipeline.
"""

import os
import sys
import pytest

# Ensure backend and root are on sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from ml.train_model import load_training_data, train_model, evaluate_model
from ml.predict import (
    load_model,
    predict_risk,
    predict_hotspot,
    predict_batch,
    predict_with_confidence,
)


@pytest.fixture
def sample_records():
    return [
        {
            "crime_type": "Theft",
            "district": "Vellore",
            "location_name": "Katpadi",
            "latitude": 12.9806,
            "longitude": 79.1368,
            "crime_date": "2026-10-20 12:00:00",
        },
        {
            "crime_type": "Murder",
            "district": "Vellore",
            "location_name": "Fort",
            "latitude": 12.9165,
            "longitude": 79.1325,
            "crime_date": "2026-10-21 22:30:00",
        },
        {
            "crime_type": "Burglary",
            "district": "Vellore",
            "location_name": "Gandhi Nagar",
            "latitude": 12.9650,
            "longitude": 79.1450,
            "crime_date": "2026-10-22 03:00:00",
        },
    ]


def test_model_loading():
    """Verify that the serialized ML model bundle loads with all required components."""
    bundle = load_model()
    assert isinstance(bundle, dict)
    assert "feature_engineer" in bundle
    assert "classifier" in bundle
    assert "classes" in bundle
    assert "version" in bundle
    assert "model_name" in bundle
    assert len(bundle["classes"]) >= 2


def test_predict_risk_single():
    """Test risk prediction on a single incident feature dict."""
    incident = {
        "crime_type": "Theft",
        "district": "Vellore",
        "location_name": "Katpadi",
        "latitude": 12.9806,
        "longitude": 79.1368,
        "crime_date": "2026-10-25 10:00:00",
    }
    result = predict_risk(incident)
    assert isinstance(result, dict)
    assert "predicted_risk_level" in result
    assert result["predicted_risk_level"] in ["Critical", "High", "Medium", "Low"]
    assert 0.0 <= result["risk_score"] <= 1.0
    assert 0.0 <= result["confidence"] <= 1.0
    assert isinstance(result["probabilities"], dict)
    assert len(result["probabilities"]) >= 2


def test_predict_hotspot_numeric():
    """Test hotspot score computation returns float between 0.0 and 1.0."""
    incident = {
        "crime_type": "Murder",
        "district": "Vellore",
        "latitude": 12.9165,
        "longitude": 79.1325,
    }
    score = predict_hotspot(None, incident)
    assert isinstance(score, float)
    assert 0.0 <= score <= 1.0


def test_predict_batch(sample_records):
    """Test batch prediction handles multiple records."""
    results = predict_batch(None, sample_records)
    assert len(results) == len(sample_records)
    for res in results:
        assert "predicted_risk_level" in res
        assert "risk_score" in res
        assert "confidence" in res


def test_predict_with_confidence():
    """Test confidence and probability extraction."""
    incident = {
        "crime_type": "Assault",
        "district": "Vellore",
        "location_name": "Bagayam",
        "latitude": 12.8700,
        "longitude": 79.1300,
    }
    res = predict_with_confidence(None, incident)
    assert "score" in res
    assert "confidence" in res
    assert "risk_level" in res
    assert "probabilities" in res


def test_ml_api_endpoints():
    """Test /api/ml/model-info and /api/ml/predict-risk Flask routes."""
    from app import app
    client = app.test_client()

    # GET /api/ml/model-info
    info_res = client.get("/api/ml/model-info")
    assert info_res.status_code == 200
    info_data = info_res.get_json()
    assert info_data["success"] is True
    assert "selected_model_metrics" in info_data["data"]
    assert "classes" in info_data["data"]

    # POST /api/ml/predict-risk (valid)
    pred_res = client.post("/api/ml/predict-risk", json={
        "crime_type": "Robbery",
        "district": "Vellore",
        "location_name": "Katpadi",
        "latitude": 12.9806,
        "longitude": 79.1368,
        "crime_date": "2026-10-25"
    })
    assert pred_res.status_code == 200
    pred_data = pred_res.get_json()
    assert pred_data["success"] is True
    assert "predicted_risk_level" in pred_data["data"]
    assert 0.0 <= pred_data["data"]["risk_score"] <= 1.0

    # POST /api/ml/predict-risk (invalid non-dict body)
    bad_res = client.post("/api/ml/predict-risk", data="not-json")
    assert bad_res.status_code == 400
    assert bad_res.get_json()["success"] is False
