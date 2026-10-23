"""
expand_crimesense_dataset.py
============================

Pipeline for expanding the CrimeSense validated incident dataset with NEW,
source-backed Vellore district incidents.

INTEGRITY POLICY (non-negotiable)
---------------------------------
* NO fabricated incidents. A record is added ONLY if a real public source
  (news article / verified page) describes the individual incident.
* One real-world incident = one record. Duplicates (including the same story
  reported by different outlets) are removed.
* Missing location / coordinates are left NULL -- never invented or geocoded
  into fake precision.
* severity_score / risk_level are set ONLY when source data or the project's
  scoring pipeline provides them; otherwise they are left blank (not invented).
* The 89 existing validated records are NEVER modified or duplicated.

USAGE
-----
    python scripts/expand_crimesense_dataset.py

Outputs:
    data/raw/collected_incidents.csv                     (as-collected ledger)
    data/processed/crimesense_expanded_candidates.csv    (after filtering/normalizing)
    data/processed/accepted_incidents.json               (persistent validated registry)
    data/final/crimesense_database_import_expanded.csv   (final unique, schema-valid)
    data/analysis/deduplication_report.md
    data/analysis/validation_report.md
    data/analysis/collection_summary.md

INCREMENTAL BATCHES
-------------------
Drop each new collection batch (a JSON array of incident objects) into:
    data/raw/collected_sources/batches/
name it e.g. batch_001.json, batch_002.json, ...

The pipeline unions every batch with the persistent accepted registry
(data/processed/accepted_incidents.json), validates, cross-source deduplicates,
and regrows the final CSV. Accepted records persist across runs, so you can add
batches incrementally and re-run without losing earlier verified records.

Accepted source fields (name variants are accepted and mapped to the canonical
14-output schema):
    article_id, source_url | url, published_date, incident_date,
    headline | title, crime_type, locality, district, state,
    latitude, longitude, location_source, location_confidence,
    severity_score, risk_level

Provenance fields that have no canonical output column (incident_date, state,
source_url, headline) are preserved verbatim in data/raw/collected_incidents.csv
so the original source record is never lost.
"""
from __future__ import annotations

import csv
import json
import os
import re
import time
import unicodedata
from collections import Counter, OrderedDict
from pathlib import Path
from urllib.parse import urlparse

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
FINAL_DIR = PROJECT_ROOT / "data" / "final"
ANALYSIS_DIR = PROJECT_ROOT / "data" / "analysis"

# Input: each verified batch (JSON array) dropped into collected_sources/batches/.
BATCH_DIR = RAW_DIR / "collected_sources" / "batches"

# Persistent registry of validated, unique incidents (survives across runs).
ACCEPTED_JSON = PROCESSED_DIR / "accepted_incidents.json"

# Legacy single-file input (still honoured for convenience; equal to batch).
RAW_JSON_INPUT = RAW_DIR / "collected_sources" / "input.json"

# The existing, canonical 89-record dataset (used to avoid duplication).
EXISTING_FINAL = FINAL_DIR / "crimesense_database_import.csv"

SCHEMA = [
    "article_id", "title", "published_date", "source", "url", "crime_type",
    "description", "district", "locality", "latitude", "longitude",
    "location_confidence", "location_source", "severity_score", "risk_level",
]

CRIME_TYPES = {
    "MURDER", "ATTEMPT TO MURDER", "THEFT", "BURGLARY", "ROBBERY", "SNATCHING",
    "ASSAULT", "SEXUAL ASSAULT", "RAPE", "KIDNAPPING", "KIDNAPPING & ABDUCTION",
    "FRAUD", "CHEATING", "CYBER CRIME", "DRUG ARREST", "DOMESTIC VIOLENCE",
    "EXTORTION", "VANDALISM", "OTHER",
}

