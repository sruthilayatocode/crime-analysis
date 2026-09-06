# CrimeSense Data Pipeline

> **Project:** CrimeSense — AI-Powered Crime Hotspot Analysis & Proximity Alert System  
> **Document:** Complete end-to-end data pipeline  
> **Authoritative source of statistics:** `data/reports/*.txt` and `data/final/*`

---

## Overview

CrimeSense ingests Vellore-district crime news, validates it, geocodes the
verified records, scores severity, and produces a clean handoff dataset that
is loaded into a backend database (`crime_incidents` table, keyed on
`article_id`). This document describes every stage, its inputs, processing,
outputs, and limitations, and reports the actual run statistics as recorded in
the pipeline reports — no figures are invented.

The pipeline is orchestrated by `scripts/run_pipeline.py` and supplemented by
dedicated scripts for each stage.

---

## Pipeline at a Glance

```
Google News RSS ─► raw candidates ─► validation ─► geocoding ─► enrichment
   │                                      │              │
   └──► clean/validate (264)              └──► 89 Vellore crime records
                                                      │
                                  ┌───────────────────┼──────────────────┐
                                  ▼                   ▼                  ▼
                          severity scoring      hotspot analysis   proximity alert
                                  │                   │                  │
                                  └───► final master dataset → SQLite DB → API
```

---

## Stage 1 — Data Acquisition

**Goal.** Collect candidate crime articles for Vellore district from public
news sources.

**Input.** Google News RSS search feeds. The collector
(`scripts/news_pipeline/collect_vellore_crime.py`) runs targeted search
queries that combine *"Vellore"* (and known Vellore-district localities such
as Katpadi, Ambur, and Ranipet) with crime keywords (*murder, theft, robbery,
arrest, …*).

**Processing.**
- Builds a list of search queries from the configured locality list
  (`data/reference/vellore_localities_config.json`).
- Fetches each RSS feed with HTTP retry/backoff and a runtime cap
  (`MAX_CANDIDATES=300`, ~10 min runtime limit).
- Parses RSS items (`title`, `link`, `pubDate`, `description`).

**Output.** `data/raw/vellore_crime_raw.csv` — the persisted candidate set.

> **Statistic:** **264 candidate records** collected (per
> `data/reports/data_quality_report.txt`, "Total input records: 264").

**Limitations.** Google News RSS is a search-based stream, not an exhaustive
official registry. It is biased toward reported, newsworthy incidents; small,
unreported, or rural crimes are under-represented. The stream only captures
what the feed returns for the configured queries on a given run.

---

## Stage 2 — Google News / RSS Collection

**Goal.** Retrieve and normalise raw article feeds into a structured,
deduplicated candidate set.

**Input.** Google News RSS search results for Vellore crime queries.

**Processing.**
- Standardise the raw RSS items into a common record shape
  (`article_id`, `title`, `published_date`, `source`, `url`, `crime_type`,
  `district`, `locality`, `description`, `collection_query`).
- Assign a deterministic hash-based `article_id` from the article URL so the
  same story is always mapped to the same primary key downstream.

**Output.** The structured candidate list persisted by the collector
(`data/raw/vellore_crime_raw.csv`, 264 records).

**Limitations.** RSS descriptions are short snippets; the source may be a
Google News redirect URL rather than the canonical publisher page. Date
parsing relies on the RSS `pubDate` format, and not all feeds are perfectly
consistent.

---

## Stage 3 — Deduplication

**Goal.** Remove repeated coverage of the same story before validation.

**Input.** Raw standardised RSS items.

**Processing.** The collector clears duplicates (the same story seen under
overlapping search queries). Deduplication is applied within the collection
stage so that the persisted candidate file contains unique articles.

**Output.** A unique candidate set written to `data/raw/vellore_crime_raw.csv`
— **264 unique candidates**.

> **Note:** Because de-duplication is embedded in collection, the 264
> records in `vellore_crime_raw.csv` are the single, non-duplicated candidate
> set carried into validation. Re-verified at every later stage: 0 duplicate
> `article_id` values in `news_validated.csv`, `news_scored_final.csv`, and
> `crimesense_master.csv`.

