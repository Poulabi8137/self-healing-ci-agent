import { Navigate } from 'react-router-dom'
import { useAuth, LoginForm } from '../lib/auth'

export default function LoginPage() {
  const { isAuthenticated } = useAuth()

  if (isAuthenticated) {
    return <Navigate to="/" replace />
  }

  return (
    <main role="main" aria-label="Login page">
      <h1>Self-Healing CI Agent</h1>
      <p>Enter your API key to access the dashboard.</p>
      <LoginForm />
    </main>
  )
}