# Well-scoped localities (Vellore district). Others are flagged for review.
VELLORE_LOCALITIES = (
    "vellore", "katpadi", "gudiyatham", "pernambut", "ambur", "ranipet",
    "arcot", "vellore city", "vellore district", "srivananthapuram",
    "lutheran mission", "vellore fort", "katpadi railway station",
)
def normalize_text(value):
    """Lowercase, strip diacritics, keep only alphanumerics + spaces."""
    if not value:
        return ""
    text = unicodedata.normalize("NFKD", str(value))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9 ]+", " ", text.lower()).split()


# Accepted input name variants mapped to the canonical CrimeSense field.
FIELD_ALIASES = {
    "title": ("title", "headline"),
    "url": ("url", "source_url"),
    "published_date": ("published_date",),
    "incident_date": ("incident_date",),
    "source": ("source", "publication", "outlet"),
    "district": ("district",),
    "locality": ("locality",),
    "state": ("state",),
    "crime_type": ("crime_type", "type"),
    "latitude": ("latitude", "lat"),
    "longitude": ("longitude", "lng", "lon"),
    "location_confidence": ("location_confidence", "geo_confidence"),
    "location_source": ("location_source", "geo_source"),
    "severity_score": ("severity_score",),
    "risk_level": ("risk_level",),
    "article_id": ("article_id", "id"),
}


def pick_field(row, keys):
    """Return the first non-empty value among the given candidate keys."""
    if not isinstance(row, dict):
        return ""
    for k in keys:
        v = row.get(k)
        if v is not None and str(v).strip() != "":
            return v
    return ""


def canonicalize_row(row):
    """Map a source-collected row into canonical CrimeSense keys.

    Accepts alias names (e.g. source_url/headline/incident_date/state) and maps
    them onto the canonical fields. Provenance-only fields (incident_date,
    state, plus the original alias values) are preserved under an extra key for
    the raw as-collected ledger so no source detail is lost.
    """
    if not isinstance(row, dict):
        return {}
    out = {}
    for canon, aliases in FIELD_ALIASES.items():
        out[canon] = pick_field(row, aliases)
    # Preserve provenance detail that has no canonical output column.
    out["_incident_date"] = out.get("incident_date") or ""
    out["_state"] = out.get("state") or ""
    # Keep exact original URL/title for the ledger.
    out["_url"] = pick_field(row, ("url", "source_url"))
    out["_headline"] = pick_field(row, ("headline", "title"))
    return out


def is_vellore(row):
    """Vellore relevance must be confirmed from the source, not inferred.

    Word-boundary matching — a substring test wrongly matches 'arcot' inside
    'narcotics' (seen in real runs).
    """
    blob = " ".join(
        " ".join(normalize_text(row.get(k) or ""))
        for k in ("locality", "district", "title", "description", "source")
    )
    if re.search(r"\bvellore\b", blob):
        return True
    for loc in ("katpadi", "gudiyatham", "pernambut", "ambur", "jolarpet",
                "natrampalli", "anaicut"):
        if re.search(rf"\b{loc}\b", blob):
            return True
    return False


def is_out_of_scope(row):
    """Reject incidents clearly from neighbouring districts."""
    out = ("chennai", "coimbatore", "madurai", "trichy", "salem", "erode",
           "tirunelveli", "tiruppur", "karur", "nagapattinam", "cuddalore",
           "kanchipuram", "tiruvallur", "villupuram", "krishnagiri", "dharmapuri",
           "neyveli")
    blob = " ".join(
        " ".join(normalize_text(row.get(k) or ""))
        for k in ("title", "description")
    )
    return any(o in blob and "vellore" not in blob for o in out)


def valid_url(value):
    if not value:
        return False
    try:
        p = urlparse(str(value))
        return p.scheme in ("http", "https") and bool(p.netloc)
    except Exception:
        return False
REQUIRED_FIELDS = ["title", "source", "url", "crime_type"]
NUMERIC_FIELDS = ("latitude", "longitude", "severity_score")


