import { useState, useCallback, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { Shield, Bug, Package, Beaker, ArrowRight, Play, RefreshCw, CheckCircle, XCircle, Lightbulb, TrendingDown, BarChart3 } from 'lucide-react'
import { toast } from 'sonner'
import { PageTransition } from '@/components/page-transition'
import { StaggerGrid, StaggerItem } from '@/components/stagger-grid'
import { StatusBadge } from '@/components/status-badge'
import { SpotlightCard } from '@/components/spotlight-card'
import { TiltCard } from '@/components/tilt-card'
import { useAgent } from '@/lib/agent-context'
import { useTriggerValidation } from '@/lib/api'
import { demoWorkflowLogsByType, demoRepos } from '@/lib/demo-data'
import { demoRootCauseCandidates, demoStrategyCandidates } from '@/lib/demo-candidates'
import { getDecisionEngine } from '@/lib/decision-engine'
import type { ValidationCheckResult, RootCauseCandidate, StrategyEvaluation, DecisionRecord } from '@/lib/types'

const FAILURE_TYPES = Object.keys(demoWorkflowLogsByType)

const PIPELINE_STAGES = [
  { id: 'unit', label: 'Unit Tests', passLabel: '139/140 passed' },
  { id: 'integration', label: 'Integration Tests', passLabel: '42/42 passed' },
  { id: 'lint', label: 'Lint & Format', passLabel: 'No issues' },
  { id: 'build', label: 'Build', passLabel: 'Compiled successfully' },
  { id: 'security', label: 'Security Scan', passLabel: '0 vulnerabilities' },
]

export default function Validation() {
  const { setState: setAgent, setMode, recordDecision, appendActivity, setHealthDelta, healthDelta } = useAgent()
  const [repo, setRepo] = useState('')
  const [logs, setLogs] = useState('')
  const [result, setResult] = useState<ValidationCheckResult | null>(null)
  const [stageIdx, setStageIdx] = useState(-1)
  const [running, setRunning] = useState(false)
  const [attemptCount, setAttemptCount] = useState(0)
  const [learning, setLearning] = useState<string | null>(null)
  const [reassessedCandidates, setReassessedCandidates] = useState<RootCauseCandidate[] | null>(null)
  const [newStrategy, setNewStrategy] = useState<StrategyEvaluation | null>(null)

  const engine = getDecisionEngine()
  const mutation = useTriggerValidation()
  const [searchParams] = useSearchParams()

  const [validationBreakdown, setValidationBreakdown] = useState<{
    baseChance: number
    healthFactor: number
    learningFactor: number
    complexityPenalty: number
    confidenceBoost: number
    effectiveChance: number
    threshold: number
  } | null>(null)

  // Auto-load investigation context from analysis page
  useEffect(() => {
    const repoParam = searchParams.get('repo')
    if (repoParam) {
      const entry = Object.values(demoWorkflowLogsByType).find(e => e.repo === repoParam)
      if (entry) {
        setRepo(entry.repo)
        setLogs(entry.logs)
      }
    }
  }, [searchParams])

  const handleLoadExample = useCallback((key: string) => {
    const entry = demoWorkflowLogsByType[key]
    if (!entry) return
    setRepo(entry.repo)
    setLogs(entry.logs)
    setResult(null)
    setStageIdx(-1)
    setRunning(false)
    setAttemptCount(0)
    setLearning(null)
    setReassessedCandidates(null)
    setNewStrategy(null)
  }, [])

  const handleRunValidation = useCallback(() => {
    setRunning(true)
    setStageIdx(0)
    setMode('validating', 'Validating', repo || 'patch')
  }, [repo, setMode])

  const handleAdvance = useCallback(() => {
    const entry = Object.values(demoWorkflowLogsByType).find(e => e.repo === repo)
    if (!entry) return

    if (stageIdx < PIPELINE_STAGES.length - 1) {
      setStageIdx((i) => i + 1)
      const stage = PIPELINE_STAGES[stageIdx + 1]
      setAgent({ label: 'Validating', context: stage.label, color: 'violet' })
    } else {
      // Use decision engine to determine outcome
      const failureKey = Object.keys(demoWorkflowLogsByType).find(k => demoWorkflowLogsByType[k].repo === repo)
      const repoInfo = demoRepos.find(r => r.repository_name === entry.repo)
      const candidates = failureKey ? demoRootCauseCandidates[failureKey] : undefined
      const strategies = failureKey ? demoStrategyCandidates[failureKey] : undefined

      if (candidates && strategies && repoInfo) {
        const evaluatedCandidates = engine.evaluateRootCauses(candidates, repoInfo.success_rate, repoInfo.avg_confidence)
        const evaluatedStrategies = engine.evaluateStrategies(evaluatedCandidates[0], strategies, {
          risk_level: 'medium',
          repo_health: repoInfo.success_rate,
          affected_files_count: evaluatedCandidates[0].affected_files.length,
          historical_success_rate: repoInfo.avg_confidence,
        })
        const outcome = engine.evaluateValidation(evaluatedStrategies[0], evaluatedCandidates[0], repoInfo.success_rate, attemptCount)

        if (outcome.passed) {
          setResult(entry.validation)
          setMode('validated_pass', 'Validation Passed', repo || 'patch')
          const valDec: DecisionRecord = {
            id: `val-${Date.now()}`,
            type: 'validation_outcome',
            context: repo || 'patch',
            outcome: 'Validation passed',
            confidence_before: evaluatedStrategies[0].success_probability,
            confidence_after: evaluatedStrategies[0].success_probability + outcome.confidence_impact,
            rationale: `All ${PIPELINE_STAGES.length} stages passed. Strategy score: ${(evaluatedStrategies[0].strategy_score * 100).toFixed(0)}%. Success probability: ${(evaluatedStrategies[0].success_probability * 100).toFixed(0)}%.`,
            evidence_used: ['validation_pipeline', 'strategy_evaluation'],
            timestamp: new Date().toISOString(),
          }
          recordDecision(valDec)
          engine.addBranchNode(null, `${repo}: Validation passed`, 'resolution', undefined, valDec)
          // Health impact: success
          const impact = engine.calculateHealthImpact(
            { repository_name: repo, total_runs: repoInfo.total_runs, success_rate: repoInfo.success_rate, avg_confidence: repoInfo.avg_confidence },
            'success',
            evaluatedStrategies[0].success_probability
          )
          setHealthDelta(healthDelta + impact.health_delta)
          const healthDec = engine.recordDecision(
            'health_impact',
            repo,
            `Repository health improved by +${impact.health_delta.toFixed(1)}`,
            repoInfo.avg_confidence,
            Math.min(1, repoInfo.avg_confidence + impact.confidence_delta),
            `Validation success: health +${impact.health_delta.toFixed(1)}, risk ${impact.risk_delta >= 0 ? '+' : ''}${impact.risk_delta.toFixed(2)}, confidence +${impact.confidence_delta.toFixed(2)}`,
            ['validation_pipeline', 'health_monitoring']
          )
          recordDecision(healthDec)
          appendActivity({
            type: 'validation_passed',
            message: `Validation passed for ${repo} (attempt ${attemptCount + 1})`,
            status: 'success',
          })
          // Store validation breakdown for display
          setValidationBreakdown({
            baseChance: evaluatedStrategies[0].success_probability,
            healthFactor: repoInfo.success_rate / 100 * 0.1,
            learningFactor: Math.min(attemptCount * 0.05, 0.2),
            complexityPenalty: Math.min(evaluatedCandidates[0].affected_files.length * 0.02, 0.1),
            confidenceBoost: evaluatedCandidates[0].confidence * 0.1,
            effectiveChance: evaluatedStrategies[0].success_probability + (repoInfo.success_rate / 100 * 0.1) + Math.min(attemptCount * 0.05, 0.2) - Math.min(evaluatedCandidates[0].affected_files.length * 0.02, 0.1) + evaluatedCandidates[0].confidence * 0.1,
            threshold: 0.65,
          })
        } else {
          // Validation failed - learning phase
          setMode('reassessing_after_failure', 'Reassessing After Failure', repo || 'patch')
          const reassessment = engine.reassessAfterFailure(
            evaluatedCandidates[0],
            evaluatedStrategies[0],
            outcome.failure_reason || 'Unknown failure',
            evaluatedCandidates,
            {
              risk_level: 'medium',
              repo_health: repoInfo.success_rate,
              affected_files_count: evaluatedCandidates[0].affected_files.length,
              historical_success_rate: repoInfo.avg_confidence,
            }
          )
          setReassessedCandidates(reassessment.updatedCandidates)
          setLearning(reassessment.learning)

          // Select new strategy from reassessed top candidate
          const newTopCandidate = reassessment.updatedCandidates[0]
          const newStrategies = engine.evaluateStrategies(newTopCandidate, strategies, {
            risk_level: 'high',
            repo_health: repoInfo.success_rate - 5,
            affected_files_count: newTopCandidate.affected_files.length,
            historical_success_rate: repoInfo.avg_confidence - 0.05,
          })
          setNewStrategy(newStrategies[0])

          const reassessDec: DecisionRecord = {
            id: `reassess-${Date.now()}`,
            type: 'reassessment',
            context: repo || 'patch',
            outcome: `Reassessing after failure: ${outcome.failure_reason}`,
            confidence_before: evaluatedStrategies[0].success_probability,
            confidence_after: newStrategies[0].success_probability,
            rationale: reassessment.learning,
            evidence_used: ['failure_analysis', 'reassessed_candidates'],
            timestamp: new Date().toISOString(),
          }
          recordDecision(reassessDec)
          engine.addBranchNode(null, `${repo}: ${outcome.failure_reason}`, 'failure', outcome.failure_reason, reassessDec)
          // Add reassessed hypotheses as child branches
          const altBranch = engine.addBranchNode(null, `Reassessed: ${newTopCandidate.error_category} (${(newTopCandidate.confidence * 100).toFixed(0)}%)`, 'root_cause', 'Reassessed — confidence adjusted after failure')
          reassessment.updatedCandidates.slice(1).forEach((alt) => {
            engine.addBranchNode(altBranch.id, `${alt.error_category} (${(alt.confidence * 100).toFixed(0)}%)`, 'root_cause', 'Rejected after reassessment')
          })
          // Health impact: failure
          const impact = engine.calculateHealthImpact(
            { repository_name: repo, total_runs: repoInfo.total_runs, success_rate: repoInfo.success_rate, avg_confidence: repoInfo.avg_confidence },
            'failure',
            evaluatedStrategies[0].success_probability
          )
          setHealthDelta(healthDelta + impact.health_delta)
          const healthDec = engine.recordDecision(
            'health_impact',
            repo,
            `Repository health decreased by ${Math.abs(impact.health_delta).toFixed(1)}`,
            repoInfo.avg_confidence,
            Math.max(0, repoInfo.avg_confidence + impact.confidence_delta),
            `Validation failure: health ${impact.health_delta.toFixed(1)}, risk +${impact.risk_delta.toFixed(2)}, confidence ${impact.confidence_delta.toFixed(2)}`,
            ['validation_pipeline', 'health_monitoring']
          )
          recordDecision(healthDec)
          appendActivity({
            type: 'reassessment',
            message: `Validation failed: ${outcome.failure_reason}. Reassessing hypotheses...`,
            status: 'failure',
          })
          // Store validation breakdown for display
          setValidationBreakdown({
            baseChance: evaluatedStrategies[0].success_probability,
            healthFactor: repoInfo.success_rate / 100 * 0.1,
            learningFactor: Math.min(attemptCount * 0.05, 0.2),
            complexityPenalty: Math.min(evaluatedCandidates[0].affected_files.length * 0.02, 0.1),
            confidenceBoost: evaluatedCandidates[0].confidence * 0.1,
            effectiveChance: evaluatedStrategies[0].success_probability + (repoInfo.success_rate / 100 * 0.1) + Math.min(attemptCount * 0.05, 0.2) - Math.min(evaluatedCandidates[0].affected_files.length * 0.02, 0.1) + evaluatedCandidates[0].confidence * 0.1,
            threshold: 0.65,
          })
        }
      }
      setRunning(false)
    }
  }, [stageIdx, repo, attemptCount, setAgent, setMode, recordDecision, appendActivity, engine, setHealthDelta, healthDelta])

  const handleTryAlternative = useCallback(() => {
    setAttemptCount((c) => c + 1)
    setResult(null)
    setStageIdx(-1)
    setRunning(false)
    setLearning(null)
    setMode('selecting_remediation_path', 'Selecting Remediation Path', `${repo} (attempt ${attemptCount + 2})`)
    appendActivity({
      type: 'strategy_selected',
      message: `New strategy selected after failure: ${newStrategy?.fix_summary.substring(0, 60)}...`,
      status: 'info',
    })
  }, [repo, attemptCount, newStrategy, setMode, appendActivity])

  const handleRunAgain = useCallback(() => {
    setResult(null)
    setStageIdx(-1)
    setRunning(true)
    setStageIdx(0)
    setMode('validating', 'Re-validating', repo || 'patch')
  }, [repo, setMode])

  async function handleSubmit() {
    if (!repo.trim() || !logs.trim()) {
      toast.error('Please enter both repository name and logs')
      return
    }
    setResult(null)
    setMode('validating', 'Validating', repo.trim())
    try {
      const data = await mutation.mutateAsync({ repository_name: repo.trim(), logs: logs.trim() })
      setResult(data as unknown as ValidationCheckResult)
      setAgent({ label: 'Idle', color: 'zinc' })
    } catch {
      setAgent({ label: 'Monitoring', color: 'emerald' })
      toast.error('Validation failed')
    }
  }

  const validationPassed = result?.validation.validation_status === 'passed'

  return (
    <PageTransition>
      <div className="mb-6">
        <h1 className="text-2xl font-semibold">Fix Validation</h1>
        <p className="text-sm text-muted-foreground">Condition-based validation with failure learning and strategy reassessment</p>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <SpotlightCard className="p-6">
          <div className="mb-4 flex items-center justify-between gap-2">
            <h2 className="text-sm font-medium text-muted-foreground">Patch Validation</h2>
            <select
              value=""
              onChange={(e) => handleLoadExample(e.target.value)}
              className="rounded-md border border-border bg-background px-2 py-1 text-[10px] font-medium text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring cursor-pointer max-w-[140px]"
            >
              <option value="">Load Example</option>
              {FAILURE_TYPES.map((type) => (
                <option key={type} value={type}>{type}</option>
              ))}
            </select>
          </div>
          <div className="space-y-4" role="form" aria-label="Validation input form">
            <div>
              <label htmlFor="validation-repo" className="mb-1.5 block text-xs font-medium text-muted-foreground">Repository name</label>
              <input id="validation-repo" value={repo} onChange={(e) => setRepo(e.target.value)} placeholder="my-org/my-repo" className="w-full rounded-lg border border-input bg-background px-4 py-2.5 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring" />
            </div>
            <div>
              <label htmlFor="validation-logs" className="mb-1.5 block text-xs font-medium text-muted-foreground">CI/CD Logs</label>
              <textarea id="validation-logs" value={logs} onChange={(e) => setLogs(e.target.value)} placeholder="Paste CI/CD logs here..." rows={8} className="w-full rounded-lg border border-input bg-background px-4 py-2.5 text-sm font-mono placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring" />
            </div>
            <motion.button onClick={handleSubmit} disabled={mutation.isPending} whileHover={{ scale: 1.01 }} whileTap={{ scale: 0.99 }} className="flex w-full items-center justify-center gap-2 rounded-lg bg-primary px-4 py-2.5 text-sm font-medium text-primary-foreground shadow-sm hover:opacity-90 disabled:opacity-50">
              {mutation.isPending ? (
                <><span className="h-4 w-4 rounded-full border-2 border-current border-t-transparent animate-spin" />Validating...</>
              ) : (
                <><Shield className="h-4 w-4" /> Run Validation Pipeline</>
              )}
            </motion.button>
          </div>
        </SpotlightCard>

        <AnimatePresence mode="wait">
          {repo && !running && !result ? (
            <motion.div key="begin" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="flex items-center justify-center h-full min-h-[300px]">
              <motion.button
                onClick={handleRunValidation}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                className="flex items-center gap-2 rounded-xl border border-violet-500/20 bg-violet-500/5 px-6 py-4 text-sm font-medium text-violet-400 hover:bg-violet-500/10 transition-colors"
              >
                <Play className="h-4 w-4" />
                Run Validation
              </motion.button>
            </motion.div>
          ) : running ? (
            <motion.div key="running" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="space-y-4">
              <SpotlightCard className="p-5">
                <div className="mb-4 flex items-center gap-2">
                  <span className="h-1.5 w-1.5 rounded-full bg-violet-500 animate-ping" />
                  <h2 className="text-sm font-medium">Validation Pipeline</h2>
                  {attemptCount > 0 && <span className="text-[10px] text-orange-400 font-medium">(Attempt {1 + attemptCount})</span>}
                </div>
                <div className="space-y-0">
                  {PIPELINE_STAGES.map((stage, i) => {
                    const isActive = i === stageIdx
                    const isDone = i < stageIdx
                    return (
                      <div key={stage.id} className="flex gap-3">
                        <div className="flex flex-col items-center">
                          <div className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-full border ${
                            isDone ? 'border-emerald-500/30 bg-emerald-500/10' :
                            isActive ? 'border-violet-500/30 bg-violet-500/10' :
                            'border-zinc-700 bg-zinc-800/50'
                          }`}>
                            {isDone ? (
                              <svg className="h-3.5 w-3.5 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" /></svg>
                            ) : isActive ? (
                              <span className="h-3 w-3 rounded-full bg-violet-500 animate-pulse" />
                            ) : (
                              <span className="h-2 w-2 rounded-full bg-zinc-600" />
                            )}
                          </div>
                          {i < PIPELINE_STAGES.length - 1 && <div className="w-px flex-1 bg-zinc-800 my-0.5" />}
                        </div>
                        <div className={`pb-5 min-w-0 flex-1 ${!isActive && !isDone ? 'opacity-30' : ''}`}>
                          <p className={`text-xs font-medium ${isDone ? 'text-emerald-300' : isActive ? 'text-violet-300' : 'text-zinc-600'}`}>
                            {stage.label}
                          </p>
                          {isActive && <p className="mt-0.5 text-[10px] text-violet-400/80">Running...</p>}
                          {isDone && <p className="mt-0.5 text-[10px] text-emerald-500/80">{stage.passLabel}</p>}
                        </div>
                      </div>
                    )
                  })}
                </div>
                <motion.button
                  onClick={handleAdvance}
                  whileHover={{ scale: 1.01 }}
                  whileTap={{ scale: 0.99 }}
                  className="mt-3 flex w-full items-center justify-center gap-1.5 rounded-lg border border-violet-500/20 bg-violet-500/5 px-4 py-2 text-xs font-medium text-violet-400 hover:bg-violet-500/10 transition-colors"
                >
                  <ArrowRight className="h-3.5 w-3.5" />
                  {stageIdx < PIPELINE_STAGES.length - 1 ? `Continue to ${PIPELINE_STAGES[stageIdx + 1].label}` : 'Complete Validation'}
                </motion.button>
              </SpotlightCard>
            </motion.div>
          ) : result ? (
            <motion.div key="results" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: 20 }} transition={{ duration: 0.3 }} className="space-y-4">
              <div className="flex items-center gap-2 mb-3">
                {validationPassed ? (
                  <><CheckCircle className="h-4 w-4 text-emerald-500" /><span className="text-xs font-medium text-emerald-400">Validation passed</span></>
                ) : (
                  <><XCircle className="h-4 w-4 text-red-500" /><span className="text-xs font-medium text-red-400">Validation failed</span></>
                )}
              </div>
              <StaggerGrid className="grid gap-4">
                <StaggerItem>
                  <TiltCard>
                    <SpotlightCard className="p-5">
                      <div className="mb-3 flex items-center gap-2">
                        <Bug className="h-4 w-4 text-red-500" />
                        <h3 className="text-sm font-medium">Syntax Validation</h3>
                      </div>
                      <StatusBadge status={result.validation.syntax_errors?.length === 0 ? 'passed' : 'failed'} />
                      <p className="mt-2 text-xs text-muted-foreground">{(result.validation.syntax_errors as string[])?.length ?? 0} errors</p>
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
                      <StatusBadge status={result.validation.build_checks?.length === 0 ? 'passed' : 'partial'} />
                      <p className="mt-2 text-xs text-muted-foreground">{result.validation.build_checks?.length ?? 0} issues</p>
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
                      <StatusBadge status={result.validation.failed_tests?.length === 0 ? 'passed' : 'failed'} />
                      <p className="mt-2 text-xs text-muted-foreground">{(result.validation.failed_tests as Array<{test: string; reason: string}>)?.length ?? 0} failed</p>
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
                    <p className="mt-2 text-xs text-muted-foreground">Fix confidence: {(result.fix_proposal.confidence * 100).toFixed(0)}%</p>
                  )}
                  {validationBreakdown && (
                    <div className="mt-3 rounded-lg border border-zinc-800 bg-zinc-900/30 p-3">
                      <div className="flex items-center gap-1.5 mb-1.5">
                        <BarChart3 className="h-3 w-3 text-violet-400" />
                        <span className="text-[10px] font-medium text-violet-400">Validation Decision</span>
                      </div>
                      <div className="space-y-0.5 text-[9px]">
                        <div className="flex justify-between"><span className="text-zinc-500">Base Chance</span><span className="text-zinc-300 font-mono">{(validationBreakdown.baseChance * 100).toFixed(1)}%</span></div>
                        <div className="flex justify-between"><span className="text-zinc-500">Health Factor</span><span className={validationBreakdown.healthFactor >= 0 ? 'text-emerald-400 font-mono' : 'text-zinc-300 font-mono'}>+{(validationBreakdown.healthFactor * 100).toFixed(1)}%</span></div>
                        <div className="flex justify-between"><span className="text-zinc-500">Learning Factor</span><span className="text-emerald-400 font-mono">+{(validationBreakdown.learningFactor * 100).toFixed(1)}%</span></div>
                        <div className="flex justify-between"><span className="text-zinc-500">Complexity Penalty</span><span className="text-red-400 font-mono">-{(validationBreakdown.complexityPenalty * 100).toFixed(1)}%</span></div>
                        <div className="flex justify-between"><span className="text-zinc-500">Confidence Boost</span><span className="text-emerald-400 font-mono">+{(validationBreakdown.confidenceBoost * 100).toFixed(1)}%</span></div>
                        <div className="border-t border-zinc-800 pt-0.5 mt-0.5 flex justify-between font-medium">
                          <span className="text-zinc-400">Effective Probability</span>
                          <span className="text-zinc-200 font-mono">{(validationBreakdown.effectiveChance * 100).toFixed(1)}%</span>
                        </div>
                        <div className="flex justify-between"><span className="text-zinc-500">Threshold</span><span className="text-zinc-300 font-mono">{(validationBreakdown.threshold * 100).toFixed(0)}%</span></div>
                        <div className="flex justify-between pt-0.5">
                          <span className="text-zinc-400 text-[10px] font-medium">Outcome</span>
                          <span className={validationPassed ? 'text-emerald-400 text-[10px] font-medium' : 'text-red-400 text-[10px] font-medium'}>
                            {validationPassed ? 'Passed' : 'Failed'}
                          </span>
                        </div>
                      </div>
                    </div>
                  )}
                  {learning && !validationPassed && (
                    <div className="mt-3 rounded-lg border border-orange-500/20 bg-orange-500/5 p-3">
                      <div className="flex items-center gap-1.5 mb-1">
                        <TrendingDown className="h-3 w-3 text-orange-400" />
                        <span className="text-[10px] font-medium text-orange-400">Failure Learning</span>
                      </div>
                      <p className="text-[10px] text-zinc-400">{learning}</p>
                      {reassessedCandidates && (
                        <div className="mt-2 space-y-1">
                          <p className="text-[10px] font-medium text-muted-foreground">Re-ranked hypotheses:</p>
                          {reassessedCandidates.map((c, i) => (
                            <div key={i} className="flex items-center justify-between text-[10px]">
                              <span className="text-zinc-500">{c.error_category}</span>
                              <span className="font-mono text-amber-400">{(c.confidence * 100).toFixed(0)}%</span>
                            </div>
                          ))}
                        </div>
                      )}
                      {newStrategy && (
                        <div className="mt-2 rounded-lg border border-zinc-800 bg-zinc-800/30 p-2">
                          <div className="flex items-center gap-1.5 mb-1">
                            <Lightbulb className="h-3 w-3 text-blue-400" />
                            <span className="text-[10px] font-medium text-blue-400">New strategy selected</span>
                          </div>
                          <p className="text-[10px] text-zinc-400">{newStrategy.fix_summary.substring(0, 100)}...</p>
                          <div className="flex items-center gap-2 mt-1">
                            <span className="text-[10px] text-emerald-400">{(newStrategy.success_probability * 100).toFixed(0)}% success</span>
                            <span className="text-[10px] text-amber-400">{newStrategy.risk_level} risk</span>
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                  {healthDelta !== 0 && (
                    <div className="mt-3 flex items-center gap-3 text-[9px] text-zinc-600 border-t border-border pt-3">
                      <span>Health: <span className={healthDelta >= 0 ? 'text-emerald-400' : 'text-red-400'}>{healthDelta >= 0 ? '+' : ''}{healthDelta.toFixed(1)}</span></span>
                      <span>Confidence: <span className={healthDelta >= 0 ? 'text-emerald-400' : 'text-red-400'}>{healthDelta >= 0 ? '+' : ''}{(healthDelta * 0.6).toFixed(2)}</span></span>
                      <span>Risk: <span className={healthDelta >= 0 ? 'text-emerald-400' : 'text-red-400'}>{healthDelta >= 0 ? '-' : '+'}{(Math.abs(healthDelta) * 0.1).toFixed(2)}</span></span>
                      {!validationPassed && <span className="text-orange-400">Agent learning from failure</span>}
                    </div>
                  )}
                  <div className="mt-4 flex flex-wrap gap-2">
                    {validationPassed ? (
                      <a href="/pr" className="inline-flex items-center gap-1.5 rounded-md border border-blue-500/20 bg-blue-500/5 px-3 py-1.5 text-[10px] font-medium text-blue-400 hover:bg-blue-500/10 transition-colors">
                        Create PR with this fix <ArrowRight className="h-3 w-3" />
                      </a>
                    ) : (
                      <>
                        {newStrategy && (
                          <button
                            onClick={handleTryAlternative}
                            className="inline-flex items-center gap-1.5 rounded-md border border-orange-500/20 bg-orange-500/5 px-3 py-1.5 text-[10px] font-medium text-orange-400 hover:bg-orange-500/10 transition-colors"
                          >
                            <RefreshCw className="h-3 w-3" />
                            Try new strategy (attempt {attemptCount + 2})
                          </button>
                        )}
                        <button
                          onClick={handleRunAgain}
                          className="inline-flex items-center gap-1.5 rounded-md border border-violet-500/20 bg-violet-500/5 px-3 py-1.5 text-[10px] font-medium text-violet-400 hover:bg-violet-500/10 transition-colors"
                        >
                          <RefreshCw className="h-3 w-3" />
                          Re-run validation
                        </button>
                      </>
                    )}
                  </div>
                </SpotlightCard>
              </TiltCard>
            </motion.div>
          ) : (
            <motion.div key="empty" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="flex h-full min-h-[300px] items-center justify-center rounded-xl border border-border bg-card">
              <div className="text-center">
                <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-xl bg-muted"><Shield className="h-5 w-5 text-muted-foreground" /></div>
                <p className="text-sm text-muted-foreground">Load example data or submit logs to run validation</p>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </PageTransition>
  )
}
