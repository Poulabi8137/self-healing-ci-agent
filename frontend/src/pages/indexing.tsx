import { useState, useEffect } from 'react'
import { Database, Activity, Heart } from 'lucide-react'
import { toast } from 'sonner'
import { PageTransition } from '@/components/page-transition'
import { SpotlightCard } from '@/components/spotlight-card'
import { EmptyState } from '@/components/empty-state'
import { useTriggerIndex, useDashboardRepositories } from '@/lib/api'

export default function Indexing() {
  const [repoUrl, setRepoUrl] = useState('')
  const [branch, setBranch] = useState('')
  const [_result, setResult] = useState<{ status: string; message: string; task_id?: number } | null>(null)
  const [heartbeat, setHeartbeat] = useState(0)
  const { data: repos } = useDashboardRepositories()

  useEffect(() => {
    const t = setInterval(() => setHeartbeat((h) => h + 1), 3000)
    return () => clearInterval(t)
  }, [])

  const mutation = useTriggerIndex()

  async function handleSubmit() {
    if (!repoUrl.trim()) {
      toast.error('Please enter a repository URL')
      return
    }
    setResult(null)
    try {
      const res = await mutation.mutateAsync({
        repo_url: repoUrl.trim(),
        branch: branch.trim() || null,
      })
      setResult(res as unknown as { status: string; message: string; task_id?: number })
      toast.success('Indexing triggered')
    } catch {
      toast.error('Indexing failed')
    }
  }

  return (
    <PageTransition>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold">Repository Monitor</h1>
            <p className="text-sm text-muted-foreground">Live health and activity across all connected repositories</p>
          </div>
          <div className="flex items-center gap-1.5 text-[10px] text-zinc-600">
            <span className="relative flex h-1.5 w-1.5">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
              <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-emerald-500" />
            </span>
            All systems monitored
          </div>
        </div>

        {repos && repos.length > 0 ? (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {repos.map((r) => (
              <div key={r.repository_name} className="rounded-xl border border-[#1f1f23] bg-[#121216]/40 p-4">
                <div className="flex items-center justify-between mb-2">
                  <p className="text-sm font-medium truncate">{r.repository_name}</p>
                  <span className={`h-1.5 w-1.5 rounded-full ${r.success_rate >= 80 ? 'bg-emerald-500' : r.success_rate >= 60 ? 'bg-amber-500' : 'bg-red-500'}`} />
                </div>
                <div className="flex items-center gap-3 text-[10px] text-muted-foreground mb-3">
                  <span>{r.total_runs} runs</span>
                  <span>{r.success_rate.toFixed(0)}% success</span>
                  <span>{r.avg_confidence.toFixed(2)} confidence</span>
                </div>
                <div className="h-1 rounded-full bg-zinc-800 overflow-hidden">
                  <div className={`h-full rounded-full ${r.success_rate >= 80 ? 'bg-emerald-500' : r.success_rate >= 60 ? 'bg-amber-500' : 'bg-red-500'}`} style={{ width: `${r.success_rate}%` }} />
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="flex items-center justify-center rounded-xl border border-border bg-card py-16">
            <EmptyState icon={Activity} title="No repositories connected" description="Connect a GitHub repository to monitor its health." />
          </div>
        )}

        <div className="grid gap-6 lg:grid-cols-[1fr_340px]">
          <SpotlightCard className="p-6">
            <div className="mb-4 flex items-center gap-2">
              <h2 className="text-sm font-medium text-muted-foreground">Connect Repository</h2>
            </div>
            <div className="space-y-4" role="form" aria-label="Add repository form">
              <div>
                <label htmlFor="index-url" className="mb-1.5 block text-xs font-medium text-muted-foreground">GitHub URL</label>
                <input id="index-url" value={repoUrl} onChange={(e) => setRepoUrl(e.target.value)} placeholder="https://github.com/my-org/my-repo" className="w-full rounded-lg border border-input bg-background px-4 py-2.5 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring" />
              </div>
              <div>
                <label htmlFor="index-branch" className="mb-1.5 block text-xs font-medium text-muted-foreground">Branch (optional)</label>
                <input id="index-branch" value={branch} onChange={(e) => setBranch(e.target.value)} placeholder="main" className="w-full rounded-lg border border-input bg-background px-4 py-2.5 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring" />
              </div>
              <button onClick={handleSubmit} disabled={mutation.isPending} className="flex w-full items-center justify-center gap-2 rounded-lg bg-primary px-4 py-2.5 text-sm font-medium text-primary-foreground shadow-sm hover:opacity-90 disabled:opacity-50">
                {mutation.isPending ? (
                  <><span className="h-4 w-4 rounded-full border-2 border-current border-t-transparent animate-spin" />Connecting...</>
                ) : (
                  <><Database className="h-4 w-4" /> Connect Repository</>
                )}
              </button>
            </div>
          </SpotlightCard>

          <div className="space-y-4">
            <SpotlightCard className="p-4">
              <div className="mb-3 flex items-center gap-2">
                <Heart className="h-3.5 w-3.5 text-zinc-500" />
                <span className="text-[11px] font-medium text-zinc-600 tracking-wider uppercase">System Pulse</span>
              </div>
              <div className="space-y-2 text-[10px]">
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">Connected repos</span>
                  <span className="font-mono text-zinc-300">{repos?.length ?? 0}</span>
                </div>
                <div className="pt-2 border-t border-border">
                  <span className="text-zinc-700">Heartbeat: iteration {heartbeat}</span>
                </div>
              </div>
            </SpotlightCard>
          </div>
        </div>
      </div>
    </PageTransition>
  )
}
