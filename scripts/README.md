# Scripts

## Responsibility

This folder contains all data engineering utility scripts for the Crime Analysis project. These scripts form the executable layer of the data pipeline — they perform the actual work of downloading, cleaning, geocoding, and transforming crime data from raw sources into ML-ready datasets.

## What Belongs Here

All scripts in this folder are organised into the `dataset_builder/` package, which contains the end-to-end data pipeline:

| Script | Responsibility |
|---|---|
| `dataset_builder/__init__.py` | Package initialisation and exports |
| `dataset_builder/download_data.py` | Download raw crime data from government, police, and news sources |
| `dataset_builder/scrape_news.py` | Extract crime incident information from news articles |
| `dataset_builder/extract_locations.py` | Parse and extract geographic locations from unstructured text |
| `dataset_builder/geocode.py` | Convert addresses and place names to latitude/longitude coordinates |
| `dataset_builder/merge_data.py` | Combine records from multiple sources into a unified dataset |
| `dataset_builder/clean_data.py` | Standardise formats, handle missing values, remove duplicates |
| `dataset_builder/validate_dataset.py` | Run schema, range, and integrity checks on the dataset |
| `dataset_builder/export_dataset.py` | Export the final dataset to CSV, JSON, Parquet formats |
| `dataset_builder/utils.py` | Shared helper functions for file I/O, JSON, and logging |

## Folder Responsibility

- **Data pipeline execution** — Each script is a self-contained pipeline stage
- **Reproducibility** — Scripts accept parameters and can be re-run to produce identical output
- **Modularity** — Each script has a single responsibility and can be run independently
- **Auditability** — Every script logs its operations for traceability

## Future Work

- Add CLI entry points using `click` or `argparse` for all pipeline stages
- Create a pipeline orchestrator (Makefile or shell script) to run stages in dependency order
- Add support for configuration via YAML config files
- Add unit tests for each pipeline stage