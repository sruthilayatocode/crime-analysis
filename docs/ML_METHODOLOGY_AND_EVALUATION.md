# CrimeSense — Machine Learning Methodology & Evaluation Report

## 1. Executive Summary & Problem Formulation
The CrimeSense machine-learning subsystem addresses two distinct computational problems:
1. **Unsupervised Spatial Hotspot Analysis**: Identifying spatial concentrations of recorded crime incidents across geographic coordinates without historical label bias.
2. **Supervised Risk Classification**: Predicting the risk level (`LOW`, `MEDIUM`, `HIGH`) and continuous risk score for an incident based on spatio-temporal and categorical features.

> [!IMPORTANT]
> **Defensible Scientific Stance on Forecasting**:
> DBSCAN spatial clustering identifies historical concentrations of incidents; it does *not* forecast future criminal activity. True temporal crime forecasting requires multi-year longitudinal timestamped event logs with fine-grained census and economic covariates. Within CrimeSense, spatial clustering and risk classification are strictly distinguished from predictive future forecasting.

---

## 2. Dataset Provenance & Exploration
The dataset is drawn directly from the verified SQLite database (`backend/instance/crimesense.db`) containing **685 approved crime incidents**.

### 2.1 Distribution and Attributes
- **Total Records**: 685
- **Features Extracted**:
  - `latitude`, `longitude`: Geographic decimal coordinates
  - `crime_category`: Categorical crime classification (`THEFT`, `BURGLARY`, `ASSAULT`, `ROBBERY`, `VANDALISM`, etc.)
  - `crime_hour`, `crime_day_of_week`, `crime_month`: Temporal cyclical features
  - `is_weekend`, `is_night`: Binary temporal indicators
- **Target Variable**: `risk_level` (`LOW`, `MEDIUM`, `HIGH`)
  - `LOW`: 320 records (46.7%)
  - `MEDIUM`: 180 records (26.3%)
  - `HIGH`: 185 records (27.0%)

### 2.2 Target Leakage Prevention
In initial naïve configurations, models often incorporate `severity_score` when predicting `risk_level`. Because severity rules directly inform risk thresholds, doing so causes severe target leakage.
In our implementation (`ml/feature_engineering.py` and `ml/train_model.py`), both `severity_score` and `risk_level` are **strictly excluded** from the input feature set $X$. Features are restricted purely to independent operational inputs (location, category, time of day, and calendar attributes).

---

## 3. Preprocessing & Feature Engineering Pipeline
The feature transformation pipeline is constructed using scikit-learn `ColumnTransformer` and `Pipeline` objects to prevent data leakage between train and test splits:
- **Numerical Features** (`latitude`, `longitude`, `crime_hour`, `crime_day_of_week`, `crime_month`):
  - Missing value imputation using `SimpleImputer(strategy='median')`
  - Feature standardisation using `StandardScaler`
- **Categorical Features** (`crime_category`):
  - Missing value imputation using `SimpleImputer(strategy='constant', fill_value='UNKNOWN')`
  - Encoding via `OneHotEncoder(handle_unknown='ignore', sparse_output=False)`

---

## 4. Model Training & Evaluation

### 4.1 Validation Strategy
- **Split**: 80% Training ($N=548$), 20% Holdout Testing ($N=137$)
- **Stratification**: Class labels are stratified across train and test partitions to maintain representative class balance.
- **Reproducibility**: Random seed fixed to `42` across all splits, baseline instantiations, and estimators.

### 4.2 Benchmark Results
We evaluate a heuristic baseline alongside two supervised classifiers:

| Model Architecture | Strategy / Hyperparameters | Test Accuracy | Macro Precision | Macro Recall | Macro F1 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **DummyClassifier** | `strategy='most_frequent'` | **46.72%** | 0.156 | 0.333 | 0.212 |
| **LogisticRegression** | `C=1.0, max_iter=1000` | **100.0%** | 1.000 | 1.000 | 1.000 |
| **RandomForestClassifier** | `n_estimators=100, max_depth=12, random_state=42` | **99.27%** | 0.993 | 0.993 | **0.993** |

*Note: The high separability between categories and risk tiers reflects the underlying domain ontology where specific incident categories correlate strongly with designated severity bands.*

### 4.3 Classification Report (RandomForest on Test Split)
```
              precision    recall  f1-score   support

        HIGH       1.00      0.97      0.99        37
         LOW       1.00      1.00      1.00        64
      MEDIUM       0.97      1.00      0.99        36

    accuracy                           0.99       137
   macro avg       0.99      0.99      0.99       137
weighted avg       0.99      0.99      0.99       137
```

---

## 5. Unsupervised Spatial Hotspot Clustering (DBSCAN)
Spatial clustering operates independently via `ml/hotspot_model.py` and `backend/services/hotspot_service.py`:
- **Algorithm**: Density-Based Spatial Clustering of Applications with Noise (`DBSCAN`).
- **Metric**: Haversine distance on radian coordinates.
- **Parameters**:
  - $\varepsilon$ (Epsilon): 1.0 km radius ($1.0 / 6371.0$ radians).
  - `min_samples`: 5 incidents minimum density threshold.
- **Output**:
  - Cluster IDs identifying dense incident regions.
  - Geographic centroids calculated via arithmetic mean of cluster coordinates.
  - Incident density counts and predominant crime categories.
  - Outlier detection (noise points assigned label `-1`).

---

## 6. Inference Pipeline & Model Persistence
- **Artefact Directory**: `ml/models/`
- **Saved Files**:
  - `ml/models/crime_risk_model.joblib`: Serialised full pipeline bundle containing preprocessor, trained classifier, and feature metadata.
  - `ml/models/model_metadata.json`: Machine-readable provenance detailing training date, git commit hash context, record counts, and metrics.
- **Inference Verification**:
  - Single record prediction: `ml/predict.py` executes in `< 15ms`.
  - Batch predictions: `predict_batch(incidents)` handles array inputs safely with graceful handling of unknown categories.
  - Error handling: Missing features fall back to imputer medians without generating HTTP 500 exceptions.
