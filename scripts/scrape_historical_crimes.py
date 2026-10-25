"""
scripts/scrape_historical_crimes.py
===================================
Multi-source historical crime data scraper for CrimeSense.
Scrapes individual criminal incidents from Wikipedia tables.
ONLY accepts records that fall within the Vellore-region geographic scope.
"""
from __future__ import annotations
import argparse, re, sys, time, unicodedata, uuid
from datetime import date
from pathlib import Path
import requests
from bs4 import BeautifulSoup

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKEND = PROJECT_ROOT / "backend"
DEFAULT_DB = BACKEND / "instance" / "crimesense.db"
sys.path.insert(0, str(BACKEND))

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "CrimeSenseResearchBot/1.0 (+academic research)"})

SOURCES = [
    ("https://en.wikipedia.org/wiki/List_of_terrorist_incidents_in_India",
     "Wikipedia - Terrorist incidents in India", "Terrorism"),
    ("https://en.wikipedia.org/wiki/List_of_riots_in_India",
     "Wikipedia - Riots in India", "Riots"),
    ("https://en.wikipedia.org/wiki/List_of_railway_accidents_in_India",
     "Wikipedia - Railway accidents in India", "Railway accident"),
    ("https://en.wikipedia.org/wiki/List_of_massacres_in_India",
     "Wikipedia - Massacres in India", "Massacre"),
]
EARLIEST_YEAR = 1970
LATEST_YEAR = date.today().year

# ============================================================
# VELLORE-REGION GEOGRAPHIC SCOPE
# ============================================================
VELLORE_REGION_LOCALITIES = {
    "vellore", "katpadi", "gudiyatham", "gudiyattam", "pernambut",
    "ambur", "vaniyambadi", "tirupattur", "tirupathur", "jolarpet",
    "natrampalli", "ranipet", "walajapet", "arcot", "melvisharam",
    "sholingur", "alangayam", "thuthipattu", "avaniyapuram",
    "kaniyambadi", "pallikonda", "vellore fort", "katpadi railway station",
}
VELLORE_REGION_DISTRICTS = {
    "vellore", "ranipet", "tirupattur", "tirupathur",
}

def _is_vellore_region(location, title, description):
    """Check if record belongs to Vellore region. Returns (is_valid, reason)."""
    if not location and not title and not description:
        return False, "no geographic evidence"
    loc = (location or "").lower()
    title_lower = (title or "").lower()
    desc_lower = (description or "").lower()
    all_text = f"{loc} {title_lower} {desc_lower}"
    for dist in VELLORE_REGION_DISTRICTS:
        if dist in loc:
            return True, f"district={dist}"
    for vloc in VELLORE_REGION_LOCALITIES:
        if vloc in loc:
            return True, f"locality={vloc}"
    for vloc in VELLORE_REGION_LOCALITIES:
        if vloc in title_lower or vloc in desc_lower:
            return True, f"mentioned={vloc}"
    if location and location.strip():
        return False, f"location={location}"
    return False, "no Vellore-region match"


def _clean(text):
    if text is None: return None
    text = unicodedata.normalize("NFKC", str(text))
    text = re.sub(r"\\s+", " ", text).strip()
    return text if text else None

def _extract_year(text):
    if not text: return None
    m = re.search(r"\\b(19[7-9]\\d|20[0-2]\\d)\\b", str(text))
    return int(m.group(1)) if m else None

def _severity_from_deaths(deaths):
    if deaths is None: return None, None
    if deaths >= 100: return 9.5, "Critical"
    if deaths >= 50: return 8.5, "Critical"
    if deaths >= 20: return 7.5, "High"
    if deaths >= 10: return 6.5, "High"
    if deaths >= 5: return 5.0, "Medium"
    if deaths >= 1: return 3.5, "Medium"
    return 1.0, "Low"

def _parse_deaths(text):
    if not text: return None
    text = str(text).strip()
    if text.lower() in ("unknown", "n/a", "na", "", "none"): return None
    m = re.search(r"(\\d+)", text.replace(",", ""))
    return int(m.group(1)) if m else None

