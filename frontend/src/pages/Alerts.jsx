import { useEffect, useState, useMemo, useCallback } from 'react'
import AlertSummaryCard from '../components/AlertSummaryCard'
import AlertItem from '../components/AlertItem'
import AlertHistoryTable from '../components/AlertHistoryTable'
import EmergencyTipsCard from '../components/EmergencyTipsCard'
import EmptyState from '../components/EmptyState'
import FilterButtons from '../components/FilterButtons'
import PageHeader from '../components/PageHeader'
import Card from '../components/Card'
import { getAllCrimes, getHotspots } from '../services/api'

const EMERGENCY_TIPS = [
  'In any active emergency or imminent threat, immediately dial 112 (National Emergency Helpline).',
  'For police assistance in Tamil Nadu, dial 100 or the local Vellore Control Room.',
  'For medical or ambulance emergency, call 108 without delay.',
  'Women Safety Helpline: Call 1091 for immediate assistance.',
  'Avoid poorly lit corridors and isolated transit routes during late hours in identified hotspot zones.',
  'Report suspicious activities or witnessed offenses using the CrimeSense incident report tool.',
]

function Alerts() {
  const [activeFilter, setActiveFilter] = useState('All')
  const [crimes, setCrimes] = useState([])
  const [hotspots, setHotspots] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const loadAlerts = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const [crimesRes, hotspotsRes] = await Promise.all([
        getAllCrimes('APPROVED').catch(() => ({ data: [] })),
        getHotspots().catch(() => ({ data: [] })),
      ])
      setCrimes(crimesRes?.data || [])
      setHotspots(hotspotsRes?.data || [])
    } catch (err) {
      setError(err.message || 'Unable to load real-time alerts.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadAlerts()
  }, [loadAlerts])

  // Generate dynamic, genuine alert notifications from real database records
  const alerts = useMemo(() => {
    const list = []

    // 1. Hotspot cluster advisories
    hotspots.forEach((spot, idx) => {
      const risk = spot.risk_level || spot.risk || 'Medium'
      const name = spot.location || spot.zone || 'Vellore Area'
      const count = spot.crime_count || spot.crimeCount || 0

      list.push({
        id: `HS-${idx + 1}`,
        title: `${risk} Risk Zone: ${name}`,
        description: `Active DBSCAN crime cluster with ${count} verified incident${count === 1 ? '' : 's'} recorded. Stay alert in this area.`,
        time: 'Active Cluster',
        location: name,
        priority: risk === 'High' ? 'High' : risk === 'Medium' ? 'Medium' : 'Low',
      })
    })

    // 2. High and critical verified incident alerts
    crimes.forEach((crime) => {
      const severity = crime.severity || 'Medium'
      if (severity === 'Critical' || severity === 'High' || severity === 'Medium') {
        list.push({
          id: `CR-${crime.id}`,
          title: `${severity} Priority Incident: ${crime.crime_type}`,
          description: crime.description || `Verified ${crime.crime_type} report registered in ${crime.location_name || 'Vellore'}.`,
          time: crime.crime_date || 'Recent',
          location: crime.location_name || 'Vellore',
          priority: severity === 'Critical' || severity === 'High' ? 'High' : 'Medium',
        })
      }
    })

    return list
  }, [hotspots, crimes])

  const filteredAlerts = useMemo(() => {
    if (activeFilter === 'All') return alerts
    return alerts.filter((alert) => alert.priority === activeFilter)
  }, [alerts, activeFilter])

  const summary = useMemo(() => {
    return {
      total: alerts.length,
      high: alerts.filter((a) => a.priority === 'High').length,
      medium: alerts.filter((a) => a.priority === 'Medium').length,
      low: alerts.filter((a) => a.priority === 'Low').length,
    }
  }, [alerts])

  const history = useMemo(() => {
    return crimes.slice(0, 8).map((c) => ({
      id: `CR-${c.id}`,
      location: c.location_name || 'Vellore',
      crimeType: c.crime_type,
      time: c.crime_date || '-',
      status: c.status || 'APPROVED',
    }))
  }, [crimes])

  return (
    <div className="space-y-6">
      <PageHeader
        title="Safety Advisories & Crime Alerts"
        description="Verified security notifications derived from active DBSCAN hotspots and severe incidents in Vellore."
        badge={
          <div className="flex items-center gap-3">
            <span className="flex h-2.5 w-2.5 relative">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-red-500" />
            </span>
            <span className="text-sm font-semibold text-red-400">
              {summary.high} High-Priority Advisories
            </span>
            <button
              onClick={loadAlerts}
              className="rounded-lg bg-gray-800 px-3 py-1.5 text-xs text-gray-300 hover:bg-gray-700"
            >
              Refresh
            </button>
          </div>
        }
      />

      {error && (
        <div className="rounded-lg border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-400">
          {error}
        </div>
      )}

      {/* Alert Summary Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <AlertSummaryCard type="total" label="Total Active Advisories" value={summary.total} />
        <AlertSummaryCard type="high" label="High Priority" value={summary.high} />
        <AlertSummaryCard type="medium" label="Medium Priority" value={summary.medium} />
        <AlertSummaryCard type="low" label="Low Priority" value={summary.low} />
      </div>

      {/* Filters and Recent Alerts */}
      <Card>
        <div className="mb-4 flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <h2 className="text-lg font-bold text-white">Security Advisories</h2>
            <p className="text-xs text-gray-400">
              Generated from verified police records and approved citizen reports
            </p>
          </div>
          <FilterButtons
            activeFilter={activeFilter}
            onFilterChange={setActiveFilter}
            filters={['All', 'High', 'Medium', 'Low']}
          />
        </div>

        {loading ? (
          <div className="py-12 text-center text-sm text-gray-500">Loading safety advisories...</div>
        ) : filteredAlerts.length > 0 ? (
          <div className="grid grid-cols-1 gap-3 xl:grid-cols-2">
            {filteredAlerts.map((alert) => (
              <AlertItem key={alert.id} alert={alert} />
            ))}
          </div>
        ) : (
          <EmptyState
            title="No alerts found"
            message={`There are no ${activeFilter === 'All' ? '' : activeFilter.toLowerCase() + ' priority '}alerts matching your filter.`}
          />
        )}
      </Card>

      {/* Alert History and Emergency Tips */}
      <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
        <div className="xl:col-span-2">
          <AlertHistoryTable history={history} />
        </div>
        <EmergencyTipsCard tips={EMERGENCY_TIPS} />
      </div>
    </div>
  )
}

export default Alerts