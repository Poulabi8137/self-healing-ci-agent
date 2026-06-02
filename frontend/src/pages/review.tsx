import { useState } from 'react'
import { motion } from 'framer-motion'
import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, BarChart, Bar, Cell,
} from 'recharts'
import { Shield, Eye } from 'lucide-react'
import { PageTransition } from '@/components/page-transition'
import { SpotlightCard } from '@/components/spotlight-card'
import { TiltCard } from '@/components/tilt-card'
import { MetricCard } from '@/components/metric-card'
import { AnimatedCounter } from '@/components/animated-counter'
import { StatusBadge } from '@/components/status-badge'
import { useChartData } from '@/lib/api'
import { tabContentVariants, safeTransition, duration } from '@/lib/motion'
import type { ReviewScores } from '@/lib/types'

const scoreColors = ['#3b82f6', '#22c55e', '#eab308', '#a855f7']

const trendData = [
  { week: 'W1', security: 72, performance: 68, quality: 75, coverage: 60 },
  { week: 'W2', security: 78, performance: 72, quality: 80, coverage: 65 },
  { week: 'W3', security: 82, performance: 78, quality: 78, coverage: 70 },
  { week: 'W4', security: 85, performance: 82, quality: 84, coverage: 72 },
  { week: 'W5', security: 88, performance: 80, quality: 86, coverage: 75 },
  { week: 'W6', security: 92, performance: 85, quality: 90, coverage: 78 },
]

const recentReviews = [
  { id: '1', repo: 'frontend-app', status: 'passed' as const, score: 88, date: '2m ago' },
  { id: '2', repo: 'api-service', status: 'partial' as const, score: 72, date: '15m ago' },
  { id: '3', repo: 'infra-modules', status: 'passed' as const, score: 95, date: '1h ago' },
  { id: '4', repo: 'docs-site', status: 'passed' as const, score: 91, date: '3h ago' },
  { id: '5', repo: 'mobile-sdk', status: 'failed' as const, score: 45, date: '6h ago' },
]

function RadarScoreCard({ data }: { data: ReviewScores }) {
  const chartData = data.categories.map((cat, i) => ({
    category: cat,
    score: data.scores[i] ?? 0,
    fullMark: 100,
  }))

  return (
    <TiltCard>
      <SpotlightCard className="p-6">
        <h3 className="mb-4 text-sm font-medium text-muted-foreground">Score Overview</h3>
        <ResponsiveContainer width="100%" height={300}>
          <RadarChart data={chartData}>
            <PolarGrid stroke="hsl(var(--border))" />
            <PolarAngleAxis dataKey="category" tick={{ fontSize: 11, fill: 'hsl(var(--muted-foreground))' }} />
            <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fontSize: 10, fill: 'hsl(var(--muted-foreground))' }} />
            <Radar name="Score" dataKey="score" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.15} strokeWidth={2} animationDuration={600} />
          </RadarChart>
        </ResponsiveContainer>
      </SpotlightCard>
    </TiltCard>
  )
}

function TrendChart() {
  return (
    <TiltCard>
      <SpotlightCard className="p-6">
        <h3 className="mb-4 text-sm font-medium text-muted-foreground">Historical Trend</h3>
        <ResponsiveContainer width="100%" height={250}>
          <LineChart data={trendData}>
            <XAxis dataKey="week" tick={{ fontSize: 11, fill: 'hsl(var(--muted-foreground))' }} axisLine={false} tickLine={false} />
            <YAxis domain={[0, 100]} tick={{ fontSize: 11, fill: 'hsl(var(--muted-foreground))' }} axisLine={false} tickLine={false} />
            <Tooltip contentStyle={{ background: '#121213', border: '1px solid #1f1f23', borderRadius: 8, fontSize: 13 }} itemStyle={{ color: '#fafafa' }} />
            <Line type="monotone" dataKey="security" stroke="#3b82f6" strokeWidth={2} dot={false} animationDuration={600} />
            <Line type="monotone" dataKey="performance" stroke="#22c55e" strokeWidth={2} dot={false} animationDuration={600} />
            <Line type="monotone" dataKey="quality" stroke="#eab308" strokeWidth={2} dot={false} animationDuration={600} />
            <Line type="monotone" dataKey="coverage" stroke="#a855f7" strokeWidth={2} dot={false} animationDuration={600} />
          </LineChart>
        </ResponsiveContainer>
      </SpotlightCard>
    </TiltCard>
  )
}

