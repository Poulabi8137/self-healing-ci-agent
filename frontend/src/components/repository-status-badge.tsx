import { cn } from '@/lib/utils'

const STATUS_CONFIG: Record<string, { label: string; color: string; pulse: boolean }> = {
  active:       { label: 'Active',       color: 'bg-emerald-500', pulse: false },
  investigating:{ label: 'Investigating',color: 'bg-amber-500',   pulse: true  },
  detecting:    { label: 'Detecting',    color: 'bg-amber-500',   pulse: true  },
  analyzing:    { label: 'Analyzing',    color: 'bg-amber-500',   pulse: true  },
  fixing:       { label: 'Fixing',       color: 'bg-orange-500',  pulse: true  },
  validating:   { label: 'Validating',   color: 'bg-blue-500',    pulse: true  },
  pr_created:   { label: 'PR Created',   color: 'bg-purple-500',  pulse: false },
  completed:    { label: 'Completed',    color: 'bg-emerald-500', pulse: false },
  failed:       { label: 'Failed',       color: 'bg-red-500',     pulse: false },
}

const STATE_ORDER = ['active', 'detecting', 'analyzing', 'fixing', 'validating', 'pr_created', 'completed', 'failed']

export function RepositoryStatusBadge({
  status,
  className,
  showLabel = true,
}: {
  status: string
  className?: string
  showLabel?: boolean
}) {
  const cfg = STATUS_CONFIG[status] ?? { label: status, color: 'bg-zinc-500', pulse: false }

  return (
    <span className={cn('inline-flex items-center gap-1.5 text-xs font-medium', className)}>
      <span className="relative flex h-2 w-2">
        <span
          className={cn(
            'absolute inline-flex h-full w-full rounded-full opacity-75',
            cfg.color,
            cfg.pulse && 'animate-ping',
          )}
        />
        <span className={cn('relative inline-flex h-2 w-2 rounded-full', cfg.color)} />
      </span>
      {showLabel && <span className="text-zinc-300">{cfg.label}</span>}
    </span>
  )
}

export function StatusProgressBar({ status }: { status: string }) {
  const currentIdx = STATE_ORDER.indexOf(status)
  if (currentIdx === -1 || status === 'failed' || status === 'completed') return null

  return (
    <div className="flex items-center gap-1">
      {STATE_ORDER.filter((s) => s !== 'active' && s !== 'failed' && s !== 'completed').map((s, idx) => {
        const cfg = STATUS_CONFIG[s]
        const isActive = idx === currentIdx
        const isDone = idx < currentIdx
        return (
          <div key={s} className="flex items-center gap-1">
            <div
              className={cn(
                'h-1.5 w-6 rounded-full transition-colors',
                isDone ? 'bg-emerald-500/60' : isActive ? 'bg-amber-500 animate-pulse' : 'bg-zinc-700',
              )}
            />
            <span className="text-[10px] text-zinc-500 hidden sm:inline">{cfg.label}</span>
          </div>
        )
      })}
    </div>
  )
}
