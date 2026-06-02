import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, AreaChart, Area,
} from 'recharts'
import { Activity } from 'lucide-react'
import { PageTransition } from '@/components/page-transition'
import { StaggerGrid, StaggerItem } from '@/components/stagger-grid'
import { MetricCard } from '@/components/metric-card'
import { AnimatedContent, ChartSkeleton, MetricSkeleton } from '@/components/animated-content'
import { TabNav } from '@/components/tab-nav'
import { EmptyState } from '@/components/empty-state'
import { ErrorBanner } from '@/components/error-banner'
import { TiltCard } from '@/components/tilt-card'
import { ActivityFeed } from '@/components/activity-feed'
import {
  useDashboardSummary,
  useDashboardMetrics,
  useDashboardRepositories,
  useChartData,
} from '@/lib/api'
import { tabContentVariants, safeTransition, duration } from '@/lib/motion'
import type {
  DashboardSummary,
  DashboardMetrics,
  RepositoryInfo,
  ReviewScores,
  ValidationResults,
  PRStatistics,
} from '@/lib/types'

const tabs = [
  'System Overview',
  'Repository Analytics',
  'Retry Analytics',
  'Validation Analytics',
  'Review Analytics',
  'PR Analytics',
]

function ChartCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <TiltCard>
      <div className="rounded-xl border border-border bg-card p-6">
        <h3 className="mb-4 text-sm font-medium text-muted-foreground">{title}</h3>
        {children}
      </div>
    </TiltCard>
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
        <ChartCard title="Success vs Failures">
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={[{ name: 'Success', value: 85 }, { name: 'Failure', value: 15 }]}>
              <XAxis dataKey="name" tick={{ fontSize: 12, fill: '#71717a' }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 12, fill: '#71717a' }} axisLine={false} tickLine={false} />
              <Tooltip
                contentStyle={{ background: '#121213', border: '1px solid #1f1f23', borderRadius: 8, fontSize: 13 }}
                itemStyle={{ color: '#fafafa' }}
              />
              <Bar dataKey="value" radius={[4, 4, 0, 0]} animationBegin={0} animationDuration={500} animationEasing="ease-out">
                <Cell fill="#22c55e" />
                <Cell fill="#ef4444" />
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Activity Trend">
          <ResponsiveContainer width="100%" height={280}>
            <AreaChart data={[
              { day: 'Mon', runs: 12 }, { day: 'Tue', runs: 18 }, { day: 'Wed', runs: 15 },
              { day: 'Thu', runs: 22 }, { day: 'Fri', runs: 20 }, { day: 'Sat', runs: 8 }, { day: 'Sun', runs: 5 },
            ]}>
              <XAxis dataKey="day" tick={{ fontSize: 12, fill: '#71717a' }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 12, fill: '#71717a' }} axisLine={false} tickLine={false} />
              <Tooltip
                contentStyle={{ background: '#121213', border: '1px solid #1f1f23', borderRadius: 8, fontSize: 13 }}
                itemStyle={{ color: '#fafafa' }}
              />
              <Area type="monotone" dataKey="runs" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.1} strokeWidth={2} animationDuration={600} />
            </AreaChart>
          </ResponsiveContainer>
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
      <TiltCard>
        <div className="overflow-x-auto rounded-xl border border-border bg-card">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border">
                <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground">Repository</th>
                <th className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wider text-muted-foreground">Total Runs</th>
                <th className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wider text-muted-foreground">Success Rate</th>
                <th className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wider text-muted-foreground">Avg Confidence</th>
              </tr>
            </thead>
            <tbody>
              {repos.map((r, i) => (
                <motion.tr
                  key={r.repository_name}
                  initial={{ opacity: 0, x: -8 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.03, duration: 0.2 }}
                  className="border-b border-border last:border-0 hover:bg-muted/50"
                >
                  <td className="px-4 py-3 font-medium">{r.repository_name}</td>
                  <td className="px-4 py-3 text-right font-mono tabular-nums">{r.total_runs}</td>
                  <td className="px-4 py-3 text-right font-mono tabular-nums">{r.success_rate.toFixed(1)}%</td>
                  <td className="px-4 py-3 text-right font-mono tabular-nums">{r.avg_confidence.toFixed(2)}</td>
                </motion.tr>
              ))}
            </tbody>
          </table>
        </div>
      </TiltCard>
    </motion.div>
  )
}

