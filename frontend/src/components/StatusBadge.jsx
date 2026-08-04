const badgeStyles = {
  High: 'bg-red-500/10 text-red-400 border-red-500/30',
  Medium: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/30',
  Low: 'bg-green-500/10 text-green-400 border-green-500/30',
  Active: 'bg-red-500/10 text-red-400 border-red-500/30',
  Resolved: 'bg-green-500/10 text-green-400 border-green-500/30',
  Pending: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/30',
  'Under Investigation': 'bg-blue-500/10 text-blue-400 border-blue-500/30',
  Safe: 'bg-green-500/10 text-green-400 border-green-500/30',
  'Medium Risk': 'bg-yellow-500/10 text-yellow-400 border-yellow-500/30',
  'High Risk': 'bg-red-500/10 text-red-400 border-red-500/30',
}

const dotStyles = {
  High: 'bg-red-500',
  Medium: 'bg-yellow-500',
  Low: 'bg-green-500',
  Active: 'bg-red-500',
  Resolved: 'bg-green-500',
  Pending: 'bg-yellow-500',
  'Under Investigation': 'bg-blue-500',
  Safe: 'bg-green-500',
  'Medium Risk': 'bg-yellow-500',
  'High Risk': 'bg-red-500',
}

function StatusBadge({ status }) {
  const badgeStyle = badgeStyles[status] || 'bg-gray-500/10 text-gray-400 border-gray-500/30'
  const dotStyle = dotStyles[status] || 'bg-gray-500'

  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium ${badgeStyle}`}>
      <span className={`h-1.5 w-1.5 rounded-full ${dotStyle}`} />
      {status}
    </span>
  )
}

export default StatusBadge