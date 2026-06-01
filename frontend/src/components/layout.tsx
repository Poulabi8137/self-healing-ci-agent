import { Outlet } from 'react-router-dom'
import { Sun, Moon, LogOut } from 'lucide-react'
import { useAuth } from '@/lib/auth'
import { Nav } from '@/components/nav'
import { cn } from '@/lib/utils'
import { useState } from 'react'

export function Layout() {
  const { user, isDark, toggleDark, logout } = useAuth()
  const [sidebarOpen, setSidebarOpen] = useState(true)

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      <aside
        className={cn(
          'flex flex-col border-r border-border bg-card transition-all duration-300',
          sidebarOpen ? 'w-60' : 'w-0 overflow-hidden md:w-16',
        )}
      >
        <div className="flex h-14 items-center gap-2 border-b border-border px-4">
          <div className="h-6 w-6 rounded bg-primary" />
          {sidebarOpen && (
            <span className="text-sm font-semibold">CI/CD Agent</span>
          )}
        </div>
        <div className="flex-1 overflow-y-auto">
          <Nav />
        </div>
        {sidebarOpen && user && (
          <div className="border-t border-border px-4 py-3">
            <p className="text-xs text-muted-foreground">{user.name}</p>
            <p className="text-xs text-muted-foreground capitalize">{user.role}</p>
          </div>
        )}
      </aside>

      <div className="flex flex-1 flex-col overflow-hidden">
        <header className="flex h-14 items-center justify-between border-b border-border px-6">
          <button
            onClick={() => setSidebarOpen((o) => !o)}
            className="rounded-md p-1.5 text-muted-foreground hover:bg-accent"
          >
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5" />
            </svg>
          </button>

          <div className="flex items-center gap-2">
            <button
              onClick={toggleDark}
              className="rounded-md p-1.5 text-muted-foreground hover:bg-accent"
              title={isDark ? 'Light mode' : 'Dark mode'}
            >
              {isDark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
            </button>
            <button
              onClick={logout}
              className="rounded-md p-1.5 text-muted-foreground hover:bg-accent"
              title="Log out"
            >
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        </header>

        <main className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
