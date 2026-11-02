import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { OpportunityCard } from '@/components/opportunity-card'

const NOW = new Date('2026-10-20T12:00:00Z')

describe('OpportunityCard', () => {
  beforeEach(() => {
    vi.useFakeTimers({ toFake: ['Date'] })
    vi.setSystemTime(NOW)
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('renders title, organizer, location and links to the detail page', () => {
    render(
      <OpportunityCard id="abc" title="CodeSprint" type="hackathon" organizer="IIT Example" location="Remote" />
    )
    expect(screen.getByRole('heading', { name: 'CodeSprint' })).toBeInTheDocument()
    expect(screen.getByText('IIT Example')).toBeInTheDocument()
    expect(screen.getByText('Remote')).toBeInTheDocument()
    expect(screen.getByRole('link')).toHaveAttribute('href', '/opportunities/abc')
  })

  it.each([
    ['hackathon', 'Rs. 50,000', 'Rs. 50,000'],
    ['internship', '10k/month', 'Stipend: 10k/month'],
    ['job', '6 LPA', 'Salary: 6 LPA'],
    ['scholarship', 'Full tuition', 'Full tuition'],
  ])('labels the prize for type %s', (type, prize, expected) => {
    render(<OpportunityCard id="1" title="T" type={type} prize={prize} />)
    expect(screen.getByText(expected)).toBeInTheDocument()
  })

  it('shows days left and marks a near deadline as urgent', () => {
    render(<OpportunityCard id="1" title="T" type="job" deadline="2026-10-22T12:00:00Z" />)
    const left = screen.getByText('(2d left)')
    expect(left).toBeInTheDocument()
    expect(left.parentElement).toHaveClass('text-red-400')
  })

  it('does not show a negative countdown for a passed deadline', () => {
    render(<OpportunityCard id="1" title="T" type="job" deadline="2026-10-01T00:00:00Z" />)
    expect(screen.queryByText(/d left\)/)).not.toBeInTheDocument()
  })

  it('shows at most four tags plus an overflow count', () => {
    render(<OpportunityCard id="1" title="T" type="job" tags={['a', 'b', 'c', 'd', 'e', 'f']} />)
    for (const t of ['a', 'b', 'c', 'd']) expect(screen.getByText(t)).toBeInTheDocument()
    expect(screen.queryByText('e')).not.toBeInTheDocument()
    expect(screen.getByText('+2')).toBeInTheDocument()
  })

  it('only renders the bookmark button when a handler is given, and calls it', async () => {
    vi.useRealTimers()
    const onBookmark = vi.fn()
    const { rerender } = render(<OpportunityCard id="1" title="T" type="job" />)
    expect(screen.queryByRole('button')).not.toBeInTheDocument()

    rerender(<OpportunityCard id="1" title="T" type="job" onBookmark={onBookmark} />)
    await userEvent.click(screen.getByRole('button', { name: /bookmark/i }))
    expect(onBookmark).toHaveBeenCalledTimes(1)
  })

  it('reflects bookmarked state for assistive tech', () => {
    render(<OpportunityCard id="1" title="T" type="job" onBookmark={() => {}} isBookmarked />)
    expect(screen.getByRole('button', { name: /remove bookmark/i })).toHaveAttribute('aria-pressed', 'true')
  })
})
