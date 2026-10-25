import Card from './Card'
import CardHeader from './CardHeader'

function PersonalInfoCard({ info }) {
  return (
    <Card>
      <CardHeader
        title="Personal Information"
        subtitle="Your contact details"
        icon="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
      />

      <div className="space-y-4">
        <div>
          <p className="text-xs text-gray-500">Address</p>
          <p className="mt-1 text-sm text-gray-300">{info.address}</p>
        </div>
        <div>
          <p className="text-xs text-gray-500">City</p>
          <p className="mt-1 text-sm text-gray-300">{info.city}</p>
        </div>
        <div>
          <p className="text-xs text-gray-500">Emergency Contact</p>
          <p className="mt-1 text-sm font-medium text-gray-300">{info.emergencyContact}</p>
        </div>
      </div>
    </Card>
  )
}

export default PersonalInfoCard