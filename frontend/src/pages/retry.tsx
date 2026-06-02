import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Tooltip, ResponsiveContainer, PieChart, Pie, Cell,
} from 'recharts'
import { RotateCw, Clock, ArrowRight } from 'lucide-react'
import { PageTransition } from '@/components/page-transition'
import { StaggerGrid, StaggerItem } from '@/components/stagger-grid'
import { SpotlightCard } from '@/components/spotlight-card'
import { TiltCard } from '@/components/tilt-card'
import { MetricCard } from '@/components/metric-card'
import { StatusBadge } from '@/components/status-badge'
import { useDashboardMetrics } from '@/lib/api'
import { tabContentVariants, safeTransition, duration } from '@/lib/motion'

interface RetryEvent {
  id: string
  attempt: number
  workflow: string
  status: 'success' | 'failure' | 'running' | 'pending'
  reason: string
  duration: string
  timestamp: string
}

const retryHistory: RetryEvent[] = [
  { id: '1', attempt: 1, workflow: 'Build & Test', status: 'failure', reason: 'Dependency resolution timeout', duration: '3m 12s', timestamp: '2m ago' },
  { id: '2', attempt: 2, workflow: 'Build & Test', status: 'failure', reason: 'Test flakiness (NetworkError)', duration: '4m 05s', timestamp: '8m ago' },
  { id: '3', attempt: 3, workflow: 'Build & Test', status: 'success', reason: 'Clean install resolved deps', duration: '3m 48s', timestamp: '15m ago' },
  { id: '4', attempt: 1, workflow: 'Lint & Format', status: 'success', reason: '', duration: '1m 22s', timestamp: '22m ago' },
  { id: '5', attempt: 1, workflow: 'Integration Tests', status: 'failure', reason: 'API contract mismatch', duration: '8m 15s', timestamp: '35m ago' },
  { id: '6', attempt: 2, workflow: 'Integration Tests', status: 'running', reason: '', duration: '—', timestamp: '42m ago' },
]

const pieData = [
  { name: 'Successful', value: 65 },
  { name: 'Failed', value: 20 },
  { name: 'Running', value: 15 },
]

const pieColors = ['#22c55e', '#ef4444', '#3b82f6']

function Timeline({ events }: { events: RetryEvent[] }) {
  const [expanded, setExpanded] = useState<string | null>(null)

  return (
    <div className="relative pl-8 before:absolute before:left-[15px] before:top-2 before:h-[calc(100%-16px)] before:w-0.5 before:bg-border">
      <AnimatePresence>
        {events.map((event, i) => {

          return (
            <motion.div
              key={event.id}
              initial={{ opacity: 0, x: -12 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.05, duration: 0.25 }}
              className="relative mb-4"
            >
              <div className={`absolute -left-8 top-1.5 h-3.5 w-3.5 rounded-full border-2 ${
                event.status === 'success' ? 'border-emerald-500 bg-emerald-500/20' :
                event.status === 'failure' ? 'border-red-500 bg-red-500/20' :
                event.status === 'running' ? 'border-blue-500 bg-blue-500/20 animate-pulse' :
                'border-muted-foreground bg-muted'
              }`} />
              <TiltCard>
                <SpotlightCard className="p-4">
                  <button
                    onClick={() => setExpanded(expanded === event.id ? null : event.id)}
                    className="flex w-full items-center justify-between"
                  >
                    <div className="flex items-center gap-3">
                      <span className="flex h-6 w-6 items-center justify-center rounded-full bg-muted text-[10px] font-mono font-medium">
                        #{event.attempt}
                      </span>
                      <div className="text-left">
                        <p className="text-sm font-medium">{event.workflow}</p>
                        <p className="text-[11px] text-muted-foreground">{event.timestamp}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <StatusBadge status={event.status} animated={false} />
                      <ArrowRight className={`h-3 w-3 text-muted-foreground transition-transform ${expanded === event.id ? 'rotate-90' : ''}`} />
                    </div>
                  </button>
                  {expanded === event.id && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      transition={{ duration: 0.2 }}
                      className="mt-3 border-t border-border pt-3"
                    >
                      <div className="grid grid-cols-2 gap-3 text-xs">
                        <div>
                          <span className="text-muted-foreground">Duration</span>
                          <p className="font-mono font-medium">{event.duration}</p>
                        </div>
                        {event.reason && (
                          <div className="col-span-2">
                            <span className="text-muted-foreground">Reason</span>
                            <p className="font-medium text-red-400">{event.reason}</p>
                          </div>
                        )}
                      </div>
                    </motion.div>
                  )}
                </SpotlightCard>
              </TiltCard>
            </motion.div>
          )
        })}
      </AnimatePresence>
    </div>
  )
}

