import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { MapContainer, TileLayer, Circle, Marker, Popup } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'
import L from 'leaflet'
import Card from './Card'
import CardHeader from './CardHeader'
import { getHotspots } from '../services/api'

// Custom circle marker icon for Vellore center
const centerIcon = L.divIcon({
  className: 'vellore-center-pin',
  html: `
    <div style="position: relative; width: 18px; height: 18px;">
      <div style="position: absolute; inset: -6px; background: rgba(59, 130, 246, 0.25); border-radius: 50%;"></div>
      <div style="position: absolute; inset: 0; background: #3b82f6; border: 2.5px solid white; border-radius: 50%; box-shadow: 0 2px 6px rgba(0,0,0,0.4);"></div>
    </div>
  `,
  iconSize: [18, 18],
  iconAnchor: [9, 9],
})

function MapPlaceholder() {
  const [hotspots, setHotspots] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let mounted = true
    getHotspots()
      .then((res) => {
        if (mounted && res?.data) {
          setHotspots(res.data)
        }
      })
      .catch(() => {})
      .finally(() => {
        if (mounted) setLoading(false)
      })
    return () => {
      mounted = false
    }
  }, [])

  const defaultCenter = [12.9165, 79.1325] // Vellore, Tamil Nadu

  return (
    <Card className="overflow-hidden p-0">
      <div className="p-4 sm:p-5 pb-3">
        <CardHeader
          title="Hotspot Spatial Overview"
          subtitle="Real-time geographic clusters (Vellore, TN)"
          action={
            <Link
              to="/map"
              className="inline-flex items-center gap-1.5 rounded-lg bg-blue-600 px-3 py-1.5 text-xs font-semibold text-white transition-colors hover:bg-blue-700 shadow"
            >
              <span>Open Full Map</span>
              <svg className="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
              </svg>
            </Link>
          }
        />
      </div>

      <div className="relative h-64 sm:h-72 w-full border-t border-gray-800">
        <MapContainer
          center={defaultCenter}
          zoom={12}
          scrollWheelZoom={false}
          className="h-full w-full z-0"
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />

          <Marker position={defaultCenter} icon={centerIcon}>
            <Popup>
              <div className="text-xs font-semibold text-gray-900">
                Vellore Central Jurisdiction
              </div>
            </Popup>
          </Marker>

          {hotspots.map((spot, idx) => {
            const lat = spot.average_latitude ?? spot.lat
            const lng = spot.average_longitude ?? spot.lng
            if (lat == null || lng == null) return null

            const isHigh = spot.risk_level === 'High' || spot.risk === 'High'
            const isMed = spot.risk_level === 'Medium' || spot.risk === 'Medium'
            const color = isHigh ? '#ef4444' : isMed ? '#eab308' : '#22c55e'
            const radius = Math.max(300, (spot.crime_count || 1) * 200)

            return (
              <Circle
                key={idx}
                center={[lat, lng]}
                radius={radius}
                pathOptions={{
                  color,
                  fillColor: color,
                  opacity: 0.8,
                  fillOpacity: 0.25,
                }}
              >
                <Popup>
                  <div className="text-xs">
                    <p className="font-bold text-gray-900">{spot.location || spot.zone}</p>
                    <p className="text-gray-600">Risk: <strong style={{ color }}>{spot.risk_level || spot.risk}</strong></p>
                    <p className="text-gray-600">Crimes: {spot.crime_count || spot.crimeCount}</p>
                  </div>
                </Popup>
              </Circle>
            )
          })}
        </MapContainer>

        {/* Floating Legend */}
        <div className="absolute bottom-3 left-3 z-[1000] flex items-center gap-3 rounded-lg bg-gray-900/90 backdrop-blur-sm border border-gray-800 px-3 py-1.5 text-xs text-gray-300 shadow">
          <span className="flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-red-500" /> High
          </span>
          <span className="flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-yellow-500" /> Medium
          </span>
          <span className="flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-green-500" /> Low
          </span>
          {loading && <span className="text-[11px] text-gray-500">(loading...)</span>}
        </div>
      </div>
    </Card>
  )
}

export default MapPlaceholder