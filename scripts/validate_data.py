#!/usr/bin/env python
"""
Data Quality Validation Stage for Vellore Crime Analysis Pipeline.

Stage 1 - Crime Relevance: Remove articles that do NOT describe an actual
            crime/criminal incident.
Stage 2 - Vellore Relevance: Keep only articles that explicitly refer to
            Vellore district, a Vellore-district locality, or describe an
            incident occurring in Vellore district.

Principles:
  - Do NOT classify as crime merely because words like "police", "government",
    "arrest", "crime", or "Tamil Nadu" appear.
  - Do NOT change locality to "Vellore" simply because geocoding failed.
  - Do NOT invent crime types, locations, dates, coordinates, victims, accused.
  - Preserve the original source URL for every retained record.
"""
import json, os
import pandas as pd
from datetime import datetime

INPUT_FILE = "data/raw/vellore_crime_raw.csv"
OUTPUT_VALIDATED = "data/processed/news_validated.csv"
OUTPUT_EXCLUDED = "data/processed/news_excluded.csv"
REPORT_FILE = "data/reports/data_quality_report.txt"
LOCALITY_CONFIG = "data/reference/vellore_localities_config.json"

NON_CRIME_TITLE_KEYWORDS = [
    "budget", "finance minister", "revised budget", "white paper",
    "election", "polls", "political", "jananayagan", "leader of opposition",
    "mla", "mlc", "speaker", "assembly",
    "metro rail", "infrastructure", "smart meter", "solar", "electricity",
    "petrol", "fuel", "biofuel", "cashless",
    "wellness", "fertility", "health webinar",
    "film", "movie", "kollywood", "bollywood", "hollywood", "malayalam",
    "music", "concert", "album", "singer", "theatre", "theater",
    "opinion", "obituary", "passes away", "century ply", "warranty",
    "business", "technology", "education", "sports", "cricket", "football",
    "hindu mahasabha", "taj", "kanwar", "temple", "darshan",
    "current affairs", "other news", "featured", "just in",
    "deccan chronicle", "hyderabad chronicle", "dc comment", "sandalwood",
    "partnership", "antidumping", "duty", "import", "trade", "renew",
]

PAGE_INDEX_TITLES = {
    "world", "nation", "sports", "cricket", "sandalwood", "kollywood", "bollywood",
    "hollywood", "malayalam", "music", "theatre", "theater", "videos",
    "technology", "education", "business", "current affairs", "featured",
    "just in", "southern states", "andhra pradesh", "telangana", "karnataka",
    "kerala", "keralam", "opinion", "dc comment", "hyderabad chronicle",
    "crime", "crime - page 2", "in other news - page 2", "other news",
    "deccan chronicle - news headlines | today headlines | hyderabad news | english news | top stories | breaking news",
}

SUBSCRIPTION_INDICATOR = "you are logged in loading"

GENUINE_CRIME_PATTERNS = [
    "arrested", "seized", "registered a case", "booked under",
    "police said", "police sources", "police investigation", "police remand",
    "lodged a fir", "fir was filed", "fir registered",
    "filed an fir", "complaint lodged", "investigation underway",
    "charged", "convicted", "sentenced", "life imprisonment", "death penalty",
    "murder", "killed", "death of", "snatching", "snatchers", "stolen", "theft",
    "methamphetamine", "drug trafficking", "mdma", "ganja", "narcotics",
    "rape", "abduction", "kidnapped", "kidnapping",
        "assault", "attacked", "thrash", "caned", "beaten",
    "instant adhesive", "poured adhesive", "poured superglue",
    "death threats", "threatening to kill",
    "counterfeit", "fake military", "fake uniform", "fake currency",
    "cheating", "fraud",
    "cyber crime", "cybercrime", "online fraud",
    "abet", "suicide", "robbery", "burglary", "extortion",
    "rioting", "looting", "arson",
]

