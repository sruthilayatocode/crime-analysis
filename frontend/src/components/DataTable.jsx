function DataTable({ columns, data, emptyMessage = 'No data available.' }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left text-sm">
        <thead>
          <tr className="border-b border-gray-800 text-xs uppercase tracking-wider text-gray-500">
            {columns.map((col) => (
              <th key={col.key} className={`pb-3 pr-4 font-medium ${col.className || ''}`}>
                {col.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.length > 0 ? (
            data.map((row, index) => (
              <tr key={row.id || index} className="border-b border-gray-800/50 transition-colors hover:bg-gray-800/30">
                {columns.map((col) => (
                  <td key={col.key} className={`py-3 pr-4 ${col.cellClassName || ''}`}>
                    {col.render ? col.render(row) : row[col.key]}
                  </td>
                ))}
              </tr>
            ))
          ) : (
            <tr>
              <td colSpan={columns.length} className="py-8 text-center text-gray-500">
                {emptyMessage}
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  )
}

export default DataTable