import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { AuthProvider } from '@/lib/auth'
import { AgentProvider } from '@/lib/agent-context'
import ValidationPage from '@/pages/validation'

function renderValidation() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <MemoryRouter>
      <QueryClientProvider client={qc}>
        <AuthProvider>
          <AgentProvider>
            <ValidationPage />
          </AgentProvider>
        </AuthProvider>
      </QueryClientProvider>
    </MemoryRouter>,
  )
}

describe('ValidationPage', () => {
  it('renders the heading', () => {
    renderValidation()
    expect(screen.getByText('Fix Validation')).toBeInTheDocument()
  })

  it('renders the form with repo and logs inputs', () => {
    renderValidation()
    expect(screen.getByLabelText('Repository name')).toBeInTheDocument()
    expect(screen.getByLabelText('CI/CD Logs')).toBeInTheDocument()
  })

  it('shows empty state before validation', () => {
    renderValidation()
    expect(screen.getByText('Load example data or submit logs to run validation')).toBeInTheDocument()
  })

  it('has a form role with correct label', () => {
    renderValidation()
    expect(screen.getByRole('form', { name: 'Validation input form' })).toBeInTheDocument()
  })

  it('renders the submit button', () => {
    renderValidation()
    expect(screen.getByText('Run Validation Pipeline')).toBeInTheDocument()
  })
})
