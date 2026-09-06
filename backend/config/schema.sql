-- ============================================================
-- CrimeSense: crimes table schema for SQLite
--
-- This file is for documentation/reference only.
-- The actual SQLite schema is managed by SQLAlchemy
-- via db.create_all() in backend/app.py.
--
-- The Crime model in backend/models/crime.py is the
-- source of truth for the table structure.
-- ============================================================

create table if not exists crimes (
    id            integer primary key autoincrement,
    crime_type    text    not null,
    description   text,
    latitude      real,
    longitude     real,
    location_name text,
    crime_date    text,
    severity      text,
    created_at    text    not null default (datetime('now'))
);

create index if not exists idx_crimes_crime_type   on crimes (crime_type);
create index if not exists idx_crimes_severity     on crimes (severity);
create index if not exists idx_crimes_location_name on crimes (location_name);
create index if not exists idx_crimes_coordinates  on crimes (latitude, longitude);