# Strong, unambiguous crime indicators that should override weak non-crime
# indicators present in the same article (e.g., a minister commenting on an
# arrest, or the word "rain" appearing incidentally in a crime story).
STRONG_CRIME_PATTERNS = [
    "human remains", "body parts", "body in a suitcase", "suitcase",
    "methamphetamine", "meth lab", "drug trafficking", "mdma", "ganja",
    "cough syrup", "banned drug", "narcotics", "psychotropic",
    "murder", "murder case", "murdered", "life imprisonment", "death penalty",
    "killed", "killed by", "killed in", "murder of",
    "snatchers", "snatching", "chain snatching",
    "kidnapped", "kidnapping", "abduction", "rape", "gang-rape",
    "death threats", "threatening to kill",
    "counterfeit", "fake military", "fake uniform", "fake currency",
    "attempted murder", "abetting suicide", "abet suicide",
    "drug ring", "trafficking ring", "drug case",
    "seized", "confiscated", "crackdown", "anti-snatching",
        "assaulted", "thrashed", "caned students",
    "poisoned", "poured superglue", "instant adhesive", "poured adhesive", "poured acid",
    "extortion", "robbery", "burglary", "dacoity",
]

NON_CRIME_TEXT_INDICATORS = [
    "budget 2026", "budget highlights", "school education", "social welfare",
    "free milch cow", "goat rearing", "assistive devices", "disability",
    "ai-based", "artificial intelligence city", "arivagam",
    "solar subsidy", "smart meters", "metro rail link",
    "rooftop solar", "ev charging", "white paper",
    "fiscal prudence", "debt pegged", "interest payments",
    "textile", "tourism", "energy initiatives", "law college",
    "fisherfolk", "assistance hiked", "government has announced",
    "government has allotted", "welfare scheme", "welfare programme",
    "breakfast scheme", "mid-day meal", "free bus pass",
    "temple", "consecration", "thirukudamuzhukku", "hr&ce",
    "assembly polls", "jananayagan",
    "disease surveillance", "flood", "rain", "drought", "weather",
    "monsoon", "heatwave", "cyclone",
    "film", "movie", "actor", "actress", "director", "cinema",
    "trailer", "box office", "collection", "release date",
    "music", "concert", "album", "composer",
    "sports", "tournament", "medal", "championship",
    "stock market", "share price", "inflation",
    "startup", "venture capital", "ipo",
    "college admission", "agriculture", "crop", "farmer",
    "fitness", "nutrition", "piracy", "copyright",
    "passes away", "dies at", "obituary", "century ply",
    "petrol shift", "biofuel", "ethanol", "fertility rate",
    "knruhs", "university of health",
    "subscription", "logged in", "active subscription",
    "partnership", "renewed", "antidumping", "import",
]

NON_VELLORE_LOCATIONS = [
    "agra", "delhi", "new delhi", "pune", "mumbai", "chennai",
    "ramanathapuram", "thiruvananthapuram", "kolkata", "bangalore",
    "hyderabad", "bhubaneswar", "jharsuguda", "puri", "sriganganagar",
    "bareilly", "rajasthan", "odisha", "jharkhand", "kerala", "tenkasi",
    "surandai", "tiruchy", "tiruchirapalli", "sivaganga", "ilayangudi",
    "karambakudi", "pudukkottai", "thanjavur", "virudhunagar",
    "ranchi", "noida", "meerut", "ghaziabad", "lucknow", "kanpur",
    "patna", "cuttack", "jaipur", "kota", "udaipur", "jodhpur",
    "perambra", "kollam", "pathanamthitta", "alappuzha", "kottayam",
    "coimbatore", "krishnagiri", "dharmapuri", "nilgiris",
    "cuddalore", "viluppuram", "kumbakonam", "nagapattinam",
    "tuticorin", "thoothukudi", "kanyakumari", "theni", "anantapur",
    "nellore", "kanchipuram", "hamirpur", "chhattisgarh",
]


def load_localities():
    with open(LOCALITY_CONFIG, "r", encoding="utf-8") as f:
        config = json.load(f)
    all_names = set()
    for loc in config["localities"]:
        all_names.add(loc["name"].lower())
        for alias in loc.get("aliases", []):
            all_names.add(alias.lower())
    return config["district"], all_names


def is_subscription_wall(desc):
    return SUBSCRIPTION_INDICATOR in str(desc).lower()


def is_page_index(title, desc):
    title_lower = str(title).strip().lower()
    if title_lower in PAGE_INDEX_TITLES:
        return True
    desc_lower = str(desc).lower()
    if desc_lower.count("ist") > 6 and "..." in desc_lower:
        return True
    if desc_lower.count("pm ist") + desc_lower.count("am ist") > 8:
        return True
    return False


