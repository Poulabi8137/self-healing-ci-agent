import { Activity } from 'lucide-react'

export function ActivityFeed() {
  return (
    <div className="rounded-xl border border-[#1f1f23] bg-[#121216]/40" role="feed" aria-label="Activity feed">
      <div className="flex items-center gap-2 border-b border-[#1f1f23] px-5 py-3">
        <Activity className="h-4 w-4 text-zinc-500" />
        <h3 className="text-sm font-medium text-zinc-300">Activity</h3>
      </div>
      <div className="flex flex-col items-center justify-center py-8 px-4">
        <Activity className="h-5 w-5 text-zinc-700 mb-2" />
        <p className="text-xs text-zinc-600 text-center">Activity feed appears when the agent detects failures</p>
        <p className="text-[10px] text-zinc-700 mt-1">Connect a repository to get started</p>
      </div>
    </div>
  )
}
