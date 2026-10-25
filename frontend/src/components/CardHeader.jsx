function CardHeader({ title, subtitle, icon, iconBg = 'bg-blue-500/20', iconColor = 'text-blue-400', action }) {
  return (
    <div className="mb-4 flex items-center justify-between">
      <div className="flex items-center gap-3">
        {icon && (
          <span className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-lg ${iconBg}`}>
            <svg className={`h-5 w-5 ${iconColor}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d={icon} />
            </svg>
          </span>
        )}
        <div>
          <h2 className="text-lg font-semibold text-white">{title}</h2>
          {subtitle && <p className="text-sm text-gray-500">{subtitle}</p>}
        </div>
      </div>
      {action}
    </div>
  )
}

export default CardHeader