import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard,
  Search,
  ShieldCheck,
  RefreshCw,
  FileText,
  GitPullRequest,
  Database,
  ListTodo,
  Key,
  type LucideIcon,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { useAuth } from '@/lib/auth'

interface NavItem {
  label: string
  href: string
  icon: LucideIcon
  roles?: ('candidate' | 'recruiter' | 'admin')[]
}

const items: NavItem[] = [
  { label: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { label: 'Analysis', href: '/analysis', icon: Search },
  { label: 'Validation', href: '/validation', icon: ShieldCheck, roles: ['recruiter', 'admin'] },
  { label: 'Retry', href: '/retry', icon: RefreshCw, roles: ['recruiter', 'admin'] },
  { label: 'Review', href: '/review', icon: FileText, roles: ['recruiter', 'admin'] },
  { label: 'Pull Requests', href: '/pr', icon: GitPullRequest, roles: ['recruiter', 'admin'] },
  { label: 'Indexing', href: '/indexing', icon: Database, roles: ['recruiter', 'admin'] },
  { label: 'Tasks', href: '/tasks', icon: ListTodo },
  { label: 'API Keys', href: '/admin/keys', icon: Key, roles: ['admin'] },
]

export function Nav() {
  const { role } = useAuth()
  const userRole = role ?? 'candidate'

  const visible = items.filter(
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
    </nav>
  )
}