**Limitations.** Deduplication is URL/hash based, so near-duplicate rewritten
stories with different URLs may slip through, and identical stories re-hosting
at different feeds are still treated as one incident.

---

## Stage 4 — Crime Relevance Filtering

**Goal.** Keep only articles that describe a genuine criminal incident or
investigation.

**Input.** `data/raw/vellore_crime_raw.csv` — 264 candidate records.

**Processing.** `scripts/dataset_builder/validate_data.py` inspects each
article's title and description against explicit relevance rules
(documented in `data/reports/data_quality_report.txt`):

An article is **crime-relevant** only when its text explicitly describes an
actual criminal incident or investigation (arrests, murders, thefts,
assaults, drug seizures, fraud, court convictions, …).

Articles are **excluded as non-crime** when they:
- are behind a subscription/paywall (content inaccessible);
- are page-index/listing pages (generic titles such as "World", "Sports",
  "Other News" with snippet-style descriptions);
- describe budgets, government announcements, infrastructure, politics,
  elections, business, entertainment, sports, health or general news;
- merely mention crime-related words ("police", "arrest", "crime",
  "Tamil Nadu") **without** describing an actual criminal incident.

**Output.**
- Crime-relevant candidates carried forward: **157**
- Non-crime records removed: **107**
  (96 no genuine criminal incident described; 5 rain; 3 general/non-crime
  title; 1 actor; 1 film; 1 temple)
- Exclusion audit trail: `data/processed/news_excluded.csv`

**Limitations.** Filtering is rule/keyword based on limited RSS snippet text,
so borderline editorial pieces (e.g. protest coverage, court commentary) can
be mis-classified. Paywalled articles cannot be assessed and are dropped.
Every exclusion is recorded with its reason in `news_excluded.csv` for audit.

---

## Stage 5 — Vellore Location Validation

**Goal.** Retain only incidents that genuinely belong to Vellore district,
and correct the locality where the article names a specific place.

**Input.** The 157 crime-relevant candidates from Stage 4.

**Processing.** The same validator applies Vellore-relevance rules:

An article is kept only when it:
- explicitly refers to Vellore district, **or**
- refers to a locality belonging to Vellore district (configurable list in
  `data/reference/vellore_localities_config.json`: Vellore, Katpadi,
  Pallikonda, Arani, Ranipet, Tiruppattur, Ambur, …), **or**
- clearly describes an incident occurring inside Vellore district.

Articles are **excluded** when the incident occurred in another district or
state. Locality is **never** blindly set to "Vellore" when geocoding fails —
the article text is inspected for an explicit locality reference; if a
Vellore-district locality is named, that value is used, otherwise the
original value is preserved with `location_verified = False`.

**Output.**
- `data/processed/news_validated.csv` — **89 validated Vellore crime
  records** (`is_crime_relevant = True`, `location_verified` flag).
- `data/processed/news_excluded.csv` — **175 total exclusions**
  (107 non-crime + 68 crime-relevant-but-not-Vellore).

> **Statistic:** **89 validated crime records** (per
> `data_quality_report.txt`: "Vellore-relevant records: 89",
> "Final validated records: 89").

**Limitations.** Articles about Vellore *people* or *police* investigating
elsewhere are excluded, but some retained records describe Vellore-connected
events whose incident occurred outside the district (e.g. a Kolkata case
covered by Vellore media) — these are retained because they explicitly name a
Vellore locality, and this residual ambiguity is documented in the quality
report. The locality list is configurable and may need extension as new
place names appear.

---

## Stage 6 — Geographic Resolution / Geocoding

**Goal.** Attach latitude/longitude to validated records at the most specific
location the article actually supports — without ever inventing coordinates.

**Input.** `data/processed/news_validated.csv` (89 records).

**Processing.** `scripts/geocode_locations_v2.py` applies a strict,
hierarchy-driven resolution:

