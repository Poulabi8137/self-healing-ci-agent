import { useAuth } from '@/lib/auth'

export function DarkModeToggle() {
  const { isDark, toggleDark } = useAuth()

  return (
    <button
      onClick={toggleDark}
      className="rounded-md px-3 py-1.5 text-sm text-muted-foreground hover:bg-accent"
      aria-label={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
    >
      {isDark ? 'Light' : 'Dark'}
    </button>
  )
}
