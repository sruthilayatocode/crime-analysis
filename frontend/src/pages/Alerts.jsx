import { useMemo, useState } from 'react'
import AlertSummaryCard from '../components/AlertSummaryCard'
import AlertItem from '../components/AlertItem'
import AlertHistoryTable from '../components/AlertHistoryTable'
import EmergencyTipsCard from '../components/EmergencyTipsCard'
import EmptyState from '../components/EmptyState'
import FilterButtons from '../components/FilterButtons'
import PageHeader from '../components/PageHeader'
import Card from '../components/Card'
import { useCrimeData } from '../hooks/useCrimeData'
import { buildAlertSummary, deriveAlerts, deriveAlertHistory } from '../utils/crimeInsights'

// Static safety guidance (not crime data); kept for the emergency tips panel.
const emergencyTips = [
  'Stay in well-lit, populated areas, especially at night.',
  'Keep your phone charged and emergency contacts on speed dial.',
  'Avoid isolated routes; use main roads with more traffic.',
  'Report suspicious activity immediately to local authorities.',
  'Share your live location with trusted family or friends.',
]

function Alerts() {
  const { crimes, loading, error } = useCrimeData()
  const [activeFilter, setActiveFilter] = useState('All')

  const alertSummary = useMemo(() => buildAlertSummary(crimes), [crimes])
  const allAlerts = useMemo(() => deriveAlerts(crimes), [crimes])
  const alertHistory = useMemo(() => deriveAlertHistory(crimes), [crimes])

  const filteredAlerts = useMemo(() => {
    if (activeFilter === 'All') return allAlerts
    return allAlerts.filter((alert) => alert.priority === activeFilter)
  }, [allAlerts, activeFilter])

  return (
    <div className="space-y-6">
      <PageHeader
        title="Alerts"
        description="Safety alerts derived from validated crime incidents."
        badge={
          <div className="flex items-center gap-3">
            <span className="flex h-2 w-2">
              <span className="absolute inline-flex h-2 w-2 animate-ping rounded-full bg-red-400 opacity-75" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-red-500" />
            </span>
            <span className="text-sm font-medium text-red-400">{alertSummary.high} Active Alerts</span>
          </div>
        }
      />

      {loading && <p className="py-12 text-center text-sm text-gray-500">Loading alert data&hellip;</p>}
      {error && <p className="py-6 text-center text-sm text-gray-400">{error}</p>}

      {/* Alert Summary Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <AlertSummaryCard type="total" label="Total Incidents" value={alertSummary.total} />
        <AlertSummaryCard type="high" label="High Priority" value={alertSummary.high} />
        <AlertSummaryCard type="medium" label="Medium Priority" value={alertSummary.medium} />
        <AlertSummaryCard type="low" label="Low Priority" value={alertSummary.low} />
      </div>

      {/* Filters and Recent Alerts */}
      <Card>
        <div className="mb-4 flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <h2 className="text-lg font-semibold text-white">Recent Alerts</h2>
            <p className="text-sm text-gray-500">Derived from validated incidents</p>
          </div>
          <FilterButtons
            activeFilter={activeFilter}
            onFilterChange={setActiveFilter}
          />
        </div>

        {filteredAlerts.length > 0 ? (
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
          <AlertHistoryTable history={alertHistory} />
        </div>
        <EmergencyTipsCard tips={emergencyTips} />
      </div>
    </div>
  )
}

export default Alerts