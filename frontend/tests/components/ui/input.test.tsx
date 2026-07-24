import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Input } from '@/components/ui/input'

describe('Input', () => {
  it('renders with placeholder', () => {
    render(<Input placeholder="Enter text" />)
    expect(screen.getByPlaceholderText('Enter text')).toBeInTheDocument()
  })

  it('accepts value changes', async () => {
    const user = userEvent.setup()
    render(<Input placeholder="Type here" />)
    const input = screen.getByPlaceholderText('Type here')
    await user.type(input, 'Hello')
    expect(input).toHaveValue('Hello')
  })

  it('renders disabled', () => {
    render(<Input disabled placeholder="Disabled" />)
    expect(screen.getByPlaceholderText('Disabled')).toBeDisabled()
  })

  it('applies className', () => {
    render(<Input className="custom-class" placeholder="Styled" />)
    expect(screen.getByPlaceholderText('Styled').className).toContain('custom-class')
  })

  it('forwards ref', () => {
    const ref = { current: null }
    render(<Input ref={ref} placeholder="Ref" />)
    expect(ref.current).toBeInstanceOf(HTMLInputElement)
  })
})
