import { useEffect, useMemo, useState, useCallback } from 'react'
import SearchBar from '../components/SearchBar'
import FilterButtons from '../components/FilterButtons'
import HotspotsTable from '../components/HotspotsTable'
import Pagination from '../components/Pagination'
import PageHeader from '../components/PageHeader'
import Card from '../components/Card'
import EmptyState from '../components/EmptyState'
import { getHotspots } from '../services/api'

const ITEMS_PER_PAGE = 8

function CrimeHotspots() {
  const [hotspots, setHotspots] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [searchTerm, setSearchTerm] = useState('')
  const [activeFilter, setActiveFilter] = useState('All')
  const [currentPage, setCurrentPage] = useState(1)

  const fetchHotspots = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const res = await getHotspots()
      setHotspots(res.data || [])
    } catch (err) {
      setError(err.message || 'Unable to load crime hotspot analytics from server.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchHotspots()
  }, [fetchHotspots])

  const filteredHotspots = useMemo(() => {
    let result = hotspots

    if (activeFilter !== 'All') {
      result = result.filter(
        (spot) => (spot.risk_level || spot.risk || '').toLowerCase() === activeFilter.toLowerCase()
      )
    }

    if (searchTerm) {
      const term = searchTerm.toLowerCase()
      result = result.filter((spot) => {
        const name = (spot.location || spot.zone || '').toLowerCase()
        const incidents = String(spot.crime_count || spot.crimeCount || '')
        return name.includes(term) || incidents.includes(term)
      })
    }

    return result
  }, [hotspots, searchTerm, activeFilter])

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

  const highRiskCount = hotspots.filter(
    (h) => (h.risk_level || h.risk || '').toLowerCase() === 'high'
  ).length

  return (
    <div className="space-y-6">
      <PageHeader
        title="Crime Hotspots"
        description="Geographic crime clusters and high-risk zones detected across verified records."
        badge={
          <div className="flex items-center gap-3">
            <div className="rounded-lg bg-gray-800/50 px-3.5 py-1.5 border border-gray-800">
              <p className="text-[10px] uppercase font-semibold text-gray-500">Total Zones</p>
              <p className="text-sm font-bold text-gray-200">{hotspots.length}</p>
            </div>
            <div className="rounded-lg bg-red-500/10 px-3.5 py-1.5 border border-red-500/20">
              <p className="text-[10px] uppercase font-semibold text-red-400">High Risk</p>
              <p className="text-sm font-bold text-red-400">{highRiskCount}</p>
            </div>
          </div>
        }
      />

      {error && (
        <div className="rounded-lg border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-400 flex items-center justify-between">
          <span>{error}</span>
          <button
            onClick={fetchHotspots}
            className="rounded bg-red-500/20 px-3 py-1 text-xs font-semibold text-red-300 hover:bg-red-500/30"
          >
            Retry
          </button>
        </div>
      )}

      {/* Search and Filters */}
      <Card>
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div className="w-full lg:max-w-md">
            <SearchBar
              value={searchTerm}
              onChange={handleSearch}
              placeholder="Search hotspots by locality or zone..."
            />
          </div>
          <FilterButtons
            activeFilter={activeFilter}
            onFilterChange={handleFilterChange}
            filters={['All', 'High', 'Medium', 'Low']}
          />
        </div>

        {/* Results count */}
        <div className="mt-4 flex items-center justify-between text-xs sm:text-sm text-gray-400">
          <span>
            Showing <strong className="text-gray-200">{currentItems.length}</strong> of{' '}
            <strong className="text-gray-200">{filteredHotspots.length}</strong> hotspot zones
          </span>
          <div className="flex items-center gap-3">
            {activeFilter !== 'All' && (
              <button
                onClick={() => handleFilterChange('All')}
                className="text-blue-400 hover:text-blue-300 text-xs font-medium"
              >
                Clear filter
              </button>
            )}
            <button
              onClick={fetchHotspots}
              className="text-gray-400 hover:text-gray-200 text-xs font-medium flex items-center gap-1"
            >
              <svg className="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              Refresh
            </button>
          </div>
        </div>
      </Card>

      {/* Table */}
      <Card>
        {loading ? (
          <div className="py-16 text-center">
            <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-blue-500 border-r-transparent" />
            <p className="mt-3 text-sm text-gray-400">Analyzing crime hotspot clusters...</p>
          </div>
        ) : filteredHotspots.length === 0 ? (
          <EmptyState
            title="No hotspots found"
            message={
              searchTerm || activeFilter !== 'All'
                ? 'No hotspot zones match your current search or filter criteria.'
                : 'No geographic crime hotspots have been detected from verified coordinates yet.'
            }
          />
        ) : (
          <>
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
          </>
        )}
      </Card>
    </div>
  )
}

export default CrimeHotspots