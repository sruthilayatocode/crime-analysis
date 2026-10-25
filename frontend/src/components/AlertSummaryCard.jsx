const summaryStyles = {
  total: {
    border: 'border-blue-500/30',
    bg: 'bg-blue-500/10',
    text: 'text-blue-400',
    icon: 'M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9',
  },
  high: {
    border: 'border-red-500/30',
    bg: 'bg-red-500/10',
    text: 'text-red-400',
    icon: 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z',
  },
  medium: {
    border: 'border-yellow-500/30',
    bg: 'bg-yellow-500/10',
    text: 'text-yellow-400',
    icon: 'M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z',
  },
  low: {
    border: 'border-green-500/30',
    bg: 'bg-green-500/10',
    text: 'text-green-400',
    icon: 'M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z',
  },
}

function AlertSummaryCard({ type, label, value }) {
  const styles = summaryStyles[type] || summaryStyles.total

  return (
    <div className={`rounded-xl border ${styles.border} ${styles.bg} p-6 backdrop-blur-sm transition-colors duration-200 hover:border-gray-700`}>
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium text-gray-400">{label}</h3>
        <span className={`flex h-8 w-8 items-center justify-center rounded-lg ${styles.bg}`}>
          <svg className={`h-4 w-4 ${styles.text}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d={styles.icon} />
          </svg>
        </span>
      </div>
      <p className={`mt-3 text-3xl font-bold ${styles.text}`}>{value}</p>
    </div>
  )
}

export default AlertSummaryCard