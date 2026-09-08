"""
News-to-database ingestion service for CrimeSense.

Converts news-pipeline records (dicts or CSV rows) into the
existing Crime SQLAlchemy model and persists them through the
shared repository layer.

Design rules:
    * Reuses the existing Flask/SQLAlchemy application context.
    * Reuses the existing Crime model and repository.
    * Never performs DELETE/DROP/TRUNCATE operations.
    * Never crashes the whole batch when a single record is bad.

Usage (from the backend/ directory):

    from services.news_ingestion_service import ingest_records

    stats = ingest_records(records)

CSV usage:

    from services.news_ingestion_service import ingest_csv

    stats = ingest_csv("path/to/news.csv")
"""

from email.utils import parsedate_to_datetime


# Field name remapped from the news pipeline to the Crime model.
# locality -> location_name
# published_date -> crime_date
# risk_level -> severity (fallback when severity is absent)

# Reused from the existing project so column lengths stay in sync.
try:
    from app import app
except ModuleNotFoundError:
    from backend.app import app  # noqa: E402

from models.crime import Crime  # noqa: E402
from services.data_service import get_crime_repository  # noqa: E402
from services.errors import ValidationError  # noqa: E402


# Maximum column lengths taken from the existing Crime model so
# the service never stores values that would overflow SQLite.
COLUMN_LIMITS = {
    "crime_type": 100,
    "description": 500,
    "location_name": 200,
    "crime_date": 50,
    "severity": 30,
    "article_id": 64,
    "title": 500,
    "source": 200,
    "url": 1000,
    "district": 200,
    "location_confidence": 50,
    "location_source": 100,
    "risk_level": 30,
}


def _truncate(value, max_length):
    """Truncate a string so it fits the model column length."""

    if value is None:
        return None

    text = str(value)

    if len(text) > max_length:
        text = text[:max_length]

    return text


def _clean_str(value):
    """
    Strip whitespace and convert empty strings to None.

    Mirrors the pattern used in import_dataset.py and
    crime_service._build_payload.
    """

    if value is None:
        return None

    text = str(value).strip()

    return text or None


def _parse_coordinate(raw_value):
    """
    Convert a latitude/longitude value to a float.

    Blank or empty values become None.
    """

    if raw_value is None:
        return None

    text = str(raw_value).strip()

    if not text:
        return None

    return float(text)


def _validate_coordinates(latitude, longitude):
    """
    Validate coordinate ranges.

    latitude  must be -90..90
    longitude must be -180..180
    A ValidationError is raised when a supplied coordinate
    is out of range. Both None is allowed (un-geocoded record).
    """

    if latitude is not None and not -90 <= latitude <= 90:
        raise ValidationError(
            "Latitude must be between -90 and 90"
        )

    if longitude is not None and not -180 <= longitude <= 180:
        raise ValidationError(
            "Longitude must be between -180 and 180"
        )


def _parse_date(raw_value):
    """
    Normalize a date value to YYYY-MM-DD.

    Supports RFC-1123 values such as
        Thu, 30 Jan 2025 08:00:00 GMT
    and common ISO-8601 values. Falls back to the raw
    value when parsing fails so ingestion is not blocked.
    """

    if raw_value is None:
        return None

    text = str(raw_value).strip()

    if not text:
        return None

    try:

        parsed = parsedate_to_datetime(text)

        if parsed is not None:
            return parsed.strftime("%Y-%m-%d")

    except (
        TypeError,
        ValueError
    ):

        pass

    # Try ISO-8601 as a second pass.
    try:

        from datetime import datetime

        parsed = datetime.fromisoformat(
            text.replace("Z", "+00:00")
        )

        return parsed.strftime("%Y-%m-%d")

    except (
        TypeError,
        ValueError
    ):

        return text


def _parse_severity_score(raw_value):
    """Return a validated integer or None."""

    if raw_value is None:
        return None

    text = str(raw_value).strip()

    if not text:
        return None

    try:
        return int(text)
    except ValueError:
        raise ValidationError(
            "severity_score must be a valid integer"
        )


