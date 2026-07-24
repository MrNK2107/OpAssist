import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card'

describe('Card', () => {
  it('renders children', () => {
    render(<Card><div>Content</div></Card>)
    expect(screen.getByText('Content')).toBeInTheDocument()
  })

  it('has correct base class', () => {
    render(<Card>Card</Card>)
    expect(screen.getByText('Card').className).toContain('rounded-xl')
  })

  it('applies additional className', () => {
    render(<Card className="custom">Custom</Card>)
    expect(screen.getByText('Custom').className).toContain('custom')
  })
})

describe('CardHeader', () => {
  it('renders children', () => {
    render(<CardHeader><h3>Header</h3></CardHeader>)
    expect(screen.getByText('Header')).toBeInTheDocument()
  })
})

describe('CardTitle', () => {
  it('renders title text', () => {
    render(<CardTitle>My Title</CardTitle>)
    expect(screen.getByText('My Title')).toBeInTheDocument()
  })

  it('renders as h3', () => {
    render(<CardTitle>Semantic</CardTitle>)
    expect(screen.getByRole('heading', { level: 3 })).toBeInTheDocument()
  })
})

describe('CardDescription', () => {
  it('renders description text', () => {
    render(<CardDescription>Some description</CardDescription>)
    expect(screen.getByText('Some description')).toBeInTheDocument()
  })
})

describe('CardContent', () => {
  it('renders children', () => {
    render(<CardContent><p>Content area</p></CardContent>)
    expect(screen.getByText('Content area')).toBeInTheDocument()
  })
})

describe('CardFooter', () => {
  it('renders children', () => {
    render(<CardFooter><button>Action</button></CardFooter>)
    expect(screen.getByRole('button')).toHaveTextContent('Action')
  })
})