def _parse_injured(text):
    if not text: return None
    text = str(text).strip()
    if text.lower() in ("unknown", "n/a", "na", "", "none"): return None
    m = re.search(r"(\\d+)", text.replace(",", ""))
    return int(m.group(1)) if m else None

def fetch_page(url):
    for attempt in range(3):
        try:
            resp = SESSION.get(url, timeout=30)
            resp.raise_for_status()
            return BeautifulSoup(resp.text, "lxml")
        except requests.RequestException as e:
            if attempt < 2: time.sleep(2 * (attempt + 1))
            else: raise RuntimeError(f"Failed to fetch {url}: {e}") from e

def _cell_texts(row):
    return [_clean(c.get_text()) for c in row.find_all(["td", "th"])]

def _find_col(header_lower, *keywords):
    for i, h in enumerate(header_lower):
        for kw in keywords:
            if kw in h: return i
    return None


def parse_terrorist_incidents(soup, source_label):
    records = []
    for table in soup.find_all("table", {"class": "wikitable"}):
        rows = table.find_all("tr")
        if not rows: continue
        headers = [_clean(c.get_text()) or "" for c in rows[0].find_all(["th", "td"])]
        hl = [h.lower() for h in headers]
        desc_idx = _find_col(hl, "incident", "description")
        if desc_idx is None: continue
        loc_idx = _find_col(hl, "location")
        killed_idx = _find_col(hl, "killed", "death", "fatal")
        injured_idx = _find_col(hl, "injured", "hurt")
        perp_idx = _find_col(hl, "perpetrator")
        for row in rows[1:]:
            ct = _cell_texts(row)
            if len(ct) < 3: continue
            date_str = ct[0] if ct[0] else None
            year = _extract_year(date_str)
            if year is None or year < EARLIEST_YEAR or year > LATEST_YEAR: continue
            desc = ct[desc_idx] if desc_idx < len(ct) else None
            if not desc: continue
            location = ct[loc_idx] if loc_idx is not None and loc_idx < len(ct) else None
            deaths = _parse_deaths(ct[killed_idx]) if killed_idx is not None and killed_idx < len(ct) else None
            injured = _parse_injured(ct[injured_idx]) if injured_idx is not None and injured_idx < len(ct) else None
            perpetrators = ct[perp_idx] if perp_idx is not None and perp_idx < len(ct) else None
            # GEOGRAPHIC VALIDATION
            is_valid, reason = _is_vellore_region(location, desc, "")
            if not is_valid: continue
            severity, risk = _severity_from_deaths(deaths)
            records.append({
                "article_id": f"wiki-terror-{uuid.uuid4().hex[:12]}",
                "title": desc[:500],
                "published_date": date_str[:50] if date_str else str(year),
                "source": source_label,
                "url": "https://en.wikipedia.org/wiki/List_of_terrorist_incidents_in_India",
                "crime_type": "Terrorism",
                "description": _clean(f"{desc}. Location: {location}. Deaths: {deaths or 'unknown'}. Injured: {injured or 'unknown'}. Perpetrators: {perpetrators or 'unknown'}."),
                "district": None,
                "locality": _clean(location)[:200] if location else None,
                "latitude": None, "longitude": None,
                "location_confidence": "LOW" if location else None,
                "location_source": "Wikipedia" if location else None,
                "severity_score": severity, "risk_level": risk,
            })
    return records

