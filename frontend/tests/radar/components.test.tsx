import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, within, fireEvent } from '@testing-library/react'

vi.mock('next/navigation', () => ({ usePathname: () => '/radar' }))

import { useRadarStore } from '@/stores/radar-store'
import { DEFAULT_FILTERS } from '@/lib/radar/filters'
import { SAMPLE_PROFILE, RADAR_OPPORTUNITIES } from '@/lib/radar/seed'
import { normalizeItem } from '@/lib/radar/normalize'
import { scoreOpportunity } from '@/lib/radar/match'
import { MatchCard } from '@/components/radar/match-card'
import { MatchesView } from '@/components/radar/matches-view'
import { BoardView } from '@/components/radar/board-view'
import { DeadlinesView } from '@/components/radar/deadlines-view'
import { RadarShell } from '@/components/radar/radar-shell'

function reset() {
  useRadarStore.setState({ profile: SAMPLE_PROFILE, customised: false, filters: DEFAULT_FILTERS, board: {} })
}

beforeEach(() => {
  // Pin "today" to the snapshot week so the seed's deadlines stay open in CI.
  vi.useFakeTimers({ toFake: ['Date'] })
  vi.setSystemTime(new Date('2026-11-03T06:00:00Z'))
  localStorage.clear()
  reset()
})

afterEach(() => {
  vi.useRealTimers()
})

const opp = normalizeItem({
  kind: 'hackathon',
  title: 'Chennai Build Night',
  organizer: 'Org',
  url: 'https://example.org/x',
  mode: 'online',
  city: 'Online',
  fee: 'free',
  deadline: '2026-11-05',
  event_dates: '',
  team: 'solo ok (1-4)',
  reward: 'Not stated',
  eligibility: 'Students',
  topics: 'Python, React',
  verified: true,
})

describe('MatchCard', () => {
  it('shows the score, why it fits, and actions', () => {
    const onTrack = vi.fn()
    const m = scoreOpportunity(SAMPLE_PROFILE, opp, '2026-11-03')
    render(<MatchCard match={m} asOf="2026-11-03" tracked={false} onTrack={onTrack} />)
    expect(screen.getByText(`Match score ${m.score} out of 100, ${m.label}`)).toBeInTheDocument()
    const why = screen.getByRole('list', { name: 'Why this fits' })
    expect(within(why).getByText(/Python and React/)).toBeInTheDocument()
    expect(screen.getByText('2 days left')).toBeInTheDocument()
    expect(screen.queryByText(/Not stated/)).not.toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Track' }))
    expect(onTrack).toHaveBeenCalled()
    expect(screen.getByRole('link', { name: /Organiser page/ })).toHaveAttribute('rel', 'noopener noreferrer')
  })

  it('shows tracked state as disabled', () => {
    const m = scoreOpportunity(SAMPLE_PROFILE, opp, '2026-11-03')
    render(<MatchCard match={m} asOf="2026-11-03" tracked onTrack={() => {}} />)
    expect(screen.getByRole('button', { name: /On your board/ })).toBeDisabled()
  })
})

describe('MatchesView', () => {
  it('ranks listings and re-ranks when the profile changes', () => {
    render(<MatchesView />)
    expect(screen.getByRole('heading', { name: 'Ranked for you' })).toBeInTheDocument()
    const firstBefore = screen.getAllByRole('article')[0].textContent
    fireEvent.click(screen.getAllByRole('button', { name: 'Blockchain' })[0])
    fireEvent.click(screen.getByRole('button', { name: 'Python' }))
    expect(useRadarStore.getState().customised).toBe(true)
    expect(useRadarStore.getState().profile.skills).toContain('Blockchain')
    expect(useRadarStore.getState().profile.skills).not.toContain('Python')
    expect(screen.getAllByRole('article')[0].textContent).not.toBe(firstBefore)
  })

  it('filters by kind and tracks to the board', () => {
    render(<MatchesView />)
    fireEvent.click(screen.getByRole('button', { name: 'Hackathons' }))
    for (const a of screen.getAllByRole('article')) expect(a.textContent).toContain('Internship')
    fireEvent.click(screen.getAllByRole('button', { name: 'Track' })[0])
    expect(Object.keys(useRadarStore.getState().board)).toHaveLength(1)
  })

  it('shows an empty state with a reset', () => {
    render(<MatchesView />)
    fireEvent.change(screen.getByLabelText('Search listings'), { target: { value: 'zzzz-nothing' } })
    expect(screen.getByText(/Nothing on the radar/)).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Reset filters' }))
    expect(useRadarStore.getState().filters.query).toBe('')
  })
})

describe('BoardView', () => {
  it('moves a card through the stages and removes it', () => {
    const id = RADAR_OPPORTUNITIES[0].id
    useRadarStore.getState().track(id)
    render(<BoardView />)
    const title = RADAR_OPPORTUNITIES[0].title
    fireEvent.click(screen.getByRole('button', { name: `Move ${title} forward to Preparing` }))
    expect(useRadarStore.getState().board[id].stage).toBe('preparing')
    fireEvent.change(screen.getByLabelText(`Note for ${title}`), { target: { value: 'ask Priya' } })
    expect(useRadarStore.getState().board[id].note).toBe('ask Priya')
    fireEvent.click(screen.getByRole('button', { name: `Remove ${title} from board` }))
    expect(useRadarStore.getState().board).toEqual({})
  })
})

describe('DeadlinesView', () => {
  it('renders the 4-week strip and calendar export buttons', () => {
    render(<DeadlinesView />)
    expect(screen.getByText('Next 4 weeks')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /My board \(0\)/ })).toBeDisabled()
    expect(screen.getByRole('button', { name: /to calendar/ })).toBeInTheDocument()
  })
})

describe('RadarShell', () => {
  it('marks the current tab and names the snapshot', () => {
    render(
      <RadarShell>
        <p>child</p>
      </RadarShell>,
    )
    expect(screen.getByRole('link', { name: 'Matches' })).toHaveAttribute('aria-current', 'page')
    expect(screen.getByText(/Demo snapshot of/)).toBeInTheDocument()
    expect(screen.getByText('child')).toBeInTheDocument()
  })
})

describe('radar store persistence', () => {
  it('writes profile and board to localStorage', async () => {
    await useRadarStore.persist.rehydrate()
    useRadarStore.getState().track('abc')
    useRadarStore.getState().setProfile({ year: 3 })
    const raw = JSON.parse(localStorage.getItem('opassist-radar-v1')!)
    expect(raw.state.board.abc.stage).toBe('shortlist')
    expect(raw.state.profile.year).toBe(3)
  })
})
