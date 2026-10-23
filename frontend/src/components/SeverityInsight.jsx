import Card from './Card'
import CardHeader from './CardHeader'

function MiniStat({ label, value, note }) {
  return (
    <div className="rounded-lg border border-gray-800 bg-gray-800/30 p-3">
      <p className="text-xs text-gray-500">{label}</p>
      <p className="mt-1 text-2xl font-bold text-white">
        {value}
        {note && <span className="ml-1 text-xs font-normal text-gray-500">{note}</span>}
      </p>
    </div>
  )
}

/**
 * Severity overview computed from real severity_score values.
 * Records without a score are excluded from the average/highest.
 */
function SeverityInsight({ insight }) {
  const { count = 0, average = 0, highest = 0 } = insight || {}
  const available = count > 0

  return (
    <Card className="h-full">
      <CardHeader
        title="Severity Insight"
        subtitle="Computed from severity_score"
      />

      <div className="grid grid-cols-3 gap-2 sm:gap-3">
        <MiniStat label="Average" value={available ? average.toFixed(1) : '—'} note="/ 10" />
        <MiniStat label="Highest" value={available ? highest.toFixed(1) : '—'} note="/ 10" />
        <MiniStat label="With scores" value={available ? count : 0} note="records" />
      </div>

      <p className="mt-3 text-xs text-gray-500">
        {available
          ? `${count} of the validated incidents have a recorded severity_score.`
          : 'No severity_score values are present in the dataset.'}
      </p>
    </Card>
  )
}

export default SeverityInsight