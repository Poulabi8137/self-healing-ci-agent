import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Database, BookOpen } from 'lucide-react'
import { toast } from 'sonner'
import { PageTransition } from '@/components/page-transition'
import { SpotlightCard } from '@/components/spotlight-card'
import { TiltCard } from '@/components/tilt-card'
import { StatusBadge } from '@/components/status-badge'
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

  return (
    <PageTransition>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-semibold">Repositories</h1>
          <p className="text-sm text-muted-foreground">Connect repositories for the agent to monitor and analyze</p>
        </div>

        <div className="grid gap-6 lg:grid-cols-[1fr_340px]">
          <SpotlightCard className="p-6">
            <h2 className="mb-4 text-sm font-medium text-muted-foreground">Connect Repository</h2>
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
                className="flex h-full min-h-[300px] items-center justify-center rounded-xl border border-border bg-card"
              >
                <div className="text-center">
                  <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-xl bg-muted">
                    <BookOpen className="h-5 w-5 text-muted-foreground" />
                  </div>
                  <p className="text-sm text-muted-foreground">No repositories connected</p>
                  <p className="text-xs text-muted-foreground mt-1">Add a repository URL to start monitoring</p>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </PageTransition>
  )
}
