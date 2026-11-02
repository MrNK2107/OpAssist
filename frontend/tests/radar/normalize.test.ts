import { describe, it, expect } from 'vitest'
import {
  canonicalSkill,
  extractTags,
  normalizeAll,
  normalizeItem,
  parseAudience,
  parseCity,
  parseMode,
  parseTeam,
  parseYears,
  stableId,
} from '@/lib/radar/normalize'
import { RADAR_OPPORTUNITIES, SNAPSHOT_DATE, SNAPSHOT_NOTE } from '@/lib/radar/seed'
import type { SeedItem } from '@/lib/radar/types'
import seed from '@/data/seed-opportunities.json'

const base: SeedItem = {
  kind: 'hackathon',
  title: 'Test Hack',
  organizer: 'Org',
  url: 'https://example.org',
  mode: 'online',
  city: 'Online',
  fee: 'free',
  deadline: '2026-11-20',
  event_dates: '',
  team: 'solo ok (1-4)',
  reward: '',
  eligibility: 'Students',
  topics: 'AI/ML, Web',
  verified: true,
}

describe('parseTeam', () => {
  it.each([
    ['solo (1)', { min: 1, max: 1, soloOk: true }],
    ['solo only', { min: 1, max: 1, soloOk: true }],
    ['solo ok', { min: 1, max: null, soloOk: true }],
    ['solo ok (1-4)', { min: 1, max: 4, soloOk: true }],
    ['1-6, solo ok', { min: 1, max: 6, soloOk: true }],
    ['solo ok (up to 6)', { min: 1, max: 6, soloOk: true }],
    ['team 2-4', { min: 2, max: 4, soloOk: false }],
    ['team 2-5 required', { min: 2, max: 5, soloOk: false }],
    ['team of exactly 2', { min: 2, max: 2, soloOk: false }],
    ['unknown', { min: null, max: null, soloOk: null }],
    ['not listed', { min: null, max: null, soloOk: null }],
    ['teams formed at event', { min: null, max: null, soloOk: null }],
  ])('%s', (text, expected) => {
    expect(parseTeam(text)).toEqual(expected)
  })
})

describe('parseYears', () => {
  it('reads "from 2nd year onward"', () => {
    expect(parseYears('Engineering students from 2nd year onward')).toEqual([2, 3, 4, 5])
  })
  it('reads roman numerals', () => {
    expect(parseYears('BE/BTech II and III year; >=65%')).toEqual([2, 3])
  })
  it('treats pre-final as 3rd year', () => {
    expect(parseYears('2nd/pre-final-year students')).toEqual([2, 3])
  })
  it('returns null when not restricted', () => {
    expect(parseYears('Students, individual')).toBeNull()
    expect(parseYears('All')).toBeNull()
  })
})

describe('field parsers', () => {
  it('maps modes', () => {
    expect(parseMode('online')).toBe('online')
    expect(parseMode('remote')).toBe('online')
    expect(parseMode('hybrid')).toBe('hybrid')
    expect(parseMode('offline')).toBe('in-person')
    expect(parseMode('onsite')).toBe('in-person')
  })
  it('finds canonical cities, including old names', () => {
    expect(parseCity('Chennai (Millenia Business Park II)')).toBe('Chennai')
    expect(parseCity('Remote (company in Bangalore)')).toBe('Bengaluru')
    expect(parseCity('Gurgaon')).toBe('Gurugram')
    expect(parseCity('Online')).toBeNull()
  })
  it('extracts skill tags with word boundaries', () => {
    expect(extractTags('Python, FastAPI, React, RAG')).toEqual(expect.arrayContaining(['python', 'react', 'llms']))
    expect(extractTags('Mainframe migration')).not.toContain('ai/ml')
    expect(extractTags('C/C++, Linux')).toContain('c/c++')
  })
  it('canonicalises typed skills', () => {
    expect(canonicalSkill(' PyTorch ')).toBe('ai/ml')
    expect(canonicalSkill('React')).toBe('react')
    expect(canonicalSkill('Rust')).toBe('rust')
  })
  it('classifies audience', () => {
    expect(parseAudience('Students only')).toBe('students')
    expect(parseAudience('Students, professionals, indie devs')).toBe('open')
    expect(parseAudience('Early-stage software startups: registered legal entity')).toBe('startups')
  })
  it('stableId is deterministic and distinct', () => {
    expect(stableId('a', 'b')).toBe(stableId('a', 'b'))
    expect(stableId('a', 'b')).not.toBe(stableId('a', 'c'))
  })
})

describe('normalizeItem', () => {
  it('builds a structured opportunity', () => {
    const o = normalizeItem(base)
    expect(o.mode).toBe('online')
    expect(o.free).toBe(true)
    expect(o.team).toEqual({ min: 1, max: 4, soloOk: true })
    expect(o.tags).toContain('ai/ml')
  })
  it('drops malformed deadlines to rolling', () => {
    expect(normalizeItem({ ...base, deadline: 'soon' }).deadline).toBeNull()
    expect(normalizeItem({ ...base, deadline: null }).deadline).toBeNull()
  })
  it('flags open themes but not "open source"', () => {
    expect(normalizeItem({ ...base, topics: 'Open innovation' }).openTheme).toBe(true)
    expect(normalizeItem({ ...base, topics: 'Open source contribution' }).openTheme).toBe(false)
  })
  it('dedupes repeated listings', () => {
    expect(normalizeAll([base, base])).toHaveLength(1)
  })
})

describe('seed snapshot', () => {
  it('is dated and carries a verification note', () => {
    expect(SNAPSHOT_DATE).toMatch(/^\d{4}-\d{2}-\d{2}$/)
    expect(SNAPSHOT_NOTE).toMatch(/confirm/i)
  })
  it('has both kinds and only https links', () => {
    expect(RADAR_OPPORTUNITIES.some((o) => o.kind === 'hackathon')).toBe(true)
    expect(RADAR_OPPORTUNITIES.some((o) => o.kind === 'internship')).toBe(true)
    for (const o of RADAR_OPPORTUNITIES) expect(o.url).toMatch(/^https:\/\//)
  })
  it('contains only public listing fields (no personal research notes)', () => {
    const allowed = ['kind', 'title', 'organizer', 'url', 'mode', 'city', 'fee', 'deadline', 'event_dates', 'team', 'reward', 'eligibility', 'topics', 'verified']
    for (const item of (seed as { items: Record<string, unknown>[] }).items) {
      expect(Object.keys(item).sort()).toEqual([...allowed].sort())
    }
  })
})