function OverallScore({ score }: { score: number }) {
  const color = score >= 80 ? '#22c55e' : score >= 60 ? '#eab308' : '#ef4444'
  return (
    <TiltCard>
      <SpotlightCard className="p-6">
        <div className="flex items-center gap-6">
          <div className="relative flex h-24 w-24 items-center justify-center">
            <svg className="absolute inset-0 h-full w-full -rotate-90" viewBox="0 0 100 100">
              <circle cx="50" cy="50" r="42" fill="none" stroke="hsl(var(--muted))" strokeWidth="8" />
              <motion.circle
                cx="50" cy="50" r="42" fill="none" stroke={color} strokeWidth="8" strokeLinecap="round"
                strokeDasharray={`${score * 2.64} ${264 - score * 2.64}`}
                initial={{ strokeDasharray: '0 264' }}
                animate={{ strokeDasharray: `${score * 2.64} ${264 - score * 2.64}` }}
                transition={{ duration: 1, ease: [0.16, 1, 0.3, 1] }}
              />
            </svg>
            <span className="font-mono text-2xl font-bold" style={{ color }}>
              <AnimatedCounter value={score} suffix="%" decimals={0} />
            </span>
          </div>
          <div>
            <p className="text-sm font-medium text-foreground">Overall Confidence</p>
            <p className="text-xs text-muted-foreground">Multi-agent consensus score</p>
            <div className="mt-2 flex items-center gap-2">
              <StatusBadge status={score >= 80 ? 'passed' : score >= 60 ? 'partial' : 'failed'} animated={false} />
            </div>
          </div>
        </div>
      </SpotlightCard>
    </TiltCard>
  )
}

function DistributionChart({ data }: { data: ReviewScores }) {
  return (
    <TiltCard>
      <SpotlightCard className="p-6">
        <h3 className="mb-4 text-sm font-medium text-muted-foreground">Score Distribution</h3>
        <ResponsiveContainer width="100%" height={250}>
          <BarChart data={data.categories.map((c, i) => ({ name: c, score: data.scores[i] ?? 0 }))}>
            <XAxis dataKey="name" tick={{ fontSize: 11, fill: 'hsl(var(--muted-foreground))' }} axisLine={false} tickLine={false} />
            <YAxis domain={[0, 100]} tick={{ fontSize: 11, fill: 'hsl(var(--muted-foreground))' }} axisLine={false} tickLine={false} />
            <Tooltip contentStyle={{ background: '#121213', border: '1px solid #1f1f23', borderRadius: 8, fontSize: 13 }} itemStyle={{ color: '#fafafa' }} />
            <Bar dataKey="score" radius={[4, 4, 0, 0]} animationDuration={500}>
              {data.scores.map((_, i) => <Cell key={i} fill={scoreColors[i % scoreColors.length]} />)}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </SpotlightCard>
    </TiltCard>
  )
}

export default function Review() {
  const { data: reviewData } = useChartData<ReviewScores>('review-scores')
  const data = reviewData ?? { categories: ['Security', 'Performance', 'Quality', 'Coverage'], scores: [92, 85, 90, 78] }
  const [activeReview, setActiveReview] = useState<string | null>(null)

  const overallScore = Math.round(data.scores.reduce((a, b) => a + b, 0) / data.scores.length)

  return (
    <PageTransition>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold">Review</h1>
            <p className="text-sm text-muted-foreground">Multi-agent review scores</p>
          </div>
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <Shield className="h-3.5 w-3.5 text-emerald-500" />
            <span>All agents reporting</span>
          </div>
        </div>

        <div className="grid gap-6 lg:grid-cols-[1fr_300px]">
          <div className="space-y-6">
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {data.categories.map((cat, i) => (
                <MetricCard
                  key={cat}
                  label={cat}
                  value={data.scores[i] ?? 0}
                  suffix="%"
                  decimals={0}
                  trend={i === 0 ? { value: 8, positive: true } : i === 1 ? { value: 3, positive: true } : undefined}
                />
              ))}
            </div>

            <motion.div
              variants={tabContentVariants}
              initial="initial"
              animate="animate"
              transition={safeTransition({ duration: duration.normal })}
              className="grid gap-6 lg:grid-cols-2"
            >
              <RadarScoreCard data={data} />
              <DistributionChart data={data} />
            </motion.div>

            <TrendChart />
          </div>

          <div className="space-y-4">
            <OverallScore score={overallScore} />

            <TiltCard>
              <SpotlightCard className="p-5">
                <div className="mb-3 flex items-center gap-2">
                  <Eye className="h-4 w-4 text-muted-foreground" />
                  <h3 className="text-sm font-medium">Recent Reviews</h3>
                </div>
                <div className="space-y-2">
                  {recentReviews.map((r) => (
                    <motion.button
                      key={r.id}
                      onClick={() => setActiveReview(r.id === activeReview ? null : r.id)}
                      whileTap={{ scale: 0.98 }}
                      className={`flex w-full items-center justify-between rounded-lg px-3 py-2 text-left transition-colors ${
                        activeReview === r.id ? 'bg-accent' : 'hover:bg-muted/50'
                      }`}
                    >
                      <div className="min-w-0">
                        <p className="text-sm font-medium truncate">{r.repo}</p>
                        <p className="text-[10px] text-muted-foreground">{r.date}</p>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-xs tabular-nums">{r.score}</span>
                        <StatusBadge status={r.status} animated={false} />
                      </div>
                    </motion.button>
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
