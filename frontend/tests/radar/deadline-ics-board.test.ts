import { describe, it, expect } from 'vitest'
import { bucketFor, countdownLabel, daysUntil, deadlineStrip, formatDate, groupByBucket, todayIST } from '@/lib/radar/deadline'
import { buildIcs, escapeText, foldLine } from '@/lib/radar/ics'
import { addCard, columns, moveCard, removeCard, setNote, stepCard, type Board } from '@/lib/radar/board'
import { normalizeItem } from '@/lib/radar/normalize'
import type { SeedItem } from '@/lib/radar/types'

const item: SeedItem = {
  kind: 'hackathon',
  title: 'Shaastra Contest, Finals; IIT Madras',
  organizer: 'IIT Madras',
  url: 'https://example.org/shaastra',
  mode: 'hybrid',
  city: 'Chennai',
  fee: 'free',
  deadline: '2026-11-10',
  event_dates: 'Jan 2027',
  team: 'solo (1)',
  reward: 'INR 1,30,000',
  eligibility: 'Students',
  topics: 'DSA',
  verified: true,
}

describe('deadline maths', () => {
  it('counts whole days across month boundaries', () => {
    expect(daysUntil('2026-12-01', '2026-11-30')).toBe(1)
    expect(daysUntil('2026-11-03', '2026-11-03')).toBe(0)
    expect(daysUntil('2026-11-01', '2026-11-03')).toBe(-2)
  })
  it('buckets deadlines', () => {
    expect(bucketFor(null, '2026-11-03')).toBe('rolling')
    expect(bucketFor('2026-11-02', '2026-11-03')).toBe('closed')
    expect(bucketFor('2026-11-03', '2026-11-03')).toBe('today')
    expect(bucketFor('2026-11-10', '2026-11-03')).toBe('this-week')
    expect(bucketFor('2026-11-24', '2026-11-03')).toBe('next-two-weeks')
    expect(bucketFor('2026-11-25', '2026-11-03')).toBe('later')
  })
  it('labels countdowns', () => {
    expect(countdownLabel(null, '2026-11-03')).toBe('Rolling')
    expect(countdownLabel('2026-11-04', '2026-11-03')).toBe('1 day left')
    expect(countdownLabel('2026-11-13', '2026-11-03')).toBe('10 days left')
    expect(countdownLabel('2026-11-01', '2026-11-03')).toBe('Closed')
  })
  it('uses the IST calendar date', () => {
    // 20:00 UTC on 2 Nov is 01:30 IST on 3 Nov.
    expect(todayIST(new Date('2026-11-02T20:00:00Z'))).toBe('2026-11-03')
  })
  it('formats dates without timezone drift', () => {
    expect(formatDate('2026-11-10')).toMatch(/10/)
    expect(formatDate('2026-11-10')).toMatch(/Nov/)
  })
  it('groups and sorts by bucket', () => {
    const g = groupByBucket([{ deadline: '2026-11-09' }, { deadline: '2026-11-05' }, { deadline: null }], '2026-11-03')
    expect(g['this-week'].map((x) => x.deadline)).toEqual(['2026-11-05', '2026-11-09'])
    expect(g.rolling).toHaveLength(1)
  })
  it('builds a day strip', () => {
    const strip = deadlineStrip([{ deadline: '2026-11-05' }], '2026-11-03', 7)
    expect(strip).toHaveLength(7)
    expect(strip[0].date).toBe('2026-11-03')
    expect(strip[2].items).toHaveLength(1)
  })
})

describe('ics export', () => {
  const opp = normalizeItem(item)
  const ics = buildIcs([opp, normalizeItem({ ...item, title: 'Rolling', deadline: null })], new Date('2026-11-03T00:00:00Z'))

  it('is a valid calendar with CRLF line endings', () => {
    expect(ics.startsWith('BEGIN:VCALENDAR\r\n')).toBe(true)
    expect(ics.endsWith('END:VCALENDAR\r\n')).toBe(true)
    expect(ics.replace(/\r\n/g, '')).not.toMatch(/\n/)
  })
  it('writes an all-day event on the deadline with reminders', () => {
    expect(ics).toContain('DTSTART;VALUE=DATE:20261110')
    expect(ics).toContain('DTEND;VALUE=DATE:20261111')
    expect(ics).toContain('TRIGGER:-P3D')
    expect(ics).toContain('TRIGGER:-P1D')
    expect(ics).toContain('DTSTAMP:20261103T000000Z')
  })
  it('skips rolling deadlines', () => {
    expect(ics.match(/BEGIN:VEVENT/g)).toHaveLength(1)
  })
  it('escapes commas and semicolons in text', () => {
    expect(ics.replace(/\r\n /g, '')).toContain('SUMMARY:Registration close: Shaastra Contest\\, Finals\\; IIT Madras')
    expect(escapeText('a\\b\nc')).toBe('a\\\\b\\nc')
  })
  it('folds long lines to 75 octets', () => {
    for (const line of ics.split('\r\n')) expect(new TextEncoder().encode(line).length).toBeLessThanOrEqual(75)
    const folded = foldLine('X'.repeat(200))
    expect(folded.split('\r\n ').join('')).toBe('X'.repeat(200))
  })
  it('does not split multi-byte characters when folding', () => {
    const s = 'DESCRIPTION:' + '₹'.repeat(60)
    const parts = foldLine(s).split('\r\n ')
    expect(parts.join('')).toBe(s)
  })
})

describe('tracker board', () => {
  const now = new Date('2026-11-03T00:00:00Z')
  it('adds once, moves, steps and removes', () => {
    let b: Board = {}
    b = addCard(b, 'x', now)
    expect(addCard(b, 'x', now)).toBe(b)
    expect(b.x.stage).toBe('shortlist')
    b = stepCard(b, 'x', 1)
    expect(b.x.stage).toBe('preparing')
    b = moveCard(b, 'x', 'result')
    b = stepCard(b, 'x', 1)
    expect(b.x.stage).toBe('result')
    b = stepCard(b, 'x', -1)
    expect(b.x.stage).toBe('applied')
    b = removeCard(b, 'x')
    expect(b).toEqual({})
  })
  it('caps notes and ignores unknown ids', () => {
    let b = addCard({}, 'y', now)
    b = setNote(b, 'y', 'n'.repeat(500))
    expect(b.y.note).toHaveLength(280)
    expect(setNote(b, 'nope', 'z')).toBe(b)
    expect(moveCard(b, 'nope', 'applied')).toBe(b)
  })
  it('groups cards into columns in the order they were added', () => {
    let b = addCard({}, 'a', new Date('2026-11-03T01:00:00Z'))
    b = addCard(b, 'b', new Date('2026-11-03T00:00:00Z'))
    b = moveCard(b, 'a', 'applied')
    b = addCard(b, 'c', new Date('2026-11-03T02:00:00Z'))
    const cols = columns(b)
    expect(cols.shortlist.map((c) => c.id)).toEqual(['b', 'c'])
    expect(cols.applied.map((c) => c.id)).toEqual(['a'])
  })
})
