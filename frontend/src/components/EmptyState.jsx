function EmptyState({ title, message }) {
  return (
    <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-gray-800 bg-gray-900/30 p-12 text-center">
      <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-gray-800/50">
        <svg className="h-8 w-8 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
        </svg>
      </div>
      <h3 className="text-lg font-semibold text-gray-300">{title}</h3>
      {message && <p className="mt-2 text-sm text-gray-500">{message}</p>}
    </div>
  )
}

export default EmptyState