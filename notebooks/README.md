# Notebooks

## Responsibility

This folder contains Jupyter notebooks used for exploratory data analysis (EDA), data visualisation, prototyping, and experimentation. Notebooks are the research and discovery layer of the project — they allow data engineers and data scientists to interactively explore the dataset, test hypotheses, and prototype feature engineering approaches before committing them to production scripts.

## What Belongs Here

| File Pattern | Responsibility |
|---|---|
| `01_eda_{city}.ipynb` | Exploratory data analysis — understand data distributions, missing values, outliers, and basic statistics |
| `02_visualisation_{city}.ipynb` | Data visualisation — crime heatmaps, time-series plots, category distributions, geographic scatter plots |
| `03_feature_prototyping.ipynb` | Prototype new feature engineering approaches before implementing in `ml/feature_engineering.py` |
| `04_model_benchmark.ipynb` | Quick model benchmarking — compare multiple algorithms on sample data before full training |
| `05_geocoding_quality.ipynb` | Evaluate geocoding accuracy, visualise geocoded points on maps, identify failed geocodes |

## Folder Responsibility

- **Exploration** — Understand the data before building production pipelines
- **Prototyping** — Test feature engineering and modelling approaches interactively
- **Visualisation** — Create charts, maps, and plots for presentations and reports
- **Documentation** — Notebooks serve as executable documentation of data analysis decisions
- **Reproducibility** — Notebooks should be self-contained with clear markdown explanations

## Guidelines

- Notebooks should be numbered in logical order (01, 02, 03...)
- Each notebook should start with a markdown cell explaining its purpose
- Use consistent variable names and coding style across notebooks
- Clear all cell outputs before committing to version control
- Do not store large datasets in notebooks — reference files from `data/` directories
- Convert successful prototypes to production scripts in `scripts/` or `ml/` when ready

## Future Work

- Add parameterised notebooks using Papermill for automated report generation
- Convert key notebooks to HTML reports for sharing with stakeholders
- Add integration with MLflow for experiment tracking
- Create a dashboard notebook for real-time data quality monitoring