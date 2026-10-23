"""Crime categories + English/Tamil keyword maps + search-matrix builder.

Categories follow the research brief. Each category carries:
  * ``en``  - English keywords used for body classification + queries
  * ``ta``  - Tamil-script keywords (many Vellore reports are Tamil-only)

``build_query_matrix()`` produces the systematic
SOURCE x CRIME CATEGORY x HISTORICAL PERIOD x LOCATION query set, so collection
never degenerates into repeating one generic "Vellore crime" search.
"""
from __future__ import annotations

# Ordered: earlier = higher precedence when several categories match.
CATEGORIES = {
    "murder": {
        "en": ["murder", "homicide", "killed", "murdered", "body found",
               "found dead", "death", "dies", "died"],
        "ta": ["கொலை", "படுகொலை", "சடலம்"],
    },
    "attempt_to_murder": {
        "en": ["attempt to murder", "attempted murder", "murder attempt",
               "hacked", "stabbed"],
        "ta": ["கொலை முயற்சி"],
    },
    "robbery": {
        "en": ["robbery", "robbed", "dacoity", "dacoit", "loot", "looted"],
        "ta": ["கொள்ளை", "கொள்ளையடித்து"],
    },
    "chain_snatching": {
        "en": ["chain snatching", "chain snatched", "snatched", "snatching"],
        "ta": ["சங்கிலி பறிப்பு", "சங்கிலி பறித்து"],
    },
    "theft": {
        "en": ["theft", "stolen", "steal", "stealing", "thief", "thieves",
               "pilferage"],
        "ta": ["திருட்டு", "திருடன்", "திருடர்கள்", "திருடிய"],
    },
    "mobile_vehicle_theft": {
        "en": ["mobile theft", "phone theft", "bike theft", "car theft",
               "motorcycle theft", "vehicle theft", "two-wheeler theft"],
        "ta": ["வாகனம் திருட்டு", "மொபைல் திருட்டு", "பைக் திருட்டு"],
    },
    "burglary": {
        "en": ["burglary", "burglar", "house break", "housebreaking",
               "broke open", "break-in"],
        "ta": ["வீடு உடைத்து", "பூட்டு உடைத்து", "வீட்டில் புகுந்து"],
    },
    "assault": {
        "en": ["assault", "attacked", "attacker", "attack", "grievous hurt",
               "thrashed", "beaten", "beat up", "clashed"],
        "ta": ["தாக்குதல்", "தாக்கப்பட்ட", "அடித்து", "தாக்கினர்"],
    },
    "kidnapping": {
        "en": ["kidnap", "kidnapped", "abduct", "abduction", "missing girl",
               "missing boy", "traced", "rescued"],
        "ta": ["கடத்தல்", "கடத்தப்பட்ட", "காணாமல்"],
    },
    "missing_person": {
        "en": ["missing person", "missing", "went missing", "untraced"],
        "ta": ["காணவில்லை", "காணாமல் போன"],
    },
    "sexual_offence": {
        "en": ["rape", "raped", "sexual assault", "molest", "molestation",
               "sexual harassment", "outraging modesty", "pocso"],
        "ta": ["பாலியல்", "பலாத்காரம்", "கற்பழிப்பு", "பாலியல் தொல்லை"],
    },
    "crimes_against_women": {
        "en": ["dowry", "dowry death", "harassment of woman", "eve teasing",
               "domestic violence", "498a", "cruelty"],
        "ta": ["வரதட்சணை", "வன்கொடுமை"],
    },
    "crimes_against_children": {
        "en": ["child abuse", "child sexual", "minor girl", "minor boy",
               "pocso", "child labour", "child trafficking"],
        "ta": ["குழந்தை", "சிறுமி", "சிறுவன்"],
    },
    "domestic_violence": {
        "en": ["domestic violence", "husband", "wife", "in-laws", "marital",
               "family dispute"],
        "ta": ["குடும்ப தகராறு", "கணவன்", "மனைவி"],
    },
    "cybercrime": {
        "en": ["cyber", "cybercrime", "phishing", "online fraud", "otp fraud",
               "hacked account", "social media", "sextortion", "online scam"],
        "ta": ["இணைய", "சைபர்", "ஆன்லைன் மோசடி"],
    },
    "fraud": {
        "en": ["fraud", "cheating", "cheated", "duped", "scam", "scammer",
               "swindle", "embezzle", "misappropriate"],
        "ta": ["மோசடி", "ஏமாத்து", "பாத்தியதை"],
    },
    "extortion": {
        "en": ["extortion", "blackmail", "ransom", "demanded money"],
        "ta": ["கப்பம்", "பயங்காரம்"],
    },
    "drug_offence": {
        "en": ["ganja", "narcotics", "ndps", "drug", "smuggling", "smuggled",
               "peddling", "contraband"],
        "ta": ["கஞ்சா", "போதை பொருள்", "கடத்தல்"],
    },
    "illegal_weapons": {
        "en": ["country-made pistol", "illegal weapon", "knife", "blade",
               "gun", "machete", "sickle", "arms"],
        "ta": ["வெடிகுண்டு", "கத்தி"],
    },
    "arson": {
        "en": ["arson", "set fire", "burnt", "torched", "fire set"],
        "ta": ["தீ வைத்து", "தீவைப்பு"],
    },
    "rioting": {
        "en": ["riot", "rioting", "clash", "clashes", "unlawful assembly",
               "violence", "protest turned", "stone pelting"],
        "ta": ["கலவரம்", "மோதல்"],
    },
    "property_crime": {
        "en": ["property crime", "trespass", "vandal", "damaged property",
               "encroachment", "land grab"],
        "ta": ["சொத்து", "ஆக்கிரமிப்பு", "சேதம்"],
    },
    "road_incident_offence": {
        "en": ["hit and run", "hit-and-run", "rash driving", "drunk driving",
               "road accident case", "killed in accident"],
        "ta": ["விபத்து", "அதிவேகம்"],
    },
    "police_action": {
        "en": ["arrest", "arrested", "booked", "case registered", "fir",
               "police custody", "remanded", "charge sheet"],
        "ta": ["கைது", "வழக்கு பதிவு", "நீதிமன்ற காவல்"],
    },
}

