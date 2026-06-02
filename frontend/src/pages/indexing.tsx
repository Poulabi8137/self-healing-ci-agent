import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Database, BookOpen, CheckCircle, Clock } from 'lucide-react'
import { toast } from 'sonner'
import { PageTransition } from '@/components/page-transition'
import { SpotlightCard } from '@/components/spotlight-card'
import { TiltCard } from '@/components/tilt-card'
import { StatusBadge } from '@/components/status-badge'
import { StaggerGrid, StaggerItem } from '@/components/stagger-grid'
import { GlassCard } from '@/components/GlassCard'
import { useTriggerIndex } from '@/lib/api'
import { demoIndexedRepos } from '@/lib/demo-data'

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

  return (
    <PageTransition>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-semibold">Repositories</h1>
          <p className="text-sm text-muted-foreground">Connect repositories for the agent to monitor and analyze</p>
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
                    Connecting...
                  </>
                ) : (
                  <><Database className="h-4 w-4" /> Connect Repository</>
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
                      <h3 className="text-sm font-medium">Connection Status</h3>
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
              </motion.div>
            ) : (
              <motion.div
                key="empty"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="space-y-4"
              >
                <TiltCard>
                  <SpotlightCard className="p-5">
                    <div className="mb-3 flex items-center gap-2">
                      <Database className="h-4 w-4 text-blue-500" />
                      <h3 className="text-sm font-medium">Connected Repositories</h3>
                    </div>
                    <div className="space-y-3">
                      {demoIndexedRepos.map((repo) => (
                        <div key={repo.name} className="flex items-center justify-between rounded-lg border border-border bg-background/50 p-3">
                          <div>
                            <p className="text-sm font-medium text-foreground">{repo.name}</p>
                            <p className="text-[10px] text-muted-foreground mt-0.5">{repo.url}</p>
                          </div>
                          <div className="flex items-center gap-3">
                            {repo.status === 'indexed' ? (
                              <>
                                <span className="text-[10px] text-muted-foreground">{repo.files} files</span>
                                <CheckCircle className="h-3.5 w-3.5 text-emerald-500" />
                              </>
                            ) : (
                              <>
                                <span className="text-[10px] text-amber-500">Indexing...</span>
                                <Clock className="h-3.5 w-3.5 text-amber-500" />
                              </>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </SpotlightCard>
                </TiltCard>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </PageTransition>
  )
}
