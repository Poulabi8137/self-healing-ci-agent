import { RotateCw } from 'lucide-react'
import { PageTransition } from '@/components/page-transition'
import { StaggerGrid, StaggerItem } from '@/components/stagger-grid'
import { MetricCard } from '@/components/metric-card'
import { EmptyState } from '@/components/empty-state'
import { useDashboardMetrics } from '@/lib/api'

export default function Retry() {
  const { data: _metrics } = useDashboardMetrics()
  const metrics = _metrics ?? null
  const wm = metrics?.workflow_metrics
  const totalRetries = wm?.total_retries ?? 0
  const avgRetries = metrics?.average_retries ?? 0

  return (
    <PageTransition>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-semibold">Retry & Recovery</h1>
          <p className="text-sm text-muted-foreground">Track workflow retries and automated recovery attempts</p>
        </div>

        <StaggerGrid className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <StaggerItem><MetricCard label="Total Retries" value={totalRetries} /></StaggerItem>
          <StaggerItem><MetricCard label="Avg Retries/Run" value={avgRetries} decimals={2} /></StaggerItem>
          <StaggerItem><MetricCard label="Resolved" value={0} /></StaggerItem>
          <StaggerItem><MetricCard label="In Progress" value={0} /></StaggerItem>
        </StaggerGrid>

        <div className="flex items-center justify-center rounded-xl border border-border bg-card py-16">
          <EmptyState icon={RotateCw} title="No retry data available yet" description="Retry data appears when workflows are automatically retried" />
        </div>
      </div>
    </PageTransition>
  )
}
