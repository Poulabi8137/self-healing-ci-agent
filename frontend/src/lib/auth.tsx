import { createContext, useContext, useState, useEffect, type ReactNode } from 'react'

interface UserInfo {
  keyPrefix: string
  name: string
  role: 'candidate' | 'recruiter' | 'admin'
}

interface AuthState {
  apiKey: string | null
  user: UserInfo | null
  isAuthenticated: boolean
  isInitialized: boolean
  isDark: boolean
  login: (key: string) => void
  logout: () => void
  setUser: (user: UserInfo) => void
  toggleDark: () => void
}

const AuthContext = createContext<AuthState | null>(null)

const STORAGE_KEY = 'sh_api_key'
const DARK_KEY = 'sh_dark_mode'

export function AuthProvider({ children }: { children: ReactNode }) {
  const [apiKey, setApiKey] = useState<string | null>(() => localStorage.getItem(STORAGE_KEY))
  const [user, setUser] = useState<UserInfo | null>(null)
  const [isInitialized, setIsInitialized] = useState(false)
  const [isDark, setIsDark] = useState(() => {
    const stored = localStorage.getItem(DARK_KEY)
    if (stored !== null) return stored === 'true'
    return true
  })

  useEffect(() => {
    setIsInitialized(true)
  }, [])

  useEffect(() => {
    const root = document.documentElement
    if (isDark) {
      root.classList.add('dark')
    } else {
      root.classList.remove('dark')
    }
    localStorage.setItem(DARK_KEY, String(isDark))
  }, [isDark])

  function login(key: string) {
    localStorage.setItem(STORAGE_KEY, key)
    setApiKey(key)
  }

  function logout() {
    localStorage.removeItem(STORAGE_KEY)
    setApiKey(null)
    setUser(null)
  }

  function toggleDark() {
    setIsDark((prev) => !prev)
  }

  return (
    <AuthContext.Provider
      value={{
        apiKey,
        user,
        isAuthenticated: !!apiKey,
        isInitialized,
        isDark,
        login,
        logout,
        setUser,
        toggleDark,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
