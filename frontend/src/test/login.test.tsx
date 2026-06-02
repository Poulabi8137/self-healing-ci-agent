import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { AuthProvider } from '@/lib/auth'
import LoginPage from '@/pages/login'

function renderLogin() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <MemoryRouter>
      <QueryClientProvider client={qc}>
        <AuthProvider>
          <LoginPage />
        </AuthProvider>
      </QueryClientProvider>
    </MemoryRouter>,
  )
}

describe('LoginPage', () => {
  it('renders the login heading', () => {
    renderLogin()
    expect(screen.getByText('Self-Healing CI Agent')).toBeInTheDocument()
  })

  it('renders the login form', () => {
    renderLogin()
    expect(screen.getByPlaceholderText('Enter your API key')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /log in/i })).toBeInTheDocument()
  })

  it('shows an error when submitting with empty key', async () => {
    const user = userEvent.setup()
    renderLogin()
    await user.click(screen.getByRole('button', { name: /log in/i }))
    expect(screen.getByText('API key is required')).toBeInTheDocument()
  })

  it('has main landmark with correct label', () => {
    renderLogin()
    expect(screen.getByRole('main', { name: 'Login page' })).toBeInTheDocument()
  })

  it('has a form role with correct label', () => {
    renderLogin()
    expect(screen.getByRole('form', { name: 'Login form' })).toBeInTheDocument()
  })
})
