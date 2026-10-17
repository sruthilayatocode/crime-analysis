import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import PageHeader from '../components/PageHeader'
import Card from '../components/Card'
import CardHeader from '../components/CardHeader'
import { useAuth } from '../hooks/useAuth'
import { reportCrime } from '../services/api'

const CRIME_TYPES = [
  'Theft',
  'Robbery',
  'Burglary',
  'Assault',
  'Murder',
  'Sexual Assault',
  'Fraud',
  'Cyber Crime',
  'Vehicle Theft',
  'Domestic Violence',
  'Chain Snatching',
  'Harassment',
  'Vandalism',
  'Other',
]

const SEVERITIES = ['Low', 'Medium', 'High', 'Critical']

const inputClass =
  'w-full rounded-lg border border-gray-800 bg-gray-950/60 px-3 py-2.5 text-sm text-gray-100 placeholder-gray-600 outline-none transition-colors focus:border-blue-500'

function ReportCrime() {
  const { token, user } = useAuth()
  const navigate = useNavigate()

  const [form, setForm] = useState({
    crime_type: 'Theft',
    severity: 'Medium',
    location_name: '',
    crime_date: new Date().toISOString().split('T')[0],
    latitude: '',
    longitude: '',
    description: '',
  })

  const [loading, setLoading] = useState(false)
  const [geoLoading, setGeoLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)

  const handleChange = (e) => {
    const { name, value } = e.target
    setForm((prev) => ({ ...prev, [name]: value }))
  }

  const handleGetLocation = () => {
    if (!navigator.geolocation) {
      setError('Geolocation is not supported by your browser.')
      return
    }

    setGeoLoading(true)
    setError('')

    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setForm((prev) => ({
          ...prev,
          latitude: pos.coords.latitude.toFixed(6),
          longitude: pos.coords.longitude.toFixed(6),
        }))
        setGeoLoading(false)
      },
      (err) => {
        setError(`Could not detect location: ${err.message}`)
        setGeoLoading(false)
      },
      { enableHighAccuracy: true, timeout: 10000 }
    )
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setSuccess(false)

    if (!form.crime_type || !form.location_name.trim() || !form.description.trim()) {
      setError('Please provide crime type, incident location, and a description.')
      return
    }

    setLoading(true)

    try {
      const payload = {
        crime_type: form.crime_type,
        severity: form.severity,
        location_name: form.location_name.trim(),
        crime_date: form.crime_date,
        description: form.description.trim(),
      }

      if (form.latitude && form.longitude) {
        payload.latitude = parseFloat(form.latitude)
        payload.longitude = parseFloat(form.longitude)
      }

      await reportCrime(payload, token)
      setSuccess(true)
      setTimeout(() => {
        navigate('/my-reports')
      }, 1500)
    } catch (err) {
      setError(err.message || 'Failed to submit crime report.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Report an Incident"
        description="Submit a verified crime incident for administrative review. Approved reports update public hotspot analytics."
        badge={
          <Link
            to="/my-reports"
            className="rounded-lg bg-gray-800 px-4 py-2 text-sm font-medium text-gray-300 transition-colors hover:bg-gray-700 hover:text-white"
          >
            View My Reports
          </Link>
        }
      />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <Card>
            <CardHeader
              title="Incident Details"
              subtitle="All submissions enter PENDING status until verified by an administrator"
              icon="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
            />

            {error && (
              <div className="mb-4 rounded-lg border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-400">
                {error}
              </div>
            )}

            {success && (
              <div className="mb-4 rounded-lg border border-green-500/30 bg-green-500/10 p-3 text-sm text-green-400">
                Crime report submitted successfully! Redirecting to your reports...
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div>
                  <label htmlFor="crime_type" className="mb-1.5 block text-xs font-medium text-gray-400">
                    Crime Category *
                  </label>
                  <select
                    id="crime_type"
                    name="crime_type"
                    value={form.crime_type}
                    onChange={handleChange}
                    className={inputClass}
                  >
                    {CRIME_TYPES.map((cat) => (
                      <option key={cat} value={cat} className="bg-gray-900 text-white">
                        {cat}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label htmlFor="severity" className="mb-1.5 block text-xs font-medium text-gray-400">
                    Perceived Severity *
                  </label>
                  <select
                    id="severity"
                    name="severity"
                    value={form.severity}
                    onChange={handleChange}
                    className={inputClass}
                  >
                    {SEVERITIES.map((sev) => (
                      <option key={sev} value={sev} className="bg-gray-900 text-white">
                        {sev}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div>
                  <label htmlFor="location_name" className="mb-1.5 block text-xs font-medium text-gray-400">
                    Locality / Area Name *
                  </label>
                  <input
                    id="location_name"
                    name="location_name"
                    type="text"
                    required
                    placeholder="e.g. Katpadi, Gandhi Nagar, Vellore"
                    value={form.location_name}
                    onChange={handleChange}
                    className={inputClass}
                  />
                </div>

                <div>
                  <label htmlFor="crime_date" className="mb-1.5 block text-xs font-medium text-gray-400">
                    Date of Incident *
                  </label>
                  <input
                    id="crime_date"
                    name="crime_date"
                    type="date"
                    required
                    value={form.crime_date}
                    onChange={handleChange}
                    className={inputClass}
                  />
                </div>
              </div>

              <div>
                <div className="mb-1.5 flex items-center justify-between">
                  <label className="text-xs font-medium text-gray-400">
                    GPS Coordinates (Optional, recommended for hotspots)
                  </label>
                  <button
                    type="button"
                    onClick={handleGetLocation}
                    disabled={geoLoading}
                    className="inline-flex items-center gap-1.5 text-xs text-blue-400 hover:text-blue-300 disabled:opacity-50"
                  >
                    <svg className="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0zM15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                    </svg>
                    {geoLoading ? 'Detecting...' : 'Use My Current Location'}
                  </button>
                </div>
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                  <input
                    type="number"
                    step="any"
                    name="latitude"
                    placeholder="Latitude (e.g. 13.043505)"
                    value={form.latitude}
                    onChange={handleChange}
                    className={inputClass}
                  />
                  <input
                    type="number"
                    step="any"
                    name="longitude"
                    placeholder="Longitude (e.g. 79.240410)"
                    value={form.longitude}
                    onChange={handleChange}
                    className={inputClass}
                  />
                </div>
              </div>

              <div>
                <label htmlFor="description" className="mb-1.5 block text-xs font-medium text-gray-400">
                  Incident Description *
                </label>
                <textarea
                  id="description"
                  name="description"
                  rows={4}
                  required
                  placeholder="Provide clear details regarding what occurred, suspects, items involved, and exact landmark..."
                  value={form.description}
                  onChange={handleChange}
                  className={inputClass}
                />
              </div>

              <div className="pt-2">
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-medium text-white transition-colors hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {loading ? 'Submitting Report...' : 'Submit Incident Report'}
                </button>
              </div>
            </form>
          </Card>
        </div>

        <div>
          <Card>
            <CardHeader
              title="Verification Policy"
              subtitle="How your report is handled"
              icon="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
            />
            <div className="space-y-4 text-xs text-gray-400">
              <div className="rounded-lg border border-gray-800 bg-gray-950/40 p-3">
                <p className="font-semibold text-gray-200">1. Citizen Submission</p>
                <p className="mt-1 text-gray-400">
                  Submitted as <strong>{user?.name || 'Citizen'}</strong>. Initially marked as <strong>PENDING</strong>.
                </p>
              </div>
              <div className="rounded-lg border border-gray-800 bg-gray-950/40 p-3">
                <p className="font-semibold text-gray-200">2. Administrative Triage</p>
                <p className="mt-1 text-gray-400">
                  Designated system administrators review the report against police feeds and local authority records.
                </p>
              </div>
              <div className="rounded-lg border border-gray-800 bg-gray-950/40 p-3">
                <p className="font-semibold text-gray-200">3. Hotspot Inclusion</p>
                <p className="mt-1 text-gray-400">
                  Only <strong>APPROVED</strong> records enter DBSCAN clustering, monthly trend charts, and proximity alert radius checks.
                </p>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  )
}

export default ReportCrime
