"""
Crime service layer.

Contains validation and business logic for crime
records. Routes call these functions instead of
touching the database directly.
"""

from services.data_service import (
    CRIME_COLUMNS,
    get_crime_repository,
)

from services.errors import (
    NotFoundError,
    ValidationError,
)


# Fields a client may send when creating/updating crimes.
EDITABLE_FIELDS = [
    field
    for field in CRIME_COLUMNS
    if field not in ("id", "created_at")
]

# Coordinates are optional because the handoff dataset
# contains records that could not be geocoded. When they
# are provided they must be valid numbers in range.
REQUIRED_FIELDS = [
    "crime_type",
]


def _validate_latitude(value):

    if not -90 <= value <= 90:
        raise ValidationError(
            "Latitude must be between -90 and 90"
        )

    return value


def _validate_longitude(value):

    if not -180 <= value <= 180:
        raise ValidationError(
            "Longitude must be between "
            "-180 and 180"
        )

    return value


def _coerce_coordinates(data):
    """
    Convert latitude/longitude to floats and
    validate their ranges. Raises ValidationError
    when the values are not valid numbers.
    """

    try:

        latitude = float(
            data["latitude"]
        )

        longitude = float(
            data["longitude"]
        )

    except (TypeError, ValueError):

        raise ValidationError(
            "Latitude and longitude must be "
            "valid numbers"
        )

    _validate_latitude(latitude)
    _validate_longitude(longitude)

    return latitude, longitude


def _build_payload(
    data,
    require_all=False
):
    """
    Build a clean payload containing only known,
    editable fields with validated coordinates.
    """

    if require_all:

        missing_fields = [
            field
            for field in REQUIRED_FIELDS
            if field not in data
        ]

        if missing_fields:
            raise ValidationError(
                "Required fields are missing",
                details={
                    "missing_fields": missing_fields
                }
            )

    payload = {}

    if "crime_type" in data:
        crime_type = str(
            data["crime_type"]
        ).strip()

        if not crime_type:
            raise ValidationError(
                "crime_type cannot be empty"
            )

        payload["crime_type"] = crime_type

    if "description" in data:
        payload["description"] = data[
            "description"
        ]

    if "location_name" in data:
        location_name = data["location_name"]

        if location_name is not None:
            location_name = str(
                location_name
            ).strip() or None

        payload["location_name"] = location_name

    if "crime_date" in data:
        payload["crime_date"] = data[
            "crime_date"
        ]

    if "severity" in data:
        severity = data["severity"]

        if severity is not None:
            severity = str(severity).strip()

        payload["severity"] = severity

    coordinate_fields = (
        "latitude",
        "longitude"
    )

    # Explicit nulls mean "not geocoded" and are
    # treated the same as omitted coordinates.
    supplied_coordinates = [
        field
        for field in coordinate_fields
        if data.get(field) is not None
    ]

    if supplied_coordinates:

        missing = [
            field
            for field in coordinate_fields
            if data.get(field) is None
        ]

        if missing:
            raise ValidationError(
                "Both latitude and longitude "
                "are required together",
                details={
                    "missing_fields": missing
                }
            )

        latitude, longitude = (
            _coerce_coordinates(data)
        )

        payload["latitude"] = latitude
        payload["longitude"] = longitude

    return payload


def list_crimes():
    """Return all crime records."""

    repository = get_crime_repository()

    return repository.list_crimes()


def get_crime(crime_id):
    """Return one crime record or raise 404."""

    repository = get_crime_repository()

    crime = repository.get_crime(
        crime_id
    )

    if crime is None:
        raise NotFoundError(
            f"Crime record {crime_id} "
            "was not found"
        )

    return crime


def create_crime(data):
    """
    Validate input and insert a new crime record.
    Returns the created record.
    """

    if not isinstance(data, dict) or not data:
        raise ValidationError(
            "Request body must contain "
            "crime data as JSON"
        )

    payload = _build_payload(
        data,
        require_all=True
    )

    repository = get_crime_repository()

    return repository.insert_crime(
        payload
    )


def update_crime(
    crime_id,
    data
):
    """
    Validate input and update an existing crime
    record. Returns the updated record.
    """

    get_crime(crime_id)

    if not isinstance(data, dict) or not data:
        raise ValidationError(
            "Request body must contain fields "
            "to update as JSON"
        )

    payload = _build_payload(data)

    if not payload:
        raise ValidationError(
            "No updatable fields were provided"
        )

    repository = get_crime_repository()

    updated = repository.update_crime(
        crime_id,
        payload
    )

    if updated is None:
        raise NotFoundError(
            f"Crime record {crime_id} "
            "was not found"
        )

    return updated


def delete_crime(crime_id):
    """Delete an existing crime record."""

    get_crime(crime_id)

    repository = get_crime_repository()

    deleted = repository.delete_crime(
        crime_id
    )

    if not deleted:
        raise NotFoundError(
            f"Crime record {crime_id} "
            "was not found"
        )

    return {
        "id": crime_id,
        "deleted": True
    }