"""
Data access layer for crime records.

Storage:
    SQLite through the SQLAlchemy Crime model.
"""

from services.errors import StorageError


# Columns of a crime record exposed by the API.
CRIME_COLUMNS = [
    "id",
    "crime_type",
    "description",
    "latitude",
    "longitude",
    "location_name",
    "crime_date",
    "severity",
    "created_at",
]


class CrimeRepository:
    """
    Crime record storage backed by SQLite via SQLAlchemy.
    """

    def list_crimes(self):
        from models.crime import Crime

        crimes = (
            Crime.query
            .order_by(Crime.id)
            .all()
        )

        return [
            crime.to_dict()
            for crime in crimes
        ]

    def get_crime(self, crime_id):
        from database import db
        from models.crime import Crime

        crime = db.session.get(
            Crime,
            crime_id
        )

        if crime is None:
            return None

        return crime.to_dict()

    def insert_crime(self, payload):
        from database import db
        from models.crime import Crime

        new_crime = Crime(**payload)

        db.session.add(new_crime)

        db.session.commit()

        return new_crime.to_dict()

    def update_crime(
        self,
        crime_id,
        payload
    ):
        from database import db
        from models.crime import Crime

        crime = db.session.get(
            Crime,
            crime_id
        )

        if crime is None:
            return None

        for field, value in payload.items():
            setattr(crime, field, value)

        db.session.commit()

        return crime.to_dict()

    def delete_crime(self, crime_id):
        from database import db
        from models.crime import Crime

        crime = db.session.get(
            Crime,
            crime_id
        )

        if crime is None:
            return False

        db.session.delete(crime)

        db.session.commit()

        return True


def get_crime_repository():
    """
    Return the active crime record repository.

    SQLite is the sole storage backend.
    """
    return CrimeRepository()
