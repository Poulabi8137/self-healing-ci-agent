import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Activity, GitPullRequest, CheckCircle, AlertCircle, RotateCw, Shield } from 'lucide-react'

type ActivityItem = {
  id: string
  type: 'workflow' | 'pr' | 'validation' | 'retry' | 'review'
  message: string
  status: 'success' | 'failure' | 'running' | 'pending'
  timestamp: Date
}

const statusIcon = {
  success: CheckCircle,
  failure: AlertCircle,
  running: Activity,
  pending: RotateCw,
}

const typeIcon = {
  workflow: Activity,
  pr: GitPullRequest,
  validation: Shield,
  retry: RotateCw,
  review: Shield,
}

const sampleMessages = [
  { type: 'workflow' as const, message: 'Workflow run #482 completed', status: 'success' as const },
  { type: 'workflow' as const, message: 'Workflow run #483 failed on build step', status: 'failure' as const },
  { type: 'retry' as const, message: 'Retry #3 initiated for run #479', status: 'running' as const },
  { type: 'validation' as const, message: 'Validation pipeline passed for run #480', status: 'success' as const },
  { type: 'review' as const, message: 'Security review flagged 2 issues in run #477', status: 'failure' as const },
  { type: 'pr' as const, message: 'PR #92 auto-approved and merged', status: 'success' as const },
  { type: 'workflow' as const, message: 'Workflow run #484 queued', status: 'pending' as const },
  { type: 'validation' as const, message: 'Validation pipeline failed on test execution', status: 'failure' as const },
  { type: 'retry' as const, message: 'Retry #2 succeeded for run #478', status: 'success' as const },
  { type: 'review' as const, message: 'Coverage review: 87% (threshold 80%)', status: 'success' as const },
  { type: 'workflow' as const, message: 'Workflow run #485 completed', status: 'success' as const },
  { type: 'pr' as const, message: 'PR #93 created by fix agent', status: 'pending' as const },
  { type: 'validation' as const, message: 'Validation pipeline passed for run #485', status: 'success' as const },
  { type: 'review' as const, message: 'Performance review: 92/100', status: 'success' as const },
  { type: 'retry' as const, message: 'Retry #1 failed for run #483', status: 'failure' as const },
]

function generateActivity(): ActivityItem {
  const now = new Date()
  const sample = sampleMessages[Math.floor(Math.random() * sampleMessages.length)]
  return {
    id: `${now.getTime()}-${Math.random().toString(36).slice(2, 6)}`,
    ...sample,
    timestamp: now,
  }
}

const initialActivities: ActivityItem[] = Array.from({ length: 10 }, (_, i) => {
  const t = new Date()
  t.setMinutes(t.getMinutes() - (10 - i) * 2)
  const sample = sampleMessages[i % sampleMessages.length]
  return { id: `init-${i}`, ...sample, timestamp: t }
})

export function ActivityFeed() {
  const [activities, setActivities] = useState<ActivityItem[]>(initialActivities)
  const [live, setLive] = useState(true)
  const listRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!live) return
    const interval = setInterval(() => {
      setActivities(prev => [generateActivity(), ...prev.slice(0, 49)])
    }, 12_000 + Math.random() * 8_000)
    return () => clearInterval(interval)
  }, [live])

  function timeLabel(t: Date): string {
    const now = new Date()
    const diff = now.getTime() - t.getTime()
    if (diff < 60_000) return 'Just now'
    if (diff < 3_600_000) return `${Math.floor(diff / 60_000)}m ago`
    if (diff < 86_400_000) return `${Math.floor(diff / 3_600_000)}h ago`
    return t.toLocaleDateString()
  }

  const statusColors = {
    success: 'text-emerald-500',
    failure: 'text-red-500',
    running: 'text-blue-500',
    pending: 'text-yellow-500',
  }

  return (
    <div className="rounded-xl border border-border bg-card">
      <div className="flex items-center justify-between border-b border-border px-5 py-3">
        <div className="flex items-center gap-2">
          <Activity className="h-4 w-4 text-muted-foreground" />
          <h3 className="text-sm font-medium">Activity Feed</h3>
          <span className="relative flex h-2 w-2">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
            <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-500" />
          </span>
        </div>
        <button
          onClick={() => setLive(!live)}
          className={`rounded-md px-2 py-1 text-[10px] font-medium transition-colors ${
            live ? 'bg-emerald-500/10 text-emerald-500' : 'bg-muted text-muted-foreground'
          }`}
        >
          {live ? 'LIVE' : 'PAUSED'}
        </button>
      </div>

      <div ref={listRef} className="overflow-y-auto max-h-[360px] px-2 py-2">
        <AnimatePresence initial={false}>
          {activities.map((item, i) => {
            const StatusIcon = statusIcon[item.status]
            const color = statusColors[item.status]
            return (
              <motion.div
                key={item.id}
                layout
                initial={i === 0 ? { opacity: 0, y: -12, height: 0 } : { opacity: 1 }}
                animate={{ opacity: 1, y: 0, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
                className="flex items-start gap-3 rounded-lg px-3 py-2.5 hover:bg-muted/50"
              >
                <StatusIcon className={`mt-0.5 h-4 w-4 shrink-0 ${color}`} />
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-foreground truncate">{item.message}</p>
                  <p className="text-[10px] text-muted-foreground">{timeLabel(item.timestamp)}</p>
                </div>
              </motion.div>
            )
          })}
        </AnimatePresence>
      </div>
    </div>
  )
}
