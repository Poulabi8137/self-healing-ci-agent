import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Database, BookOpen, Clock, AlertTriangle, Activity, Wrench, Heart } from 'lucide-react'
import { toast } from 'sonner'
import { PageTransition } from '@/components/page-transition'
import { SpotlightCard } from '@/components/spotlight-card'
import { TiltCard } from '@/components/tilt-card'
import { StatusBadge } from '@/components/status-badge'
import { useTriggerIndex } from '@/lib/api'
import { demoIndexedRepos, demoActivities, demoRepos } from '@/lib/demo-data'
import { timeAgo } from '@/lib/time'

function repoHealth(repoName: string): { status: 'healthy' | 'degraded' | 'down'; label: string; color: string; bar: string } {
  const info = demoRepos.find(r => r.repository_name === repoName)
  if (!info) return { status: 'down', label: 'Unknown', color: 'text-zinc-500', bar: 'bg-zinc-500' }
  if (info.success_rate >= 80) return { status: 'healthy', label: 'Healthy', color: 'text-emerald-400', bar: 'bg-emerald-500' }
  if (info.success_rate >= 60) return { status: 'degraded', label: 'Degraded', color: 'text-amber-400', bar: 'bg-amber-500' }
  return { status: 'down', label: 'Critical', color: 'text-red-400', bar: 'bg-red-500' }
}

function repoActivity(repoName: string, type: string, limit = 3) {
  return demoActivities.filter(a => a.repo === repoName && a.type === type).slice(0, limit)
}

function repoIncidents(repoName: string) {
  return repoActivity(repoName, 'failure_detected')
}

function repoFixes(repoName: string) {
  return [...repoActivity(repoName, 'auto_resolved'), ...repoActivity(repoName, 'fix_generated')].slice(0, 3)
}

