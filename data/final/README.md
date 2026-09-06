# Final Data

## Purpose

This directory stores the **fully processed, geocoded, and feature-engineered** crime dataset ready for machine learning consumption. Final data is the end product of the entire data pipeline and serves as the authoritative input for model training, evaluation, and inference.

## Contents

| File Pattern | Description |
|---|---|
| `{city}_crime_final.csv` | Complete dataset with all features, geocoded coordinates, and derived columns |
| `{city}_crime_final_metadata.json` | Dataset metadata including column descriptions, row count, date range, and feature list |
| `{city}_crime_train.csv` | Training split (typically 70% of the data) |
| `{city}_crime_val.csv` | Validation split (typically 15% of the data) |
| `{city}_crime_test.csv` | Test split (typically 15% of the data) |

## Naming Rules

- Format: `{city}_crime_final.csv`
- Example: `vellore_crime_final.csv`
- Train/validation/test splits use `_train`, `_val`, `_test` suffixes
- Metadata files use the `_metadata.json` suffix

## Do's

- Include all 26 columns as defined in the Data Dictionary (§4.1)
- Verify geocoding quality — at least 95% of records must have valid coordinates
- Generate train/val/test splits using stratified sampling to preserve class distribution
- Document the feature engineering steps applied in a companion metadata file
- Version each final dataset with a timestamp or version number in the metadata

## Don'ts

- Do **not** include raw or unprocessed records
- Do **not** include personally identifiable information (PII)
- Do **not** modify the final dataset manually — regenerate from the pipeline
- Do **not** overwrite the previous version without updating the version history