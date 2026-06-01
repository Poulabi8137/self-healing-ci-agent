import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '@/lib/auth'

export default function Login() {
  const { login, setUser } = useAuth()
  const navigate = useNavigate()
  const [key, setKey] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!key.trim()) return

    setLoading(true)
    setError('')

    try {
      const res = await fetch('/api/auth/me', {
        headers: { 'X-API-Key': key.trim() },
      })

      if (!res.ok) {
        setError(res.status === 401 ? 'Invalid API key' : `Error ${res.status}`)
        setLoading(false)
        return
      }

      const data = await res.json()
      login(key.trim())
      setUser({ keyPrefix: data.key_prefix, name: data.name, role: data.role })
      navigate('/dashboard')
    } catch {
      setError('Could not connect to server')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <div className="w-full max-w-sm">
        <div className="mb-8 text-center">
          <div className="mx-auto mb-4 h-10 w-10 rounded bg-primary" />
          <h1 className="text-xl font-semibold">CI/CD Agent</h1>
          <p className="mt-1 text-sm text-muted-foreground">Enter your API key to continue</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <input
              type="password"
              placeholder="sk-..."
              value={key}
              onChange={(e) => setKey(e.target.value)}
              className="w-full rounded-lg border border-input bg-background px-4 py-2.5 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
              autoFocus
            />
          </div>

          {error && (
            <p className="text-sm text-destructive">{error}</p>
          )}

          <button
            type="submit"
            disabled={loading || !key.trim()}
            className="w-full rounded-lg bg-primary px-4 py-2.5 text-sm font-medium text-primary-foreground shadow-sm hover:opacity-90 disabled:opacity-50"
          >
            {loading ? 'Verifying...' : 'Continue'}
          </button>
        </form>

        <p className="mt-6 text-center text-xs text-muted-foreground">
          <button
            onClick={() => navigate('/')}
            className="underline hover:text-foreground"
          >
            Back to landing
          </button>
        </p>
      </div>
    </div>
  )
}
