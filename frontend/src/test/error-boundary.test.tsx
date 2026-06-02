import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Component, type ReactNode } from 'react'
import { ErrorBoundary } from '@/components/error-boundary'

class BrokenComponent extends Component<Record<string, never>> {
  render(): ReactNode {
    throw new Error('Test error from broken component')
  }
}

describe('ErrorBoundary', () => {
  it('renders children when no error', () => {
    render(
      <ErrorBoundary>
        <div data-testid="child">OK</div>
      </ErrorBoundary>,
    )
    expect(screen.getByTestId('child')).toHaveTextContent('OK')
  })

  it('catches errors and shows fallback', () => {
    vi.spyOn(console, 'error').mockImplementation(() => {})
    render(
      <ErrorBoundary>
        <BrokenComponent />
      </ErrorBoundary>,
    )
    expect(screen.getByText('Unexpected error')).toBeInTheDocument()
    expect(screen.getByText(/Test error from broken component/)).toBeInTheDocument()
    expect(screen.getByRole('alert')).toBeInTheDocument()
    ;(console.error as unknown as ReturnType<typeof vi.spyOn>).mockRestore()
  })

  it('renders custom fallback when provided', () => {
    vi.spyOn(console, 'error').mockImplementation(() => {})
    render(
      <ErrorBoundary fallback={<div data-testid="custom">Custom error UI</div>}>
        <BrokenComponent />
      </ErrorBoundary>,
    )
    expect(screen.getByTestId('custom')).toHaveTextContent('Custom error UI')
    ;(console.error as unknown as ReturnType<typeof vi.spyOn>).mockRestore()
  })

  it('renders a reload button in the fallback', () => {
    vi.spyOn(console, 'error').mockImplementation(() => {})
    render(
      <ErrorBoundary>
        <BrokenComponent />
      </ErrorBoundary>,
    )
    expect(screen.getByText('Reload page')).toBeInTheDocument()
    ;(console.error as unknown as ReturnType<typeof vi.spyOn>).mockRestore()
  })
})
