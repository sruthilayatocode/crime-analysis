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
import fallbackCrimes from '../data/fallbackCrimes.json';
import fallbackHotspots from '../data/fallbackHotspots.json';
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
  try {
    return await request('/api/crimes');
  } catch (err) {
    console.warn('[crimeService] Live API unreachable, using verified local dataset:', err.message);
    return fallbackCrimes;
  }
}

/** Fetch the verified hotspot analysis from the backend (/api/hotspots). */
export async function getHotspots() {
  try {
    return await request('/api/hotspots');
  } catch (err) {
    console.warn('[crimeService] Live API unreachable, using verified local hotspots:', err.message);
    return fallbackHotspots;
  }
}

/** Submit a citizen incident report to the backend (/api/crimes/report). */
export async function reportCrime(reportData) {
  try {
    return await request('/api/crimes/report', {
      method: 'POST',
      body: JSON.stringify(reportData),
    });
  } catch (err) {
    console.warn('[crimeService] Backend offline, saving report to demo store:', err.message);
    const existing = JSON.parse(localStorage.getItem('crimesense_my_reports') || '[]');
    const newReport = {
      id: Date.now(),
      ...reportData,
      status: 'PENDING_REVIEW',
      created_at: new Date().toISOString(),
    };
    localStorage.setItem('crimesense_my_reports', JSON.stringify([newReport, ...existing]));
    return { success: true, message: 'Report submitted (Stored in demo mode)', data: newReport };
  }
}

/** Fetch reports submitted by the logged-in citizen (/api/crimes/my-reports). */
export async function getMyReports() {
  try {
    const res = await request('/api/crimes/my-reports');
    return Array.isArray(res) ? res : res.data || [];
  } catch {
    return JSON.parse(localStorage.getItem('crimesense_my_reports') || '[]');
  }
}