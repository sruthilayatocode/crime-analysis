/**
 * crimeInsights.js
 *
 * Pure helper functions used to turn raw /api/crimes and /api/hotspots
 * responses into the derived statistics shown on the dashboard, hotspot
 * table, and interactive map. No data is hardcoded here.
 */

/**
 * Extract a 4-digit year from a date string (e.g. "Fri, 12 Jun 2026 07:00:00 GMT").
 * Returns an integer year or null when no year can be parsed.
 */
export function extractYear(dateString) {
  if (!dateString) return null
  const match = String(dateString).match(/(20\d{2})/)
  return match ? parseInt(match[1], 10) : null
}

/** True when the given crime record has usable latitude/longitude values. */
export function hasCoordinates(crime) {
  return (
    crime &&
    Number.isFinite(Number(crime.latitude)) &&
    Number.isFinite(Number(crime.longitude))
  )
}

/** Return a human-friendly date label, or the raw value when unparseable. */
export function formatDate(dateString) {
  if (!dateString) return 'Unknown'
  const date = new Date(dateString)
  if (Number.isNaN(date.getTime())) return String(dateString)
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

/** Count crime records by their risk_level (falls back to 'Unknown'). */
export function countByRiskLevel(crimes) {
  const counts = { Critical: 0, High: 0, Medium: 0, Low: 0, Unknown: 0 }
  for (const crime of crimes || []) {
    const level = crime && crime.risk_level
    const key = counts[level] !== undefined ? level : 'Unknown'
    counts[key] += 1
  }
  return counts
}

/**
 * Build the four dashboard KPI cards from the actual records.
 * Critical and High are grouped into the high-severity card so the existing
 * four-card grid is preserved while every record is counted exactly once.
 */
export function buildKpis(crimes) {
  const counts = countByRiskLevel(crimes || [])
  return [
    { id: 1, label: 'Total Crimes', value: crimes ? crimes.length : 0, color: 'blue' },
    {
      id: 2,
      label: 'High Risk Incidents',
      value: counts.Critical + counts.High,
      color: 'red',
    },
    { id: 3, label: 'Medium Risk Incidents', value: counts.Medium, color: 'yellow' },
    { id: 4, label: 'Low Risk Incidents', value: counts.Low, color: 'green' },
  ]
}

/**
 * Count crime records by crime_type, returned as a descending-sorted array
 * of { label, count } objects.
 */
export function countByCrimeType(crimes) {
  const counts = {}
  for (const crime of crimes || []) {
    const type = (crime && crime.crime_type) || 'Unknown'
    counts[type] = (counts[type] || 0) + 1
  }
  return Object.entries(counts)
    .map(([label, count]) => ({ label, count }))
    .sort((a, b) => b.count - a.count)
}

/**
 * Group crime records by the year in published_date (ascending by year).
 * Returns an array of { label, count } objects.
 */
export function trendByYear(crimes) {
  const counts = {}
  for (const crime of crimes || []) {
    const year = extractYear(crime && crime.published_date)
    if (year === null || year === undefined) continue
    counts[year] = (counts[year] || 0) + 1
  }
  return Object.entries(counts)
    .map(([year, count]) => ({ label: String(year), count }))
    .sort((a, b) => Number(a.label) - Number(b.label))
}

/**
 * Derive the dominant risk label for a hotspot from its per-risk incident counts.
 * Falls back to 'Unknown' when no counts or data are present.
 */
export function deriveHotspotRisk(hotspot) {
  if (!hotspot) return 'Unknown'
  if (Number(hotspot.critical_count) > 0) return 'Critical'
  if (Number(hotspot.high_count) > 0) return 'High'
  if (Number(hotspot.medium_count) > 0) return 'Medium'
  if (Number(hotspot.low_count) > 0) return 'Low'
  return 'Unknown'
}

/** A stable display name for a hotspot. */
export function hotspotZone(hotspot) {
  if (!hotspot) return 'Unknown zone'
  return hotspot.location_name || hotspot.zone || `Hotspot ${hotspot.hotspot_id}`
}

/** Convert a raw hotspot payload into the marker shape used by the map. */
export function toHotspotMarker(hotspot) {
  const lat = Number(hotspot.latitude)
  const lng = Number(hotspot.longitude)
  return {
    id: hotspot.hotspot_id,
    zone: hotspotZone(hotspot),
    lat,
    lng,
    risk: deriveHotspotRisk(hotspot),
    crimeCount: Number(hotspot.incident_count) || 0,
    incidents: hotspot.dominant_crime_type || 'Unknown',
    weightedScore: hotspot.weighted_risk_score,
  }
}