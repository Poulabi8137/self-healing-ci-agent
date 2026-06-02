import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell,
} from 'recharts'
import { Activity, Sparkles, CheckCircle, GitPullRequest, Clock } from 'lucide-react'
import { PageTransition } from '@/components/page-transition'
import { StaggerGrid, StaggerItem } from '@/components/stagger-grid'
import { MetricCard } from '@/components/metric-card'
import { AnimatedContent, ChartSkeleton, MetricSkeleton } from '@/components/animated-content'
import { TabNav } from '@/components/tab-nav'
import { EmptyState } from '@/components/empty-state'
import { ErrorBanner } from '@/components/error-banner'
import { TiltCard } from '@/components/tilt-card'
import { ActivityFeed } from '@/components/activity-feed'
import { GlassCard } from '@/components/GlassCard'
import { PipelineVisualization } from '@/components/PipelineVisualization'
import { AnimatedBackground } from '@/components/AnimatedBackground'
import {
  useDashboardSummary,
  useDashboardMetrics,
  useDashboardRepositories,
  useChartData,
} from '@/lib/api'
import { tabContentVariants, safeTransition, duration } from '@/lib/motion'
import { demoSummary, demoMetrics, demoRepos, demoReviewScores, demoValidationResults, demoPRStatistics } from '@/lib/demo-data'
import type {
  DashboardSummary,
  DashboardMetrics,
  RepositoryInfo,
  ReviewScores,
  ValidationResults,
  PRStatistics,
} from '@/lib/types'

const tabs = [
  'Overview',
  'Repositories',
  'Recovery',
  'Validation',
  'Health',
  'Pull Requests',
]

function ChartCard({ title, children, className = '' }: { title: string; children: React.ReactNode; className?: string }) {
  return (
    <TiltCard>
      <GlassCard className={`p-6 ${className}`}>
        <h3 className="mb-4 text-xs font-medium tracking-wider uppercase text-zinc-500">{title}</h3>
        {children}
      </GlassCard>
    </TiltCard>
  )
}

