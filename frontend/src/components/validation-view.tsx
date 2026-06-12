import { useState, useEffect } from 'react'
import { Beaker, CheckCircle, XCircle, Loader2 } from 'lucide-react'

interface ValidationStageResult {
  id: number
  investigation_id: number
  validation_type: string
  status: string
  started_at: string | null
  completed_at: string | null
  duration_ms: number | null
  logs: string[]
  metadata: Record<string, unknown>
  confidence_score: number | null
  created_at: string | null
}

export function ValidationView({
  investigationId,
}: {
  investigationId: number
}) {
  const [stages, setStages] = useState<ValidationStageResult[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    fetch(`/api/investigations/${investigationId}/validations`, { credentials: 'include' })
      .then((r) => {
        if (!r.ok) throw new Error('Failed to load validation results')
        return r.json()
      })
      .then((data: ValidationStageResult[]) => {
        if (!cancelled) { setStages(data); setLoading(false) }
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
        <span className="text-sm">Loading validation results…</span>
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

  if (stages.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-8 text-zinc-500">
        <Beaker className="h-6 w-6 mb-2 opacity-40" />
        <p className="text-sm">Validation not yet run</p>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {stages.map((stage) => {
        const passed = stage.status === 'passed'
        return (
          <div key={stage.id} className="rounded-lg border border-zinc-800 bg-zinc-900/30 p-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                {passed
                  ? <CheckCircle className="h-4 w-4 text-emerald-500" />
                  : <XCircle className="h-4 w-4 text-red-500" />
                }
                <span className="text-sm font-medium text-zinc-200 capitalize">
                  {stage.validation_type.replace(/_/g, ' ')}
                </span>
              </div>
              <div className="flex items-center gap-3">
                {stage.duration_ms != null && (
                  <span className="text-xs text-zinc-500">{(stage.duration_ms / 1000).toFixed(1)}s</span>
                )}
                <span className={`text-xs font-medium ${passed ? 'text-emerald-400' : 'text-red-400'}`}>
                  {passed ? 'Passed' : 'Failed'}
                </span>
              </div>
            </div>

            {stage.confidence_score != null && (
              <div className="mt-2 flex items-center gap-2">
                <span className="text-xs text-zinc-500">Confidence:</span>
                <div className="h-1.5 w-20 rounded-full bg-zinc-700 overflow-hidden">
                  <div
                    className={`h-full rounded-full ${stage.confidence_score >= 0.7 ? 'bg-emerald-500' : stage.confidence_score >= 0.4 ? 'bg-amber-500' : 'bg-red-500'}`}
                    style={{ width: `${(stage.confidence_score * 100).toFixed(0)}%` }}
                  />
                </div>
                <span className="text-xs text-zinc-400">{(stage.confidence_score * 100).toFixed(0)}%</span>
              </div>
            )}

            {stage.logs && stage.logs.length > 0 && (
              <div className="mt-2 max-h-24 overflow-y-auto rounded bg-zinc-950 p-2 font-mono text-xs text-zinc-400 border border-zinc-800 space-y-0.5">
                {stage.logs.map((line, i) => (
                  <div key={i}>{line}</div>
                ))}
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}
