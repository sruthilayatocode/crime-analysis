import { useEffect, useState } from 'react'
import UserProfileCard from '../components/UserProfileCard'
import PersonalInfoCard from '../components/PersonalInfoCard'
import AccountStatsCard from '../components/AccountStatsCard'
import SettingsCard from '../components/SettingsCard'
import AccountActionsCard from '../components/AccountActionsCard'
import RecentActivityCard from '../components/RecentActivityCard'
import PageHeader from '../components/PageHeader'
import { useAuth } from '../hooks/useAuth'
import { formatRole, initialsFor, ROLES } from '../utils/roles'
import { getMyReports, getStatistics } from '../services/api'

function Profile() {
  const { user, role, token } = useAuth()
  const [statsData, setStatsData] = useState({
    alertsReceived: 0,
    crimeReportsViewed: 0,
    lastLogin: 'Active JWT',
    stat1Label: 'Reports Submitted',
    stat2Label: 'Approved Incidents',
    stat3Label: 'Session Status',
  })

  useEffect(() => {
    let mounted = true
    if (role === ROLES.USER) {
      getMyReports(token)
        .then((res) => {
          if (!mounted) return
          const reports = res.data || []
          const approved = reports.filter((r) => r.status === 'APPROVED').length
          setStatsData({
            alertsReceived: reports.length,
            crimeReportsViewed: approved,
            lastLogin: 'Active JWT Session',
            stat1Label: 'My Reports',
            stat2Label: 'Approved Records',
            stat3Label: 'Auth Token',
          })
        })
        .catch(() => {})
    } else {
      getStatistics()
        .then((res) => {
          if (!mounted) return
          const s = res.data || {}
          setStatsData({
            alertsReceived: s.total_crimes || 0,
            crimeReportsViewed: s.pending_approvals || 0,
            lastLogin: 'Admin Privileged',
            stat1Label: 'Verified Database Crimes',
            stat2Label: 'Pending Approvals',
            stat3Label: 'Access Level',
          })
        })
        .catch(() => {})
    }
    return () => {
      mounted = false
    }
  }, [role, token])

  const profile = {
    name: user?.name || 'Citizen User',
    email: user?.email || 'N/A',
    role: formatRole(role),
    initials: initialsFor(user?.name || 'CrimeSense User'),
    userId: user?.id,
  }

  const jurisdictionInfo = {
    jurisdiction: 'Vellore District, Tamil Nadu',
    authMode: 'JWT Bearer Authorization',
    emergencyContact: '112 (National Emergency Helpline)',
  }

  const settingsPreferences = {
    notifications: true,
    darkMode: true,
    gpsPermission: 'Browser Controlled',
  }

  const activities = [
    { id: 1, action: `Authenticated as ${user?.name || 'User'} (${formatRole(role)})`, time: 'Current Session' },
    { id: 2, action: 'Connected to CrimeSense Vellore jurisdiction API', time: 'Active' },
    { id: 3, action: 'Role authorization verified by token_required guard', time: 'Verified' },
  ]

  return (
    <div className="space-y-6">
      <PageHeader
        title="Account Profile & Settings"
        description="Review your authenticated user credentials, session authorization, and jurisdictional status."
        badge={
          <div className="flex items-center gap-3">
            <span className="flex h-2 w-2 relative">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-green-400 opacity-75" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-green-500" />
            </span>
            <span className="text-xs font-semibold text-green-400">Authenticated & Active</span>
          </div>
        }
      />

      {/* Profile and Account Info */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <UserProfileCard profile={profile} />
        <div className="lg:col-span-2">
          <PersonalInfoCard info={jurisdictionInfo} />
        </div>
      </div>

      {/* Stats and Settings */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <AccountStatsCard stats={statsData} />
        <SettingsCard settings={settingsPreferences} />
      </div>

      {/* Actions and Activity */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <AccountActionsCard />
        <div className="lg:col-span-2">
          <RecentActivityCard activities={activities} />
        </div>
      </div>
    </div>
  )
}

export default Profile