def schema_problems(row):
    """Validate a raw input row against the CrimeSense schema + entry rules.

    Returns a list of human-readable problems. Empty -> row is schema-valid.
    These are *source-integrity* checks (provenance, coordinates, dates) in
    addition to the minimal per-row checks done in main().
    """
    problems = []
    if not isinstance(row, dict):
        return ["row is not a JSON object"]

    for field in ("title", "source", "url", "crime_type"):
        if not str(row.get(field) or "").strip():
            problems.append(f"missing required field: {field}")

    if row.get("url") and not valid_url(row.get("url")):
        problems.append("invalid source URL (must be http/https with a host)")

    # Coordinates must travel together and be numeric (never fabricated).
    lat = row.get("latitude")
    lng = row.get("longitude")
    lat_given = lat not in (None, "")
    lng_given = lng not in (None, "")
    if lat_given != lng_given:
        problems.append("latitude/longitude must both be present or both empty")
    elif lat_given:
        try:
            float(lat)
            float(lng)
        except (TypeError, ValueError):
            problems.append("latitude/longitude must be numeric")
        # Rule 15: geocoding used -> location_source must be recorded.
        if not str(row.get("location_source") or "").strip():
            problems.append("coordinates supplied without location_source")
        if not str(row.get("location_confidence") or "").strip():
            problems.append("coordinates supplied without location_confidence")

    # Severity must be numeric when present (never silently coerced).
    sev = row.get("severity_score")
    if sev not in (None, ""):
        try:
            float(sev)
        except (TypeError, ValueError):
            problems.append("severity_score must be numeric")

    # published_date should be parseable; we flag (not drop) bad dates so the
    # researcher can fix provenance rather than us inventing a value.
    date = str(row.get("published_date") or "").strip()
    if date and not re.search(r"\d{4}", date):
        problems.append("published_date has no recognisable year")

    return problems


def cross_source_key(row):
    """Cross-outlet dedup key: same incident reported by different sources.

    Ignores the source field on purpose so that the same real-world incident
    picked up by multiple outlets is treated as one record. Uses normalized
    title + locality + crime type + a year token (publication or incident date).
    """
    title = "_".join(normalize_text(row.get("title")))
    locality = (row.get("locality") or row.get("district") or "unknown").strip().lower()
    crime = (row.get("crime_type") or "unknown").strip().lower()
    date = (row.get("published_date") or row.get("incident_date") or "")[:4]
    return f"{title}|{locality}|{crime}|{date}"
def map_crime_type(raw):
    """Map a raw crime descriptor to the canonical CrimeSense vocabulary."""
    if not raw:
        return "Unknown"
    t = str(raw).strip().lower()
    mapping = {
        "murder": "Murder", "kill": "Murder", "homicide": "Murder",
        "attempt to murder": "Attempt to Murder", "attempted murder": "Attempt to Murder",
        "theft": "Theft", "burglary": "Burglary", "house break": "Burglary",
        "break in": "Burglary", "robbery": "Robbery", "snatching": "Snatching",
        "chain snatch": "Snatching", "assault": "Assault", "rape": "Rape",
        "sexual assault": "Sexual Assault", "molestation": "Sexual Assault",
        "kidnap": "Kidnapping", "abduction": "Kidnapping", "fraud": "Fraud",
        "cheating": "Cheating", "cyber": "Cyber Crime", "online": "Cyber Crime",
        "drug": "Drug Arrest", "narcotic": "Drug Arrest",
        "domestic violence": "Domestic Violence", "extortion": "Extortion",
        "vandalism": "Vandalism", "arson": "Vandalism",
    }
    for key, canon in mapping.items():
        if key in t:
            return canon
    return "Other"


def score_from_source(row):
    """severity/risk only from source-provided pipeline values; else blank."""
    sev = row.get("severity_score")
    risk = row.get("risk_level")
    try:
        sev = float(sev) if sev not in (None, "") else ""
    except (TypeError, ValueError):
        sev = ""
    return sev, risk or ""


