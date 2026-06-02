/* eslint-disable react-hooks/set-state-in-effect */
import { useState, useEffect, useRef, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  LayoutDashboard, Search, ShieldCheck, RotateCw, Eye, GitPullRequest,
  BookOpen, ListChecks, Key, Moon, LogOut, type LucideIcon,
} from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '@/lib/auth'

interface Command {
  id: string
  label: string
  shortcut: string
  icon: LucideIcon
  section: string
  action: () => void
}

const FOCUSABLE_SELECTOR = 'a[href], button:not([disabled]), input:not([disabled]), textarea:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])'

export function CommandPalette({ open, onClose }: { open: boolean; onClose: () => void }) {
  const navigate = useNavigate()
  const { toggleDark, logout } = useAuth()
  const inputRef = useRef<HTMLInputElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const previousFocusRef = useRef<HTMLElement | null>(null)
  const [query, setQuery] = useState('')
  const [selectedIdx, setSelectedIdx] = useState(0)

  useEffect(() => {
    if (open) {
      previousFocusRef.current = document.activeElement as HTMLElement
      setQuery('')
      setSelectedIdx(0)
      setTimeout(() => inputRef.current?.focus(), 10)
    } else if (previousFocusRef.current && typeof previousFocusRef.current.focus === 'function') {
      previousFocusRef.current.focus()
      previousFocusRef.current = null
    }
  }, [open])

  useEffect(() => {
    setSelectedIdx(0)
  }, [query])

  const commands: Command[] = [
    { id: 'dashboard', label: 'Dashboard', shortcut: 'G D', icon: LayoutDashboard, section: 'Pages', action: () => navigate('/dashboard') },
    { id: 'analysis', label: 'Analysis', shortcut: 'G A', icon: Search, section: 'Pages', action: () => navigate('/analysis') },
    { id: 'validation', label: 'Validation', shortcut: 'G V', icon: ShieldCheck, section: 'Pages', action: () => navigate('/validation') },
    { id: 'retry', label: 'Retry', shortcut: '', icon: RotateCw, section: 'Pages', action: () => navigate('/retry') },
    { id: 'review', label: 'Review', shortcut: 'G R', icon: Eye, section: 'Pages', action: () => navigate('/review') },
    { id: 'pr', label: 'Pull Requests', shortcut: '', icon: GitPullRequest, section: 'Pages', action: () => navigate('/pr') },
    { id: 'indexing', label: 'Indexing', shortcut: '', icon: BookOpen, section: 'Pages', action: () => navigate('/indexing') },
    { id: 'tasks', label: 'Tasks', shortcut: 'G T', icon: ListChecks, section: 'Pages', action: () => navigate('/tasks') },
    { id: 'admin-keys', label: 'Admin Keys', shortcut: '', icon: Key, section: 'Pages', action: () => navigate('/admin/keys') },
    { id: 'dark-mode', label: 'Toggle Dark Mode', shortcut: '', icon: Moon, section: 'Actions', action: () => { toggleDark(); onClose() } },
    { id: 'logout', label: 'Logout', shortcut: '', icon: LogOut, section: 'Actions', action: () => { logout(); navigate('/login') } },
  ]

  const filtered = query.trim()
    ? commands.filter(c => c.label.toLowerCase().includes(query.toLowerCase()) || c.section.toLowerCase().includes(query.toLowerCase()))
    : commands

  const select = useCallback((cmd: Command) => {
    cmd.action()
    onClose()
  }, [onClose])

  useEffect(() => {
    if (!open && previousFocusRef.current && typeof previousFocusRef.current.focus === 'function') {
      previousFocusRef.current.focus()
      previousFocusRef.current = null
    }
  }, [open])

  const trapFocus = useCallback((e: KeyboardEvent) => {
    if (!open || !containerRef.current) return
    const focusable = containerRef.current.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTOR)
    if (focusable.length === 0) return
    const first = focusable[0]
    const last = focusable[focusable.length - 1]
    if (e.key === 'Tab') {
      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault()
        last.focus()
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault()
        first.focus()
      }
    }
  }, [open])

  useEffect(() => {
    if (!open) return
    function handleKey(e: KeyboardEvent) {
      if (e.key === 'Escape') { e.preventDefault(); onClose(); return }
      if (e.key === 'ArrowDown') { e.preventDefault(); setSelectedIdx(i => Math.min(i + 1, filtered.length - 1)); return }
      if (e.key === 'ArrowUp') { e.preventDefault(); setSelectedIdx(i => Math.max(i - 1, 0)); return }
      if (e.key === 'Enter' && filtered[selectedIdx]) { e.preventDefault(); select(filtered[selectedIdx]); return }
      trapFocus(e)
    }
    window.addEventListener('keydown', handleKey)
    return () => window.removeEventListener('keydown', handleKey)
  }, [open, filtered, selectedIdx, select, onClose, trapFocus])

  const grouped = filtered.reduce<Record<string, Command[]>>((acc, cmd) => {
    if (!acc[cmd.section]) acc[cmd.section] = []
    acc[cmd.section].push(cmd)
    return acc
  }, {})

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.15 }}
          className="fixed inset-0 z-[100] flex items-start justify-center pt-[15vh] bg-black/50 backdrop-blur-sm"
          onClick={(e) => { if (e.target === e.currentTarget) onClose() }}
          role="dialog"
          aria-modal="true"
          aria-label="Command palette"
        >
          <motion.div
            ref={containerRef}
            initial={{ opacity: 0, scale: 0.96, y: -10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.96, y: -10 }}
            transition={{ duration: 0.2, ease: [0.16, 1, 0.3, 1] }}
            className="w-full max-w-lg rounded-xl border border-border bg-card shadow-2xl overflow-hidden"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center gap-3 border-b border-border px-4">
              <Search className="h-4 w-4 shrink-0 text-muted-foreground" aria-hidden="true" />
              <input
                ref={inputRef}
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search pages and actions…"
                aria-label="Search commands"
                className="h-12 w-full bg-transparent text-sm text-foreground outline-none placeholder:text-muted-foreground"
              />
              <kbd className="hidden shrink-0 rounded-md border border-border px-1.5 py-0.5 text-[10px] text-muted-foreground sm:inline" aria-label="Close">ESC</kbd>
            </div>

            <div className="max-h-80 overflow-y-auto px-2 py-2" role="listbox" aria-label="Commands">
              {Object.entries(grouped).map(([section, items]) => (
                <div key={section}>
                  <p className="px-2 py-1.5 text-[11px] font-medium uppercase tracking-wider text-muted-foreground" role="presentation">{section}</p>
                  {items.map((cmd) => {
                    const idx = filtered.indexOf(cmd)
                    return (
                      <button
                        key={cmd.id}
                        role="option"
                        aria-selected={idx === selectedIdx}
                        onClick={() => select(cmd)}
                        onMouseEnter={() => setSelectedIdx(idx)}
                        className={`flex w-full items-center gap-3 rounded-lg px-2 py-2.5 text-left text-sm transition-colors ${
                          idx === selectedIdx ? 'bg-accent text-accent-foreground' : 'text-foreground'
                        }`}
                      >
                        <cmd.icon className="h-4 w-4 shrink-0 text-muted-foreground" aria-hidden="true" />
                        <span className="flex-1">{cmd.label}</span>
                        {cmd.shortcut && (
                          <kbd className="rounded-md border border-border px-1.5 py-0.5 text-[10px] text-muted-foreground">{cmd.shortcut}</kbd>
                        )}
                      </button>
                    )
                  })}
                </div>
              ))}

              {filtered.length === 0 && (
                <p className="px-2 py-8 text-center text-sm text-muted-foreground" role="status">No results for &ldquo;{query}&rdquo;</p>
              )}
            </div>

            <div className="flex items-center gap-4 border-t border-border px-4 py-2 text-[10px] text-muted-foreground" aria-hidden="true">
              <span>↑↓ navigate</span>
              <span>↵ select</span>
              <span>esc close</span>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
