import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Badge } from '@/components/ui/badge'

describe('Badge', () => {
  it('renders with text', () => {
    render(<Badge>New</Badge>)
    expect(screen.getByText('New')).toBeInTheDocument()
  })

  it('renders with default variant', () => {
    render(<Badge>Default</Badge>)
    expect(screen.getByText('Default').className).toContain('bg-primary/15')
  })

  it('renders with secondary variant', () => {
    render(<Badge variant="secondary">Secondary</Badge>)
    expect(screen.getByText('Secondary').className).toContain('bg-secondary')
  })

  it('renders with destructive variant', () => {
    render(<Badge variant="destructive">Destructive</Badge>)
    expect(screen.getByText('Destructive').className).toContain('bg-destructive')
  })

  it('renders with outline variant', () => {
    render(<Badge variant="outline">Outline</Badge>)
    expect(screen.getByText('Outline').className).toContain('border-border')
  })

  it('renders with success variant', () => {
    render(<Badge variant="success">Success</Badge>)
    expect(screen.getByText('Success').className).toContain('bg-success')
  })

  it('renders with warning variant', () => {
    render(<Badge variant="warning">Warning</Badge>)
    expect(screen.getByText('Warning').className).toContain('bg-warning')
  })

  it('applies additional className', () => {
    render(<Badge className="custom">Styled</Badge>)
    expect(screen.getByText('Styled').className).toContain('custom')
  })
})