function RetryTab({ metrics }: { metrics: DashboardMetrics }) {
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
        <MetricCard label="Recovery Rate" value={78} suffix="%" />
      </div>
      <ChartCard title="Retry Distribution">
        <ResponsiveContainer width="100%" height={280}>
          <PieChart>
            <Pie
              data={[
                { name: 'Attempt 1', value: 40 },
                { name: 'Attempt 2', value: 30 },
                { name: 'Attempt 3', value: 20 },
                { name: 'Failed', value: 10 },
              ]}
              cx="50%"
              cy="50%"
              innerRadius={60}
              outerRadius={100}
              animationBegin={0}
              animationDuration={600}
              animationEasing="ease-out"
              dataKey="value"
            >
              {['#3b82f6', '#22c55e', '#eab308', '#ef4444'].map((color, i) => (
                <Cell key={i} fill={color} />
              ))}
            </Pie>
            <Tooltip
              contentStyle={{ background: '#121213', border: '1px solid #1f1f23', borderRadius: 8, fontSize: 13 }}
              itemStyle={{ color: '#fafafa' }}
            />
          </PieChart>
        </ResponsiveContainer>
      </ChartCard>
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
      <ChartCard title="Validation Results">
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={validation.labels.map((l, i) => ({ name: l, value: validation.values[i] ?? 0 }))}>
            <XAxis dataKey="name" tick={{ fontSize: 12, fill: '#71717a' }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fontSize: 12, fill: '#71717a' }} axisLine={false} tickLine={false} />
            <Tooltip
              contentStyle={{ background: '#121213', border: '1px solid #1f1f23', borderRadius: 8, fontSize: 13 }}
              itemStyle={{ color: '#fafafa' }}
            />
            <Bar dataKey="value" radius={[4, 4, 0, 0]} animationDuration={500}>
              {validation.labels.map((_, i) => (
                <Cell key={i} fill={i === 0 ? '#22c55e' : '#ef4444'} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </ChartCard>
    </motion.div>
  )
}

function ReviewTab({ review }: { review: ReviewScores }) {
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
              <div className="rounded-xl border border-border bg-card p-5">
                <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">{cat}</p>
                <p className="mt-2 font-mono text-2xl font-semibold tabular-nums">
                  {review.scores[i]?.toFixed(2) ?? '—'}
                </p>
                <div className="mt-3 flex gap-0.5">
                  {Array.from({ length: 10 }).map((_, j) => (
                    <div
                      key={j}
                      className={`h-1.5 flex-1 rounded-full ${
                        j < Math.round((review.scores[i] ?? 0) * 10) ? 'bg-foreground' : 'bg-muted'
                      }`}
                    />
                  ))}
                </div>
              </div>
            </TiltCard>
          </StaggerItem>
        ))}
      </StaggerGrid>
    </motion.div>
  )
}

function PRTab({ prStats }: { prStats: PRStatistics }) {
  return (
    <motion.div
      variants={tabContentVariants}
      initial="initial"
      animate="animate"
      exit="exit"
      transition={safeTransition({ duration: duration.normal })}
    >
      <div className="mb-6 grid gap-4 sm:grid-cols-2">
        <MetricCard label={prStats.labels[0] ?? 'Simulated'} value={prStats.values[0] ?? 0} />
        <MetricCard label={prStats.labels[1] ?? 'Real'} value={prStats.values[1] ?? 0} />
      </div>
      <ChartCard title="PR Distribution">
        <ResponsiveContainer width="100%" height={280}>
          <PieChart>
            <Pie
              data={prStats.labels.map((l, i) => ({ name: l, value: prStats.values[i] ?? 0 }))}
              cx="50%"
              cy="50%"
              outerRadius={100}
              animationBegin={0}
              animationDuration={600}
              dataKey="value"
            >
              {['#3b82f6', '#22c55e'].map((color, i) => (
                <Cell key={i} fill={color} />
              ))}
            </Pie>
            <Tooltip
              contentStyle={{ background: '#121213', border: '1px solid #1f1f23', borderRadius: 8, fontSize: 13 }}
              itemStyle={{ color: '#fafafa' }}
            />
          </PieChart>
        </ResponsiveContainer>
      </ChartCard>
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

  return (
    <PageTransition>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Dashboard</h1>
          <p className="text-sm text-muted-foreground">System-wide metrics and analytics</p>
        </div>
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <Activity className="h-3.5 w-3.5" />
          <span>Live</span>
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
                {activeTab === 'System Overview' && <OverviewTab key="overview" summary={summary ?? { system_health: { total_workflow_runs: 0, overall_success_rate: 0, average_retries_per_run: 0 }, confidence: { overall_confidence: 0 } }} />}
                {activeTab === 'Repository Analytics' && <ReposTab key="repos" repos={repos ?? []} />}
                {activeTab === 'Retry Analytics' && <RetryTab key="retry" metrics={metrics ?? {} as DashboardMetrics} />}
                {activeTab === 'Validation Analytics' && <ValidationTab key="validation" validation={validation ?? { labels: [], values: [] }} />}
                {activeTab === 'Review Analytics' && <ReviewTab key="review" review={review ?? { categories: [], scores: [] }} />}
                {activeTab === 'PR Analytics' && <PRTab key="pr" prStats={prStats ?? { labels: [], values: [] }} />}
              </AnimatePresence>
            </div>
          </AnimatedContent>
        </div>

        <div className="hidden lg:block">
          <div className="sticky top-20">
            <ActivityFeed />
          </div>
        </div>
      </div>
    </PageTransition>
  )
}
