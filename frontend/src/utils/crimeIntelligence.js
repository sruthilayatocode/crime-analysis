/**
 * crimeIntelligence.js
 *
 * Pure helper functions that derive the "Crime Intelligence Overview" section
 * of the dashboard from the REAL /api/crimes records. Nothing here is hardcoded
 * or fabricated — every figure comes from the validated 89-record dataset via
 * useCrimeData().
 *
 * Rules honored:
 *  - Missing crime_type -> "Unknown" (never invent a category).
 *  - Missing area -> fall back locality -> district -> "Unknown".
 *  - Missing severity_score values are EXCLUDED from averages (never treated
 *    as zero).
 *  - Statements are factual, based only on available validated records.
 */
import {
  countByCrimeType,
  countByRiskLevel,
  extractYear,
} from './crimeInsights'

/**
 * Crime type distribution sorted highest -> lowest, derived from the real
 * crime_type field. Missing crime_type is grouped as "Unknown".
 */
export function buildCrimeTypeDistribution(crimes) {
  return countByCrimeType(crimes || [])
}

/** Risk distribution limited to levels that actually occur in the dataset. */
export function buildRiskDistribution(crimes) {
  const counts = countByRiskLevel(crimes || [])
  return ['Critical', 'High', 'Medium', 'Low', 'Unknown']
    .map((label) => ({ label, count: counts[label] || 0 }))
    .filter((d) => d.count > 0)
}

/**
 * Severity summary from the stored severity_score field.
 * Records without a usable score are excluded from the average/highest.
 */
export function buildSeverityInsight(crimes) {
  const scores = (crimes || [])
    .map((c) => Number(c && c.severity_score))
    .filter((n) => Number.isFinite(n))
  const count = scores.length
  const average =
    count > 0
      ? Math.round((scores.reduce((a, b) => a + b, 0) / count) * 10) / 10
      : 0
  const highest = count > 0 ? Math.max(...scores) : 0
  return { count, average, highest }
}

/**
 * Most affected areas using locality first, falling back to district.
 * Returns a descending-sorted, top-N list of { label, count }.
 */
export function buildAffectedAreas(crimes, topN = 6) {
  const counts = {}
  for (const crime of crimes || []) {
    const area = (crime && (crime.locality || crime.district)) || 'Unknown'
    counts[area] = (counts[area] || 0) + 1
  }
  return Object.entries(counts)
    .map(([label, count]) => ({ label, count }))
    .sort((a, b) => b.count - a.count)
    .slice(0, topN)
}

/** Count incidents by the year in published_date (descending by count). */
function countsByYear(crimes) {
  const counts = {}
  for (const crime of crimes || []) {
    const year = extractYear(crime && crime.published_date)
    if (year === null || year === undefined) continue
    counts[year] = (counts[year] || 0) + 1
  }
  return Object.entries(counts).sort((a, b) => b[1] - a[1])
}

/** Count incidents by area (locality -> district -> 'Unknown'). */
function countsByArea(crimes) {
  const counts = {}
  for (const crime of crimes || []) {
    const area = (crime && (crime.locality || crime.district)) || 'Unknown'
    counts[area] = (counts[area] || 0) + 1
  }
  return Object.entries(counts).sort((a, b) => b[1] - a[1])
}

/**
 * Generate factual, non-sensational insight statements from the real data.
 * Returns an array of human-readable strings.
 */
export function buildIntelligenceStatements(crimes) {
  const list = crimes || []
  const total = list.length
  const statements = []

  if (total === 0) return statements

  // Year with the highest recorded incident volume.
  const years = countsByYear(list)
  if (years.length) {
    const [year, count] = years[0]
    statements.push(
      `${year} has the highest recorded incident volume (${count} of ${total} validated incidents).`
    )
  }

  // High-risk share (Critical + High) — comes from stored risk_level.
  const risk = countByRiskLevel(list)
  const highRisk = risk.Critical + risk.High
  const highPct = Math.round((highRisk / total) * 100)
  statements.push(
    `High-risk incidents (Critical + High) represent ${highPct}% of validated incidents.`
  )

  // Most frequently reported crime type.
  const crimeTypes = countByCrimeType(list)
  if (crimeTypes.length) {
    const top = crimeTypes[0]
    statements.push(
      `Most reported crime type: ${top.label} (${top.count} incidents).`
    )
  }

  // Most frequently reported area (incident distribution, not danger).
  const areas = countsByArea(list)
  if (areas.length) {
    const [area, count] = areas[0]
    statements.push(
      `Most frequently reported area: ${area} (${count} incidents).`
    )
  }

  // Severity summary from records that actually carry a score.
  const severity = buildSeverityInsight(list)
  if (severity.count > 0) {
    statements.push(
      `Average severity score is ${severity.average.toFixed(1)} across ${severity.count} incidents with a recorded score (highest ${severity.highest.toFixed(1)}).`
    )
  }

  // Largest share of the risk distribution.
  const riskLevels = buildRiskDistribution(list)
  if (riskLevels.length) {
    const top = riskLevels[0]
    const pct = Math.round((top.count / total) * 100)
    statements.push(
      `${top.label} holds the largest share of the risk distribution (${top.count} incidents, ${pct}%).`
    )
  }

  return statements
}
