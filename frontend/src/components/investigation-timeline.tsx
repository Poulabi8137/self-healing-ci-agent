import { useEffect, useReducer } from 'react'
import { AlertTriangle, Search, FileText, Brain, Wrench, Beaker, CheckCircle, XCircle, GitPullRequest, Activity, Loader2 } from 'lucide-react'
import type { SseEvent } from '../lib/types'
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

type TimelineState = {
  events: SseEvent[]
  loading: boolean
  error: string | null
}

type TimelineAction =
  | { type: 'fetch_start' }
  | { type: 'fetch_success'; events: SseEvent[] }
  | { type: 'fetch_error'; error: string }
  | { type: 'merge_sse'; events: SseEvent[] }

function timelineReducer(state: TimelineState, action: TimelineAction): TimelineState {
  switch (action.type) {
    case 'fetch_start':
      return { ...state, loading: true, error: null }
    case 'fetch_success':
      return { events: action.events, loading: false, error: null }
    case 'fetch_error':
      return { ...state, loading: false, error: action.error }
    case 'merge_sse': {
      const ids = new Set(state.events.map((e) => e.id))
      const fresh = action.events.filter((e) => !ids.has(e.id))
      if (fresh.length === 0) return state
      return {
        ...state,
        events: [...fresh, ...state.events].sort(
          (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
        ),
      }
    }
  }
}

export function InvestigationTimeline({
  investigationId,
  sseEvents,
}: {
  investigationId: number
  sseEvents?: SseEvent[]
}) {
  const [state, dispatch] = useReducer(timelineReducer, { events: [], loading: true, error: null })

  useEffect(() => {
    dispatch({ type: 'fetch_start' })
    let cancelled = false
    fetch(`/api/events/investigation/${investigationId}`)
      .then((r) => {
        if (!r.ok) throw new Error(r.status === 404 ? 'Investigation not found' : 'Failed to load timeline')
        return r.json()
      })
      .then((data: SseEvent[]) => {
        if (!cancelled) dispatch({ type: 'fetch_success', events: data })
      })
      .catch((err) => {
        if (!cancelled) dispatch({ type: 'fetch_error', error: err.message })
      })
    return () => { cancelled = true }
  }, [investigationId])

  useEffect(() => {
    if (!sseEvents || sseEvents.length === 0) return
    dispatch({ type: 'merge_sse', events: sseEvents })
  }, [sseEvents])

  if (state.loading) {
    return (
      <div className="flex items-center justify-center py-12 text-zinc-500">
        <Loader2 className="h-5 w-5 animate-spin mr-2" />
        <span className="text-sm">Loading timeline…</span>
      </div>
    )
  }

  if (state.error) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-red-400">
        <XCircle className="h-6 w-6 mb-2" />
        <p className="text-sm">{state.error}</p>
      </div>
    )
  }

  if (state.events.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-zinc-500">
        <Activity className="h-8 w-8 mb-2 opacity-40" />
        <p className="text-sm">No events recorded for this investigation</p>
      </div>
    )
  }

  return (
    <div className="relative">
      <div className="absolute left-[11px] top-2 bottom-2 w-0.5 bg-zinc-700/50" />
      <div className="space-y-0">
        {state.events.map((event, idx) => {
          const cfg = getConfig(event.event_type)
          const Icon = cfg.icon
          const isLast = idx === state.events.length - 1
          return (
            <div key={event.id} className="relative flex items-start gap-4 pb-4">
              {!isLast && (
                <div className="absolute left-[11px] top-6 bottom-0 w-0.5 bg-zinc-700/50" />
              )}
              <div className={`relative z-10 flex h-6 w-6 items-center justify-center rounded-full bg-zinc-900 ring-2 ring-zinc-800 ${cfg.color}`}>
                <Icon className="h-3 w-3" />
              </div>
              <div className="flex-1 min-w-0 pt-0.5">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-zinc-200">{cfg.label}</span>
                  <span className="text-xs text-zinc-500">{timeAgo(event.created_at)}</span>
                </div>
                {renderEventData(event)}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

function renderEventData(event: SseEvent) {
  const d = event.data
  if (!d) return null

  switch (event.event_type) {
    case 'investigation_started':
      return d.analysis_summary ? <p className="text-xs text-zinc-400 mt-1">{String(d.analysis_summary)}</p> : null
    case 'root_cause_identified':
      return (
        <div className="mt-1 space-y-0.5">
          {d.root_cause ? <p className="text-xs text-zinc-400">Root cause: <span className="text-zinc-300">{String(d.root_cause)}</span></p> : null}
          {d.error_category ? <p className="text-xs text-zinc-400">Category: {String(d.error_category)}</p> : null}
          {d.confidence != null ? <p className="text-xs text-zinc-400">Confidence: {(Number(d.confidence) * 100).toFixed(0)}%</p> : null}
        </div>
      )
    case 'fix_generated':
      return (
        <div className="mt-1 space-y-0.5">
          {d.fix_summary ? <p className="text-xs text-zinc-400">{String(d.fix_summary)}</p> : null}
          {Array.isArray(d.modified_files) && d.modified_files.length > 0
            ? <p className="text-xs text-zinc-500">Files: {(d.modified_files as string[]).join(', ')}</p>
            : null}
        </div>
      )
    case 'validation_completed':
      return (
        <div className="mt-1 space-y-0.5">
          <p className="text-xs text-zinc-400">Status: <span className={d.status === 'passed' ? 'text-emerald-400' : 'text-red-400'}>{String(d.status)}</span></p>
          {Array.isArray(d.failed_tests) && d.failed_tests.length > 0
            ? <p className="text-xs text-red-400/80">Failed tests: {(d.failed_tests as string[]).join(', ')}</p>
            : null}
        </div>
      )
    case 'pr_created':
      return (
        <div className="mt-1">
          {d.pr_url ? (
            <a href={String(d.pr_url)} target="_blank" rel="noopener noreferrer" className="text-xs text-blue-400 hover:underline">{String(d.pr_title)}</a>
          ) : (
            <p className="text-xs text-zinc-400">{String(d.pr_title)}</p>
          )}
        </div>
      )
    case 'failure_detected':
      return d.error_message ? <p className="text-xs text-zinc-400 mt-1">{String(d.error_message)}</p> : null
    case 'logs_collected':
      return d.log_size != null ? <p className="text-xs text-zinc-500 mt-1">{Number(d.log_size).toLocaleString()} bytes</p> : null
    default:
      return null
  }
}
