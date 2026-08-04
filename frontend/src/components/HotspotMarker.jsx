import { Marker, Popup } from 'react-leaflet'
import L from 'leaflet'

const markerColors = {
  High: '#ef4444',
  Medium: '#eab308',
  Low: '#22c55e',
}

function createHotspotIcon(risk) {
  const color = markerColors[risk] || '#3b82f6'
  return L.divIcon({
    className: 'hotspot-marker',
    html: `
      <div style="
        width: 24px;
        height: 24px;
        background: ${color};
        border: 3px solid rgba(255,255,255,0.9);
        border-radius: 50% 50% 50% 0;
        transform: rotate(-45deg);
        box-shadow: 0 2px 8px rgba(0,0,0,0.4);
      "></div>
    `,
    iconSize: [24, 24],
    iconAnchor: [12, 24],
    popupAnchor: [0, -20],
  })
}

function HotspotMarker({ hotspot }) {
  return (
    <Marker
      position={[hotspot.lat, hotspot.lng]}
      icon={createHotspotIcon(hotspot.risk)}
    >
      <Popup>
        <div className="min-w-[180px]">
          <h3 className="mb-1 text-sm font-bold text-gray-900">{hotspot.zone}</h3>
          <div className="space-y-1 text-xs text-gray-600">
            <p>
              <span className="font-medium">Risk:</span>{' '}
              <span className={`font-semibold ${
                hotspot.risk === 'High' ? 'text-red-600' : hotspot.risk === 'Medium' ? 'text-yellow-600' : 'text-green-600'
              }`}>
                {hotspot.risk}
              </span>
            </p>
            <p>
              <span className="font-medium">Crime Count:</span> {hotspot.crimeCount}
            </p>
          </div>
        </div>
      </Popup>
    </Marker>
  )
}

export default HotspotMarker