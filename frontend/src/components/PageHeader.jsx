function PageHeader({ title, description, badge }) {
  return (
    <div className="flex flex-col gap-4 rounded-xl border border-gray-800 bg-gradient-to-r from-blue-950 via-gray-900 to-gray-900 p-6 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <h1 className="text-2xl font-bold text-white">{title}</h1>
        {description && <p className="mt-1 text-sm text-gray-400">{description}</p>}
      </div>
      {badge}
    </div>
  )
}

export default PageHeader