import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { RotateCw, ChevronDown, Clock, GitBranch, Activity, CheckCircle, XCircle, ArrowUpRight, Lightbulb } from 'lucide-react'
import { PageTransition } from '@/components/page-transition'
import { StaggerGrid, StaggerItem } from '@/components/stagger-grid'
import { MetricCard } from '@/components/metric-card'
import { StatusBadge } from '@/components/status-badge'
import { SpotlightCard } from '@/components/spotlight-card'
import { TiltCard } from '@/components/tilt-card'
import { EmptyState } from '@/components/empty-state'
import { StepTimeline } from '@/components/step-timeline'
import type { TimelineStep } from '@/components/step-timeline'
import { useDashboardMetrics } from '@/lib/api'
import { demoMetrics, demoRetryTimeline } from '@/lib/demo-data'
import { timeAgo } from '@/lib/time'

function recoverySteps(attempt: typeof demoRetryTimeline[number]): TimelineStep[] {
  return [
    { id: 'detect', title: 'Failure detected', description: timeAgo(attempt.timestamp), status: 'completed' },
    { id: 'diagnose', title: 'Diagnosing error', description: attempt.error_type, status: attempt.status === 'running' ? 'active' : 'completed' },
    { id: 'apply', title: 'Applying fix strategy', description: attempt.fix_strategy, status: attempt.status === 'running' ? 'pending' : 'completed' },
    { id: 'verify', title: 'Verifying recovery', description: 'Running validation checks...', status: attempt.status === 'resolved' ? 'completed' : attempt.status === 'failed' ? 'failed' : 'pending' },
  ]
}

