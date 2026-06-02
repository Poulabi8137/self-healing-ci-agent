import { createContext, useContext } from 'react'

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

export function useAuth() {
  return useContext(AuthContext)
}

export type { AuthContextValue }
export { AuthContext, extractRole, getInitialDark, applyDark }
