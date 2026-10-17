import { useEffect, useState, useCallback } from 'react'
import PageHeader from '../components/PageHeader'
import Card from '../components/Card'
import CardHeader from '../components/CardHeader'
import StatusBadge from '../components/StatusBadge'
import EmptyState from '../components/EmptyState'
import { useAuth } from '../hooks/useAuth'
import { getPendingReports, approveCrimeReport, rejectCrimeReport } from '../services/api'

function PendingApprovals() {
  const { token } = useAuth()
  const [pending, setPending] = useState([])
  const [loading, setLoading] = useState(true)
  const [actionLoadingId, setActionLoadingId] = useState(null)
  const [adminNotes, setAdminNotes] = useState({})
  const [error, setError] = useState('')
  const [successMessage, setSuccessMessage] = useState('')

  const loadPending = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const res = await getPendingReports(token)
      setPending(res.data || [])
    } catch (err) {
      setError(err.message || 'Unable to load pending crime reports.')
    } finally {
      setLoading(false)
    }
  }, [token])

  useEffect(() => {
    loadPending()
  }, [loadPending])

  const handleNotesChange = (id, text) => {
    setAdminNotes((prev) => ({ ...prev, [id]: text }))
  }

  const handleApprove = async (id) => {
    setActionLoadingId(id)
    setError('')
    setSuccessMessage('')
    try {
      const notes = adminNotes[id] || ''
      await approveCrimeReport(id, notes, token)
      setSuccessMessage(`Crime report #${id} approved and added to active database.`)
      setPending((prev) => prev.filter((item) => item.id !== id))
    } catch (err) {
      setError(err.message || `Failed to approve report #${id}.`)
    } finally {
      setActionLoadingId(null)
    }
  }

  const handleReject = async (id) => {
    setActionLoadingId(id)
    setError('')
    setSuccessMessage('')
    try {
      const notes = adminNotes[id] || ''
      await rejectCrimeReport(id, notes, token)
      setSuccessMessage(`Crime report #${id} rejected.`)
      setPending((prev) => prev.filter((item) => item.id !== id))
    } catch (err) {
      setError(err.message || `Failed to reject report #${id}.`)
    } finally {
      setActionLoadingId(null)
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Pending Incident Approvals"
        description="Review, verify, and triage citizen-submitted crime reports before they enter hotspot analytics."
        badge={
          <div className="flex items-center gap-2">
            <span className="flex h-2.5 w-2.5 rounded-full bg-yellow-400 animate-pulse" />
            <span className="text-sm font-medium text-yellow-400">
              {pending.length} Report(s) Awaiting Review
            </span>
          </div>
        }
      />

      {error && (
        <div className="rounded-lg border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-400">
          {error}
        </div>
      )}

      {successMessage && (
        <div className="rounded-lg border border-green-500/30 bg-green-500/10 p-4 text-sm text-green-400">
          {successMessage}
        </div>
      )}

      <Card>
        <CardHeader
          title="Verification Queue"
          subtitle="Carefully inspect coordinates and incident credibility before approving"
          icon="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
          action={
            <button
              onClick={loadPending}
              className="rounded-lg bg-gray-800 px-3 py-1.5 text-xs font-medium text-gray-300 hover:bg-gray-700"
            >
              Refresh Queue
            </button>
          }
        />

        {loading ? (
          <p className="py-12 text-center text-sm text-gray-500">Loading pending reports...</p>
        ) : pending.length === 0 ? (
          <EmptyState
            title="Queue is empty"
            message="There are no pending incident reports awaiting administrative review."
          />
        ) : (
          <div className="space-y-6">
            {pending.map((report) => (
              <div
                key={report.id}
                className="rounded-xl border border-gray-800 bg-gray-900/60 p-5 transition-colors hover:border-gray-700"
              >
                <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-start">
                  <div>
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="font-mono text-xs text-gray-500">#{report.id}</span>
                      <h3 className="text-base font-bold text-white">{report.crime_type}</h3>
                      <StatusBadge status="Pending" />
                      <span className="rounded bg-gray-800 px-2 py-0.5 text-xs text-yellow-400">
                        Severity: {report.severity || 'Medium'}
                      </span>
                    </div>

                    <p className="mt-2 text-sm text-gray-300">{report.description}</p>

                    <div className="mt-3 flex flex-wrap gap-4 text-xs text-gray-400">
                      <span>
                        Area: <strong className="text-gray-200">{report.location_name || 'Vellore'}</strong>
                      </span>
                      {report.latitude && report.longitude ? (
                        <span>
                          Coordinates: <strong className="text-blue-400">{report.latitude}, {report.longitude}</strong>
                        </span>
                      ) : (
                        <span className="text-gray-500">No exact GPS coordinates</span>
                      )}
                      <span>
                        Incident Date: <strong className="text-gray-200">{report.crime_date || '-'}</strong>
                      </span>
                      <span>
                        Reported By: <strong className="text-gray-200">{report.reported_by_name || `User #${report.reported_by_id}`}</strong>
                      </span>
                      <span>
                        Submitted At: <strong className="text-gray-200">{report.created_at ? report.created_at.slice(0, 16).replace('T', ' ') : '-'}</strong>
                      </span>
                    </div>
                  </div>
                </div>

                <div className="mt-4 border-t border-gray-800 pt-4">
                  <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
                    <div className="flex-1">
                      <input
                        type="text"
                        placeholder="Optional administrative review notes or verification reference..."
                        value={adminNotes[report.id] || ''}
                        onChange={(e) => handleNotesChange(report.id, e.target.value)}
                        className="w-full rounded-lg border border-gray-800 bg-gray-950/80 px-3 py-2 text-xs text-gray-200 placeholder-gray-600 outline-none focus:border-blue-500"
                      />
                    </div>
                    <div className="flex items-center gap-2">
                      <button
                        type="button"
                        disabled={actionLoadingId === report.id}
                        onClick={() => handleApprove(report.id)}
                        className="rounded-lg bg-green-600 px-4 py-2 text-xs font-semibold text-white transition-colors hover:bg-green-700 disabled:opacity-50"
                      >
                        {actionLoadingId === report.id ? 'Processing...' : 'Approve Report'}
                      </button>
                      <button
                        type="button"
                        disabled={actionLoadingId === report.id}
                        onClick={() => handleReject(report.id)}
                        className="rounded-lg bg-red-600/20 border border-red-500/30 px-4 py-2 text-xs font-semibold text-red-400 transition-colors hover:bg-red-600/30 disabled:opacity-50"
                      >
                        {actionLoadingId === report.id ? 'Processing...' : 'Reject'}
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  )
}

export default PendingApprovals
