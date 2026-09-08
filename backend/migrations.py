from database import db


def migrate_crime_schema():
    """
    Lightweight SQLite migration for the crimes table.

    Adds any missing columns and indexes so that upgrading
    from an older schema does not require deleting existing data.
    """

    expected_columns = {
        "id": "integer",
        "crime_type": "text",
        "description": "text",
        "latitude": "real",
        "longitude": "real",
        "location_name": "text",
        "crime_date": "text",
        "severity": "text",
        "article_id": "text",
        "title": "text",
        "source": "text",
        "url": "text",
        "district": "text",
        "location_confidence": "text",
        "location_source": "text",
        "severity_score": "integer",
        "risk_level": "text",
        "created_at": "text",
    }

    with db.session.begin():
        result = db.session.execute(
            db.text("PRAGMA table_info(crimes)")
        )
        existing_columns = {
            row[1] for row in result.fetchall()
        }

        for column, column_type in expected_columns.items():
            if column not in existing_columns:
                db.session.execute(
                    db.text(
                        f"ALTER TABLE crimes "
                        f"ADD COLUMN {column} {column_type}"
                    )
                )

    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_crimes_crime_type ON crimes (crime_type)",
        "CREATE INDEX IF NOT EXISTS idx_crimes_severity ON crimes (severity)",
        "CREATE INDEX IF NOT EXISTS idx_crimes_location_name ON crimes (location_name)",
        "CREATE INDEX IF NOT EXISTS idx_crimes_coordinates ON crimes (latitude, longitude)",
        "CREATE INDEX IF NOT EXISTS idx_crimes_article_id ON crimes (article_id)",
        "CREATE INDEX IF NOT EXISTS idx_crimes_district ON crimes (district)",
        "CREATE INDEX IF NOT EXISTS idx_crimes_risk_level ON crimes (risk_level)",
        "CREATE INDEX IF NOT EXISTS idx_crimes_url ON crimes (url)",
    ]

    with db.session.begin():
        for statement in indexes:
            db.session.execute(db.text(statement))
