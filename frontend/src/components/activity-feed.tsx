import { Link } from 'react-router-dom'
import { Activity, GitPullRequest, AlertTriangle, CheckCircle, RotateCw, Wrench, Users, Lightbulb, TrendingUp, Search, Target, RefreshCw, ArrowUpRight } from 'lucide-react'
import type { ActivityItem } from '@/lib/types'
import { demoActivities } from '@/lib/demo-data'
import { timeAgo } from '@/lib/time'

const iconMap: Record<ActivityItem['type'], typeof Activity> = {
  workflow_run: Activity,
  failure_detected: AlertTriangle,
  fix_generated: Wrench,
  pr_created: GitPullRequest,
  validation_passed: CheckCircle,
  validation_failed: AlertTriangle,
  retry_attempted: RotateCw,
  auto_resolved: CheckCircle,
  human_resolved: Users,
  decision_made: Lightbulb,
  strategy_selected: Target,
  hypothesis_evaluated: Search,
  confidence_changed: TrendingUp,
  reassessment: RefreshCw,
  escalation: AlertTriangle,
  health_impact: ArrowUpRight,
}

const itemLink: Record<ActivityItem['type'], string> = {
  workflow_run: '/dashboard',
  failure_detected: '/analysis',
  fix_generated: '/analysis',
  pr_created: '/pr',
  validation_passed: '/validation',
  validation_failed: '/validation',
  retry_attempted: '/retry',
  auto_resolved: '/dashboard',
  human_resolved: '/dashboard',
  decision_made: '/analysis',
  strategy_selected: '/analysis',
  hypothesis_evaluated: '/analysis',
  confidence_changed: '/dashboard',
  reassessment: '/validation',
  escalation: '/validation',
  health_impact: '/dashboard',
}

export function ActivityFeed({ items }: { items?: ActivityItem[] }) {
  const activities = (items ?? demoActivities).slice(0, 20)

  if (activities.length === 0) {
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

  return (
    <div className="rounded-xl border border-[#1f1f23] bg-[#121216]/40" role="feed" aria-label="Activity feed">
      <div className="flex items-center gap-2 border-b border-[#1f1f23] px-5 py-3">
        <Activity className="h-4 w-4 text-zinc-500" />
        <h3 className="text-sm font-medium text-zinc-300">Activity</h3>
        <span className="ml-auto text-[10px] text-zinc-600">{activities.length} events</span>
      </div>
      <div className="max-h-[420px] overflow-y-auto">
        {activities.map((item) => {
          const Icon = iconMap[item.type] ?? Activity
          const statusColor =
            item.status === 'success' ? 'text-emerald-500' :
            item.status === 'failure' ? 'text-red-500' :
            item.status === 'pending' ? 'text-amber-500' :
            'text-blue-500'
          return (
            <Link
              key={item.id}
              to={itemLink[item.type] ?? '/dashboard'}
              className="flex gap-3 border-b border-[#1f1f23]/50 px-5 py-2.5 last:border-0 hover:bg-[#1f1f23]/30 transition-colors"
            >
              <div className={`mt-0.5 ${statusColor}`}>
                <Icon className="h-3.5 w-3.5" />
              </div>
              <div className="min-w-0 flex-1">
                <p className="text-xs text-zinc-300 leading-relaxed">{item.message}</p>
                <p className="mt-0.5 text-[10px] text-zinc-600">
                  {item.repo} · {timeAgo(item.timestamp)}
                </p>
              </div>
            </Link>
          )
        })}
      </div>
    </div>
  )
}
