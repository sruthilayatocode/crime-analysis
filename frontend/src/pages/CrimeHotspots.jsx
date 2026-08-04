import { useMemo, useState } from 'react'
import SearchBar from '../components/SearchBar'
import FilterButtons from '../components/FilterButtons'
import HotspotsTable from '../components/HotspotsTable'
import Pagination from '../components/Pagination'
import PageHeader from '../components/PageHeader'
import Card from '../components/Card'
import { hotspots } from '../data/hotspotsData'

const ITEMS_PER_PAGE = 8

function CrimeHotspots() {
  const [searchTerm, setSearchTerm] = useState('')
  const [activeFilter, setActiveFilter] = useState('All')
  const [currentPage, setCurrentPage] = useState(1)

  const filteredHotspots = useMemo(() => {
    let result = hotspots

    if (activeFilter !== 'All') {
      result = result.filter((spot) => spot.risk === activeFilter)
    }

    if (searchTerm) {
      const term = searchTerm.toLowerCase()
      result = result.filter(
        (spot) =>
          spot.zone.toLowerCase().includes(term) ||
          spot.region.toLowerCase().includes(term) ||
          spot.incidents.toLowerCase().includes(term)
      )
    }

    return result
  }, [searchTerm, activeFilter])

  const totalPages = Math.max(1, Math.ceil(filteredHotspots.length / ITEMS_PER_PAGE))
  const currentItems = filteredHotspots.slice(
    (currentPage - 1) * ITEMS_PER_PAGE,
    currentPage * ITEMS_PER_PAGE
  )

  const handleSearch = (value) => {
    setSearchTerm(value)
    setCurrentPage(1)
  }

  const handleFilterChange = (filter) => {
    setActiveFilter(filter)
    setCurrentPage(1)
  }

  const handlePageChange = (page) => {
    if (page >= 1 && page <= totalPages) {
      setCurrentPage(page)
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Crime Hotspots"
        description="Monitor high-risk areas detected by the AI analysis system."
        badge={
          <div className="flex items-center gap-3">
            <div className="rounded-lg bg-gray-800/50 px-4 py-2">
              <p className="text-xs text-gray-500">Total Zones</p>
              <p className="text-sm font-medium text-gray-300">{hotspots.length}</p>
            </div>
            <div className="rounded-lg bg-gray-800/50 px-4 py-2">
              <p className="text-xs text-gray-500">High Risk</p>
              <p className="text-sm font-medium text-red-400">
                {hotspots.filter((h) => h.risk === 'High').length}
              </p>
            </div>
          </div>
        }
      />

      {/* Search and Filters */}
      <Card>
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div className="w-full lg:max-w-md">
            <SearchBar
              value={searchTerm}
              onChange={handleSearch}
              placeholder="Search hotspots by zone, region, or incident type..."
            />
          </div>
          <FilterButtons
            activeFilter={activeFilter}
            onFilterChange={handleFilterChange}
          />
        </div>

        {/* Results count */}
        <div className="mt-4 flex items-center justify-between text-sm text-gray-500">
          <span>
            Showing <span className="font-medium text-gray-300">{currentItems.length}</span> of{' '}
            <span className="font-medium text-gray-300">{filteredHotspots.length}</span> hotspots
          </span>
          {activeFilter !== 'All' && (
            <button
              onClick={() => handleFilterChange('All')}
              className="text-blue-400 hover:text-blue-300"
            >
              Clear filter
            </button>
          )}
        </div>
      </Card>

      {/* Table */}
      <Card>
        <HotspotsTable hotspots={currentItems} />

        {filteredHotspots.length > ITEMS_PER_PAGE && (
          <div className="mt-6">
            <Pagination
              currentPage={currentPage}
              totalPages={totalPages}
              onPageChange={handlePageChange}
            />
          </div>
        )}
      </Card>
    </div>
  )
}

export default CrimeHotspots