export default function Indexing() {
  const [repoUrl, setRepoUrl] = useState('')
  const [branch, setBranch] = useState('')
  const [_result, setResult] = useState<{ status: string; message: string; task_id?: number } | null>(null)
  const [heartbeat, setHeartbeat] = useState(0)

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
            <span className={`relative flex h-1.5 w-1.5`}>
              <span className={`absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75`} />
              <span className={`relative inline-flex h-1.5 w-1.5 rounded-full bg-emerald-500`} />
            </span>
            All systems monitored
          </div>
        </div>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {demoIndexedRepos.map((repo, i) => {
            const health = repoHealth(repo.name)
            const incidents = repoIncidents(repo.name)
            const fixes = repoFixes(repo.name)
            const info = demoRepos.find(r => r.repository_name === repo.name)
            return (
              <motion.div key={repo.name} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.05 }}>
                <TiltCard>
                  <SpotlightCard className="p-4">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2 min-w-0">
                        <span className={`relative flex h-2 w-2`}>
                          <span className={`absolute inline-flex h-full w-full animate-ping rounded-full ${health.bar} opacity-40`} />
                          <span className={`relative inline-flex h-2 w-2 rounded-full ${health.bar}`} />
                        </span>
                        <p className="text-sm font-medium truncate">{repo.name}</p>
                      </div>
                      <StatusBadge status={repo.status === 'indexed' ? 'passed' : 'running'} animated={repo.status === 'pending'} />
                    </div>
                    <div className="flex items-center gap-3 text-[10px] text-muted-foreground mb-3">
                      <span className={`font-medium ${health.color}`}>{health.label}</span>
                      <span>{info ? `${info.success_rate.toFixed(0)}% success` : '—'}</span>
                      <span>{info ? `${info.total_runs} runs` : '—'}</span>
                    </div>
                    {repo.lastIndexed && (
                      <p className="text-[10px] text-zinc-700 flex items-center gap-1 mb-3">
                        <Clock className="h-3 w-3" />
                        Last indexed {timeAgo(repo.lastIndexed)}
                      </p>
                    )}
                    <div className="space-y-1.5">
                      {incidents.length > 0 && (
                        <div className="flex items-center gap-1.5 text-[10px]">
                          <AlertTriangle className="h-3 w-3 text-red-500" />
                          <span className="text-red-400/80">{incidents.length} recent incident{incidents.length > 1 ? 's' : ''}</span>
                        </div>
                      )}
                      {fixes.length > 0 && (
                        <div className="flex items-center gap-1.5 text-[10px]">
                          <Wrench className="h-3 w-3 text-emerald-500" />
                          <span className="text-emerald-400/80">{fixes.length} auto-fix{fixes.length > 1 ? 'es' : ''}</span>
                        </div>
                      )}
                      {info && (
                        <div className="flex items-center gap-1.5 text-[10px]">
                          <Activity className="h-3 w-3 text-blue-500" />
                          <span className="text-blue-400/80">{info.avg_confidence.toFixed(2)} avg confidence</span>
                        </div>
                      )}
                    </div>
                    <div className="mt-3 h-1 rounded-full bg-zinc-800 overflow-hidden">
                      <motion.div
                        className={`h-full rounded-full ${health.bar}`}
                        initial={{ width: 0 }}
                        animate={{ width: `${info ? info.success_rate : 50}%` }}
                        transition={{ duration: 0.8, ease: 'easeOut' }}
                      />
                    </div>
                  </SpotlightCard>
                </TiltCard>
              </motion.div>
            )
          })}
        </div>

        <div className="grid gap-6 lg:grid-cols-[1fr_340px]">
          <SpotlightCard className="p-6">
            <div className="mb-4 flex items-center justify-between gap-2">
              <h2 className="text-sm font-medium text-muted-foreground">Connect Repository</h2>
              <button
                onClick={() => {
                  setRepoUrl('https://github.com/my-org/frontend-app')
                  setBranch('main')
                  setResult({ status: 'running', message: 'Indexing repository...', task_id: 42 })
                }}
                className="flex items-center gap-1.5 rounded-md border border-border px-2.5 py-1 text-[10px] font-medium text-muted-foreground hover:bg-accent transition-colors"
              >
                <BookOpen className="h-3 w-3" />
                Load Example
              </button>
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
              <motion.button onClick={handleSubmit} disabled={mutation.isPending} whileHover={{ scale: 1.01 }} whileTap={{ scale: 0.99 }} className="flex w-full items-center justify-center gap-2 rounded-lg bg-primary px-4 py-2.5 text-sm font-medium text-primary-foreground shadow-sm hover:opacity-90 disabled:opacity-50">
                {mutation.isPending ? (
                  <><span className="h-4 w-4 rounded-full border-2 border-current border-t-transparent animate-spin" />Connecting...</>
                ) : (
                  <><Database className="h-4 w-4" /> Connect Repository</>
                )}
              </motion.button>
            </div>
          </SpotlightCard>

          <div className="space-y-4">
            <SpotlightCard className="p-4">
              <div className="mb-3 flex items-center gap-2">
                <Activity className="h-3.5 w-3.5 text-zinc-500" />
                <span className="text-[11px] font-medium text-zinc-600 tracking-wider uppercase">Recent Activity</span>
              </div>
              <div className="space-y-2">
                {demoActivities.slice(0, 5).map((a) => (
                  <div key={a.id} className="flex items-center gap-2 text-[10px]">
                    <span className={`h-1.5 w-1.5 rounded-full ${
                      a.status === 'success' ? 'bg-emerald-500' :
                      a.status === 'failure' ? 'bg-red-500' : 'bg-amber-500'
                    }`} />
                    <span className="text-muted-foreground truncate flex-1">{a.message}</span>
                    <span className="text-zinc-700 shrink-0">{timeAgo(a.timestamp)}</span>
                  </div>
                ))}
              </div>
            </SpotlightCard>
            <SpotlightCard className="p-4">
              <div className="mb-3 flex items-center gap-2">
                <Heart className="h-3.5 w-3.5 text-zinc-500" />
                <span className="text-[11px] font-medium text-zinc-600 tracking-wider uppercase">System Pulse</span>
              </div>
              <div className="space-y-2 text-[10px]">
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">Monitored repos</span>
                  <span className="font-mono text-zinc-300">{demoIndexedRepos.length}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">Indexed</span>
                  <span className="font-mono text-emerald-400">{demoIndexedRepos.filter(r => r.status === 'indexed').length}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">Pending</span>
                  <span className="font-mono text-amber-400">{demoIndexedRepos.filter(r => r.status === 'pending').length}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">Total runs</span>
                  <span className="font-mono text-zinc-300">{demoRepos.reduce((s, r) => s + r.total_runs, 0)}</span>
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
