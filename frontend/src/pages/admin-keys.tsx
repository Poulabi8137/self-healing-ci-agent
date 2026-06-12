import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Key, Plus, Trash2, Copy } from 'lucide-react'
import { toast } from 'sonner'
import { PageTransition } from '@/components/page-transition'
import { SpotlightCard } from '@/components/spotlight-card'
import { TiltCard } from '@/components/tilt-card'
import { EmptyState } from '@/components/empty-state'


interface ApiKey {
  id: string
  prefix: string
  name: string
  role: string
  created: string
  lastUsed: string | null
}

const roleDisplay: Record<string, string> = {
  admin: 'Admin',
  recruiter: 'Developer',
  candidate: 'Read-only',
}

function KeyCard({ k, onDelete }: { k: ApiKey; onDelete: (id: string) => void }) {
  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(k.prefix)
      toast.success('Copied to clipboard')
    } catch {
      toast.error('Failed to copy')
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, height: 0, marginBottom: 0 }}
      transition={{ duration: 0.2 }}
    >
      <TiltCard>
        <SpotlightCard className="p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3 min-w-0">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-muted">
                <Key className="h-4 w-4 text-muted-foreground" />
              </div>
              <div className="min-w-0">
                <p className="text-sm font-medium">{k.name}</p>
                <p className="font-mono text-[11px] text-muted-foreground">{k.prefix}</p>
              </div>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              <span className="text-[10px] text-muted-foreground uppercase">{roleDisplay[k.role] ?? k.role}</span>
              <button
                onClick={handleCopy}
                className="rounded-md p-1.5 text-muted-foreground hover:bg-accent"
                aria-label="Copy key"
              >
                <Copy className="h-3.5 w-3.5" />
              </button>
              <button
                onClick={() => onDelete(k.id)}
                className="rounded-md p-1.5 text-red-400 hover:bg-red-500/10"
                aria-label="Delete key"
              >
                <Trash2 className="h-3.5 w-3.5" />
              </button>
            </div>
          </div>
          <div className="mt-2 flex gap-4 text-[10px] text-muted-foreground">
            <span>Created: {k.created}</span>
            {k.lastUsed && <span>Last used: {k.lastUsed}</span>}
          </div>
        </SpotlightCard>
      </TiltCard>
    </motion.div>
  )
}

export default function AdminKeys() {
  const [keys, setKeys] = useState<ApiKey[]>(() => []
  )
  const [showForm, setShowForm] = useState(false)
  const [newName, setNewName] = useState('')
  const [newRole, setNewRole] = useState('candidate')

  function handleDelete(id: string) {
    setKeys((prev) => prev.filter((k) => k.id !== id))
    toast.success('Key deleted')
  }

  async function handleCreate() {
    if (!newName.trim()) {
      toast.error('Please enter a name for the key')
      return
    }
    const newKey: ApiKey = {
      id: `${Date.now()}`,
      prefix: `ci_agent_sk_${Math.random().toString(36).slice(2, 10)}`,
      name: newName.trim(),
      role: newRole,
      created: new Date().toISOString().split('T')[0],
      lastUsed: null,
    }
    setKeys((prev) => [newKey, ...prev])
    setNewName('')
    setShowForm(false)
    toast.success('API key created')
  }

  return (
    <PageTransition>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold">Settings</h1>
            <p className="text-sm text-muted-foreground">Manage API keys and access tokens</p>
          </div>
          <button
            onClick={() => setShowForm(!showForm)}
            className="flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:opacity-90"
          >
            <Plus className="h-4 w-4" />
            Create Key
          </button>
        </div>

        <AnimatePresence>
          {showForm && (
            <motion.div
              initial={{ opacity: 0, y: -8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
            >
              <SpotlightCard className="p-5">
                <h3 className="mb-4 text-sm font-medium">New API Key</h3>
                <div className="grid gap-4 sm:grid-cols-3">
                  <div>
                    <label htmlFor="key-name" className="mb-1.5 block text-xs font-medium text-muted-foreground">Key name</label>
                    <input
                      id="key-name"
                      value={newName}
                      onChange={(e) => setNewName(e.target.value)}
                      placeholder="e.g. CI Pipeline Token"
                      className="w-full rounded-lg border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                    />
                  </div>
                  <div>
                    <label htmlFor="key-role" className="mb-1.5 block text-xs font-medium text-muted-foreground">Role</label>
                    <select
                      id="key-role"
                      value={newRole}
                      onChange={(e) => setNewRole(e.target.value)}
                      className="w-full rounded-lg border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                    >
                      <option value="candidate">Read-only</option>
                      <option value="recruiter">Developer</option>
                      <option value="admin">Admin</option>
                    </select>
                  </div>
                  <div className="flex items-end gap-2">
                    <button
                      onClick={handleCreate}
                      className="flex w-full items-center justify-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:opacity-90"
                    >
                      Create
                    </button>
                    <button
                      onClick={() => setShowForm(false)}
                      className="rounded-lg border border-border px-4 py-2 text-sm font-medium text-foreground hover:bg-accent"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              </SpotlightCard>
            </motion.div>
          )}
        </AnimatePresence>

        {keys.length > 0 ? (
          <div className="space-y-3">
            <AnimatePresence>
              {keys.map((k) => (
                <KeyCard key={k.id} k={k} onDelete={handleDelete} />
              ))}
            </AnimatePresence>
          </div>
        ) : (
          <div className="rounded-xl border border-border bg-card">
            <EmptyState
              icon={Key}
              title="No API keys"
              description="Create an API key to connect the CI agent."
            />
          </div>
        )}
      </div>
    </PageTransition>
  )
}
