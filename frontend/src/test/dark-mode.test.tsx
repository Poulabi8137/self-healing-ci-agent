import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { AuthProvider } from '@/lib/auth'
import { DarkModeToggle } from '@/components/dark-mode'

function renderDarkMode() {
  return render(
    <AuthProvider>
      <DarkModeToggle />
    </AuthProvider>,
  )
}

describe('DarkModeToggle', () => {
  it('renders the toggle button', () => {
    renderDarkMode()
    expect(screen.getByRole('button', { name: /switch/i })).toBeInTheDocument()
  })

  it('toggles label on click', async () => {
    const user = userEvent.setup()
    renderDarkMode()
    const btn = screen.getByRole('button', { name: /switch/i })
    const initialLabel = btn.getAttribute('aria-label')
    await user.click(btn)
    const afterLabel = btn.getAttribute('aria-label')
    expect(afterLabel).not.toBe(initialLabel)
  })
})
