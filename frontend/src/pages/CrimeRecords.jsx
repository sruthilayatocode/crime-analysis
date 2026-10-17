import { useEffect, useState, useMemo, useCallback } from 'react'
import PageHeader from '../components/PageHeader'
import Card from '../components/Card'
import CardHeader from '../components/CardHeader'
import StatusBadge from '../components/StatusBadge'
import SearchBar from '../components/SearchBar'
import FilterButtons from '../components/FilterButtons'
import Pagination from '../components/Pagination'
import { getAllCrimes } from '../services/api'

const ITEMS_PER_PAGE = 10

function CrimeRecords() {
  const [crimes, setCrimes] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [searchTerm, setSearchTerm] = useState('')
  const [severityFilter, setSeverityFilter] = useState('All')
  const [statusFilter, setStatusFilter] = useState('APPROVED')
  const [currentPage, setCurrentPage] = useState(1)

  const loadCrimes = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const res = await getAllCrimes(statusFilter)
      setCrimes(res.data || [])
      setCurrentPage(1)
    } catch (err) {
      setError(err.message || 'Failed to fetch crime records.')
    } finally {
      setLoading(false)
    }
  }, [statusFilter])

  useEffect(() => {
    loadCrimes()
  }, [loadCrimes])

  const filtered = useMemo(() => {
    let result = crimes

    if (severityFilter !== 'All') {
      result = result.filter(
        (c) => (c.severity || '').toLowerCase() === severityFilter.toLowerCase()
      )
    }

    if (searchTerm) {
      const term = searchTerm.toLowerCase()
      result = result.filter(
        (c) =>
          c.crime_type?.toLowerCase().includes(term) ||
          c.location_name?.toLowerCase().includes(term) ||
          c.description?.toLowerCase().includes(term)
      )
    }

    return result
  }, [crimes, severityFilter, searchTerm])

  const totalPages = Math.max(1, Math.ceil(filtered.length / ITEMS_PER_PAGE))
  const paginated = filtered.slice(
    (currentPage - 1) * ITEMS_PER_PAGE,
    currentPage * ITEMS_PER_PAGE
  )

  const geocodedCount = crimes.filter((c) => c.latitude && c.longitude).length

  return (
    <div className="space-y-6">
      <PageHeader
        title="Crime Records"
        description="Comprehensive repository of verified crime incidents in the Vellore jurisdiction."
        badge={
          <div className="flex items-center gap-3">
            <div className="rounded-lg bg-gray-800/50 px-3 py-1.5 text-xs text-gray-300">
              Total Records: <strong className="text-white">{crimes.length}</strong>
            </div>
            <div className="rounded-lg bg-gray-800/50 px-3 py-1.5 text-xs text-blue-400">
              GPS Verified: <strong className="text-white">{geocodedCount}</strong>
            </div>
          </div>
        }
      />

      <Card>
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div className="w-full lg:max-w-md">
            <SearchBar
              value={searchTerm}
              onChange={(val) => {
                setSearchTerm(val)
                setCurrentPage(1)
              }}
              placeholder="Search by crime type, locality, or description..."
            />
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <div className="flex items-center gap-1 rounded-lg border border-gray-800 bg-gray-950/60 p-1 text-xs">
              <span className="px-2 text-gray-500">Status:</span>
              {['APPROVED', 'PENDING', 'ALL'].map((st) => (
                <button
                  key={st}
                  onClick={() => setStatusFilter(st)}
                  className={`rounded-md px-2.5 py-1 font-medium transition-colors ${
                    statusFilter === st
                      ? 'bg-blue-600 text-white'
                      : 'text-gray-400 hover:text-white'
                  }`}
                >
                  {st}
                </button>
              ))}
            </div>

            <FilterButtons
              activeFilter={severityFilter}
              onFilterChange={(f) => {
                setSeverityFilter(f)
                setCurrentPage(1)
              }}
              filters={['All', 'Critical', 'High', 'Medium', 'Low']}
            />
          </div>
        </div>

        <div className="mt-4 flex items-center justify-between text-xs text-gray-500">
          <span>
            Showing <strong className="text-gray-300">{paginated.length}</strong> of{' '}
            <strong className="text-gray-300">{filtered.length}</strong> matching records
          </span>
          <button
            onClick={loadCrimes}
            className="text-blue-400 hover:text-blue-300"
          >
            Refresh records
          </button>
        </div>
      </Card>

      <Card>
        <CardHeader
          title="Incident Registry"
          subtitle="Real historical news data and approved citizen submissions"
          icon="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"
        />

        {error && (
          <div className="mb-4 rounded-lg border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-400">
            {error}
          </div>
        )}

        {loading ? (
          <p className="py-12 text-center text-sm text-gray-500">Loading crime records...</p>
        ) : filtered.length === 0 ? (
          <p className="py-12 text-center text-sm text-gray-500">No records match your filters.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-gray-300">
              <thead className="border-b border-gray-800 bg-gray-950/40 text-xs uppercase text-gray-500">
                <tr>
                  <th className="px-4 py-3">ID</th>
                  <th className="px-4 py-3">Crime Type</th>
                  <th className="px-4 py-3">Locality</th>
                  <th className="px-4 py-3">Date</th>
                  <th className="px-4 py-3">Severity</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">GPS Coordinates</th>
                  <th className="px-4 py-3">Description</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-800/60 font-normal">
                {paginated.map((crime) => (
                  <tr key={crime.id} className="transition-colors hover:bg-gray-800/30">
                    <td className="px-4 py-3 font-mono text-xs text-gray-500">#{crime.id}</td>
                    <td className="px-4 py-3 font-medium text-white">{crime.crime_type}</td>
                    <td className="px-4 py-3 text-gray-300">{crime.location_name || 'Vellore'}</td>
                    <td className="px-4 py-3 text-xs text-gray-400">{crime.crime_date || '-'}</td>
                    <td className="px-4 py-3">
                      <StatusBadge status={crime.severity || 'Medium'} />
                    </td>
                    <td className="px-4 py-3">
                      <StatusBadge status={crime.status || 'APPROVED'} />
                    </td>
                    <td className="px-4 py-3 font-mono text-xs">
                      {crime.latitude && crime.longitude ? (
                        <span className="text-blue-400">
                          {crime.latitude.toFixed(4)}, {crime.longitude.toFixed(4)}
                        </span>
                      ) : (
                        <span className="text-gray-600">District level</span>
                      )}
                    </td>
                    <td className="max-w-xs truncate px-4 py-3 text-xs text-gray-400" title={crime.description}>
                      {crime.description}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {filtered.length > ITEMS_PER_PAGE && (
          <div className="mt-6">
            <Pagination
              currentPage={currentPage}
              totalPages={totalPages}
              onPageChange={setCurrentPage}
            />
          </div>
        )}
      </Card>
    </div>
  )
}

export default CrimeRecords
