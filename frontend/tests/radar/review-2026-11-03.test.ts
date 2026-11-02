import { describe, it, expect } from 'vitest'
import { buildIcs, escapeText, exportableDeadlines } from '@/lib/radar/ics'
import { normalizeItem, safeHttpsUrl } from '@/lib/radar/normalize'
import { rankOpportunities, scoreOpportunity, STALE_AFTER_DAYS } from '@/lib/radar/match'
import type { SeedItem, StudentProfile } from '@/lib/radar/types'

const item: SeedItem = {
  kind: 'hackathon',
  title: 'Shaastra Contest',
  organizer: 'IIT Madras',
  url: 'https://example.org/shaastra',
  mode: 'online',
  city: 'Online',
  fee: 'free',
  deadline: '2026-11-10',
  event_dates: '',
  team: 'solo ok (1-4)',
  reward: '',
  eligibility: 'Students',
  topics: 'Python',
  verified: true,
}
const NOW = new Date('2026-11-03T00:00:00Z')
const unfold = (s: string) => s.replace(/\r\n /g, '')

describe('ics: stable identity and revision fields', () => {
  it('keeps the UID when the deadline moves, and bumps SEQUENCE with the snapshot', () => {
    const a = buildIcs([normalizeItem(item)], NOW, 'x', '2026-11-02')
    const b = buildIcs([normalizeItem({ ...item, deadline: '2026-11-20' })], NOW, 'x', '2026-11-09')
    const uid = (s: string) => s.match(/^UID:(.*)$/m)![1]
    expect(uid(a)).toBe(uid(b))
    expect(uid(a)).toBe(`${normalizeItem(item).id}@opassist`)
    const seq = (s: string) => Number(s.match(/^SEQUENCE:(\d+)$/m)![1])
    expect(seq(b)).toBeGreaterThan(seq(a))
    expect(a).toMatch(/^LAST-MODIFIED:20261102T000000Z$/m)
  })
})

describe('ics: CR/LF injection', () => {
  it('escapes lone CR as well as LF and CRLF', () => {
    expect(escapeText('a\rb')).toBe('a\\nb')
    expect(escapeText('a\r\nb\nc')).toBe('a\\nb\\nc')
    expect(escapeText('a\rb')).not.toMatch(/\r/)
  })

  const crafted = 'https://evil.example/\r\nATTENDEE:mailto:victim@example.com\r\nX-INJECT:1'

  it('drops a crafted CRLF url before it reaches the calendar', () => {
    const opp = normalizeItem({ ...item, url: crafted })
    expect(opp.url).not.toMatch(/[\r\n]/)
    const ics = buildIcs([opp], NOW)
    expect(ics.replace(/\r\n/g, '\u0000')).not.toMatch(/[\r\n]/) // no bare CR or LF anywhere
    const lines = unfold(ics).split('\r\n')
    expect(lines.some((l) => l.startsWith('ATTENDEE'))).toBe(false)
    expect(lines.some((l) => l.startsWith('X-INJECT'))).toBe(false)
  })

  it('a lone CR in a title cannot start a new property', () => {
    const ics = buildIcs([normalizeItem({ ...item, title: 'Hack\rATTENDEE:mailto:x@example.com' })], NOW)
    expect(ics.replace(/\r\n/g, '')).not.toMatch(/\r/)
    expect(unfold(ics).split('\r\n').some((l) => l.startsWith('ATTENDEE'))).toBe(false)
  })

  it('even an unnormalised opportunity with a bad url is written safely', () => {
    const ics = buildIcs([{ ...normalizeItem(item), url: crafted }], NOW)
    expect(unfold(ics).split('\r\n').some((l) => l.startsWith('ATTENDEE'))).toBe(false)
  })
})

describe('normalizeItem url validation', () => {
  it.each([
    ['https://example.org/a?b=1', 'https://example.org/a?b=1'],
    ['  https://Example.org  ', 'https://example.org/'],
    ['http://example.org', ''],
    ['javascript:alert(1)', ''],
    ['data:text/html,hi', ''],
    ['not a url', ''],
    ['', ''],
    ['https://user:pw@example.org', ''],
  ])('%j -> %j', (raw, expected) => {
    expect(safeHttpsUrl(raw)).toBe(expected)
    expect(normalizeItem({ ...item, url: raw }).url).toBe(expected)
  })
  it('the ics omits the URL line when there is no valid url', () => {
    const ics = buildIcs([normalizeItem({ ...item, url: 'javascript:alert(1)' })], NOW)
    expect(ics).not.toMatch(/^URL:/m)
    expect(ics).not.toContain('javascript')
  })
})

describe('exports and ranking respect the clock', () => {
  const past = normalizeItem({ ...item, title: 'past', deadline: '2026-11-01' })
  const today = normalizeItem({ ...item, title: 'today', deadline: '2026-11-03' })
  const rolling = normalizeItem({ ...item, title: 'rolling', deadline: null })

  it('only exports deadlines that have not passed', () => {
    expect(exportableDeadlines([past, today, rolling], '2026-11-03').map((o) => o.title)).toEqual(['today'])
  })

  const me: StudentProfile = { skills: ['Python'], year: 2, city: 'Chennai', teamSize: 1, remoteOnly: false }

  it('keeps no-deadline listings only while the snapshot is fresh', () => {
    const snap = '2026-11-02'
    expect(rankOpportunities(me, [rolling], '2026-11-03', snap)).toHaveLength(1)
    const stale = new Date(Date.UTC(2026, 10, 2 + STALE_AFTER_DAYS + 1)).toISOString().slice(0, 10)
    expect(rankOpportunities(me, [rolling], stale, snap)).toHaveLength(0)
  })

  it('ages the verified boost against the snapshot date', () => {
    const fresh = scoreOpportunity(me, today, '2026-11-03', '2026-11-02')
    const stale = scoreOpportunity(me, today, '2026-11-03', '2026-08-01')
    expect(fresh.score).toBeGreaterThan(stale.score)
    expect(stale.cautions.join(' ')).toMatch(/checked/i)
    expect(fresh.cautions.join(' ')).not.toMatch(/checked/i)
  })
})
