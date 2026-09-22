import { useState } from 'react'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { dashboardPathForRole } from '../utils/roles'

const inputClass =
  'w-full rounded-lg border border-gray-800 bg-gray-950/60 px-3 py-2.5 text-sm text-gray-100 placeholder-gray-600 outline-none transition-colors focus:border-blue-500'

function Login() {
  const { isAuthenticated, user, login, submitting } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  const [form, setForm] = useState({ email: '', password: '' })
  const [error, setError] = useState('')

  const requestedPath = location.state?.from

  if (isAuthenticated) {
    return <Navigate to={requestedPath || dashboardPathForRole(user?.role)} replace />
  }

  const handleChange = (event) => {
    const { name, value } = event.target
    setForm((previous) => ({ ...previous, [name]: value }))
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    setError('')

    if (!form.email.trim() || !form.password) {
      setError('Email and password are required.')
      return
    }

    try {
      const signedInUser = await login(form.email.trim(), form.password)
      navigate(requestedPath || dashboardPathForRole(signedInUser.role), { replace: true })
    } catch (submitError) {
      setError(submitError.message || 'Unable to sign in. Please try again.')
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-950 px-4 py-10">
      <div className="w-full max-w-md rounded-xl border border-gray-800 bg-gray-900/50 p-8 backdrop-blur-sm">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-600">
            <svg className="h-5 w-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 11c0 3.517-1.009 6.799-2.753 9.571m-3.44-2.04l.054-.09A13.916 13.916 0 008 8a4 4 0 118 0c0 1.017-.07 2.019-.203 3" />
            </svg>
          </div>
          <div>
            <h1 className="text-lg font-bold text-white">CrimeSense</h1>
            <p className="text-xs text-gray-500">Sign in to continue</p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="mt-6 space-y-4">
          <div>
            <label htmlFor="email" className="mb-1.5 block text-xs font-medium text-gray-400">
              Email address
            </label>
            <input
              id="email"
              name="email"
              type="email"
              autoComplete="email"
              value={form.email}
              onChange={handleChange}
              placeholder="you@example.com"
              className={inputClass}
            />
          </div>

          <div>
            <label htmlFor="password" className="mb-1.5 block text-xs font-medium text-gray-400">
              Password
            </label>
            <input
              id="password"
              name="password"
              type="password"
              autoComplete="current-password"
              value={form.password}
              onChange={handleChange}
              placeholder="Enter your password"
              className={inputClass}
            />
          </div>

          {error && (
            <p className="rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-400">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={submitting}
            className="w-full rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-medium text-white transition-colors hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {submitting ? 'Signing in...' : 'Sign In'}
          </button>
        </form>

        <p className="mt-5 text-center text-sm text-gray-500">
          Don&apos;t have an account?{' '}
          <Link to="/register" className="font-medium text-blue-400 hover:text-blue-300">
            Create one
          </Link>
        </p>

        <div className="mt-6 rounded-lg border border-gray-800 bg-gray-800/40 p-3">
          <p className="text-[11px] font-medium uppercase tracking-wider text-gray-500">
            Demo administrator
          </p>
          <p className="mt-1 font-mono text-xs text-gray-400">
            admin@crimesense.local / Admin@12345
          </p>
        </div>
      </div>
    </div>
  )
}

export default Login
