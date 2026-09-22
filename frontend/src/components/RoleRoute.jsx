import { Navigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { normalizeRole } from '../utils/roles'

function RoleRoute({ allow, children }) {
  const { isAuthenticated, role } = useAuth()

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  if (allow?.length && !allow.includes(normalizeRole(role))) {
    return <Navigate to="/unauthorized" replace />
  }

  return children
}

export default RoleRoute
