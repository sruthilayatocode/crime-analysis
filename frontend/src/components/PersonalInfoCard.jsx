import Card from './Card'
import CardHeader from './CardHeader'

function PersonalInfoCard({ info }) {
  return (
    <Card>
      <CardHeader
        title="Account & Jurisdiction Information"
        subtitle="Verified identity and jurisdictional clearance"
        icon="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
      />

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div className="rounded-lg bg-gray-800/40 p-3.5 border border-gray-800">
          <p className="text-xs text-gray-500">Jurisdiction Region</p>
          <p className="mt-1 text-sm font-medium text-gray-200">{info?.jurisdiction || info?.address || 'Vellore, Tamil Nadu'}</p>
        </div>
        <div className="rounded-lg bg-gray-800/40 p-3.5 border border-gray-800">
          <p className="text-xs text-gray-500">Security Mode</p>
          <p className="mt-1 text-sm font-medium text-gray-200">{info?.authMode || info?.city || 'JWT Token Authentication'}</p>
        </div>
        <div className="rounded-lg bg-gray-800/40 p-3.5 border border-gray-800">
          <p className="text-xs text-gray-500">Emergency Helpline</p>
          <p className="mt-1 text-sm font-semibold text-blue-400">{info?.emergencyContact || '112 (National Helpline)'}</p>
        </div>
      </div>
    </Card>
  )
}

export default PersonalInfoCard