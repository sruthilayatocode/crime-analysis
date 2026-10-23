import Card from './Card'
import CardHeader from './CardHeader'

/**
 * JARVIS-style intelligence summary panel.
 * Displays fully factual statements auto-generated from the validated records.
 */
function IntelligenceSummary({ statements = [], total = 0 }) {
  return (
    <Card>
      <CardHeader
        icon="M12 3v3m0 16v-3m9-9h-3M6 12H3m15.36 6.36l-2.12-2.12M7.76 7.76L5.64 5.64m12.72 0l-2.12 2.12M7.76 16.24l-2.12 2.12M12 8a4 4 0 110 8 4 4 0 010-8z"
        title="CrimeSense Intelligence"
        subtitle={`Automated analysis of ${total} validated incidents`}
      />

      {statements.length === 0 ? (
        <p className="py-6 text-center text-sm text-gray-500">
          No intelligence summaries available.
        </p>
      ) : (
        <ul className="space-y-2.5">
          {statements.map((statement, index) => (
            <li key={index} className="flex items-start gap-3 text-sm text-gray-300">
              <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-cyan-400" />
              <span>{statement}</span>
            </li>
          ))}
        </ul>
      )}

      <p className="mt-4 border-t border-gray-800 pt-3 text-xs text-gray-500">
        Statements are generated from the available validated records and
        describe recorded incident distribution only — no predictions or claims
        of causation.
      </p>
    </Card>
  )
}

export default IntelligenceSummary