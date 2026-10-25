import StatusBadge from './StatusBadge'

const priorityBorderStyles = {
  High: 'border-l-red-500',
  Medium: 'border-l-yellow-500',
  Low: 'border-l-green-500',
}

function AlertItem({ alert }) {
  return (
    <div
      className={`rounded-lg border border-gray-800 border-l-4 ${priorityBorderStyles[alert.priority] || 'border-l-gray-500'} bg-gray-800/30 p-4 transition-all duration-200 hover:bg-gray-800/50 hover:border-gray-700`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="text-sm font-medium text-gray-200">{alert.title}</h3>
            <StatusBadge status={alert.priority} />
          </div>
          <p className="mt-1 text-xs text-gray-500">{alert.description}</p>
          <div className="mt-2 flex flex-wrap items-center gap-3 text-xs text-gray-500">
            <span className="flex items-center gap-1">
              <svg className="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0zM15 11a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
              {alert.location}
            </span>
            <span className="flex items-center gap-1">
              <svg className="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              {alert.time}
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}

export default AlertItem