/**
 * useGPSTracking.js
 *
 * React hook that provides REAL GPS/proximity data for the GPSTracking page.
 *
 * - The user's current position is obtained from the browser Geolocation API
 *   (opt-in). We NEVER fabricate coordinates: if geolocation is unavailable or
 *   denied, position stays null and the UI shows an informative state instead
 *   of a fake location.
 * - Verified crime locations and proximity alerts come from the real Flask API
 *   (/api/verified-locations and /api/proximity-check), which only use
 *   HIGH-confidence coordinates from the CrimeSense dataset.
 * - A short location history is built from real position reads only.
 */
import { useEffect, useRef, useState } from 'react'
import { checkProximity, getVerifiedLocations } from '../services/gpsService'

const SEVERITY_MAP = {
  CRITICAL: 'High Risk',
  HIGH: 'High Risk',
  MEDIUM: 'Medium Risk',
  LOW: 'Medium Risk',
  NONE: 'Safe',
}
const SAFETY_LABEL = {
  'High Risk': 'High Risk',
  'Medium Risk': 'Medium Risk',
  Safe: 'Safe',
}

function fmtTime(d) {
  return d.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
}

export function useGPSTracking() {
  const [position, setPosition] = useState(null)
  const [positionError, setPositionError] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [verifiedLocations, setVerifiedLocations] = useState([])
  const [proximity, setProximity] = useState(null)
  const [history, setHistory] = useState([])

  const watchIdRef = useRef(null)

  // Request the real device position (opt-in, never fabricated).
  useEffect(() => {
    if (!navigator.geolocation) {
      setPositionError('Geolocation is not supported by your browser.')
      setLoading(false)
      return
    }

    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const p = {
          latitude: pos.coords.latitude,
          longitude: pos.coords.longitude,
          accuracy: pos.coords.accuracy,
          lastUpdated: new Date(pos.timestamp).toISOString(),
        }
        setPosition(p)
        setPositionError('')
        setHistory((h) => [
          {
            id: pos.timestamp,
            time: fmtTime(new Date(pos.timestamp)),
            latitude: p.latitude,
            longitude: p.longitude,
            status: 'Locating',
          },
          ...h.slice(0, 9),
        ])
      },
      (err) => {
        setPositionError(
          err.code === err.PERMISSION_DENIED
            ? 'Location permission denied. Enable it to see nearby crime hotspots.'
            : 'Unable to determine your location.'
        )
      },
      { enableHighAccuracy: true, timeout: 8000 }
    )

    return () => {
      if (watchIdRef.current) {
        navigator.geolocation.clearWatch(watchIdRef.current)
      }
    }
  }, [])

  // Verify the current real position against verified crime locations.
  useEffect(() => {
    if (!position) return
    let cancelled = false
    checkProximity(position.latitude, position.longitude)
      .then((data) => {
        if (cancelled) return
        setProximity(data)
      })
      .catch((e) => {
        if (cancelled) setError(e.message || 'Unable to check proximity.')
      })
    return () => {
      cancelled = true
    }
  }, [position])

  // Load verified locations for the standalone map view (no user position
  // required). This powers the nearest-hotspot/summary cards when a position
  // is unavailable, without inventing one.
  useEffect(() => {
    let cancelled = false
    setLoading(true)
    getVerifiedLocations()
      .then((locs) => {
        if (!cancelled) {
          setVerifiedLocations(locs)
          setError('')
        }
      })
      .catch((e) => {
        if (!cancelled) setError(e.message || 'Unable to load hotspots.')
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [])

  // Derived: nearest verified hotspot from a REAL position.
  const nearestHotspot = proximity
    ? proximity.nearby_locations.length > 0
      ? (() => {
          const n = proximity.nearby_locations[0]
          return {
            name: n.location_name,
            crimeType: n.dominant_crime_type,
            distance: n.distance_km,
            risk: n.highest_risk_level,
            riskDistribution: n.risk_counts,
            incidentCount: n.incident_count,
          }
        })()
      : null
    : null

  const safetyStatus = position
    ? {
        level: SEVERITY_MAP[proximity?.alert_level || 'NONE'] || 'Safe',
        message: proximity?.message || 'No verified hotspots within range.',
      }
    : {
        level: 'Safe',
        message:
          'Enable location access to assess safety for your current position.',
      }

  const nearbyCrimeSummary = proximity
    ? {
        totalCrimes: proximity.verified_locations_nearby,
        mostCommonCrime: proximity.nearby_locations[0]?.dominant_crime_type
          ? proximity.nearby_locations[0].dominant_crime_type
          : 'No verified incidents nearby',
        lastReported: proximity.nearby_locations[0]?.location_name
          ? proximity.nearby_locations[0].location_name
          : 'N/A',
        radiusKm: proximity.radius_km,
        basis: proximity.data_basis,
      }
    : {
        totalCrimes: verifiedLocations.length,
        mostCommonCrime: verifiedLocations[0]?.dominant_crime_type || 'N/A',
        lastReported: 'Verified locations (see map)',
      }

  const safetyBadge = SAFETY_LABEL[safetyStatus.level] || 'Safe'

  return {
    loading,
    error,
    position,
    positionError,
    verifiedLocations,
    proximity,
    nearestHotspot,
    safetyStatus,
    safetyBadge,
    nearbyCrimeSummary,
    history,
    positionAvailable: !!position,
  }
}
