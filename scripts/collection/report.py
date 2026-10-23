"""Audit reporting + final CSV export for the incident pipeline.

Produces the research-paper metrics: discovered/fetched/rejected/accepted/
duplicates/valid incidents + breakdowns by source, year, crime type, locality,
geocoding status. Writes:
  - data/final/crimesense_incidents_v2.csv        (full incident-level schema)
  - data/final/crimesense_import_v2_canonical.csv (15-col backend-compatible)
  - data/provenance/incident_provenance.csv       (source link table)
The protected 89-record CSV is never touched; totals are reported additively.
"""
from __future__ import annotations
import csv, io, json, os
from collections import Counter
from pathlib import Path

from scripts.collection.config import (FINAL_DIR, PROVENANCE_DIR,
                                       PROTECTED_FINAL_CSV, INCIDENTS_CSV,
                                       CANONICAL_CSV, PROVENANCE_CSV,
                                       TARGET_INCIDENTS)

FULL_FIELDS = ["incident_id", "incident_date", "incident_year", "crime_type",
               "crime_subtype", "description", "locality", "police_station",
               "district", "latitude", "longitude", "source_name",
               "source_url", "source_publication_date", "case_number",
               "crime_number", "source_type", "confidence_score",
               "geocoding_status", "validation_status", "duplicate_group_id",
               "n_sources", "scope_class"]

# 15-column canonical schema (matches the existing backend import format).
CANONICAL_FIELDS = ["article_id", "title", "date", "crime_type", "description",
                    "district", "locality", "state", "latitude", "longitude",
                    "location_confidence", "location_source",
                    "severity_score", "risk_level", "source"]

PROV_FIELDS = ["incident_id", "source_name", "source_url",
               "source_publication_date", "source_type", "title", "is_primary"]


def _write(path: Path, fields, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=fields, lineterminator="\n",
                       extrasaction="ignore")
    w.writeheader()
    for r in rows:
        w.writerow({k: r.get(k, "") for k in fields})
    tmp = path.with_suffix(".csv.tmp")
    tmp.write_text(buf.getvalue(), encoding="utf-8")
    os.replace(tmp, path)


def export_csvs(incidents: list, provenance: list) -> dict:
    _write(INCIDENTS_CSV, FULL_FIELDS, incidents)
    prov = [p for p in provenance if p.get("is_primary")] or provenance
    prim_by_iid = {p["incident_id"]: p for p in prov}
    canon = []
    for r in incidents:
        p = prim_by_iid.get(r["incident_id"], {})
        canon.append({
            "article_id": r.get("incident_id"),
            "title": (r.get("description") or "")[:120],
            "date": r.get("incident_date")
                    or r.get("source_publication_date") or "",
            "crime_type": r.get("crime_type"),
            "description": r.get("description"),
            "district": r.get("district") or "Vellore",
            "locality": r.get("locality"),
            "state": "Tamil Nadu",
            "latitude": r.get("latitude"),
            "longitude": r.get("longitude"),
            "location_confidence": r.get("geocoding_status"),
            "location_source": "gazetteer",
            "severity_score": "",
            "risk_level": "",
            "source": p.get("source_name") or r.get("source_name") or "",
        })
    _write(CANONICAL_CSV, CANONICAL_FIELDS, canon)
    _write(PROVENANCE_CSV, PROV_FIELDS, provenance)
    return {"incidents_csv": str(INCIDENTS_CSV),
            "canonical_csv": str(CANONICAL_CSV),
            "provenance_csv": str(PROVENANCE_CSV),
            "canonical_rows": len(canon)}


def print_report(stats: dict, incidents: list) -> None:
    n = len(incidents)
    existing = 89
    lines = ["", "=" * 64, "  CRIMESENSE COLLECTION RUN REPORT", "=" * 64,
             f"  discovered URLs        : {stats.get('discovered', 0)}",
             f"  fetched articles       : {stats.get('fetched', 0)}",
             f"  extraction failures    : {stats.get('fetch_failed', 0)}",
             f"  rejected (scope/crime) : {stats.get('rejected', 0)}",
             f"  accepted candidates    : {stats.get('accepted', 0)}",
             f"  duplicates collapsed   : {stats.get('duplicates', 0)}",
             f"  valid incidents (run)  : {n}",
             f"  incidents total (v2)   : {n}",
             f"  + existing validated   : {existing}",
             f"  = dataset total        : {n + existing}",
             f"  target                 : {TARGET_INCIDENTS}",
             "-" * 64]
    for field, label in (("source_name", "by source"),
                         ("incident_year", "by year"),
                         ("crime_type", "by crime type"),
                         ("locality", "by locality")):
        c = Counter((r.get(field) or "(unknown)") for r in incidents)
        lines.append(f"  {label}: " + ", ".join(
            f"{k}={v}" for k, v in c.most_common(12)))
    geo = Counter(r.get("geocoding_status") or "unknown" for r in incidents)
    lines.append(f"  geocoding: " + ", ".join(f"{k}={v}" for k, v in geo.items()))
    conf = Counter(r.get("confidence_score") for r in incidents)
    lines.append(f"  confidence: " + ", ".join(f"{k}={v}" for k, v in conf.items()))
    lines.append("=" * 64)
    print("\n".join(lines))
