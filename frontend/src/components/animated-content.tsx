import { motion, AnimatePresence } from 'framer-motion'
import type { ReactNode } from 'react'

function SkeletonPulse({ className }: { className?: string }) {
  return <div className={`animate-pulse rounded bg-muted ${className ?? ''}`} />
}

export function MetricSkeleton() {
  return (
    <div className="rounded-xl border border-border bg-card p-5">
      <SkeletonPulse className="mb-3 h-3 w-24" />
      <SkeletonPulse className="mb-2 h-8 w-20" />
      <SkeletonPulse className="h-3 w-32" />
    </div>
  )
}

export function ChartSkeleton() {
  return (
    <div className="rounded-xl border border-border bg-card p-6">
      <div className="flex h-64 items-center justify-center">
        <div className="h-48 w-full animate-pulse rounded bg-muted" />
      </div>
    </div>
  )
}

export function AnimatedContent({
  isLoading,
  skeleton,
  children,
}: {
  isLoading: boolean
  skeleton: ReactNode
  children: ReactNode
}) {
  return (
    <AnimatePresence mode="wait">
      {isLoading ? (
        <motion.div
          key="skeleton"
          exit={{ opacity: 0, y: -8 }}
          transition={{ duration: 0.2 }}
        >
          {skeleton}
        </motion.div>
      ) : (
        <motion.div
          key="content"
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
        >
          {children}
        </motion.div>
      )}
    </AnimatePresence>
  )
}
