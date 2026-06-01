import { PageTransition } from '@/components/page-transition'
import { useTaskList } from '@/lib/api'

export default function Tasks() {
  const { data: tasks } = useTaskList()

  return (
    <PageTransition>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-semibold">Tasks</h1>
          <p className="text-sm text-muted-foreground">Background task queue</p>
        </div>
        <div className="rounded-xl border border-border bg-card p-6">
          <div className="flex h-48 items-center justify-center">
            <p className="text-sm text-muted-foreground">
              {tasks ? `${(tasks as unknown[]).length} tasks` : 'Task list — Phase 7'}
            </p>
          </div>
        </div>
      </div>
    </PageTransition>
  )
}
