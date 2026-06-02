import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { AuthProvider } from '@/lib/auth'
import { AuthGuard } from '@/components/auth-guard'

function renderWithProviders(ui: React.ReactElement, { initialEntries = ['/'] } = {}) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <MemoryRouter initialEntries={initialEntries}>
      <QueryClientProvider client={qc}>
        <AuthProvider>
          {ui}
        </AuthProvider>
      </QueryClientProvider>
    </MemoryRouter>,
  )
}

describe('AuthGuard', () => {
  it('renders child route when authenticated', () => {
    sessionStorage.setItem('ci_agent_api_key', 'some-key')
    renderWithProviders(
      <Routes>
        <Route element={<AuthGuard />}>
          <Route path="/" element={<div data-testid="protected">Protected content</div>} />
        </Route>
      </Routes>,
    )
    expect(screen.getByTestId('protected')).toHaveTextContent('Protected content')
    sessionStorage.clear()
  })

  it('renders nothing when not authenticated', () => {
    renderWithProviders(
      <Routes>
        <Route element={<AuthGuard />}>
          <Route path="/" element={<div data-testid="protected">Protected content</div>} />
        </Route>
      </Routes>,
    )
    expect(screen.queryByTestId('protected')).not.toBeInTheDocument()
  })
})
