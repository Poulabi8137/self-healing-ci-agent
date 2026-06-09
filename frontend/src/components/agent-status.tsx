import { useAgent } from '@/lib/agent-context'

const COLORS = {
  emerald: { label: 'text-emerald-400', dot: 'bg-emerald-500' },
  amber: { label: 'text-amber-400', dot: 'bg-amber-500' },
  blue: { label: 'text-blue-400', dot: 'bg-blue-500' },
  violet: { label: 'text-violet-400', dot: 'bg-violet-500' },
  zinc: { label: 'text-zinc-400', dot: 'bg-zinc-500' },
  red: { label: 'text-red-400', dot: 'bg-red-500' },
  orange: { label: 'text-orange-400', dot: 'bg-orange-500' },
  purple: { label: 'text-purple-400', dot: 'bg-purple-500' },
  cyan: { label: 'text-cyan-400', dot: 'bg-cyan-500' },
}

export function AgentStatus() {
  const { state } = useAgent()
  const c = COLORS[state.color]

  return (
    <span className="hidden sm:inline-flex items-center gap-1.5 rounded-md border border-zinc-800 bg-zinc-900/50 px-2 py-1">
      <span className="relative flex h-2 w-2">
        <span className={`absolute inline-flex h-full w-full animate-ping rounded-full ${c.dot} opacity-40`} />
        <span className={`relative inline-flex h-2 w-2 rounded-full ${c.dot}`} />
      </span>
      <span className={`text-[10px] font-medium ${c.label}`}>{state.label}</span>
      {state.context && <span className="text-[10px] text-zinc-600 hidden xl:inline">· {state.context}</span>}
    </span>
  )
}
