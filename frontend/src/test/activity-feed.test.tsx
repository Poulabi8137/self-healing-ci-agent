import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { ActivityFeed } from '@/components/activity-feed'

function renderWithRouter(ui: React.ReactElement) {
  return render(<MemoryRouter>{ui}</MemoryRouter>)
}

describe('ActivityFeed', () => {
  it('renders the heading', () => {
    renderWithRouter(<ActivityFeed />)
    expect(screen.getByText('Activity')).toBeInTheDocument()
  })

  it('has feed role', () => {
    renderWithRouter(<ActivityFeed />)
    expect(screen.getByRole('feed')).toBeInTheDocument()
  })

  it('has feed aria-label', () => {
    renderWithRouter(<ActivityFeed />)
    expect(screen.getByRole('feed')).toHaveAttribute('aria-label', 'Activity feed')
  })
})
