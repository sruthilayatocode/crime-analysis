import { MapContainer, TileLayer, Marker, Popup, Circle } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'
import L from 'leaflet'
import Card from './Card'
import CardHeader from './CardHeader'

const userPin = L.divIcon({
  className: 'live-user-pin',
  html: `
    <div style="position: relative; width: 22px; height: 22px;">
      <div style="position: absolute; inset: -8px; background: rgba(59, 130, 246, 0.35); border-radius: 50%;"></div>
      <div style="position: absolute; inset: 0; background: #2563eb; border: 3px solid white; border-radius: 50%; box-shadow: 0 2px 8px rgba(0,0,0,0.5);"></div>
    </div>
  `,
  iconSize: [22, 22],
  iconAnchor: [11, 11],
})

function MiniMapPlaceholder({ location, radiusMeters = 500, nearestHotspot = null }) {
  const lat = location?.latitude ?? location?.lat ?? 12.9165
  const lng = location?.longitude ?? location?.lng ?? 79.1325
  const hasCoordinates = location?.latitude != null || location?.lat != null

  return (
    <Card className="overflow-hidden p-0">
      <div className="p-4 sm:p-5 pb-3">
        <CardHeader
          title="Position Map"
          subtitle={hasCoordinates ? "Live GPS coordinates active" : "Default jurisdiction view (Vellore)"}
          action={
            <span className={`rounded-lg px-2.5 py-1 text-xs font-semibold ${
              hasCoordinates ? 'bg-green-500/10 text-green-400 border border-green-500/30' : 'bg-gray-800 text-gray-400'
            }`}>
              {hasCoordinates ? 'GPS Active' : 'Ready'}
            </span>
          }
        />
      </div>

      <div className="relative h-64 sm:h-72 w-full border-t border-gray-800">
        <MapContainer
          key={`${lat}-${lng}`}
          center={[lat, lng]}
          zoom={14}
          scrollWheelZoom={false}
          className="h-full w-full z-0"
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />

          <Marker position={[lat, lng]} icon={userPin}>
            <Popup>
              <div className="text-xs">
                <p className="font-bold text-gray-900">Your Current Position</p>
                <p className="text-gray-600 font-mono text-[11px]">{Number(lat).toFixed(4)}, {Number(lng).toFixed(4)}</p>
              </div>
            </Popup>
          </Marker>

          {/* Alert radius boundary circle */}
          <Circle
            center={[lat, lng]}
            radius={radiusMeters}
            pathOptions={{
              color: '#3b82f6',
              fillColor: '#3b82f6',
              opacity: 0.7,
              fillOpacity: 0.12,
              dashArray: '4, 4',
            }}
          />

          {nearestHotspot && nearestHotspot.latitude && (
            <Circle
              center={[nearestHotspot.latitude, nearestHotspot.longitude]}
              radius={Math.max(250, (nearestHotspot.crime_count || 1) * 150)}
              pathOptions={{
                color: '#ef4444',
                fillColor: '#ef4444',
                opacity: 0.8,
                fillOpacity: 0.3,
              }}
            >
              <Popup>
                <div className="text-xs">
                  <p className="font-bold text-gray-900">{nearestHotspot.location || 'Nearest Hotspot'}</p>
                  <p className="text-red-600 font-semibold">{nearestHotspot.risk_level || 'High'} Risk</p>
                </div>
              </Popup>
            </Circle>
          )}
        </MapContainer>

        <div className="absolute bottom-3 left-3 z-[1000] rounded-lg bg-gray-900/90 backdrop-blur-sm border border-gray-800 px-3 py-1.5 font-mono text-xs text-gray-300 shadow">
          {Number(lat).toFixed(4)}, {Number(lng).toFixed(4)}
          <span className="ml-2 text-[10px] text-blue-400">({radiusMeters}m perimeter)</span>
        </div>
      </div>
    </Card>
  )
}

export default MiniMapPlaceholder