import { useMemo } from 'react'
import { AlertTriangle, Search, FileText, Brain, Wrench, Beaker, CheckCircle, GitPullRequest, Activity, Loader2, XCircle } from 'lucide-react'
import type { SseEvent } from '../lib/types'
import { timeAgo } from '../lib/time'

const EVENT_ICONS: Record<string, { icon: typeof Activity; color: string; label: string }> = {
  failure_detected: { icon: AlertTriangle, color: 'text-red-500', label: 'Failure Detected' },
  investigation_started: { icon: Search, color: 'text-amber-500', label: 'Investigation Started' },
  logs_collected: { icon: FileText, color: 'text-blue-500', label: 'Logs Collected' },
  root_cause_identified: { icon: Brain, color: 'text-purple-500', label: 'Root Cause Identified' },
  fix_generated: { icon: Wrench, color: 'text-green-500', label: 'Fix Generated' },
  validation_started: { icon: Beaker, color: 'text-amber-500', label: 'Validation Started' },
  validation_completed: { icon: CheckCircle, color: 'text-emerald-500', label: 'Validation Completed' },
  pr_created: { icon: GitPullRequest, color: 'text-blue-500', label: 'PR Created' },
  repository_status_changed: { icon: Activity, color: 'text-cyan-500', label: 'Status Changed' },
}

function getIcon(eventType: string) {
  return EVENT_ICONS[eventType] ?? { icon: Activity, color: 'text-zinc-400', label: eventType }
}

export function ActivityStream({
  investigationId,
  events,
  loading,
  error,
}: {
  investigationId: number | null
  events: SseEvent[]
  loading: boolean
  error: string | null
}) {
  const grouped = useMemo(() => {
    const filtered = investigationId
      ? events.filter((e) => e.investigation_id === investigationId)
      : events
    const groups = new Map<string, SseEvent[]>()
    for (const event of filtered) {
      const date = event.created_at?.split('T')[0] ?? 'unknown'
      if (!groups.has(date)) groups.set(date, [])
      groups.get(date)!.push(event)
    }
    return groups
  }, [events, investigationId])

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12 text-zinc-500">
        <Loader2 className="h-5 w-5 animate-spin mr-2" />
        <span className="text-sm">Loading events…</span>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-red-400">
        <XCircle className="h-6 w-6 mb-2" />
        <p className="text-sm">{error}</p>
      </div>
    )
  }

  if (grouped.size === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-zinc-500">
        <Activity className="h-8 w-8 mb-2 opacity-40" />
        <p className="text-sm">No events yet</p>
        <p className="text-xs mt-1 opacity-60">
          {investigationId
            ? 'Events will appear here as the investigation progresses.'
            : 'Connect a repository and trigger a workflow to see events.'}
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {Array.from(grouped.entries()).map(([date, dateEvents]) => (
        <div key={date}>
          <h4 className="text-xs font-medium text-zinc-500 uppercase tracking-wider mb-2">
            {date === new Date().toISOString().split('T')[0] ? 'Today' : date}
          </h4>
          <div className="space-y-0.5">
            {dateEvents.map((event) => {
              const cfg = getIcon(event.event_type)
              const Icon = cfg.icon
              return (
                <div
                  key={event.id}
                  className="flex items-start gap-3 rounded-lg px-3 py-2 text-sm hover:bg-zinc-800/50 transition-colors"
                >
                  <div className={`mt-0.5 ${cfg.color}`}>
                    <Icon className="h-4 w-4" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-zinc-200">{cfg.label}</span>
                      {event.data?.repository
                        ? <span className="text-zinc-500 truncate text-xs">{String(event.data.repository)}</span>
                        : null}
                    </div>
                    {event.data?.workflow
                      ? <p className="text-xs text-zinc-500 truncate">{String(event.data.workflow)}</p>
                      : null}
                  </div>
                  <span className="text-xs text-zinc-500 shrink-0">
                    {timeAgo(event.created_at)}
                  </span>
                </div>
              )
            })}
          </div>
        </div>
      ))}
    </div>
  )
}