def normalize_record(record):
    """
    Normalize one news-pipeline record into a Crime payload.

    Performs field remapping, date parsing, coordinate
    validation, and respects model string-length limits.

    Returns a dict keyed by Crime model column names.
    Raises ValidationError for invalid coordinates or
    severity_score so the caller can count the record as
    invalid without aborting the whole batch.
    """

    if not isinstance(record, dict):
        raise ValidationError(
            "Record must be a dict"
        )

    # --- latitude / longitude ---------------------------------
    latitude = _parse_coordinate(
        record.get("latitude")
    )
    longitude = _parse_coordinate(
        record.get("longitude")
    )

    _validate_coordinates(latitude, longitude)

    # --- date -------------------------------------------------
    crime_date = _parse_date(
        record.get("published_date")
    )

    # --- risk_level -> severity fallback ----------------------
    severity = _clean_str(
        record.get("severity")
    )

    if not severity:
        severity = _clean_str(
            record.get("risk_level")
        )

    # --- severity_score ---------------------------------------
    severity_score = _parse_severity_score(
        record.get("severity_score")
    )

    payload = {
        "article_id": _truncate(
            _clean_str(record.get("article_id")),
            COLUMN_LIMITS["article_id"]
        ),
        "title": _truncate(
            _clean_str(record.get("title")),
            COLUMN_LIMITS["title"]
        ),
        "source": _truncate(
            _clean_str(record.get("source")),
            COLUMN_LIMITS["source"]
        ),
        "url": _truncate(
            _clean_str(record.get("url")),
            COLUMN_LIMITS["url"]
        ),
        "crime_type": _truncate(
            _clean_str(record.get("crime_type")),
            COLUMN_LIMITS["crime_type"]
        ),
        "description": _truncate(
            _clean_str(record.get("description")),
            COLUMN_LIMITS["description"]
        ),
        "district": _truncate(
            _clean_str(record.get("district")),
            COLUMN_LIMITS["district"]
        ),
        "location_name": _truncate(
            _clean_str(
                record.get("locality")
                or record.get("location_name")
            ),
            COLUMN_LIMITS["location_name"]
        ),
        "crime_date": _truncate(
            _clean_str(crime_date),
            COLUMN_LIMITS["crime_date"]
        ),
        "latitude": latitude,
        "longitude": longitude,
        "location_confidence": _truncate(
            _clean_str(record.get("location_confidence")),
            COLUMN_LIMITS["location_confidence"]
        ),
        "location_source": _truncate(
            _clean_str(record.get("location_source")),
            COLUMN_LIMITS["location_source"]
        ),
        "severity_score": severity_score,
        "severity": _truncate(
            severity,
            COLUMN_LIMITS["severity"]
        ),
        "risk_level": _truncate(
            _clean_str(record.get("risk_level")),
            COLUMN_LIMITS["risk_level"]
        ),
    }

    if not payload["crime_type"]:
        raise ValidationError(
            "crime_type is required and cannot be empty"
        )

    return payload


def _deduplication_key(record):
    """
    Return the stable key used for deduplication.

    Priority:
        1. article_id
        2. url
    Returns None when neither is available.
    """

    article_id = record.get("article_id")

    if article_id:
        return ("article_id", article_id)

    url = record.get("url")

    if url:
        return ("url", url)

    return None


def _find_existing(record):
    """
    Look up an existing Crime by the deduplication key.

    Uses article_id first, then url, matching the priority
    defined in the requirements.
    """

    article_id = record.get("article_id")

    if article_id:
        existing = (
            Crime.query
            .filter_by(article_id=article_id)
            .first()
        )

        if existing:
            return existing

    url = record.get("url")

    if url:
        existing = (
            Crime.query
            .filter_by(url=url)
            .first()
        )

        if existing:
            return existing

    return None


def ingest_records(records):
    """
    Ingest an iterable of news-pipeline records.

    For each record:
      * normalize_record is applied
      * duplicates within the batch are skipped
      * existing DB rows are updated, new rows inserted

    Returns a statistics dict:

        {
            "total": int,
            "inserted": int,
            "updated": int,
            "duplicates": int,
            "invalid": int,
            "missing_coordinates": int,
        }

    Invalid records are counted and skipped rather than
    aborting the batch.
    """

    repository = get_crime_repository()

    stats = {
        "total": 0,
        "inserted": 0,
        "updated": 0,
        "duplicates": 0,
        "invalid": 0,
        "missing_coordinates": 0,
    }

    seen_keys = set()

    for record in records:

        stats["total"] += 1

        try:

            payload = normalize_record(record)

        except ValidationError:

            stats["invalid"] += 1
            continue

        except (
            TypeError,
            ValueError
        ):

            stats["invalid"] += 1
            continue

        if (
            payload.get("latitude") is None
            or payload.get("longitude") is None
        ):

            stats["missing_coordinates"] += 1

        key = _deduplication_key(payload)

        if key is not None:

            if key in seen_keys:

                stats["duplicates"] += 1
                continue

            seen_keys.add(key)

        with app.app_context():

            existing = _find_existing(payload)

            if existing:

                try:

                    repository.update_crime(
                        existing.id,
                        payload
                    )

                    stats["updated"] += 1

                except Exception:

                    stats["invalid"] += 1

            else:

                try:

                    repository.insert_crime(payload)

                    stats["inserted"] += 1

                except Exception:

                    stats["invalid"] += 1

    return stats


def ingest_csv(file_path):
    """
    Read a CSV file and ingest its rows.

    Each row is converted to a dict and passed to
    ingest_records. The CSV column names match the news
    pipeline field names.

    Returns the same statistics dict as ingest_records.
    """

    import csv

    records = []

    with open(
        file_path,
        newline="",
        encoding="utf-8"
    ) as csv_file:

        reader = csv.DictReader(csv_file)

        for row in reader:
            records.append(row)

    return ingest_records(records)
