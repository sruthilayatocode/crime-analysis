import { useEffect, useState, useCallback } from 'react'
import { Link } from 'react-router-dom'
import PageHeader from '../components/PageHeader'
import Card from '../components/Card'
import CardHeader from '../components/CardHeader'
import StatusBadge from '../components/StatusBadge'
import EmptyState from '../components/EmptyState'
import { useAuth } from '../hooks/useAuth'
import { getMyReports } from '../services/api'

function MyReports() {
  const { token, user } = useAuth()
  const [reports, setReports] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const loadReports = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const res = await getMyReports(token)
      setReports(res.data || [])
    } catch (err) {
      setError(err.message || 'Unable to load your crime reports.')
    } finally {
      setLoading(false)
    }
  }, [token])

  useEffect(() => {
    loadReports()
  }, [loadReports])

  const pendingCount = reports.filter((r) => r.status === 'PENDING').length
  const approvedCount = reports.filter((r) => r.status === 'APPROVED').length
  const rejectedCount = reports.filter((r) => r.status === 'REJECTED').length

  return (
    <div className="space-y-6">
      <PageHeader
        title="My Submitted Reports"
        description="Track the verification status of crime incidents you have reported."
        badge={
          <Link
            to="/report-crime"
            className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-700"
          >
            + Report New Incident
          </Link>
        }
      />

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div className="rounded-xl border border-gray-800 bg-gray-900/50 p-4">
          <p className="text-xs text-gray-500">Pending Review</p>
          <p className="mt-1 text-2xl font-bold text-yellow-400">{pendingCount}</p>
        </div>
        <div className="rounded-xl border border-gray-800 bg-gray-900/50 p-4">
          <p className="text-xs text-gray-500">Approved & Active</p>
          <p className="mt-1 text-2xl font-bold text-green-400">{approvedCount}</p>
        </div>
        <div className="rounded-xl border border-gray-800 bg-gray-900/50 p-4">
          <p className="text-xs text-gray-500">Rejected</p>
          <p className="mt-1 text-2xl font-bold text-red-400">{rejectedCount}</p>
        </div>
      </div>

      <Card>
        <CardHeader
          title="Submitted Reports"
          subtitle={`Showing all ${reports.length} report(s) submitted by ${user?.name || 'you'}`}
          icon="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
          action={
            <button
              onClick={loadReports}
              className="rounded-lg bg-gray-800 px-3 py-1.5 text-xs font-medium text-gray-300 hover:bg-gray-700"
            >
              Refresh
            </button>
          }
        />

        {error && (
          <div className="mb-4 rounded-lg border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-400">
            {error}
          </div>
        )}

        {loading ? (
          <p className="py-12 text-center text-sm text-gray-500">Loading your reports...</p>
        ) : reports.length === 0 ? (
          <EmptyState
            title="No reports submitted yet"
            message="You haven't submitted any crime reports yet. Help keep the community safe by reporting incidents."
            action={
              <Link
                to="/report-crime"
                className="mt-4 inline-block rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
              >
                Submit First Report
              </Link>
            }
          />
        ) : (
          <div className="divide-y divide-gray-800">
            {reports.map((report) => (
              <div key={report.id} className="py-4 first:pt-0 last:pb-0">
                <div className="flex flex-col justify-between gap-2 sm:flex-row sm:items-center">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs text-gray-500">#{report.id}</span>
                      <span className="text-base font-semibold text-gray-200">
                        {report.crime_type}
                      </span>
                      <StatusBadge status={report.status} />
                      <span className="rounded bg-gray-800 px-2 py-0.5 text-[11px] text-gray-400">
                        Severity: {report.severity || 'Medium'}
                      </span>
                    </div>
                    <p className="text-sm text-gray-400">{report.description}</p>
                    <div className="flex flex-wrap gap-4 text-xs text-gray-500">
                      <span>Location: <strong className="text-gray-300">{report.location_name || 'Vellore'}</strong></span>
                      {report.latitude && report.longitude && (
                        <span>GPS: <strong className="text-gray-300">{report.latitude}, {report.longitude}</strong></span>
                      )}
                      <span>Date of incident: <strong className="text-gray-300">{report.crime_date || '-'}</strong></span>
                      <span>Submitted: <strong className="text-gray-300">{report.created_at ? report.created_at.slice(0, 10) : '-'}</strong></span>
                    </div>
                  </div>
                </div>

                {report.admin_notes && (
                  <div className="mt-3 rounded-lg border border-gray-800 bg-gray-950/60 p-3 text-xs">
                    <p className="font-medium text-gray-400">Admin Review Notes:</p>
                    <p className="mt-0.5 text-gray-300">{report.admin_notes}</p>
                    {report.reviewed_at && (
                      <p className="mt-1 text-[11px] text-gray-500">
                        Reviewed on {report.reviewed_at.slice(0, 10)} by {report.reviewed_by_name || 'Administrator'}
                      </p>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  )
}

export default MyReports
