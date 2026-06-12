import { useState } from 'react'
import { GitPullRequest, CheckCircle, ExternalLink, BookOpen } from 'lucide-react'
import { toast } from 'sonner'
import { PageTransition } from '@/components/page-transition'
import { SpotlightCard } from '@/components/spotlight-card'
import { EmptyState } from '@/components/empty-state'
import { useAgent } from '@/lib/agent-context'
import { useTriggerPR } from '@/lib/api'

export default function PR() {
  const { setState: setAgent } = useAgent()
  const [repo, setRepo] = useState('')
  const [logs, setLogs] = useState('')
  const dryRun = true
  const [result, setResult] = useState<{ pr_url?: string; pr_number?: number; status: string; message: string } | null>(null)

  const mutation = useTriggerPR()

  async function handleSubmit() {
    if (!repo.trim() || !logs.trim()) {
      toast.error('Please enter both repository name and logs')
      return
    }

    try {
      setAgent({ label: 'Generating Fix', context: repo, color: 'blue' })
      const res = await mutation.mutateAsync({
        repository_name: repo,
        logs,
        dry_run: dryRun,
        approved: !dryRun,
      })
      setResult({ pr_url: res.pr_url, pr_number: res.pr_number, status: res.status, message: res.message })
      setAgent({ label: 'Idle', color: 'zinc' })
      toast.success('Pull request created')
    } catch {
      toast.error('Failed to create pull request')
      setAgent({ label: 'Idle', color: 'zinc' })
    }
  }

  return (
    <PageTransition>
      <div className="mb-6">
        <h1 className="text-2xl font-semibold">Pull Request Automation</h1>
        <p className="text-sm text-muted-foreground">Create pull requests from fix strategies with auto-generated descriptions</p>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <SpotlightCard className="p-6">
          <div className="mb-4 flex items-center gap-2">
            <GitPullRequest className="h-4 w-4 text-blue-500" />
            <h2 className="text-sm font-medium">Create Pull Request</h2>
          </div>
          <div className="space-y-4">
            <div>
              <label className="mb-1.5 block text-xs font-medium text-muted-foreground">Repository name</label>
              <input value={repo} onChange={(e) => setRepo(e.target.value)} placeholder="my-org/my-repo" className="w-full rounded-lg border border-input bg-background px-4 py-2.5 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring" />
            </div>
            <div>
              <label className="mb-1.5 block text-xs font-medium text-muted-foreground">CI/CD Logs</label>
              <textarea value={logs} onChange={(e) => setLogs(e.target.value)} placeholder="Paste CI/CD logs here..." rows={10} className="w-full rounded-lg border border-input bg-background px-4 py-2.5 text-sm font-mono placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring" />
            </div>
            <button onClick={handleSubmit} disabled={mutation.isPending} className="w-full rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-blue-500 disabled:opacity-50 transition-colors">
              {mutation.isPending ? 'Creating...' : dryRun ? 'Simulate PR (Dry Run)' : 'Create Pull Request'}
            </button>
          </div>
        </SpotlightCard>

        <SpotlightCard className="p-6">
          <div className="mb-4 flex items-center gap-2">
            <BookOpen className="h-4 w-4 text-zinc-400" />
            <h2 className="text-sm font-medium">Results</h2>
          </div>
          {result ? (
            <div className="space-y-4">
              <div className="flex items-center gap-2 rounded-lg border border-emerald-500/20 bg-emerald-500/5 p-3">
                <CheckCircle className="h-4 w-4 text-emerald-500" />
                <span className="text-sm text-emerald-400">{result.status === 'completed' ? 'Pull request created' : result.status}</span>
              </div>
              {result.pr_url && (
                <a href={result.pr_url} target="_blank" rel="noopener noreferrer" className="flex items-center gap-2 text-sm text-blue-500 hover:text-blue-400">
                  <ExternalLink className="h-4 w-4" />
                  View PR #{result.pr_number}
                </a>
              )}
              <p className="text-sm text-zinc-400">{result.message}</p>
            </div>
          ) : (
            <EmptyState icon={GitPullRequest} title="No results yet" description="Enter repository name and logs, then create a pull request." />
          )}
        </SpotlightCard>
      </div>
    </PageTransition>
  )
}
