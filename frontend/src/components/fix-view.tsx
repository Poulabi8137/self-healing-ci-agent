import { useState, useEffect } from 'react'
import { Wrench, FileCode, ChevronDown, ChevronRight, Loader2, XCircle, Clock } from 'lucide-react'

interface FixArtifact {
  id: number | null
  investigation_id: number
  fix_summary: string | null
  root_cause: string | null
  confidence_score: number | null
  files_modified: string[]
  patch_content: string | null
  branch_name: string | null
  dry_run: boolean
  status: string | null
  generated_at: string | null
  applied_at: string | null
}

export function FixView({
  investigationId,
}: {
  investigationId: number
}) {
  const [artifact, setArtifact] = useState<FixArtifact | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showPatch, setShowPatch] = useState(false)

  useEffect(() => {
    let cancelled = false
    fetch(`/api/investigations/${investigationId}/fix`, { credentials: 'include' })
      .then((r) => {
        if (!r.ok) throw new Error('Failed to load fix artifact')
        return r.json()
      })
      .then((data: FixArtifact) => {
        if (!cancelled) { setArtifact(data); setLoading(false) }
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
        <span className="text-sm">Loading fix artifact…</span>
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

  const hasData = artifact && artifact.fix_summary

  if (!hasData) {
    return (
      <div className="flex flex-col items-center justify-center py-8 text-zinc-500">
        <Wrench className="h-6 w-6 mb-2 opacity-40" />
        <p className="text-sm">Fix not yet generated</p>
      </div>
    )
  }

  const isApplied = artifact.status === 'applied'
  const confidence = artifact.confidence_score

  return (
    <div className="space-y-4">
      {artifact.fix_summary && (
        <div>
          <h4 className="text-xs font-medium text-zinc-500 uppercase tracking-wider mb-1">Fix Summary</h4>
          <p className="text-sm text-zinc-200">{artifact.fix_summary}</p>
        </div>
      )}

      {artifact.root_cause && (
        <div>
          <h4 className="text-xs font-medium text-zinc-500 uppercase tracking-wider mb-1">Root Cause</h4>
          <p className="text-sm text-zinc-300">{artifact.root_cause}</p>
        </div>
      )}

      {artifact.files_modified.length > 0 && (
        <div>
          <h4 className="text-xs font-medium text-zinc-500 uppercase tracking-wider mb-1">Files Modified</h4>
          <div className="space-y-1">
            {artifact.files_modified.map((f) => (
              <div key={f} className="flex items-center gap-2 text-sm text-zinc-300">
                <FileCode className="h-3.5 w-3.5 text-blue-400 shrink-0" />
                <span className="font-mono text-xs">{f}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {artifact.patch_content && (
        <div>
          <button
            onClick={() => setShowPatch(!showPatch)}
            className="flex items-center gap-1 text-xs font-medium text-zinc-400 hover:text-zinc-200 transition-colors"
          >
            {showPatch ? <ChevronDown className="h-3 w-3" /> : <ChevronRight className="h-3 w-3" />}
            View Patch
          </button>
          {showPatch && (
            <pre className="mt-2 overflow-x-auto rounded-lg bg-zinc-900 p-3 text-xs text-zinc-300 font-mono leading-relaxed border border-zinc-800 max-h-80 overflow-y-auto">
              {artifact.patch_content}
            </pre>
          )}
        </div>
      )}

      <div className="flex flex-wrap items-center gap-4">
        {confidence != null && (
          <div className="flex items-center gap-1.5">
            <span className="text-xs text-zinc-500">Confidence:</span>
            <span
              className={`text-xs font-medium ${
                confidence >= 0.7 ? 'text-emerald-400' : confidence >= 0.4 ? 'text-amber-400' : 'text-red-400'
              }`}
            >
              {(confidence * 100).toFixed(0)}%
            </span>
          </div>
        )}

        {artifact.status && (
          <div className="flex items-center gap-1.5">
            <span className="text-xs text-zinc-500">Status:</span>
            <span
              className={`text-xs font-medium ${
                isApplied ? 'text-emerald-400' : 'text-amber-400'
              }`}
            >
              {artifact.status}
            </span>
          </div>
        )}

        {artifact.dry_run && (
          <span className="text-xs font-medium text-amber-500">Dry Run</span>
        )}

        {artifact.branch_name && (
          <div className="flex items-center gap-1.5">
            <span className="text-xs text-zinc-500">Branch:</span>
            <span className="text-xs font-mono text-zinc-300">{artifact.branch_name}</span>
          </div>
        )}
      </div>

      {artifact.generated_at && (
        <div className="flex items-center gap-1.5 text-xs text-zinc-500">
          <Clock className="h-3 w-3" />
          <span>
            Generated {new Date(artifact.generated_at).toLocaleString()}
            {artifact.applied_at && ` · Applied ${new Date(artifact.applied_at).toLocaleString()}`}
          </span>
        </div>
      )}
    </div>
  )
}
