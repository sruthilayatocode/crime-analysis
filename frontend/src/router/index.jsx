import { createBrowserRouter } from 'react-router-dom'
import MainLayout from '../layouts/MainLayout'
import Login from '../pages/Login'
import Register from '../pages/Register'
import Dashboard from '../pages/Dashboard'
import CrimeHotspots from '../pages/CrimeHotspots'
import InteractiveMap from '../pages/InteractiveMap'
import GPSTracking from '../pages/GPSTracking'
import Alerts from '../pages/Alerts'
import Profile from '../pages/Profile'
import NotFound from '../pages/NotFound'

const router = createBrowserRouter([
  {
    path: '/',
    element: <MainLayout />,
    children: [
      { index: true, element: <Dashboard /> },
      { path: 'crime-hotspots', element: <CrimeHotspots /> },
      { path: 'map', element: <InteractiveMap /> },
      { path: 'gps-tracking', element: <GPSTracking /> },
      { path: 'alerts', element: <Alerts /> },
      { path: 'profile', element: <Profile /> },
    ],
  },
  { path: '/login', element: <Login /> },
  { path: '/register', element: <Register /> },
  { path: '*', element: <NotFound /> },
])

export default router