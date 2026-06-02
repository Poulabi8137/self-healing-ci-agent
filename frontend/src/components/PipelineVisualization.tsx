import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { GitCommitHorizontal, Package, CircleCheckBig, Search, Wand, GitPullRequest, ArrowRight, Sparkles, type LucideIcon } from 'lucide-react'
import { pipelineNodeVariant } from '@/lib/motion'

interface Stage {
  key: string
  icon: LucideIcon
  label: string
  agent: boolean
}

const stages: Stage[] = [
  { key: 'push', icon: GitCommitHorizontal, label: 'Push', agent: false },
  { key: 'build', icon: Package, label: 'Build', agent: false },
  { key: 'test', icon: CircleCheckBig, label: 'Test', agent: false },
  { key: 'analyze', icon: Search, label: 'Analyze', agent: true },
  { key: 'fix', icon: Wand, label: 'Fix', agent: true },
  { key: 'pr', icon: GitPullRequest, label: 'PR', agent: true },
]

export type PipelineState = 'idle' | 'running' | 'success' | 'failed'

interface PipelineVisualizationProps {
  onComplete?: () => void
  autoRun?: boolean
  compact?: boolean
}

export function PipelineVisualization({ onComplete, autoRun = false, compact = false }: PipelineVisualizationProps) {
  const [activeIndex, setActiveIndex] = useState(-1)
  const [states, setStates] = useState<PipelineState[]>(stages.map(() => 'idle'))

  const runPipeline = () => {
    setActiveIndex(0)
    setStates(stages.map(() => 'idle'))
  }

  useEffect(() => {
    if (!autoRun) return
    const t = setTimeout(() => runPipeline(), 500)
    return () => clearTimeout(t)
  }, [autoRun])

  useEffect(() => {
    if (activeIndex < 0 || activeIndex >= stages.length) return
    const timer = setTimeout(() => {
      setStates(prev => {
        const next = [...prev]
        const isFailed = !stages[activeIndex].agent && Math.random() < 0.15
        next[activeIndex] = isFailed ? 'failed' : 'success'
        return next
      })
      if (activeIndex === stages.length - 1) {
        onComplete?.()
      } else {
        const nextTimer = setTimeout(() => {
          setActiveIndex(prev => prev + 1)
        }, stages[activeIndex].agent ? 800 : 500)
        return () => clearTimeout(nextTimer)
      }
    }, stages[activeIndex].agent ? 1200 : 600)
    return () => clearTimeout(timer)
  }, [activeIndex, onComplete])

  if (activeIndex >= stages.length && autoRun) {
    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className={`flex flex-col items-center justify-center gap-3 ${compact ? 'py-4' : 'py-8'}`}
      >
        <div className="flex h-12 w-12 items-center justify-center rounded-full bg-emerald-500/10">
          <Sparkles className="h-6 w-6 text-emerald-400" />
        </div>
        <p className="text-sm font-medium text-emerald-400">Pipeline complete</p>
        <button onClick={runPipeline} className="text-xs text-zinc-500 hover:text-zinc-300 underline underline-offset-2">
          Run again
        </button>
      </motion.div>
    )
  }

  return (
    <div className={`flex items-center ${compact ? 'gap-0' : 'gap-0'}`}>
      {stages.map((stage, i) => (
        <div key={stage.key} className="flex items-center">
          <motion.div
            variants={pipelineNodeVariant(i)}
            initial="hidden"
            animate="visible"
            className={`flex flex-col items-center ${compact ? 'gap-1.5' : 'gap-2'}`}
          >
            <div className={`relative flex items-center justify-center rounded-lg border transition-all duration-500 ${
              compact ? 'h-7 w-7' : 'h-9 w-9'
            } ${
              states[i] === 'success' ? 'border-emerald-500/40 bg-emerald-500/15 text-emerald-400' :
              states[i] === 'failed' ? 'border-red-500/40 bg-red-500/15 text-red-400' :
              activeIndex === i ? 'border-blue-500/40 bg-blue-500/15 text-blue-400' :
              activeIndex > i ? 'border-zinc-700/40 bg-zinc-800/40 text-zinc-500' :
              stage.agent ? 'border-zinc-700/30 bg-zinc-800/20 text-zinc-600' : 'border-zinc-700/20 bg-zinc-800/10 text-zinc-600'
            }`}>
              <stage.icon className={compact ? 'h-3 w-3' : 'h-4 w-4'} />
              {activeIndex === i && (
                <span className="absolute -top-1 -right-1 flex h-2.5 w-2.5">
                  <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-blue-400/60" />
                  <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-blue-500" />
                </span>
              )}
            </div>
            <span className={`text-[10px] font-medium tracking-wider uppercase ${
              states[i] === 'success' ? 'text-emerald-400/80' :
              states[i] === 'failed' ? 'text-red-400/80' :
              activeIndex === i ? 'text-blue-400/80' :
              'text-zinc-600'
            }`}>
              {stage.label}
            </span>
          </motion.div>
          {i < stages.length - 1 && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.3, delay: 0.3 + i * 0.1 }}
              className={`flex items-center ${compact ? 'mx-1' : 'mx-1.5'}`}
            >
              <div className={`h-px ${compact ? 'w-4' : 'w-5'} ${
                states[i] === 'success' ? 'bg-emerald-500/30' :
                activeIndex > i ? 'bg-zinc-700/50' :
                activeIndex === i ? 'bg-blue-500/30' :
                'bg-zinc-800'
              }`} />
              <ArrowRight className={`${compact ? 'h-2.5 w-2.5' : 'h-3 w-3'} -ml-1 ${
                states[i] === 'success' ? 'text-emerald-500/40' :
                activeIndex > i ? 'text-zinc-600' :
                'text-zinc-700'
              }`} />
            </motion.div>
          )}
        </div>
      ))}
    </div>
  )
}
