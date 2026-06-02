import { useState, useEffect, useCallback, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { GitCommitHorizontal, Package, CircleCheckBig, Search, Wand, GitPullRequest, Check, X, Play, RotateCw, type LucideIcon } from 'lucide-react'
import { cinematic } from '@/lib/motion'

interface Step {
  id: string
  icon: LucideIcon
  title: string
  detail: string
  status: 'waiting' | 'active' | 'success' | 'failed'
  duration: number
}

const replaySteps: Step[] = [
  { id: 'trigger', icon: GitCommitHorizontal, title: 'Workflow triggered', detail: 'New push detected on main branch', status: 'waiting', duration: 600 },
  { id: 'build', icon: Package, title: 'Build running', detail: 'npm run build — 142 packages', status: 'waiting', duration: 800 },
  { id: 'test-start', icon: CircleCheckBig, title: 'Tests executing', detail: 'Running 142 test suites', status: 'waiting', duration: 700 },
  { id: 'test-fail', icon: CircleCheckBig, title: 'Tests failed', detail: '3 test suites failed — assertion errors in auth.spec.ts', status: 'waiting', duration: 500 },
  { id: 'detect', icon: RotateCw, title: 'Failure detected', detail: 'Agent monitoring flagged test failure', status: 'waiting', duration: 400 },
  { id: 'logs', icon: Search, title: 'Logs analyzed', detail: 'Scanning stack traces, error output, and git blame', status: 'waiting', duration: 600 },
  { id: 'root-cause', icon: Search, title: 'Root cause extracted', detail: 'Session token expires before async test completes', status: 'waiting', duration: 500 },
  { id: 'analyze', icon: Wand, title: 'AI analysis complete', detail: 'Fix strategy: extend token refresh interval', status: 'waiting', duration: 600 },
  { id: 'fix', icon: Wand, title: 'Fix generated', detail: 'Patch ready — 3 files changed', status: 'waiting', duration: 800 },
  { id: 'rerun', icon: RotateCw, title: 'Pipeline rerun', detail: 'Validated fix passes all 142 tests', status: 'waiting', duration: 700 },
  { id: 'pr', icon: GitPullRequest, title: 'Pull request created', detail: 'PR submitted for review', status: 'waiting', duration: 600 },
  { id: 'success', icon: Check, title: 'All checks passing', detail: 'CI pipeline green — 142/142 tests passed', status: 'waiting', duration: 400 },
]

const sampleDiff = `diff --git a/src/auth/session.ts b/src/auth/session.ts
index a1b2c3d..e4f5g6h 100644
--- a/src/auth/session.ts
+++ b/src/auth/session.ts
@@ -45,7 +45,7 @@ export class SessionManager {
   async refreshToken(): Promise<Token> {
-    const ttl = 300_000; // 5 min
+    const ttl = 600_000; // 10 min
     const token = await this.store.get(this.sessionId);
     if (!token || Date.now() - token.created > ttl) {`

interface SelfHealingDemoProps {
  onComplete?: () => void
  autoPlay?: boolean
  className?: string
}

export function SelfHealingDemo({ onComplete, autoPlay = false, className = '' }: SelfHealingDemoProps) {
  const [currentStep, setCurrentStep] = useState(-1)
  const [steps, setSteps] = useState<Step[]>(replaySteps)
  const [completed, setCompleted] = useState(false)
  const [showDiff, setShowDiff] = useState(false)
  const [elapsed, setElapsed] = useState(0)
  const timersRef = useRef<ReturnType<typeof setTimeout>[]>([])
  const startTimeRef = useRef<number>(0)
  const elapsedIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const clearTimers = useCallback(() => {
    timersRef.current.forEach(clearTimeout)
    timersRef.current = []
    if (elapsedIntervalRef.current) {
      clearInterval(elapsedIntervalRef.current)
      elapsedIntervalRef.current = null
    }
  }, [])

  const startReplay = useCallback(() => {
    clearTimers()
    setCompleted(false)
    setShowDiff(false)
    setElapsed(0)
    setSteps(replaySteps.map(s => ({ ...s, status: 'waiting' as const })))
    setCurrentStep(-1)
    startTimeRef.current = Date.now()

    elapsedIntervalRef.current = setInterval(() => {
      setElapsed(Date.now() - startTimeRef.current)
    }, 100)

    const t = setTimeout(() => setCurrentStep(0), 400)
    timersRef.current.push(t)
  }, [clearTimers])

  useEffect(() => {
    if (!autoPlay) return
    startReplay()
    return clearTimers
  }, [autoPlay, startReplay, clearTimers])

  useEffect(() => {
    if (currentStep < 0 || currentStep >= steps.length) return

    setSteps(prev => prev.map((s, i) =>
      i === currentStep ? { ...s, status: 'active' as const } : s
    ))

    const step = steps[currentStep]
    const isFixStep = step.id === 'fix'

    const t = setTimeout(() => {
      const isFailed = step.id === 'test-fail'
      setSteps(prev => prev.map((s, i) =>
        i === currentStep ? { ...s, status: isFailed ? 'failed' as const : 'success' as const } : s
      ))

      if (isFailed) {
        const t2 = setTimeout(() => {
          setSteps(prev => prev.map((s, i) =>
            i === currentStep ? { ...s, status: 'success' as const } : s
          ))
          setCurrentStep(prev => prev + 1)
        }, 600)
        timersRef.current.push(t2)
      } else if (isFixStep) {
        setShowDiff(true)
        const t2 = setTimeout(() => {
          setCurrentStep(prev => prev + 1)
        }, step.duration)
        timersRef.current.push(t2)
      } else if (currentStep < steps.length - 1) {
        setCurrentStep(prev => prev + 1)
      } else {
        setCompleted(true)
        if (elapsedIntervalRef.current) {
          clearInterval(elapsedIntervalRef.current)
          elapsedIntervalRef.current = null
        }
        onComplete?.()
      }
    }, step.duration)
    timersRef.current.push(t)
  }, [currentStep, steps.length, onComplete])

  useEffect(() => {
    return () => clearTimers()
  }, [clearTimers])

  const formatElapsed = (ms: number) => {
    const secs = (ms / 1000).toFixed(1)
    return `${secs}s`
  }

  return (
    <div className={className}>
      <div className="flex flex-col gap-1.5">
        {steps.map((step, i) => {
          const isPast = i < currentStep && step.status === 'success'
          const isActive = i === currentStep
          const Icon = step.icon

          return (
            <motion.div
              key={step.id}
              initial={{ opacity: 0, x: -8 }}
              animate={{
                opacity: isActive || isPast || (i === currentStep && completed) ? 1 : 0.35,
                x: 0,
              }}
              transition={{ duration: 0.3, delay: i * 0.04, ease: cinematic }}
              className={`flex items-center gap-3 rounded-lg px-3 py-2 transition-all duration-500 ${
                isActive ? 'bg-blue-500/8 border border-blue-500/15' :
                isPast || (i === currentStep && completed) ? 'bg-zinc-800/20 border border-transparent' :
                'border border-transparent'
              }`}
            >
              <div className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-md transition-all duration-500 ${
                isActive ? 'bg-blue-500/20 text-blue-400' :
                isPast || (i === currentStep && completed) ? 'bg-emerald-500/15 text-emerald-400' :
                step.id === 'test-fail' && i <= currentStep ? 'bg-red-500/15 text-red-400' :
                'bg-zinc-800/40 text-zinc-600'
              }`}>
                {isActive ? (
                  <div className="h-3.5 w-3.5 rounded-full border-2 border-current border-t-transparent animate-spin" />
                ) : isPast || (i === currentStep && completed) ? (
                  <Check className="h-3.5 w-3.5" />
                ) : (
                  <Icon className="h-3.5 w-3.5" />
                )}
              </div>
              <div className="flex-1 min-w-0">
                <p className={`text-sm font-medium transition-colors duration-500 ${
                  isActive ? 'text-blue-300' :
                  isPast || (i === currentStep && completed) ? 'text-zinc-200' :
                  'text-zinc-600'
                }`}>
                  {step.title}
                </p>
                <p className={`text-xs mt-0.5 transition-colors duration-500 ${
                  isActive ? 'text-blue-400/60' :
                  isPast || (i === currentStep && completed) ? 'text-zinc-500' :
                  'text-zinc-700'
                }`}>
                  {step.detail}
                </p>
              </div>
              {isPast || (i === currentStep && completed) ? (
                <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ type: 'spring', stiffness: 400, damping: 20 }}>
                  <Check className="h-4 w-4 text-emerald-500" />
                </motion.div>
              ) : isActive && step.id === 'test-fail' ? (
                <X className="h-4 w-4 text-red-400" />
              ) : null}
            </motion.div>
          )
        })}
      </div>

      <AnimatePresence>
        {showDiff && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="mt-3 overflow-hidden"
          >
            <div className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-3">
              <div className="mb-2 flex items-center gap-2">
                <Wand className="h-3 w-3 text-blue-400" />
                <span className="text-[10px] font-medium text-zinc-500 uppercase tracking-wider">Generated Patch</span>
              </div>
              <pre className="overflow-x-auto text-[11px] leading-relaxed text-zinc-400 font-mono">
                <code>{sampleDiff}</code>
              </pre>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {completed && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            className="mt-4 flex items-center gap-3 rounded-lg bg-emerald-500/8 border border-emerald-500/15 px-3 py-2.5"
          >
            <div className="rounded-full bg-emerald-500/15 p-1">
              <Check className="h-3.5 w-3.5 text-emerald-400" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-emerald-300">Pipeline recovered</p>
              <p className="text-[11px] text-emerald-400/60">Elapsed: {formatElapsed(elapsed)}</p>
            </div>
            <button onClick={startReplay} className="flex items-center gap-1.5 text-xs text-zinc-500 hover:text-zinc-300 transition-colors">
              <Play className="h-3 w-3" />
              Replay
            </button>
          </motion.div>
        )}
      </AnimatePresence>

      {currentStep === -1 && !autoPlay && (
        <button
          onClick={startReplay}
          className="flex items-center gap-2 rounded-lg border border-zinc-800 bg-zinc-900/50 px-4 py-2.5 text-sm text-zinc-300 hover:bg-zinc-800/40 hover:text-zinc-100 transition-colors w-full justify-center"
        >
          <Play className="h-4 w-4" />
          Replay Failure
        </button>
      )}
    </div>
  )
}
