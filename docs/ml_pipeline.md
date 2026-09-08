# CrimeSense ML Pipeline Documentation

## 1. ML Objective

The CrimeSense ML pipeline performs **unsupervised spatial hotspot detection** and **descriptive temporal/pattern analysis** on crime records stored in the project's SQLite database.

It does **not** perform supervised crime-risk prediction.

## 2. Why Supervised Prediction Is Currently Not Scientifically Defensible

The current CrimeSense dataset does not provide sufficient independent ground-truth data for reliable supervised learning. Specifically:

| Limitation | Detail |
|---|---|
| **Rule-derived labels** | `risk_level` and `severity_score` are assigned from `crime_type` via a fixed configuration file (`config/crime_severity_config.json`). They are not independently observed outcomes. |
| **Missing target independence** | Using `severity_score` or `risk_level` as both features and targets creates target leakage. |
| **Missing coordinates** | 82 of 159 records (51%) lack valid latitude/longitude. |
| **Missing/invalid dates** | 58 of 159 records (36%) have missing or unparseable publication dates. |
| **Single district** | All records belong to "Vellore". There is no spatial diversity for learning area-level risk differences. |
| **Limited location diversity** | 150 of 159 records have `location_name = "Vellore"`. Only 6 unique location names exist. |
| **Sparse overlap** | Only 19 records have both valid coordinates and dates. Only 7 records have coordinates, dates, and a non-null `risk_level`. |
| **Small dataset** | 159 records is too few for reliable supervised time-series or count forecasting. |

Because of these limitations, any supervised model trained on the current data would either:
- reproduce the rule-based mapping from `crime_type` to `risk_level`, or
- overfit to noise and fail to generalize.

**No supervised model is trained in this pipeline.**

## 3. Dataset Limitations

- **Publication dates, not crime-occurrence dates**: The `crime_date` column stores article publication timestamps. These lag behind actual events and are subject to reporting delays.
- **Spatial granularity**: Coordinates are sparse and clustered in a single city/district.
- **Temporal coverage**: The date range spans 2012–2026, but with heavy sparsity and uneven distribution.
- **Class imbalance**: Crime types are heavily imbalanced (e.g., Murder: 51, Other: 31, Assault: 24, Theft: 13, etc.).

## 4. DBSCAN Methodology

The hotspot detection uses **DBSCAN** (Density-Based Spatial Clustering of Applications with Noise) applied to latitude/longitude coordinates.

### 4.1 Algorithm
DBSCAN groups points that are closely packed together and marks points in low-density regions as noise.

### 4.2 Haversine Distance
Because crime coordinates are geographic (latitude/longitude), Euclidean distance on raw degree values is not physically meaningful. The **Haversine formula** computes the great-circle distance between two points on a sphere, which is the standard approach for geographic clustering.

### 4.3 Parameters
| Parameter | Default | Description |
|---|---|---|
| `eps_km` | 1.0 km | Neighborhood radius. Points within this Haversine distance are considered neighbors. |
| `min_samples` | 2 | Minimum number of crimes required to form a dense cluster. Smaller values create more clusters (including spurious ones); larger values merge nearby areas. |

### 4.4 Noise Handling
Points that do not belong to any cluster are assigned label `-1` by DBSCAN. These are treated as **noise/outliers** and are not returned as hotspots.

## 5. Hotspot Definition

A **hotspot** is a DBSCAN cluster containing at least `min_samples` valid coordinate points within `eps_km` kilometres of each other.

Each hotspot summary includes:
- `cluster_id`: Unique integer identifier.
- `crime_count`: Number of crimes in the cluster.
- `centroid_latitude` / `centroid_longitude`: Geographic center.
- `dominant_crime_type`: Most frequent crime type (descriptive only).
- `avg_severity_score`: Average severity score (descriptive only; rule-derived).
- `dominant_risk_level`: Most frequent risk level (descriptive only; rule-derived).
- `dominant_location`: Most frequent location name (descriptive only).

## 6. Temporal Descriptive Analysis

Temporal analysis reports **publication-date trends** (article publication dates), not crime-occurrence trends.

Supported aggregations:
- Monthly counts (`YYYY-MM`)
- Yearly counts (`YYYY`)
- Day-of-week counts
- Crime-type trends over time

