# CrimeSense — Human Collection Guide

This guide explains how a researcher adds **real, source-backed** crime incidents
to the CrimeSense validation pipeline. The pipeline does **NOT** scrape or invent
data — it only transforms records a human supplies after verifying them against a
real public source article or page.

---

## 1. Where collected records go

Create/place one **JSON batch** per submission inside:

```
data/raw/collected_sources/batches/
```

Name batches sequentially: `batch_001.json`, `batch_002.json`, … (they are
processed in name order). A batch is a JSON **array** of incident objects.

> Note: a legacy single file at `data/raw/collected_sources/input.json` is still
> accepted (treated as one more batch), but the batch folder is the recommended,
> incremental way to add records.

---

## 2. Required / accepted fields

Each incident object maps onto the canonical CrimeSense schema. Use any of the
accepted name variants (aliases are mapped automatically):

| Canonical field | Accepted input names | Required? |
|---|---|---|
| `article_id` | `article_id`, `id` | optional |
| `title` | `title`, `headline` | **yes** |
| `published_date` | `published_date` | recommended |
| `incident_date` | `incident_date` | optional (kept as provenance) |
| `source` | `source`, `publication`, `outlet` | **yes** |
| `url` | `url`, `source_url` | **yes** — a real verifiable link |
| `crime_type` | `crime_type`, `type` | **yes** (normalized by pipeline) |
| `description` | `description` | optional |
| `district` | `district` | recommended (Vellore district) |
| `locality` | `locality` | optional (falls back to district) |
| `state` | `state` | optional (e.g. Tamil Nadu; kept as provenance) |
| `latitude` | `latitude`, `lat` | leave empty if unknown |
| `longitude` | `longitude`, `lng`, `lon` | leave empty if unknown |
| `location_confidence` | `location_confidence`, `geo_confidence` | required if coords given |
| `location_source` | `location_source`, `geo_source` | required if coords given |
| `severity_score` | `severity_score` | optional numeric |
| `risk_level` | `risk_level` | optional |

Example batch entry:

```json
{
  "headline": "Man held for murder in Vellore",
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

---

## 3. How to record a source

- Every record **must** include a real `url`/`source_url` that links to the
  article or page describing that individual incident.
- One real-world incident = one record. If multiple outlets cover the same
  incident, keep **one** record (the pipeline deduplicates cross-outlet too, but
  do not submit duplicate URLs).
- If the source only gives a publication date, use that in `published_date` and
  note it — never invent an incident date. If coordinates are unknown, leave
  `latitude`/`longitude` empty. If you do supply coordinates, also supply
  `location_source` and `location_confidence`.

---

## 4. How to run validation + regenerate the final dataset

From the project root (`c:\Users\sruth\crime analysis`):

```bash
python scripts/expand_crimesense_dataset.py
```

This:
- validates every row (required fields, valid URL, Vellore relevance, valid
  coordinates/date, numeric severity),
- rejects invalid rows (reported, not silently dropped),
- normalizes crime_type to the canonical vocabulary,
- deduplicates across outlets/batches,
- appends unique, schema-valid rows to the persistent registry and regenerates
  the final CSV.

---

## 5. How duplicates are handled

- Deduplication uses a deterministic key = normalized `title | locality |
  crime_type | year` (ignoring the source field, so the same story covered by
  different outlets is one record).
- On a match, the **first** validated record is kept and the later one is
  removed. A report in `data/analysis/deduplication_report.md` lists every
  suspected duplicate and the decision.
- Records already accepted are never re-added; the persistent registry
  (`data/processed/accepted_incidents.json`) preserves them across runs.

---

## 6. The existing 89 records

`data/final/crimesense_database_import.csv` (the validated 89) is **never
modified** by this pipeline. New records are only placed in the **separate**
output file `data/final/crimesense_database_import_expanded.csv`.

---

## 7. Outputs regenerated each run

| Path | Contents |
|---|---|
| `data/raw/collected_incidents.csv` | as-collected ledger (preserves provenance) |
| `data/processed/accepted_incidents.json` | persistent validated unique registry |
| `data/processed/crimesense_expanded_candidates.csv` | validated/normalized rows |
| `data/final/crimesense_database_import_expanded.csv` | final unique, schema-valid |
| `data/analysis/deduplication_report.md` | duplicates + decision |
| `data/analysis/validation_report.md` | totals, by year/type/source, dropped rows |
| `data/analysis/collection_summary.md` | source summary |

---

## Integrity rules (non-negotiable)

- No fabricated, synthesized, or extrapolated incidents.
- Missing geography stays **NULL** — never invent coordinates or geocode a vague
  location into fake precision.
- Each record is traceable to one real source.
- No aggregate statistics are converted into individual rows.
- The existing 89 validated records are never changed.