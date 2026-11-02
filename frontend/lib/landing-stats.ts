// Landing-page opportunity counts.
//
// Single source of truth for every number on the landing page. Live values
// come from the public `GET /api/opportunities/stats` endpoint; when the API
// is down, slow, or reports an empty database, the static FALLBACK_COUNTS are
// shown instead. Those fallback numbers are NOT measured: they are
// illustrative placeholders, rendered with a "+" suffix and always paired on
// the page with ILLUSTRATIVE_NOTE so nobody mistakes them for real data.

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export type LandingType = 'hackathon' | 'internship' | 'job' | 'scholarship' | 'oss' | 'ambassador'

export const LANDING_TYPES: LandingType[] = ['hackathon', 'internship', 'job', 'scholarship', 'oss', 'ambassador']

export const FALLBACK_COUNTS: Record<LandingType, number> = {
  hackathon: 500,
  internship: 200,
  job: 1000,
  scholarship: 50,
  oss: 100,
  ambassador: 30,
}

/** Shown next to the counts whenever they are the illustrative fallback. */
export const ILLUSTRATIVE_NOTE =
  'Illustrative figures: live counts could not be loaded, so these numbers are placeholders, not real data.'

/** Label for the hero total card. */
export function totalLabel(live: boolean): string {
  return live ? 'Live opportunities' : 'Opportunities (illustrative)'
}

export interface LandingStats {
  byType: Record<LandingType, number>
  total: number
  live: boolean
}

export const FALLBACK_STATS: LandingStats = {
  byType: { ...FALLBACK_COUNTS },
  total: LANDING_TYPES.reduce((sum, t) => sum + FALLBACK_COUNTS[t], 0),
  live: false,
}

interface StatsResponse {
  by_type?: Record<string, unknown>
  total?: unknown
  available?: unknown
}

/** Turn an API payload into LandingStats, or null if it is unusable. */
export function parseStatsResponse(body: unknown): LandingStats | null {
  if (!body || typeof body !== 'object') return null
  const { by_type, available } = body as StatsResponse
  if (available !== true || !by_type || typeof by_type !== 'object') return null

  const byType = {} as Record<LandingType, number>
  for (const t of LANDING_TYPES) {
    const n = Number(by_type[t] ?? 0)
    byType[t] = Number.isFinite(n) && n > 0 ? Math.floor(n) : 0
  }
  const total = LANDING_TYPES.reduce((sum, t) => sum + byType[t], 0)
  // An empty database (fresh dev setup, failed first scrape) would render a
  // wall of zeros; the estimates are more useful there.
  if (total === 0) return null
  return { byType, total, live: true }
}

export async function fetchLandingStats(
  fetchImpl: typeof fetch = fetch,
  timeoutMs = 4000,
): Promise<LandingStats> {
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), timeoutMs)
  try {
    const res = await fetchImpl(`${API_URL}/api/opportunities/stats`, { signal: controller.signal })
    if (!res.ok) return FALLBACK_STATS
    return parseStatsResponse(await res.json()) ?? FALLBACK_STATS
  } catch {
    return FALLBACK_STATS
  } finally {
    clearTimeout(timer)
  }
}

/** 1234 -> "1.2K", 999 -> "999"; estimates get a "+" suffix. */
export function formatCount(n: number, live: boolean): string {
  let s: string
  if (n >= 10_000) s = `${Math.floor(n / 1000)}K`
  else if (n >= 1000) s = `${(Math.floor(n / 100) / 10).toString()}K`
  else s = String(n)
  return live ? s : `${s}+`
}
