import { useState, useEffect } from 'react'
import { GitPullRequest, ExternalLink, Loader2, XCircle } from 'lucide-react'

interface PullRequestRecord {
  id: number | null
  investigation_id: number
  pr_number: number | null
  pr_url: string | null
  title: string | null
  description: string | null
  branch_name: string | null
  status: string | null
  dry_run: boolean
  created_at: string | null
}

export function PullRequestView({
  investigationId,
}: {
  investigationId: number
}) {
  const [pr, setPr] = useState<PullRequestRecord | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    fetch(`/api/investigations/${investigationId}/pull-request`, { credentials: 'include' })
      .then((r) => {
        if (!r.ok) throw new Error('Failed to load pull request')
        return r.json()
      })
      .then((data: PullRequestRecord) => {
        if (!cancelled) { setPr(data); setLoading(false) }
      })
      .catch((err) => {
        if (!cancelled) { setError(err.message); setLoading(false) }
      })
    return () => { cancelled = true }
  }, [investigationId])

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8 text-zinc-500">
        <Loader2 className="h-5 w-5 animate-spin mr-2" />
        <span className="text-sm">Loading pull request…</span>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-8 text-red-400">
        <XCircle className="h-6 w-6 mb-2" />
        <p className="text-sm">{error}</p>
      </div>
    )
  }

  if (!pr || !pr.id) {
    return (
      <div className="flex flex-col items-center justify-center py-8 text-zinc-500">
        <GitPullRequest className="h-6 w-6 mb-2 opacity-40" />
        <p className="text-sm">Pull request not yet created</p>
      </div>
    )
  }

  const isCreated = pr.status === 'created'

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <GitPullRequest className={`h-5 w-5 ${isCreated ? 'text-emerald-400' : 'text-zinc-400'}`} />
        <div>
          <h3 className="text-sm font-semibold text-zinc-100">{pr.title}</h3>
          <div className="flex items-center gap-2 mt-0.5">
            <span
              className={`text-xs font-medium px-1.5 py-0.5 rounded ${
                isCreated
                  ? 'bg-emerald-500/10 text-emerald-400'
                  : pr.status === 'blocked'
                    ? 'bg-amber-500/10 text-amber-400'
                    : pr.status === 'failed'
                      ? 'bg-red-500/10 text-red-400'
                      : 'bg-zinc-700 text-zinc-300'
              }`}
            >
              {pr.status}
            </span>
            {pr.dry_run && (
              <span className="text-xs font-medium text-amber-500">Dry Run</span>
            )}
          </div>
        </div>
      </div>

      {pr.branch_name && (
        <div className="flex items-center gap-2">
          <span className="text-xs text-zinc-500">Branch:</span>
          <code className="text-xs font-mono text-zinc-300 bg-zinc-800 px-1.5 py-0.5 rounded">{pr.branch_name}</code>
        </div>
      )}

      {pr.pr_url && (
        <a
          href={pr.pr_url}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1.5 text-xs text-blue-400 hover:text-blue-300 transition-colors"
        >
          <ExternalLink className="h-3 w-3" />
          View on GitHub {pr.pr_number ? `(#${pr.pr_number})` : ''}
        </a>
      )}

      {pr.description && (
        <div className="rounded-lg border border-zinc-800 bg-zinc-900/30 p-3">
          <pre className="text-xs text-zinc-300 whitespace-pre-wrap font-sans leading-relaxed">
            {pr.description}
          </pre>
        </div>
      )}

      {pr.created_at && (
        <p className="text-xs text-zinc-500">
          Created {new Date(pr.created_at).toLocaleString()}
        </p>
      )}
    </div>
  )
}
