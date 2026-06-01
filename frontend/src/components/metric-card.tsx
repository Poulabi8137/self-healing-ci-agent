import { AnimatedCounter } from '@/components/animated-counter'
import { SpotlightCard } from '@/components/spotlight-card'
import { TiltCard } from '@/components/tilt-card'

export function MetricCard({
  label,
  value,
  prefix,
  suffix = '',
  decimals = 0,
  trend,
}: {
  label: string
  value: number
  prefix?: string
  suffix?: string
  decimals?: number
  trend?: { value: number; positive: boolean }
}) {
  return (
    <TiltCard>
      <SpotlightCard className="p-5">
        <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">{label}</p>
        <p className="mt-2 font-mono text-2xl font-semibold tabular-nums tracking-tight">
          <AnimatedCounter value={value} decimals={decimals} prefix={prefix} suffix={suffix} />
        </p>
        {trend && (
          <p
            className={`mt-1 text-xs ${
              trend.positive ? 'text-emerald-500' : 'text-red-500'
            }`}
          >
            {trend.positive ? '↑' : '↓'} {Math.abs(trend.value)}% from last week
          </p>
        )}
      </SpotlightCard>
    </TiltCard>
  )
}
