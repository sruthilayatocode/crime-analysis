import { Link } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { dashboardPathForRole } from '../utils/roles'

function Unauthorized() {
  const { user, role } = useAuth()

  return (
    <div className="flex min-h-[70vh] items-center justify-center p-6">
      <div className="w-full max-w-md rounded-xl border border-gray-800 bg-gray-900/50 p-8 text-center backdrop-blur-sm">
        <span className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-red-500/10">
          <svg className="h-7 w-7 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
          </svg>
        </span>

        <h1 className="mt-4 text-2xl font-bold text-white">Access denied</h1>

        <p className="mt-2 text-sm text-gray-400">
          {user?.name ? `${user.name}, your` : 'Your'} account does not have permission to open
          this page.
        </p>

        <Link
          to={dashboardPathForRole(role)}
          className="mt-6 inline-block rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-medium text-white transition-colors hover:bg-blue-700"
        >
          Back to my dashboard
        </Link>
      </div>
    </div>
  )
}

export default Unauthorized
