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
| `backend/services/alert_service.py` | Backend service for proximity alert decisions |
| `backend/services/proximity_service.py` | Improved proximity calculations (Haversine, validation, limits) |
| `backend/routes/crime_routes.py` | Modified to add `/api/ml/hotspots` endpoint and improve `/api/crimes/nearby` |
| `backend/routes/alert_routes.py` | Improved `/api/proximity-check` endpoint |
| `tests/test_hotspot_model.py` | Hotspot model tests |
| `tests/test_temporal_analysis.py` | Temporal analysis tests |
| `tests/test_crime_pattern_analysis.py` | Pattern analysis tests |
| `tests/test_ml_prediction_service.py` | ML service tests |
| `tests/test_proximity_service.py` | Proximity service tests |
| `tests/test_alert_service.py` | Alert service tests |
| `tests/test_alert_routes.py` | Alert route tests |
| `tests/test_e2e_backend.py` | End-to-end integration test |
| `docs/ml_pipeline.md` | This documentation |

## 13. API Documentation

### 13.1 `POST /api/proximity-check`

**Purpose**: Check whether the user's current location is near historical crime locations or detected hotspots.

**Request body**:
```json
{
  "latitude": 13.043505,
  "longitude": 79.240410,
  "alert_radius_meters": 500
}
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `latitude` | float | Yes | User latitude (-90 to 90) |
| `longitude` | float | Yes | User longitude (-180 to 180) |
| `alert_radius_meters` | float | No | Alert radius in metres (default: 500, min: 10, max: 50000) |

**Success response (200)**:
```json
{
  "success": true,
  "alert": true,
  "message": "Warning: You are near a historical crime hotspot.",
  "user_location": {
    "latitude": 13.043505,
    "longitude": 79.240410
  },
  "nearby_crimes": [
    {
      "id": 1,
      "crime_type": "Theft",
      "latitude": 13.043505,
      "longitude": 79.240410,
      "distance_km": 0.0,
      "risk_level": "Medium"
    }
  ],
  "nearby_hotspots": [],
  "checked_radius_meters": 500,
  "nearest_hotspot": {
    "location": "Katpadi",
    "latitude": 13.043505,
    "longitude": 79.240410,
    "crime_count": 3,
    "risk_level": "Low"
  },
  "limitations": "This alert is based on historical crime locations only. It does not predict future crime events."
}
```

**No-result response (200)**:
```json
{
  "success": true,
  "alert": false,
  "message": "You are outside the crime hotspot alert radius.",
  "user_location": {
    "latitude": 13.043505,
    "longitude": 79.240410
  },
  "nearby_crimes": [],
  "nearby_hotspots": [],
  "checked_radius_meters": 500,
  "limitations": "This alert is based on historical crime locations only. It does not predict future crime events."
}
```

**Validation errors (400)**:
- Missing latitude/longitude
- Invalid latitude/longitude (out of range or non-numeric)
- Invalid alert_radius_meters (<= 0, < 10, or > 50000)

**Important**: This endpoint checks proximity to **historical** crime locations. It does **not** predict that a crime will occur.

### 13.2 `POST /api/ml/hotspots`

**Purpose**: Run unsupervised spatial hotspot detection and descriptive temporal/pattern analysis on all crime records.

**Request body** (optional):
```json
{
  "eps_km": 1.0,
  "min_samples": 2
}
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `eps_km` | float | No | DBSCAN neighbourhood radius in km (default: 1.0) |
| `min_samples` | int | No | Minimum cluster size (default: 2) |

**Success response (200)**:
```json
{
  "status": "success",
  "method": "DBSCAN",
  "analysis_type": "unsupervised_hotspot_detection",
  "parameters": {
    "eps_km": 1.0,
    "min_samples": 2
  },
  "hotspots": [
    {
      "cluster_id": 0,
      "crime_count": 5,
      "centroid_latitude": 13.043505,
      "centroid_longitude": 79.240410,
      "noise": false,
      "dominant_crime_type": "Theft",
      "avg_severity_score": 4.5,
      "dominant_risk_level": "Medium",
      "dominant_location": "Katpadi"
    }
  ],
  "temporal": {
    "total_records": 159,
    "valid_dates": 101,
    "invalid_dates": 58,
    "monthly_counts": {"2025-01": 6, ...},
    "yearly_counts": {"2025": 28, ...},
    "day_of_week_counts": {"Tuesday": 22, ...}
  },
  "patterns": {
    "crime_type_distribution": {"Murder": 51, ...},
    "severity_score_distribution": {10: 45, ...},
    "risk_level_distribution": {"Critical": 45, ...}
  },
  "metrics": {
    "total_records": 159,
    "valid_coordinates": 77,
    "cluster_count": 2,
    "noise_points": 2,
    "noise_percentage": 2.6,
    "silhouette_score": null,
    "silhouette_note": "Silhouette score is not reported because the current dataset is too small..."
  },
  "limitations": "All analyses are descriptive/unsupervised. No supervised prediction is performed."
}
```

