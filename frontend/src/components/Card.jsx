function Card({ children, className = '' }) {
  return (
    <div className={`rounded-xl border border-gray-800 bg-gray-900/50 p-6 backdrop-blur-sm transition-colors duration-200 hover:border-gray-700 ${className}`}>
      {children}
    </div>
  )
}

export default Card