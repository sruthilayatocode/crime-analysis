import { useState, useEffect, useRef } from 'react'
import CurrentLocationCard from '../components/CurrentLocationCard'
import SafetyStatusCard from '../components/SafetyStatusCard'
import NearestHotspotCard from '../components/NearestHotspotCard'
import MiniMapPlaceholder from '../components/MiniMapPlaceholder'
import NearbyCrimeSummary from '../components/NearbyCrimeSummary'
import LocationHistoryTable from '../components/LocationHistoryTable'
import PageHeader from '../components/PageHeader'
import { checkProximity, getNearbyCrimes } from '../services/api'

const DEFAULT_COORDS = {
  latitude: 12.9165,
  longitude: 79.1325,
  accuracy: 15,
  lastUpdated: 'Default (Vellore, TN)',
}

function GPSTracking() {
  const [location, setLocation] = useState(DEFAULT_COORDS)
  const [isLiveActive, setIsLiveActive] = useState(false)
  const [loading, setLoading] = useState(false)
  const [geoError, setGeoError] = useState('')

  const [safety, setSafety] = useState({
    level: 'Safe',
    message: 'Click "Enable Live GPS" to check your real-time proximity against verified crime hotspots.',
  })

  const [nearestSpot, setNearestSpot] = useState({
    name: 'Jurisdiction Monitoring',
    crimeType: 'Awaiting Location',
    distance: 0,
    risk: 'Low',
  })

  const [crimeSummary, setCrimeSummary] = useState({
    totalCrimes: 0,
    mostCommonCrime: 'None nearby',
    lastReported: 'No incidents detected in range',
  })

  const [history, setHistory] = useState([])
  const watchIdRef = useRef(null)

  const evaluateProximity = async (lat, lng) => {
    try {
      const [proxRes, nearbyRes] = await Promise.all([
        checkProximity(lat, lng, 1000).catch(() => null),
        getNearbyCrimes(lat, lng, 5).catch(() => ({ data: [] })),
      ])

      const timeStr = new Date().toLocaleTimeString()
      let statusLevel = 'Safe'

      if (proxRes && proxRes.success) {
        const hotspot = proxRes.nearest_hotspot
        const isNearby = proxRes.alert
        const distKm = (proxRes.distance_meters / 1000).toFixed(2)

        statusLevel = isNearby
          ? hotspot?.risk_level === 'High'
            ? 'High Risk'
            : 'Medium Risk'
          : 'Safe'

        setSafety({
          level: statusLevel,
          message: isNearby
            ? `Warning: You are approximately ${Math.round(proxRes.distance_meters)}m from ${hotspot?.location || 'a crime hotspot'}. Please remain alert and avoid isolated areas.`
            : `You are outside the active alert radius. Nearest detected hotspot is ${hotspot?.location || 'Vellore area'} (${distKm} km away).`,
        })

        if (hotspot) {
          setNearestSpot({
            name: hotspot.location || 'Hotspot Zone',
            crimeType: `${hotspot.crime_count || 0} verified crimes recorded`,
            distance: distKm,
            risk: hotspot.risk_level || 'Medium',
            latitude: hotspot.latitude,
            longitude: hotspot.longitude,
          })
        }
      }

      if (nearbyRes && nearbyRes.data) {
        const crimes = nearbyRes.data
        const counts = {}
        crimes.forEach((c) => {
          counts[c.crime_type] = (counts[c.crime_type] || 0) + 1
        })
        const mostCommon =
          Object.keys(counts).sort((a, b) => counts[b] - counts[a])[0] || 'None'
        const latest = crimes[0]

        setCrimeSummary({
          totalCrimes: crimes.length,
          mostCommonCrime: mostCommon,
          lastReported: latest
            ? `${latest.crime_type} at ${latest.location_name || 'Vellore'} (${latest.crime_date || 'Recent'})`
            : 'No incidents recorded in immediate 5 km radius',
        })
      }

      // Add to session history
      setHistory((prev) => [
        {
          id: Date.now(),
          time: timeStr,
          latitude: lat.toFixed(4),
          longitude: lng.toFixed(4),
          status: statusLevel,
        },
        ...prev.slice(0, 7),
      ])
    } catch {
      // Graceful fallback on API error
    }
  }

  const handleStartTracking = () => {
    if (!navigator.geolocation) {
      setGeoError('Geolocation is not supported by your browser.')
      return
    }

    setLoading(true)
    setGeoError('')

    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const lat = pos.coords.latitude
        const lng = pos.coords.longitude
        const acc = Math.round(pos.coords.accuracy || 10)
        const updated = {
          latitude: lat,
          longitude: lng,
          accuracy: acc,
          lastUpdated: new Date().toLocaleTimeString(),
        }
        setLocation(updated)
        setIsLiveActive(true)
        setLoading(false)
        evaluateProximity(lat, lng, acc)
      },
      (err) => {
        setLoading(false)
        setIsLiveActive(false)
        setGeoError(`Unable to retrieve location: ${err.message}. Please verify browser permissions.`)
      },
      { enableHighAccuracy: true, timeout: 10000 }
    )
  }

  const handleStopTracking = () => {
    if (watchIdRef.current) {
      navigator.geolocation.clearWatch(watchIdRef.current)
      watchIdRef.current = null
    }
    setIsLiveActive(false)
  }

  useEffect(() => {
    return () => {
      if (watchIdRef.current) {
        navigator.geolocation.clearWatch(watchIdRef.current)
      }
    }
  }, [])

  return (
    <div className="space-y-6">
      <PageHeader
        title="GPS Location & Proximity Alerts"
        description="Monitor real-time device location and check distance against active crime hotspots."
        badge={
          <div className="flex items-center gap-3">
            {isLiveActive ? (
              <div className="flex items-center gap-2 rounded-lg bg-green-500/10 border border-green-500/30 px-3.5 py-1.5 text-xs font-semibold text-green-400">
                <span className="flex h-2 w-2 relative">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75" />
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500" />
                </span>
                <span>Live GPS Active</span>
              </div>
            ) : (
              <div className="flex items-center gap-2 rounded-lg bg-gray-800 border border-gray-700 px-3.5 py-1.5 text-xs font-medium text-gray-400">
                <span className="h-2 w-2 rounded-full bg-gray-500" />
                <span>GPS Ready (Standby)</span>
              </div>
            )}

            {!isLiveActive ? (
              <button
                type="button"
                onClick={handleStartTracking}
                disabled={loading}
                className="rounded-lg bg-blue-600 px-4 py-2 text-xs font-semibold text-white shadow transition-colors hover:bg-blue-700 disabled:opacity-50"
              >
                {loading ? 'Detecting Location...' : 'Enable Live GPS'}
              </button>
            ) : (
              <button
                type="button"
                onClick={handleStopTracking}
                className="rounded-lg bg-gray-800 px-3.5 py-2 text-xs font-semibold text-gray-300 transition-colors hover:bg-gray-700"
              >
                Pause GPS
              </button>
            )}
          </div>
        }
      />

      {geoError && (
        <div className="rounded-lg border border-yellow-500/30 bg-yellow-500/10 p-4 text-xs sm:text-sm text-yellow-300">
          {geoError}
        </div>
      )}

      {/* Top Cards: Current Location, Safety Status, Nearest Hotspot */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <CurrentLocationCard location={location} />
        <SafetyStatusCard safety={safety} />
        <NearestHotspotCard hotspot={nearestSpot} />
      </div>

      {/* Map and Summary */}
      <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
        <MiniMapPlaceholder
          location={location}
          radiusMeters={500}
          nearestHotspot={nearestSpot}
        />
        <NearbyCrimeSummary summary={crimeSummary} />
      </div>

      {/* Session Location History */}
      <LocationHistoryTable
        history={
          history.length > 0
            ? history
            : [
                {
                  id: 1,
                  time: location.lastUpdated,
                  latitude: location.latitude.toFixed(4),
                  longitude: location.longitude.toFixed(4),
                  status: safety.level,
                },
              ]
        }
      />
    </div>
  )
}

export default GPSTracking