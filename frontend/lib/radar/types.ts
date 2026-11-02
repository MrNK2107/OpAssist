// Domain types for the Radar: OpAssist's public, no-login discovery surface.

export type RadarKind = 'hackathon' | 'internship'
export type RadarMode = 'online' | 'hybrid' | 'in-person'
export type Audience = 'students' | 'open' | 'startups'

/** One row of data/seed-opportunities.json (public listing fields only). */
export interface SeedItem {
  kind: RadarKind
  title: string
  organizer: string
  url: string
  mode: string
  city: string
  fee: string
  deadline: string | null
  event_dates: string
  team: string
  reward: string
  eligibility: string
  topics: string
  verified: boolean
}

export interface SeedFile {
  snapshot_date: string
  note: string
  items: SeedItem[]
}

export interface TeamRule {
  min: number | null
  max: number | null
  /** true = individuals may enter, false = a team is required, null = not stated */
  soloOk: boolean | null
}

export interface RadarOpportunity {
  id: string
  kind: RadarKind
  title: string
  organizer: string
  url: string
  mode: RadarMode
  /** Canonical Indian city when the listing names one, else null. */
  city: string | null
  cityText: string
  free: boolean
  /** ISO date (YYYY-MM-DD) or null for rolling applications. */
  deadline: string | null
  eventDates: string
  team: TeamRule
  teamText: string
  reward: string
  eligibility: string
  /** Study years (1-5) this is open to, or null when not restricted. */
  years: number[] | null
  audience: Audience
  /** Lower-cased canonical skill/topic tags. */
  tags: string[]
  /** True when the listing has an open theme (any stack is welcome). */
  openTheme: boolean
  verified: boolean
}

export interface StudentProfile {
  skills: string[]
  /** Year of study, 1-5. null = not set. */
  year: number | null
  city: string | null
  teamSize: number | null
  /** Prefer things that do not need travel. */
  remoteOnly: boolean
}

export interface MatchResult {
  opportunity: RadarOpportunity
  score: number
  label: 'Strong fit' | 'Good fit' | 'Stretch'
  reasons: string[]
  cautions: string[]
  eligible: boolean
}
