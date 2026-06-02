import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { AuthProvider } from '@/lib/auth'
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
        <BrowserRouter>
          <Dashboard />
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>,
  )
}

describe('Dashboard page', () => {
  it('renders the heading', () => {
    renderDashboard()
    expect(screen.getByText('Dashboard')).toBeInTheDocument()
  })

  it('renders dashboard tabs', () => {
    renderDashboard()
    expect(screen.getByText('System Overview')).toBeInTheDocument()
    expect(screen.getByText('Repository Analytics')).toBeInTheDocument()
    expect(screen.getByText('Retry Analytics')).toBeInTheDocument()
    expect(screen.getByText('Validation Analytics')).toBeInTheDocument()
    expect(screen.getByText('Review Analytics')).toBeInTheDocument()
    expect(screen.getByText('PR Analytics')).toBeInTheDocument()
  })
})
