import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { PageTransition } from '@/components/page-transition'

describe('PageTransition', () => {
  it('renders children', () => {
    render(
      <PageTransition>
        <div data-testid="content">Hello</div>
      </PageTransition>,
    )
    expect(screen.getByTestId('content')).toHaveTextContent('Hello')
  })
})
