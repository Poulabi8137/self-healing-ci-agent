import { useState, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { GitPullRequest, CheckCircle, ExternalLink, BookOpen, ArrowRight, Play } from 'lucide-react'
import { toast } from 'sonner'
import { PageTransition } from '@/components/page-transition'
import { SpotlightCard } from '@/components/spotlight-card'
import { TiltCard } from '@/components/tilt-card'
import { StatusBadge } from '@/components/status-badge'
import { useAgent } from '@/lib/agent-context'
import { useTriggerPR } from '@/lib/api'
import { demoExampleRepo, demoExampleLogs, demoPRUrl, demoPRNumber } from '@/lib/demo-data'

const LIFECYCLE_STAGES = [
  { id: 'draft', label: 'Draft Created', desc: 'Branch created from fix patch' },
  { id: 'validation', label: 'Validation Checks', desc: 'Running CI on PR branch' },
  { id: 'checks', label: 'All Checks Passing', desc: 'Build, tests, lint passed' },
  { id: 'review', label: 'Ready for Review', desc: 'Auto-assigned to code owners' },
  { id: 'merged', label: 'Merged', desc: 'Changes applied to target branch' },
]

export default function PR() {
  const { setState: setAgent } = useAgent()
  const [repo, setRepo] = useState('')
  const [logs, setLogs] = useState('')
  const [dryRun, setDryRun] = useState(true)
  const [stageIdx, setStageIdx] = useState(-1)
  const [progressing, setProgressing] = useState(false)
  const [result, setResult] = useState<{ pr_url?: string; pr_number?: number; status: string; message: string } | null>(null)

  const mutation = useTriggerPR()

  const handleLoadExample = useCallback(() => {
    setRepo(demoExampleRepo)
    setLogs(demoExampleLogs)
    setResult(null)
    setStageIdx(-1)
    setProgressing(false)
  }, [])

  const handleStartLifecycle = useCallback(() => {
    setProgressing(true)
    setStageIdx(0)
    setAgent({ label: 'Generating Fix', context: repo, color: 'blue' })
  }, [repo, setAgent])

  const handleAdvance = useCallback(() => {
    if (stageIdx < LIFECYCLE_STAGES.length - 1) {
      setStageIdx((i) => i + 1)
      const stage = LIFECYCLE_STAGES[stageIdx + 1]
      setAgent({ label: 'Generating Fix', context: stage.label, color: 'blue' })
    } else {
      setResult({ status: 'completed', message: `Pull request #${demoPRNumber} created successfully. The fix adds environment variable fallback for test environments and patches the ApiService error handling.`, pr_url: demoPRUrl, pr_number: demoPRNumber })
      setProgressing(false)
      setAgent({ label: 'Idle', color: 'zinc' })
    }
  }, [stageIdx, setAgent])

  async function handleSubmit() {
    if (!repo.trim() || !logs.trim()) {
      toast.error('Please enter both repository name and logs')
      return
    }
    setResult(null)
    setAgent({ label: 'Generating Fix', context: repo.trim(), color: 'blue' })
    try {
      const res = await mutation.mutateAsync({
        repository_name: repo.trim(),
        logs: logs.trim(),
        dry_run: dryRun,
        approved: !dryRun,
      })
      setResult(res as unknown as { pr_url?: string; pr_number?: number; status: string; message: string })
      setAgent({ label: 'Idle', color: 'zinc' })
    } catch {
      setAgent({ label: 'Monitoring', color: 'emerald' })
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
                onClick={handleLoadExample}
                className="flex items-center gap-1.5 rounded-md border border-border px-2.5 py-1 text-[10px] font-medium text-muted-foreground hover:bg-accent transition-colors"
              >
                <BookOpen className="h-3 w-3" />
                Load Example
              </button>
            </div>
            <div className="space-y-4" role="form" aria-label="PR creation form">
              <div>
                <label htmlFor="pr-repo" className="mb-1.5 block text-xs font-medium text-muted-foreground">Repository name</label>
                <input id="pr-repo" value={repo} onChange={(e) => setRepo(e.target.value)} placeholder="my-org/my-repo" className="w-full rounded-lg border border-input bg-background px-4 py-2.5 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring" />
              </div>
              <div>
                <label htmlFor="pr-logs" className="mb-1.5 block text-xs font-medium text-muted-foreground">CI/CD Logs</label>
                <textarea id="pr-logs" value={logs} onChange={(e) => setLogs(e.target.value)} placeholder="Paste CI/CD logs to generate PR..." rows={8} className="w-full rounded-lg border border-input bg-background px-4 py-2.5 text-sm font-mono placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring" />
              </div>
              <label className="flex items-center gap-2 text-sm">
                <input type="checkbox" checked={dryRun} onChange={(e) => setDryRun(e.target.checked)} className="rounded border-input" />
                Preview only (dry run)
              </label>
              <motion.button onClick={handleSubmit} disabled={mutation.isPending} whileHover={{ scale: 1.01 }} whileTap={{ scale: 0.99 }} className="flex w-full items-center justify-center gap-2 rounded-lg bg-primary px-4 py-2.5 text-sm font-medium text-primary-foreground shadow-sm hover:opacity-90 disabled:opacity-50">
                {mutation.isPending ? (
                  <><span className="h-4 w-4 rounded-full border-2 border-current border-t-transparent animate-spin" />{dryRun ? 'Previewing...' : 'Creating PR...'}</>
                ) : (
                  <><GitPullRequest className="h-4 w-4" /> {dryRun ? 'Preview Fix' : 'Create Pull Request'}</>
                )}
              </motion.button>
            </div>
          </SpotlightCard>

          <AnimatePresence mode="wait">
            {repo && !progressing && !result ? (
              <motion.div key="begin" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="flex items-center justify-center h-full min-h-[300px]">
                <motion.button
                  onClick={handleStartLifecycle}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  className="flex items-center gap-2 rounded-xl border border-blue-500/20 bg-blue-500/5 px-6 py-4 text-sm font-medium text-blue-400 hover:bg-blue-500/10 transition-colors"
                >
                  <Play className="h-4 w-4" />
                  Create Pull Request
                </motion.button>
              </motion.div>
            ) : progressing ? (
              <motion.div key="progressing" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="space-y-4">
                <SpotlightCard className="p-5">
                  <div className="mb-4 flex items-center gap-2">
                    <GitPullRequest className="h-4 w-4 text-blue-500" />
                    <span className="h-1.5 w-1.5 rounded-full bg-blue-500 animate-ping" />
                    <h2 className="text-sm font-medium">PR Lifecycle</h2>
                  </div>
                  <div className="space-y-0">
                    {LIFECYCLE_STAGES.map((stage, i) => {
                      const isActive = i === stageIdx
                      const isDone = i < stageIdx
                      return (
                        <div key={stage.id} className="flex gap-3">
                          <div className="flex flex-col items-center">
                            <div className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-full border ${
                              isDone ? 'border-emerald-500/30 bg-emerald-500/10' :
                              isActive ? 'border-blue-500/30 bg-blue-500/10' :
                              'border-zinc-700 bg-zinc-800/50'
                            }`}>
                              {isDone ? (
                                <CheckCircle className="h-3.5 w-3.5 text-emerald-500" />
                              ) : isActive ? (
                                <span className="h-3 w-3 rounded-full bg-blue-500 animate-pulse" />
                              ) : (
                                <span className="h-2 w-2 rounded-full bg-zinc-600" />
                              )}
                            </div>
                            {i < LIFECYCLE_STAGES.length - 1 && <div className="w-px flex-1 bg-zinc-800 my-0.5" />}
                          </div>
                          <div className={`pb-5 min-w-0 flex-1 ${!isActive && !isDone ? 'opacity-30' : ''}`}>
                            <p className={`text-xs font-medium ${isDone ? 'text-emerald-300' : isActive ? 'text-blue-300' : 'text-zinc-600'}`}>
                              {stage.label}
                            </p>
                            {isActive && <p className="mt-0.5 text-[10px] text-zinc-500">{stage.desc}</p>}
                          </div>
                        </div>
                      )
                    })}
                  </div>
                  <motion.button
                    onClick={handleAdvance}
                    whileHover={{ scale: 1.01 }}
                    whileTap={{ scale: 0.99 }}
                    className="mt-3 flex w-full items-center justify-center gap-1.5 rounded-lg border border-blue-500/20 bg-blue-500/5 px-4 py-2 text-xs font-medium text-blue-400 hover:bg-blue-500/10 transition-colors"
                  >
                    <ArrowRight className="h-3.5 w-3.5" />
                    {stageIdx < LIFECYCLE_STAGES.length - 1 ? `Proceed to "${LIFECYCLE_STAGES[stageIdx + 1].label}"` : 'Complete PR'}
                  </motion.button>
                </SpotlightCard>
              </motion.div>
            ) : result ? (
              <motion.div key="results" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: 20 }} transition={{ duration: 0.3 }} className="space-y-4">
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
              <motion.div key="empty" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="flex h-full min-h-[300px] items-center justify-center rounded-xl border border-border bg-card">
                <div className="text-center">
                  <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-xl bg-muted"><GitPullRequest className="h-5 w-5 text-muted-foreground" /></div>
                  <p className="text-sm text-muted-foreground">Load example data or submit logs to create a PR</p>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </PageTransition>
  )
}
