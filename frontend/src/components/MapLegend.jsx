function MapLegend() {
  return (
    <div className="rounded-lg border border-gray-800 bg-gray-900/90 p-3 text-xs text-gray-400">
      <p className="mb-2 font-medium text-gray-300">Legend</p>
      <div className="space-y-1.5">
        <span className="flex items-center gap-2">
          <span className="h-3 w-3 rounded-full bg-red-500" /> High Risk
        </span>
        <span className="flex items-center gap-2">
          <span className="h-3 w-3 rounded-full bg-yellow-500" /> Medium Risk
        </span>
        <span className="flex items-center gap-2">
          <span className="h-3 w-3 rounded-full bg-green-500" /> Low Risk
        </span>
        <span className="flex items-center gap-2">
          <span className="h-3 w-3 rounded-full bg-blue-500" /> Your Location
        </span>
      </div>
    </div>
  )
}

export default MapLegend