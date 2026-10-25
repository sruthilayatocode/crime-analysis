"""Persistent stores: candidates, incidents, provenance. Nothing existing is
overwritten — the new datasets live under data/raw/candidates/,
data/processed/incidents/ and data/provenance/."""
from __future__ import annotations
import json, re, unicodedata
from datetime import date
from pathlib import Path

from scripts.collection.config import (CANDIDATE_DIR, PROVENANCE_DIR,
                                       INCIDENTS_DIR)

CAND_DIR = Path(CANDIDATE_DIR)
CAND_DIR.mkdir(parents=True, exist_ok=True)
PROV_DIR = Path(PROVENANCE_DIR)
PROV_DIR.mkdir(parents=True, exist_ok=True)
INC_DIR = Path(INCIDENTS_DIR)
INC_DIR.mkdir(parents=True, exist_ok=True)

CANDIDATES_JSON = CAND_DIR / "article_candidates.json"
FETCHED_JSON = CAND_DIR / "fetched_urls.json"
INCIDENTS_JSON = INC_DIR / "incidents.json"
PROVENANCE_JSON = PROV_DIR / "provenance.json"


def _load(path: Path, default):
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return default
    return default


def _save(path: Path, data) -> None:
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    tmp.replace(path)


# ---- fetched-URL ledger (dedup of fetch work) ----
def fetched_urls() -> set:
    return set(_load(FETCHED_JSON, []))


def mark_fetched(urls) -> None:
    have = fetched_urls()
    have.update(urls)
    _save(FETCHED_JSON, sorted(have))


# ---- candidate articles ----
def load_candidates() -> list:
    return _load(CANDIDATES_JSON, [])


def add_candidates(rows) -> int:
    """Append candidates keyed by URL; returns number added."""
    cur = load_candidates()
    by_url = {r.get("source_url"): r for r in cur}
    added = 0
    for r in rows:
        u = r.get("source_url")
        if u and u not in by_url:
            cur.append(r)
            by_url[u] = r
            added += 1
    if added:
        _save(CANDIDATES_JSON, cur)
    return added


# ---- incidents ----
def load_incidents() -> list:
    return _load(INCIDENTS_JSON, [])


def save_incidents(rows) -> None:
    _save(INCIDENTS_JSON, rows)


def upsert_incidents(rows) -> dict:
    """Merge validated incident rows (keyed by incident_id)."""
    cur = {r.get("incident_id"): r for r in load_incidents()}
    added = updated = 0
    for r in rows:
        iid = r.get("incident_id")
        if not iid:
            continue
        if iid in cur:
            cur[iid].update({k: v for k, v in r.items() if v not in (None, "")})
            updated += 1
        else:
            cur[iid] = r
            added += 1
    save_incidents(list(cur.values()))
    return {"added": added, "updated": updated}


# ---- provenance ----
def load_provenance() -> list:
    return _load(PROVENANCE_JSON, [])


def add_provenance(rows) -> int:
    cur = load_provenance()
    keyset = {(r.get("incident_id"), r.get("source_url")) for r in cur}
    added = 0
    for r in rows:
        if r.get("source_url") and \
                (r.get("incident_id"), r["source_url"]) not in keyset:
            cur.append(r)
            keyset.add((r.get("incident_id"), r["source_url"]))
            added += 1
    if added:
        _save(PROVENANCE_JSON, cur)
    return added


def normalize_title(t) -> str:
    t = unicodedata.normalize("NFKD", str(t or "")).lower()
    return re.sub(r"[^a-z0-9 ]+", " ", t).strip()
