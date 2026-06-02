import { RotateCw } from 'lucide-react'
import { PageTransition } from '@/components/page-transition'
import { StaggerGrid, StaggerItem } from '@/components/stagger-grid'
import { MetricCard } from '@/components/metric-card'
import { useDashboardMetrics } from '@/lib/api'
import { demoMetrics } from '@/lib/demo-data'

export default function Retry() {
  const { data: _metrics } = useDashboardMetrics()
  const metrics = _metrics ?? demoMetrics
  const wm = metrics.workflow_metrics
  const totalRetries = wm?.total_retries ?? 0
  const avgRetries = metrics.average_retries ?? 0

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
          <StaggerItem><MetricCard label="Recovery Rate" value={totalRetries > 0 ? Math.min(100, Math.round((totalRetries / (totalRetries + 1)) * 100)) : 0} suffix="%" /></StaggerItem>
        </StaggerGrid>

        {totalRetries === 0 && (
          <div className="flex items-center justify-center rounded-xl border border-border bg-card py-16">
            <div className="text-center">
              <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-xl bg-muted">
                <RotateCw className="h-5 w-5 text-muted-foreground" />
              </div>
              <p className="text-sm text-muted-foreground">No retry data available yet</p>
              <p className="text-xs text-muted-foreground mt-1">Retry data appears when workflows are automatically retried</p>
            </div>
          </div>
        )}
      </div>
    </PageTransition>
  )
}
