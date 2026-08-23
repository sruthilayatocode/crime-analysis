-- ============================================================
-- CrimeSense: crimes table for Supabase PostgreSQL
--
-- Run this once in the Supabase SQL Editor
-- (Dashboard -> SQL Editor -> New query -> paste -> Run).
--
-- Columns match the existing backend Crime model:
--   id, crime_type, description, latitude, longitude,
--   location_name, crime_date, severity (+ created_at)
-- ============================================================

create table if not exists public.crimes (
    id            bigint generated always as identity primary key,
    crime_type    text             not null,
    description   text,
    latitude      double precision not null,
    longitude     double precision not null,
    location_name text,
    crime_date    text,
    severity      text,
    created_at    timestamptz      not null default now()
);

-- Indexes used by the statistics / hotspot queries
create index if not exists idx_crimes_crime_type   on public.crimes (crime_type);
create index if not exists idx_crimes_severity     on public.crimes (severity);
create index if not exists idx_crimes_location_name on public.crimes (location_name);
create index if not exists idx_crimes_coordinates  on public.crimes (latitude, longitude);

-- ------------------------------------------------------------
-- Row Level Security
--
-- The Flask backend is a trusted server-side client. During
-- development the anon key is used with the permissive policy
-- below so CRUD through the API works.
--
-- SECURITY NOTE: before production, either
--   a) tighten these policies (e.g. read-only for anon), or
--   b) switch the backend to the service_role key kept only
--      in backend/.env (never committed).
-- ------------------------------------------------------------

alter table public.crimes enable row level security;

drop policy if exists "crimes_dev_all_access" on public.crimes;

create policy "crimes_dev_all_access"
    on public.crimes
    for all
    to anon, authenticated
    using (true)
    with check (true);