def parse_riots(soup, source_label):
    records = []
    for table in soup.find_all("table", {"class": "wikitable"}):
        rows = table.find_all("tr")
        if not rows: continue
        headers = [_clean(c.get_text()) or "" for c in rows[0].find_all(["th", "td"])]
        hl = [h.lower() for h in headers]
        if _find_col(hl, "year") is None: continue
        name_idx = _find_col(hl, "name")
        year_idx = _find_col(hl, "year")
        loc_idx = _find_col(hl, "location")
        cause_idx = _find_col(hl, "cause")
        deaths_idx = _find_col(hl, "death", "killed", "fatal")
        wounded_idx = _find_col(hl, "wounded", "injured")
        for row in rows[1:]:
            ct = _cell_texts(row)
            if len(ct) < 3: continue
            name = ct[name_idx] if name_idx is not None and name_idx < len(ct) else None
            year = _extract_year(ct[year_idx]) if year_idx is not None and year_idx < len(ct) else None
            location = ct[loc_idx] if loc_idx is not None and loc_idx < len(ct) else None
            cause = ct[cause_idx] if cause_idx is not None and cause_idx < len(ct) else None
            deaths = _parse_deaths(ct[deaths_idx]) if deaths_idx is not None and deaths_idx < len(ct) else None
            wounded = _parse_injured(ct[wounded_idx]) if wounded_idx is not None and wounded_idx < len(ct) else None
            if year is None or year < EARLIEST_YEAR or year > LATEST_YEAR: continue
            if not name and not location: continue
            title = _clean(name) if name else _clean(location)
            if not title: continue
            # GEOGRAPHIC VALIDATION
            is_valid, reason = _is_vellore_region(location, title, "")
            if not is_valid: continue
            severity, risk = _severity_from_deaths(deaths)
            records.append({
                "article_id": f"wiki-riot-{uuid.uuid4().hex[:12]}",
                "title": title[:500],
                "published_date": str(year),
                "source": source_label,
                "url": "https://en.wikipedia.org/wiki/List_of_riots_in_India",
                "crime_type": "Riots",
                "description": _clean(f"{title}. Year: {year}. Location: {location or 'unknown'}. Cause: {cause or 'unknown'}. Deaths: {deaths or 'unknown'}. Wounded: {wounded or 'unknown'}."),
                "district": None,
                "locality": _clean(location)[:200] if location else None,
                "latitude": None, "longitude": None,
                "location_confidence": "LOW" if location else None,
                "location_source": "Wikipedia" if location else None,
                "severity_score": severity, "risk_level": risk,
            })
    return records


