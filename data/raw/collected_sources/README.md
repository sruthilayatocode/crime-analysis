# CrimeSense Dataset Expansion — How to Supply Source-Backed Incidents

This pipeline does **not** scrape or generate data. It transforms **manually /
source-collected** incident rows (verified against real public sources) into the
CrimeSense schema and produces validation/dedup reports.

> **Read the full `HUMAN_COLLECTION_GUIDE.md` in this folder first.** It covers
> required fields, source recording, validation, deduplication, and regeneration.

## Step 1 — Add your batch

Place each batch as a JSON file in:

```
data/raw/collected_sources/batches/
```

Name them `batch_001.json`, `batch_002.json`, … Each file is a JSON **array** of
incident objects. A single legacy file at `data/raw/collected_sources/input.json`
is also accepted as one batch.

Example entry (aliases like `headline`, `source_url`, `incident_date`, `state`
are accepted and mapped to the canonical schema):

```json
{
  "headline": "Man arrested for murder in Vellore",
  "source_url": "https://www.thehindu.com/.../vellore-murder",
  "published_date": "2025-01-10",
  "incident_date": "2025-01-09",
  "source": "The Hindu",
  "crime_type": "murder",
  "description": "A 30-year-old man was arrested following a murder reported in Vellore.",
  "district": "Vellore",
  "locality": "Vellore",
  "state": "Tamil Nadu",
  "latitude": "",
  "longitude": ""
}
```

A ready-to-edit template is at `data/raw/collected_sources/batches/batch_template.json`.

## Step 2 — Run the pipeline

```
python scripts/expand_crimesense_dataset.py
```

## What the pipeline does

1. **Input schema validation** — checks required fields, source-URL validity,
   coordinate pairing/numeric type, numeric severity, and date sanity. Rows
   failing validation are reported and excluded (never silently coerced).
2. **Vellore relevance + scope filter** — confirms each row is Vellore-related
   and rejects neighbouring-district incidents.
3. **Existing-89 duplicate check** — rejects any row matching an existing
   validated record's article_id so the 89 are never duplicated.
4. **Normalization** — maps raw crime descriptors to the canonical CrimeSense
   vocabulary; locality falls back to district; empty coords stay empty.
5. **Dedup (cross-outlet, cross-batch)** — the same real-world incident reported
   by multiple outlets/batches counts once, using normalized
   title / locality / crime / year.
6. **Incremental accumulation** — a persistent registry
   (`data/processed/accepted_incidents.json`) keeps accepted records across runs;
   add new batches and re-run without losing earlier verified records.
7. **Output generation + reports**.

Crime types recognized by `map_crime_type` include (not exhaustive):
Murder, Attempt to Murder, Theft, Burglary, Robbery, Snatching, Assault, Rape,
Sexual Assault, Kidnapping, Fraud, Cheating, Cyber Crime, Drug Arrest,
Domestic Violence, Extortion, Vandalism, Other.

## Integrity rules enforced

- A row is added only if a real public source URL describes the individual
  incident. Missing/unknown coordinates stay **empty** — never invented or
  geocoded into fake precision.
- If coordinates are supplied, `location_source` and `location_confidence`
  are required (provenance).
- `severity_score` / `risk_level` are kept only when the source/scoring pipeline
  provides them; otherwise left blank.
- The existing 89 validated records are never modified or duplicated.
- No aggregate statistics are converted into individual rows.

## Outputs

| Path | Contents |
|---|---|
| `data/raw/collected_incidents.csv` | as-supplied rows |
| `data/processed/crimesense_expanded_candidates.csv` | after validation/filter |
| `data/final/crimesense_database_import_expanded.csv` | final unique schema-valid |
| `data/analysis/deduplication_report.md` | suspected duplicates & decision |
| `data/analysis/validation_report.md` | totals, by year/type/source, dropped rows |
| `data/analysis/collection_summary.md` | summary + sources used |