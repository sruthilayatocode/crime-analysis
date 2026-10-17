import { Marker, Popup } from 'react-leaflet'
import L from 'leaflet'

function createUserIcon() {
  return L.divIcon({
    className: 'user-location-marker',
    html: `
      <div style="position: relative; width: 20px; height: 20px;">
        <div style="
          position: absolute;
          inset: -8px;
          background: rgba(59, 130, 246, 0.3);
          border-radius: 50%;
          animation: pulse-ring 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
        "></div>
        <div style="
          position: absolute;
          inset: 0;
          background: #3b82f6;
          border: 3px solid white;
          border-radius: 50%;
          box-shadow: 0 2px 8px rgba(0,0,0,0.4);
        "></div>
      </div>
    `,
    iconSize: [20, 20],
    iconAnchor: [10, 10],
    popupAnchor: [0, -12],
  })
}

function UserLocationMarker({ location }) {
  if (!location) return null
  const lat = location.lat ?? location.latitude
  const lng = location.lng ?? location.longitude
  const label = location.label || 'Your Location'

  if (lat == null || lng == null) return null

  return (
    <Marker position={[lat, lng]} icon={createUserIcon()}>
      <Popup>
        <div className="min-w-[150px]">
          <h3 className="mb-1 text-sm font-bold text-gray-900">{label}</h3>
          <p className="font-mono text-xs text-gray-600">
            {Number(lat).toFixed(4)}, {Number(lng).toFixed(4)}
          </p>
        </div>
      </Popup>
    </Marker>
  )
}

export default UserLocationMarker