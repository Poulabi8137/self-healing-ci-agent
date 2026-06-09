import { useState, useCallback, useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { Search, FileCode, AlertTriangle, CheckCircle, Cpu, ArrowRight, Play, Lightbulb, GitBranch, BarChart3, XCircle } from 'lucide-react'
import { toast } from 'sonner'
import { PageTransition } from '@/components/page-transition'
import { StatusBadge } from '@/components/status-badge'
import { SpotlightCard } from '@/components/spotlight-card'
import { TiltCard } from '@/components/tilt-card'
import { useAgent } from '@/lib/agent-context'
import { useTriggerAnalysis, useTriggerFix } from '@/lib/api'
import { demoWorkflowLogsByType, demoRepos } from '@/lib/demo-data'
import { demoRootCauseCandidates, demoStrategyCandidates } from '@/lib/demo-candidates'
import { getDecisionEngine } from '@/lib/decision-engine'
import type { AnalysisResult, FixResult, RootCauseCandidate, StrategyEvaluation } from '@/lib/types'

const FAILURE_TYPES = Object.keys(demoWorkflowLogsByType)

interface Step {
  id: string
  title: string
  description: string
  done: boolean
}

const INVESTIGATION_STEPS: Step[] = [
  { id: 'collect', title: 'Collect Logs', description: 'Fetch CI/CD output from the failed run', done: false },
  { id: 'analyze', title: 'Analyze Stack Trace', description: 'Parse error patterns and classify the failure', done: false },
  { id: 'root_cause', title: 'Evaluate Root Causes', description: 'Score each hypothesis against evidence', done: false },
  { id: 'fix', title: 'Select Fix Strategy', description: 'Evaluate and choose best remediation', done: false },
]

export default function Analysis() {
  const { setState: setAgent, setMode, recordDecision, appendActivity } = useAgent()
  const [repo, setRepo] = useState('')
  const [logs, setLogs] = useState('')
  const [result, setResult] = useState<AnalysisResult | null>(null)
  const [fix, setFix] = useState<FixResult | null>(null)
  const [stepIdx, setStepIdx] = useState(-1)
  const [phase, setPhase] = useState<'idle' | 'investigating' | 'generating' | 'done'>('idle')
  const [rootCauseCandidates, setRootCauseCandidates] = useState<RootCauseCandidate[]>([])
  const [selectedRootCause, setSelectedRootCause] = useState<RootCauseCandidate | null>(null)
  const [evaluatedStrategies, setEvaluatedStrategies] = useState<StrategyEvaluation[]>([])
  const [selectedStrategy, setSelectedStrategy] = useState<StrategyEvaluation | null>(null)

  const engine = getDecisionEngine()
  const analysisMutation = useTriggerAnalysis()
  const fixMutation = useTriggerFix()
  const [autoAdvancing, setAutoAdvancing] = useState(false)
  const autoTimerRef = useRef<ReturnType<typeof setTimeout>>(undefined)
  const advanceRef = useRef<() => void>(() => {})
  const generateRef = useRef<() => void>(() => {})

  const handleLoadExample = useCallback((key: string) => {
    const entry = demoWorkflowLogsByType[key]
    if (!entry) return
    setRepo(entry.repo)
    setLogs(entry.logs)
    setResult(null)
    setFix(null)
    setStepIdx(-1)
    setPhase('idle')
    setRootCauseCandidates([])
    setSelectedRootCause(null)
    setEvaluatedStrategies([])
    setSelectedStrategy(null)
  }, [])

  const handleBeginInvestigation = useCallback(() => {
    setPhase('investigating')
    setStepIdx(0)
    setMode('investigating', 'Investigating', repo || 'failure')
    appendActivity({ type: 'failure_detected', message: `Investigation started for ${repo}`, status: 'pending' })
    setAutoAdvancing(true)
  }, [repo, setMode, appendActivity])

  const handleAdvance = useCallback(() => {
    const entry = Object.values(demoWorkflowLogsByType).find(e => e.repo === repo)
    if (!entry) return

    if (stepIdx < INVESTIGATION_STEPS.length - 1) {
      setStepIdx((i) => i + 1)
      const step = INVESTIGATION_STEPS[stepIdx + 1]

      if (step.id === 'root_cause' && !selectedRootCause) {
        // Evaluate root causes
        setMode('evaluating_hypotheses', 'Evaluating Hypotheses', entry.repo)
        const failureKey = Object.keys(demoWorkflowLogsByType).find(k => demoWorkflowLogsByType[k].repo === entry.repo)
        const candidates = failureKey ? demoRootCauseCandidates[failureKey] : undefined
        if (candidates) {
          const repoInfo = demoRepos.find(r => r.repository_name === entry.repo)
          const evaluated = engine.evaluateRootCauses(candidates, repoInfo?.success_rate ?? 70, 0.7)
          setRootCauseCandidates(evaluated)
          setSelectedRootCause(evaluated[0])
          setResult({
            root_cause: evaluated[0].root_cause,
            error_category: evaluated[0].error_category,
            confidence: evaluated[0].confidence,
            affected_files: evaluated[0].affected_files,
          })
          // Record decision
          const dec = engine.recordDecision(
            'hypothesis_evaluation',
            evaluated[0].root_cause.substring(0, 80),
            `Selected: ${evaluated[0].error_category} with ${(evaluated[0].confidence * 100).toFixed(0)}% confidence`,
            0,
            evaluated[0].confidence,
            evaluated[0].reasoning,
            evaluated[0].evidence.map(e => e.detail)
          )
          recordDecision(dec)
          // Record branch node
          const hypBranch = engine.addBranchNode(null, `${evaluated[0].error_category} (${(evaluated[0].confidence * 100).toFixed(0)}%)`, 'root_cause', undefined, dec)
          // Add alternative hypotheses as child branches
          evaluated.slice(1).forEach((alt) => {
            engine.addBranchNode(hypBranch.id, `${alt.error_category} (${(alt.confidence * 100).toFixed(0)}%)`, 'root_cause', 'Rejected — lower confidence score')
          })
          appendActivity({
            type: 'hypothesis_evaluated',
            message: `Root cause evaluated: ${evaluated[0].error_category} (${(evaluated[0].confidence * 100).toFixed(0)}% confidence)`,
            status: 'success',
          })
        }
      }

      setAgent({ label: `Investigating`, context: step.title, color: 'amber' })
    } else {
      // Move to fix generation - evaluate strategies
      const failureKey = Object.keys(demoWorkflowLogsByType).find(k => demoWorkflowLogsByType[k].repo === repo)
      if (failureKey && selectedRootCause) {
        setMode('comparing_strategies', 'Comparing Strategies', entry.repo)
        const strategyDefs = demoStrategyCandidates[failureKey]
        if (strategyDefs) {
          const repoInfo = demoRepos.find(r => r.repository_name === entry.repo)
          const strategies = engine.evaluateStrategies(selectedRootCause, strategyDefs, {
            risk_level: selectedRootCause.confidence > 0.8 ? 'low' : 'medium',
            repo_health: repoInfo?.success_rate ?? 70,
            affected_files_count: selectedRootCause.affected_files.length,
            historical_success_rate: repoInfo?.avg_confidence ?? 0.8,
          })
          setEvaluatedStrategies(strategies)
          setSelectedStrategy(strategies[0])
          setFix({
            fix_summary: strategies[0].fix_summary,
            assumptions: strategies[0].assumptions,
            patch: strategies[0].patch,
          })
          // Record decision
          const dec = engine.recordDecision(
            'strategy_selection',
            strategies[0].fix_summary.substring(0, 80),
            `Selected strategy with ${(strategies[0].strategy_score * 100).toFixed(0)}% score, ${(strategies[0].success_probability * 100).toFixed(0)}% expected success`,
            selectedRootCause.confidence,
            strategies[0].success_probability,
            strategies[0].reasoning,
            [strategies[0].reasoning]
          )
          recordDecision(dec)
          // Record strategy branch under the root cause
          engine.addBranchNode(null, `${strategies[0].fix_summary.substring(0, 50)}...`, 'strategy', undefined, dec)
          // Add rejected strategies as sibling branches
          strategies.slice(1).forEach((alt) => {
            const reason = alt.strategy_score < 0.4 ? 'Low overall score' :
              alt.risk_level === 'high' ? 'Risk too high' :
              alt.success_probability < 0.5 ? 'Insufficient success probability' :
              `Score ${(alt.strategy_score * 100).toFixed(0)}% vs selected ${(strategies[0].strategy_score * 100).toFixed(0)}%`
            engine.addBranchNode(null, `${alt.fix_summary.substring(0, 50)}...`, 'strategy', `Rejected — ${reason}`, {
              ...dec,
              id: `rejected-${alt.fix_summary.substring(0, 10)}`,
              outcome: `Rejected: ${reason}`,
              confidence_before: alt.success_probability,
              confidence_after: alt.success_probability,
            })
          })
          appendActivity({
            type: 'strategy_selected',
            message: `Strategy selected: ${strategies[0].fix_summary.substring(0, 60)}... (${(strategies[0].strategy_score * 100).toFixed(0)}% score)`,
            status: 'success',
          })
        }
      }
      setPhase('generating')
      setStepIdx(0)
      setAgent({ label: 'Generating Fix', context: entry.repo, color: 'blue' })
    }
  }, [stepIdx, repo, selectedRootCause, setAgent, setMode, recordDecision, appendActivity, engine])

  const handleGenerateFix = useCallback(() => {
    if (stepIdx < 3) {
      setStepIdx((i) => i + 1)
    }
    if (stepIdx >= 2) {
      setPhase('done')
      setAgent({ label: 'Fix Generated', context: repo || 'patch', color: 'emerald' })
      appendActivity({
        type: 'fix_generated',
        message: `Fix for ${repo}: ${selectedStrategy?.fix_summary.substring(0, 60)}...`,
        status: 'success',
      })
    }
  }, [stepIdx, repo, selectedStrategy, setAgent, appendActivity])

  // Keep refs in sync with latest callbacks
  advanceRef.current = handleAdvance
  generateRef.current = handleGenerateFix

  // Auto-advance through investigation and generating phases
  useEffect(() => {
    if (!autoAdvancing || phase === 'done' || phase === 'idle') return
    autoTimerRef.current = setTimeout(() => {
      if (phase === 'investigating') {
        advanceRef.current()
      } else if (phase === 'generating') {
        generateRef.current()
      }
    }, 1800)
    return () => { if (autoTimerRef.current) clearTimeout(autoTimerRef.current) }
  }, [autoAdvancing, phase, stepIdx])

  const handleSelectAlternativeCause = useCallback((candidate: RootCauseCandidate) => {
    setSelectedRootCause(candidate)
    setResult({
      root_cause: candidate.root_cause,
      error_category: candidate.error_category,
      confidence: candidate.confidence,
      affected_files: candidate.affected_files,
    })
    setMode('selecting_remediation_path', 'Selecting Remediation Path', candidate.error_category)
    appendActivity({
      type: 'hypothesis_evaluated',
      message: `Switched to hypothesis: ${candidate.error_category} (${(candidate.confidence * 100).toFixed(0)}% confidence)`,
      status: 'info',
    })
  }, [setMode, appendActivity])

  async function handleSubmit() {
    if (!repo.trim() || !logs.trim()) {
      toast.error('Please enter both repository name and logs')
      return
    }
    setResult(null)
    setFix(null)
    setMode('evaluating_hypotheses', 'Evaluating Hypotheses', repo.trim())
    try {
      const analysisResult = await analysisMutation.mutateAsync({ repository_name: repo.trim(), logs: logs.trim() })
      setResult(analysisResult as unknown as AnalysisResult)
      const fixResult = await fixMutation.mutateAsync({ repository_name: repo.trim(), logs: logs.trim() })
      setFix(fixResult as unknown as FixResult)
      setAgent({ label: 'Idle', color: 'zinc' })
    } catch {
      setAgent({ label: 'Monitoring', color: 'emerald' })
      toast.error('Analysis failed. Check server logs.')
    }
  }

  const isRunning = analysisMutation.isPending || fixMutation.isPending

  return (
    <PageTransition>
      <div className="mb-6">
        <h1 className="text-2xl font-semibold">Failure Analysis</h1>
        <p className="text-sm text-muted-foreground">Confidence-based root cause investigation and strategy evaluation</p>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <SpotlightCard className="p-6">
          <div className="mb-4 flex items-center justify-between gap-2">
            <h2 className="text-sm font-medium text-muted-foreground">Failure Logs</h2>
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
          <div className="space-y-4" role="form" aria-label="Analysis input form">
            <div>
              <label htmlFor="analysis-repo" className="mb-1.5 block text-xs font-medium text-muted-foreground">Repository name</label>
              <input id="analysis-repo" value={repo} onChange={(e) => setRepo(e.target.value)} placeholder="my-org/my-repo" className="w-full rounded-lg border border-input bg-background px-4 py-2.5 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring" />
            </div>
            <div>
              <label htmlFor="analysis-logs" className="mb-1.5 block text-xs font-medium text-muted-foreground">CI/CD Logs</label>
              <textarea id="analysis-logs" value={logs} onChange={(e) => setLogs(e.target.value)} placeholder="Paste CI/CD logs here..." rows={10} className="w-full rounded-lg border border-input bg-background px-4 py-2.5 text-sm font-mono placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring" />
            </div>
            <motion.button onClick={handleSubmit} disabled={isRunning} whileHover={{ scale: 1.01 }} whileTap={{ scale: 0.99 }} className="flex w-full items-center justify-center gap-2 rounded-lg bg-primary px-4 py-2.5 text-sm font-medium text-primary-foreground shadow-sm hover:opacity-90 disabled:opacity-50">
              {isRunning ? (
                <><span className="h-4 w-4 rounded-full border-2 border-current border-t-transparent animate-spin" />{analysisMutation.isPending ? 'Analyzing...' : 'Generating fix...'}</>
              ) : (
                <><Search className="h-4 w-4" /> Analyze & Generate Fix</>
              )}
            </motion.button>
          </div>
        </SpotlightCard>

        <AnimatePresence mode="wait">
          {phase === 'idle' && repo ? (
            <motion.div key="begin" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="flex items-center justify-center h-full min-h-[300px]">
              <motion.button
                onClick={handleBeginInvestigation}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                className="flex items-center gap-2 rounded-xl border border-blue-500/20 bg-blue-500/5 px-6 py-4 text-sm font-medium text-blue-400 hover:bg-blue-500/10 transition-colors"
              >
                <Play className="h-4 w-4" />
                Begin Investigation
              </motion.button>
            </motion.div>
          ) : phase === 'investigating' ? (
            <motion.div key="investigating" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="space-y-4">
              <SpotlightCard className="p-5">
                <div className="mb-4 flex items-center gap-2">
                  <span className="h-1.5 w-1.5 rounded-full bg-amber-500 animate-ping" />
                  <h2 className="text-sm font-medium">AI Investigation Session</h2>
                  <span className="text-[9px] text-zinc-600 ml-auto">
                    {stepIdx === 0 ? 'Collecting CI/CD logs...' :
                     stepIdx === 1 ? 'Analyzing stack trace patterns...' :
                     stepIdx === 2 ? `Evaluating hypotheses against evidence...` :
                     stepIdx === 3 ? `Comparing strategies...` : ''}
                    {autoAdvancing && stepIdx < 3 && <span className="text-zinc-700 ml-1">(auto-advancing)</span>}
                  </span>
                </div>
                <div className="space-y-0">
                  {INVESTIGATION_STEPS.map((step, i) => {
                    const isActive = i === stepIdx
                    const isDone = i < stepIdx
                    return (
                      <div key={step.id} className="flex gap-3">
                        <div className="flex flex-col items-center">
                          <div className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-full border ${
                            isDone ? 'border-emerald-500/30 bg-emerald-500/10' :
                            isActive ? 'border-amber-500/30 bg-amber-500/10' :
                            'border-zinc-700 bg-zinc-800/50'
                          }`}>
                            {isDone ? (
                              <CheckCircle className="h-3.5 w-3.5 text-emerald-500" />
                            ) : isActive ? (
                              <span className="h-3 w-3 rounded-full bg-amber-500 animate-pulse" />
                            ) : (
                              <span className="h-2 w-2 rounded-full bg-zinc-600" />
                            )}
                          </div>
                          {i < INVESTIGATION_STEPS.length - 1 && <div className="w-px flex-1 bg-zinc-800 my-0.5" />}
                        </div>
                        <div className={`pb-5 min-w-0 flex-1 ${!isActive && !isDone ? 'opacity-30' : ''}`}>
                          <p className={`text-xs font-medium ${isDone ? 'text-emerald-300' : isActive ? 'text-amber-300' : 'text-zinc-600'}`}>
                            {step.title}
                          </p>
                          {isActive && <p className="mt-0.5 text-[10px] text-zinc-600">{step.description}</p>}
                        </div>
                      </div>
                    )
                  })}
                </div>
                {selectedRootCause && stepIdx >= 2 && (
                  <div className="mt-3 space-y-2 border-t border-border pt-3">
                    <p className="text-[10px] font-medium text-muted-foreground">Top Root Cause Candidates</p>
                    {rootCauseCandidates.map((c, i) => (
                      <button
                        key={i}
                        onClick={() => handleSelectAlternativeCause(c)}
                        className={`w-full text-left rounded-lg p-2 text-xs transition-colors ${
                          c === selectedRootCause
                            ? 'bg-amber-500/10 border border-amber-500/20'
                            : 'bg-zinc-800/30 border border-transparent hover:bg-zinc-800/50'
                        }`}
                      >
                        <div className="flex items-center justify-between mb-1">
                          <span className="font-medium text-zinc-300">{c.error_category}</span>
                          <span className="text-amber-400 font-mono">{(c.confidence * 100).toFixed(0)}%</span>
                        </div>
                        <p className="text-[10px] text-zinc-500">{c.evidence.map(e => e.source).join(', ')}</p>
                      </button>
                    ))}
                  </div>
                )}
                {selectedRootCause && stepIdx >= 2 && (
                  <div className="mt-3 rounded-lg border border-amber-500/20 bg-amber-500/5 p-3">
                    <div className="flex items-center gap-2 mb-1">
                      <BarChart3 className="h-3.5 w-3.5 text-amber-400" />
                      <span className="text-[10px] font-medium text-amber-400">Evidence Summary</span>
                    </div>
                    <ul className="space-y-1">
                      {selectedRootCause.evidence.map((e, i) => (
                        <li key={i} className="flex items-start gap-1.5 text-[10px] text-zinc-400">
                          <span className={`mt-0.5 h-1.5 w-1.5 shrink-0 rounded-full ${
                            e.weight > 0.7 ? 'bg-emerald-500' : e.weight > 0.4 ? 'bg-amber-500' : 'bg-zinc-500'
                          }`} />
                          <span>{e.detail} <span className="text-zinc-600">({(e.weight * 100).toFixed(0)}% weight)</span></span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                <motion.button
                  onClick={handleAdvance}
                  whileHover={{ scale: 1.01 }}
                  whileTap={{ scale: 0.99 }}
                  className="mt-3 flex w-full items-center justify-center gap-1.5 rounded-lg border border-amber-500/20 bg-amber-500/5 px-4 py-2 text-xs font-medium text-amber-400 hover:bg-amber-500/10 transition-colors"
                >
                  {stepIdx < INVESTIGATION_STEPS.length - 1 ? (
                    <><ArrowRight className="h-3.5 w-3.5" /> Continue to "{INVESTIGATION_STEPS[stepIdx + 1].title}"</>
                  ) : (
                    <><ArrowRight className="h-3.5 w-3.5" /> Evaluate Strategies & Generate Fix</>
                  )}
                </motion.button>
              </SpotlightCard>
            </motion.div>
          ) : phase === 'generating' ? (
            <motion.div key="generating" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="space-y-4">
              <SpotlightCard className="p-5">
                <div className="mb-4 flex items-center gap-2">
                  <Cpu className="h-4 w-4 text-blue-500" />
                  <span className="h-1.5 w-1.5 rounded-full bg-blue-500 animate-ping" />
                  <h2 className="text-sm font-medium">AI Working Session — Strategy Evaluation</h2>
                  {selectedRootCause && (
                    <span className="text-[9px] text-zinc-600 ml-auto">Confidence: {(selectedRootCause.confidence * 100).toFixed(0)}%</span>
                  )}
                </div>
                {evaluatedStrategies.length > 0 && (
                  <div className="mb-3 space-y-2">
                    <p className="text-[10px] font-medium text-muted-foreground">Evaluated Strategies</p>
                    {evaluatedStrategies.map((s, i) => (
                      <div
                        key={i}
                        className={`rounded-lg p-2.5 border ${
                          i === 0
                            ? 'border-blue-500/20 bg-blue-500/5'
                            : 'border-zinc-800 bg-zinc-800/30'
                        }`}
                      >
                        <div className="flex items-center justify-between mb-1">
                          <span className={`text-[10px] font-medium ${i === 0 ? 'text-blue-300' : 'text-zinc-400'}`}>
                            {i === 0 ? '★ Selected' : `#${i + 1}`}
                          </span>
                          <div className="flex items-center gap-2">
                            <span className="text-[10px] text-emerald-400">{(s.success_probability * 100).toFixed(0)}% success</span>
                            <span className={`text-[10px] ${
                              s.risk_level === 'low' ? 'text-emerald-500' :
                              s.risk_level === 'medium' ? 'text-amber-500' : 'text-red-500'
                            }`}>
                              {s.risk_level} risk
                            </span>
                          </div>
                        </div>
                        <p className="text-[10px] text-zinc-500">{s.fix_summary.substring(0, 80)}...</p>
                        <div className="flex items-center gap-3 mt-1">
                          <span className="text-[10px] text-zinc-600">Score: {(s.strategy_score * 100).toFixed(0)}%</span>
                          <span className="text-[10px] text-zinc-600">{s.estimated_execution_time}</span>
                          {i > 0 && (
                            <span className="text-[10px] text-zinc-700">Rank #{i + 1} of {evaluatedStrategies.length}</span>
                          )}
                        </div>
                        {i > 0 && evaluatedStrategies[0] && (
                          <div className="mt-1">
                            <span className="text-[9px] text-zinc-700">
                              Not selected — score {(s.strategy_score * 100).toFixed(0)}% vs {(evaluatedStrategies[0].strategy_score * 100).toFixed(0)}% for top option
                              {s.risk_level === 'high' ? ' (high risk)' : s.strategy_score < 0.4 ? ' (low score)' : ''}
                            </span>
                          </div>
                        )}
                      </div>
                    ))}
                    <div className="rounded-lg border border-zinc-800 bg-zinc-800/30 p-2.5 mt-2">
                      <div className="flex items-center gap-1.5 mb-1">
                        <Lightbulb className="h-3 w-3 text-blue-400" />
                        <span className="text-[10px] font-medium text-blue-400">Why this strategy?</span>
                      </div>
                      <p className="text-[10px] text-zinc-500">{evaluatedStrategies[0]?.reasoning}</p>
                    </div>
                  </div>
                )}
                <div className="space-y-0">
                  {['Analyzing Code', 'Planning Fix', 'Generating Patch', 'Validating', 'Ready for PR'].map((title, i) => {
                    const isActive = i === stepIdx
                    const isDone = i < stepIdx
                    return (
                      <div key={title} className="flex gap-3">
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
                          {i < 4 && <div className="w-px flex-1 bg-zinc-800 my-0.5" />}
                        </div>
                        <div className={`pb-5 min-w-0 flex-1 ${!isActive && !isDone ? 'opacity-30' : ''}`}>
                          <p className={`text-xs font-medium ${isDone ? 'text-emerald-300' : isActive ? 'text-blue-300' : 'text-zinc-600'}`}>{title}</p>
                        </div>
                      </div>
                    )
                  })}
                </div>
                <motion.button
                  onClick={handleGenerateFix}
                  whileHover={{ scale: 1.01 }}
                  whileTap={{ scale: 0.99 }}
                  className="mt-3 flex w-full items-center justify-center gap-1.5 rounded-lg border border-blue-500/20 bg-blue-500/5 px-4 py-2 text-xs font-medium text-blue-400 hover:bg-blue-500/10 transition-colors"
                >
                  <ArrowRight className="h-3.5 w-3.5" />
                  {stepIdx < 3 ? 'Advance Step' : 'Complete & View Results'}
                </motion.button>
              </SpotlightCard>
            </motion.div>
          ) : phase === 'done' && result ? (
              <motion.div key="results" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: 20 }} transition={{ duration: 0.3 }} className="space-y-4">
              <div className="space-y-1 mb-3">
                <div className="flex items-center gap-2">
                  <CheckCircle className="h-4 w-4 text-emerald-500" />
                  <span className="text-xs font-medium text-emerald-400">AI session complete</span>
                </div>
                <div className="flex items-center gap-3 text-[10px] text-zinc-600 ml-6">
                  <span>Root cause: {result.error_category} ({(result.confidence * 100).toFixed(0)}%)</span>
                  <span>·</span>
                  <span>Strategy: {selectedStrategy ? (selectedStrategy.strategy_score * 100).toFixed(0) : '—'}% score</span>
                  <span>·</span>
                  <span className="text-blue-400">Next: Validate fix</span>
                </div>
              </div>

              <TiltCard>
                <SpotlightCard className="p-5">
                  <div className="mb-3 flex items-center gap-2">
                    <AlertTriangle className="h-4 w-4 text-yellow-500" />
                    <h2 className="text-sm font-medium">Root Cause</h2>
                    <StatusBadge status={result.error_category ?? 'unknown'} />
                  </div>
                  <p className="text-sm text-muted-foreground">{result.root_cause}</p>
                  <div className="mt-3 flex items-center gap-4">
                    <span className="text-xs text-muted-foreground">Confidence: {(result.confidence * 100).toFixed(0)}%</span>
                  </div>
                  {selectedRootCause && (
                    <div className="mt-3 border-t border-border pt-3">
                      <p className="text-[10px] font-medium text-muted-foreground mb-2">Evidence</p>
                      <ul className="space-y-1">
                        {selectedRootCause.evidence.map((e, i) => (
                          <li key={i} className="flex items-start gap-1.5 text-[10px] text-zinc-500">
                            <span className={`mt-0.5 h-1.5 w-1.5 shrink-0 rounded-full ${
                              e.weight > 0.7 ? 'bg-emerald-500' : e.weight > 0.4 ? 'bg-amber-500' : 'bg-zinc-500'
                            }`} />
                            <span>{e.detail}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </SpotlightCard>
              </TiltCard>

              <TiltCard>
                <SpotlightCard className="p-5">
                  <div className="mb-3 flex items-center gap-2">
                    <FileCode className="h-4 w-4 text-blue-500" />
                    <h2 className="text-sm font-medium">Affected Files</h2>
                  </div>
                  {result.affected_files?.length > 0 ? (
                    <ul className="space-y-1">
                      {result.affected_files.map((f, i) => (
                        <motion.li key={f} initial={{ opacity: 0, x: -8 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.05 }} className="text-sm font-mono text-muted-foreground">{f}</motion.li>
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
                    <p className="text-sm text-muted-foreground">{fix.fix_summary}</p>
                    {selectedStrategy && (
                      <div className="mt-2 flex items-center gap-3 text-[10px] text-muted-foreground">
                        <span className="text-emerald-400">{(selectedStrategy.success_probability * 100).toFixed(0)}% success prob.</span>
                        <span className={selectedStrategy.risk_level === 'low' ? 'text-emerald-500' : selectedStrategy.risk_level === 'medium' ? 'text-amber-500' : 'text-red-500'}>
                          {selectedStrategy.risk_level} risk
                        </span>
                        <span>{selectedStrategy.estimated_execution_time}</span>
                      </div>
                    )}
                    {fix.assumptions?.length > 0 && (
                      <div className="mt-3">
                        <p className="mb-1 text-xs font-medium text-muted-foreground">Assumptions:</p>
                        <ul className="space-y-0.5">{fix.assumptions.map((a, i) => (<li key={i} className="text-xs text-muted-foreground">• {a}</li>))}</ul>
                      </div>
                    )}
                    {selectedStrategy && (
                      <div className="mt-3 rounded-lg border border-zinc-800 bg-zinc-800/30 p-2.5">
                        <div className="flex items-center gap-1.5 mb-1">
                          <Lightbulb className="h-3 w-3 text-blue-400" />
                          <span className="text-[10px] font-medium text-blue-400">Strategy Selection</span>
                        </div>
                        <p className="text-[10px] text-zinc-500">{selectedStrategy.reasoning}</p>
                      </div>
                    )}
                    {evaluatedStrategies.length > 1 && (
                      <div className="mt-3 rounded-lg border border-zinc-800 bg-zinc-900/30 p-2.5">
                        <div className="flex items-center gap-1.5 mb-1.5">
                          <GitBranch className="h-3 w-3 text-zinc-500" />
                          <span className="text-[10px] font-medium text-zinc-500">Rejected Alternatives</span>
                        </div>
                        {evaluatedStrategies.slice(1).map((alt, i) => (
                          <div key={i} className="flex items-start gap-1.5 text-[10px] text-zinc-600 py-0.5">
                            <XCircle className="h-3 w-3 text-zinc-700 shrink-0 mt-0.5" />
                            <span className="flex-1">{alt.fix_summary.substring(0, 60)}...</span>
                            <span className="text-zinc-700 shrink-0">score {(alt.strategy_score * 100).toFixed(0)}%</span>
                          </div>
                        ))}
                      </div>
                    )}
                    <div className="mt-4 flex gap-2">
                      <Link
                        to={`/validation?repo=${encodeURIComponent(repo)}`}
                        className="inline-flex items-center gap-1.5 rounded-md border border-blue-500/20 bg-blue-500/5 px-3 py-1.5 text-[10px] font-medium text-blue-400 hover:bg-blue-500/10 transition-colors"
                      >
                        Validate this fix <ArrowRight className="h-3 w-3" />
                      </Link>
                      {rootCauseCandidates.length > 1 && (
                        <div className="inline-flex items-center gap-1 rounded-md border border-zinc-700 bg-zinc-800/50 px-2 py-1.5 text-[10px] text-zinc-500">
                          <GitBranch className="h-3 w-3" />
                          {rootCauseCandidates.length - 1} alternative hypotheses
                        </div>
                      )}
                    </div>
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
                    <pre className="overflow-x-auto rounded-lg bg-background p-4 text-xs text-muted-foreground"><code>{fix.patch}</code></pre>
                  </SpotlightCard>
                </TiltCard>
              )}
            </motion.div>
          ) : (
            <motion.div key="empty" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="flex h-full min-h-[300px] items-center justify-center rounded-xl border border-border bg-card">
              <div className="text-center">
                <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-xl bg-muted"><Search className="h-5 w-5 text-muted-foreground" /></div>
                <p className="text-sm text-muted-foreground">Load example data or submit logs to begin</p>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </PageTransition>
  )
}
