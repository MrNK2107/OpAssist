import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Button } from '@/components/ui/button'

describe('Button', () => {
  it('renders with text', () => {
    render(<Button>Click me</Button>)
    expect(screen.getByRole('button')).toHaveTextContent('Click me')
  })

  it('renders with default variant class', () => {
    render(<Button>Default</Button>)
    const button = screen.getByRole('button')
    expect(button.className).toContain('bg-gradient-to-br')
  })

  it('renders with outline variant', () => {
    render(<Button variant="outline">Outline</Button>)
    const button = screen.getByRole('button')
    expect(button.className).toContain('border-border')
  })

  it('renders with destructive variant', () => {
    render(<Button variant="destructive">Destructive</Button>)
    const button = screen.getByRole('button')
    expect(button.className).toContain('bg-destructive')
  })

  it('renders with ghost variant', () => {
    render(<Button variant="ghost">Ghost</Button>)
    const button = screen.getByRole('button')
    expect(button.className).toContain('hover:bg-accent')
  })

  it('renders with link variant', () => {
    render(<Button variant="link">Link</Button>)
    const button = screen.getByRole('button')
    expect(button.className).toContain('underline-offset-4')
  })

  it('renders with gradient variant', () => {
    render(<Button variant="gradient">Gradient</Button>)
    const button = screen.getByRole('button')
    expect(button.className).toContain('from-amber-500')
  })

  it('renders with different sizes', () => {
    render(<Button size="sm">Small</Button>)
    expect(screen.getByRole('button').className).toContain('h-8')

    render(<Button size="lg">Large</Button>)
    const buttons = screen.getAllByRole('button')
    expect(buttons[1].className).toContain('h-11')
  })

  it('calls onClick when clicked', async () => {
    const handleClick = vi.fn()
    render(<Button onClick={handleClick}>Click</Button>)
    await userEvent.click(screen.getByRole('button'))
    expect(handleClick).toHaveBeenCalledTimes(1)
  })

  it('is disabled when disabled prop is true', () => {
    render(<Button disabled>Disabled</Button>)
    expect(screen.getByRole('button')).toBeDisabled()
  })

  it('does not call onClick when disabled', async () => {
    const handleClick = vi.fn()
    render(<Button disabled onClick={handleClick}>Disabled</Button>)
    await userEvent.click(screen.getByRole('button'))
    expect(handleClick).not.toHaveBeenCalled()
  })

  it('renders as icon size', () => {
    render(<Button size="icon">+</Button>)
    expect(screen.getByRole('button').className).toContain('w-9')
  })

  it('renders as icon-lg size', () => {
    render(<Button size="icon-lg">+</Button>)
    expect(screen.getByRole('button').className).toContain('w-11')
  })

  it('applies additional className', () => {
    render(<Button className="extra-class">Styled</Button>)
    expect(screen.getByRole('button').className).toContain('extra-class')
  })

  it('forwards ref', () => {
    const ref = { current: null }
    render(<Button ref={ref}>Ref</Button>)
    expect(ref.current).toBeInstanceOf(HTMLButtonElement)
  })
})
