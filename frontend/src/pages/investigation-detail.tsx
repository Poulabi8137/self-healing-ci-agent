import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { ArrowLeft, Loader2, XCircle, ListTodo, Activity, GitPullRequest } from 'lucide-react'
import { useEventStream } from '@/hooks/use-event-stream'
import { timeAgo } from '@/lib/time'
import { InvestigationTimeline } from '@/components/investigation-timeline'
import { ActivityStream } from '@/components/activity-stream'
import { RootCauseView } from '@/components/root-cause-view'
import { FixView } from '@/components/fix-view'
import { ValidationView } from '@/components/validation-view'
import { PullRequestView } from '@/components/pull-request-view'
import { RepositoryStatusBadge, StatusProgressBar } from '@/components/repository-status-badge'

interface InvestigationDetail {
  id: number
  failure_id: number | null
  repository_id: number | null
  status: string
  root_cause: string | null
  error_category: string | null
  confidence: number | null
  summary: string | null
  stages: unknown[]
  current_stage: string | null
  current_stage_status: string | null
  created_at: string | null
  updated_at: string | null
  completed_at: string | null
}

type Tab = 'timeline' | 'activity' | 'root_cause' | 'fix' | 'validation' | 'pull_request'

export default function InvestigationDetail() {
  const { id } = useParams<{ id: string }>()
  const investigationId = Number(id)
  const [investigation, setInvestigation] = useState<InvestigationDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<Tab>('timeline')
  const { events, connected } = useEventStream(true)

  const scopedEvents = events
    .filter((e) => e.investigation_id === investigationId)
    .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())

  useEffect(() => {
    let cancelled = false
    fetch(`/api/investigations/${investigationId}`, { credentials: 'include' })
      .then((r) => {
        if (!r.ok) throw new Error(r.status === 404 ? 'Investigation not found' : 'Failed to load investigation')
        return r.json()
      })
      .then((data: InvestigationDetail) => {
        if (!cancelled) { setInvestigation(data); setLoading(false) }
      })
      .catch((err) => {
        if (!cancelled) { setError(err.message); setLoading(false) }
      })
    return () => { cancelled = true }
  }, [investigationId])

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh] text-zinc-500">
        <Loader2 className="h-6 w-6 animate-spin mr-2" />
        <span>Loading investigation…</span>
      </div>
    )
  }

  if (error || !investigation) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] text-red-400">
        <XCircle className="h-8 w-8 mb-3" />
        <p className="text-sm">{error ?? 'Investigation not found'}</p>
        <Link to="/investigations" className="mt-4 text-sm text-blue-400 hover:underline">Back to investigations</Link>
      </div>
    )
  }

  const tabs: { id: Tab; label: string; icon: typeof Activity }[] = [
    { id: 'timeline', label: 'Timeline', icon: ListTodo },
    { id: 'activity', label: 'Activity', icon: Activity },
    { id: 'root_cause', label: 'Root Cause', icon: Activity },
    { id: 'fix', label: 'Fix', icon: Activity },
    { id: 'validation', label: 'Validation', icon: Activity },
    { id: 'pull_request', label: 'Pull Request', icon: GitPullRequest },
  ]

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div className="flex items-center gap-3">
        <Link to="/investigations" className="text-zinc-400 hover:text-zinc-200 transition-colors">
          <ArrowLeft className="h-4 w-4" />
        </Link>
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-lg font-semibold text-zinc-100">
              Investigation #{investigation.id}
            </h1>
            <RepositoryStatusBadge status={investigation.status} />
          </div>
          {investigation.created_at && (
            <p className="text-xs text-zinc-500 mt-0.5">
              Started {timeAgo(investigation.created_at)}
              {investigation.completed_at && ` · Completed ${timeAgo(investigation.completed_at)}`}
            </p>
          )}
        </div>
      </div>

      <StatusProgressBar status={investigation.status} />

      <div className="flex items-center gap-1 border-b border-zinc-800">
        {tabs.map((tab) => {
          const Icon = tab.icon
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-1.5 px-3 py-2 text-sm font-medium border-b-2 transition-colors ${
                activeTab === tab.id
                  ? 'border-blue-500 text-zinc-200'
                  : 'border-transparent text-zinc-500 hover:text-zinc-300'
              }`}
            >
              <Icon className="h-3.5 w-3.5" />
              {tab.label}
            </button>
          )
        })}
        {!connected && (
          <span className="ml-auto text-xs text-amber-500 flex items-center gap-1">
            <span className="h-1.5 w-1.5 rounded-full bg-amber-500 animate-pulse" />
            Reconnecting…
          </span>
        )}
      </div>

      <div>
        {activeTab === 'timeline' && (
          <InvestigationTimeline investigationId={investigationId} sseEvents={scopedEvents} />
        )}
        {activeTab === 'activity' && (
          <ActivityStream
            investigationId={investigationId}
            events={events}
            loading={false}
            error={null}
          />
        )}
        {activeTab === 'root_cause' && (
          <RootCauseView
            rootCause={investigation.root_cause}
            errorCategory={investigation.error_category}
            confidence={investigation.confidence}
            summary={investigation.summary}
          />
        )}
        {activeTab === 'fix' && (
          <FixView investigationId={investigationId} />
        )}
        {activeTab === 'validation' && (
          <ValidationView investigationId={investigationId} />
        )}
        {activeTab === 'pull_request' && (
          <PullRequestView investigationId={investigationId} />
        )}
      </div>

      {scopedEvents.length > 0 && (
        <div className="fixed bottom-4 right-4">
          <div className="flex items-center gap-2 rounded-full bg-blue-500/10 border border-blue-500/20 px-3 py-1.5 text-xs text-blue-400">
            <Activity className="h-3 w-3" />
            <span>{scopedEvents.length} live event{scopedEvents.length !== 1 ? 's' : ''}</span>
          </div>
        </div>
      )}
    </div>
  )
}
