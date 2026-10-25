import { MapContainer, TileLayer } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'
import HotspotMarker from './HotspotMarker'
import MapLegend from './MapLegend'

/**
 * Reusable Leaflet map that renders real hotspot markers.
 * `markers` should be produced with toHotspotMarker() from the backend
 * /api/hotspots response. Incidents/hotspots without coordinates are filtered
 * out before this component is used, so nothing is ever invented.
 */
function HotspotMap({ markers = [], heightClass = 'h-[420px] w-full' }) {
  const hasMarkers = Array.isArray(markers) && markers.length > 0

  return (
    <div className="relative overflow-hidden rounded-lg border border-gray-800">
      <div className={`relative ${heightClass}`}>
        {hasMarkers ? (
          <MapContainer
            center={[markers[0].lat, markers[0].lng]}
            zoom={12}
            scrollWheelZoom={true}
            className="h-full w-full"
          >
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
            {markers.map((hotspot) => (
              <HotspotMarker key={hotspot.id} hotspot={hotspot} />
            ))}
          </MapContainer>
        ) : (
          <div className="flex h-full w-full items-center justify-center text-center text-sm text-gray-500">
            No verified hotspot coordinates are available from the analysis.
          </div>
        )}

        <div className="absolute bottom-4 left-4 z-[1000]">
          <MapLegend />
        </div>
      </div>
    </div>
  )
}

export default HotspotMap