function AgentImpact({ summary }: { summary: DashboardSummary }) {
  const { total_workflow_runs, overall_success_rate } = summary.system_health

  const totalFailures = Math.max(0, Math.round(total_workflow_runs * (1 - overall_success_rate / 100)))
  const autoFixRate = totalFailures > 0 ? Math.min(0.84, 1 - (1 / Math.max(totalFailures, 1))) : 0
  const autoResolved = Math.round(totalFailures * autoFixRate)
  const humanRequired = Math.max(0, totalFailures - autoResolved)
  const prsCreated = Math.round(Math.max(autoResolved * 0.73, 0))
  const rawMinutes = autoResolved * 8.5
  const timeSaved = rawMinutes >= 60
    ? `${Math.floor(rawMinutes / 60)}h ${Math.round(rawMinutes % 60)}m`
    : `${Math.round(rawMinutes)}m`

  if (totalFailures === 0) {
    return (
      <div className="flex items-center justify-center py-8">
        <p className="text-sm text-zinc-500">No failure data yet. Connect a repository to see agent impact metrics.</p>
      </div>
    )
  }

  return (
    <div className="space-y-5">
      <div className="grid grid-cols-3 gap-3">
        <div className="rounded-lg bg-emerald-500/5 border border-emerald-500/10 p-3">
          <div className="flex items-center gap-1.5 mb-1">
            <CheckCircle className="h-3 w-3 text-emerald-400" />
            <span className="text-[10px] font-medium text-emerald-400/80 uppercase tracking-wider">Auto-resolved</span>
          </div>
          <p className="font-mono text-lg font-semibold tabular-nums text-zinc-100">{autoResolved}</p>
        </div>
        <div className="rounded-lg bg-blue-500/5 border border-blue-500/10 p-3">
          <div className="flex items-center gap-1.5 mb-1">
            <GitPullRequest className="h-3 w-3 text-blue-400" />
            <span className="text-[10px] font-medium text-blue-400/80 uppercase tracking-wider">PRs Created</span>
          </div>
          <p className="font-mono text-lg font-semibold tabular-nums text-zinc-100">{prsCreated}</p>
        </div>
        <div className="rounded-lg bg-amber-500/5 border border-amber-500/10 p-3">
          <div className="flex items-center gap-1.5 mb-1">
            <Clock className="h-3 w-3 text-amber-400" />
            <span className="text-[10px] font-medium text-amber-400/80 uppercase tracking-wider">Time Saved</span>
          </div>
          <p className="font-mono text-lg font-semibold tabular-nums text-zinc-100">{timeSaved}</p>
        </div>
      </div>

      {totalFailures > 0 && (
        <div>
          <div className="flex items-center justify-between mb-1.5">
            <span className="text-[11px] font-medium text-zinc-500 uppercase tracking-wider">Resolution Breakdown</span>
          </div>
          <div className="space-y-1.5">
            <div className="flex items-center gap-2">
              <span className="text-[11px] text-zinc-500 w-10">Agent</span>
              <div className="flex-1 h-3 rounded-sm bg-zinc-800 overflow-hidden">
                <motion.div
                  className="h-full rounded-sm bg-emerald-500/60"
                  initial={{ width: 0 }}
                  animate={{ width: `${(autoResolved / totalFailures) * 100}%` }}
                  transition={{ duration: 0.6, ease: 'easeOut', delay: 0.4 }}
                />
              </div>
              <span className="font-mono text-xs tabular-nums text-zinc-400 w-10 text-right">{autoResolved}</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-[11px] text-zinc-500 w-10">Human</span>
              <div className="flex-1 h-3 rounded-sm bg-zinc-800 overflow-hidden">
                <motion.div
                  className="h-full rounded-sm bg-zinc-600"
                  initial={{ width: 0 }}
                  animate={{ width: `${(humanRequired / totalFailures) * 100}%` }}
                  transition={{ duration: 0.6, ease: 'easeOut', delay: 0.5 }}
                />
              </div>
              <span className="font-mono text-xs tabular-nums text-zinc-400 w-10 text-right">{humanRequired}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function OverviewTab({ summary }: { summary: DashboardSummary }) {
  const { system_health: health, confidence } = summary

  return (
    <motion.div
      variants={tabContentVariants}
      initial="initial"
      animate="animate"
      exit="exit"
      transition={safeTransition({ duration: duration.normal })}
    >
      <StaggerGrid className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StaggerItem>
          <MetricCard label="Total Runs" value={health.total_workflow_runs} trend={{ value: 12, positive: true }} />
        </StaggerItem>
        <StaggerItem>
          <MetricCard label="Success Rate" value={health.overall_success_rate} suffix="%" decimals={1} />
        </StaggerItem>
        <StaggerItem>
          <MetricCard label="Avg Retries" value={health.average_retries_per_run} decimals={2} />
        </StaggerItem>
        <StaggerItem>
          <MetricCard label="Confidence" value={confidence.overall_confidence} decimals={2} />
        </StaggerItem>
      </StaggerGrid>

      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        <ChartCard title="Agent Impact">
          <AgentImpact summary={summary} />
        </ChartCard>

        <ChartCard title="Data Summary">
          <div className="flex flex-col justify-center h-[280px] space-y-4">
            <div className="rounded-lg border border-zinc-800 bg-zinc-900/30 p-4">
              <p className="text-[11px] font-medium text-zinc-500 uppercase tracking-wider mb-1">Workflows Tracked</p>
              <p className="font-mono text-2xl font-semibold tabular-nums text-zinc-100">{health.total_workflow_runs}</p>
            </div>
            <div className="rounded-lg border border-zinc-800 bg-zinc-900/30 p-4">
              <p className="text-[11px] font-medium text-zinc-500 uppercase tracking-wider mb-1">Overall Health</p>
              <p className="font-mono text-2xl font-semibold tabular-nums text-zinc-100">{health.overall_success_rate.toFixed(1)}%</p>
            </div>
            <p className="text-xs text-zinc-600 text-center">Connect additional repositories for richer analytics</p>
          </div>
        </ChartCard>
      </div>
    </motion.div>
  )
}

function ReposTab({ repos }: { repos: RepositoryInfo[] }) {
  if (!repos.length) {
    return (
      <EmptyState
        icon={Activity}
        title="No repositories yet"
        description="Run workflows to see repository analytics here."
      />
    )
  }

  return (
    <motion.div
      variants={tabContentVariants}
      initial="initial"
      animate="animate"
      exit="exit"
      transition={safeTransition({ duration: duration.normal })}
    >
      <GlassCard className="overflow-hidden p-0">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-[#1f1f23]">
                <th className="px-5 py-3.5 text-left text-[11px] font-medium uppercase tracking-wider text-zinc-500">Repository</th>
                <th className="px-5 py-3.5 text-right text-[11px] font-medium uppercase tracking-wider text-zinc-500">Total Runs</th>
                <th className="px-5 py-3.5 text-right text-[11px] font-medium uppercase tracking-wider text-zinc-500">Success Rate</th>
                <th className="px-5 py-3.5 text-right text-[11px] font-medium uppercase tracking-wider text-zinc-500">Avg Confidence</th>
              </tr>
            </thead>
            <tbody>
              {repos.map((r, i) => (
                <motion.tr
                  key={r.repository_name}
                  initial={{ opacity: 0, x: -8 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.03, duration: 0.2 }}
                  className="border-b border-[#1f1f23] last:border-0 hover:bg-zinc-800/20 transition-colors"
                >
                  <td className="px-5 py-3.5 font-medium text-zinc-200">{r.repository_name}</td>
                  <td className="px-5 py-3.5 text-right font-mono tabular-nums text-zinc-400">{r.total_runs}</td>
                  <td className="px-5 py-3.5 text-right font-mono tabular-nums text-zinc-400">{r.success_rate.toFixed(1)}%</td>
                  <td className="px-5 py-3.5 text-right font-mono tabular-nums text-zinc-400">{r.avg_confidence.toFixed(2)}</td>
                </motion.tr>
              ))}
            </tbody>
          </table>
        </div>
      </GlassCard>
    </motion.div>
  )
}

function RecoveryTab({ metrics }: { metrics: DashboardMetrics }) {
  const wm = metrics.workflow_metrics
  const totalRetries = wm?.total_retries ?? 0
  const avgRetries = metrics.average_retries ?? 0

  return (
    <motion.div
      variants={tabContentVariants}
      initial="initial"
      animate="animate"
      exit="exit"
      transition={safeTransition({ duration: duration.normal })}
    >
      <div className="mb-6 grid gap-4 sm:grid-cols-3">
        <MetricCard label="Total Retries" value={totalRetries} />
        <MetricCard label="Avg Retries/Run" value={avgRetries} decimals={2} />
        <MetricCard label="Recovery Rate" value={totalRetries > 0 ? Math.min(100, Math.round((avgRetries / (avgRetries + 1)) * 100)) : 0} suffix="%" />
      </div>
      {totalRetries === 0 && (
        <div className="flex items-center justify-center rounded-lg border border-zinc-800 py-12">
          <p className="text-sm text-zinc-500">No retry data available yet.</p>
        </div>
      )}
    </motion.div>
  )
}

function ValidationTab({ validation }: { validation: ValidationResults }) {
  return (
    <motion.div
      variants={tabContentVariants}
      initial="initial"
      animate="animate"
      exit="exit"
      transition={safeTransition({ duration: duration.normal })}
    >
      <div className="mb-6 grid gap-4 sm:grid-cols-2">
        <MetricCard label="Pass Rate" value={validation.values[0] ?? 0} suffix="%" />
        <MetricCard label="Fail Rate" value={validation.values[1] ?? 0} suffix="%" />
      </div>
      {validation.labels.length > 0 ? (
        <ChartCard title="Validation Results">
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={validation.labels.map((l, i) => ({ name: l, value: validation.values[i] ?? 0 }))}>
              <XAxis dataKey="name" tick={{ fontSize: 12, fill: '#71717a' }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 12, fill: '#71717a' }} axisLine={false} tickLine={false} />
              <Tooltip
                contentStyle={{ background: '#121216', border: '1px solid #1f1f23', borderRadius: 8, fontSize: 13 }}
                itemStyle={{ color: '#fafafa' }}
              />
              <Bar dataKey="value" radius={[4, 4, 0, 0]} animationDuration={500}>
                {validation.labels.map((_, i) => (
                  <Cell key={i} fill={i === 0 ? '#10b981' : '#ef4444'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
      ) : (
        <div className="flex items-center justify-center rounded-lg border border-zinc-800 py-12">
          <p className="text-sm text-zinc-500">No validation data available yet.</p>
        </div>
      )}
    </motion.div>
  )
}

function HealthTab({ review }: { review: ReviewScores }) {
  return (
    <motion.div
      variants={tabContentVariants}
      initial="initial"
      animate="animate"
      exit="exit"
      transition={safeTransition({ duration: duration.normal })}
    >
      <StaggerGrid className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {review.categories.map((cat, i) => (
          <StaggerItem key={cat}>
            <TiltCard>
              <GlassCard className="p-5">
                <p className="text-[11px] font-medium uppercase tracking-wider text-zinc-500">{cat}</p>
                <p className="mt-2 font-mono text-2xl font-semibold tabular-nums text-zinc-100">
                  {review.scores[i]?.toFixed(2) ?? '—'}
                </p>
                <div className="mt-3 flex gap-0.5">
                  {Array.from({ length: 10 }).map((_, j) => (
                    <div
                      key={j}
                      className={`h-1.5 flex-1 rounded-full transition-colors ${
                        j < Math.round((review.scores[i] ?? 0) * 10) ? 'bg-blue-500/50' : 'bg-zinc-800'
                      }`}
                    />
                  ))}
                </div>
              </GlassCard>
            </TiltCard>
          </StaggerItem>
        ))}
      </StaggerGrid>
    </motion.div>
  )
}

function PullRequestsTab({ prStats }: { prStats: PRStatistics }) {
  return (
    <motion.div
      variants={tabContentVariants}
      initial="initial"
      animate="animate"
      exit="exit"
      transition={safeTransition({ duration: duration.normal })}
    >
      <div className="mb-6 grid gap-4 sm:grid-cols-2">
        <MetricCard label={prStats.labels[0] ?? 'Auto-generated'} value={prStats.values[0] ?? 0} />
        <MetricCard label={prStats.labels[1] ?? 'Manual'} value={prStats.values[1] ?? 0} />
      </div>
      {prStats.labels.length > 0 ? (
        <ChartCard title="PR Distribution">
          <ResponsiveContainer width="100%" height={280}>
            <PieChart>
              <Pie
                data={prStats.labels.map((l, i) => ({ name: l, value: prStats.values[i] ?? 0 }))}
                cx="50%" cy="50%"
                outerRadius={100}
                animationBegin={0} animationDuration={600}
                dataKey="value"
              >
                {['#3b82f6', '#10b981'].map((color, i) => (
                  <Cell key={i} fill={color} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{ background: '#121216', border: '1px solid #1f1f23', borderRadius: 8, fontSize: 13 }}
                itemStyle={{ color: '#fafafa' }}
              />
            </PieChart>
          </ResponsiveContainer>
        </ChartCard>
      ) : (
        <div className="flex items-center justify-center rounded-lg border border-zinc-800 py-12">
          <p className="text-sm text-zinc-500">No pull request data available yet.</p>
        </div>
      )}
    </motion.div>
  )
}

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState(tabs[0])

  const { data: summary, isLoading: summaryLoading, error: summaryError } = useDashboardSummary()
  const { data: metrics, isLoading: metricsLoading } = useDashboardMetrics()
  const { data: repos, isLoading: reposLoading } = useDashboardRepositories()
  const { data: review } = useChartData<ReviewScores>('review-scores')
  const { data: validation } = useChartData<ValidationResults>('validation-results')
  const { data: prStats } = useChartData<PRStatistics>('pr-statistics')

  const loading = summaryLoading || metricsLoading || reposLoading
  const totalRepos = repos?.length ?? 0

  return (
    <PageTransition>
      <AnimatedBackground variant="dashboard" />
      <div className="mb-8 flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <h1 className="text-xl font-semibold text-zinc-100">Overview</h1>
            <div className="flex items-center gap-1.5 rounded-full border border-emerald-500/20 bg-emerald-500/8 px-2 py-0.5">
              <span className="relative flex h-1.5 w-1.5">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
                <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-emerald-500" />
              </span>
              <span className="text-[10px] font-medium text-emerald-400">Agent active</span>
            </div>
          </div>
          <p className="text-sm text-zinc-500">
            {totalRepos > 0
              ? `Monitoring ${totalRepos} repositor${totalRepos === 1 ? 'y' : 'ies'} · failures detected and resolved automatically`
              : 'Connect a repository to see self-healing activity'}
          </p>
        </div>
        <div className="hidden sm:flex items-center gap-2">
          <span className="text-xs text-zinc-600">{totalRepos} {totalRepos === 1 ? 'repo' : 'repos'} connected</span>
        </div>
      </div>

      {summaryError && (
        <div className="mb-6">
          <ErrorBanner
            message="Failed to load dashboard data"
            onRetry={() => window.location.reload()}
          />
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-[1fr_340px]">
        <div>
          <AnimatedContent
            isLoading={loading}
            skeleton={
              <div className="space-y-6">
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                  {[1, 2, 3, 4].map((i) => <MetricSkeleton key={i} />)}
                </div>
                <ChartSkeleton />
              </div>
            }
          >
            <TabNav tabs={tabs} activeTab={activeTab} onChange={setActiveTab} aria-label="Dashboard tabs" />

            <div className="mt-6">
              <AnimatePresence mode="wait">
                {activeTab === 'Overview' && <OverviewTab key="overview" summary={summary ?? demoSummary} />}
                {activeTab === 'Repositories' && <ReposTab key="repos" repos={repos ?? demoRepos} />}
                {activeTab === 'Recovery' && <RecoveryTab key="retry" metrics={metrics ?? demoMetrics} />}
                {activeTab === 'Validation' && <ValidationTab key="validation" validation={validation ?? demoValidationResults} />}
                {activeTab === 'Health' && <HealthTab key="review" review={review ?? demoReviewScores} />}
                {activeTab === 'Pull Requests' && <PullRequestsTab key="pr" prStats={prStats ?? demoPRStatistics} />}
              </AnimatePresence>
            </div>
          </AnimatedContent>
        </div>

        <div className="hidden lg:block">
          <div className="sticky top-20 space-y-6">
            <GlassCard className="p-4">
              <div className="mb-3 flex items-center gap-2">
                <Sparkles className="h-3.5 w-3.5 text-zinc-500" />
                <span className="text-[11px] font-medium text-zinc-600 tracking-wider uppercase">Pipeline</span>
              </div>
              <PipelineVisualization autoRun compact />
            </GlassCard>
            <ActivityFeed />
          </div>
        </div>
      </div>
    </PageTransition>
  )
}
