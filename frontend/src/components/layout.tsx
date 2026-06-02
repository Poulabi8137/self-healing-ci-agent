import { Outlet, Link, useLocation } from 'react-router-dom'
import { useAuth } from '../lib/auth-context'
import { DarkModeToggle } from '../components/dark-mode'
import { useEffect, useCallback, useRef } from 'react'
import { AlertTriangle, ShieldCheck, GitPullRequest, BookOpen, BarChart3, Settings, ListTodo, LogOut, LayoutDashboard } from 'lucide-react'

interface NavItem {
  to: string
  label: string
  icon: typeof LayoutDashboard
}

const NAV_ITEMS: NavItem[] = [
  { to: '/dashboard', label: 'Overview', icon: LayoutDashboard },
  { to: '/analysis', label: 'Failures', icon: AlertTriangle },
  { to: '/validation', label: 'Fixes', icon: ShieldCheck },
  { to: '/pr', label: 'Pull Requests', icon: GitPullRequest },
  { to: '/indexing', label: 'Repositories', icon: BookOpen },
  { to: '/review', label: 'Analytics', icon: BarChart3 },
]

const SECONDARY_ITEMS: NavItem[] = [
  { to: '/admin/keys', label: 'Settings', icon: Settings },
  { to: '/tasks', label: 'Tasks', icon: ListTodo },
]

export default function Layout() {
  const { isAuthenticated, role, logout } = useAuth()
  const location = useLocation()
  const mainRef = useRef<HTMLElement>(null)

  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    if (e.key === 'Escape') mainRef.current?.focus()
  }, [])

  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [handleKeyDown])

  if (!isAuthenticated) return null

  return (
    <div className="min-h-screen bg-[#070708] text-zinc-100 flex flex-col">
      <a href="#main-content" className="sr-only focus:not-sr-only focus:fixed focus:top-2 focus:left-2 focus:z-50 focus:px-4 focus:py-2 focus:bg-blue-600 focus:text-white focus:rounded">
        Skip to main content
      </a>

      <header className="border-b border-[#1f1f23] bg-[#0a0a0c]/80 backdrop-blur-xl sticky top-0 z-50">
        <div className="mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-14">
            <div className="flex items-center gap-5">
              <Link to="/dashboard" className="flex items-center gap-2.5 shrink-0">
                <div className="flex h-7 w-7 items-center justify-center rounded-md bg-gradient-to-br from-blue-500 to-violet-600">
                  <svg className="h-4 w-4 text-white" viewBox="0 0 24 24" fill="currentColor"><path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/></svg>
                </div>
                <span className="text-sm font-semibold text-zinc-100 hidden sm:inline">CI Agent</span>
              </Link>
              <nav className="hidden lg:flex items-center gap-0.5">
                {NAV_ITEMS.map((item) => {
                  const Icon = item.icon
                  const active = location.pathname === item.to
                  return (
                    <Link
                      key={item.to}
                      to={item.to}
                      className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-md text-xs font-medium transition-all duration-200 ${
                        active
                          ? 'bg-blue-500/10 text-blue-400 border border-blue-500/15'
                          : 'text-zinc-500 hover:text-zinc-300 hover:bg-zinc-800/40 border border-transparent'
                      }`}
                    >
                      <Icon className="h-3.5 w-3.5" />
                      {item.label}
                    </Link>
                  )
                })}
                <span className="mx-1.5 h-4 w-px bg-zinc-800" />
                {SECONDARY_ITEMS.map((item) => {
                  const Icon = item.icon
                  const active = location.pathname === item.to
                  return (
                    <Link
                      key={item.to}
                      to={item.to}
                      className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-md text-xs font-medium transition-all duration-200 ${
                        active
                          ? 'bg-zinc-700/30 text-zinc-300 border border-zinc-700/30'
                          : 'text-zinc-600 hover:text-zinc-400 hover:bg-zinc-800/30 border border-transparent'
                      }`}
                    >
                      <Icon className="h-3.5 w-3.5" />
                      {item.label}
                    </Link>
                  )
                })}
              </nav>
            </div>

            <div className="flex items-center gap-3">
              <DarkModeToggle />
              <div className="flex items-center gap-2.5">
                <span className="text-xs text-zinc-500 hidden sm:inline">{role ?? 'user'}</span>
                <span className="hidden sm:inline-flex h-5 w-px bg-[#1f1f23]" />
                <button
                  onClick={logout}
                  className="flex items-center gap-1.5 text-xs text-zinc-500 hover:text-zinc-300 transition-colors"
                  aria-label="Log out"
                >
                  <LogOut className="h-3.5 w-3.5" />
                  <span className="hidden sm:inline">Logout</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </header>

      <main
        ref={mainRef}
        id="main-content"
        tabIndex={-1}
        className="flex-1 mx-auto px-4 sm:px-6 lg:px-8 py-6 w-full max-w-7xl outline-none"
      >
        <Outlet />
      </main>
    </div>
  )
}
