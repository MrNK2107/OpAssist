import seed from '@/data/seed-opportunities.json'
import { normalizeAll } from './normalize'
import type { RadarOpportunity, SeedFile, StudentProfile } from './types'

const file = seed as SeedFile

export const SNAPSHOT_DATE = file.snapshot_date
export const SNAPSHOT_NOTE = file.note
export const RADAR_OPPORTUNITIES: RadarOpportunity[] = normalizeAll(file.items)

/** Pre-filled so first-time visitors see ranked results; editable in place. */
export const SAMPLE_PROFILE: StudentProfile = {
  skills: ['Python', 'React', 'AI/ML', 'LLMs'],
  year: 2,
  city: 'Chennai',
  teamSize: 1,
  remoteOnly: false,
}

export function byId(id: string): RadarOpportunity | undefined {
  return RADAR_OPPORTUNITIES.find((o) => o.id === id)
}
