import { useQuery } from '@tanstack/react-query'
import { Bell, Mail, MessageSquare, CheckCircle2, XCircle, Clock } from 'lucide-react'
import { useState } from 'react'
import { fetchApi } from '@/lib/api'

interface Notification {
  id: number
  channel_type: string
  event_type: string
  status: string
  recipient: string | null
  subject: string | null
  delivered_at: string | null
  failure_reason: string | null
  created_at: string | null
}

interface NotificationsResponse {
  total: number
  limit: number
  offset: number
  notifications: Notification[]
}

const EVENT_LABELS: Record<string, string> = {
  investigation_started: 'Investigation Started',
  root_cause_identified: 'Root Cause Identified',
  fix_generated: 'Fix Generated',
  validation_completed: 'Validation Completed',
  pr_created: 'Pull Request Created',
  workflow_failed: 'Workflow Failed',
}

const EVENT_ICONS: Record<string, string> = {
  investigation_started: '🔍',
  root_cause_identified: '🕵️',
  fix_generated: '🔧',
  validation_completed: '✅',
  pr_created: '🎉',
  workflow_failed: '❌',
}

export default function NotificationsPage() {
  const [limit] = useState(50)
  const [offset, setOffset] = useState(0)

  const { data, isLoading, error } = useQuery<NotificationsResponse>({
    queryKey: ['notifications', limit, offset],
    queryFn: async () => fetchApi(`/notifications?limit=${limit}&offset=${offset}`),
  })

  if (isLoading) {
    return (
      <div className="flex h-full min-h-[60vh] items-center justify-center">
        <div className="h-8 w-8 animate-pulse rounded-full bg-muted-foreground/20" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex h-full min-h-[60vh] flex-col items-center justify-center gap-4">
        <XCircle className="h-12 w-12 text-destructive" />
        <p className="text-lg text-muted-foreground">Failed to load notifications</p>
        <p className="text-sm text-muted-foreground">{(error as Error).message}</p>
      </div>
    )
  }

  const notifs = data?.notifications ?? []

  if (notifs.length === 0) {
    return (
      <div className="mx-auto max-w-4xl space-y-8 p-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Notifications</h1>
          <p className="text-sm text-muted-foreground">Notification history</p>
        </div>
        <div className="flex flex-col items-center justify-center gap-4 rounded-lg border border-dashed p-12">
          <Bell className="h-12 w-12 text-muted-foreground/50" />
          <p className="text-lg text-muted-foreground">No notifications yet</p>
          <p className="text-sm text-muted-foreground">
            Notifications will appear here when workflow events occur.
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-4xl space-y-8 p-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Notifications</h1>
        <p className="text-sm text-muted-foreground">
          {data?.total ?? 0} notification{(data?.total ?? 0) !== 1 ? 's' : ''}
        </p>
      </div>

      <div className="space-y-3">
        {notifs.map((n) => (
          <div
            key={n.id}
            className="flex items-start gap-4 rounded-lg border bg-card p-4 text-card-foreground shadow-sm"
          >
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-muted text-lg">
              {EVENT_ICONS[n.event_type] ?? '📋'}
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <span className="font-medium">
                  {EVENT_LABELS[n.event_type] ?? n.event_type.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())}
                </span>
                {n.status === 'sent' && <CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0" />}
                {n.status === 'failed' && <XCircle className="h-4 w-4 text-red-500 shrink-0" />}
                {n.status === 'pending' && <Clock className="h-4 w-4 text-amber-500 shrink-0" />}
              </div>
              {n.subject && (
                <p className="mt-1 text-sm text-muted-foreground truncate">{n.subject}</p>
              )}
              <div className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-muted-foreground">
                <span className="inline-flex items-center gap-1">
                  {n.channel_type === 'email' ? <Mail className="h-3 w-3" /> : <MessageSquare className="h-3 w-3" />}
                  {n.channel_type}
                </span>
                {n.recipient && <span>to {n.recipient}</span>}
                {n.created_at && (
                  <span>{new Date(n.created_at).toLocaleString()}</span>
                )}
                {n.delivered_at && (
                  <span>delivered {new Date(n.delivered_at).toLocaleString()}</span>
                )}
                {n.failure_reason && (
                  <span className="text-red-500">error: {n.failure_reason}</span>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      {data && data.total > limit && (
        <div className="flex items-center justify-center gap-4">
          <button
            onClick={() => setOffset(Math.max(0, offset - limit))}
            disabled={offset === 0}
            className="rounded-md border bg-background px-4 py-2 text-sm font-medium disabled:opacity-50"
          >
            Previous
          </button>
          <span className="text-sm text-muted-foreground">
            {offset + 1}–{Math.min(offset + limit, data.total)} of {data.total}
          </span>
          <button
            onClick={() => setOffset(offset + limit)}
            disabled={offset + limit >= data.total}
            className="rounded-md border bg-background px-4 py-2 text-sm font-medium disabled:opacity-50"
          >
            Next
          </button>
        </div>
      )}
    </div>
  )
}
