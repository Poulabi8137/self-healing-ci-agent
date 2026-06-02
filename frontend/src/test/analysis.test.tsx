import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { AuthProvider } from '@/lib/auth'
import AnalysisPage from '@/pages/analysis'

function renderAnalysis() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <MemoryRouter>
      <QueryClientProvider client={qc}>
        <AuthProvider>
          <AnalysisPage />
        </AuthProvider>
      </QueryClientProvider>
    </MemoryRouter>,
  )
}

describe('AnalysisPage', () => {
  it('renders the heading', () => {
    renderAnalysis()
    expect(screen.getByText('Failure Analysis')).toBeInTheDocument()
  })

  it('renders the form with repo and logs inputs', () => {
    renderAnalysis()
    expect(screen.getByLabelText('Repository name')).toBeInTheDocument()
    expect(screen.getByLabelText('CI/CD Logs')).toBeInTheDocument()
  })

  it('shows empty state before analysis', () => {
    renderAnalysis()
    expect(screen.getByText('Results will appear here')).toBeInTheDocument()
  })

  it('has a form role with correct label', () => {
    renderAnalysis()
    expect(screen.getByRole('form', { name: 'Analysis input form' })).toBeInTheDocument()
  })

  it('renders the submit button', () => {
    renderAnalysis()
    expect(screen.getByText('Analyze & Generate Fix')).toBeInTheDocument()
  })
})
