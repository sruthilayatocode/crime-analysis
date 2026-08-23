"""
Data access layer for crime records.

Primary storage:
    Supabase PostgreSQL through the supabase-py client.

Fallback storage (development only):
    Local SQLite database through the existing SQLAlchemy
    Crime model. Used automatically when Supabase
    credentials are not configured in backend/.env.

Both repositories return plain dictionaries so the rest of
the service layer does not care which storage is active.
"""

from config.config import (
    CRIMES_TABLE,
    get_supabase_client,
    supabase_enabled,
)

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


class SupabaseCrimeRepository:
    """
    Crime record storage backed by Supabase PostgreSQL.
    """

    def __init__(
        self,
        client=None,
        table_name=CRIMES_TABLE
    ):

        self.client = (
            client or get_supabase_client()
        )

        self.table_name = table_name

    def _execute(self, query_builder):

        try:

            response = query_builder.execute()

        except Exception as error:

            raise StorageError(
                "Database request failed: "
                f"{error}"
            )

        return response

    def list_crimes(self):

        response = self._execute(
            self.client
            .table(self.table_name)
            .select("*")
            .order("id")
        )

        return response.data or []

    def get_crime(self, crime_id):

        response = self._execute(
            self.client
            .table(self.table_name)
            .select("*")
            .eq("id", crime_id)
            .limit(1)
        )

        rows = response.data or []

        if not rows:
            return None

        return rows[0]

    def insert_crime(self, payload):

        response = self._execute(
            self.client
            .table(self.table_name)
            .insert(payload)
        )

        rows = response.data or []

        if not rows:
            raise StorageError(
                "Crime record could not "
                "be inserted"
            )

        return rows[0]

    def update_crime(
        self,
        crime_id,
        payload
    ):

        response = self._execute(
            self.client
            .table(self.table_name)
            .update(payload)
            .eq("id", crime_id)
        )

        rows = response.data or []

        if not rows:
            return None

        return rows[0]

    def delete_crime(self, crime_id):

        response = self._execute(
            self.client
            .table(self.table_name)
            .delete()
            .eq("id", crime_id)
        )

        return bool(response.data)


class LocalCrimeRepository:
    """
    SQLite fallback used only for local development
    when Supabase credentials are not configured.
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
    Return the active crime record repository:

    - Supabase PostgreSQL when credentials exist.
    - Local SQLite otherwise (development only).
    """

    if supabase_enabled():
        return SupabaseCrimeRepository()

    return LocalCrimeRepository()