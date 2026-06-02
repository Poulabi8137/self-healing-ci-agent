import { Outlet, Link, useLocation } from 'react-router-dom'
import { useAuth } from '../lib/auth'
import { DarkModeToggle } from '../components/dark-mode'
import { useEffect, useCallback, useRef } from 'react'

const NAV_ITEMS = [
  { to: '/', label: 'Dashboard', 'aria-label': 'Navigate to dashboard' },
  { to: '/analysis', label: 'Analysis', 'aria-label': 'Navigate to analysis' },
  { to: '/validation', label: 'Validation', 'aria-label': 'Navigate to validation' },
]

export default function Layout() {
  const { isAuthenticated, role, logout } = useAuth()
  const location = useLocation()
  const logoutRef = useRef<HTMLButtonElement>(null)
  const mainRef = useRef<HTMLElement>(null)

  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        mainRef.current?.focus()
      }
    },
    [],
  )

  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [handleKeyDown])

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-gray-100 flex flex-col">
      <a href="#main-content" className="sr-only focus:not-sr-only focus:fixed focus:top-2 focus:left-2 focus:z-50 focus:px-4 focus:py-2 focus:bg-blue-600 focus:text-white focus:rounded">
        Skip to main content
      </a>

      <header role="banner" className="border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-6">
              <span className="text-lg font-semibold text-gray-900 dark:text-white">
                CI Agent
              </span>
              {isAuthenticated && (
                <nav role="navigation" aria-label="Main navigation">
                  <ul className="flex items-center gap-1">
                    {NAV_ITEMS.map((item) => (
                      <li key={item.to}>
                        <Link
                          to={item.to}
                          aria-label={item['aria-label']}
                          aria-current={location.pathname === item.to ? 'page' : undefined}
                          className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                            location.pathname === item.to
                              ? 'bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-200'
                              : 'text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                          }`}
                        >
                          {item.label}
                        </Link>
                      </li>
                    ))}
                  </ul>
                </nav>
              )}
            </div>

            <div className="flex items-center gap-4">
              <DarkModeToggle />
              {isAuthenticated && (
                <div className="flex items-center gap-3">
                  <span className="text-sm text-gray-500 dark:text-gray-400">
                    {role ?? 'user'}
                  </span>
                  <button
                    ref={logoutRef}
                    onClick={logout}
                    className="text-sm text-red-600 dark:text-red-400 hover:text-red-800 dark:hover:text-red-300"
                    aria-label="Log out of the application"
                  >
                    Logout
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </header>

      <main
        ref={mainRef}
        id="main-content"
        role="main"
        tabIndex={-1}
        className="flex-1 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 w-full outline-none"
      >
        <Outlet />
      </main>

      <footer role="contentinfo" className="border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 py-4">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center text-sm text-gray-500 dark:text-gray-400">
          Self-Healing CI Agent
        </div>
      </footer>
    </div>
  )
}
