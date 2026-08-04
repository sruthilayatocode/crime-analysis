import CurrentLocationCard from '../components/CurrentLocationCard'
import SafetyStatusCard from '../components/SafetyStatusCard'
import NearestHotspotCard from '../components/NearestHotspotCard'
import MiniMapPlaceholder from '../components/MiniMapPlaceholder'
import NearbyCrimeSummary from '../components/NearbyCrimeSummary'
import LocationHistoryTable from '../components/LocationHistoryTable'
import PageHeader from '../components/PageHeader'
import {
  currentLocation,
  safetyStatus,
  nearestHotspot,
  nearbyCrimeSummary,
  locationHistory,
} from '../data/gpsData'

function GPSTracking() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="GPS Tracking"
        description="Real-time location monitoring with proximity alerts for your safety."
        badge={
          <div className="flex items-center gap-3">
            <span className="flex h-2 w-2">
              <span className="absolute inline-flex h-2 w-2 animate-ping rounded-full bg-green-400 opacity-75" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-green-500" />
            </span>
            <span className="text-sm font-medium text-green-400">Tracking Active</span>
          </div>
        }
      />

      {/* Top cards */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <CurrentLocationCard location={currentLocation} />
        <SafetyStatusCard safety={safetyStatus} />
        <NearestHotspotCard hotspot={nearestHotspot} />
      </div>

      {/* Map and summary */}
      <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
        <MiniMapPlaceholder location={currentLocation} />
        <NearbyCrimeSummary summary={nearbyCrimeSummary} />
      </div>

      {/* Location history */}
      <LocationHistoryTable history={locationHistory} />
    </div>
  )
}

export default GPSTracking