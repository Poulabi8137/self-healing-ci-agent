import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { StatusBadge } from '@/components/status-badge'

describe('StatusBadge', () => {
  it('renders passed status', () => {
    render(<StatusBadge status="passed" animated={false} />)
    expect(screen.getByText('Passed')).toBeInTheDocument()
    expect(screen.getByRole('status')).toHaveAttribute('aria-label', 'Status: Passed')
  })

  it('renders failed status', () => {
    render(<StatusBadge status="failed" animated={false} />)
    expect(screen.getByText('Failed')).toBeInTheDocument()
  })

  it('renders running status', () => {
    render(<StatusBadge status="running" animated={false} />)
    expect(screen.getByText('Running')).toBeInTheDocument()
  })

  it('renders unknown for unrecognized status', () => {
    render(<StatusBadge status="bogus" animated={false} />)
    expect(screen.getByText('Unknown')).toBeInTheDocument()
  })
})
