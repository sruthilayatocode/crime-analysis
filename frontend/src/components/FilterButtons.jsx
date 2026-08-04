const filters = [
  { key: 'All', label: 'All' },
  { key: 'High', label: 'High' },
  { key: 'Medium', label: 'Medium' },
  { key: 'Low', label: 'Low' },
]

function FilterButtons({ activeFilter, onFilterChange }) {
  return (
    <div className="flex flex-wrap gap-2">
      {filters.map((filter) => {
        const isActive = activeFilter === filter.key
        const activeStyles = {
          All: 'bg-blue-600 text-white',
          High: 'bg-red-600 text-white',
          Medium: 'bg-yellow-600 text-white',
          Low: 'bg-green-600 text-white',
        }
        return (
          <button
            key={filter.key}
            onClick={() => onFilterChange(filter.key)}
            className={`rounded-lg px-4 py-2 text-sm font-medium transition-all ${
              isActive
                ? activeStyles[filter.key]
                : 'bg-gray-800 text-gray-400 hover:bg-gray-700 hover:text-white'
            }`}
          >
            {filter.label}
          </button>
        )
      })}
    </div>
  )
}

export default FilterButtons