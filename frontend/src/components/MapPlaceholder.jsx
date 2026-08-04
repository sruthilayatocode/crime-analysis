import Card from './Card'
import CardHeader from './CardHeader'

function MapPlaceholder() {
  return (
    <Card>
      <CardHeader
        title="Interactive Map"
        subtitle="Crime hotspot visualization"
        action={
          <div className="flex gap-2">
            <button className="rounded-lg bg-gray-800 px-3 py-1.5 text-xs font-medium text-gray-400 hover:text-white">
              Satellite
            </button>
            <button className="rounded-lg bg-blue-600 px-3 py-1.5 text-xs font-medium text-white">
              Heatmap
            </button>
          </div>
        }
      />

      <div className="relative flex h-64 items-center justify-center overflow-hidden rounded-lg border border-gray-800 bg-gradient-to-br from-gray-900 via-blue-950 to-gray-900 sm:h-72">
        {/* Grid lines */}
        <div className="absolute inset-0 opacity-20" style={{
          backgroundImage: 'linear-gradient(rgba(59,130,246,0.3) 1px, transparent 1px), linear-gradient(90deg, rgba(59,130,246,0.3) 1px, transparent 1px)',
          backgroundSize: '40px 40px',
        }} />

        {/* Heat spots */}
        <div className="absolute left-1/4 top-1/3 h-24 w-24 rounded-full bg-red-500/30 blur-2xl" />
        <div className="absolute left-1/2 top-1/2 h-32 w-32 rounded-full bg-orange-500/25 blur-2xl" />
        <div className="absolute left-3/4 top-1/4 h-20 w-20 rounded-full bg-yellow-500/20 blur-2xl" />
        <div className="absolute left-1/3 top-2/3 h-16 w-16 rounded-full bg-blue-500/20 blur-2xl" />

        {/* Center content */}
        <div className="relative z-10 text-center">
          <svg className="mx-auto mb-3 h-12 w-12 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
          </svg>
          <p className="text-sm font-medium text-gray-300">Map visualization coming soon</p>
          <p className="mt-1 text-xs text-gray-500">Interactive crime hotspot map will be displayed here</p>
        </div>

        {/* Legend */}
        <div className="absolute bottom-3 left-3 z-10 flex items-center gap-3 rounded-lg bg-gray-900/80 px-3 py-2 text-xs text-gray-400">
          <span className="flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-red-500" /> High
          </span>
          <span className="flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-yellow-500" /> Medium
          </span>
          <span className="flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-green-500" /> Low
          </span>
        </div>
      </div>
    </Card>
  )
}

export default MapPlaceholder