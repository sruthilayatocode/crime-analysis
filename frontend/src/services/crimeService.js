/**
 * crimeService.js
 *
 * Frontend API service for the CrimeSense Flask backend.
 *
 * The backend responses follow this shape:
 *   GET /api/crimes  -> { success, count, data: [crime, ...] }
 *   GET /api/hotspots -> { success, message, source, count, data: [hotspot, ...] }
 */

import { API_BASE_URL, API_BASE, apiFetch } from './apiConfig';
export { API_BASE_URL, API_BASE };

async function request(path, options = {}) {
  const payload = await apiFetch(path, options, `Crime data request (${path})`);

  // Tolerate either the backend envelope ({ data: [...] }) or a bare array.
  if (Array.isArray(payload)) return payload;
  if (Array.isArray(payload && payload.data)) return payload.data;
  return payload;
}

/** Fetch all validated crime records from the backend (/api/crimes). */
export async function getCrimes() {
  return request('/api/crimes');
}

/** Fetch the verified hotspot analysis from the backend (/api/hotspots). */
export async function getHotspots() {
  return request('/api/hotspots');
}

/** Submit a citizen incident report to the backend (/api/crimes/report). */
export async function reportCrime(reportData) {
  return request('/api/crimes/report', {
    method: 'POST',
    body: JSON.stringify(reportData),
  });
}

/** Fetch reports submitted by the logged-in citizen (/api/crimes/my-reports). */
export async function getMyReports() {
  const res = await request('/api/crimes/my-reports');
  return Array.isArray(res) ? res : res.data || [];
}