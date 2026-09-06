# Dataset Pipeline — Crime Analysis

> **Project:** AI-Powered Crime Hotspot Analysis and Proximity Alert System  
> **Version:** 1.0  
> **Last Updated:** 2026-07-28

---

## Overview

The dataset pipeline is the backbone of the Crime Analysis system. It ingests raw crime data from multiple heterogeneous sources, validates and cleans it, enriches it with geocoded coordinates and engineered features, and produces a final curated dataset ready for machine learning. This document describes each stage of the pipeline in detail.

---

## Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         DATA SOURCES                                │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐   │
│  │Government│  │  Police  │  │   News   │  │   Open Data      │   │
│  │  NCRB    │  │    FIR   │  │ Articles │  │   Portals        │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └───────┬──────────┘   │
│       │             │             │                 │              │
└───────┼─────────────┼─────────────┼─────────────────┼──────────────┘
        │             │             │                 │
        ▼             ▼             ▼                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         STAGE 1: RAW DATA                           │
│                                                                     │
│  Directory: data/raw/                                               │
│  Subdirectories: government/, police/, news/, archived/             │
│  Format: Original source format (CSV, JSON, PDF, HTML)              │
│  Rule: Immutable — never modify raw files in-place                  │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         STAGE 2: VALIDATION                         │
│                                                                     │
│  Script: scripts/dataset_builder/validate_dataset.py                │
│                                                                     │
│  Activities:                                                        │
│  ├── Schema validation — check column names, data types, null rates │
│  ├── Range validation — verify lat/lon, dates, counts within bounds │
│  ├── Uniqueness check — ensure no duplicate incident IDs            │
│  ├── Cross-field validation — date vs day_of_week consistency       │
│  └── Quality scoring — compute completeness, accuracy, timeliness   │
│                                                                     │
│  Output: Validation report (JSON) with pass/fail per record         │
│  Gate: Records failing critical validations are quarantined         │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         STAGE 3: CLEANING                           │
│                                                                     │
│  Script: scripts/dataset_builder/clean_data.py                      │
│                                                                     │
│  Activities:                                                        │
│  ├── Handle missing values (drop, fill, or impute)                  │
│  ├── Standardise date/time formats to ISO 8601                      │
│  ├── Normalise categorical values to standard taxonomy              │
│  ├── Remove duplicate records based on incident_id                  │
│  ├── Correct data types (string→date, string→float, etc.)           │
│  └── Remove outliers using IQR or Z-score methods                   │
│                                                                     │
│  Output: Cleaned dataset (CSV) + cleaning log                       │
│  Directory: data/processed/                                         │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         STAGE 4: GEOCODING                          │
│                                                                     │
│  Script: scripts/dataset_builder/geocode.py                         │
│                                                                     │
│  Activities:                                                        │
│  ├── Convert address strings to lat/lon coordinates                 │
│  ├── Batch geocoding with rate limiting                             │
│  ├── Reverse geocode for coordinate validation                      │
│  ├── Fallback strategy for failed geocodes (landmark→approximate)   │
│  └── Cache previously geocoded addresses to reduce API calls        │
│                                                                     │
│  Geocoding Providers (configurable):                                │
│  ├── Google Maps Geocoding API (primary)                            │
│  ├── OpenStreetMap Nominatim (fallback)                             │
│  └── Local gazetteer for Vellore landmarks (offline)                │
│                                                                     │
│  Quality Target: ≥95% of records successfully geocoded              │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    STAGE 5: FEATURE ENGINEERING                     │
│                                                                     │
│  Script: ml/feature_engineering.py                                  │
│                                                                     │
│  Activities:                                                        │
│  ├── Temporal features:                                             │
│  │   ├── day_of_week (Monday–Sunday)                                │
│  │   ├── hour_of_day (0–23)                                         │
│  │   ├── month (1–12)                                               │
│  │   ├── season (Summer, Monsoon, Post-Monsoon, Winter)             │
│  │   └── is_weekend (boolean)                                       │
│  ├── Geographic features:                                           │
│  │   ├── geo_cluster_id (from DBSCAN/K-means spatial clustering)    │
│  │   ├── distance_to_nearest_hotspot (meters)                       │
│  │   ├── distance_to_nearest_police_station (meters)                │
│  │   └── crime_density_score (normalised incidents per sq. km)      │
│  ├── Aggregated features:                                           │
│  │   ├── crime_frequency_7d (incidents in last 7 days at location)  │
│  │   ├── crime_frequency_30d (incidents in last 30 days)            │
│  │   └── same_category_ratio (proportion of same-category crimes)   │
│  └── Encoding:                                                      │
│      ├── One-hot encoding for categorical variables                 │
│      └── Label encoding for ordinal variables                       │
│                                                                     │
│  Output: Feature-engineered dataset (CSV)                           │
│  Directory: data/final/                                             │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         STAGE 6: FINAL DATASET                      │
│                                                                     │
│  Directory: data/final/                                             │
│                                                                     │
│  Contents:                                                          │
│  ├── {city}_crime_final.csv — Complete dataset with all features    │
│  ├── {city}_crime_train.csv — Training split (70%)                  │
│  ├── {city}_crime_val.csv   — Validation split (15%)                │
│  ├── {city}_crime_test.csv  — Test split (15%)                     │
│  └── {city}_crime_metadata.json — Column descriptions, version info │
│                                                                     │
│  Splitting Strategy:                                                │
│  ├── Stratified by crime_category to preserve class distribution    │
│  ├── Temporal split: train = earlier periods, test = later periods  │
│  └── Random seed fixed for reproducibility                          │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      STAGE 7: MACHINE LEARNING                      │
│                                                                     │
│  Scripts: ml/train_model.py, ml/predict.py                          │
│                                                                     │
│  Activities:                                                        │
│  ├── Load final dataset from data/final/                            │
│  ├── Train hotspot prediction models (XGBoost, Random Forest)       │
│  ├── Hyperparameter tuning with cross-validation                    │
│  ├── Model evaluation and selection                                 │
│  └── Model serialisation for deployment                             │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Stage Details