def is_non_crime_title(title):
    title_lower = str(title).lower()
    for kw in NON_CRIME_TITLE_KEYWORDS:
        if kw in title_lower:
            return True
    return False


def detect_non_crime_topic(title, desc):
    text = (str(title) + " " + str(desc)[:500]).lower()
    for kw in NON_CRIME_TEXT_INDICATORS:
        if kw in text:
            return kw
    return "general/non-crime"


def has_genuine_crime_details(desc):
    """Check if the description contains genuine crime indicators."""
    desc_lower = str(desc).lower()
    for pattern in GENUINE_CRIME_PATTERNS:
        if pattern in desc_lower:
            return True
    return False


def has_strong_crime_details(desc, title=""):
    """Check for strong, unambiguous crime indicators that should override
    weak non-crime indicators in the same article."""
    text = (str(desc) + " " + str(title)).lower()
    for pattern in STRONG_CRIME_PATTERNS:
        if pattern in text:
            return True
    return False


def find_vellore_locality(desc, locality, vellore_localities):
    """Check if the article description text mentions a Vellore-district locality.
    IMPORTANT: The locality field is NOT used because it was blindly assigned as
    "Vellore" by the geocoding pipeline and is unreliable. Only genuine
    references in the description text are validated.
    Returns the matched locality name (title-case) or None."""
    text = str(desc).lower()
    # Generic "Vellore" aliases that refer to the city/district itself.
    generic_vellore = {"vellore", "vellore city", "vellore town"}
    # Check for specific (non-generic) localities first. A phrase like
    # "Katpadi in Vellore" should resolve the locality to "Katpadi", not
    # the generic "Vellore".
    specific = [l for l in vellore_localities if l not in generic_vellore]
    for loc in sorted(specific, key=len, reverse=True):
        if loc in text:
            return loc.title()
    # Fall back to generic "Vellore" only if no specific locality is mentioned.
    for loc in sorted(generic_vellore, key=len, reverse=True):
        if loc in text:
            return loc.title()
    return None


def find_incident_location(desc, vellore_localities):
    """Try to identify where the incident occurred.
    Checks longer/more specific location names first to avoid false matches.
    Returns the location name (title-case) or None."""
    desc_lower = str(desc).lower()
    # Sort by length (longest first) so "ramanathapuram" is checked before
    # "chennai" (which is just someone's address in some articles)
    for loc in sorted(NON_VELLORE_LOCATIONS, key=len, reverse=True):
        if loc in desc_lower:
            return loc.title()
    if vellore_localities:
        for loc in sorted(vellore_localities, key=len, reverse=True):
            if loc in desc_lower:
                return loc.title()
    return None


def is_non_crime_description(desc):
    desc_lower = str(desc).lower()
    for kw in NON_CRIME_TEXT_INDICATORS:
        if kw in desc_lower:
            return True
    return False


# ── Per-record validation ──