1. **Exact / landmark patterns** matched in title + description
   (`Katpadi railway station`, `Vellore Fort`, `Vellore GH`, `Pallikonda`,
   `Katpadi`).
2. **Locality / town patterns** for named Vellore-district towns.
3. **Nominatim (OpenStreetMap)** look-up for resolved place names, with a
   permanent cache at `data/cache/geocode_cache_v2.json` so the same place is
   never queried twice; results that are too broad (e.g. a whole district
   returned for a landmark query) are **rejected**, not accepted.
4. **District-only / ambiguous mentions** (`"in Vellore"`,
   `"Vellore man…"`, `"Vellore district…"`) are deliberately **not**
   geocoded — no district-centroid coordinate is fabricated.

Coordinates are validated against the Vellore bounding box
(lat 12.5–13.5, lon 78.5–79.8). The known-incorrect Arani cache entry
(13.331040, 80.083573 — actually in the Bay of Bengal) is excluded.

**Output.** `data/processed/news_geocoded_v2.csv` — 89 records with
`latitude` / `longitude` columns added (empty where unresolved).

> **Statistics** (per `data/reports/hotspot_analysis_report.txt`):
> **7 records with coordinates**, **82 without**. Resolved localities:
> Katpadi 5, Pallikonda 1, Vellore Fort 1, Vellore GH 1,
> Katpadi railway station 1; 80 records have no locality label.

**Limitations.** Only 7 of 89 records carry coordinates because most articles
name no place more specific than "Vellore". Nominatim is rate-limited and was
unavailable for some queries; two landmark queries (`Katpadi railway
station`, `Vellore GH`) were rejected as too broad and left un-geocoded
rather than guessed. Hotspot precision is therefore limited to the small
set of precisely geocoded incidents.

---

## Stage 7 — Location Confidence

**Goal.** Record how reliably each incident's location is known, so downstream
analysis never treats a vague mention as a precise point.

**Input.** `data/processed/news_validated.csv` (89 records).

**Processing.** `scripts/enrich_locations.py` inspects title + description
for explicit locality evidence and assigns:

| Level | Meaning |
|---|---|
| `HIGH` | An exact locality/landmark is explicitly evidenced in the text |
| `LOW` | Vellore is mentioned but no exact incident locality is stated |
| `UNKNOWN` | No reliable Vellore incident location can be established |

along with a `location_source` note explaining how the value was derived.

**Output.** `data/processed/news_location_enriched.csv` — 89 records with
`location_confidence` / `location_source`.

> **Statistics:** **HIGH 9, LOW 53, UNKNOWN 27** (of 89). Of the 9 HIGH
> records, 7 also carry coordinates.

**Limitations.** Confidence reflects *textual evidence*, not ground truth —
a HIGH label means the article names the place, not that the coordinate is
survey-accurate. Only HIGH-confidence records are eligible for spatial
clustering and proximity alerts; LOW/UNKNOWN records remain in the dataset
for locality-level and risk-level analysis but are never promoted to precise
points.

---

## Stage 8 — Severity Scoring

**Goal.** Assign every validated incident a deterministic severity score and
risk level from the project's standard crime taxonomy.

**Input.** `data/processed/news_location_enriched.csv` (89 records).

**Processing.**
1. `scripts/classify_crimes.py` re-classifies records whose upstream label is
   `Other`, using priority-ordered keyword rules (Murder → Assault → Sexual
   Assault → Cyber Crime → Robbery → Theft → Fraud) plus combination rules
   for Vehicle Theft (theft verb **and** vehicle keyword). Records that
   genuinely fit no category stay `Other`.
2. `scripts/score_crime_risk.py` maps `crime_type` →
   (`severity`, `risk_score`) using `data/reference/crime_categories.csv`,
   cross-checked against `data/reference/severity_mapping.csv`
   (Low=2, Medium=5, High=8, Critical=10). Unmapped types would be reported
   explicitly and left unscored — none remain.

**Output.** `data/processed/news_scored_final.csv` — 89 records with
`severity_score` / `risk_level`; report at
`data/reports/risk_scoring_final_report.txt`; classification audit at
`data/reports/crime_classification_report.txt`.

