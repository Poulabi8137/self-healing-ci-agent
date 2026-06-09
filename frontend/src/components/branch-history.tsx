import { GitBranch, CheckCircle, XCircle, Search, Wrench, Activity } from 'lucide-react'
import { getDecisionEngine } from '@/lib/decision-engine'
import type { BranchNode } from '@/lib/decision-engine'

const typeIcon: Record<string, typeof GitBranch> = {
  root_cause: Search,
  strategy: Wrench,
  validation: Activity,
  resolution: CheckCircle,
  failure: XCircle,
}

const typeColor: Record<string, string> = {
  root_cause: 'text-purple-400',
  strategy: 'text-blue-400',
  validation: 'text-violet-400',
  resolution: 'text-emerald-400',
  failure: 'text-red-400',
}

const typeBg: Record<string, string> = {
  root_cause: 'bg-purple-500/10 border-purple-500/20',
  strategy: 'bg-blue-500/10 border-blue-500/20',
  validation: 'bg-violet-500/10 border-violet-500/20',
  resolution: 'bg-emerald-500/10 border-emerald-500/20',
  failure: 'bg-red-500/10 border-red-500/20',
}

function BranchNodeEntry({ node, depth = 0 }: { node: BranchNode; depth?: number }) {
  const Icon = typeIcon[node.type] ?? GitBranch
  const color = typeColor[node.type] ?? 'text-zinc-400'
  const bg = typeBg[node.type] ?? 'bg-zinc-800/30 border-zinc-700/30'

  return (
    <>
      <div className={`flex gap-2 ${depth > 0 ? 'ml-4 border-l border-zinc-800 pl-3' : ''}`}>
        <div className={`flex h-5 w-5 shrink-0 items-center justify-center rounded ${bg.replace('border-', '')}`}>
          <Icon className={`h-3 w-3 ${color}`} />
        </div>
        <div className="min-w-0 flex-1 pb-2">
          <div className="flex items-center gap-1.5 flex-wrap">
            <span className="text-[10px] font-medium text-zinc-300">{node.label.substring(0, 60)}</span>
            <span className={`text-[9px] px-1 rounded ${
              node.status === 'completed' ? 'text-emerald-400 bg-emerald-500/10' :
              node.status === 'failed' ? 'text-red-400 bg-red-500/10' :
              'text-amber-400 bg-amber-500/10'
            }`}>
              {node.status}
            </span>
          </div>
          {node.decision && (
            <div className="mt-0.5 flex items-center gap-2 text-[9px] text-zinc-500">
              <span>confidence: {(node.decision.confidence_before * 100).toFixed(0)}% → {(node.decision.confidence_after * 100).toFixed(0)}%</span>
            </div>
          )}
          {node.outcome && (
            <p className="mt-0.5 text-[9px] text-zinc-600 truncate">{node.outcome}</p>
          )}
        </div>
      </div>
      {node.children.map((child) => (
        <BranchNodeEntry key={child.id} node={child} depth={depth + 1} />
      ))}
    </>
  )
}

export function BranchHistory() {
  const engine = getDecisionEngine()
  const branches = engine.getBranches()

  if (branches.length === 0) {
    return (
      <div className="rounded-xl border border-zinc-800 bg-zinc-900/40">
        <div className="flex items-center gap-2 border-b border-zinc-800 px-4 py-2.5">
          <GitBranch className="h-3.5 w-3.5 text-zinc-500" />
          <h3 className="text-xs font-medium text-zinc-300">Branch History</h3>
        </div>
        <div className="flex flex-col items-center justify-center py-6 px-4">
          <GitBranch className="h-5 w-5 text-zinc-700 mb-1" />
          <p className="text-[10px] text-zinc-600 text-center">Run investigations to see explored branches</p>
        </div>
      </div>
    )
  }

  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900/40">
      <div className="flex items-center gap-2 border-b border-zinc-800 px-4 py-2.5">
        <GitBranch className="h-3.5 w-3.5 text-zinc-500" />
        <h3 className="text-xs font-medium text-zinc-300">Branch History</h3>
        <span className="ml-auto text-[9px] text-zinc-600">{branches.length} branches</span>
      </div>
      <div className="max-h-[320px] overflow-y-auto px-4 py-2 space-y-0">
        {branches.map((branch) => (
          <BranchNodeEntry key={branch.id} node={branch} />
        ))}
      </div>
    </div>
  )
}
