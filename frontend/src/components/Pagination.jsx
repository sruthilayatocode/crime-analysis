function Pagination({ currentPage, totalPages, onPageChange }) {
  return (
    <div className="flex flex-col items-center justify-between gap-3 border-t border-gray-800 pt-4 sm:flex-row">
      <p className="text-sm text-gray-500">
        Showing page <span className="font-medium text-gray-300">{currentPage}</span> of{' '}
        <span className="font-medium text-gray-300">{totalPages}</span>
      </p>
      <div className="flex items-center gap-2">
        <button
          onClick={() => onPageChange(currentPage - 1)}
          disabled={currentPage === 1}
          className="rounded-lg bg-gray-800 px-3 py-1.5 text-sm font-medium text-gray-400 transition-colors hover:bg-gray-700 hover:text-white disabled:cursor-not-allowed disabled:opacity-50"
        >
          Previous
        </button>
        {Array.from({ length: totalPages }, (_, i) => i + 1).map((page) => (
          <button
            key={page}
            onClick={() => onPageChange(page)}
            className={`h-8 w-8 rounded-lg text-sm font-medium transition-all ${
              page === currentPage
                ? 'bg-blue-600 text-white'
                : 'bg-gray-800 text-gray-400 hover:bg-gray-700 hover:text-white'
            }`}
          >
            {page}
          </button>
        ))}
        <button
          onClick={() => onPageChange(currentPage + 1)}
          disabled={currentPage === totalPages}
          className="rounded-lg bg-gray-800 px-3 py-1.5 text-sm font-medium text-gray-400 transition-colors hover:bg-gray-700 hover:text-white disabled:cursor-not-allowed disabled:opacity-50"
        >
          Next
        </button>
      </div>
    </div>
  )
}

export default Pagination