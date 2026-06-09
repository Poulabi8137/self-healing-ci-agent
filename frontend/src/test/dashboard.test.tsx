import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { AuthProvider } from '@/lib/auth'
import { AgentProvider } from '@/lib/agent-context'
import Dashboard from '@/pages/dashboard'

function renderDashboard() {
  const qc = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  })
  return render(
    <QueryClientProvider client={qc}>
      <AuthProvider>
        <AgentProvider>
          <BrowserRouter>
            <Dashboard />
          </BrowserRouter>
        </AgentProvider>
      </AuthProvider>
    </QueryClientProvider>,
  )
}

describe('Dashboard page', () => {
  it('renders the heading', () => {
    renderDashboard()
    expect(screen.getByRole('heading', { name: 'Overview' })).toBeInTheDocument()
  })

  it('renders dashboard tabs', () => {
    renderDashboard()
    expect(screen.getByRole('tab', { name: 'Overview' })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: 'Repositories' })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: 'Recovery' })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: 'Validation' })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: 'Health' })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: 'Pull Requests' })).toBeInTheDocument()
  })
})
