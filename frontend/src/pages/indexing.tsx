import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Database, BookOpen, HardDrive, Search, Activity } from 'lucide-react'
import { toast } from 'sonner'
import { PageTransition } from '@/components/page-transition'
import { StaggerGrid, StaggerItem } from '@/components/stagger-grid'
import { SpotlightCard } from '@/components/spotlight-card'
import { TiltCard } from '@/components/tilt-card'
import { StatusBadge } from '@/components/status-badge'
import { EmptyState } from '@/components/empty-state'
import { useTriggerIndex } from '@/lib/api'

export default function Indexing() {
  const [repoUrl, setRepoUrl] = useState('')
  const [branch, setBranch] = useState('')
  const [result, setResult] = useState<{ status: string; message: string; task_id?: number } | null>(null)

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

  const metrics = [
    { label: 'Chunks Indexed', value: 2847, icon: BookOpen },
    { label: 'Vector Dimensions', value: 1536, icon: HardDrive },
    { label: 'Avg Retrieval Score', value: 0.87, decimals: 2, icon: Search },
    { label: 'Index Size', value: 42, suffix: ' MB', icon: Database },
  ]

  return (
    <PageTransition>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold">Repository Indexing</h1>
            <p className="text-sm text-muted-foreground">Index repositories for RAG context</p>
          </div>
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <Activity className="h-3.5 w-3.5 text-emerald-500" />
            <span>{result ? 'Indexing active' : 'Ready'}</span>
          </div>
        </div>

        <StaggerGrid className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {metrics.map((m) => (
            <StaggerItem key={m.label}>
              <TiltCard>
                <SpotlightCard className="p-5">
                  <div className="mb-2 flex items-center gap-2">
                    <m.icon className="h-4 w-4 text-muted-foreground" />
                    <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">{m.label}</p>
                  </div>
                  <p className="font-mono text-2xl font-semibold tabular-nums">
                    {m.decimals ? m.value.toFixed(m.decimals) : m.value}{m.suffix ?? ''}
                  </p>
                </SpotlightCard>
              </TiltCard>
            </StaggerItem>
          ))}
        </StaggerGrid>

        <div className="grid gap-6 lg:grid-cols-[1fr_340px]">
          <SpotlightCard className="p-6">
            <h2 className="mb-4 text-sm font-medium text-muted-foreground">Index Repository</h2>
            <div className="space-y-4" role="form" aria-label="Index repository form">
              <div>
                <label htmlFor="index-url" className="mb-1.5 block text-xs font-medium text-muted-foreground">GitHub URL</label>
                <input
                  id="index-url"
                  value={repoUrl}
                  onChange={(e) => setRepoUrl(e.target.value)}
                  placeholder="https://github.com/my-org/my-repo"
                  className="w-full rounded-lg border border-input bg-background px-4 py-2.5 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                />
              </div>
              <div>
                <label htmlFor="index-branch" className="mb-1.5 block text-xs font-medium text-muted-foreground">Branch (optional)</label>
                <input
                  id="index-branch"
                  value={branch}
                  onChange={(e) => setBranch(e.target.value)}
                  placeholder="main"
                  className="w-full rounded-lg border border-input bg-background px-4 py-2.5 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                />
              </div>
              <motion.button
                onClick={handleSubmit}
                disabled={mutation.isPending}
                whileHover={{ scale: 1.01 }}
                whileTap={{ scale: 0.99 }}
                className="flex w-full items-center justify-center gap-2 rounded-lg bg-primary px-4 py-2.5 text-sm font-medium text-primary-foreground shadow-sm hover:opacity-90 disabled:opacity-50"
              >
                {mutation.isPending ? (
                  <>
                    <motion.div animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 1, ease: 'linear' }} className="h-4 w-4 rounded-full border-2 border-current border-t-transparent" />
                    Indexing...
                  </>
                ) : (
                  <><Database className="h-4 w-4" /> Start Indexing</>
                )}
              </motion.button>
            </div>
          </SpotlightCard>

          <AnimatePresence mode="wait">
            {result ? (
              <motion.div
                key="results"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                className="space-y-4"
              >
                <TiltCard>
                  <SpotlightCard className="p-5">
                    <div className="mb-3 flex items-center gap-2">
                      <Database className="h-4 w-4 text-emerald-500" />
                      <h3 className="text-sm font-medium">Index Status</h3>
                    </div>
                    <div className="space-y-2">
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-muted-foreground">Status</span>
                        <StatusBadge status={result.status === 'completed' ? 'passed' : result.status === 'running' ? 'running' : 'pending'} animated={false} />
                      </div>
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-muted-foreground">Message</span>
                        <span className="text-xs text-right max-w-[200px]">{result.message}</span>
                      </div>
                      {result.task_id && (
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-muted-foreground">Task ID</span>
                          <span className="font-mono text-xs">#{result.task_id}</span>
                        </div>
                      )}
                    </div>
                  </SpotlightCard>
                </TiltCard>

                <TiltCard>
                  <SpotlightCard className="p-5">
                    <h3 className="mb-3 text-sm font-medium">Recent Indexes</h3>
                    <div className="space-y-2">
                      {[
                        { repo: 'frontend-app', chunks: 1240, time: '2h ago', status: 'completed' as const },
                        { repo: 'api-service', chunks: 890, time: '5h ago', status: 'completed' as const },
                        { repo: 'infra-modules', chunks: 712, time: '1d ago', status: 'completed' as const },
                      ].map((idx) => (
                        <div key={idx.repo} className="flex items-center justify-between rounded-lg px-3 py-2 text-sm hover:bg-muted/50">
                          <div>
                            <p className="text-sm font-medium">{idx.repo}</p>
                            <p className="text-[10px] text-muted-foreground">{idx.chunks} chunks · {idx.time}</p>
                          </div>
                          <StatusBadge status={idx.status} animated={false} />
                        </div>
                      ))}
                    </div>
                  </SpotlightCard>
                </TiltCard>
              </motion.div>
            ) : (
              <motion.div
                key="empty"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="flex h-full min-h-[300px] items-center justify-center rounded-xl border border-border bg-card"
              >
                <EmptyState
                  icon={BookOpen}
                  title="No repositories indexed"
                  description="Submit a repository URL to start indexing."
                />
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </PageTransition>
  )
}