CATEGORY_LABEL = {
    "murder": "Murder", "attempt_to_murder": "Attempt to Murder",
    "robbery": "Robbery", "chain_snatching": "Chain Snatching",
    "theft": "Theft", "mobile_vehicle_theft": "Vehicle Theft",
    "burglary": "Burglary", "assault": "Assault",
    "kidnapping": "Kidnapping", "missing_person": "Missing Person",
    "sexual_offence": "Sexual Offence",
    "crimes_against_women": "Crime Against Woman",
    "crimes_against_children": "Crime Against Child",
    "domestic_violence": "Domestic Violence", "cybercrime": "Cyber Crime",
    "fraud": "Fraud", "extortion": "Extortion",
    "drug_offence": "Drug Offence", "illegal_weapons": "Illegal Weapons",
    "arson": "Arson", "rioting": "Rioting",
    "property_crime": "Property Crime",
    "road_incident_offence": "Road Incident Offence",
    "police_action": "Police Action",
}

# More specific subtype label, checked before the category default.
SUBTYPES = [
    (("attempt to murder", "attempted murder", "murder attempt"),
     "Attempt to Murder"),
    (("chain snatching", "chain snatched"), "Chain Snatching"),
    (("house breaking", "housebreaking", "broke open"), "Burglary"),
    (("dowry death",), "Dowry Death"), (("dowry",), "Dowry Harassment"),
    (("hit and run", "hit-and-run"), "Hit and Run"),
    (("drunk driving",), "Drunk Driving"), (("rash driving",), "Rash Driving"),
    (("otp fraud",), "OTP Fraud"), (("online fraud",), "Online Fraud"),
    (("phishing",), "Phishing"), (("sextortion",), "Sextortion"),
    (("ganja",), "Ganja Peddling"), (("ndps",), "NDPS Act"),
    (("country bomb",), "Illegal Explosive"),
    (("country-made",), "Illegal Weapon"), (("pocso",), "POCSO Act"),
    (("498a",), "Dowry Harassment"), (("chain",), "Chain Snatching"),
]

# Locality anchors for query generation (English + Tamil).
LOCATION_TERMS_EN = ["Vellore", "Katpadi", "Gudiyatham", "Pernambut",
                     "Anaicut", "K V Kuppam", "Vellore district"]
LOCATION_TERMS_TA = ["வேலூர்", "காட்பாடி", "குடியாத்தம்", "பேர்ணாம்பட்டு"]

# Vendor search operators used for discovery (Google News / Bing style).
SITE_OPERATORS = {
    "dinamalar": "site:dinamalar.com",
    "dinamani": "site:dinamani.com",
    "dailythanthi": "site:dailythanthi.com",
    "maalaimalar": "site:maalaimalar.com",
    "thehindu": "site:thehindu.com",
    "dtnext": "site:dtnext.in",
    "nie": "site:newindianexpress.com",
}


def label_for(category: str) -> str:
    """Canonical crime_type label for a category key."""
    return CATEGORY_LABEL.get(category, category.replace("_", " ").title())


def build_query_matrix(periods, locations=None, categories=None,
                       max_keywords_per_category=5, source_key=None):
    """Flat, traceable query list: SOURCE x CATEGORY x PERIOD x LOCATION.

    Returns a list of dicts with the query string plus the matrix coordinates
    (source/category/period/location) so every accepted record can be traced
    back to the query that found it.
    """
    locations = locations or (LOCATION_TERMS_EN + LOCATION_TERMS_TA)
    cats = categories or list(CATEGORIES.keys())
    prefix = SITE_OPERATORS.get(source_key or "", "")
    out = []
    for label, year_from, year_to in periods:
        for cat in cats:
            spec = CATEGORIES.get(cat, {})
            for loc in locations:
                tamil = any("\u0b80" <= ch <= "\u0bff" for ch in loc)
                kws = spec.get("ta" if tamil else "en", [])[:max_keywords_per_category]
                for kw in kws:
                    parts = [p for p in (prefix, loc, kw) if p]
                    out.append({
                        "query": " ".join(parts),
                        "source_key": source_key,
                        "category": cat,
                        "period": label,
                        "year_from": year_from,
                        "year_to": year_to,
                        "location": loc,
                    })
    return out
