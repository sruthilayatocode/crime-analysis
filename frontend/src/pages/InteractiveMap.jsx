import { useEffect, useState, useMemo } from 'react'
import { useSearchParams } from 'react-router-dom'
import { MapContainer, TileLayer, Circle, Marker, Popup, useMap } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'
import L from 'leaflet'
import HotspotMarker from '../components/HotspotMarker'
import UserLocationMarker from '../components/UserLocationMarker'
import MapLegend from '../components/MapLegend'
import PageHeader from '../components/PageHeader'
import Card from '../components/Card'
import { getHotspots, getAllCrimes } from '../services/api'

const VELLORE_DEFAULT = [12.9165, 79.1325]

const incidentPinIcon = L.divIcon({
  className: 'crime-incident-pin',
  html: `
    <div style="position: relative; width: 14px; height: 14px;">
      <div style="position: absolute; inset: 0; background: #f97316; border: 2px solid white; border-radius: 50%; box-shadow: 0 1px 4px rgba(0,0,0,0.4);"></div>
    </div>
  `,
  iconSize: [14, 14],
  iconAnchor: [7, 7],
})

function MapFlyController({ center, zoom }) {
  const map = useMap()
  useEffect(() => {
    if (center && center[0] && center[1]) {
      map.flyTo(center, zoom || 13, { duration: 1.2 })
    }
  }, [center, zoom, map])
  return null
}

