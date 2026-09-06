# CrimeSense Database Schema

Final handoff dataset for the backend/database import. A single physical table is defined by `crimesense_database_import.csv`, keyed on `article_id`.

## Primary Key

| Field | Type | Role |
|---|---|---|
| `article_id` | TEXT | `PRIMARY KEY` |

## Columns

| Field | Data Type | Description | Nullable | Example |
|---|---|---|---|---|
| `article_id` | TEXT/VARCHAR(64) | Unique primary key for each crime incident (hash of the original article). | NOT NULL | 70d2d39686e4ee8b |
| `title` | TEXT | Headline of the original news article. | NOT NULL | Four get 20 years imprisonment in 2022 Katpadi gang-rape case |
| `published_date` | TEXT | Publication date of the article (RFC-1123 format). | NOT NULL | Thu, 30 Jan 2025 08:00:00 GMT |
| `source` | TEXT | Name of the publishing outlet. | NULLABLE | The Hindu |
| `url` | TEXT | Original canonical URL of the article. | NOT NULL | https://www.… |
| `crime_type` | TEXT | Normalised crime category label. | NOT NULL | Sexual Assault |
| `description` | TEXT | Article description / body snippet. | NOT NULL | Two persons were arrested for… |
| `district` | TEXT | Administrative district. | NOT NULL | Vellore |
| `locality` | TEXT | Specific locality/neighbourhood of the incident (empty/NULL when not mentioned). | NULLABLE | Katpadi |
| `latitude` | NUMERIC(9,6) | Decimal latitude of the incident. NULL when the location was not geocoded. | NULLABLE | 13.043505 |
| `longitude` | NUMERIC(9,6) | Decimal longitude of the incident. NULL when the location was not geocoded. | NULLABLE | 79.240410 |
| `location_confidence` | TEXT | Confidence of the geocoding: HIGH / LOW / UNKNOWN. | NULLABLE | HIGH |
| `location_source` | TEXT | Free-text note describing how the location was derived. | NULLABLE | Vellore mentioned without exact incident locality |
| `severity_score` | INTEGER | Numeric risk weight (2 / 5 / 8 / 10). 10=Critical, 8=High, 5=Medium, 2=Low. | NULLABLE | 10 |
| `risk_level` | TEXT | Categorical risk level: Critical / High / Medium / Low. | NULLABLE | Critical |

## Notes

* `article_id` is unique and non-null (89 records).
* Only 7 records have geocoded `latitude`/`longitude`; the other 82 are NULL for these two columns.
* `risk_level` / `severity_score` are jointly set; a row either has both or neither.