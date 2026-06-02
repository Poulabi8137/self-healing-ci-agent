import { lazy, Suspense, useState, useCallback } from 'react'
import { BrowserRouter, Routes, Route, useLocation } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { LazyMotion, domAnimation, AnimatePresence } from 'framer-motion'
import { Toaster } from 'sonner'
import { AuthProvider } from '@/lib/auth'
import Layout from '@/components/layout'
import { AuthGuard, PublicGuard } from '@/components/auth-guard'
import { CommandPalette } from '@/components/command-palette'
import { ErrorBoundary } from '@/components/error-boundary'
import { useKeyboardShortcuts } from '@/hooks/use-keyboard-shortcuts'
import Landing from '@/pages/landing'
import Login from '@/pages/login'

const Dashboard = lazy(() => import('@/pages/dashboard'))
const Analysis = lazy(() => import('@/pages/analysis'))
const Validation = lazy(() => import('@/pages/validation'))
const Retry = lazy(() => import('@/pages/retry'))
const Review = lazy(() => import('@/pages/review'))
const PR = lazy(() => import('@/pages/pr'))
const Indexing = lazy(() => import('@/pages/indexing'))
const Tasks = lazy(() => import('@/pages/tasks'))
const AdminKeys = lazy(() => import('@/pages/admin-keys'))

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      retry: 2,
    },
  },
})

function PageLoader() {
  return (
    <div className="flex h-full min-h-[60vh] items-center justify-center">
      <div className="h-8 w-8 animate-pulse rounded-full bg-muted-foreground/20" />
    </div>
  )
}

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
            <Route path="/dashboard" element={<Suspense fallback={<PageLoader />}><Dashboard /></Suspense>} />
            <Route path="/analysis" element={<Suspense fallback={<PageLoader />}><Analysis /></Suspense>} />
            <Route path="/validation" element={<Suspense fallback={<PageLoader />}><Validation /></Suspense>} />
            <Route path="/retry" element={<Suspense fallback={<PageLoader />}><Retry /></Suspense>} />
            <Route path="/review" element={<Suspense fallback={<PageLoader />}><Review /></Suspense>} />
            <Route path="/pr" element={<Suspense fallback={<PageLoader />}><PR /></Suspense>} />
            <Route path="/indexing" element={<Suspense fallback={<PageLoader />}><Indexing /></Suspense>} />
            <Route path="/tasks" element={<Suspense fallback={<PageLoader />}><Tasks /></Suspense>} />
            <Route path="/admin/keys" element={<Suspense fallback={<PageLoader />}><AdminKeys /></Suspense>} />
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
    <ErrorBoundary>
      <AnimatedRoutes />
      <CommandPalette open={paletteOpen} onClose={closePalette} />
    </ErrorBoundary>
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
