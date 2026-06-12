import { motion } from 'framer-motion'
import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  ResponsiveContainer, BarChart, Bar, Cell, XAxis, YAxis, Tooltip,
} from 'recharts'
import { Eye } from 'lucide-react'
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
            <p className="text-sm font-medium text-foreground">Overall Score</p>
            <p className="text-xs text-muted-foreground">Aggregate code health across categories</p>
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
  const { data: _reviewData } = useChartData<ReviewScores>('review-scores')
  const data = _reviewData ?? { categories: [], scores: [] }

  const overallScore = data.scores.length > 0 ? Math.round(data.scores.reduce((a, b) => a + b, 0) / data.scores.length) : 0

  if (data.categories.length === 0) {
    return (
      <PageTransition>
        <div className="space-y-6">
          <div>
            <h1 className="text-2xl font-semibold">Code Health</h1>
            <p className="text-sm text-muted-foreground">Track code quality metrics and review scores</p>
          </div>
          <div className="flex items-center justify-center rounded-xl border border-border bg-card py-16">
            <div className="text-center">
              <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-xl bg-muted">
                <Eye className="h-5 w-5 text-muted-foreground" />
              </div>
              <p className="text-sm text-muted-foreground">No health data available yet</p>
              <p className="text-xs text-muted-foreground mt-1">Code health scores appear after repositories are connected</p>
            </div>
          </div>
        </div>
      </PageTransition>
    )
  }

  return (
    <PageTransition>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold">Code Health</h1>
            <p className="text-sm text-muted-foreground">Track code quality metrics and review scores</p>
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
          </div>

          <div className="space-y-4">
            <OverallScore score={overallScore} />
          </div>
        </div>
      </div>
    </PageTransition>
  )
}
