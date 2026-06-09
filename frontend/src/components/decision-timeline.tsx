import { Lightbulb, Target, Search, TrendingUp, RefreshCw, Activity } from 'lucide-react'
import { getDecisionEngine } from '@/lib/decision-engine'
import { timeAgo } from '@/lib/time'

const typeIcon: Record<string, typeof Lightbulb> = {
  hypothesis_evaluation: Search,
  strategy_selection: Target,
  validation_outcome: Activity,
  reassessment: RefreshCw,
  health_impact: TrendingUp,
}

const typeColor: Record<string, string> = {
  hypothesis_evaluation: 'text-purple-400',
  strategy_selection: 'text-blue-400',
  validation_outcome: 'text-violet-400',
  reassessment: 'text-orange-400',
  health_impact: 'text-emerald-400',
}

const typeLabel: Record<string, string> = {
  hypothesis_evaluation: 'Hypothesis Evaluation',
  strategy_selection: 'Strategy Selection',
  validation_outcome: 'Validation Outcome',
  reassessment: 'Reassessment',
  health_impact: 'Health Impact',
}

export function DecisionTimeline() {
  const engine = getDecisionEngine()
  const decisions = engine.getDecisions()

  if (decisions.length === 0) {
    return (
      <div className="rounded-xl border border-zinc-800 bg-zinc-900/40">
        <div className="flex items-center gap-2 border-b border-zinc-800 px-4 py-2.5">
          <TrendingUp className="h-3.5 w-3.5 text-zinc-500" />
          <h3 className="text-xs font-medium text-zinc-300">Decision Timeline</h3>
        </div>
        <div className="flex flex-col items-center justify-center py-6 px-4">
          <TrendingUp className="h-5 w-5 text-zinc-700 mb-1" />
          <p className="text-[10px] text-zinc-600 text-center">No decisions recorded yet</p>
        </div>
      </div>
    )
  }

  const sorted = [...decisions].sort(
    (a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
  )

  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900/40">
      <div className="flex items-center gap-2 border-b border-zinc-800 px-4 py-2.5">
        <TrendingUp className="h-3.5 w-3.5 text-zinc-500" />
        <h3 className="text-xs font-medium text-zinc-300">Decision Timeline</h3>
        <span className="ml-auto text-[9px] text-zinc-600">{decisions.length} decisions</span>
      </div>
      <div className="max-h-[320px] overflow-y-auto">
        {sorted.map((d) => {
          const Icon = typeIcon[d.type] ?? Lightbulb
          const color = typeColor[d.type] ?? 'text-zinc-400'
          const label = typeLabel[d.type] ?? d.type
          const confidenceDelta = ((d.confidence_after - d.confidence_before) * 100).toFixed(1)

          return (
            <div key={d.id} className="flex gap-3 border-b border-zinc-800/50 px-4 py-2.5 last:border-0">
              <div className={`mt-0.5 ${color}`}>
                <Icon className="h-3.5 w-3.5" />
              </div>
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-1.5 flex-wrap">
                  <span className="text-[10px] font-medium text-zinc-400">{label}</span>
                  <span className={`text-[9px] font-mono ${
                    Number(confidenceDelta) >= 0 ? 'text-emerald-500' : 'text-red-400'
                  }`}>
                    {(d.confidence_before * 100).toFixed(0)}% → {(d.confidence_after * 100).toFixed(0)}%
                  </span>
                </div>
                <p className="text-[10px] text-zinc-500 leading-relaxed mt-0.5">{d.outcome}</p>
                <p className="text-[9px] text-zinc-700 mt-0.5 truncate">{d.rationale.substring(0, 120)}</p>
                {d.evidence_used.length > 0 && (
                  <div className="flex gap-1 mt-0.5 flex-wrap">
                    {d.evidence_used.map((e) => (
                      <span key={e} className="text-[8px] text-zinc-700 bg-zinc-800/50 px-1 rounded">{e}</span>
                    ))}
                  </div>
                )}
                <p className="text-[8px] text-zinc-700 mt-0.5">{d.context} · {timeAgo(d.timestamp)}</p>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
