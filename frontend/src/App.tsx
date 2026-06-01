import { useState, useCallback } from 'react'
import { BrowserRouter, Routes, Route, useLocation } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { LazyMotion, domAnimation, AnimatePresence } from 'framer-motion'
import { Toaster } from 'sonner'
import { AuthProvider } from '@/lib/auth'
import { Layout } from '@/components/layout'
import { AuthGuard, PublicGuard } from '@/components/auth-guard'
import { CommandPalette } from '@/components/command-palette'
import { useKeyboardShortcuts } from '@/hooks/use-keyboard-shortcuts'
import Landing from '@/pages/landing'
import Login from '@/pages/login'
import Dashboard from '@/pages/dashboard'
import Analysis from '@/pages/analysis'
import Validation from '@/pages/validation'
import Retry from '@/pages/retry'
import Review from '@/pages/review'
import PR from '@/pages/pr'
import Indexing from '@/pages/indexing'
import Tasks from '@/pages/tasks'
import AdminKeys from '@/pages/admin-keys'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      retry: 2,
    },
  },
})

function AnimatedRoutes() {
  const location = useLocation()

  return (
    <AnimatePresence mode="wait">
      <Routes location={location} key={location.pathname}>
        <Route element={<PublicGuard />}>
          <Route path="/" element={<Landing />} />
          <Route path="/login" element={<Login />} />
        </Route>
        <Route element={<AuthGuard />}>
          <Route element={<Layout />}>
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/analysis" element={<Analysis />} />
            <Route path="/validation" element={<Validation />} />
            <Route path="/retry" element={<Retry />} />
            <Route path="/review" element={<Review />} />
            <Route path="/pr" element={<PR />} />
            <Route path="/indexing" element={<Indexing />} />
            <Route path="/tasks" element={<Tasks />} />
            <Route path="/admin/keys" element={<AdminKeys />} />
          </Route>
        </Route>
      </Routes>
    </AnimatePresence>
  )
}

function AppShell() {
  const [paletteOpen, setPaletteOpen] = useState(false)
  const openPalette = useCallback(() => setPaletteOpen(true), [])
  const closePalette = useCallback(() => setPaletteOpen(false), [])

  useKeyboardShortcuts(openPalette)

  return (
    <>
      <AnimatedRoutes />
      <CommandPalette open={paletteOpen} onClose={closePalette} />
    </>
  )
}

export default function App() {
  return (
    <LazyMotion features={domAnimation}>
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <BrowserRouter>
            <AppShell />
            <Toaster
              position="bottom-right"
              theme="dark"
              toastOptions={{
                style: {
                  background: '#121213',
                  border: '1px solid #1f1f23',
                  color: '#fafafa',
                },
              }}
            />
          </BrowserRouter>
        </AuthProvider>
      </QueryClientProvider>
    </LazyMotion>
  )
}
