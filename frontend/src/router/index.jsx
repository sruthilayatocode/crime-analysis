import { createBrowserRouter, Navigate } from 'react-router-dom';
import MainLayout from '../layouts/MainLayout';
import UserAppLayout from '../layouts/UserAppLayout';
import ProtectedRoute from '../components/ProtectedRoute';

// User pages (mobile-first under /app)
import UserHome from '../pages/user/UserHome';
import UserSaved from '../pages/user/UserSaved';
import UserSOS from '../pages/user/UserSOS';
import UserSettings from '../pages/user/UserSettings';

// Admin pages (desktop-first under /admin)
import AdminOverview from '../pages/admin/AdminOverview';
import AdminCrimeData from '../pages/admin/AdminCrimeData';
import AdminTrends from '../pages/admin/AdminTrends';
import AdminUsers from '../pages/admin/AdminUsers';
import AdminLiveMap from '../pages/admin/AdminLiveMap';
import AdminAlertsSOS from '../pages/admin/AdminAlertsSOS';
import AdminAuditLog from '../pages/admin/AdminAuditLog';

// Auth & Public pages
import Login from '../pages/Login';
import Register from '../pages/Register';
import NotFound from '../pages/NotFound';
import PublicSharedLocation from '../pages/PublicSharedLocation';

const router = createBrowserRouter([
  // Default entry point routes to user app
  {
    path: '/',
    element: <Navigate to="/app" replace />,
  },

  // Public Share URL (/s/:token) - Requires NO Authentication
  {
    path: '/s/:token',
    element: <PublicSharedLocation />,
  },

  // User Mobile-First Interface under /app
  {
    path: '/app',
    element: <UserAppLayout />,
    children: [
      { index: true, element: <UserHome /> },
      { path: 'home', element: <UserHome /> },
      { path: 'saved', element: <UserSaved /> },
      { path: 'sos', element: <UserSOS /> },
      { path: 'settings', element: <UserSettings /> },
    ],
  },

  // Admin Portal Interface under /admin (Guarded by ProtectedRoute with admin role)
  {
    path: '/admin',
    element: (
      <ProtectedRoute allowedRoles={['admin']}>
        <MainLayout />
      </ProtectedRoute>
    ),
    children: [
      { index: true, element: <AdminOverview /> },
      { path: 'overview', element: <AdminOverview /> },
      { path: 'dashboard', element: <AdminOverview /> },
      { path: 'crimes', element: <AdminCrimeData /> },
      { path: 'crime-hotspots', element: <AdminCrimeData /> },
      { path: 'map', element: <AdminCrimeData /> },
      { path: 'trends', element: <AdminTrends /> },
      { path: 'users', element: <AdminUsers /> },
      { path: 'live-map', element: <AdminLiveMap /> },
      { path: 'gps-tracking', element: <AdminLiveMap /> },
      { path: 'alerts', element: <AdminAlertsSOS /> },
      { path: 'audit-logs', element: <AdminAuditLog /> },
    ],
  },

  // Legacy route aliases (redirect to /admin)
  {
    path: '/dashboard',
    element: <Navigate to="/admin/overview" replace />,
  },
  {
    path: '/crime-hotspots',
    element: <Navigate to="/admin/crimes" replace />,
  },
  {
    path: '/map',
    element: <Navigate to="/admin/crimes" replace />,
  },
  {
    path: '/gps-tracking',
    element: <Navigate to="/admin/live-map" replace />,
  },
  {
    path: '/alerts',
    element: <Navigate to="/admin/alerts" replace />,
  },

  // Auth routes
  { path: '/login', element: <Login /> },
  { path: '/register', element: <Register /> },
  { path: '/signup', element: <Register /> },

  // Catch-all
  { path: '*', element: <NotFound /> },
]);

export default router;