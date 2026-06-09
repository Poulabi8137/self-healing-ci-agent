import { useState, useEffect } from 'react'
import type { ReactNode } from 'react'
import { CheckCircle, Circle, Loader } from 'lucide-react'

export interface TimelineStep {
  id: string
  icon?: ReactNode
  title: string
  description?: string
  status: 'pending' | 'active' | 'completed' | 'failed'
}

interface StepTimelineProps {
  steps: TimelineStep[]
  autoProgress?: boolean
  intervalMs?: number
}

export function StepTimeline({ steps, autoProgress = true, intervalMs = 600 }: StepTimelineProps) {
  const [visible, setVisible] = useState(autoProgress ? 0 : steps.length)

  useEffect(() => {
    if (!autoProgress) return
    if (visible >= steps.length) return
    const t = setTimeout(() => setVisible((v) => v + 1), intervalMs)
    return () => clearTimeout(t)
  }, [visible, autoProgress, steps.length, intervalMs])

  return (
    <div className="space-y-0">
      {steps.map((step, i) => {
        const isVisible = i < visible
        const isLast = i === steps.length - 1

        return (
          <div key={step.id} className="flex gap-3">
            <div className="flex flex-col items-center">
              <div className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-full border ${
                step.status === 'completed' ? 'border-emerald-500/30 bg-emerald-500/10' :
                step.status === 'failed' ? 'border-red-500/30 bg-red-500/10' :
                step.status === 'active' || !isVisible ? 'border-blue-500/30 bg-blue-500/10' :
                'border-zinc-700 bg-zinc-800/50'
              }`}>
                {step.status === 'completed' ? (
                  <CheckCircle className="h-3.5 w-3.5 text-emerald-500" />
                ) : step.status === 'failed' ? (
                  <span className="h-3.5 w-3.5 text-red-500 text-[10px] font-bold">!</span>
                ) : step.status === 'active' || !isVisible ? (
                  <Loader className="h-3 w-3 text-blue-500" />
                ) : (
                  <Circle className="h-3 w-3 text-zinc-600" />
                )}
              </div>
              {!isLast && <div className="w-px flex-1 bg-zinc-800 my-0.5" />}
            </div>
            <div className={`pb-4 min-w-0 flex-1 ${!isVisible ? 'opacity-40' : ''}`}>
              <p className={`text-xs font-medium ${
                step.status === 'completed' ? 'text-emerald-300' :
                step.status === 'failed' ? 'text-red-300' :
                'text-zinc-300'
              }`}>{step.title}</p>
              {step.description && (
                <p className="mt-0.5 text-[10px] text-zinc-600">{step.description}</p>
              )}
            </div>
          </div>
        )
      })}
    </div>
  )
}