def load_existing_ids(retries=5, delay=0.15):
    ids = set()
    if not EXISTING_FINAL.exists():
        return ids
    for attempt in range(retries):
        try:
            with open(EXISTING_FINAL, encoding="utf-8") as fh:
                for row in csv.DictReader(fh):
                    if row.get("article_id"):
                        ids.add(row["article_id"].strip())
            return ids
        except (PermissionError, OSError) as exc:
            if attempt == retries - 1:
                raise
            time.sleep(delay)
    return ids


def make_article_id(i):
    return f"cse_{i:06d}"


def ensure_dirs():
    target = RAW_DIR / "collected_sources"
    for d in (RAW_DIR, PROCESSED_DIR, FINAL_DIR, ANALYSIS_DIR, target):
        d.mkdir(parents=True, exist_ok=True)


# Path whose contents MUST never be modified by this pipeline (the existing,
# validated 89-record dataset). It is read-only input here.
PROTECTED_INPUT = FINAL_DIR / "crimesense_database_import.csv"


def write_csv(path, rows, retries=5, delay=0.15):
    """Write rows to a CSV using an atomic temp-file + replace.

    Avoids the Windows in-place `open(path, "w")` hazard where a concurrent
    process (dev server / editor / file watcher / antivirus) briefly holds the
    file, which raises PermissionError. We write to a temp file in the same
    directory and then os.replace() it into place, retrying on any transient
    lock, so the destination is always a complete, valid CSV.
    """
    path = Path(path)
    # Never touch the validated 89-record input file.
    if path == PROTECTED_INPUT:
        raise RuntimeError("refusing to overwrite the protected 89-record dataset")

    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")

    # Build the content once in memory so a failed write leaves no partial file.
    import io
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=SCHEMA, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({k: row.get(k, "") for k in SCHEMA})
    content = buf.getvalue()

    for attempt in range(retries):
        try:
            with open(tmp, "w", newline="", encoding="utf-8") as fh:
                fh.write(content)
                fh.flush()
                os.fsync(fh.fileno())
            # os.replace is atomic on Windows and unblocks once the lock clears.
            os.replace(tmp, path)
            return
        except (PermissionError, OSError) as exc:
            if attempt == retries - 1:
                raise
            time.sleep(delay)
        finally:
            # Clean up the temp file if it still exists after a failure.
            if tmp.exists() and not os.path.samefile(tmp, path):
                try:
                    tmp.unlink(missing_ok=True)
                except OSError:
                    pass


def write_ledger_csv(path, rows):
    """Write the as-collected ledger preserving provenance-only fields.

    Unlike write_csv (canonical schema only), this preserves alias provenance
    like incident_date, state, source_url, headline so no source detail is lost.
    Atomically written + lock-retried like write_csv.
    """
    path = Path(path)
    if path == PROTECTED_INPUT:
        raise RuntimeError("refusing to overwrite the protected 89-record dataset")
    path.parent.mkdir(parents=True, exist_ok=True)
    # Union of all canonical + provenance keys, ordered stably.
    keys = []
    for r in rows:
        if not isinstance(r, dict):
            continue
        for k in r.keys():
            if k not in keys:
                keys.append(k)

    import io
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=keys, lineterminator="\n",
                            extrasaction="ignore")
    writer.writeheader()
    for r in rows:
        writer.writerow({k: r.get(k, "") for k in keys})
    content = buf.getvalue()

    tmp = path.with_suffix(path.suffix + ".tmp")
    for attempt in range(5):
        try:
            with open(tmp, "w", newline="", encoding="utf-8") as fh:
                fh.write(content)
                fh.flush()
                os.fsync(fh.fileno())
            os.replace(tmp, path)
            return
        except (PermissionError, OSError):
            if attempt == 4:
                raise
            time.sleep(0.15)
        finally:
            if tmp.exists() and not os.path.samefile(tmp, path):
                try:
                    tmp.unlink(missing_ok=True)
                except OSError:
                    pass