def parse_railway_accidents(soup, source_label):
    records = []
    for table in soup.find_all("table", {"class": "wikitable"}):
        rows = table.find_all("tr")
        if not rows: continue
        headers = [_clean(c.get_text()) or "" for c in rows[0].find_all(["th", "td"])]
        hl = [h.lower() for h in headers]
        date_idx = _find_col(hl, "date")
        if date_idx is None: continue
        loc_idx = _find_col(hl, "location")
        fatal_idx = _find_col(hl, "fatal", "death")
        cause_idx = _find_col(hl, "cause")
        for row in rows[1:]:
            ct = _cell_texts(row)
            if len(ct) < 3: continue
            date_str = ct[date_idx] if date_idx < len(ct) else None
            year = _extract_year(date_str)
            if year is None or year < EARLIEST_YEAR or year > LATEST_YEAR: continue
            location = ct[loc_idx] if loc_idx is not None and loc_idx < len(ct) else None
            fatalities = _parse_deaths(ct[fatal_idx]) if fatal_idx is not None and fatal_idx < len(ct) else None
            cause = ct[cause_idx] if cause_idx is not None and cause_idx < len(ct) else None
            title = f"Railway accident near {location}" if location else "Railway accident in India"
            # GEOGRAPHIC VALIDATION
            is_valid, reason = _is_vellore_region(location, title, "")
            if not is_valid: continue
            severity, risk = _severity_from_deaths(fatalities)
            records.append({
                "article_id": f"wiki-rail-{uuid.uuid4().hex[:12]}",
                "title": _clean(title)[:500],
                "published_date": _clean(date_str)[:50] if date_str else str(year),
                "source": source_label,
                "url": "https://en.wikipedia.org/wiki/List_of_railway_accidents_in_India",
                "crime_type": "Railway accident",
                "description": _clean(f"Railway accident. Date: {date_str or year}. Location: {location or 'unknown'}. Fatalities: {fatalities or 'unknown'}. Cause: {cause or 'unknown'}."),
                "district": None,
                "locality": _clean(location)[:200] if location else None,
                "latitude": None, "longitude": None,
                "location_confidence": "LOW" if location else None,
                "location_source": "Wikipedia" if location else None,
                "severity_score": severity, "risk_level": risk,
            })
    # Also parse bullet-list entries
    current_year = None
    for elem in soup.find_all(["h2", "h3", "li"]):
        if elem.name in ("h2", "h3"):
            y = _extract_year(elem.get_text())
            if y and EARLIEST_YEAR <= y <= LATEST_YEAR: current_year = y
            elif y is not None: current_year = None
        elif elem.name == "li" and current_year:
            text = _clean(elem.get_text())
            if not text or len(text) < 20: continue
            fatalities = None
            m = re.search(r"(\\d+)\\s*(?:people\\s*)?(?:were\\s*)?(?:killed|died|fatal)", text, re.I)
            if m: fatalities = int(m.group(1))
            location = None
            loc_match = re.search(r"(?:near|in|at)\\s+([A-Z][a-zA-Z\\s,\\-]+?)(?:\\.|,|$)", text)
            if loc_match: location = _clean(loc_match.group(1))
            # GEOGRAPHIC VALIDATION
            is_valid, reason = _is_vellore_region(location, text, "")
            if not is_valid: continue
            severity, risk = _severity_from_deaths(fatalities)
            records.append({
                "article_id": f"wiki-rail-bl-{uuid.uuid4().hex[:12]}",
                "title": text[:500],
                "published_date": str(current_year),
                "source": source_label,
                "url": "https://en.wikipedia.org/wiki/List_of_railway_accidents_in_India",
                "crime_type": "Railway accident",
                "description": text,
                "district": None,
                "locality": _clean(location)[:200] if location else None,
                "latitude": None, "longitude": None,
                "location_confidence": "LOW" if location else None,
                "location_source": "Wikipedia" if location else None,
                "severity_score": severity, "risk_level": risk,
            })
    return records


def parse_massacres(soup, source_label):
    records = []
    for table in soup.find_all("table", {"class": "wikitable"}):
        rows = table.find_all("tr")
        if not rows: continue
        headers = [_clean(c.get_text()) or "" for c in rows[0].find_all(["th", "td"])]
        hl = [h.lower() for h in headers]
        if _find_col(hl, "date") is None: continue
        name_idx = _find_col(hl, "name", "place")
        date_idx = _find_col(hl, "date")
        loc_idx = _find_col(hl, "location")
        perp_idx = _find_col(hl, "perpetrator")
        deaths_idx = _find_col(hl, "death", "killed", "fatal")
        notes_idx = _find_col(hl, "notes")
        for row in rows[1:]:
            ct = _cell_texts(row)
            if len(ct) < 3: continue
            name = ct[name_idx] if name_idx is not None and name_idx < len(ct) else None
            date_str = ct[date_idx] if date_idx is not None and date_idx < len(ct) else None
            location = ct[loc_idx] if loc_idx is not None and loc_idx < len(ct) else None
            perpetrator = ct[perp_idx] if perp_idx is not None and perp_idx < len(ct) else None
            deaths = _parse_deaths(ct[deaths_idx]) if deaths_idx is not None and deaths_idx < len(ct) else None
            notes = ct[notes_idx] if notes_idx is not None and notes_idx < len(ct) else None
            year = _extract_year(date_str)
            if year is None or year < EARLIEST_YEAR or year > LATEST_YEAR: continue
            if not name and not location: continue
            title = _clean(name) if name else f"Massacre in {location}"
            # GEOGRAPHIC VALIDATION
            is_valid, reason = _is_vellore_region(location, title, "")
            if not is_valid: continue
            severity, risk = _severity_from_deaths(deaths)
            records.append({
                "article_id": f"wiki-massacre-{uuid.uuid4().hex[:12]}",
                "title": title[:500],
                "published_date": _clean(date_str)[:50] if date_str else str(year),
                "source": source_label,
                "url": "https://en.wikipedia.org/wiki/List_of_massacres_in_India",
                "crime_type": "Massacre",
                "description": _clean(f"{title}. Date: {date_str or year}. Location: {location or 'unknown'}. Perpetrator: {perpetrator or 'unknown'}. Deaths: {deaths or 'unknown'}. Notes: {notes or 'none'}."),
                "district": None,
                "locality": _clean(location)[:200] if location else None,
                "latitude": None, "longitude": None,
                "location_confidence": "LOW" if location else None,
                "location_source": "Wikipedia" if location else None,
                "severity_score": severity, "risk_level": risk,
            })
    return records


