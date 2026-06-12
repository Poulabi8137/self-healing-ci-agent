import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard,
  AlertTriangle,
  ShieldCheck,
  GitPullRequest,
  BookOpen,
  BarChart3,
  ListTodo,
  Settings,
  Activity,
  Bell,
  type LucideIcon,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { useAuth } from '@/lib/auth-context'

interface NavItem {
  label: string
  href: string
  icon: LucideIcon
  roles?: ('candidate' | 'recruiter' | 'admin')[]
}

const items: NavItem[] = [
  { label: 'Overview', href: '/dashboard', icon: LayoutDashboard },
  { label: 'Investigations', href: '/investigations', icon: Activity },
  { label: 'Failures', href: '/analysis', icon: AlertTriangle },
  { label: 'Fixes', href: '/validation', icon: ShieldCheck, roles: ['recruiter', 'admin'] },
  { label: 'Pull Requests', href: '/pr', icon: GitPullRequest, roles: ['recruiter', 'admin'] },
  { label: 'Repositories', href: '/indexing', icon: BookOpen, roles: ['recruiter', 'admin'] },
  { label: 'Analytics', href: '/review', icon: BarChart3, roles: ['recruiter', 'admin'] },
]

const secondaryItems: NavItem[] = [
  { label: 'Tasks', href: '/tasks', icon: ListTodo },
  { label: 'Notifications', href: '/notifications', icon: Bell },
  { label: 'Settings', href: '/admin/keys', icon: Settings, roles: ['admin'] },
]

export function Nav() {
  const { role } = useAuth()
  const userRole = role ?? 'candidate'

  const visible = items.filter(
    (item) => !item.roles || item.roles.includes(userRole as 'candidate' | 'recruiter' | 'admin'),
  )

  const visibleSecondary = secondaryItems.filter(
    (item) => !item.roles || item.roles.includes(userRole as 'candidate' | 'recruiter' | 'admin'),
  )

  return (
    <nav className="flex flex-col gap-1 px-3 py-4" aria-label="Sidebar navigation">
      {visible.map((item) => (
        <NavLink
          key={item.href}
          to={item.href}
          aria-label={item.label}
          className={({ isActive }) =>
            cn(
              'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
              isActive
                ? 'bg-accent text-accent-foreground'
                : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground',
            )
          }
        >
          <item.icon className="h-4 w-4" aria-hidden="true" />
          {item.label}
        </NavLink>
      ))}
      {visibleSecondary.length > 0 && (
        <>
          <div className="my-2 border-t border-border" />
          {visibleSecondary.map((item) => (
            <NavLink
              key={item.href}
              to={item.href}
              aria-label={item.label}
              className={({ isActive }) =>
                cn(
                  'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-accent text-accent-foreground'
                    : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground',
                )
              }
            >
              <item.icon className="h-4 w-4" aria-hidden="true" />
              {item.label}
            </NavLink>
          ))}
        </>
      )}
    </nav>
  )
}
