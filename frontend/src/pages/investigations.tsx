import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { Search, Loader2, XCircle, Activity, ArrowRight } from 'lucide-react'
import { timeAgo } from '@/lib/time'
import { RepositoryStatusBadge } from '@/components/repository-status-badge'

interface InvestigationListItem {
  id: number
  failure_id: number | null
  repository_id: number | null
  status: string
  root_cause: string | null
  error_category: string | null
  confidence: number | null
  summary: string | null
  current_stage: string | null
  current_stage_status: string | null
  created_at: string | null
  updated_at: string | null
  completed_at: string | null
}

const STATUS_FILTERS = ['all', 'detecting', 'analyzing', 'fixing', 'validating', 'completed', 'failed']

export default function Investigations() {
  const [investigations, setInvestigations] = useState<InvestigationListItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [statusFilter, setStatusFilter] = useState('all')
  const [searchTerm, setSearchTerm] = useState('')

  useEffect(() => {
    const params = new URLSearchParams()
    if (statusFilter !== 'all') params.set('status', statusFilter)
    params.set('limit', '100')
    let cancelled = false
    fetch(`/api/investigations/?${params}`, { credentials: 'include' })
      .then((r) => {
        if (!r.ok) throw new Error('Failed to load investigations')
        return r.json()
      })
      .then((data: InvestigationListItem[]) => {
        if (!cancelled) { setInvestigations(data); setLoading(false) }
      })
      .catch((err) => {
        if (!cancelled) { setError(err.message); setLoading(false) }
      })
    return () => { cancelled = true }
  }, [statusFilter])

  const filtered = investigations.filter((inv) => {
    if (!searchTerm) return true
    const term = searchTerm.toLowerCase()
    return (
      inv.root_cause?.toLowerCase().includes(term) ||
      inv.summary?.toLowerCase().includes(term) ||
      inv.error_category?.toLowerCase().includes(term) ||
      `#${inv.id}`.includes(term)
    )
  })

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold text-zinc-100">Investigations</h1>
          <p className="text-sm text-zinc-500 mt-0.5">
            Track and monitor all failure investigations
          </p>
        </div>
      </div>

      <div className="flex items-center gap-3 flex-wrap">
        <div className="relative flex-1 max-w-xs">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-500" />
          <input
            type="text"
            placeholder="Search investigations…"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full rounded-lg border border-zinc-800 bg-zinc-900/50 py-1.5 pl-8 pr-3 text-sm text-zinc-200 placeholder-zinc-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
        </div>
        <div className="flex gap-1">
          {STATUS_FILTERS.map((s) => (
            <button
              key={s}
              onClick={() => setStatusFilter(s)}
              className={`rounded-lg px-2.5 py-1.5 text-xs font-medium transition-colors capitalize ${
                statusFilter === s
                  ? 'bg-zinc-700 text-zinc-200'
                  : 'text-zinc-500 hover:text-zinc-300 hover:bg-zinc-800/50'
              }`}
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      {loading && (
        <div className="flex items-center justify-center py-16 text-zinc-500">
          <Loader2 className="h-5 w-5 animate-spin mr-2" />
          <span className="text-sm">Loading…</span>
        </div>
      )}

      {error && (
        <div className="flex flex-col items-center justify-center py-16 text-red-400">
          <XCircle className="h-6 w-6 mb-2" />
          <p className="text-sm">{error}</p>
          <button onClick={() => setStatusFilter('all')} className="mt-3 text-xs text-blue-400 hover:underline">
            Try again
          </button>
        </div>
      )}

      {!loading && !error && filtered.length === 0 && (
        <div className="flex flex-col items-center justify-center py-16 text-zinc-500">
          <Activity className="h-8 w-8 mb-2 opacity-40" />
          <p className="text-sm">No investigations found</p>
          <p className="text-xs mt-1 opacity-60">
            {statusFilter !== 'all'
              ? `No investigations with status "${statusFilter}". Try a different filter.`
              : 'Investigations will appear here when failures are detected.'}
          </p>
        </div>
      )}

      {!loading && !error && filtered.length > 0 && (
        <div className="space-y-2">
          {filtered.map((inv) => (
            <Link
              key={inv.id}
              to={`/investigations/${inv.id}`}
              className="flex items-center gap-4 rounded-lg border border-zinc-800 bg-zinc-900/30 px-4 py-3 hover:bg-zinc-800/40 transition-colors group"
            >
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-zinc-200">#{inv.id}</span>
                  <RepositoryStatusBadge status={inv.status} />
                </div>
                <div className="mt-1 flex items-center gap-3 text-xs text-zinc-500">
                  {inv.root_cause && (
                    <span className="truncate max-w-md">{inv.root_cause}</span>
                  )}
                  {inv.error_category && (
                    <span className="shrink-0 rounded bg-purple-500/10 px-1.5 py-0.5 text-purple-400">
                      {inv.error_category}
                    </span>
                  )}
                  {inv.confidence != null && (
                    <span className="shrink-0">
                      {(inv.confidence * 100).toFixed(0)}% confidence
                    </span>
                  )}
                </div>
              </div>
              <div className="flex items-center gap-3 shrink-0">
                <div className="text-right">
                  <p className="text-xs text-zinc-500">
                    {inv.created_at ? timeAgo(inv.created_at) : ''}
                  </p>
                  {inv.completed_at && (
                    <p className="text-xs text-zinc-600">
                      {timeAgo(inv.completed_at)}
                    </p>
                  )}
                </div>
                <ArrowRight className="h-4 w-4 text-zinc-600 group-hover:text-zinc-400 transition-colors" />
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}
