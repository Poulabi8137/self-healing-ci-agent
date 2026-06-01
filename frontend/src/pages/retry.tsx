import { PageTransition } from '@/components/page-transition'

export default function Retry() {
  return (
    <PageTransition>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-semibold">Retry</h1>
          <p className="text-sm text-muted-foreground">Self-healing retry loop</p>
        </div>
        <div className="rounded-xl border border-border bg-card p-6">
          <div className="flex h-48 items-center justify-center">
            <p className="text-sm text-muted-foreground">Retry timeline — Phase 7</p>
          </div>
        </div>
      </div>
    </PageTransition>
  )
}
