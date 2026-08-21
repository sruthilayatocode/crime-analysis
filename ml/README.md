# Machine Learning

## Responsibility

This folder contains the machine learning pipeline for the Crime Analysis project. It is responsible for consuming the final curated dataset produced by the data pipeline and training predictive models that identify crime hotspots with high risk scores.

## What Belongs Here

| File | Responsibility |
|---|---|
| `train_model.py` | Load the final dataset from `data/final/`, train hotspot prediction models (XGBoost, Random Forest, LightGBM), perform hyperparameter tuning, and save the trained model to disk |
| `predict.py` | Load a serialised model and generate hotspot risk predictions for new location data; includes single-prediction and batch-prediction modes |
| `feature_engineering.py` | Create derived features from the processed dataset including temporal features (day_of_week, hour, season), geographic features (clusters, density scores), and aggregated features (crime frequency windows) |
| `__init__.py` | Package initialisation |

## Folder Responsibility

- **Model training** — Train, validate, and select the best-performing hotspot prediction model
- **Inference** — Provide prediction capabilities for real-time and batch use cases
- **Feature engineering** — Transform raw features into ML-ready representations
- **Reproducibility** — All training runs use fixed random seeds and logged hyperparameters
- **Model versioning** — Trained models are serialised with version metadata for traceability

## Relationship with Data Pipeline

This folder is the downstream consumer of the data pipeline. The pipeline at `scripts/dataset_builder/` produces the final dataset at `data/final/`, which is then ingested by `train_model.py`. Feature engineering (`feature_engineering.py`) sits at the boundary — it can be used by the data pipeline during export or called independently during model training.

## Future Work

- Implement automated hyperparameter search (Optuna, GridSearchCV)
- Add model evaluation metrics (precision, recall, F1, AUC-ROC)
- Add model explainability using SHAP and LIME
- Integrate model predictions with the backend API for real-time serving
- Add A/B testing framework for model deployment