export default function Retry() {
  const { data: metrics } = useDashboardMetrics()
  const wm = metrics?.workflow_metrics
  const totalRetries = wm?.total_retries ?? 42
  const avgRetries = metrics?.average_retries ?? 1.8

  return (
    <PageTransition>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold">Retry</h1>
            <p className="text-sm text-muted-foreground">Self-healing retry loop</p>
          </div>
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <RotateCw className="h-3.5 w-3.5 text-blue-500" />
            <span>Auto-retry enabled</span>
          </div>
        </div>

        <StaggerGrid className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <StaggerItem><MetricCard label="Total Retries" value={totalRetries} /></StaggerItem>
          <StaggerItem><MetricCard label="Avg Retries/Run" value={avgRetries} decimals={2} /></StaggerItem>
          <StaggerItem><MetricCard label="Recovery Rate" value={78} suffix="%" /></StaggerItem>
          <StaggerItem><MetricCard label="Active Retries" value={3} trend={{ value: 15, positive: false }} /></StaggerItem>
        </StaggerGrid>

        <div className="grid gap-6 lg:grid-cols-[1fr_340px]">
          <motion.div
            variants={tabContentVariants}
            initial="initial"
            animate="animate"
            transition={safeTransition({ duration: duration.normal })}
          >
            <TiltCard>
              <SpotlightCard className="p-5">
                <div className="mb-4 flex items-center gap-2">
                  <Clock className="h-4 w-4 text-muted-foreground" />
                  <h3 className="text-sm font-medium">Retry Timeline</h3>
                </div>
                <Timeline events={retryHistory} />
              </SpotlightCard>
            </TiltCard>
          </motion.div>

          <div className="space-y-4">
            <TiltCard>
              <SpotlightCard className="p-5">
                <h3 className="mb-4 text-sm font-medium text-muted-foreground">Retry Distribution</h3>
                <ResponsiveContainer width="100%" height={200}>
                  <PieChart>
                    <Pie data={pieData} cx="50%" cy="50%" innerRadius={45} outerRadius={75} dataKey="value" animationDuration={600}>
                      {pieData.map((_, i) => <Cell key={i} fill={pieColors[i]} />)}
                    </Pie>
                    <Tooltip contentStyle={{ background: '#121213', border: '1px solid #1f1f23', borderRadius: 8, fontSize: 13 }} itemStyle={{ color: '#fafafa' }} />
                  </PieChart>
                </ResponsiveContainer>
                <div className="mt-2 flex justify-center gap-4 text-xs text-muted-foreground">
                  {pieData.map((d, i) => (
                    <span key={d.name} className="flex items-center gap-1">
                      <span className="h-2 w-2 rounded-full" style={{ backgroundColor: pieColors[i] }} />
                      {d.name}
                    </span>
                  ))}
                </div>
              </SpotlightCard>
            </TiltCard>

            <TiltCard>
              <SpotlightCard className="p-5">
                <h3 className="mb-4 text-sm font-medium text-muted-foreground">Common Failure Reasons</h3>
                <div className="space-y-2">
                  {[
                    { reason: 'Dependency resolution', count: 12 },
                    { reason: 'Test flakiness', count: 8 },
                    { reason: 'Network timeout', count: 6 },
                    { reason: 'API contract mismatch', count: 4 },
                  ].map((r) => (
                    <div key={r.reason} className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">{r.reason}</span>
                      <span className="font-mono text-xs tabular-nums">{r.count}</span>
                    </div>
                  ))}
                </div>
              </SpotlightCard>
            </TiltCard>
          </div>
        </div>
      </div>
    </PageTransition>
  )
}
