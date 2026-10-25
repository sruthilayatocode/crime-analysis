/**
 * crimeService.js
 *
 * Frontend API service for the CrimeSense Flask backend.
 *
 * The backend responses follow this shape:
 *   GET /api/crimes  -> { success, count, data: [crime, ...] }
 *   GET /api/hotspots -> { success, message, source, count, data: [hotspot, ...] }
 */

export { API_BASE_URL } from './apiConfig';

async function request(path) {
  const response = await fetch(`${API_BASE_URL}${path}`)
  if (!response.ok) {
    throw new Error(`Request to ${path} failed with status ${response.status}`)
  }
  const payload = await response.json()
  // Tolerate either the backend envelope ({ data: [...] }) or a bare array.
  if (Array.isArray(payload)) return payload
  if (Array.isArray(payload && payload.data)) return payload.data
  return []
}

/** Fetch all validated crime records from the backend (/api/crimes). */
export async function getCrimes() {
  return request('/api/crimes')
}

/** Fetch the verified hotspot analysis from the backend (/api/hotspots). */
export async function getHotspots() {
  return request('/api/hotspots')
}