### Stage 1: Raw Data Ingestion

**Responsible script:** `scripts/dataset_builder/download_data.py`

Raw data is ingested from the sources documented in `docs/Data_Sources.md`. Each source is stored in its respective subdirectory under `data/raw/`. Files are named according to the convention `{source}_{city}_{period}.{ext}`.

**Key principles:**
- Raw files are **immutable** — never modified after ingestion
- Each file is accompanied by a `.meta.json` sidecar file containing source URL, download timestamp, file hash, and any preprocessing notes
- Large files are compressed using `.gz` to save space

**Validation gate:** Before moving to Stage 2, a quick integrity check verifies that files are not corrupted (checksum validation) and have the expected number of columns.

---

### Stage 2: Validation

**Responsible script:** `scripts/dataset_builder/validate_dataset.py`

Every record in the raw dataset is validated against the rules defined in the Data Dictionary (§8). Records that fail critical validations are quarantined in a separate file for manual review.

**Validation categories:**

| Category | Checks | Action on Failure |
|---|---|---|
| Critical | Missing required fields, out-of-range coordinates | Quarantine record |
| Warning | Missing optional fields, unusual values | Log warning, include record |
| Informational | Format inconsistencies, minor deviations | Log info, auto-correct |

**Output:** A validation report (`{city}_validation_report.json`) is generated with:
- Total records processed
- Pass/fail counts per validation rule
- List of quarantined records with failure reasons
- Overall data quality score (0.0–1.0)

---

### Stage 3: Cleaning

**Responsible script:** `scripts/dataset_builder/clean_data.py`

Cleaning transforms the validated raw data into a consistent, standardised format. All cleaning operations are logged for auditability.

**Cleaning operations applied in order:**

1. **Deduplication** — Remove exact duplicates based on `incident_id`. Near-duplicates (same date, location, and category) are flagged for manual review.
2. **Missing value handling** — Columns with >50% missing values are dropped. Remaining missing values are handled per column:
   - Numeric columns: fill with median
   - Categorical columns: fill with mode
   - Date columns: drop record if date is missing
3. **Type casting** — Force columns to their expected data types (e.g., string→date, string→float)
4. **Categorical normalisation** — Map source-specific category names to the standard taxonomy defined in `docs/Crime_Categories.md`
5. **Outlier removal** — Remove records where numerical fields exceed 3 standard deviations from the mean (after log transformation for skewed distributions)

**Output:** Cleaned dataset saved to `data/processed/{city}_crime_clean.csv`

---

### Stage 4: Geocoding

**Responsible script:** `scripts/dataset_builder/geocode.py`

Geocoding converts textual location descriptions into precise latitude/longitude coordinates. This is a critical step because spatial analysis and hotspot detection depend on accurate coordinates.

**Geocoding workflow:**

```
Address string
    │
    ▼
Check geocoding cache
    │
    ├── Cache hit → Return cached coordinates
    │
    └── Cache miss
            │
            ▼
        Try Google Maps Geocoding API
            │
            ├── Success → Store in cache, return coordinates
            │
            └── Failure
                    │
                    ▼
                Try OpenStreetMap Nominatim
                    │
                    ├── Success → Store in cache, return coordinates
                    │
                    └── Failure
                            │
                            ▼
                        Fallback: Use landmark-based approximation
                            │
                            ▼
                        Log failed geocode for manual review
```

**Quality metrics tracked:**
- Geocoding success rate (target: ≥95%)
- Average geocoding accuracy (distance between geocoded and true location)
- API call volume and cost tracking

---

### Stage 5: Feature Engineering

**Responsible script:** `ml/feature_engineering.py`

Feature engineering creates derived attributes that help machine learning models identify patterns in crime data. Features are grouped into temporal, geographic, and aggregated categories.

