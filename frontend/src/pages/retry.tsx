import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { RotateCw, ChevronDown, Clock, GitBranch } from 'lucide-react'
import { PageTransition } from '@/components/page-transition'
import { StaggerGrid, StaggerItem } from '@/components/stagger-grid'
import { MetricCard } from '@/components/metric-card'
import { StatusBadge } from '@/components/status-badge'
import { SpotlightCard } from '@/components/spotlight-card'
import { TiltCard } from '@/components/tilt-card'
import { EmptyState } from '@/components/empty-state'
import { useDashboardMetrics } from '@/lib/api'
import { demoMetrics, demoRetryTimeline } from '@/lib/demo-data'

export default function Retry() {
  const { data: _metrics } = useDashboardMetrics()
  const metrics = _metrics ?? demoMetrics
  const wm = metrics.workflow_metrics
  const totalRetries = wm?.total_retries ?? 0
  const avgRetries = metrics.average_retries ?? 0
  const [expandedId, setExpandedId] = useState<number | null>(null)

  return (
    <PageTransition>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-semibold">Retry History</h1>
          <p className="text-sm text-muted-foreground">Track workflow retries and recovery attempts</p>
        </div>

        <StaggerGrid className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <StaggerItem><MetricCard label="Total Retries" value={totalRetries} /></StaggerItem>
          <StaggerItem><MetricCard label="Avg Retries/Run" value={avgRetries} decimals={2} /></StaggerItem>
          <StaggerItem>
            <MetricCard
              label="Recovery Rate"
              value={totalRetries > 0 ? Math.min(100, Math.round((demoRetryTimeline.filter(r => r.status === 'resolved').length / demoRetryTimeline.length) * 100)) : 0}
              suffix="%"
            />
          </StaggerItem>
        </StaggerGrid>

        {totalRetries === 0 ? (
          <div className="flex items-center justify-center rounded-xl border border-border bg-card py-16">
            <EmptyState
              icon={RotateCw}
              title="No retry data available yet"
              description="Retry data appears when workflows are automatically retried"
            />
          </div>
        ) : (
          <div className="space-y-3">
            <h2 className="text-sm font-medium text-muted-foreground">Recent Retry Attempts</h2>
            {demoRetryTimeline.slice(0, 10).map((attempt) => (
              <motion.div
                key={attempt.id}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.2 }}
              >
                <TiltCard>
                  <SpotlightCard className="p-4">
                    <button
                      onClick={() => setExpandedId(expandedId === attempt.id ? null : attempt.id)}
                      className="flex w-full items-center justify-between"
                    >
                      <div className="flex items-center gap-3">
                        <div className={`flex h-8 w-8 items-center justify-center rounded-lg ${
                          attempt.status === 'resolved' ? 'bg-emerald-500/10' :
                          attempt.status === 'running' ? 'bg-amber-500/10' : 'bg-red-500/10'
                        }`}>
                          <RotateCw className={`h-4 w-4 ${
                            attempt.status === 'resolved' ? 'text-emerald-500' :
                            attempt.status === 'running' ? 'text-amber-500' : 'text-red-500'
                          }`} />
                        </div>
                        <div className="text-left">
                          <p className="text-sm font-medium text-foreground">{attempt.repo}</p>
                          <p className="text-xs text-muted-foreground">Run #{attempt.runId} · Attempt {attempt.attempt}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-3">
                        <StatusBadge status={attempt.status === 'resolved' ? 'passed' : attempt.status === 'running' ? 'running' : 'failed'} animated={false} />
                        <ChevronDown className={`h-4 w-4 text-muted-foreground transition-transform ${expandedId === attempt.id ? 'rotate-180' : ''}`} />
                      </div>
                    </button>
                    <AnimatePresence>
                      {expandedId === attempt.id && (
                        <motion.div
                          initial={{ height: 0, opacity: 0 }}
                          animate={{ height: 'auto', opacity: 1 }}
                          exit={{ height: 0, opacity: 0 }}
                          transition={{ duration: 0.2 }}
                          className="overflow-hidden"
                        >
                          <div className="mt-3 border-t border-border pt-3 space-y-2">
                            <div className="flex items-center gap-2 text-xs text-muted-foreground">
                              <Clock className="h-3 w-3" />
                              <span>Duration: {attempt.duration_seconds > 0 ? `${attempt.duration_seconds}s` : 'In progress...'}</span>
                            </div>
                            <div className="flex items-center gap-2 text-xs text-muted-foreground">
                              <GitBranch className="h-3 w-3" />
                              <span>Error: {attempt.error_type}</span>
                            </div>
                            {attempt.fix_strategy && (
                              <p className="text-xs text-muted-foreground mt-1">
                                Strategy: {attempt.fix_strategy}
                              </p>
                            )}
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </SpotlightCard>
                </TiltCard>
              </motion.div>
            ))}
          </div>
        )}
      </div>
    </PageTransition>
  )
}
