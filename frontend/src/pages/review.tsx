import { PageTransition } from '@/components/page-transition'

export default function Review() {
  return (
    <PageTransition>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-semibold">Review</h1>
          <p className="text-sm text-muted-foreground">Multi-agent review scores</p>
        </div>
        <div className="rounded-xl border border-border bg-card p-6">
          <div className="flex h-48 items-center justify-center">
            <p className="text-sm text-muted-foreground">Review scores — Phase 7</p>
          </div>
        </div>
      </div>
    </PageTransition>
  )
}
