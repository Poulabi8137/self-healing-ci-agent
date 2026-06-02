import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { GitPullRequest, FileCode, CheckCircle, ExternalLink, GitBranch, GitCommit } from 'lucide-react'
import { toast } from 'sonner'
import { PageTransition } from '@/components/page-transition'
import { SpotlightCard } from '@/components/spotlight-card'
import { TiltCard } from '@/components/tilt-card'
import { StatusBadge } from '@/components/status-badge'
import { EmptyState } from '@/components/empty-state'
import { useTriggerPR } from '@/lib/api'

interface FileChange {
  path: string
  status: 'added' | 'modified' | 'deleted'
  lines: number
}

export default function PR() {
  const [repo, setRepo] = useState('')
  const [logs, setLogs] = useState('')
  const [dryRun, setDryRun] = useState(true)
  const [result, setResult] = useState<{ pr_url?: string; pr_number?: number; status: string; message: string } | null>(null)
  const [branchTimestamp] = useState(() => Date.now().toString(36))

  const mutation = useTriggerPR()

  const mockFiles: FileChange[] = [
    { path: 'src/deployment.yaml', status: 'modified', lines: 12 },
    { path: 'ci/pipeline.yml', status: 'modified', lines: 8 },
    { path: 'tests/test_deploy.py', status: 'added', lines: 45 },
    { path: 'config/prod.env', status: 'modified', lines: 3 },
    { path: 'README.md', status: 'modified', lines: 1 },
  ]

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
      toast.success(dryRun ? 'Dry run complete' : 'PR created successfully')
    } catch {
      toast.error('PR creation failed')
    }
  }

  return (
    <PageTransition>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold">Pull Requests</h1>
            <p className="text-sm text-muted-foreground">Automated PR creation</p>
          </div>
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <GitPullRequest className="h-3.5 w-3.5 text-purple-500" />
            <span>Auto-approval ready</span>
          </div>
        </div>

        <div className="grid gap-6 lg:grid-cols-2">
          <SpotlightCard className="p-6">
            <h2 className="mb-4 text-sm font-medium text-muted-foreground">PR Configuration</h2>
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
                Dry run (preview only)
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
                  <><GitPullRequest className="h-4 w-4" /> {dryRun ? 'Preview PR' : 'Create Pull Request'}</>
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

                <TiltCard>
                  <SpotlightCard className="p-5">
                    <div className="mb-3 flex items-center gap-2">
                      <FileCode className="h-4 w-4 text-blue-500" />
                      <h2 className="text-sm font-medium">File Changes ({mockFiles.length})</h2>
                    </div>
                    <div className="space-y-1">
                      {mockFiles.map((f, i) => (
                        <motion.div
                          key={f.path}
                          initial={{ opacity: 0, x: -8 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: i * 0.05 }}
                          className="flex items-center justify-between rounded-lg px-3 py-2 text-sm hover:bg-muted/50"
                        >
                          <div className="flex items-center gap-2 min-w-0">
                            <span className={`text-xs font-mono ${
                              f.status === 'added' ? 'text-emerald-500' :
                              f.status === 'deleted' ? 'text-red-500' : 'text-blue-500'
                            }`}>
                              {f.status === 'added' ? 'A' : f.status === 'deleted' ? 'D' : 'M'}
                            </span>
                            <span className="truncate font-mono text-xs">{f.path}</span>
                          </div>
                          <span className="text-xs text-muted-foreground">+{f.lines}</span>
                        </motion.div>
                      ))}
                    </div>
                  </SpotlightCard>
                </TiltCard>

                <TiltCard>
                  <SpotlightCard className="p-5">
                    <div className="mb-3 flex items-center gap-2">
                      <GitBranch className="h-4 w-4 text-muted-foreground" />
                      <h2 className="text-sm font-medium">Branch Details</h2>
                    </div>
                    <div className="space-y-2 text-xs">
                      <div className="flex items-center gap-2">
                        <GitBranch className="h-3 w-3 text-muted-foreground" />
                        <span className="text-muted-foreground">Base:</span>
                        <span className="font-mono">main</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <GitCommit className="h-3 w-3 text-muted-foreground" />
                        <span className="text-muted-foreground">Head:</span>
                        <span className="font-mono">fix/auto-{branchTimestamp}</span>
                      </div>
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
                  icon={GitPullRequest}
                  title="No PR generated yet"
                  description="Configure the PR and run a preview or create action."
                />
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </PageTransition>
  )
}