**Important**: This endpoint performs **historical spatial clustering** and **descriptive analysis**. It does **not** predict future crime events.

## 14. Terminology Clarification

| Term | Meaning in CrimeSense |
|---|---|
| **Historical hotspot detection** | DBSCAN clustering of past crime coordinates to identify areas with concentrated historical activity. |
| **Current-user proximity checking** | Comparing the user's current GPS coordinates against historical crime locations and hotspot centroids. |
| **Alert generation** | Returning a structured response indicating whether the user is within a configured radius of historical crime locations. |
| **Crime prediction** | NOT IMPLEMENTED. The system does not forecast future crime events. |

## 15. Validation Rules

| Input | Rule |
|---|---|
| `latitude` | Must be a number in [-90, 90] |
| `longitude` | Must be a number in [-180, 180] |
| `alert_radius_meters` | Must be a number in [10, 50000] |
| `radius_km` (query param) | Must be a number in (0, 100] |
| `limit` (query param) | Must be an integer in (0, 200] |
| `eps_km` | Must be a positive number |
| `min_samples` | Must be a positive integer |

## 16. Proximity Algorithm

The system uses the **Haversine formula** to compute great-circle distances between latitude/longitude coordinates on a spherical Earth model (radius = 6371 km).

Formula:
```
a = sin²(Δlat/2) + cos(lat1) * cos(lat2) * sin²(Δlon/2)
c = 2 * atan2(√a, √(1-a))
d = R * c
```

Where:
- `Δlat` = latitude difference in radians
- `Δlon` = longitude difference in radians
- `R` = Earth radius (6371 km)
- `d` = distance in kilometres

## 17. Alert Logic

1. Validate user coordinates.
2. Retrieve all crime records from the database.
3. Filter to records with valid coordinates.
4. Run DBSCAN hotspot detection on valid coordinates.
5. Calculate Haversine distance from user to each crime and each hotspot centroid.
6. Filter crimes/hotspots within the configured alert radius.
7. Sort results by distance (nearest first).
8. If any nearby crimes or hotspots exist, set `alert: true`.
9. Return structured response with nearby items and limitations.

**No probability or confidence scores are computed or returned.**

## 18. Backward Compatibility

| Endpoint | Change | Compatibility |
|---|---|---|
| `GET /api/crimes` | None | Unchanged |
| `GET /api/crimes/<id>` | None | Unchanged |
| `POST /api/crimes` | None | Unchanged |
| `PUT /api/crimes/<id>` | None | Unchanged |
| `DELETE /api/crimes/<id>` | None | Unchanged |
| `GET /api/crimes/hotspots` | None | Unchanged |
| `GET /api/hotspots` | None | Unchanged |
| `GET /api/crimes/nearby` | Added `limit` parameter | Backward compatible (optional) |
| `GET /api/crimes/statistics` | None | Unchanged |
| `GET /api/risk/<location>` | None | Unchanged |
| `POST /api/proximity-check` | Strengthened validation, added `nearby_hotspots`, `limitations` | Backward compatible (additional fields) |
| `POST /api/ml/hotspots` | New endpoint | New |

## 19. Bug Fixes

| Bug | File | Fix |
|---|---|---|
| `find_nearest_hotspot` used non-existent `average_latitude`/`average_longitude` keys | `backend/services/proximity_service.py` | Changed to use correct `centroid_latitude`/`centroid_longitude` keys |
| No validation for user coordinates in proximity check | `backend/services/proximity_service.py` | Added `_validate_coordinate` helper |
| No limit on nearby crime results | `backend/services/proximity_service.py` | Added `limit` parameter to `find_nearby_crimes` |
| No nearby hotspot detection function | `backend/services/proximity_service.py` | Added `find_nearby_hotspots` |
| Alert logic duplicated in route | `backend/routes/alert_routes.py` | Extracted to `backend/services/alert_service.py` |
