import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { AuthProvider } from '@/lib/auth'
import { CommandPalette } from '@/components/command-palette'

function renderPalette(open: boolean, onClose = vi.fn()) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <AuthProvider>
        <BrowserRouter>
          <CommandPalette open={open} onClose={onClose} />
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>,
  )
}

describe('CommandPalette', () => {
  it('does not render when closed', () => {
    renderPalette(false)
    expect(screen.queryByPlaceholderText(/search/i)).not.toBeInTheDocument()
  })

  it('renders when open', () => {
    renderPalette(true)
    expect(screen.getByPlaceholderText(/search/i)).toBeInTheDocument()
  })

  it('shows dialog role and aria-modal', () => {
    renderPalette(true)
    expect(screen.getByRole('dialog')).toHaveAttribute('aria-modal', 'true')
  })

  it('filters commands based on query', async () => {
    const user = userEvent.setup()
    renderPalette(true)
    const input = screen.getByPlaceholderText(/search/i)
    await user.type(input, 'Dashboard')
    expect(screen.getByText('Dashboard')).toBeInTheDocument()
    expect(screen.queryByText('Analysis')).not.toBeInTheDocument()
  })

  it('calls onClose when Escape is pressed', async () => {
    const onClose = vi.fn()
    const user = userEvent.setup()
    renderPalette(true, onClose)
    await user.keyboard('{Escape}')
    expect(onClose).toHaveBeenCalledTimes(1)
  })

  it('closes when backdrop is clicked', async () => {
    const onClose = vi.fn()
    const user = userEvent.setup()
    renderPalette(true, onClose)
    const backdrop = screen.getByRole('dialog')
    await user.click(backdrop)
    expect(onClose).toHaveBeenCalledTimes(1)
  })
})