export default function Retry() {
  const { data: _metrics } = useDashboardMetrics()
  const metrics = _metrics ?? demoMetrics
  const wm = metrics.workflow_metrics
  const totalRetries = wm?.total_retries ?? 0
  const avgRetries = metrics.average_retries ?? 0
  const [expandedId, setExpandedId] = useState<number | null>(null)
  const runningCount = demoRetryTimeline.filter(r => r.status === 'running').length
  const resolvedCount = demoRetryTimeline.filter(r => r.status === 'resolved').length

  const groupedByRun = demoRetryTimeline.reduce((acc, attempt) => {
    const key = `${attempt.repo}-${attempt.runId}`
    if (!acc[key]) acc[key] = []
    acc[key].push(attempt)
    return acc
  }, {} as Record<string, typeof demoRetryTimeline>)

  return (
    <PageTransition>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-semibold">Retry & Recovery</h1>
          <p className="text-sm text-muted-foreground">Track workflow retries and automated recovery attempts with escalating strategies</p>
        </div>

        <StaggerGrid className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <StaggerItem><MetricCard label="Total Retries" value={totalRetries} /></StaggerItem>
          <StaggerItem><MetricCard label="Avg Retries/Run" value={avgRetries} decimals={2} /></StaggerItem>
          <StaggerItem>
            <MetricCard label="Resolved" value={resolvedCount} />
          </StaggerItem>
          <StaggerItem>
            <MetricCard label="In Progress" value={runningCount} />
          </StaggerItem>
        </StaggerGrid>

        {totalRetries === 0 ? (
          <div className="flex items-center justify-center rounded-xl border border-border bg-card py-16">
            <EmptyState icon={RotateCw} title="No retry data available yet" description="Retry data appears when workflows are automatically retried" />
          </div>
        ) : (
          <div className="grid gap-6 lg:grid-cols-[1fr_320px]">
            <div className="space-y-3">
              <h2 className="text-sm font-medium text-muted-foreground">Recent Recovery Attempts</h2>
              {demoRetryTimeline.slice(0, 10).map((attempt) => {
                const isRunning = attempt.status === 'running'
                const groupKey = `${attempt.repo}-${attempt.runId}`
                const siblings = groupedByRun[groupKey] || []
                const groupIndex = siblings.indexOf(attempt)
                const showEscalation = groupIndex > 0 && siblings[groupIndex - 1].status === 'failed'
                return (
                  <motion.div key={attempt.id} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.2 }}>
                    <TiltCard>
                      <SpotlightCard className="p-4">
                        <button onClick={() => setExpandedId(expandedId === attempt.id ? null : attempt.id)} className="flex w-full items-center justify-between">
                          <div className="flex items-center gap-3">
                            <div className={`flex h-8 w-8 items-center justify-center rounded-lg ${attempt.status === 'resolved' ? 'bg-emerald-500/10' : attempt.status === 'running' ? 'bg-amber-500/10' : 'bg-red-500/10'}`}>
                              {attempt.status === 'resolved' ? <CheckCircle className="h-4 w-4 text-emerald-500" /> : attempt.status === 'running' ? <Activity className="h-4 w-4 text-amber-500" /> : <XCircle className="h-4 w-4 text-red-500" />}
                            </div>
                            <div className="text-left">
                              <p className="text-sm font-medium text-foreground">{attempt.repo}</p>
                              <p className="text-xs text-muted-foreground">Run #{attempt.runId} · Attempt {attempt.attempt} · {timeAgo(attempt.timestamp)}</p>
                            </div>
                          </div>
                          <div className="flex items-center gap-3">
                            {showEscalation && (
                              <div className="flex items-center gap-1 text-[10px] text-orange-400">
                                <ArrowUpRight className="h-3 w-3" />
                                Escalated
                              </div>
                            )}
                            <StatusBadge status={attempt.status === 'resolved' ? 'passed' : attempt.status === 'running' ? 'running' : 'failed'} animated={isRunning} />
                            <ChevronDown className={`h-4 w-4 text-muted-foreground transition-transform ${expandedId === attempt.id ? 'rotate-180' : ''}`} />
                          </div>
                        </button>
                        <AnimatePresence>
                          {expandedId === attempt.id && (
                            <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }} transition={{ duration: 0.2 }} className="overflow-hidden">
                              <div className="mt-3 space-y-3">
                                {showEscalation && (
                                  <div className="rounded-lg border border-orange-500/20 bg-orange-500/5 p-2.5">
                                    <div className="flex items-center gap-1.5 mb-1">
                                      <Lightbulb className="h-3 w-3 text-orange-400" />
                                      <span className="text-[10px] font-medium text-orange-400">Strategy escalation</span>
                                    </div>
                                    <p className="text-[10px] text-muted-foreground">
                                      Previous attempt failed — applying {groupIndex === 1 ? 'escalated' : 'further escalated'} strategy: {attempt.fix_strategy}
                                    </p>
                                  </div>
                                )}
                                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                                  <Clock className="h-3 w-3" />
                                  <span>Duration: {attempt.duration_seconds > 0 ? `${attempt.duration_seconds}s` : 'In progress...'}</span>
                                </div>
                                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                                  <GitBranch className="h-3 w-3" />
                                  <span>Error: {attempt.error_type}</span>
                                </div>
                                {attempt.fix_strategy && (
                                  <p className="text-xs text-muted-foreground">Strategy: {attempt.fix_strategy}</p>
                                )}
                                <div className="border-t border-border pt-3">
                                  <p className="text-[10px] font-medium text-muted-foreground mb-2">Recovery Timeline</p>
                                  <StepTimeline steps={recoverySteps(attempt)} autoProgress={false} />
                                </div>
                              </div>
                            </motion.div>
                          )}
                        </AnimatePresence>
                      </SpotlightCard>
                    </TiltCard>
                  </motion.div>
                )
              })}
            </div>
            <div className="hidden lg:block">
              <div className="sticky top-20">
                <SpotlightCard className="p-4">
                  <div className="mb-3 flex items-center gap-2">
                    <Activity className="h-3.5 w-3.5 text-zinc-500" />
                    <span className="text-[11px] font-medium text-zinc-600 tracking-wider uppercase">Recovery Summary</span>
                  </div>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-muted-foreground">Active recoveries</span>
                      <span className="font-mono text-amber-400">{runningCount}</span>
                    </div>
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-muted-foreground">Successfully resolved</span>
                      <span className="font-mono text-emerald-400">{resolvedCount}</span>
                    </div>
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-muted-foreground">Failed</span>
                      <span className="font-mono text-red-400">{demoRetryTimeline.filter(r => r.status === 'failed').length}</span>
                    </div>
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-muted-foreground">Escalated strategies</span>
                      <span className="font-mono text-orange-400">{demoRetryTimeline.filter(a => a.attempt > 1).length}</span>
                    </div>
                    <div className="pt-2 border-t border-border">
                      <div className="flex h-2 w-full rounded-full overflow-hidden bg-zinc-800">
                        {['resolved', 'running', 'failed'].map((status) => {
                          const count = demoRetryTimeline.filter(r => r.status === status).length
                          const pct = (count / demoRetryTimeline.length) * 100
                          return pct > 0 ? (
                            <div
                              key={status}
                              className={`h-full ${status === 'resolved' ? 'bg-emerald-500/60' : status === 'running' ? 'bg-amber-500/60' : 'bg-red-500/60'}`}
                              style={{ width: `${pct}%` }}
                            />
                          ) : null
                        })}
                      </div>
                    </div>
                    <div className="pt-2 border-t border-border">
                      <p className="text-[10px] font-medium text-muted-foreground mb-1">Escalation Paths</p>
                      {Object.entries(groupedByRun).slice(0, 4).map(([key, attempts]) => (
                        <div key={key} className="mb-2">
                          <p className="text-[10px] text-muted-foreground mb-0.5">{attempts[0].repo} · Run #{attempts[0].runId}</p>
                          <div className="flex gap-1">
                            {attempts.map((a, i) => (
                              <div
                                key={a.id}
                                className={`flex-1 h-1.5 rounded-full ${
                                  a.status === 'resolved' ? 'bg-emerald-500/60' :
                                  a.status === 'running' ? 'bg-amber-500/60' : 'bg-red-500/60'
                                } ${i > 0 && attempts[i-1].status === 'failed' ? 'ring-1 ring-orange-500/30' : ''}`}
                              />
                            ))}
                          </div>
                          <div className="flex gap-1 mt-0.5">
                            {attempts.map((a) => (
                              <span key={a.id} className="flex-1 text-[8px] text-muted-foreground text-center">{a.attempt}</span>
                            ))}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </SpotlightCard>
              </div>
            </div>
          </div>
        )}
      </div>
    </PageTransition>
  )
}