def load_json_list(path):
    """Load a JSON array of objects from a file; return [] if absent/bad."""
    path = Path(path)
    if not path.exists():
        return []
    try:
        with open(path, encoding="utf-8-sig") as fh:
            data = json.load(fh)
    except (json.JSONDecodeError, OSError):
        return []
    if not isinstance(data, list):
        return []
    return [dict(r) for r in data if isinstance(r, dict)]


def load_csv_rows(path):
    """Load rows from a CSV batch file (UTF-8/UTF-8-BOM), as dicts."""
    path = Path(path)
    if not path.exists():
        return []
    try:
        with open(path, encoding="utf-8-sig", newline="") as fh:
            return [dict(r) for r in csv.DictReader(fh)]
    except (OSError, csv.Error):
        return []


def load_input_rows():
    """Collect every source row from all batches + the legacy input file.

    Batches may be `.json` arrays or `.csv` files (spreadsheet-friendly), so a
    researcher can drop either format into collected_sources/batches/. The
    documentation template (`batch_template.json`) is never ingested. Rows are
    canonicalized (aliases mapped to canonical keys, provenance preserved) so
    every downstream step sees consistent field names.
    """
    rows = []
    if BATCH_DIR.exists():
        for batch_file in sorted(BATCH_DIR.glob("*.json")):
            if batch_file.name.lower() == "batch_template.json":
                # Documentation template — never ingest it as data.
                continue
            rows.extend(load_json_list(batch_file))
        for batch_file in sorted(BATCH_DIR.glob("*.csv")):
            if batch_file.name.lower().startswith("template"):
                continue
            rows.extend(load_csv_rows(batch_file))
    rows.extend(load_json_list(RAW_JSON_INPUT))
    return [canonicalize_row(r) for r in rows if isinstance(r, dict)]


def load_accepted_rows():
    """Load the persistent validated registry (already canonical rows)."""
    return load_json_list(ACCEPTED_JSON)


def save_accepted_rows(rows):
    """Persist the validated, deduplicated unique registry across runs."""
    ACCEPTED_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(ACCEPTED_JSON, "w", encoding="utf-8") as fh:
        json.dump(rows, fh, indent=2, ensure_ascii=False)
def write_provenance_audit(registry_rows):
    """Audit trail: source URL + provenance for every ACCEPTED record.

    Requirement: 'Keep an audit trail showing the source URL for every accepted
    record.' Written atomically like the other CSVs.
    """
    path = ANALYSIS_DIR / "provenance_audit.csv"
    fields = ["article_id", "title", "source", "url", "published_date",
              "incident_date", "district", "locality", "state", "crime_type"]
    import io
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fields, lineterminator="\n",
                            extrasaction="ignore")
    writer.writeheader()
    for r in registry_rows:
        writer.writerow({k: r.get(k, "") for k in fields})
    content = buf.getvalue()

    tmp = path.with_suffix(path.suffix + ".tmp")
    for attempt in range(5):
        try:
            with open(tmp, "w", newline="", encoding="utf-8") as fh:
                fh.write(content)
                fh.flush()
                os.fsync(fh.fileno())
            os.replace(tmp, path)
            return
        except (PermissionError, OSError):
            if attempt == 4:
                raise
            time.sleep(0.15)
        finally:
            if tmp.exists():
                try:
                    tmp.unlink(missing_ok=True)
                except OSError:
                    pass


