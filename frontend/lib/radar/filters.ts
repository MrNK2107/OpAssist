// Eligibility filters: year of study, team size, fee, and online vs city.

import { eligibility } from './match'
import type { RadarKind, RadarMode, RadarOpportunity, StudentProfile } from './types'

export interface RadarFilters {
  kinds: RadarKind[]
  modes: RadarMode[]
  freeOnly: boolean
  /** Hide anything the profile is not eligible for (year, team, audience). */
  eligibleOnly: boolean
  /** Only in-person events in the profile's city (online stays visible). */
  nearMeOnly: boolean
  query: string
}

export const DEFAULT_FILTERS: RadarFilters = {
  kinds: ['hackathon', 'internship'],
  modes: ['online', 'hybrid', 'in-person'],
  freeOnly: false,
  eligibleOnly: true,
  nearMeOnly: false,
  query: '',
}

export function passesFilters(opp: RadarOpportunity, f: RadarFilters, profile: StudentProfile): boolean {
  if (!f.kinds.includes(opp.kind)) return false
  if (!f.modes.includes(opp.mode)) return false
  if (f.freeOnly && !opp.free) return false
  if (f.eligibleOnly && eligibility(profile, opp).length > 0) return false
  if (f.nearMeOnly && opp.mode !== 'online') {
    if (!profile.city || opp.city !== profile.city) return false
  }
  const q = f.query.trim().toLowerCase()
  if (q) {
    const hay = `${opp.title} ${opp.organizer} ${opp.tags.join(' ')} ${opp.cityText}`.toLowerCase()
    if (!q.split(/\s+/).every((w) => hay.includes(w))) return false
  }
  return true
}

export function applyFilters(opps: RadarOpportunity[], f: RadarFilters, profile: StudentProfile): RadarOpportunity[] {
  return opps.filter((o) => passesFilters(o, f, profile))
}

export function toggle<T>(list: T[], value: T): T[] {
  return list.includes(value) ? list.filter((v) => v !== value) : [...list, value]
}
