import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { GitPullRequest, CheckCircle, ExternalLink, BookOpen } from 'lucide-react'
import { toast } from 'sonner'
import { PageTransition } from '@/components/page-transition'
import { SpotlightCard } from '@/components/spotlight-card'
import { TiltCard } from '@/components/tilt-card'
import { StatusBadge } from '@/components/status-badge'
import { useTriggerPR } from '@/lib/api'
import { demoExampleRepo, demoExampleLogs, demoPRUrl, demoPRNumber } from '@/lib/demo-data'

export default function PR() {
  const [repo, setRepo] = useState('')
  const [logs, setLogs] = useState('')
  const [dryRun, setDryRun] = useState(true)
  const [result, setResult] = useState<{ pr_url?: string; pr_number?: number; status: string; message: string } | null>(null)

  const mutation = useTriggerPR()

  async function handleSubmit() {
    if (!repo.trim() || !logs.trim()) {
      toast.error('Please enter both repository name and logs')
      return
    }
    setResult(null)
    try {
      const res = await mutation.mutateAsync({
        repository_name: repo.trim(),
        logs: logs.trim(),
        dry_run: dryRun,
        approved: !dryRun,
      })
      setResult(res as unknown as { pr_url?: string; pr_number?: number; status: string; message: string })
      toast.success(dryRun ? 'Preview generated' : 'PR created')
    } catch {
      toast.error('PR creation failed')
    }
  }

  return (
    <PageTransition>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-semibold">Pull Requests</h1>
          <p className="text-sm text-muted-foreground">Create pull requests from auto-generated fixes</p>
        </div>

        <div className="grid gap-6 lg:grid-cols-2">
          <SpotlightCard className="p-6">
            <div className="mb-4 flex items-center justify-between gap-2">
              <h2 className="text-sm font-medium text-muted-foreground">PR Configuration</h2>
              <button
                onClick={() => {
                  setRepo(demoExampleRepo)
                  setLogs(demoExampleLogs)
                  setResult({ status: 'completed', message: 'Pull request #124 created successfully. The fix extends token refresh interval and adds environment variable fallback for test environments.', pr_url: demoPRUrl, pr_number: demoPRNumber })
                }}
                className="flex items-center gap-1.5 rounded-md border border-border px-2.5 py-1 text-[10px] font-medium text-muted-foreground hover:bg-accent transition-colors"
              >
                <BookOpen className="h-3 w-3" />
                Load Example
              </button>
            </div>
            <div className="space-y-4" role="form" aria-label="PR creation form">
              <div>
                <label htmlFor="pr-repo" className="mb-1.5 block text-xs font-medium text-muted-foreground">Repository name</label>
                <input
                  id="pr-repo"
                  value={repo}
                  onChange={(e) => setRepo(e.target.value)}
                  placeholder="my-org/my-repo"
                  className="w-full rounded-lg border border-input bg-background px-4 py-2.5 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                />
              </div>
              <div>
                <label htmlFor="pr-logs" className="mb-1.5 block text-xs font-medium text-muted-foreground">CI/CD Logs</label>
                <textarea
                  id="pr-logs"
                  value={logs}
                  onChange={(e) => setLogs(e.target.value)}
                  placeholder="Paste CI/CD logs to generate PR..."
                  rows={8}
                  className="w-full rounded-lg border border-input bg-background px-4 py-2.5 text-sm font-mono placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                />
              </div>
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={dryRun}
                  onChange={(e) => setDryRun(e.target.checked)}
                  className="rounded border-input"
                />
                Preview only (dry run)
              </label>
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
                    {dryRun ? 'Previewing...' : 'Creating PR...'}
                  </>
                ) : (
                  <><GitPullRequest className="h-4 w-4" /> {dryRun ? 'Preview Fix' : 'Create Pull Request'}</>
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
                transition={{ duration: 0.3 }}
                className="space-y-4"
              >
                <TiltCard>
                  <SpotlightCard className="p-5">
                    <div className="mb-3 flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <CheckCircle className="h-4 w-4 text-emerald-500" />
                        <h2 className="text-sm font-medium">PR Summary</h2>
                      </div>
                      <StatusBadge status={result.status === 'completed' ? 'passed' : 'partial'} animated={false} />
                    </div>
                    <p className="text-sm text-muted-foreground">{result.message}</p>
                    {result.pr_url && (
                      <a href={result.pr_url} target="_blank" rel="noreferrer" className="mt-3 inline-flex items-center gap-1 text-sm text-blue-500 hover:text-blue-400">
                        <ExternalLink className="h-3.5 w-3.5" />
                        View PR #{result.pr_number}
                      </a>
                    )}
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
                    <GitPullRequest className="h-5 w-5 text-muted-foreground" />
                  </div>
                  <p className="text-sm text-muted-foreground">No PR generated yet</p>
                  <p className="text-xs text-muted-foreground mt-1">Submit logs to preview or create a pull request</p>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </PageTransition>
  )
}