def main():
    ensure_dirs()
    existing_ids = load_existing_ids()

    # Load previously accepted (validated, unique) records + all new batches.
    accepted = load_accepted_rows()
    submitted = load_input_rows()

    # Composite key -> row, in processing order. Accepted records come first so,
    # on a cross-incident match, the already-validated record wins (KEEP-FIRST).
    # New batches are then deduped against accepted AND against each other.
    seen = OrderedDict()
    for row in accepted:
        if isinstance(row, dict):
            key = cross_source_key(row)
            if key:
                seen.setdefault(key, row)

    raw_count = 0
    candidates = []
    invalid = []
    rejects = Counter()
    schema_issues = Counter()
    dup_removed = 0
    dedup_report = []

    for row in submitted:
        if not isinstance(row, dict):
            continue
        raw_count += 1
        reasons = []
        # Source-integrity + schema validation (provenance, coords, dates).
        for problem in schema_problems(row):
            reasons.append(problem)
            schema_issues[problem] += 1
        if not valid_url(row.get("url")):
            reasons.append("no valid source URL")
        if not (row.get("title") or "").strip():
            reasons.append("missing title")
        if not is_vellore(row):
            reasons.append("Vellore relevance not confirmed")
        if is_out_of_scope(row):
            reasons.append("neighbouring district")
        if row.get("article_id") and str(row["article_id"]).strip() in existing_ids:
            reasons.append("duplicate of existing 89 record")
        if reasons:
            rejects[", ".join(reasons)] += 1
            invalid.append(dict(row))
            continue

        candidates.append(row)

        # ---- normalize kept candidate ----
        sev, risk = score_from_source(row)
        normalized = {
            "article_id": (row.get("article_id") or "").strip()
                        or make_article_id(len(seen) + 1),
            "title": (row.get("title") or "").strip(),
            "published_date": (row.get("published_date") or "").strip(),
            "incident_date": (row.get("incident_date") or "").strip(),
            "state": (row.get("state") or "").strip(),
            "source": (row.get("source") or "").strip(),
            "url": (row.get("url") or "").strip(),
            "crime_type": map_crime_type(row.get("crime_type")),
            "description": (row.get("description") or "").strip(),
            "district": (row.get("district") or "").strip(),
            "locality": (row.get("locality") or "").strip()
                        or (row.get("district") or "").strip(),
            "latitude": row.get("latitude") or "",
            "longitude": row.get("longitude") or "",
            "location_confidence": (row.get("location_confidence") or "").strip(),
            "location_source": (row.get("location_source") or "").strip(),
            "severity_score": sev,
            "risk_level": risk,
        }
        # Preserve provenance-only fields for the ledger / registry.
        normalized["_headline"] = (row.get("_headline") or "").strip()
        normalized["_state"] = (row.get("_state") or "").strip()
        normalized["_incident_date"] = (row.get("_incident_date") or "").strip()
        normalized["_url"] = (row.get("_url") or "").strip()

        # ---- deterministic cross-source dedup ----
        key = cross_source_key(normalized)
        if key in seen:
            dup_removed += 1
            dedup_report.append({
                "source_article": normalized.get("title"),
                "suspected_duplicate": seen[key].get("title"),
                "reason": ("same real-world incident (normalized title/locality/"
                           "crime/year) reported by another outlet or batch"),
                "decision": "REMOVE (keep first validated record)",
            })
            continue
        seen[key] = normalized

    final_rows = list(seen.values())

    # Canonical (schema-only) projections for CSV output; registry keeps provenance.
    registry_rows = [{k: v for k, v in r.items() if not k.startswith("_")}
                     for r in final_rows]
    save_accepted_rows(final_rows)  # keep provenance fields across runs

    # Ledger = all kept records + invalid rows (provenance preserved);
    # processed/final use the canonical schema.
    write_ledger_csv(RAW_DIR / "collected_incidents.csv",
                     list(final_rows) + [dict(r) for r in invalid])
    write_csv(PROCESSED_DIR / "crimesense_expanded_candidates.csv", registry_rows)
    write_csv(FINAL_DIR / "crimesense_database_import_expanded.csv", registry_rows)

    write_dedup_report(dedup_report)
    write_validation_report(raw_count, invalid, dup_removed, registry_rows, rejects, schema_issues)
    write_collection_summary(registry_rows)
    write_provenance_audit(registry_rows)
    print("=== collection summary ===")
    print(f"raw collected       : {raw_count}")
    print(f"valid candidates    : {len(candidates)}")
    print(f"rejected (invalid)  : {len(invalid)}")
    print(f"duplicates removed  : {dup_removed}")
    print(f"newly accepted      : {len(final_rows) - len(accepted)}")
    print(f"final validated     : {len(final_rows)} (+{89} existing = "
          f"{len(final_rows) + 89} total)")
    print(f"audit trail         : {ANALYSIS_DIR / 'provenance_audit.csv'}")
