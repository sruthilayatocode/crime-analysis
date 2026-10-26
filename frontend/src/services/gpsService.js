/**
 * gpsService.js
 *
 * Frontend API service for GPS/proximity features of the CrimeSense Flask
 * backend. Uses ONLY verified (HIGH-confidence) coordinates from the backend -
 * never fabricated locations.
 *
 *   GET  /api/verified-locations  -> { success, count, data: [location, ...] }
 *   POST /api/proximity-check     -> { success, alert_level, nearby_locations, ... }
 */

import { apiFetch } from './apiConfig';

/** Fetch all verified (HIGH-confidence) crime locations from the backend. */
export async function getVerifiedLocations() {
  const payload = await apiFetch('/verified-locations', { method: 'GET' }, 'Fetch verified locations');
  return payload.data || [];
}

/**
 * Run a proximity check against real verified locations using the caller's
 * real latitude/longitude (e.g. from the browser Geolocation API).
 */
export async function checkProximity(latitude, longitude, radiusKm = 2) {
  return apiFetch(
    '/proximity-check',
    {
      method: 'POST',
      body: JSON.stringify({
        latitude,
        longitude,
        radius_km: radiusKm,
      }),
    },
    'Proximity check'
  );
}