function InteractiveMap() {
  const [searchParams] = useSearchParams()
  const qLat = searchParams.get('lat')
  const qLng = searchParams.get('lng')

  const [hotspots, setHotspots] = useState([])
  const [crimes, setCrimes] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const [userLocation, setUserLocation] = useState(null)
  const [geoLocating, setGeoLocating] = useState(false)
  const [geoError, setGeoError] = useState('')

  const [riskFilter, setRiskFilter] = useState('All')
  const [showIncidents, setShowIncidents] = useState(true)
  const [showHotspotZones, setShowHotspotZones] = useState(true)

  const [flyTarget, setFlyTarget] = useState(
    qLat && qLng ? [parseFloat(qLat), parseFloat(qLng)] : null
  )

  useEffect(() => {
    let mounted = true
    setLoading(true)
    setError('')

    Promise.all([
      getHotspots().catch(() => ({ data: [] })),
      getAllCrimes('APPROVED').catch(() => ({ data: [] })),
    ])
      .then(([hotspotsRes, crimesRes]) => {
        if (!mounted) return
        setHotspots(hotspotsRes?.data || [])
        setCrimes(crimesRes?.data || [])
      })
      .catch((err) => {
        if (mounted) setError(err.message || 'Unable to load spatial data.')
      })
      .finally(() => {
        if (mounted) setLoading(false)
      })

    return () => {
      mounted = false
    }
  }, [])

  const handleLocateMe = () => {
    if (!navigator.geolocation) {
      setGeoError('Geolocation is not supported by your browser.')
      return
    }

    setGeoLocating(true)
    setGeoError('')

    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const coords = {
          lat: pos.coords.latitude,
          lng: pos.coords.longitude,
          accuracy: pos.coords.accuracy,
          label: 'Your Current Position',
        }
        setUserLocation(coords)
        setFlyTarget([coords.lat, coords.lng])
        setGeoLocating(false)
      },
      (err) => {
        setGeoError(`Location access failed: ${err.message}`)
        setGeoLocating(false)
      },
      { enableHighAccuracy: true, timeout: 10000 }
    )
  }

  // Filter hotspots
  const filteredHotspots = useMemo(() => {
    if (riskFilter === 'All') return hotspots
    return hotspots.filter(
      (h) => (h.risk_level || h.risk || '').toLowerCase() === riskFilter.toLowerCase()
    )
  }, [hotspots, riskFilter])

  // Filter geocoded crimes
  const geocodedCrimes = useMemo(() => {
    return crimes.filter((c) => c.latitude != null && c.longitude != null)
  }, [crimes])

  const highRiskHotspots = hotspots.filter(
    (h) => (h.risk_level || h.risk || '').toLowerCase() === 'high'
  ).length
  const mediumRiskHotspots = hotspots.filter(
    (h) => (h.risk_level || h.risk || '').toLowerCase() === 'medium'
  ).length

  return (
    <div className="space-y-6">
      <PageHeader
        title="Interactive Crime Hotspot Map"
        description="Geospatial visualization of verified crime incidents and DBSCAN hotspot clusters in Vellore."
        badge={
          <div className="flex flex-wrap items-center gap-2">
            <div className="rounded-lg bg-gray-800/60 px-3.5 py-1.5 border border-gray-800">
              <p className="text-[10px] uppercase font-semibold text-gray-500">Hotspots</p>
              <p className="text-sm font-bold text-gray-200">{hotspots.length}</p>
            </div>
            <div className="rounded-lg bg-red-500/10 px-3.5 py-1.5 border border-red-500/20">
              <p className="text-[10px] uppercase font-semibold text-red-400">High Risk</p>
              <p className="text-sm font-bold text-red-400">{highRiskHotspots}</p>
            </div>
            <div className="rounded-lg bg-blue-500/10 px-3.5 py-1.5 border border-blue-500/20">
              <p className="text-[10px] uppercase font-semibold text-blue-400">Verified Pins</p>
              <p className="text-sm font-bold text-blue-400">{geocodedCrimes.length}</p>
            </div>
          </div>
        }
      />

      {error && (
        <div className="rounded-lg border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-400">
          {error}
        </div>
      )}

      {geoError && (
        <div className="rounded-lg border border-yellow-500/30 bg-yellow-500/10 p-3 text-sm text-yellow-300">
          {geoError}
        </div>
      )}

      {/* Map Controls */}
      <Card className="p-4">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-xs font-medium text-gray-400">Filter Risk:</span>
            {['All', 'High', 'Medium', 'Low'].map((level) => (
              <button
                key={level}
                onClick={() => setRiskFilter(level)}
                className={`rounded-lg px-3 py-1 text-xs font-semibold transition-colors ${
                  riskFilter === level
                    ? 'bg-blue-600 text-white shadow'
                    : 'bg-gray-800 text-gray-400 hover:text-white'
                }`}
              >
                {level}
              </button>
            ))}
          </div>

          <div className="flex flex-wrap items-center gap-3 text-xs">
            <label className="flex items-center gap-2 cursor-pointer text-gray-300">
              <input
                type="checkbox"
                checked={showHotspotZones}
                onChange={(e) => setShowHotspotZones(e.target.checked)}
                className="rounded border-gray-700 bg-gray-900 text-blue-600 focus:ring-0"
              />
              Hotspot Zones
            </label>

            <label className="flex items-center gap-2 cursor-pointer text-gray-300">
              <input
                type="checkbox"
                checked={showIncidents}
                onChange={(e) => setShowIncidents(e.target.checked)}
                className="rounded border-gray-700 bg-gray-900 text-orange-500 focus:ring-0"
              />
              Incident Pins ({geocodedCrimes.length})
            </label>

            <button
              type="button"
              onClick={handleLocateMe}
              disabled={geoLocating}
              className="inline-flex items-center gap-1.5 rounded-lg bg-blue-600 px-3 py-1.5 text-xs font-medium text-white transition-colors hover:bg-blue-700 disabled:opacity-50"
            >
              <svg className="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0zM15 11a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
              {geoLocating ? 'Locating...' : 'Locate Me'}
            </button>
          </div>
        </div>
      </Card>

      {/* Map Viewport */}
      <Card className="overflow-hidden p-0 border border-gray-800 shadow-xl">
        <div className="relative h-[480px] w-full sm:h-[620px]">
          <MapContainer
            center={flyTarget || VELLORE_DEFAULT}
            zoom={13}
            scrollWheelZoom={true}
            className="h-full w-full z-0"
          >
            {flyTarget && <MapFlyController center={flyTarget} zoom={14} />}
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />

            {/* Hotspot Zones (Circles & Markers) */}
            {showHotspotZones &&
              filteredHotspots.map((spot, index) => {
                const lat = spot.average_latitude ?? spot.lat
                const lng = spot.average_longitude ?? spot.lng
                if (lat == null || lng == null) return null

                const risk = spot.risk_level || spot.risk || 'Medium'
                const isHigh = risk === 'High'
                const isMed = risk === 'Medium'
                const color = isHigh ? '#ef4444' : isMed ? '#eab308' : '#22c55e'
                const radius = Math.max(350, (spot.crime_count || 1) * 200)

                return (
                  <div key={`hotspot-${index}`}>
                    <Circle
                      center={[lat, lng]}
                      radius={radius}
                      pathOptions={{
                        color,
                        fillColor: color,
                        opacity: 0.8,
                        fillOpacity: isHigh ? 0.25 : 0.15,
                      }}
                    />
                    <HotspotMarker hotspot={spot} />
                  </div>
                )
              })}

            {/* Verified Individual Crime Incidents */}
            {showIncidents &&
              geocodedCrimes.map((crime) => (
                <Marker
                  key={`crime-${crime.id}`}
                  position={[crime.latitude, crime.longitude]}
                  icon={incidentPinIcon}
                >
                  <Popup>
                    <div className="min-w-[170px] text-xs">
                      <span className="font-semibold text-orange-600 uppercase text-[10px] tracking-wider">
                        Verified Crime
                      </span>
                      <h4 className="font-bold text-gray-900 text-sm mt-0.5">{crime.crime_type}</h4>
                      <p className="text-gray-600 mt-1">{crime.location_name || 'Vellore'}</p>
                      <p className="text-gray-500 font-mono text-[11px]">{crime.crime_date || '-'}</p>
                      <p className="mt-1 font-medium text-gray-700">Severity: {crime.severity || 'Medium'}</p>
                      {crime.description && (
                        <p className="mt-1 text-gray-600 text-[11px] italic border-t pt-1">
                          {crime.description}
                        </p>
                      )}
                    </div>
                  </Popup>
                </Marker>
              ))}

            {/* Live User Position */}
            {userLocation && (
              <>
                <UserLocationMarker location={userLocation} />
                {userLocation.accuracy && (
                  <Circle
                    center={[userLocation.lat, userLocation.lng]}
                    radius={userLocation.accuracy}
                    pathOptions={{ color: '#3b82f6', fillOpacity: 0.08, dashArray: '4, 4' }}
                  />
                )}
              </>
            )}
          </MapContainer>

          {/* Map Legend Overlay */}
          <div className="absolute bottom-4 left-4 z-[1000]">
            <MapLegend />
          </div>

          {loading && (
            <div className="absolute top-4 right-4 z-[1000] rounded-lg bg-gray-900/90 border border-gray-800 px-3 py-1.5 text-xs text-gray-300 shadow flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-blue-500 animate-ping" />
              Loading spatial data...
            </div>
          )}
        </div>
      </Card>

      {/* Info Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div className="rounded-xl border border-gray-800 bg-gray-900/50 p-4">
          <div className="flex items-center gap-3">
            <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-red-500/20">
              <span className="h-3 w-3 rounded-full bg-red-500" />
            </span>
            <div>
              <p className="text-xs font-medium text-gray-400">High Risk Clusters</p>
              <p className="text-lg font-bold text-red-400">{highRiskHotspots}</p>
            </div>
          </div>
        </div>

        <div className="rounded-xl border border-gray-800 bg-gray-900/50 p-4">
          <div className="flex items-center gap-3">
            <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-yellow-500/20">
              <span className="h-3 w-3 rounded-full bg-yellow-500" />
            </span>
            <div>
              <p className="text-xs font-medium text-gray-400">Medium Risk Clusters</p>
              <p className="text-lg font-bold text-yellow-400">{mediumRiskHotspots}</p>
            </div>
          </div>
        </div>

        <div className="rounded-xl border border-gray-800 bg-gray-900/50 p-4">
          <div className="flex items-center gap-3">
            <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-orange-500/20">
              <span className="h-3 w-3 rounded-full bg-orange-500" />
            </span>
            <div>
              <p className="text-xs font-medium text-gray-400">Geocoded Incidents</p>
              <p className="text-lg font-bold text-orange-400">{geocodedCrimes.length}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default InteractiveMap