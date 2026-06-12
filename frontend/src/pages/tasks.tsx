import { useState } from 'react'
import { motion } from 'framer-motion'
import { ListTodo, Clock, CheckCircle, AlertCircle, Timer, ArrowRight } from 'lucide-react'
import { PageTransition } from '@/components/page-transition'
import { StaggerGrid, StaggerItem } from '@/components/stagger-grid'
import { SpotlightCard } from '@/components/spotlight-card'
import { TiltCard } from '@/components/tilt-card'
import { StatusBadge } from '@/components/status-badge'
import { EmptyState } from '@/components/empty-state'
import { MetricCard } from '@/components/metric-card'
import { useTaskList } from '@/lib/api'

import type { TaskStatusResponse } from '@/lib/types'

function TaskCard({ task, index }: { task: TaskStatusResponse; index: number }) {
  const [expanded, setExpanded] = useState(false)
  const isRunning = task.status === 'running'
  const isPending = task.status === 'pending'

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.03 }}
    >
      <TiltCard>
        <SpotlightCard className="p-4">
          <button
            onClick={() => setExpanded(!expanded)}
            className="flex w-full items-center justify-between"
          >
            <div className="flex items-center gap-3 min-w-0">
              <div className={`flex h-8 w-8 items-center justify-center rounded-lg ${
                task.status === 'completed' ? 'bg-emerald-500/10' :
                task.status === 'failed' ? 'bg-red-500/10' :
                'bg-blue-500/10'
              }`}>
                {task.status === 'completed' ? <CheckCircle className="h-4 w-4 text-emerald-500" /> :
                 task.status === 'failed' ? <AlertCircle className="h-4 w-4 text-red-500" /> :
                 <Clock className={`h-4 w-4 text-blue-500 ${isRunning ? 'animate-pulse' : ''}`} />}
              </div>
              <div className="text-left min-w-0">
                <p className="text-sm font-medium truncate">{task.type}</p>
                <p className="text-[11px] text-muted-foreground">
                  {new Date(task.created_at).toLocaleString()}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              <StatusBadge status={task.status} />
              <ArrowRight className={`h-3 w-3 text-muted-foreground transition-transform ${expanded ? 'rotate-90' : ''}`} />
            </div>
          </button>

          {(isRunning || isPending) && (
            <div className="mt-3">
              <div className="flex h-1.5 w-full overflow-hidden rounded-full bg-muted">
                <motion.div
                  className={`h-full rounded-full ${isRunning ? 'bg-blue-500' : 'bg-yellow-500'}`}
                  initial={{ width: '0%' }}
                  animate={isRunning ? { width: '60%' } : { width: '10%' }}
                  transition={isRunning ? { duration: 2, repeat: Infinity, repeatType: 'reverse' } : {}}
                />
              </div>
              <p className="mt-1 text-[10px] text-muted-foreground">
                {isRunning ? 'Processing...' : 'Queued...'}
              </p>
            </div>
          )}

          {expanded && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="mt-3 border-t border-border pt-3"
            >
              <div className="grid grid-cols-2 gap-3 text-xs">
                <div>
                  <span className="text-muted-foreground">Task ID</span>
                  <p className="font-mono font-medium">#{task.id}</p>
                </div>
                <div>
                  <span className="text-muted-foreground">Updated</span>
                  <p className="font-medium">{new Date(task.updated_at).toLocaleString()}</p>
                </div>
                {task.result && Object.keys(task.result).length > 0 && (
                  <div className="col-span-2">
                    <span className="text-muted-foreground">Result</span>
                    <pre className="mt-1 overflow-x-auto rounded bg-muted p-2 text-[10px] font-mono">
                      {JSON.stringify(task.result, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            </motion.div>
          )}
        </SpotlightCard>
      </TiltCard>
    </motion.div>
  )
}

export default function Tasks() {
  const { data: _tasks, error } = useTaskList()
  const taskList = _tasks ?? []

  const completed = taskList.filter((t) => t.status === 'completed').length
  const running = taskList.filter((t) => t.status === 'running').length

  return (
    <PageTransition>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold">Tasks</h1>
            <p className="text-sm text-muted-foreground">Background task queue</p>
          </div>
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <Timer className="h-3.5 w-3.5 text-blue-500" />
            <span>Polling every 10s</span>
          </div>
        </div>

        {error && (
          <div className="rounded-xl border border-red-500/20 bg-red-500/10 p-4" role="alert">
            <p className="text-sm text-red-500">Failed to load tasks. Running in demo mode.</p>
          </div>
        )}

        <StaggerGrid className="grid gap-4 sm:grid-cols-3">
          <StaggerItem><MetricCard label="Total" value={taskList.length} /></StaggerItem>
          <StaggerItem><MetricCard label="Running" value={running} trend={{ value: running > 0 ? 100 : 0, positive: running > 0 }} /></StaggerItem>
          <StaggerItem><MetricCard label="Completed" value={completed} suffix="%" decimals={0} /></StaggerItem>
        </StaggerGrid>

        {taskList.length > 0 ? (
          <div className="space-y-3">
            {taskList.map((task, i) => (
              <TaskCard key={task.id} task={task} index={i} />
            ))}
          </div>
        ) : (
          <div className="rounded-xl border border-border bg-card">
            <EmptyState
              icon={ListTodo}
              title="No tasks yet"
              description="Tasks will appear here when background jobs are running."
            />
          </div>
        )}
      </div>
    </PageTransition>
  )
}
