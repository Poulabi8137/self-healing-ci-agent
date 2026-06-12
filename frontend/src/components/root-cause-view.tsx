import { AlertTriangle, Brain, Cpu } from 'lucide-react'

export function RootCauseView({
  rootCause,
  errorCategory,
  confidence,
  summary,
}: {
  rootCause: string | null
  errorCategory: string | null
  confidence: number | null
  summary: string | null
}) {
  if (!rootCause && !errorCategory && !summary) {
    return (
      <div className="flex flex-col items-center justify-center py-8 text-zinc-500">
        <Brain className="h-6 w-6 mb-2 opacity-40" />
        <p className="text-sm">Root cause not yet identified</p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {summary && (
        <div>
          <h4 className="text-xs font-medium text-zinc-500 uppercase tracking-wider mb-1">Summary</h4>
          <p className="text-sm text-zinc-200">{summary}</p>
        </div>
      )}

      {rootCause && (
        <div>
          <h4 className="text-xs font-medium text-zinc-500 uppercase tracking-wider mb-1 flex items-center gap-1.5">
            <AlertTriangle className="h-3 w-3 text-red-400" />
            Root Cause
          </h4>
          <p className="text-sm text-zinc-200">{rootCause}</p>
        </div>
      )}

      <div className="flex flex-wrap gap-4">
        {errorCategory && (
          <div>
            <h4 className="text-xs font-medium text-zinc-500 uppercase tracking-wider mb-1">Category</h4>
            <span className="inline-flex items-center gap-1 rounded-full bg-purple-500/10 px-2.5 py-0.5 text-xs font-medium text-purple-400">
              <Cpu className="h-3 w-3" />
              {errorCategory}
            </span>
          </div>
        )}

        {confidence != null && (
          <div>
            <h4 className="text-xs font-medium text-zinc-500 uppercase tracking-wider mb-1">Confidence</h4>
            <div className="flex items-center gap-2">
              <div className="h-2 w-24 rounded-full bg-zinc-700 overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all ${
                    confidence >= 0.7 ? 'bg-emerald-500' : confidence >= 0.4 ? 'bg-amber-500' : 'bg-red-500'
                  }`}
                  style={{ width: `${(confidence * 100).toFixed(0)}%` }}
                />
              </div>
              <span className="text-xs text-zinc-400">{(confidence * 100).toFixed(0)}%</span>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