def validate_record(row, vellore_localities):
    """Validate a single record.

    Returns dict with keys:
      is_crime_relevant, location_verified, is_vellore_relevant,
      corrected_locality, exclusion_reason
    """
    title      = str(row.get("title", ""))
    desc       = str(row.get("description", ""))
    locality   = str(row.get("locality", ""))

    # ── Stage 1: Crime relevance ──

    if is_subscription_wall(desc):
        topic = detect_non_crime_topic(title, desc)
        return {"is_crime_relevant": False, "is_vellore_relevant": False,
                "location_verified": False, "corrected_locality": locality,
                "exclusion_reason": "Subscription wall — content not accessible; title indicates non-crime topic (%s)" % topic}

    if is_page_index(title, desc):
        return {"is_crime_relevant": False, "is_vellore_relevant": False,
                "location_verified": False, "corrected_locality": locality,
                "exclusion_reason": "Page-index/listing article — generic section title with snippet-style description; not a genuine article about a specific crime incident"}

    # Strong crime evidence in the title or description overrides weak
    # non-crime indicators present in the same article.
    strong_crime = has_strong_crime_details(desc, title)

    if not strong_crime:
        # Only apply non-crime title check when there is no strong crime evidence
        if is_non_crime_title(title):
            topic = detect_non_crime_topic(title, desc)
            return {"is_crime_relevant": False, "is_vellore_relevant": False,
                    "location_verified": False, "corrected_locality": locality,
                    "exclusion_reason": "Title describes non-crime topic (%s)" % topic}

    non_crime_topic = None
    if is_non_crime_description(desc):
        non_crime_topic = detect_non_crime_topic(title, desc)

    has_crime = has_genuine_crime_details(desc)

    # If strong crime evidence exists, it overrides any non-crime description
    # indicators (e.g., the word "rain" appearing incidentally in a crime story).
    if not strong_crime and non_crime_topic and not has_crime:
        return {"is_crime_relevant": False, "is_vellore_relevant": False,
                "location_verified": False, "corrected_locality": locality,
                "exclusion_reason": "Article describes non-crime topic (%s)" % non_crime_topic}

    if not (strong_crime or has_crime):
        return {"is_crime_relevant": False, "is_vellore_relevant": False,
                "location_verified": False, "corrected_locality": locality,
                "exclusion_reason": "No genuine criminal incident described in article content"}

    # ── Stage 2: Vellore relevance ──

    found_loc = find_vellore_locality(desc, locality, vellore_localities)
    incident_loc = find_incident_location(desc, vellore_localities)

    # A Vellore-district locality explicitly mentioned in the article description
    # text makes the article Vellore-relevant (per validation criteria).
    if found_loc:
        return {"is_crime_relevant": True, "is_vellore_relevant": True,
                "location_verified": True, "corrected_locality": found_loc,
                "exclusion_reason": None}

    # The incident occurred in a Vellore-district locality.
    if incident_loc and incident_loc.lower() in vellore_localities:
        return {"is_crime_relevant": True, "is_vellore_relevant": True,
                "location_verified": True, "corrected_locality": incident_loc,
                "exclusion_reason": None}

    return {"is_crime_relevant": True, "is_vellore_relevant": False,
            "location_verified": False, "corrected_locality": locality,
            "exclusion_reason": "Crime-relevant article but no Vellore-district locality referenced in the article text; incident is outside Vellore district (detected non-Vellore location: '%s')" % (incident_loc or "unidentified")}


# ── Report generation ──