> **Statistics** (per `risk_scoring_final_report.txt`):
> **Crime types:** Murder 34, Theft 12, Assault 11, Sexual Assault 11,
> Robbery 6, Fraud 5, Other 4, Cyber Crime 3, Vehicle Theft 2,
> Domestic Violence 1.
> **Severity-score distribution:** 10 → 45, 8 → 18, 5 → 14, 2 → 12.
> **Risk-level distribution:** Critical 45, High 18, Medium 14, Low 12.
> **Records with missing severity: 0**; unmapped crime types: none.

**Limitations.** Scoring is a fixed lookup, not a learned model — two
incidents of the same category always receive the same score regardless of
aggravating factors. The `Other` fallback (Medium/5) is a safe default for
genuinely unclassifiable incidents (wildlife seizure, non-crime news).

---

## Stage 9 — Hotspot Analysis

**Goal.** Distinguish **verified crime locations** (exact coordinates) from
**statistical hotspots** (spatial clusters), without manufacturing clusters.

**Input.** `data/processed/news_geocoded_v2.csv` joined with
`data/processed/news_scored_final.csv` on `article_id` (severity/risk).

**Processing.** `scripts/analyze_hotspots.py`:
- Uses **only HIGH-confidence, in-bounds coordinates** for clustering
  (LOW/UNKNOWN are never promoted).
- Runs **DBSCAN** with Haversine distance; parameters are configurable and
  the effect of each combination is reported rather than blindly chosen.
- A cluster must contain **≥ 2 incidents**; isolated single incidents are
  noise, never hotspots.
- Computes per-hotspot weighted risk = mean severity of its incidents.

**Output.** `data/analysis/crime_hotspots.csv`,
`crime_by_locality_and_type.csv`, `crime_temporal_trends.csv`,
`hotspot_map_points.csv`, `locality_crime_summary.csv`; report at
`data/reports/hotspot_analysis_report.txt`.

> **Statistics** (per `hotspot_analysis_report.txt`):
> Spatial points used: **7** (of 89). Parameters: **eps = 1.5 km,
> min_samples = 3**. **Hotspots detected: 1** —
> **#1 Katpadi**: 5 incidents, weighted risk **7.20**, dominant crime
> **Robbery**, at (13.043505, 79.240410); Critical 1, High 3, Low 1.
> Pallikonda and Vellore Fort (1 incident each) are correctly treated as
> verified locations, **not** hotspots.

**Limitations.** With only 7 precisely geocoded incidents the statistical
power is minimal; the single hotspot reflects co-reported incidents at one
named locality rather than an independently confirmed crime pattern. 82
records cannot participate in spatial clustering at all. The analysis
explicitly states this insufficiency instead of manufacturing hotspots.

---

## Stage 10 — Proximity Alert

**Goal.** Given a user's current position, report nearby **verified** crime
locations and a transparent alert level.

**Input.** User `latitude` / `longitude` and a search radius
(`--radius`, default 2 km), plus the verified crime locations derived from
HIGH-confidence records (`data/analysis/hotspot_map_points.csv`; falls back to
`verified_location_summary.csv` when present).

**Processing.** `scripts/proximity_alert.py`:
- Computes **Haversine great-circle distance** in kilometres from the user to
  every verified location (Euclidean distance on raw degrees is never used).
- Keeps locations with `distance_km <= radius`, sorted by distance ascending.
- Classifies the alert deterministically (no ML):
  **CRITICAL** → a nearby verified location has Critical incidents;
  **HIGH** → High incidents; **MEDIUM** → Medium; **LOW** → only Low;
  **NONE** → no verified crime location within the radius.
- When nothing is found nearby it states that there is *insufficient verified
  geographic information* — never "no crimes exist nearby".

**Output.** `data/analysis/proximity_alert_results.csv` and
`data/reports/proximity_alert_report.txt`.