Records with missing or invalid dates are excluded and their count is reported.

## 7. Crime Pattern Profiling

Pattern profiling reports descriptive distributions for:
- Crime types
- Severity scores
- Risk levels
- Locations
- Districts

No artificial ML labels are created.

## 8. Evaluation Methodology

### 8.1 Unsupervised Metrics
Because DBSCAN is unsupervised, evaluation focuses on cluster structure rather than predictive accuracy:

| Metric | Description |
|---|---|
| `cluster_count` | Number of non-noise clusters detected. |
| `noise_points` | Number of points labeled as noise (-1). |
| `noise_percentage` | Fraction of valid coordinates treated as noise. |
| `silhouette_score` | Reported **only** when mathematically valid (≥2 non-noise clusters, sufficient samples). |

### 8.2 Silhouette Score Availability
Silhouette score requires:
1. At least 2 non-noise clusters.
2. Enough samples per cluster for stable pairwise distance computation.

On the current dataset, silhouette score is **often unavailable** because:
- The dataset is small (159 records, 77 with coordinates).
- With `eps_km=1.0` and `min_samples=2`, many points are labeled as noise.
- When fewer than 2 non-noise clusters exist, silhouette is mathematically undefined.

The API explicitly reports why silhouette is unavailable rather than fabricating a value.

## 9. API Endpoint

`POST /api/ml/hotspots`

Request body (optional):
```json
{
  "eps_km": 1.0,
  "min_samples": 2
}
```

Response:
```json
{
  "status": "success",
  "method": "DBSCAN",
  "analysis_type": "unsupervised_hotspot_detection",
  "hotspots": [...],
  "temporal": {...},
  "patterns": {...},
  "metrics": {
    "cluster_count": ...,
    "noise_points": ...,
    "noise_percentage": ...,
    "silhouette_score": null,
    "silhouette_note": "..."
  },
  "limitations": "..."
}
```

**Important**: This endpoint does NOT return prediction probabilities or future-crime forecasts.

## 10. Limitations

1. **No supervised prediction**: The current data does not support defensible supervised crime-risk prediction.
2. **Spatial limitation**: All records are in Vellore district. Hotspots reflect micro-variations within one city, not regional patterns.
3. **Temporal limitation**: Publication dates are not verified crime-occurrence dates. Trends reflect reporting patterns, not actual crime patterns.
4. **Data sparsity**: 51% of records lack coordinates. 36% lack usable dates.
5. **Small sample size**: 159 records is insufficient for reliable ML generalization.
6. **Rule-derived labels**: `risk_level` and `severity_score` are fixed by `crime_type`. Any model using them as targets or features would learn the rule, not real-world risk.

## 11. Future Requirements for Supervised Prediction

To support scientifically valid supervised crime-risk prediction, the project would need:

1. **Verified crime-occurrence timestamps** with known reporting lag distributions.
2. **Reliable, high-coverage latitude/longitude** for all records.
3. **Multiple geographic areas** (districts/cities) to learn spatial variation.
4. **Larger dataset** (ideally thousands of records with balanced coverage across time and space).
5. **Independent outcome definition**: A target variable that is NOT derived from the same features used for prediction. For example:
   - Actual arrest outcomes
   - Independent severity assessments from multiple sources
   - Verified harm/cost metrics
6. **Temporal validation**: Proper time-based train/validation/test splits that respect causality (features before prediction period, target after).

## 12. Files Created

| File | Purpose |
|---|---|
| `ml/hotspot_model.py` | Reusable DBSCAN hotspot detector |
| `ml/temporal_analysis.py` | Descriptive publication-date analysis |
| `ml/crime_pattern_analysis.py` | Descriptive crime pattern profiling |
| `backend/services/ml_prediction_service.py` | Backend service wrapping unsupervised analytics |
| `backend/routes/crime_routes.py` | Modified to add `/api/ml/hotspots` endpoint |
| `tests/test_hotspot_model.py` | Hotspot model tests |
| `tests/test_temporal_analysis.py` | Temporal analysis tests |
| `tests/test_crime_pattern_analysis.py` | Pattern analysis tests |
| `tests/test_ml_prediction_service.py` | ML service tests |
| `docs/ml_pipeline.md` | This documentation |
