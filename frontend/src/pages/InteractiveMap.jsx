import { useMemo } from 'react'
import HotspotMap from '../components/HotspotMap'
import PageHeader from '../components/PageHeader'
import Card from '../components/Card'
import { useCrimeData } from '../hooks/useCrimeData'
import { toHotspotMarker } from '../utils/crimeInsights'

function InteractiveMap() {
  const { hotspots, loading, error } = useCrimeData()

  const markers = useMemo(
    () => (Array.isArray(hotspots) ? hotspots : []).map(toHotspotMarker),
    [hotspots]
  )

  const highCount = markers.filter((h) => h.risk === 'Critical' || h.risk === 'High').length
  const mediumCount = markers.filter((h) => h.risk === 'Medium').length
  const lowCount = markers.filter((h) => h.risk === 'Low').length

  return (
    <div className="space-y-6">
      <PageHeader
        title="Interactive Map"
        description="Verified crime hotspots rendered from the CrimeSense analysis."
        badge={
          <div className="flex items-center gap-3">
            <div className="rounded-lg bg-gray-800/50 px-4 py-2">
              <p className="text-xs text-gray-500">Hotspots</p>
              <p className="text-sm font-medium text-gray-300">{markers.length}</p>
            </div>
            <div className="rounded-lg bg-gray-800/50 px-4 py-2">
              <p className="text-xs text-gray-500">High Risk</p>
              <p className="text-sm font-medium text-red-400">{highCount}</p>
            </div>
          </div>
        }
      />

      {loading && <p className="py-12 text-center text-sm text-gray-500">Loading hotspot coordinates&hellip;</p>}

      {error && <p className="py-6 text-center text-sm text-gray-400">{error}</p>}

      {/* Map */}
      <Card className="p-0">
        <div className="p-6 pb-0">
          <h2 className="text-lg font-semibold text-white">Verified Hotspot Locations</h2>
          <p className="text-sm text-gray-500">
            Only records/hotspots with reliable coordinates are shown. Incidents without coordinates are not placed on the map.
          </p>
        </div>
        <div className="p-4">
          <HotspotMap markers={markers} heightClass="h-[500px] w-full sm:h-[600px]" />
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
              <p className="text-lg font-bold text-red-400">{highCount}</p>
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
              <p className="text-lg font-bold text-yellow-400">{mediumCount}</p>
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
              <p className="text-lg font-bold text-green-400">{lowCount}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default InteractiveMap