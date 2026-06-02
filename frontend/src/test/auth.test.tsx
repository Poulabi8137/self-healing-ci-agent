import { describe, it, expect, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { AuthProvider } from '@/lib/auth'
import { useAuth } from '@/lib/auth-context'

function TestConsumer() {
  const { isAuthenticated, role, apiKey, login, logout } = useAuth()
  return (
    <div>
      <span data-testid="authenticated">{String(isAuthenticated)}</span>
      <span data-testid="role">{role ?? 'none'}</span>
      <span data-testid="apiKey">{apiKey ?? 'none'}</span>
      <button data-testid="login-admin" onClick={() => login('admin-token')}>Login Admin</button>
      <button data-testid="login-candidate" onClick={() => login('candidate-token')}>Login Candidate</button>
      <button data-testid="logout" onClick={logout}>Logout</button>
    </div>
  )
}

function renderWithAuth() {
  return render(
    <AuthProvider>
      <TestConsumer />
    </AuthProvider>,
  )
}

beforeEach(() => {
  sessionStorage.clear()
})

describe('AuthProvider', () => {
  it('starts unauthenticated with no stored key', () => {
    renderWithAuth()
    expect(screen.getByTestId('authenticated')).toHaveTextContent('false')
    expect(screen.getByTestId('role')).toHaveTextContent('none')
    expect(screen.getByTestId('apiKey')).toHaveTextContent('none')
  })

  it('reads an existing key from sessionStorage on mount', () => {
    sessionStorage.setItem('ci_agent_api_key', 'stored-key')
    renderWithAuth()
    expect(screen.getByTestId('authenticated')).toHaveTextContent('true')
  })

  it('updates state after login', async () => {
    const user = userEvent.setup()
    renderWithAuth()
    await user.click(screen.getByTestId('login-admin'))
    expect(screen.getByTestId('authenticated')).toHaveTextContent('true')
    expect(screen.getByTestId('apiKey')).not.toHaveTextContent('none')
  })

  it('clears state after logout', async () => {
    const user = userEvent.setup()
    renderWithAuth()
    await user.click(screen.getByTestId('login-admin'))
    expect(screen.getByTestId('authenticated')).toHaveTextContent('true')
    await user.click(screen.getByTestId('logout'))
    expect(screen.getByTestId('authenticated')).toHaveTextContent('false')
    expect(screen.getByTestId('apiKey')).toHaveTextContent('none')
  })

  it('stores the key in sessionStorage on login', async () => {
    const user = userEvent.setup()
    renderWithAuth()
    await user.click(screen.getByTestId('login-admin'))
    expect(sessionStorage.getItem('ci_agent_api_key')).toBe('admin-token')
  })

  it('removes the key from sessionStorage on logout', async () => {
    const user = userEvent.setup()
    renderWithAuth()
    await user.click(screen.getByTestId('login-admin'))
    expect(sessionStorage.getItem('ci_agent_api_key')).toBe('admin-token')
    await user.click(screen.getByTestId('logout'))
    expect(sessionStorage.getItem('ci_agent_api_key')).toBeNull()
  })
})
