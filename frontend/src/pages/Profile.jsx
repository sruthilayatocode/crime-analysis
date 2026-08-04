import UserProfileCard from '../components/UserProfileCard'
import PersonalInfoCard from '../components/PersonalInfoCard'
import AccountStatsCard from '../components/AccountStatsCard'
import SettingsCard from '../components/SettingsCard'
import AccountActionsCard from '../components/AccountActionsCard'
import RecentActivityCard from '../components/RecentActivityCard'
import PageHeader from '../components/PageHeader'
import {
  userProfile,
  personalInfo,
  accountStats,
  settings,
  recentActivity,
} from '../data/profileData'

function Profile() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="Profile"
        description="Manage your account information and preferences."
        badge={
          <div className="flex items-center gap-3">
            <span className="flex h-2 w-2">
              <span className="absolute inline-flex h-2 w-2 animate-ping rounded-full bg-green-400 opacity-75" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-green-500" />
            </span>
            <span className="text-sm font-medium text-green-400">Account Active</span>
          </div>
        }
      />

      {/* Profile and Personal Info */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <UserProfileCard profile={userProfile} />
        <div className="lg:col-span-2">
          <PersonalInfoCard info={personalInfo} />
        </div>
      </div>

      {/* Stats and Settings */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <AccountStatsCard stats={accountStats} />
        <SettingsCard settings={settings} />
      </div>

      {/* Actions and Activity */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <AccountActionsCard />
        <div className="lg:col-span-2">
          <RecentActivityCard activities={recentActivity} />
        </div>
      </div>
    </div>
  )
}

export default Profile