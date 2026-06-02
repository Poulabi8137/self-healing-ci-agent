import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Shield, Bug, Package, Beaker, BookOpen } from 'lucide-react'
import { toast } from 'sonner'
import { PageTransition } from '@/components/page-transition'
import { StaggerGrid, StaggerItem } from '@/components/stagger-grid'
import { StatusBadge } from '@/components/status-badge'
import { SpotlightCard } from '@/components/spotlight-card'
import { TiltCard } from '@/components/tilt-card'
import { useTriggerValidation } from '@/lib/api'
import { demoExampleRepo, demoExampleLogs, demoValidationResult } from '@/lib/demo-data'
import type { ValidationCheckResult } from '@/lib/types'

export default function Validation() {
  const [repo, setRepo] = useState('')
  const [logs, setLogs] = useState('')
  const [result, setResult] = useState<ValidationCheckResult | null>(null)

  const mutation = useTriggerValidation()

  async function handleSubmit() {
    if (!repo.trim() || !logs.trim()) {
      toast.error('Please enter both repository name and logs')
      return
    }

    setResult(null)

    try {
      const data = await mutation.mutateAsync({
        repository_name: repo.trim(),
        logs: logs.trim(),
      })
      setResult(data as unknown as ValidationCheckResult)
      toast.success('Validation complete')
    } catch {
      toast.error('Validation failed')
    }
  }

  return (
    <PageTransition>
      <div className="mb-6">
        <h1 className="text-2xl font-semibold">Fix Validation</h1>
        <p className="text-sm text-muted-foreground">Validate generated patches against your CI/CD pipeline</p>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <SpotlightCard className="p-6">
          <div className="mb-4 flex items-center justify-between gap-2">
            <h2 className="text-sm font-medium text-muted-foreground">Patch Validation</h2>
            <button
              onClick={() => {
                setRepo(demoExampleRepo)
                setLogs(demoExampleLogs)
                setResult(demoValidationResult)
              }}
              className="flex items-center gap-1.5 rounded-md border border-border px-2.5 py-1 text-[10px] font-medium text-muted-foreground hover:bg-accent transition-colors"
            >
              <BookOpen className="h-3 w-3" />
              Load Example
            </button>
          </div>
          <div className="space-y-4" role="form" aria-label="Validation input form">
            <div>
              <label htmlFor="validation-repo" className="mb-1.5 block text-xs font-medium text-muted-foreground">Repository name</label>
              <input
                id="validation-repo"
                value={repo}
                onChange={(e) => setRepo(e.target.value)}
                placeholder="my-org/my-repo"
                className="w-full rounded-lg border border-input bg-background px-4 py-2.5 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
              />
            </div>
            <div>
              <label htmlFor="validation-logs" className="mb-1.5 block text-xs font-medium text-muted-foreground">CI/CD Logs</label>
              <textarea
                id="validation-logs"
                value={logs}
                onChange={(e) => setLogs(e.target.value)}
                placeholder="Paste CI/CD logs here..."
                rows={8}
                className="w-full rounded-lg border border-input bg-background px-4 py-2.5 text-sm font-mono placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
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
                  <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ repeat: Infinity, duration: 1, ease: 'linear' }}
                    className="h-4 w-4 rounded-full border-2 border-current border-t-transparent"
                  />
                  Validating...
                </>
              ) : (
                <>
                  <Shield className="h-4 w-4" />
                  Run Validation Pipeline
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
              <StaggerGrid className="grid gap-4">
                <StaggerItem>
                  <TiltCard>
                    <SpotlightCard className="p-5">
                      <div className="mb-3 flex items-center gap-2">
                        <Bug className="h-4 w-4 text-red-500" />
                        <h3 className="text-sm font-medium">Syntax Validation</h3>
                      </div>
                      <StatusBadge status={
                        result.validation.syntax_errors?.length === 0 ? 'passed' : 'failed'
                      } />
                      <p className="mt-2 text-xs text-muted-foreground">
                        {result.validation.syntax_errors?.length ?? 0} errors
                      </p>
                    </SpotlightCard>
                  </TiltCard>
                </StaggerItem>

                <StaggerItem>
                  <TiltCard>
                    <SpotlightCard className="p-5">
                      <div className="mb-3 flex items-center gap-2">
                        <Package className="h-4 w-4 text-blue-500" />
                        <h3 className="text-sm font-medium">Build Checks</h3>
                      </div>
                      <StatusBadge status={
                        result.validation.build_checks?.length === 0 ? 'passed' : 'partial'
                      } />
                      <p className="mt-2 text-xs text-muted-foreground">
                        {result.validation.build_checks?.length ?? 0} issues
                      </p>
                    </SpotlightCard>
                  </TiltCard>
                </StaggerItem>

                <StaggerItem>
                  <TiltCard>
                    <SpotlightCard className="p-5">
                      <div className="mb-3 flex items-center gap-2">
                        <Beaker className="h-4 w-4 text-purple-500" />
                        <h3 className="text-sm font-medium">Test Execution</h3>
                      </div>
                      <StatusBadge status={
                        result.validation.failed_tests?.length === 0 ? 'passed' : 'failed'
                      } />
                      <p className="mt-2 text-xs text-muted-foreground">
                        {result.validation.failed_tests?.length ?? 0} failed
                      </p>
                    </SpotlightCard>
                  </TiltCard>
                </StaggerItem>
              </StaggerGrid>

              <TiltCard>
                <SpotlightCard className="p-5">
                  <div className="mb-3 flex items-center gap-2">
                    <Shield className="h-4 w-4 text-foreground" />
                    <h3 className="text-sm font-medium">Overall Status</h3>
                  </div>
                  <StatusBadge status={result.validation.validation_status ?? 'unknown'} />
                  {!!(result.fix_proposal?.confidence) && (
                    <p className="mt-2 text-xs text-muted-foreground">
                      Fix confidence: {(result.fix_proposal.confidence * 100).toFixed(0)}%
                    </p>
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
                  <Shield className="h-5 w-5 text-muted-foreground" />
                </div>
                <p className="text-sm text-muted-foreground">Submit logs to validate a generated fix</p>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </PageTransition>
  )
}
