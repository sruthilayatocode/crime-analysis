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

function StatCard({ label, value, color = 'blue', total }) {
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
      {typeof total === 'number' && Number.isFinite(total) && (
        <span className="mt-1 block text-xs text-gray-500">
          Of {total.toLocaleString()} validated incidents
        </span>
      )}
    </div>
  )
}

export default StatCard