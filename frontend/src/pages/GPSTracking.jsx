import CurrentLocationCard from '../components/CurrentLocationCard'
import SafetyStatusCard from '../components/SafetyStatusCard'
import NearestHotspotCard from '../components/NearestHotspotCard'
import MiniMapPlaceholder from '../components/MiniMapPlaceholder'
import NearbyCrimeSummary from '../components/NearbyCrimeSummary'
import LocationHistoryTable from '../components/LocationHistoryTable'
import PageHeader from '../components/PageHeader'
import { useGPSTracking } from '../hooks/useGPSTracking'

function GPSTracking() {
  const {
    loading,
    error,
    position,
    positionError,
    nearestHotspot,
    safetyStatus,
    safetyBadge,
    nearbyCrimeSummary,
    history,
    positionAvailable,
  } = useGPSTracking()

  return (
    <div className="space-y-6">
      <PageHeader
        title="GPS Tracking"
        description="Real-time location monitoring with verified-crime proximity alerts."
        badge={
          <div className="flex items-center gap-3">
            <span className="flex h-2 w-2">
              <span className="absolute inline-flex h-2 w-2 animate-ping rounded-full bg-green-400 opacity-75" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-green-500" />
            </span>
            <span className="text-sm font-medium text-green-400">{safetyBadge}</span>
          </div>
        }
      />

      {/* Location permission / error state */ }
      {positionError && (
        <div className="rounded-lg border border-yellow-500/30 bg-yellow-500/10 p-4 text-sm text-yellow-300">
          {positionError}
        </div>
      )}

      {error && <p className="py-6 text-center text-sm text-gray-400">{error}</p>}

      {/* Top cards: position-dependent data only renders once we have a REAL
          browser-derived position. We never fabricate coordinates. */ }
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {position ? (
          <CurrentLocationCard location={position} />
        ) : (
          <CurrentLocationCard
            location={{
              latitude: null,
              longitude: null,
              accuracy: null,
              lastUpdated: null,
            }}
          />
        )}
        <SafetyStatusCard safety={safetyStatus} />
        {nearestHotspot ? (
          <NearestHotspotCard hotspot={nearestHotspot} />
        ) : (
          <NearestHotspotCard
            hotspot={{ name: 'N/A', crimeType: 'N/A', distance: null, risk: 'Unknown' }}
          />
        )}
      </div>

      {/* Map and summary */ }
      <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
        <MiniMapPlaceholder location={position} />
        <NearbyCrimeSummary summary={nearbyCrimeSummary} />
      </div>

      {/* Location history (built only from real position reads) */ }
      <LocationHistoryTable history={history} />

      {loading && !position && (
        <p className="py-12 text-center text-sm text-gray-500">
          Loading verified hotspots&hellip;
        </p>
      )}
    </div>
  )
}

export default GPSTracking
