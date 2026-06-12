import { AlertTriangle, Search, FileText, Brain, Wrench, Beaker, CheckCircle, GitPullRequest, Activity } from 'lucide-react'
import type { SseEvent } from '../hooks/use-event-stream'
import { timeAgo } from '../lib/time'

const EVENT_CONFIG: Record<string, { icon: typeof Activity; color: string; label: string }> = {
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

function getConfig(eventType: string) {
  return EVENT_CONFIG[eventType] ?? { icon: Activity, color: 'text-zinc-400', label: eventType }
}

export function LiveActivityFeed({
  events,
  connected,
  maxItems = 50,
}: {
  events: SseEvent[]
  connected: boolean
  maxItems?: number
}) {
  const display = events.slice(0, maxItems)

  if (display.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-zinc-500">
        <Activity className="h-8 w-8 mb-2 opacity-40" />
        <p className="text-sm">No recent activity</p>
        <p className="text-xs mt-1 opacity-60">Connect a repository and trigger a workflow to see events here.</p>
      </div>
    )
  }

  return (
    <div className="space-y-1">
      {display.map((event) => {
        const cfg = getConfig(event.event_type)
        const Icon = cfg.icon
        const repo = (event.data?.repository as string) ?? ''
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
                {repo ? <span className="text-zinc-500 truncate">{repo}</span> : null}
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
      {!connected && (
        <div className="text-center py-3 text-xs text-amber-500">
          Connection lost — new events may not appear until reconnected.
        </div>
      )}
    </div>
  )
}
