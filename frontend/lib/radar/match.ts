// Personalised matching. Deterministic and explainable: every point a listing
// earns comes with a sentence the student can read ("why this fits"), and
// every hard blocker comes with a caution. No model, no black box.

import { canonicalSkill, SKILL_SYNONYMS } from './normalize'
import { daysUntil } from './deadline'
import type { MatchResult, RadarOpportunity, StudentProfile } from './types'

const ORD = ['', '1st', '2nd', '3rd', '4th', '5th']

export const WEIGHTS = {
  skillEach: 15,
  skillCap: 45,
  openTheme: 15,
  online: 20,
  sameCity: 25,
  year: 10,
  solo: 5,
  free: 5,
  verified: 5,
} as const

const MAX = WEIGHTS.skillCap + WEIGHTS.sameCity + WEIGHTS.year + WEIGHTS.solo + WEIGHTS.free + WEIGHTS.verified

function displaySkill(tag: string): string {
  if (tag === 'ai/ml') return 'AI/ML'
  if (tag === 'llms') return 'LLMs'
  if (tag === 'dsa') return 'DSA'
  if (tag === 'iot') return 'IoT'
  if (tag === 'c/c++') return 'C/C++'
  if (tag.length <= 3) return tag.toUpperCase()
  return tag.charAt(0).toUpperCase() + tag.slice(1)
}

function listJoin(xs: string[]): string {
  if (xs.length <= 1) return xs.join('')
  return `${xs.slice(0, -1).join(', ')} and ${xs[xs.length - 1]}`
}

/** Profile skills that the listing asks for (canonical tags). */
export function matchedSkills(profile: StudentProfile, opp: RadarOpportunity): string[] {
  const mine = new Set(profile.skills.map(canonicalSkill))
  return opp.tags.filter((t) => mine.has(t) || (SKILL_SYNONYMS[t] ?? []).some((w) => mine.has(w)))
}

export function eligibility(profile: StudentProfile, opp: RadarOpportunity): string[] {
  const blockers: string[] = []
  if (profile.year && opp.years && !opp.years.includes(profile.year)) {
    const allowed = opp.years.map((y) => ORD[y]).join('/')
    blockers.push(`Open to ${allowed} year only; you are in ${ORD[profile.year]} year`)
  }
  if (profile.teamSize && opp.team.min !== null && profile.teamSize < opp.team.min) {
    blockers.push(`Needs a team of at least ${opp.team.min}; you have ${profile.teamSize}`)
  }
  if (profile.teamSize && opp.team.max !== null && profile.teamSize > opp.team.max) {
    blockers.push(`Teams of up to ${opp.team.max}; yours is ${profile.teamSize}`)
  }
  if (opp.audience === 'startups') blockers.push('For registered startups, not individual students')
  return blockers
}

export function scoreOpportunity(profile: StudentProfile, opp: RadarOpportunity, asOf: string): MatchResult {
  const reasons: string[] = []
  const cautions: string[] = []
  let points = 0

  const skills = matchedSkills(profile, opp)
  if (skills.length) {
    points += Math.min(WEIGHTS.skillCap, skills.length * WEIGHTS.skillEach)
    reasons.push(`Asks for ${listJoin(skills.map(displaySkill))}, which you have`)
  } else if (opp.openTheme) {
    points += WEIGHTS.openTheme
    reasons.push('Open theme, so any stack you know counts')
  }

  if (opp.mode === 'online') {
    points += WEIGHTS.online
    reasons.push(opp.kind === 'internship' ? 'Remote, so it fits around classes' : 'Fully online, no travel needed')
  } else if (profile.city && opp.city === profile.city) {
    points += WEIGHTS.sameCity
    reasons.push(
      opp.kind === 'internship'
        ? `Based in ${opp.city}, your city`
        : `${opp.mode === 'hybrid' ? 'Finals' : 'Held'} in ${opp.city}, your city`,
    )
  } else if (opp.mode === 'hybrid') {
    points += WEIGHTS.online / 2
    reasons.push('Hybrid: early rounds are online')
    if (opp.city) cautions.push(`Final round may need travel to ${opp.city}`)
  } else {
    cautions.push(`In person${opp.city ? ` in ${opp.city}` : ''}; plan travel`)
    if (profile.remoteOnly) points -= 15
  }

  if (profile.year && opp.years?.includes(profile.year)) {
    points += WEIGHTS.year
    reasons.push(`Open to ${ORD[profile.year]}-year students like you`)
  }

  if (profile.teamSize === 1 && opp.team.soloOk) {
    points += WEIGHTS.solo
    reasons.push('Solo entries welcome')
  } else if (opp.team.soloOk === null && opp.kind === 'hackathon') {
    cautions.push('Team size not stated; check the rules')
  }

  if (opp.free) points += WEIGHTS.free
  else cautions.push('Entry fee not confirmed')

  if (opp.verified) {
    points += WEIGHTS.verified
  } else {
    cautions.push('Details not yet re-verified')
  }

  if (opp.deadline) {
    const d = daysUntil(opp.deadline, asOf)
    if (d >= 0 && d <= 3) cautions.push(d === 0 ? 'Closes today' : `Closes in ${d} day${d === 1 ? '' : 's'}`)
  }

  const blockers = eligibility(profile, opp)
  cautions.unshift(...blockers)
  const eligible = blockers.length === 0

  let score = Math.round((Math.max(0, points) / MAX) * 100)
  if (!eligible) score = Math.min(score, 25)
  score = Math.max(0, Math.min(100, score))
  const label = score >= 65 ? 'Strong fit' : score >= 40 ? 'Good fit' : 'Stretch'
  return { opportunity: opp, score, label, reasons, cautions, eligible }
}

/** Rank open opportunities for a profile: best fit first, sooner deadline breaks ties. */
export function rankOpportunities(profile: StudentProfile, opps: RadarOpportunity[], asOf: string): MatchResult[] {
  return opps
    .filter((o) => !o.deadline || daysUntil(o.deadline, asOf) >= 0)
    .map((o) => scoreOpportunity(profile, o, asOf))
    .sort((a, b) => {
      if (b.score !== a.score) return b.score - a.score
      return (a.opportunity.deadline ?? '9999').localeCompare(b.opportunity.deadline ?? '9999')
    })
}
