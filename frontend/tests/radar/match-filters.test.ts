import { describe, it, expect } from 'vitest'
import { normalizeItem } from '@/lib/radar/normalize'
import { eligibility, matchedSkills, rankOpportunities, scoreOpportunity } from '@/lib/radar/match'
import { applyFilters, DEFAULT_FILTERS, toggle } from '@/lib/radar/filters'
import type { SeedItem, StudentProfile } from '@/lib/radar/types'

const ASOF = '2026-11-03'

const mk = (over: Partial<SeedItem>): SeedItem => ({
  kind: 'hackathon',
  title: 'Hack',
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
  topics: 'Python, React',
  verified: true,
  ...over,
})

const me: StudentProfile = { skills: ['Python', 'React'], year: 2, city: 'Chennai', teamSize: 1, remoteOnly: false }

describe('scoreOpportunity', () => {
  it('explains skill, mode and solo fit', () => {
    const r = scoreOpportunity(me, normalizeItem(mk({ title: 'A' })), ASOF)
    expect(r.eligible).toBe(true)
    expect(r.reasons.join(' ')).toMatch(/Python and React/)
    expect(r.reasons).toContain('Fully online, no travel needed')
    expect(r.reasons).toContain('Solo entries welcome')
    expect(r.label).toBe('Strong fit')
  })

  it('rewards the same city and warns about travel elsewhere', () => {
    const local = scoreOpportunity(me, normalizeItem(mk({ title: 'L', mode: 'offline', city: 'Chennai' })), ASOF)
    const far = scoreOpportunity(me, normalizeItem(mk({ title: 'F', mode: 'offline', city: 'Kanpur' })), ASOF)
    expect(local.reasons.join(' ')).toMatch(/Chennai, your city/)
    expect(far.cautions.join(' ')).toMatch(/Kanpur/)
    expect(local.score).toBeGreaterThan(far.score)
  })

  it('penalises in-person events for remote-only students', () => {
    const opp = normalizeItem(mk({ title: 'F', mode: 'offline', city: 'Kanpur' }))
    const a = scoreOpportunity(me, opp, ASOF).score
    const b = scoreOpportunity({ ...me, remoteOnly: true }, opp, ASOF).score
    expect(b).toBeLessThan(a)
  })

  it('caps the score and explains why when ineligible by year', () => {
    const r = scoreOpportunity(me, normalizeItem(mk({ eligibility: 'BE/BTech III and IV year' })), ASOF)
    expect(r.eligible).toBe(false)
    expect(r.score).toBeLessThanOrEqual(25)
    expect(r.cautions[0]).toMatch(/3rd\/4th year only/)
  })

  it('blocks solo students from team-required events', () => {
    const opp = normalizeItem(mk({ team: 'team 2-4' }))
    expect(eligibility(me, opp)[0]).toMatch(/at least 2/)
    expect(eligibility({ ...me, teamSize: 3 }, opp)).toEqual([])
    expect(eligibility({ ...me, teamSize: 6 }, opp)[0]).toMatch(/up to 4/)
  })

  it('uses open themes when no skills match', () => {
    const r = scoreOpportunity({ ...me, skills: ['Rust'] }, normalizeItem(mk({ topics: 'Open innovation' })), ASOF)
    expect(r.reasons[0]).toMatch(/Open theme/)
  })

  it('warns when a deadline is close or details are unverified', () => {
    const r = scoreOpportunity(me, normalizeItem(mk({ deadline: '2026-11-04', verified: false, fee: 'fee_unknown' })), ASOF)
    expect(r.cautions).toEqual(expect.arrayContaining(['Closes in 1 day', 'Details not yet re-verified', 'Entry fee not confirmed']))
  })

  it('matches synonyms (PyTorch counts as AI/ML)', () => {
    const opp = normalizeItem(mk({ topics: 'Machine learning' }))
    expect(matchedSkills({ ...me, skills: ['PyTorch'] }, opp)).toEqual(['ai/ml'])
  })

  it('keeps scores within 0..100 for an empty profile', () => {
    const r = scoreOpportunity({ skills: [], year: null, city: null, teamSize: null, remoteOnly: true }, normalizeItem(mk({ mode: 'offline', fee: 'x', verified: false })), ASOF)
    expect(r.score).toBeGreaterThanOrEqual(0)
    expect(r.score).toBeLessThanOrEqual(100)
  })
})

describe('rankOpportunities', () => {
  it('drops closed listings and sorts by score then deadline', () => {
    const opps = [
      normalizeItem(mk({ title: 'closed', deadline: '2026-11-01' })),
      normalizeItem(mk({ title: 'weak', topics: 'Biology', mode: 'offline', city: 'Kanpur' })),
      normalizeItem(mk({ title: 'strong-late', deadline: '2026-12-20' })),
      normalizeItem(mk({ title: 'strong-soon', deadline: '2026-11-10' })),
    ]
    const titles = rankOpportunities(me, opps, ASOF).map((r) => r.opportunity.title)
    expect(titles).toEqual(['strong-soon', 'strong-late', 'weak'])
  })
})

describe('filters', () => {
  const opps = [
    normalizeItem(mk({ title: 'online-hack' })),
    normalizeItem(mk({ title: 'kanpur-hack', mode: 'offline', city: 'Kanpur' })),
    normalizeItem(mk({ title: 'chennai-hack', mode: 'offline', city: 'Chennai' })),
    normalizeItem(mk({ title: 'team-only', team: 'team 2-4' })),
    normalizeItem(mk({ title: 'paid', fee: 'fee_unknown' })),
    normalizeItem(mk({ title: 'intern', kind: 'internship', mode: 'remote', topics: 'Java' })),
  ]
  const names = (f = DEFAULT_FILTERS, p = me) => applyFilters(opps, f, p).map((o) => o.title)

  it('hides ineligible listings by default', () => {
    expect(names()).not.toContain('team-only')
    expect(names({ ...DEFAULT_FILTERS, eligibleOnly: false })).toContain('team-only')
  })
  it('filters by kind, mode and fee', () => {
    expect(names({ ...DEFAULT_FILTERS, kinds: ['internship'] })).toEqual(['intern'])
    expect(names({ ...DEFAULT_FILTERS, modes: ['in-person'] })).toEqual(['kanpur-hack', 'chennai-hack'])
    expect(names({ ...DEFAULT_FILTERS, freeOnly: true })).not.toContain('paid')
  })
  it('near-me keeps online plus in-person in my city only', () => {
    const r = names({ ...DEFAULT_FILTERS, nearMeOnly: true })
    expect(r).toContain('chennai-hack')
    expect(r).toContain('online-hack')
    expect(r).not.toContain('kanpur-hack')
  })
  it('matches every word of the search query', () => {
    expect(names({ ...DEFAULT_FILTERS, query: 'chennai hack' })).toEqual(['chennai-hack'])
    expect(names({ ...DEFAULT_FILTERS, query: 'java' })).toEqual(['intern'])
  })
  it('toggle adds and removes', () => {
    expect(toggle(['a'], 'b')).toEqual(['a', 'b'])
    expect(toggle(['a', 'b'], 'a')).toEqual(['b'])
  })
})
