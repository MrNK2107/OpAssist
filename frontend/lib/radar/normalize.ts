// Turns free-text listing fields into structured, filterable data.
// Every parser is conservative: when the text is ambiguous it returns
// "not stated" (null) instead of guessing, so filters never hide something
// a student could actually enter.

import type { Audience, RadarMode, RadarOpportunity, SeedItem, TeamRule } from './types'

export const CITIES: Record<string, string[]> = {
  Chennai: ['chennai', 'madras'],
  Bengaluru: ['bengaluru', 'bangalore'],
  Mumbai: ['mumbai'],
  Delhi: ['delhi', 'new delhi'],
  Hyderabad: ['hyderabad'],
  Pune: ['pune'],
  Kolkata: ['kolkata', 'calcutta'],
  Kanpur: ['kanpur'],
  Gurugram: ['gurugram', 'gurgaon'],
  Noida: ['noida'],
  Bhubaneswar: ['bhubaneswar'],
  Coimbatore: ['coimbatore'],
  Erode: ['erode'],
  Ahmedabad: ['ahmedabad'],
  Jaipur: ['jaipur'],
  Kochi: ['kochi', 'cochin'],
}

export const CITY_NAMES = Object.keys(CITIES)

/** Canonical skill vocabulary: tag -> words that imply it. */
export const SKILL_SYNONYMS: Record<string, string[]> = {
  python: ['python', 'pandas', 'numpy', 'fastapi', 'django', 'flask'],
  javascript: ['javascript', 'js', 'node', 'node.js'],
  typescript: ['typescript', 'ts'],
  react: ['react', 'next.js', 'nextjs'],
  'web dev': ['web', 'frontend', 'backend', 'full stack', 'full-stack', 'rest api', 'apis'],
  'ai/ml': ['ai', 'ml', 'machine learning', 'deep learning', 'dl', 'pytorch', 'tensorflow', 'scikit-learn', 'nlp', 'computer vision', 'cv'],
  llms: ['llm', 'llms', 'genai', 'generative ai', 'rag', 'langchain', 'agents', 'agentic', 'openai', 'gemini', 'chatbot'],
  'data science': ['data', 'analytics', 'statistics', 'sql', 'data science'],
  dsa: ['dsa', 'competitive programming', 'algorithms', 'coding contest', 'programming contest'],
  java: ['java'],
  'c/c++': ['c++', 'c/c++', 'cpp'],
  blockchain: ['blockchain', 'web3', 'crypto', 'solidity', 'defi'],
  security: ['security', 'cybersecurity', 'ctf', 'bug bounty'],
  iot: ['iot', 'embedded', 'hardware'],
  robotics: ['robotics', 'ros', 'ros 2'],
  mobile: ['android', 'ios', 'flutter', 'mobile', 'react native'],
  cloud: ['cloud', 'aws', 'gcp', 'azure', 'devops', 'docker', 'kubernetes'],
  design: ['design', 'ui', 'ux', 'figma', 'product design'],
  'open source': ['open source', 'open-source', 'git', 'github'],
  sustainability: ['climate', 'sustainability', 'sdg', 'sdgs', 'social good', 'energy'],
  health: ['health', 'healthcare', 'medical', 'biotech'],
  fintech: ['fintech', 'finance', 'payments', 'banking'],
  education: ['education', 'edtech', 'learning'],
}

export const SKILL_TAGS = Object.keys(SKILL_SYNONYMS)

