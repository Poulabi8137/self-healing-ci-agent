import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { AuthProvider } from '@/lib/auth'
import Landing from '@/pages/landing'

function renderLanding() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <MemoryRouter>
      <QueryClientProvider client={qc}>
        <AuthProvider>
          <Landing />
        </AuthProvider>
      </QueryClientProvider>
    </MemoryRouter>,
  )
}

describe('LandingPage', () => {
  it('renders the hero heading', () => {
    renderLanding()
    expect(screen.getByText(/Autonomous CI\/CD/)).toBeInTheDocument()
  })

  it('renders hero description', () => {
    renderLanding()
    expect(screen.getByText(/intelligent agent that analyzes/)).toBeInTheDocument()
  })

  it('renders Get Started button', () => {
    renderLanding()
    expect(screen.getByText('Get Started')).toBeInTheDocument()
  })

  it('renders Sign In button', () => {
    renderLanding()
    expect(screen.getByText('Sign In')).toBeInTheDocument()
  })

  it('renders Dark/Light toggle', () => {
    renderLanding()
    expect(screen.getByRole('button', { name: /switch/i })).toBeInTheDocument()
  })

  it('renders three feature cards', () => {
    renderLanding()
    expect(screen.getByText('Analyze')).toBeInTheDocument()
    expect(screen.getByText('Fix')).toBeInTheDocument()
    expect(screen.getByText('Deploy')).toBeInTheDocument()
  })

  it('has banner landmark', () => {
    renderLanding()
    expect(screen.getByRole('banner')).toBeInTheDocument()
  })

  it('has contentinfo landmark', () => {
    renderLanding()
    expect(screen.getByRole('contentinfo')).toBeInTheDocument()
  })
})
