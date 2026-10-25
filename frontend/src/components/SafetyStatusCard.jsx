import Card from './Card'
import CardHeader from './CardHeader'

const statusStyles = {
  Safe: {
    border: 'border-green-500/30',
    bg: 'bg-green-500/10',
    text: 'text-green-400',
    icon: 'M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z',
  },
  'Medium Risk': {
    border: 'border-yellow-500/30',
    bg: 'bg-yellow-500/10',
    text: 'text-yellow-400',
    icon: 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z',
  },
  'High Risk': {
    border: 'border-red-500/30',
    bg: 'bg-red-500/10',
    text: 'text-red-400',
    icon: 'M12 11c0 3.517-1.009 6.799-2.753 9.571m-3.44-2.04l.054-.09A13.916 13.916 0 008 8a4 4 0 118 0c0 1.017-.07 2.019-.203 3m-2.118 6.844A21.88 21.88 0 0015.171 17h3.839c.278 0 .554-.042.822-.125M19 9c0 1.017-.07 2.019-.203 3m-2.118 6.844A21.88 21.88 0 0112 21m0 0a21.88 21.88 0 01-4.679-1.281',
  },
}

function SafetyStatusCard({ safety }) {
  const styles = statusStyles[safety.level] || statusStyles['Safe']

  return (
    <Card className={`${styles.border} ${styles.bg}`}>
      <CardHeader
        title="Safety Status"
        subtitle="Current area assessment"
        icon={styles.icon}
        iconBg={styles.bg}
        iconColor={styles.text}
      />

      <div className="flex items-center gap-3">
        <span className={`h-3 w-3 rounded-full ${styles.text.replace('text-', 'bg-')}`} />
        <p className={`text-xl font-bold ${styles.text}`}>{safety.level}</p>
      </div>

      <p className="mt-3 text-sm leading-relaxed text-gray-400">{safety.message}</p>
    </Card>
  )
}

export default SafetyStatusCard