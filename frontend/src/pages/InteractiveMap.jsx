import { MapContainer, TileLayer, Circle, useMap } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'
import HotspotMarker from '../components/HotspotMarker'
import UserLocationMarker from '../components/UserLocationMarker'
import MapLegend from '../components/MapLegend'
import PageHeader from '../components/PageHeader'
import Card from '../components/Card'
import { hotspotMarkers, userLocation, heatmapZones } from '../data/mapData'

const heatmapColors = {
  high: { color: '#ef4444', fillColor: '#ef4444', opacity: 0.6, fillOpacity: 0.15 },
  medium: { color: '#eab308', fillColor: '#eab308', opacity: 0.5, fillOpacity: 0.12 },
  low: { color: '#22c55e', fillColor: '#22c55e', opacity: 0.4, fillOpacity: 0.1 },
}

function MapController() {
  const map = useMap()
  return null
}

function InteractiveMap() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="Interactive Map"
        description="Real-time crime hotspot visualization with proximity alerts."
        badge={
          <div className="flex items-center gap-3">
            <div className="rounded-lg bg-gray-800/50 px-4 py-2">
              <p className="text-xs text-gray-500">Hotspots</p>
              <p className="text-sm font-medium text-gray-300">{hotspotMarkers.length}</p>
            </div>
            <div className="rounded-lg bg-gray-800/50 px-4 py-2">
              <p className="text-xs text-gray-500">High Risk</p>
              <p className="text-sm font-medium text-red-400">
                {hotspotMarkers.filter((h) => h.risk === 'High').length}
              </p>
            </div>
          </div>
        }
      />

      {/* Map */}
      <Card className="p-0">
        <div className="relative h-[500px] w-full sm:h-[600px]">
          <MapContainer
            center={[userLocation.lat, userLocation.lng]}
            zoom={13}
            scrollWheelZoom={true}
            className="h-full w-full"
          >
            <MapController />
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />

            {/* Heatmap placeholder circles */}
            {heatmapZones.map((zone) => {
              const intensity = zone.intensity
              const color =
                intensity >= 0.7
                  ? heatmapColors.high
                  : intensity >= 0.4
                  ? heatmapColors.medium
                  : heatmapColors.low
              return (
                <Circle
                  key={zone.id}
                  center={[zone.lat, zone.lng]}
                  radius={zone.radius}
                  pathOptions={{
                    color: color.color,
                    fillColor: color.fillColor,
                    opacity: color.opacity,
                    fillOpacity: color.fillOpacity,
                  }}
                />
              )
            })}

            {/* Hotspot markers */}
            {hotspotMarkers.map((hotspot) => (
              <HotspotMarker key={hotspot.id} hotspot={hotspot} />
            ))}

            {/* User location marker */}
            <UserLocationMarker location={userLocation} />
          </MapContainer>

          {/* Legend overlay */}
          <div className="absolute bottom-4 left-4 z-[1000]">
            <MapLegend />
          </div>
        </div>
      </Card>

      {/* Info cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div className="rounded-xl border border-gray-800 bg-gray-900/50 p-4 transition-colors duration-200 hover:border-gray-700">
          <div className="flex items-center gap-3">
            <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-red-500/20">
              <span className="h-3 w-3 rounded-full bg-red-500" />
            </span>
            <div>
              <p className="text-sm font-medium text-gray-300">High Risk Zones</p>
              <p className="text-lg font-bold text-red-400">
                {hotspotMarkers.filter((h) => h.risk === 'High').length}
              </p>
            </div>
          </div>
        </div>
        <div className="rounded-xl border border-gray-800 bg-gray-900/50 p-4 transition-colors duration-200 hover:border-gray-700">
          <div className="flex items-center gap-3">
            <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-yellow-500/20">
              <span className="h-3 w-3 rounded-full bg-yellow-500" />
            </span>
            <div>
              <p className="text-sm font-medium text-gray-300">Medium Risk Zones</p>
              <p className="text-lg font-bold text-yellow-400">
                {hotspotMarkers.filter((h) => h.risk === 'Medium').length}
              </p>
            </div>
          </div>
        </div>
        <div className="rounded-xl border border-gray-800 bg-gray-900/50 p-4 transition-colors duration-200 hover:border-gray-700">
          <div className="flex items-center gap-3">
            <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-green-500/20">
              <span className="h-3 w-3 rounded-full bg-green-500" />
            </span>
            <div>
              <p className="text-sm font-medium text-gray-300">Low Risk Zones</p>
              <p className="text-lg font-bold text-green-400">
                {hotspotMarkers.filter((h) => h.risk === 'Low').length}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default InteractiveMap