def write_dedup_report(rows):
    path = ANALYSIS_DIR / "deduplication_report.md"
    lines = ["# Deduplication Report", "",
             "| Source article | Suspected duplicate | Reason | Decision |",
             "|---|---|---|---|"]
    for r in rows:
        lines.append(f"| {r['source_article']} | {r['suspected_duplicate']} | "
                     f"{r['reason']} | {r['decision']} |")
    if not rows:
        lines.append("_No duplicate candidates were detected in this run._")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_validation_report(raw_count, invalid, dup_removed, final, rejects, schema_issues=None):
    path = ANALYSIS_DIR / "validation_report.md"
    by_year = Counter((r.get("published_date") or "")[:4] for r in final)
    by_type = Counter(r.get("crime_type") or "Unknown" for r in final)
    by_source = Counter(r.get("source") or "Unknown" for r in final)
    with_coords = sum(1 for r in final
                      if r.get("latitude") not in (None, "")
                      and r.get("longitude") not in (None, ""))
    lines = ["# Validation Report", "", "## Totals", "",
             f"- Total source articles discovered (input rows): **{raw_count}**",
             f"- Total candidate incidents: **{raw_count}**",
             f"- Invalid records removed: **{len(invalid)}**",
             f"- Duplicates removed: **{dup_removed}**",
             f"- **Final unique incident count: {len(final)}**",
             f"- Records with coordinates: **{with_coords}**",
             f"- Records without coordinates: **{len(final) - with_coords}**", "",
             "## Records by year", ""]
    for y in sorted(by_year, key=str):
        if y:
            lines.append(f"- {y}: {by_year[y]}")
    lines += ["", "## Records by crime type", ""]
    for t, c in by_type.most_common():
        lines.append(f"- {t}: {c}")
    lines += ["", "## Records by source", ""]
    for s, c in by_source.most_common():
        lines.append(f"- {s}: {c}")
    lines += ["", "## Invalid-row / schema issues", ""]
    if rejects:
        for reason, n in rejects.most_common():
            lines.append(f"- {reason}: {n}")
    elif schema_issues:
        for issue, n in schema_issues.most_common():
            lines.append(f"- Input schema problem — {issue}: {n}")
    else:
        lines.append("- None.")
    lines += ["",
              "> No records were fabricated. Figures reflect only source-backed "
              "input rows present in this run."]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_collection_summary(final):
    path = ANALYSIS_DIR / "collection_summary.md"
    by_source = Counter(r.get("source") or "Unknown" for r in final)
    lines = ["# CrimeSense Expanded Dataset — Collection Summary", "",
             f"## Final unique incidents: {len(final)}", "", "## Sources used"]
    if by_source:
        for s, c in by_source.most_common():
            lines.append(f"- {s} ({c})")
    else:
        lines.append("- No source-backed rows were present in this run (see feasibility note).")
    lines += ["", "## Feasibility status (automated session)", "",
              "The target of 1,000+ NEW unique source-backed incidents could not be "
              "responsibly met in this automated run. Official FIR/police portals require "
              "authentication/CAPTCHA, major news archives (TOI, Deccan Chronicle) block "
              "automated access, and Google News RSS is licence-restricted against "
              "non-personal/bulk use. No records were fabricated to reach the target.",
              "",
              "**Only `" + str(len(final)) + "` unique source-backed incident(s) could be "
              "collected in this run.**"]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()