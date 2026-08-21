# Data

## Purpose
All data artifacts organized by processing stage from raw ingestion through to final curated datasets.

## Structure
- `raw/` — Raw data from government, news, police, and archived sources
- `processed/` — Cleaned and transformed data ready for analysis
- `geo/` — Geospatial data files (shapefiles, GeoJSON)
- `ml/` — Data prepared for machine learning (train/validation/test splits)
- `final/` — Final curated datasets for production use

## Future Work
- Add data versioning with DVC
- Implement automated data pipeline orchestration
- Add data quality monitoring and alerting
- Create data catalog with schema documentation