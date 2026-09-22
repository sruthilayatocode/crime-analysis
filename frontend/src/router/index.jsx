import { createBrowserRouter } from 'react-router-dom'
import MainLayout from '../layouts/MainLayout'
import ProtectedRoute from '../components/ProtectedRoute'
import RoleRoute from '../components/RoleRoute'
import Login from '../pages/Login'
import Register from '../pages/Register'
import Dashboard from '../pages/Dashboard'
import UserDashboard from '../pages/UserDashboard'
import AdminDashboard from '../pages/AdminDashboard'
import ManageUsers from '../pages/ManageUsers'
import Unauthorized from '../pages/Unauthorized'
import CrimeHotspots from '../pages/CrimeHotspots'
import InteractiveMap from '../pages/InteractiveMap'
import GPSTracking from '../pages/GPSTracking'
import Alerts from '../pages/Alerts'
import Profile from '../pages/Profile'
import NotFound from '../pages/NotFound'
import { useAuth } from '../hooks/useAuth'
import { ROLES } from '../utils/roles'

/**
 * Index route for "/". Shows the dashboard that matches the
 * signed-in account's role.
 */
function RoleHome() {
  const { role } = useAuth()

  return role === ROLES.ADMIN ? <AdminDashboard /> : <UserDashboard />
}

const router = createBrowserRouter([
  {
    path: '/',
    element: (
      <ProtectedRoute>
        <MainLayout />
      </ProtectedRoute>
    ),
    children: [
      { index: true, element: <RoleHome /> },
      {
        path: 'user/dashboard',
        element: (
          <RoleRoute allow={[ROLES.USER]}>
            <UserDashboard />
          </RoleRoute>
        ),
      },
      {
        path: 'admin/dashboard',
        element: (
          <RoleRoute allow={[ROLES.ADMIN]}>
            <AdminDashboard />
          </RoleRoute>
        ),
      },
      {
        path: 'dashboard',
        element: (
          <RoleRoute allow={[ROLES.ADMIN]}>
            <Dashboard />
          </RoleRoute>
        ),
      },
      {
        path: 'admin/users',
        element: (
          <RoleRoute allow={[ROLES.ADMIN]}>
            <ManageUsers />
          </RoleRoute>
        ),
      },
      { path: 'crime-hotspots', element: <CrimeHotspots /> },
      { path: 'map', element: <InteractiveMap /> },
      { path: 'gps-tracking', element: <GPSTracking /> },
      { path: 'alerts', element: <Alerts /> },
      { path: 'profile', element: <Profile /> },
      { path: 'unauthorized', element: <Unauthorized /> },
    ],
  },
  { path: '/login', element: <Login /> },
  { path: '/register', element: <Register /> },
  { path: '*', element: <NotFound /> },
])

export default router