PARSERS = {
    "List of terrorist incidents in India": parse_terrorist_incidents,
    "List of riots in India": parse_riots,
    "List of railway accidents and incidents in India": parse_railway_accidents,
    "List of massacres in India": parse_massacres,
}

def scrape_source(url, source_label, crime_type):
    print(f"  fetching: {url}")
    soup = fetch_page(url)
    title_tag = soup.find("h1", {"id": "firstHeading"})
    page_title = title_tag.get_text() if title_tag else ""
    parser = None
    for key, fn in PARSERS.items():
        if key.lower() in page_title.lower():
            parser = fn
            break
    if parser is None:
        for fn in PARSERS.values():
            recs = fn(soup, source_label)
            if recs:
                parser = fn
                break
    if parser is None:
        print(f"    WARNING: no parser matched for {page_title}, skipping")
        return []
    records = parser(soup, source_label)
    print(f"    parsed {len(records)} Vellore-region incidents")
    return records

def import_records(records, db_path, reset=False):
    from flask import Flask
    from database import db
    from models.crime import Crime
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + db_path.as_posix()
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)
    with app.app_context():
        db.create_all()
        if reset:
            db.session.query(Crime).delete()
            db.session.commit()
        for payload in records:
            if not payload.get("article_id"): continue
            existing = db.session.execute(
                db.select(Crime).filter_by(article_id=payload["article_id"])
            ).scalar_one_or_none()
            if existing is None:
                db.session.add(Crime(**payload))
            else:
                for field, value in payload.items():
                    setattr(existing, field, value)
        db.session.commit()
        return db.session.query(Crime).count()

def main(argv=None):
    parser = argparse.ArgumentParser(description="Scrape Vellore-region crime data from Wikipedia")
    parser.add_argument("--reset", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--db", default=str(DEFAULT_DB))
    args = parser.parse_args(argv)
    db_path = Path(args.db).resolve()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    print("=" * 60)
    print("CrimeSense Vellore-Region Crime Scraper")
    print(f"Window: {EARLIEST_YEAR}-{LATEST_YEAR}")
    print("Geographic scope: Vellore region, Tamil Nadu")
    print("=" * 60)
    all_records = []
    for url, source_label, crime_type in SOURCES:
        print(f"\\n[{source_label}]")
        try:
            recs = scrape_source(url, source_label, crime_type)
            all_records.extend(recs)
        except Exception as e:
            print(f"    ERROR: {e}")
        time.sleep(1.5)
    print(f"\\n{'=' * 60}")
    print(f"Total Vellore-region incidents parsed: {len(all_records)}")
    if args.verbose:
        for i, r in enumerate(all_records, 1):
            print(f"  {i:3d}. [{r['crime_type']}] {r.get('published_date','')} -- {r.get('title','')[:80]}")
    if args.dry_run:
        print("\\nDRY RUN -- no database changes made.")
        return 0
    if not all_records:
        print("\\nNo records to import.")
        return 1
    total = import_records(all_records, db_path, reset=args.reset)
    print(f"\\nImport complete: {total} total records in database ({db_path})")
    return 0 if total >= 300 else 1

if __name__ == "__main__":
    sys.exit(main())
