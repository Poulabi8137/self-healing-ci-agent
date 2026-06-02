import { useState, useCallback, useEffect, type ReactNode } from 'react'

import { AuthContext, extractRole, getInitialDark, applyDark, useAuth } from './auth-context'

export function AuthProvider({ children }: { children: ReactNode }) {
  const [apiKey, setApiKey] = useState<string | null>(() => {
    try {
      return sessionStorage.getItem('ci_agent_api_key')
    } catch {
      return null
    }
  })

  const [role, setRole] = useState<string | null>(() =>
    apiKey ? extractRole(apiKey) : null,
  )

  const [isInitialized] = useState(true)

  const [isDark, setIsDark] = useState<boolean>(() => {
    const initial = getInitialDark()
    applyDark(initial)
    return initial
  })

  const toggleDark = useCallback(() => {
    setIsDark((prev) => {
      const next = !prev
      applyDark(next)
      try {
        localStorage.setItem('ci_agent_dark_mode', String(next))
      } catch {
        /* localStorage may be unavailable */
      }
      return next
    })
  }, [])

  const login = useCallback((key: string) => {
    setApiKey(key)
    setRole(extractRole(key))
    try {
      sessionStorage.setItem('ci_agent_api_key', key)
    } catch {
      /* sessionStorage may be full or unavailable */
    }
  }, [])

  const logout = useCallback(() => {
    setApiKey(null)
    setRole(null)
    try {
      sessionStorage.removeItem('ci_agent_api_key')
    } catch {
      /* sessionStorage may be unavailable */
    }
  }, [])

  const handleStorage = useCallback((e: StorageEvent) => {
    if (e.key === 'ci_agent_api_key') {
      if (e.newValue) {
        setApiKey(e.newValue)
        setRole(extractRole(e.newValue))
      } else {
        setApiKey(null)
        setRole(null)
      }
    }
  }, [])

  useEffect(() => {
    window.addEventListener('storage', handleStorage)
    return () => window.removeEventListener('storage', handleStorage)
  }, [handleStorage])

  const value = {
    apiKey,
    role,
    isAuthenticated: !!apiKey,
    isInitialized,
    isDark,
    login,
    logout,
    toggleDark,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

interface LoginFormProps {
  onLogin?: (key: string) => void
}

export function LoginForm({ onLogin }: LoginFormProps) {
  const { login } = useAuth()
  const [keyInput, setKeyInput] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [showKey, setShowKey] = useState(false)

  const handleSubmit = useCallback(() => {
    const trimmed = keyInput.trim()
    if (!trimmed) {
      setError('API key is required')
      return
    }
    setError('')
    setLoading(true)
    login(trimmed)
    onLogin?.(trimmed)
    setLoading(false)
  }, [keyInput, login, onLogin])

  const handleInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setKeyInput(e.target.value)
    if (error) setError('')
  }, [error])

  return (
    <form
      onSubmit={(e) => { e.preventDefault(); handleSubmit() }}
      aria-label="Login form"
      className="flex flex-col gap-6"
    >
      <div className="flex flex-col gap-2">
        <label htmlFor="api-key-input" className="text-sm font-medium text-foreground/90">
          API Key
        </label>
        <div className="relative">
          <input
            id="api-key-input"
            type={showKey ? 'text' : 'password'}
            value={keyInput}
            onChange={handleInputChange}
            placeholder="Enter your API key"
            autoFocus
            aria-required="true"
            aria-invalid={!!error}
            aria-describedby={error ? 'login-error' : undefined}
            autoComplete="off"
            disabled={loading}
            className="h-11 w-full rounded-lg border bg-zinc-900/50 px-3.5 text-sm text-foreground placeholder:text-zinc-500 transition-all duration-200 focus:border-blue-500 focus:ring-[1.5px] focus:ring-blue-500/30 focus:outline-none disabled:opacity-50"
            style={{ borderColor: error ? 'rgb(239 68 68 / 0.5)' : undefined }}
          />
          <button
            type="button"
            onClick={() => setShowKey((v) => !v)}
            tabIndex={-1}
            className="absolute right-2.5 top-1/2 -translate-y-1/2 text-zinc-500 hover:text-zinc-300 transition-colors"
            aria-label={showKey ? 'Hide API key' : 'Show API key'}
          >
            {showKey ? (
              <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94" />
                <path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19" />
                <line x1="1" y1="1" x2="23" y2="23" />
              </svg>
            ) : (
              <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z" />
                <circle cx="12" cy="12" r="3" />
              </svg>
            )}
          </button>
        </div>
      </div>
      <div className="min-h-[1.25rem]">
        {error && (
          <p id="login-error" role="alert" className="flex items-center gap-1.5 text-sm text-red-400">
            <svg className="h-4 w-4 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="10" />
              <line x1="12" y1="8" x2="12" y2="12" />
              <line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
            {error}
          </p>
        )}
      </div>
      <button
        type="submit"
        disabled={loading}
        aria-label="Log in with the provided API key"
        className="flex h-11 w-full items-center justify-center gap-2 rounded-lg bg-blue-600 px-4 text-sm font-semibold text-white shadow-sm transition-all duration-200 hover:bg-blue-700 hover:shadow-md active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-blue-500/50"
      >
        {loading ? (
          <>
            <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            Signing in
          </>
        ) : (
          'Sign in'
        )}
      </button>
    </form>
  )
}