> **Statistics:** **3 verified crime locations** are known
> (Katpadi, Pallikonda, Vellore Fort). Reference test at the Katpadi
> coordinate with a 2 km radius finds **1 location at 0.000 km** and returns
> an overall alert of **CRITICAL** (Katpadi: 5 incidents, weighted risk 7.20,
> highest risk Critical). A control point several kilometres away correctly
> returns **NONE**.

**Limitations.** Alerts cover only the 3 verified locations; 82 records have
no usable coordinates and cannot generate proximity alerts. Distances are
straight-line, not walking/driving. The alert reflects reported *news*
incidents, not real-time police data.

---

## Stage 11 — Final Master Dataset

**Goal.** Produce one clean, de-duplicated handoff dataset for the backend
and database.

**Input.**
- `data/processed/news_scored_final.csv` (authoritative for title,
  crime_type, description, district, locality, is_crime_relevant,
  severity_score, risk_level)
- `data/processed/news_geocoded_v2.csv` (authoritative for latitude,
  longitude)

**Processing.** `scripts/build_master_dataset.py` performs a 1:1 join on
`article_id` (verified: 0 orphans on either side; `location_confidence`
identical in both sources). Unavailable fields are left NULL — nothing is
invented. It then runs field-level quality checks and emits the schema
document.

**Output.**
- `data/final/crimesense_master.csv` (89 × 16 columns)
- `data/final/crimesense_database_import.csv` (89 × 15 backend columns)
- `data/final/crimesense_database_schema.md`
- `data/final/master_dataset_quality_report.txt`

> **Statistics** (per `master_dataset_quality_report.txt`):
> Total 89 · unique 89 · duplicates 0 · with coordinates 7 · without 82 ·
> missing title/url/crime_type/published_date/severity/risk = 0 ·
> missing locality 80 · missing latitude/longitude 82.

The import file is then loaded by `scripts/init_database.py` into the
`crime_incidents` table of `database/crimesense.db` (SQLite, `article_id`
PRIMARY KEY, indexes on locality / crime_type / risk_level /
location_confidence) and served by the FastAPI backend (`backend/app.py`)
with endpoints for all crimes, crimes by locality / crime type / risk level,
hotspot data, and proximity results.

---

## Final Dataset Statistics

All figures below are read from the pipeline reports and output files; none
are estimated.

### Funnel

| Stage | Records | Source |
|---|---:|---|
| Raw articles collected (Google News RSS candidates) | **264** | `data/raw/vellore_crime_raw.csv` |
| Deduplicated candidates carried into validation | **264** | same file (dedup applied in collection) |
| Crime-relevant records | **157** | `data_quality_report.txt` |
| Non-crime records removed | 107 | `data_quality_report.txt` |
| Vellore-relevant / final validated records | **89** | `data_quality_report.txt` |
| Records excluded in total (non-crime + non-Vellore) | 175 | `data_quality_report.txt` |

### Geographic coverage

| Metric | Value |
|---|---:|
| Validated records | 89 |
| Records with coordinates | **7** |
| Records without coordinates | 82 |
| HIGH-confidence records | 9 |
| LOW-confidence records | 53 |
| UNKNOWN-confidence records | 27 |
| Unique verified locations | **3** (Katpadi, Pallikonda, Vellore Fort) |

Resolved localities (7 geocoded records): Katpadi 5, Pallikonda 1,
Vellore Fort 1. Named-but-unresolved localities: Katpadi railway station 1,
Vellore GH 1. Remaining 80 records carry no locality label.

### Risk distribution (89 records)

| Risk level | Incidents | Severity score |
|---|---:|---|
| Critical | 45 | 10 |
| High | 18 | 8 |
| Medium | 14 | 5 |
| Low | 12 | 2 |

### Crime type distribution (89 records)

| Crime type | Incidents |
|---|---:|
| Murder | 34 |
| Theft | 12 |
| Assault | 11 |
| Sexual Assault | 11 |
| Robbery | 6 |
| Fraud | 5 |
| Other | 4 |
| Cyber Crime | 3 |
| Vehicle Theft | 2 |
| Domestic Violence | 1 |

### Hotspot results

