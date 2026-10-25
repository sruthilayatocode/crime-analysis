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

import { API_BASE_URL } from './crimeService'

/** Fetch all verified (HIGH-confidence) crime locations from the backend. */
export async function getVerifiedLocations() {
  const res = await fetch(`${API_BASE_URL}/api/verified-locations`)
  const payload = await res.json()
  if (!res.ok || payload.success === false) {
    throw new Error(
      payload.message || `Request to /api/verified-locations failed (status ${res.status})`
    )
  }
  return payload.data || []
}

/**
 * Run a proximity check against real verified locations using the caller's
 * real latitude/longitude (e.g. from the browser Geolocation API).
 */
export async function checkProximity(latitude, longitude, radiusKm = 2) {
  const res = await fetch(`${API_BASE_URL}/api/proximity-check`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      latitude,
      longitude,
      radius_km: radiusKm,
    }),
  })
  const payload = await res.json()
  if (!res.ok || payload.success === false) {
    throw new Error(
      payload.message || `Proximity check failed (status ${res.status})`
    )
  }
  return payload
}