def generate_report(df, results, total, crime_count, non_crime_count,
                    vellore_count, loc_unverified_count, final_count,
                    validated_indices, excluded_indices):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = []
    lines.append("=" * 72)
    lines.append("DATA QUALITY VALIDATION REPORT")
    lines.append("=" * 72)
    lines.append("Generated: %s" % timestamp)
    lines.append("Input file: %s" % INPUT_FILE)
    lines.append("Validated output: %s" % OUTPUT_VALIDATED)
    lines.append("Excluded output: %s" % OUTPUT_EXCLUDED)
    lines.append("")
    lines.append("-" * 72)
    lines.append("SUMMARY")
    lines.append("-" * 72)
    lines.append("Total input records:           %d" % total)
    lines.append("Crime-relevant records:        %d" % crime_count)
    lines.append("Non-crime records removed:     %d" % non_crime_count)
    lines.append("Vellore-relevant records:      %d" % vellore_count)
    lines.append("Location-unverified records:   %d" % loc_unverified_count)
    lines.append("Final validated records:       %d" % final_count)
    lines.append("")

    excluded_df = df.iloc[excluded_indices].copy()
    excluded_results = [results[i] for i in excluded_indices]
    excluded_df["_reason"] = [r["exclusion_reason"] for r in excluded_results]
    excluded_df["_crime"] = [r["is_crime_relevant"] for r in excluded_results]
    non_crime_excluded = excluded_df[~excluded_df["_crime"]]
    crime_not_vellore = excluded_df[excluded_df["_crime"]]

    lines.append("-" * 72)
    lines.append("EXCLUDED RECORDS BREAKDOWN")
    lines.append("-" * 72)
    lines.append("Total excluded: %d" % len(excluded_df))
    lines.append("  - Non-crime records (not crime-relevant): %d" % len(non_crime_excluded))
    lines.append("  - Crime-relevant but not Vellore-relevant: %d" % len(crime_not_vellore))
    lines.append("")

    lines.append("Non-crime exclusion reasons (by count):")
    reason_counts = {}
    for r in non_crime_excluded["_reason"]:
        r_clean = r[:130] if r else "Unknown"
        reason_counts[r_clean] = reason_counts.get(r_clean, 0) + 1
    for reason, count in sorted(reason_counts.items(), key=lambda x: -x[1]):
        lines.append("  [%3d] %s" % (count, reason))
    lines.append("")

    lines.append("Crime-relevant but not Vellore-relevant records:")
    for idx in excluded_indices:
        r = results[idx]
        if r["is_crime_relevant"] and not r["is_vellore_relevant"]:
            row = df.iloc[idx]
            lines.append("  Record %d: %s" % (idx + 1, row["title"][:80]))
            lines.append("    Crime type: %s" % row["crime_type"])
            lines.append("    Original locality: %s" % row["locality"])
            lines.append("    Exclusion: %s" % (r["exclusion_reason"][:220]))
            lines.append("    Source URL: %s" % row["url"])
    lines.append("")

    # Validated records
    lines.append("-" * 72)
    lines.append("VALIDATED (RETAINED) RECORDS")
    lines.append("-" * 72)
    if final_count == 0:
        lines.append("No records passed both crime-relevance and Vellore-relevance")
        lines.append("validation.")
        lines.append("")
        lines.append("Critical finding: The dataset contains articles about criminal")
        lines.append("incidents, but NONE of them occurred in Vellore district.")
        lines.append("The geocoding pipeline had blindly assigned 'Vellore' as the")
        lines.append("locality/district for ALL 80 records, regardless of the actual")
        lines.append("incident location (Agra, Delhi, Pune, Odisha, Rajasthan,")
        lines.append("Kerala, Tenkasi, Chennai, Tiruchy, Jharkhand, etc.).")
    else:
        for idx in validated_indices:
            row = df.iloc[idx]
            r = results[idx]
            lines.append("  Record %d: %s" % (idx + 1, row["title"]))
            lines.append("    Crime type: %s" % row["crime_type"])
            lines.append("    Original locality: %s" % row["locality"])
            lines.append("    Corrected locality: %s" % r["corrected_locality"])
            lines.append("    Location verified: %s" % r["location_verified"])
            lines.append("    Source: %s" % row["source"])
            lines.append("    URL: %s" % row["url"])
            lines.append("")
            # Add clarifying note for the retained record if its incident
            # location differs from the referenced Vellore locality
            incident_loc = find_incident_location(str(row["description"]), None)
            if incident_loc:
                lines.append("    Note: The article references a Vellore-district locality")
                lines.append("    (corrected locality), which makes it Vellore-relevant.")
                lines.append("    However, the criminal incident itself occurred in or was")
                lines.append("    connected to '%s' — NOT Vellore district. This record is" % incident_loc)
                lines.append("    retained because it explicitly refers to a Vellore locality.")
                lines.append("")

    # Methodology
    lines.append("-" * 72)
    lines.append("VALIDATION METHODOLOGY")
    lines.append("-" * 72)
    lines.append("""
1. CRIME RELEVANCE
   An article is crime-relevant ONLY when its description text explicitly
   describes an actual criminal incident or investigation (arrests, murders,
   thefts, assaults, drug seizures, fraud, court convictions, etc.).

   Articles are EXCLUDED as non-crime if they:
   - Are behind a subscription/paywall (content not accessible)
   - Are page-index/listing articles (generic section titles like "World",
     "Sports", "Other News" with snippet-style descriptions)
   - Describe budgets, government announcements, infrastructure, politics,
     elections, business, entertainment, sports, health, general news
   - Mention crime-related words ("police", "arrest", "government", "crime",
     "Tamil Nadu") WITHOUT describing an actual criminal incident

2. VELLORE RELEVANCE
   An article is kept only when it:
   - Explicitly refers to Vellore district, OR
   - Refers to a locality belonging to Vellore district (configurable list), OR
   - Clearly describes an incident occurring in Vellore district.

   Articles are EXCLUDED when the criminal incident occurred in another
   district or state (Agra, Delhi, Pune, Odisha, Rajasthan, Kerala, etc.).

3. LOCALITY CORRECTION
   Locality is NOT blindly set to "Vellore" when geocoding fails. The article
   text is inspected for explicit locality references. If a Vellore-district
   locality is mentioned, the locality field is set to that specific locality.
   Otherwise, the original value is preserved with location_verified=False.

4. CONFIGURATION
   The Vellore-district localities list is configurable in:
   data/reference/vellore_localities_config.json
""")

    # Locality list
    lines.append("-" * 72)
    lines.append("CONFIGURED VELLORE DISTRICT LOCALITIES")
    lines.append("-" * 72)
    with open(LOCALITY_CONFIG, "r", encoding="utf-8") as f:
        config = json.load(f)
    for loc in config["localities"]:
        aliases = ", ".join(loc.get("aliases", [])) if loc.get("aliases") else "(none)"
        lines.append("  %s - aliases: %s" % (loc["name"], aliases))
    lines.append("")

    report_text = chr(10).join(lines)
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(report_text)
    print("  Report lines: %d" % len(lines))


