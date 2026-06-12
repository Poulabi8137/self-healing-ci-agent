import { useEffect, useRef, useState, useCallback } from 'react'

export interface SseEvent {
  id: number
  investigation_id: number | null
  event_type: string
  data: Record<string, unknown>
  created_at: string
}

const EVENT_TYPES = [
  'failure_detected',
  'investigation_started',
  'logs_collected',
  'root_cause_identified',
  'fix_generated',
  'validation_started',
  'validation_completed',
  'pr_created',
  'repository_status_changed',
] as const

export type EventType = (typeof EVENT_TYPES)[number]

export function useEventStream(enabled = true) {
  const [events, setEvents] = useState<SseEvent[]>([])
  const [connected, setConnected] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const esRef = useRef<EventSource | null>(null)
  const MAX_EVENTS = 100

  const backfill = useCallback(async (since?: string) => {
    try {
      const params = new URLSearchParams()
      if (since) params.set('since', since)
      params.set('limit', '50')
      const res = await fetch(`/api/events/history?${params}`, { credentials: 'include' })
      if (!res.ok) return
      const data: SseEvent[] = await res.json()
      if (data.length > 0) {
        setEvents((prev) => {
          const existingIds = new Set(prev.map((e) => e.id))
          const newEvents = data.filter((e) => !existingIds.has(e.id))
          return [...newEvents, ...prev].slice(0, MAX_EVENTS)
        })
      }
    } catch {
      // silent — backfill is best-effort
    }
  }, [])

  useEffect(() => {
    if (!enabled) return

    const url = `/api/events/stream`
    const es = new EventSource(url, { withCredentials: true })
    esRef.current = es

    es.onopen = () => {
      setConnected(true)
      setError(null)
      backfill()
    }

    for (const et of EVENT_TYPES) {
      es.addEventListener(et, (event: MessageEvent) => {
        try {
          const parsed: SseEvent = JSON.parse(event.data)
          setEvents((prev) => {
            if (prev.some((e) => e.id === parsed.id)) return prev
            return [parsed, ...prev].slice(0, MAX_EVENTS)
          })
        } catch {
          // skip malformed events
        }
      })
    }

    es.addEventListener('connected', () => {
      // initial connection event — no action needed
    })

    es.onerror = () => {
      setConnected(false)
      if (es.readyState === EventSource.CLOSED) {
        setError('Connection lost. Reconnecting...')
      }
    }

    return () => {
      es.close()
      esRef.current = null
      setConnected(false)
    }
  }, [enabled, backfill])

  const clear = useCallback(() => setEvents([]), [])
  const getByInvestigation = useCallback(
    (investigationId: number) => events.filter((e) => e.investigation_id === investigationId),
    [events],
  )

  return { events, connected, error, clear, getByInvestigation }
}
