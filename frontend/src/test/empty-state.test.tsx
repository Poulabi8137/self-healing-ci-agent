import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { EmptyState } from '@/components/empty-state'
import { Activity } from 'lucide-react'

describe('EmptyState', () => {
  it('renders title and description', () => {
    render(<EmptyState icon={Activity} title="No items" description="Nothing to show" />)
    expect(screen.getByText('No items')).toBeInTheDocument()
    expect(screen.getByText('Nothing to show')).toBeInTheDocument()
  })

  it('renders action button when provided', () => {
    render(
      <EmptyState
        icon={Activity}
        title="No items"
        description="Nothing to show"
        action={{ label: 'Retry', onClick: () => {} }}
      />,
    )
    expect(screen.getByText('Retry')).toBeInTheDocument()
  })
})