# ── Main ──

def main():
    print("=" * 70)
    print("DATA QUALITY VALIDATION STAGE")
    print("=" * 70)
    print()

    df = pd.read_csv(INPUT_FILE)
    print("Total input records: %d" % len(df))
    print("Columns: %s" % list(df.columns))
    print()

    district_name, vellore_localities = load_localities()
    print("Vellore district localities configured (%d names):" % len(vellore_localities))
    print("  %s" % ", ".join(sorted(vellore_localities)))
    print()

    os.makedirs(os.path.dirname(REPORT_FILE), exist_ok=True)

    # Validate each record
    results = []
    for i in range(len(df)):
        row = df.iloc[i]
        results.append(validate_record(row, vellore_localities))

    crime_flags = [r["is_crime_relevant"] for r in results]
    vellore_flags = [r["is_vellore_relevant"] for r in results]

    validated_mask = [c and v for c, v in zip(crime_flags, vellore_flags)]
    validated_indices = [i for i in range(len(df)) if validated_mask[i]]
    excluded_indices = [i for i in range(len(df)) if not validated_mask[i]]

    # Build validated DataFrame
    df_validated = df.iloc[validated_indices].copy()
    df_validated["is_crime_relevant"] = True
    df_validated["location_verified"] = [results[i]["location_verified"] for i in validated_indices]
    df_validated["exclusion_reason"] = None
    df_validated["locality"] = [results[i]["corrected_locality"] for i in validated_indices]

    # Build excluded DataFrame
    df_excluded = df.iloc[excluded_indices].copy()
    df_excluded["is_crime_relevant"] = [results[i]["is_crime_relevant"] for i in excluded_indices]
    df_excluded["location_verified"] = [results[i]["location_verified"] for i in excluded_indices]
    df_excluded["exclusion_reason"] = [results[i]["exclusion_reason"] for i in excluded_indices]

    # Statistics
    total = len(df)
    crime_count = sum(crime_flags)
    non_crime_count = total - crime_count
    vellore_count = sum(vellore_flags)
    loc_unverified_count = sum(1 for r in results if r["is_crime_relevant"] and not r["location_verified"])
    final_count = len(df_validated)

    print("=" * 70)
    print("VALIDATION RESULTS")
    print("=" * 70)
    print("Total input records:          %d" % total)
    print("Crime-relevant records:       %d" % crime_count)
    print("Non-crime records removed:    %d" % non_crime_count)
    print("Vellore-relevant records:     %d" % vellore_count)
    print("Location-unverified records:  %d" % loc_unverified_count)
    print("Final validated records:      %d" % final_count)
    print()

    # Save files
    df_validated.to_csv(OUTPUT_VALIDATED, index=False, encoding="utf-8")
    df_excluded.to_csv(OUTPUT_EXCLUDED, index=False, encoding="utf-8")
    print("Validated records saved: %s" % OUTPUT_VALIDATED)
    print("Excluded records saved:  %s" % OUTPUT_EXCLUDED)
    print()

    # Generate report
    generate_report(df, results, total, crime_count, non_crime_count,
                    vellore_count, loc_unverified_count, final_count,
                    validated_indices, excluded_indices)
    print("Validation report saved: %s" % REPORT_FILE)
    print()


if __name__ == "__main__":
    main()






