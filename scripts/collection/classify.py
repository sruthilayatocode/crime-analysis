"""Classification: geographic scope -> crime relevance -> crime type ->
dates/locality extraction. Uses scope.py (documented scope rule) and
categories.py (keyword maps). Unknown fields stay empty — never guessed."""
from __future__ import annotations
import re

from scripts.collection import scope as SCOPE
from scripts.collection.categories import CATEGORIES, SUBTYPES, label_for
from scripts.collection.extract import parse_date

# --- generic Tamil place anchors (district-level mention in Tamil text) ---
_TAMIL_LOC = ("வேலூர்", "காட்பாடி", "குடியாத்தம்", "பேர்ணாம்பட்டு", "ஆம்பூர்",
              "திருப்பத்தூர்", "ராணிப்பேட்டை", "ஆரக்கோணம்", "வாணியம்பாடி",
              "சோளிங்கர்", "அனைக்குன்று", "ஜோலார்பேட்டை", "காஞ்சிபுரம்",
              "திருவண்ணாமலை")

_POLICE_UR = re.compile(
    r"\b([A-Za-z .-]{2,40}?)\s+police station\b", re.I)
_TAMIL_PS = re.compile(r"([^\s,،]{2,30}?)\s*போலீஸ்(?:\s*நிலையம்)?")


# --- precision controls -------------------------------------------------
# Weak terms only indicate crime when a crime-context marker co-occurs
# (police/arrest/case/court). Stops "bus fare hike" -> crime misfires.
WEAK_TERMS = {"death", "dies", "died", "missing person", "missing",
              "went missing", "untraced", "traced", "rescued", "clashed",
              "cruelty", "attack"}
CRIME_CONTEXT_RE = re.compile(
    r"\b(police|arrested|arrest|fir|case registered|charged|chargesheet|"
    r"custody|complaint|accused|suspect|court|inquiry|investigation|"
    r"\u0b95\u0bc8\u0ba4\u0bc1|\u0baa\u0bcb\u0bb2\u0bc0\u0bb8\u0bcd|"
    r"\u0bb5\u0bb4\u0b95\u0bcd\u0b95\u0bc1|\u0b95\u0bc1\u0bb1\u0bcd\u0bb1\u0bae\u0bcd|"
    r"\u0ba8\u0bc0\u0ba4\u0bbf\u0bae\u0ba9\u0bcd\u0bb1\u0bae\u0bcd)\b", re.I)
# Suicides are documented but are NOT criminal incidents for CrimeSense.
SUICIDE_RE = re.compile(
    r"\b(suicide|suicided|hanged herself|hanged himself|self-immolation|"
    r"kills self|took her own life|took his own life)\b|"
    r"\u0ba4\u0bb1\u0bcd\u0b95\u0bca\u0bb2\u0bc8", re.I)


def validate(article: dict) -> dict | None:
    """Full DISCOVERY->CANDIDATE validation for one extracted article.

    Returns a candidate dict (scope classified, crime typed, dated) or None if
    it fails scope/crime relevance. Never fabricates a field.
    """
    title = article.get("title") or ""
    desc = article.get("description") or ""
    body = article.get("body_text") or ""
    url = article.get("source_url") or ""
    blob = f"{title} {desc} {body[:4000]}"

    # --- 1) Vellore scope validation (documented rule in scope.py) ---
    sc_scope, sc_place, sc_now = SCOPE.classify_scope(blob.lower(), blob)
    if sc_scope in (SCOPE.OUT, SCOPE.UNKNOWN):
        return None
    sc = {"scope": sc_scope, "locality": sc_place, "basis": sc_now}

    # --- 2) crime relevance: category keyword hits, precision-gated ---
    bl = blob.lower()
    has_context = bool(CRIME_CONTEXT_RE.search(blob))
    matched = {}
    for cat, spec in CATEGORIES.items():
        hits = [t for t in spec["en"]
                if re.search(rf"\b{re.escape(t.lower())}\b", bl)]
        # weak terms need crime context; strong terms stand alone
        strong = [t for t in hits if t not in WEAK_TERMS]
        weak_ok = [t for t in hits if t in WEAK_TERMS and has_context]
        hits = strong + weak_ok
        hits += [t for t in spec["ta"] if t in blob]
        if hits:
            matched[cat] = hits
    if not matched:
        return None
    # suicide guard: documented death but not a criminal incident
    if SUICIDE_RE.search(blob):
        non_suicide = {c: h for c, h in matched.items()
                       if c not in ("murder", "attempt_to_murder",
                                    "missing_person")}
        # keep only if an unrelated strong category (e.g. the victim was
        # murdered and the case also involves another offence)
        if not non_suicide or not any(
                t for c, h in non_suicide.items() for t in h
                if t not in WEAK_TERMS):
            return None
        matched = non_suicide

    # precedence: dict order = severity/specificity
    category = next(iter(matched))

    # subtype refinement
    bl = blob.lower()
    subtype = ""
    for kws, lab in SUBTYPES:
        if any(re.search(rf"\b{re.escape(k)}\b", bl) for k in kws):
            subtype = lab
            break
    crime_type = subtype or label_for(category)

    # --- 3) incident date (explicit) ---
    incident_date = ""
    # prefer an explicitly reported date inside the body
    m = re.search(r"\b(\d{4})-(\d{2})-(\d{2})\b", body)
    if m:
        iso = parse_date(m.group(0))
        if iso:
            incident_date = iso
    if not incident_date:
        # visible "DD Month YYYY" inside body
        m = re.search(r"\b(\d{1,2}) (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|"
                      r"Nov|Dec) (\d{4})\b", body, re.I)
        if m:
            incident_date = parse_date(f"{m.group(1)} {m.group(2)} {m.group(3)}")

    # --- 4) police station (only when clearly declared) ---
    police_station = ""
    m = _POLICE_UR.search(body)
    if m:
        police_station = f"{m.group(1).strip().title()} Police Station"
    else:
        m = _TAMIL_PS.search(body)
        if m:
            police_station = m.group(1).strip()

    # --- 5) locality (in-scope place name or Tamil anchor) ---
    locality = sc.get("locality") or ""
    if not locality:
        for t in _TAMIL_LOC:
            if t in blob:
                locality = SCOPE.TAMIL_CITY.get(t) or "Vellore"
                break

    return {
        "source_url": article.get("source_url"),
        "source_name": article.get("source_name"),
        "title": title,
        "crime_type": crime_type,
        "crime_category": category,
        "incident_date": incident_date or "",
        "incident_year": (incident_date or "")[:4],
        "locality": locality,
        "police_station": police_station,
        "district": "Vellore",
        "state": "Tamil Nadu",
        "description": (desc or body[:300]).strip(),
        "source_publication_date": article.get("published_date") or "",
        "scope_class": sc["scope"],
        "scope_locality": sc.get("locality", ""),
        "scope_basis": sc.get("basis", ""),
    }