**Temporal features** capture time-based patterns:
- Crimes are not uniformly distributed across time — weekends see different crime patterns than weekdays
- Certain crimes (e.g., burglary) peak during daytime when homes are empty
- Seasonal effects: theft increases during festival seasons, chain snatching is more common in crowded markets

**Geographic features** capture spatial patterns:
- `geo_cluster_id` is assigned using DBSCAN clustering on historical crime locations
- `crime_density_score` is computed using kernel density estimation (KDE) over a 500m grid
- Distance to nearest police station is a proxy for response time and deterrence

**Aggregated features** capture recent crime trends:
- `crime_frequency_7d` and `crime_frequency_30d` capture short-term and medium-term trends
- These features help the model understand if a location is experiencing a crime surge

---

### Stage 6: Final Dataset

**Output directory:** `data/final/`

The final dataset is the culmination of all previous stages. It contains all 26 columns defined in the Data Dictionary (§4.1) and is split into training, validation, and test sets.

**Splitting strategy:**

| Split | Proportion | Purpose | Method |
|---|---|---|---|
| Training | 70% | Model training | Stratified random sampling by crime_category |
| Validation | 15% | Hyperparameter tuning | Stratified random sampling |
| Test | 15% | Final evaluation | Held-out set, never used during development |

**Reproducibility:** All splits use a fixed random seed (`42`) to ensure that repeated runs produce identical splits.

---

### Stage 7: Machine Learning

**Responsible scripts:** `ml/train_model.py`, `ml/predict.py`

The final dataset is consumed by the ML pipeline for training hotspot prediction models. This stage is documented separately in the ML module documentation.

---

## Pipeline Orchestration

The entire pipeline is orchestrated using a dependency-based execution model:

```
download_data.py
    │
    ▼
validate_dataset.py
    │
    ▼
clean_data.py
    │
    ▼
geocode.py
    │
    ▼
feature_engineering.py
    │
    ▼
export_dataset.py
```

Each script can be run independently, but downstream scripts expect the output of upstream scripts to be present. A Makefile or shell script will be provided to run the full pipeline with a single command.

---

## Data Flow Diagram

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  NCRB    │    │  Police  │    │   News   │    │  Open    │
│  Data    │    │   FIR    │    │ Articles │    │  Data    │
└────┬─────┘    └────┬─────┘    └────┬─────┘    └────┬─────┘
     │               │               │               │
     ▼               ▼               ▼               ▼
┌─────────────────────────────────────────────────────────────┐
│                    data/raw/                                 │
│  government/  │  police/  │  news/  │  archived/            │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              validate_dataset.py                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  Schema  │  │  Range   │  │Uniqueness│  │  Cross-  │   │
│  │Validation│  │Validation│  │  Check   │  │  field   │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                 clean_data.py                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │Dedup     │  │ Missing  │  │  Type    │  │Outlier   │   │
│  │          │  │  Handle  │  │  Cast    │  │ Remove   │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              data/processed/                                │
│              vellore_crime_clean.csv                        │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   geocode.py                                │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  Google  │  │   OSM    │  │  Cache   │  │  Fallback│   │
│  │  Maps    │  │Nominatim │  │  Layer   │  │  Logic   │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              feature_engineering.py                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ Temporal │  │Geographic│  │Aggregated│  │ Encoding │   │
│  │Features  │  │Features  │  │Features  │  │          │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              data/final/                                    │
│  vellore_crime_final.csv  │  _train  │  _val  │  _test     │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              train_model.py  →  predict.py                  │
│              Machine Learning Pipeline                      │
└─────────────────────────────────────────────────────────────┘
```

---

## Error Handling

| Stage | Error Type | Handling Strategy |
|---|---|---|
| Ingestion | Network failure | Retry with exponential backoff (3 attempts) |
| Validation | Schema mismatch | Log error, quarantine file, continue pipeline |
| Cleaning | Unparseable date | Drop record, log warning |
| Geocoding | API quota exceeded | Switch to fallback provider, log alert |
| Feature Engineering | Division by zero | Use epsilon (1e-10) to avoid NaN |
| Export | Disk full | Abort pipeline, notify operator |

---

## Monitoring and Logging

Each pipeline stage produces structured logs with the following fields:

- `timestamp` — When the event occurred
- `stage` — Pipeline stage name
- `status` — `STARTED`, `IN_PROGRESS`, `COMPLETED`, `FAILED`
- `records_processed` — Number of records handled
- `records_failed` — Number of records that failed
- `duration_seconds` — Time taken for the stage
- `error_message` — Description of any error encountered

Logs are written to `logs/pipeline.log` with daily rotation.

---

## Version History

| Version | Date | Author | Changes |
|---|---|---|---|
| 1.0 | 2026-07-28 | Data Engineering Team | Initial pipeline documentation with 7 stages |

---

*End of Dataset Pipeline*