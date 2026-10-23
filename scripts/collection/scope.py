"""CrimeSense geographic-scope rule (DOCUMENTED, single source of truth).

The project studies CRIME IN VELLORE. "Vellore" is ambiguous across time because
Tamil Nadu's districts were reorganised:

  * 1989  - North Arcot district split; Vellore district formed
            (still contained today's Ranipet + Tirupattur + Vellore).
  * 2019  - Vellore district split into THREE districts:
              Vellore      (Vellore, Katpadi, Gudiyatham, Pernambut,
                            Anaicut, K.V.Kuppam taluks)
              Ranipet      (Arcot, Walajapet, Sholinghur, Arakkonam,
                            Nemili, Kalavai, Melvisharam, Ranipet ...)
              Tirupattur   (Tirupattur, Vaniyambadi, Ambur, Natrampalli,
                            Alangayam, Jolarpet ...)

SCOPE VALUES (exactly one per record):
  VELLORE_CITY                 - inside Vellore city / corporation area
  VELLORE_DISTRICT             - inside the CURRENT (post-2019) Vellore district
  HISTORIC_VELLORE_OUT_OF_SCOPE- was in Vellore district BEFORE 2019 but is now
                                 in Ranipet / Tirupattur (or older North Arcot
                                 areas outside today's Vellore district)
  OUT_OF_SCOPE                 - clearly some other district/state
  UNKNOWN                      - no place evidence at all

ACCEPTANCE RULE (enforced in classify.py + config.ACCEPT_SCOPES):
  Only VELLORE_CITY and VELLORE_DISTRICT enter the MAIN incident dataset.
  HISTORIC_VELLORE_OUT_OF_SCOPE records are kept in a clearly-flagged side table
  so administrative boundaries are NEVER silently mixed.
"""
from __future__ import annotations

# --- Vellore city / corporation localities (city scope) --------------------
CITY_LOCALITIES = {
    "vellore", "vellore city", "katpadi", "sathuvachari", "sathuvacheri",
    "bagayam", "thorapadi", "thottapalayam", "kaspa", "sankaranpalayam",
    "ariyur", "virupakshipuram", "sainathapuram", "allapuram", "konavattam",
    "pallikonda road", "vellore fort", "fort round road", "officer's line",
    "vellore collectorate", "cmc vellore", "vellore cmc",
}

# --- Current (post-2019) Vellore district towns/taluks ---------------------
# NOTE: deliberately small + unambiguous. Bare "kuppam" (Andhra Pradesh town),
# "vaniyambadi"/"sevoor" (Tirupattur/Ranipet post-2019) and uncertain village
# names are NOT here — misclassifying scope is worse than missing a record.
DISTRICT_PLACES = {
    "gudiyatham", "gudiyattam", "pernambut", "pernamputtur",
    "anaicut", "anaikattu", "kv kuppam", "k v kuppam", "k.v.kuppam",
    "katpadi", "pallikonda", "kalinjur", "vellore district",
}


# --- Historic Vellore, now other districts (SIDE-TABLE ONLY) ---------------
HISTORIC_VELLORE = {
    "ranipet": "Ranipet",
    "arcot": "Ranipet",
    "walajapet": "Ranipet",
    "walajah": "Ranipet",
    "sholingur": "Ranipet",
    "sholinghur": "Ranipet",
    "arakkonam": "Ranipet",
    "arakonam": "Ranipet",
    "melvisharam": "Ranipet",
    "nemili": "Ranipet",
    "kalavai": "Ranipet",
    "tirupattur": "Tirupattur",
    "tirupathur": "Tirupattur",
    "vaniyambadi": "Tirupattur",
    "ambur": "Tirupattur",
    "natrampalli": "Tirupattur",
    "nattrampalli": "Tirupattur",
    "alangayam": "Tirupattur",
    "jolarpet": "Tirupattur",
    "tiruvannamalai": "Tiruvannamalai",
}

# --- Other Tamil Nadu districts (explicit OUT_OF_SCOPE evidence) ------------
OTHER_DISTRICTS = (
    "chennai", "coimbatore", "madurai", "salem", "trichy", "tiruchirappalli",
    "kanchipuram", "chengalpattu", "tiruvallur", "villupuram", "cuddalore",
    "dharmapuri", "krishnagiri", "erode", "tirunelveli", "thanjavur",
    "tiruppur", "dindigul", "karur", "namakkal", "nagapattinam", "virudhunagar",
    "sivaganga", "ramanathapuram", "pudukkottai", "ariyalur", "perambalur",
    "nilgiris", "kallakurichi", "tenkasi", "chengalpattu",
)

# Tamil-script place names (Vellore city/district) --------------------------
TAMIL_CITY = ("வேலூர்", "காட்பாடி", "சத்துவாச்சாரி", "பாகாயம்", "தோரப்பாடி")
TAMIL_DISTRICT = ("குடியாத்தம்", "பேர்ணாம்பட்டு", "அணைக்கட்டு", "கே.வி.குப்பம்",
                  "பள்ளிக்கொண்டா", "லத்தேரி")
