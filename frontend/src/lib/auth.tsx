/* eslint-disable react-refresh/only-export-components */
import { createContext, useContext, useState, useCallback, useEffect, type ReactNode } from 'react'

interface AuthContextValue {
  apiKey: string | null
  role: string | null
  isAuthenticated: boolean
  isInitialized: boolean
  isDark: boolean
  login: (key: string) => void
  logout: () => void
  toggleDark: () => void
}

const AuthContext = createContext<AuthContextValue>({
  apiKey: null,
  role: null,
  isAuthenticated: false,
  isInitialized: true,
  isDark: false,
  login: () => {},
  logout: () => {},
  toggleDark: () => {},
})

function decodeRole(raw: string): string {
  const lower = raw.toLowerCase()
  if (lower.includes('admin')) return 'admin'
  if (lower.includes('recruiter')) return 'recruiter'
  return 'candidate'
}

function extractRole(apiKey: string): string | null {
  try {
    const parts = apiKey.split('.')
    if (parts.length >= 2) {
      return decodeRole(atob(parts[0]))
    }
    const payload = atob(apiKey.split('.')[0] || apiKey)
    const parsed = JSON.parse(payload)
    return parsed.role || parsed.type || null
  } catch {
    return null
  }
}

function getInitialDark(): boolean {
  try {
    return localStorage.getItem('ci_agent_dark_mode') === 'true'
  } catch {
    return false
  }
}

function applyDark(dark: boolean) {
  if (dark) {
    document.documentElement.classList.add('dark')
  } else {
    document.documentElement.classList.remove('dark')
  }
}

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

  const value: AuthContextValue = {
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

export function useAuth() {
  return useContext(AuthContext)
}

export function AuthGuard({ children }: { children: ReactNode }) {
  const { isAuthenticated } = useAuth()
  if (!isAuthenticated) {
    return null
  }
  return <>{children}</>
}

interface LoginFormProps {
  onLogin?: (key: string) => void
}

export function LoginForm({ onLogin }: LoginFormProps) {
  const { login } = useAuth()
  const [keyInput, setKeyInput] = useState('')
  const [error, setError] = useState('')

  const handleSubmit = useCallback(() => {
    const trimmed = keyInput.trim()
    if (!trimmed) {
      setError('API key is required')
      return
    }
    setError('')
    login(trimmed)
    onLogin?.(trimmed)
  }, [keyInput, login, onLogin])

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLInputElement>) => {
      if (e.key === 'Enter') {
        handleSubmit()
      }
    },
    [handleSubmit],
  )

  return (
    <div role="form" aria-label="Login form">
      <label htmlFor="api-key-input">API Key</label>
      <input
        id="api-key-input"
        type="text"
        value={keyInput}
        onChange={(e) => setKeyInput(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Enter your API key"
        aria-required="true"
        aria-invalid={!!error}
        aria-describedby={error ? 'login-error' : undefined}
        autoComplete="off"
      />
      {error && (
        <p id="login-error" role="alert">
          {error}
        </p>
      )}
      <button onClick={handleSubmit} aria-label="Log in with the provided API key">
        Login
      </button>
    </div>
  )
}
