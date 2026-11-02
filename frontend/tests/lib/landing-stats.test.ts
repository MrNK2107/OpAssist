import { describe, it, expect, vi } from 'vitest'
import fs from 'node:fs'
import path from 'node:path'
import {
  FALLBACK_STATS,
  ILLUSTRATIVE_NOTE,
  LANDING_TYPES,
  fetchLandingStats,
  formatCount,
  parseStatsResponse,
  totalLabel,
} from '@/lib/landing-stats'

const LIVE = {
  by_type: { hackathon: 12, internship: 7, job: 40, scholarship: 0, oss: 3, ambassador: 1, event: 99 },
  total: 162,
  available: true,
}

describe('parseStatsResponse', () => {
  it('maps live counts and recomputes total from landing types only', () => {
    const s = parseStatsResponse(LIVE)!
    expect(s.live).toBe(true)
    expect(s.byType.job).toBe(40)
    expect(s.byType.scholarship).toBe(0)
    expect(s.total).toBe(63) // events are not shown on the landing page
  })

  it('rejects unavailable, malformed and empty payloads', () => {
    expect(parseStatsResponse({ ...LIVE, available: false })).toBeNull()
    expect(parseStatsResponse(null)).toBeNull()
    expect(parseStatsResponse('nope')).toBeNull()
    expect(parseStatsResponse({ available: true })).toBeNull()
    expect(parseStatsResponse({ available: true, by_type: { job: 0 } })).toBeNull()
  })

  it('treats negative / non-numeric counts as zero', () => {
    const s = parseStatsResponse({ available: true, by_type: { job: 'x', hackathon: -4, oss: 2 } })!
    expect(s.byType.job).toBe(0)
    expect(s.byType.hackathon).toBe(0)
    expect(s.total).toBe(2)
  })
})

describe('fetchLandingStats', () => {
  it('returns live stats from the public endpoint', async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify(LIVE), { status: 200 }))
    const s = await fetchLandingStats(fetchMock as unknown as typeof fetch)
    expect(fetchMock.mock.calls[0][0]).toMatch(/\/api\/opportunities\/stats$/)
    expect(s.live).toBe(true)
    expect(s.byType.hackathon).toBe(12)
  })

  it('falls back when the API is down', async () => {
    const fetchMock = vi.fn().mockRejectedValue(new TypeError('Failed to fetch'))
    expect(await fetchLandingStats(fetchMock as unknown as typeof fetch)).toBe(FALLBACK_STATS)
  })

  it('falls back on a non-OK response', async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response('boom', { status: 500 }))
    expect(await fetchLandingStats(fetchMock as unknown as typeof fetch)).toBe(FALLBACK_STATS)
  })

  it('falls back when the request times out', async () => {
    const fetchMock = vi.fn(
      (_url: string, init?: RequestInit) =>
        new Promise<Response>((_, reject) => {
          init?.signal?.addEventListener('abort', () => reject(new DOMException('aborted', 'AbortError')))
        }),
    )
    const s = await fetchLandingStats(fetchMock as unknown as typeof fetch, 10)
    expect(s).toBe(FALLBACK_STATS)
  })
})

describe('formatCount', () => {
  it('formats live and estimated counts', () => {
    expect(formatCount(42, true)).toBe('42')
    expect(formatCount(500, false)).toBe('500+')
    expect(formatCount(1234, true)).toBe('1.2K')
    expect(formatCount(1000, false)).toBe('1K+')
    expect(formatCount(25_400, true)).toBe('25K')
  })
})

describe('fallback stats', () => {
  it('covers every landing type and sums to total', () => {
    const sum = LANDING_TYPES.reduce((acc, t) => acc + FALLBACK_STATS.byType[t], 0)
    expect(FALLBACK_STATS.total).toBe(sum)
    expect(FALLBACK_STATS.live).toBe(false)
  })
})

describe('illustrative labelling', () => {
  it('labels the fallback total as illustrative and the live one as live', () => {
    expect(totalLabel(false)).toMatch(/illustrative/i)
    expect(totalLabel(true)).toBe('Live opportunities')
    expect(ILLUSTRATIVE_NOTE).toMatch(/not real data/i)
  })
})

describe('landing page', () => {
  const src = fs.readFileSync(path.resolve(__dirname, '..', '..', 'app', 'page.tsx'), 'utf8')

  it('has no hard-coded opportunity counts', () => {
    expect(src).not.toMatch(/['"]\d+K?\+['"]/)
  })

  it('shows the illustrative note next to both groups of fallback counts', () => {
    const notes = src.match(/!stats\.live && \(\s*<p[^>]*>\s*\{ILLUSTRATIVE_NOTE\}/g) ?? []
    expect(notes.length).toBe(2)
    expect(src).toContain('totalLabel(stats.live)')
  })

  it('links categories by API type key', () => {
    expect(src).toContain('/opportunities?type=${type.type}')
  })
})