TAMIL_HISTORIC = ("ராணிப்பேட்டை", "ஆர்க்காடு", "வாலாஜாபேட்டை", "சோளிங்கர்",
                  "அரக்கோணம்", "திருப்பத்தூர்", "வாணியம்பாடி", "ஆம்பூர்",
                  "ஜோலார்பேட்டை", "நாட்டாறம்பள்ளி", "திருவண்ணாமலை")

CITY, DISTRICT = "VELLORE_CITY", "VELLORE_DISTRICT"
HISTORIC, OUT, UNKNOWN = "HISTORIC_VELLORE_OUT_OF_SCOPE", "OUT_OF_SCOPE", "UNKNOWN"

# --- Tamil-script normalization --------------------------------------------
# Several Tamil outlets (Dinamalar, Daily Thanthi) encode the long-vowel "ூ"
# as the three-codepoint sequence "உ + ா" (e.g. "வேலுார்" instead of
# "வேலூர்"). NFC does NOT unify these, so keyword matching silently fails.
# ta_norm() re-composes them so every matcher sees canonical spellings.
import unicodedata as _uni
import re as _ta_re

_TA_CONS = _ta_re.compile(r"([\u0b95-\u0bb9])ுா")
_TAMIL_DIGITS = str.maketrans("௦௧௨௩௪௫௬௭௮௯", "0123456789")


def ta_norm(text: str) -> str:
    """NFC-normalize + re-compose decomposed 'ூ' + Tamil digits → ASCII."""
    t = _uni.normalize("NFC", text or "")
    t = _TA_CONS.sub(r"\1ூ", t)
    return t.translate(_TAMIL_DIGITS)


# --- URL-slug matcher for discovery prioritisation --------------------------
# Matches Vellore-region place names (English OR Tamil) inside a URL. Used by
# discovery to rank candidate URLs: Vellore-specific slugs are fetched first.
import re as _re

_URL_PLACES = sorted(
    {p.replace(" ", "-").replace(".", "") for p in (CITY_LOCALITIES | DISTRICT_PLACES)}
    | set(TAMIL_CITY) | set(TAMIL_DISTRICT),
    key=len, reverse=True)
URL_PLACE_RE = _re.compile(
    "(" + "|".join(_re.escape(p) for p in _URL_PLACES if p) + ")", _re.I)


# Evidence phrases that explicitly mark the CURRENT Vellore district (post-2019).
_DISTRICT_EVIDENCE = (
    "vellore district", "vellore dt", "vellore dist",
    "வேலூர் மாவட்டம்", "வேலூர் மாவட்ட",
)

# Evidence phrases that explicitly mark Vellore CITY.
_CITY_EVIDENCE = (
    "vellore city", "vellore corporation", "vellore taluk",
    "வேலூர் மாநகர", "வேலூர் வட்டம்",
)


def classify_scope(text_lower: str, raw_text: str = "") -> tuple:
    """Return (scope, matched_place, now_district).

    DOCUMENTED ORDER (never silently mixes boundaries):
      1. explicit Vellore-city evidence          -> VELLORE_CITY
      2. explicit Vellore-district evidence      -> VELLORE_DISTRICT
      3. named city/district localities          -> CITY / DISTRICT
      4. historic-Vellore-only place             -> HISTORIC (side table)
      5. other districts                         -> OUT_OF_SCOPE
      6. nothing                                 -> UNKNOWN
    A historic place is only used to downgrade when no current-scope evidence
    exists, so "Ranipet mentioned in passing" never outranks a real Vellore
    incident location.
    """
    blob = ta_norm(text_lower or "")
    raw = ta_norm(raw_text or blob)

    for ev in _CITY_EVIDENCE:
        if ev in blob:
            return CITY, ev.title(), "Vellore"
    for pl in sorted(TAMIL_CITY, key=len, reverse=True):
        if pl in raw:
            return CITY, pl, "Vellore"

    for ev in _DISTRICT_EVIDENCE:
        if ev in blob:
            return DISTRICT, "Vellore district", "Vellore"
    for place in sorted(DISTRICT_PLACES, key=len, reverse=True):
        if place in blob:
            return DISTRICT, place.title(), "Vellore"
    for pl in sorted(TAMIL_DISTRICT, key=len, reverse=True):
        if pl in raw:
            return DISTRICT, pl, "Vellore"

    # plain "vellore" mention with no district qualifier -> city-level scope
    if "vellore" in blob:
        return CITY, "Vellore", "Vellore"

    for place, now in sorted(HISTORIC_VELLORE.items(), key=lambda kv: -len(kv[0])):
        if place in blob:
            return HISTORIC, place.title(), now
    for pl in TAMIL_HISTORIC:
        if pl in raw:
            return HISTORIC, pl, "other"

    for place in OTHER_DISTRICTS:
        if place in blob:
            return OUT, place.title(), ""
    return UNKNOWN, "", ""



def in_main_dataset(scope: str) -> bool:
    return scope in (CITY, DISTRICT)
