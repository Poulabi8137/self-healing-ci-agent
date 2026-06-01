import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Search, FileCode, AlertTriangle, CheckCircle } from 'lucide-react'
import { toast } from 'sonner'
import { PageTransition } from '@/components/page-transition'
import { StatusBadge } from '@/components/status-badge'
import { SpotlightCard } from '@/components/spotlight-card'
import { TiltCard } from '@/components/tilt-card'
import { useTriggerAnalysis, useTriggerFix } from '@/lib/api'

export default function Analysis() {
  const [repo, setRepo] = useState('')
  const [logs, setLogs] = useState('')
  const [result, setResult] = useState<Record<string, unknown> | null>(null)
  const [fix, setFix] = useState<Record<string, unknown> | null>(null)

  const analysisMutation = useTriggerAnalysis()
  const fixMutation = useTriggerFix()

  async function handleSubmit() {
    if (!repo.trim() || !logs.trim()) {
      toast.error('Please enter both repository name and logs')
      return
    }

    setResult(null)
    setFix(null)

    try {
      const analysisResult = await analysisMutation.mutateAsync({
        repository_name: repo.trim(),
        logs: logs.trim(),
      })
      setResult(analysisResult as Record<string, unknown>)
      toast.success('Analysis complete')

      const fixResult = await fixMutation.mutateAsync({
        repository_name: repo.trim(),
        logs: logs.trim(),
      })
      setFix(fixResult as Record<string, unknown>)
      toast.success('Fix generated')
    } catch {
      toast.error('Analysis failed. Check server logs.')
    }
  }

  const isRunning = analysisMutation.isPending || fixMutation.isPending

  return (
    <PageTransition>
      <div className="mb-6">
        <h1 className="text-2xl font-semibold">Analysis</h1>
        <p className="text-sm text-muted-foreground">Root cause analysis for CI/CD failures</p>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <SpotlightCard className="p-6">
          <h2 className="mb-4 text-sm font-medium text-muted-foreground">CI/CD Log Input</h2>
          <div className="space-y-4">
            <div>
              <label className="mb-1.5 block text-xs font-medium text-muted-foreground">Repository name</label>
              <input
                value={repo}
                onChange={(e) => setRepo(e.target.value)}
                placeholder="my-org/my-repo"
                className="w-full rounded-lg border border-input bg-background px-4 py-2.5 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
              />
            </div>
            <div>
              <label className="mb-1.5 block text-xs font-medium text-muted-foreground">CI/CD Logs</label>
              <textarea
                value={logs}
                onChange={(e) => setLogs(e.target.value)}
                placeholder="Paste CI/CD logs here..."
                rows={10}
                className="w-full rounded-lg border border-input bg-background px-4 py-2.5 text-sm font-mono placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
              />
            </div>
            <motion.button
              onClick={handleSubmit}
              disabled={isRunning}
              whileHover={{ scale: 1.01 }}
              whileTap={{ scale: 0.99 }}
              className="flex w-full items-center justify-center gap-2 rounded-lg bg-primary px-4 py-2.5 text-sm font-medium text-primary-foreground shadow-sm hover:opacity-90 disabled:opacity-50"
            >
              {isRunning ? (
                <>
                  <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ repeat: Infinity, duration: 1, ease: 'linear' }}
                    className="h-4 w-4 rounded-full border-2 border-current border-t-transparent"
                  />
                  {analysisMutation.isPending ? 'Analyzing...' : 'Generating fix...'}
                </>
              ) : (
                <>
                  <Search className="h-4 w-4" />
                  Analyze & Generate Fix
                </>
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
                  <div className="mb-3 flex items-center gap-2">
                    <AlertTriangle className="h-4 w-4 text-yellow-500" />
                    <h2 className="text-sm font-medium">Root Cause</h2>
                  </div>
                  <p className="text-sm text-muted-foreground">{result.root_cause as string}</p>
                  <div className="mt-3 flex items-center gap-4">
                    <StatusBadge status={(result.error_category as string) ?? 'unknown'} />
                    <span className="text-xs text-muted-foreground">
                      Confidence: {((result.confidence as number) * 100).toFixed(0)}%
                    </span>
                  </div>
                </SpotlightCard>
              </TiltCard>

              <TiltCard>
                <SpotlightCard className="p-5">
                  <div className="mb-3 flex items-center gap-2">
                    <FileCode className="h-4 w-4 text-blue-500" />
                    <h2 className="text-sm font-medium">Affected Files</h2>
                  </div>
                  {(result.affected_files as string[])?.length > 0 ? (
                    <ul className="space-y-1">
                      {(result.affected_files as string[]).map((f, i) => (
                        <motion.li
                          key={f}
                          initial={{ opacity: 0, x: -8 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: i * 0.05 }}
                          className="text-sm font-mono text-muted-foreground"
                        >
                          {f}
                        </motion.li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-sm text-muted-foreground">No files identified</p>
                  )}
                </SpotlightCard>
              </TiltCard>

              {fix && (
                <TiltCard>
                  <SpotlightCard className="p-5">
                    <div className="mb-3 flex items-center gap-2">
                      <CheckCircle className="h-4 w-4 text-emerald-500" />
                      <h2 className="text-sm font-medium">Fix Summary</h2>
                    </div>
                    <p className="text-sm text-muted-foreground">{fix.fix_summary as string}</p>
                    {(fix.assumptions as string[])?.length > 0 && (
                      <div className="mt-3">
                        <p className="mb-1 text-xs font-medium text-muted-foreground">Assumptions:</p>
                        <ul className="space-y-0.5">
                          {(fix.assumptions as string[]).map((a, i) => (
                            <li key={i} className="text-xs text-muted-foreground">• {a}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </SpotlightCard>
                </TiltCard>
              )}

              {!!(fix?.patch) && (
                <TiltCard>
                  <SpotlightCard className="p-5">
                    <div className="mb-3 flex items-center gap-2">
                      <FileCode className="h-4 w-4 text-purple-500" />
                      <h2 className="text-sm font-medium">Patch Preview</h2>
                    </div>
                    <pre className="overflow-x-auto rounded-lg bg-background p-4 text-xs text-muted-foreground">
                      <code>{fix.patch as string}</code>
                    </pre>
                  </SpotlightCard>
                </TiltCard>
              )}
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
                  <Search className="h-5 w-5 text-muted-foreground" />
                </div>
                <p className="text-sm text-muted-foreground">Results will appear here</p>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </PageTransition>
  )
}
