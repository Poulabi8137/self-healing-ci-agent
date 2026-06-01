import { PageTransition } from '@/components/page-transition'

export default function AdminKeys() {
  return (
    <PageTransition>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-semibold">API Keys</h1>
          <p className="text-sm text-muted-foreground">Manage API keys (admin only)</p>
        </div>
        <div className="rounded-xl border border-border bg-card p-6">
          <div className="flex h-48 items-center justify-center">
            <p className="text-sm text-muted-foreground">Key management — Phase 8</p>
          </div>
        </div>
      </div>
    </PageTransition>
  )
}
