import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ActivityFeed } from '@/components/activity-feed'

describe('ActivityFeed', () => {
  it('renders the heading', () => {
    render(<ActivityFeed />)
    expect(screen.getByText('Activity Feed')).toBeInTheDocument()
  })

  it('renders LIVE toggle', () => {
    render(<ActivityFeed />)
    expect(screen.getByText('LIVE')).toBeInTheDocument()
  })

  it('has feed role', () => {
    render(<ActivityFeed />)
    expect(screen.getByRole('feed')).toBeInTheDocument()
  })

  it('has polite aria-live', () => {
    render(<ActivityFeed />)
    expect(screen.getByRole('feed')).toHaveAttribute('aria-live', 'polite')
  })
})
