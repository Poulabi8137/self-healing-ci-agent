import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ErrorBanner } from '@/components/error-banner'

describe('ErrorBanner', () => {
  it('renders the message', () => {
    render(<ErrorBanner message="Something went wrong" />)
    expect(screen.getByText('Something went wrong')).toBeInTheDocument()
  })

  it('has alert role', () => {
    render(<ErrorBanner message="Error!" />)
    expect(screen.getByRole('alert')).toBeInTheDocument()
  })

  it('renders retry button when onRetry provided', () => {
    const onRetry = vi.fn()
    render(<ErrorBanner message="Error!" onRetry={onRetry} />)
    expect(screen.getByText('Try Again')).toBeInTheDocument()
  })

  it('calls onRetry when clicked', async () => {
    const onRetry = vi.fn()
    const user = userEvent.setup()
    render(<ErrorBanner message="Error!" onRetry={onRetry} />)
    await user.click(screen.getByText('Try Again'))
    expect(onRetry).toHaveBeenCalledTimes(1)
  })
})
