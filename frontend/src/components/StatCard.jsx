const colorStyles = {
  red: {
    border: 'border-red-500/30',
    bg: 'bg-red-500/10',
    text: 'text-red-400',
    iconBg: 'bg-red-500/20',
  },
  yellow: {
    border: 'border-yellow-500/30',
    bg: 'bg-yellow-500/10',
    text: 'text-yellow-400',
    iconBg: 'bg-yellow-500/20',
  },
  green: {
    border: 'border-green-500/30',
    bg: 'bg-green-500/10',
    text: 'text-green-400',
    iconBg: 'bg-green-500/20',
  },
  blue: {
    border: 'border-blue-500/30',
    bg: 'bg-blue-500/10',
    text: 'text-blue-400',
    iconBg: 'bg-blue-500/20',
  },
}

function StatCard({ label, value, change, trend, color = 'blue' }) {
  const styles = colorStyles[color] || colorStyles.blue

  return (
    <div className={`rounded-xl border ${styles.border} ${styles.bg} p-6 backdrop-blur-sm transition-colors duration-200 hover:border-gray-700`}>
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium text-gray-400">{label}</h3>
        <span className={`flex h-8 w-8 items-center justify-center rounded-lg ${styles.iconBg} ${styles.text}`}>
          <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
          </svg>
        </span>
      </div>
      <p className={`mt-3 text-3xl font-bold ${styles.text}`}>{value.toLocaleString()}</p>
      <div className="mt-2 flex items-center gap-2">
        <span className={`text-xs font-medium ${trend === 'up' ? 'text-red-400' : 'text-green-400'}`}>
          {change}
        </span>
        <span className="text-xs text-gray-500">vs last month</span>
      </div>
    </div>
  )
}

export default StatCard