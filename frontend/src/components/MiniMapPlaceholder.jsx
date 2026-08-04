import Card from './Card'
import CardHeader from './CardHeader'

function MiniMapPlaceholder({ location }) {
  return (
    <Card>
      <CardHeader
        title="Location Map"
        subtitle="Your position on the map"
        action={
          <span className="rounded-lg bg-blue-600 px-3 py-1.5 text-xs font-medium text-white">
            Live
          </span>
        }
      />

      <div className="relative flex h-64 items-center justify-center overflow-hidden rounded-lg border border-gray-800 bg-gradient-to-br from-gray-900 via-blue-950 to-gray-900">
        {/* Grid lines */}
        <div className="absolute inset-0 opacity-20" style={{
          backgroundImage: 'linear-gradient(rgba(59,130,246,0.3) 1px, transparent 1px), linear-gradient(90deg, rgba(59,130,246,0.3) 1px, transparent 1px)',
          backgroundSize: '40px 40px',
        }} />

        {/* Heat blob */}
        <div className="absolute left-1/2 top-1/2 h-40 w-40 -translate-x-1/2 -translate-y-1/2 rounded-full bg-red-500/20 blur-3xl" />

        {/* User location marker with pulse */}
        <div className="relative flex items-center justify-center">
          <span className="absolute inline-flex h-12 w-12 animate-ping rounded-full bg-blue-500 opacity-30" />
          <span className="relative flex h-5 w-5 items-center justify-center rounded-full border-[3px] border-white bg-blue-500 shadow-lg">
            <span className="h-2 w-2 rounded-full bg-white/70" />
          </span>
        </div>

        {/* Coordinates overlay */}
        <div className="absolute bottom-3 left-3 rounded-lg bg-gray-900/80 px-3 py-2 font-mono text-xs text-gray-400">
          {location.latitude.toFixed(4)}, {location.longitude.toFixed(4)}
        </div>

        {/* Placeholder note */}
        <div className="absolute right-3 top-3 rounded-lg bg-gray-900/80 px-3 py-2 text-xs text-gray-500">
          Map integration coming soon
        </div>
      </div>
    </Card>
  )
}

export default MiniMapPlaceholder