| Metric | Value |
|---|---:|
| Spatial points used for clustering | 7 |
| DBSCAN parameters | eps = 1.5 km, min_samples = 3 |
| Statistical hotspots detected | **1** |
| Largest hotspot | Katpadi — 5 incidents |
| Hotspot weighted risk score | 7.20 |
| Hotspot dominant crime type | Robbery |
| Verified locations (not hotspots) | Pallikonda (1), Vellore Fort (1) |

---

## Artefact Inventory

| Stage | Script | Output |
|---|---|---|
| Collection | `scripts/news_pipeline/collect_vellore_crime.py` | `data/raw/vellore_crime_raw.csv` |
| Validation | `scripts/dataset_builder/validate_data.py` | `news_validated.csv`, `news_excluded.csv`, `data/reports/data_quality_report.txt` |
| Geocoding | `scripts/geocode_locations_v2.py` | `news_geocoded_v2.csv`, `data/cache/geocode_cache_v2.json` |
| Confidence | `scripts/enrich_locations.py` | `news_location_enriched.csv` |
| Classification | `scripts/classify_crimes.py` | `data/reports/crime_classification_report.txt` |
| Scoring | `scripts/score_crime_risk.py` | `news_scored_final.csv`, `data/reports/risk_scoring_final_report.txt` |
| Hotspots | `scripts/analyze_hotspots.py` | `data/analysis/*.csv`, `data/reports/hotspot_analysis_report.txt` |
| Proximity | `scripts/proximity_alert.py` | `data/analysis/proximity_alert_results.csv`, `data/reports/proximity_alert_report.txt` |
| Master dataset | `scripts/build_master_dataset.py` | `data/final/crimesense_*.csv`, schema + quality report |
| Database | `scripts/init_database.py` | `database/crimesense.db` (`crime_incidents`) |
| API | `backend/app.py`, `backend/routes.py`, `backend/db.py` | FastAPI service on `/crimes`, `/hotspots`, `/proximity`, … |

---

## Reproducing the Pipeline

```bash
# 1. Collect candidates (network access to Google News RSS required)
python scripts/news_pipeline/collect_vellore_crime.py

# 2. Validate crime relevance + Vellore relevance
python scripts/dataset_builder/validate_data.py

# 3. Geocode verified records
python scripts/geocode_locations_v2.py

# 4. Assign location confidence
python scripts/enrich_locations.py

# 5. Re-classify 'Other' crime types
python scripts/classify_crimes.py

# 6. Score severity / risk
python scripts/score_crime_risk.py

# 7. Hotspot analysis
python scripts/analyze_hotspots.py

# 8. Proximity alert (example)
python scripts/proximity_alert.py --latitude 13.043505 --longitude 79.240410 --radius 2

# 9. Build the final master dataset
python scripts/build_master_dataset.py

# 10. Create and populate the database
python scripts/init_database.py

# 11. Serve the API
uvicorn backend.app:app --host 0.0.0.0 --port 8000
```

Stages 3–6 can also be run together via `python scripts/run_pipeline.py`.

---

## Cross-Cutting Data Integrity Rules

1. **No record is ever deleted.** All 89 validated incidents appear in every
   downstream dataset; exclusions are written to `news_excluded.csv`.
2. **No coordinate is invented.** Unresolved locations stay NULL; district
   centroids are never used as incident points.
3. **Confidence is never upgraded.** LOW/UNKNOWN locations are excluded from
   spatial clustering and proximity alerts.
4. **Scores are looked up, not learned.** `severity_score` / `risk_level`
   come from the reference taxonomy and are identical for identical categories.
5. **Raw data is immutable.** Every stage writes a new file under
   `data/processed/` or `data/final/`.
6. **Every exclusion and unmapped value is reported**, never silently dropped.

---

## Version History

| Version | Date | Changes |
|---|---|---|
| 1.0 | 2026-08-21 | Initial documentation of the implemented CrimeSense pipeline (collection → validation → geocoding → scoring → hotspots → proximity → master dataset → database/API). |

---

*End of Data Pipeline Documentation*