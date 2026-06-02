import { motion } from 'framer-motion'
import { cn } from '@/lib/utils'

const variants = {
  passed: 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20',
  failed: 'bg-red-500/10 text-red-500 border-red-500/20',
  partial: 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20',
  running: 'bg-blue-500/10 text-blue-500 border-blue-500/20',
  pending: 'bg-muted text-muted-foreground border-border',
  unknown: 'bg-muted text-muted-foreground border-border',
} as const

type Status = keyof typeof variants

const labels: Record<Status, string> = {
  passed: 'Passed',
  failed: 'Failed',
  partial: 'Partial',
  running: 'Running',
  pending: 'Pending',
  unknown: 'Unknown',
}

export function StatusBadge({
  status,
  animated = true,
}: {
  status: Status | string
  animated?: boolean
}) {
  const s = (Object.keys(variants).includes(status) ? status : 'unknown') as Status
  const el = (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium',
        variants[s],
      )}
      role="status"
      aria-label={`Status: ${labels[s]}`}
    >
      <span
        className={cn(
          'h-1.5 w-1.5 rounded-full',
          s === 'running' && 'animate-pulse',
          s === 'passed' && 'bg-emerald-500',
          s === 'failed' && 'bg-red-500',
          s === 'partial' && 'bg-yellow-500',
          s === 'running' && 'bg-blue-500',
          (s === 'pending' || s === 'unknown') && 'bg-muted-foreground',
        )}
        aria-hidden="true"
      />
      {labels[s]}
    </span>
  )

  if (!animated) return el

  return (
    <motion.div
      key={status}
      initial={{ scale: 0 }}
      animate={{ scale: 1 }}
      transition={{ type: 'spring', stiffness: 400, damping: 20 }}
    >
      {el}
    </motion.div>
  )
}