function escapeRe(s: string) {
  return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

function hasWord(text: string, word: string): boolean {
  // Word boundaries that also work for tokens like "c++" and "node.js".
  return new RegExp(`(^|[^a-z0-9+])${escapeRe(word)}($|[^a-z0-9+])`).test(text)
}

/** Map arbitrary free text to canonical skill tags. */
export function extractTags(text: string): string[] {
  const t = text.toLowerCase()
  return SKILL_TAGS.filter((tag) => SKILL_SYNONYMS[tag].some((w) => hasWord(t, w)))
}

/** Normalise a user-typed skill to a canonical tag when one exists. */
export function canonicalSkill(skill: string): string {
  const s = skill.trim().toLowerCase()
  if (SKILL_SYNONYMS[s]) return s
  const hit = SKILL_TAGS.find((tag) => SKILL_SYNONYMS[tag].includes(s))
  return hit ?? s
}

export function parseMode(mode: string): RadarMode {
  const m = mode.toLowerCase()
  if (m === 'hybrid') return 'hybrid'
  if (m === 'offline' || m === 'onsite' || m === 'in-person') return 'in-person'
  return 'online'
}

export function parseCity(text: string): string | null {
  const t = text.toLowerCase()
  for (const [name, words] of Object.entries(CITIES)) {
    if (words.some((w) => hasWord(t, w))) return name
  }
  return null
}

export function parseTeam(text: string): TeamRule {
  const t = text.toLowerCase().trim()
  if (!t || /unknown|not listed|formed at event/.test(t)) return { min: null, max: null, soloOk: null }

  const exactly = t.match(/exactly\s+(\d+)/)
  if (exactly) {
    const n = Number(exactly[1])
    return { min: n, max: n, soloOk: n === 1 }
  }

  const range = t.match(/(\d+)\s*-\s*(\d+)/)
  const upTo = t.match(/up to\s+(\d+)/)
  const soloWord = /\bsolo\b/.test(t)
  const required = /\bteam\b/.test(t) && !soloWord

  if (range) {
    const min = Number(range[1])
    const max = Number(range[2])
    return { min, max, soloOk: min <= 1 }
  }
  if (upTo) return { min: 1, max: Number(upTo[1]), soloOk: true }
  if (/solo \(1\)|solo only|^solo$/.test(t)) return { min: 1, max: 1, soloOk: true }
  if (soloWord) return { min: 1, max: null, soloOk: true }
  if (required) return { min: 2, max: null, soloOk: false }
  return { min: null, max: null, soloOk: null }
}

const ROMAN: Record<string, number> = { i: 1, ii: 2, iii: 3, iv: 4, v: 5 }
const ORDINAL: Record<string, number> = { '1st': 1, first: 1, '2nd': 2, second: 2, '3rd': 3, third: 3, '4th': 4, fourth: 4, final: 4 }

function yearToken(tok: string): number | null {
  const k = tok.toLowerCase()
  return ROMAN[k] ?? ORDINAL[k] ?? null
}

/**
 * Study years an eligibility line allows, or null when it does not restrict
 * by year. Handles "from 2nd year onward", "II and III year", "3rd/4th year".
 */
export function parseYears(text: string): number[] | null {
  // "pre-final" is 3rd year of a 4-year degree.
  const t = text.toLowerCase().replace(/pre-?final/g, '3rd')
  const onward = t.match(/(?:from\s+)?(1st|2nd|3rd|4th|first|second|third|fourth)\s+year\s+(?:onwards?|and above|\+)/)
  if (onward) {
    const start = yearToken(onward[1])!
    return [1, 2, 3, 4, 5].filter((y) => y >= start)
  }
  const list = t.match(/\b((?:(?:i{1,3}|iv|v|1st|2nd|3rd|4th|first|second|third|fourth|final)\s*(?:,|\/|and|or|&)\s*)+(?:i{1,3}|iv|v|1st|2nd|3rd|4th|first|second|third|fourth|final))[\s-]+year/)
  if (list) {
    const years = list[1]
      .split(/\s*(?:,|\/|and|or|&)\s*/)
      .map(yearToken)
      .filter((y): y is number => y !== null)
    if (years.length) return Array.from(new Set(years)).sort()
  }
  const single = t.match(/\b(1st|2nd|3rd|4th|first|second|third|fourth|final)[- ]year\s+(?:students?|only)/)
  if (single) return [yearToken(single[1])!]
  return null
}

export function parseAudience(text: string): Audience {
  const t = text.toLowerCase()
  if (/startup|founder|legal entity/.test(t) && !/student/.test(t)) return 'startups'
  if (/students? only|enrolled|currently pursuing|students?\b/.test(t) && !/professionals?|open to all|^all$/.test(t)) return 'students'
  return 'open'
}

/** Small stable hash so ids survive reloads without a database. */
export function stableId(...parts: string[]): string {
  let h = 2166136261
  for (const ch of parts.join('|')) {
    h ^= ch.charCodeAt(0)
    h = Math.imul(h, 16777619)
  }
  return (h >>> 0).toString(36)
}

/** The url if it parses as an https URL without credentials, else ''. Seed data is
 * hand-collected; anything else (http, javascript:, CR/LF tricks) is blanked, not trusted. */
export function safeHttpsUrl(raw: string | null | undefined): string {
  if (!raw) return ''
  const trimmed = raw.trim()
  // the URL parser silently strips tabs and newlines; refuse control characters outright
  if ([...trimmed].some((c) => c.charCodeAt(0) < 0x20 || c.charCodeAt(0) === 0x7f)) return ''
  let u: URL
  try {
    u = new URL(trimmed)
  } catch {
    return ''
  }
  if (u.protocol !== 'https:' || u.username || u.password || !u.hostname) return ''
  return u.href
}

export function normalizeItem(item: SeedItem): RadarOpportunity {
  const topicText = `${item.topics} ${item.title}`
  const deadline = item.deadline && /^\d{4}-\d{2}-\d{2}$/.test(item.deadline) ? item.deadline : null
  return {
    id: stableId(item.kind, item.title, item.organizer),
    kind: item.kind,
    title: item.title,
    organizer: item.organizer,
    url: safeHttpsUrl(item.url),
    mode: parseMode(item.mode),
    city: parseCity(item.city),
    cityText: item.city,
    free: item.fee === 'free',
    deadline,
    eventDates: item.event_dates,
    team: parseTeam(item.team),
    teamText: item.team,
    reward: item.reward,
    eligibility: item.eligibility,
    years: parseYears(item.eligibility),
    audience: parseAudience(item.eligibility),
    tags: extractTags(topicText),
    openTheme: /\bopen\b(?! source)|open innovation|open ended|any theme/i.test(item.topics),
    verified: item.verified,
  }
}

export function normalizeAll(items: SeedItem[]): RadarOpportunity[] {
  const seen = new Set<string>()
  const out: RadarOpportunity[] = []
  for (const item of items) {
    const n = normalizeItem(item)
    if (seen.has(n.id)) continue
    seen.add(n.id)
    out.push(n)
  }
  return out
}
