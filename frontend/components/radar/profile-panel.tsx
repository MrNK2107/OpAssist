'use client'

import { useState } from 'react'
import { RotateCcw, X } from 'lucide-react'
import { canonicalSkill, CITY_NAMES, SKILL_TAGS } from '@/lib/radar/normalize'
import { useRadarStore } from '@/stores/radar-store'
import { Chip } from './pieces'

const QUICK_SKILLS = ['Python', 'React', 'AI/ML', 'LLMs', 'Web dev', 'DSA', 'Java', 'Data science', 'Blockchain', 'Design', 'Mobile', 'Cloud']
const YEARS = [1, 2, 3, 4, 5]

function same(a: string, b: string) {
  return canonicalSkill(a) === canonicalSkill(b)
}

export function ProfilePanel() {
  const profile = useRadarStore((s) => s.profile)
  const customised = useRadarStore((s) => s.customised)
  const setProfile = useRadarStore((s) => s.setProfile)
  const resetProfile = useRadarStore((s) => s.resetProfile)
  const [draft, setDraft] = useState('')

  const hasSkill = (k: string) => profile.skills.some((s) => same(s, k))
  const toggleSkill = (k: string) =>
    setProfile({ skills: hasSkill(k) ? profile.skills.filter((s) => !same(s, k)) : [...profile.skills, k] })

  const addDraft = () => {
    const v = draft.trim()
    if (v && !hasSkill(v)) setProfile({ skills: [...profile.skills, v.slice(0, 30)] })
    setDraft('')
  }
  const custom = profile.skills.filter((s) => !QUICK_SKILLS.some((q) => same(q, s)))

  return (
    <section aria-labelledby="profile-h" className="rounded-2xl border border-border bg-card p-5">
      <div className="flex items-start justify-between gap-2">
        <div>
          <h2 id="profile-h" className="font-display text-lg font-bold">
            Your profile
          </h2>
          <p className="text-xs text-muted-foreground">
            {customised ? 'Saved in this browser.' : 'A sample student. Change anything and the ranking updates.'}
          </p>
        </div>
        {customised && (
          <button
            type="button"
            onClick={resetProfile}
            className="inline-flex items-center gap-1 rounded-md px-2 py-1 text-xs text-muted-foreground hover:bg-secondary hover:text-foreground"
          >
            <RotateCcw className="h-3 w-3" aria-hidden /> Sample
          </button>
        )}
      </div>

      <fieldset className="mt-4">
        <legend className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Skills</legend>
        <div className="mt-2 flex flex-wrap gap-1.5">
          {QUICK_SKILLS.map((k) => (
            <Chip key={k} pressed={hasSkill(k)} onClick={() => toggleSkill(k)}>
              {k}
            </Chip>
          ))}
          {custom.map((k) => (
            <Chip key={k} pressed onClick={() => toggleSkill(k)}>
              {k} <X className="h-3 w-3" aria-label="remove" />
            </Chip>
          ))}
        </div>
        <form
          className="mt-2 flex gap-1.5"
          onSubmit={(e) => {
            e.preventDefault()
            addDraft()
          }}
        >
          <label htmlFor="skill-add" className="sr-only">
            Add another skill
          </label>
          <input
            id="skill-add"
            list="skill-vocab"
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            placeholder="Add a skill, e.g. Flutter"
            className="h-8 min-w-0 flex-1 rounded-lg border border-input bg-background px-2.5 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
          />
          <datalist id="skill-vocab">
            {SKILL_TAGS.map((t) => (
              <option key={t} value={t} />
            ))}
          </datalist>
          <button type="submit" className="h-8 rounded-lg border border-border px-3 text-xs font-semibold hover:bg-secondary">
            Add
          </button>
        </form>
      </fieldset>

      <fieldset className="mt-5">
        <legend className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Year of study</legend>
        <div className="mt-2 flex gap-1.5">
          {YEARS.map((y) => (
            <Chip key={y} pressed={profile.year === y} onClick={() => setProfile({ year: profile.year === y ? null : y })} className="w-10 justify-center font-mono">
              {y}
            </Chip>
          ))}
        </div>
      </fieldset>

      <div className="mt-5 grid grid-cols-2 gap-3">
        <div>
          <label htmlFor="city" className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            City
          </label>
          <select
            id="city"
            value={profile.city ?? ''}
            onChange={(e) => setProfile({ city: e.target.value || null })}
            className="mt-2 h-9 w-full rounded-lg border border-input bg-background px-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
          >
            <option value="">Anywhere</option>
            {CITY_NAMES.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label htmlFor="team" className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            Team size
          </label>
          <select
            id="team"
            value={profile.teamSize ?? ''}
            onChange={(e) => setProfile({ teamSize: e.target.value ? Number(e.target.value) : null })}
            className="mt-2 h-9 w-full rounded-lg border border-input bg-background px-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
          >
            <option value="">Flexible</option>
            <option value="1">Just me</option>
            {[2, 3, 4, 5, 6].map((n) => (
              <option key={n} value={n}>
                {n} people
              </option>
            ))}
          </select>
        </div>
      </div>

      <label className="mt-5 flex cursor-pointer items-center justify-between gap-3 text-sm">
        <span>
          <span className="font-medium">No travel</span>
          <span className="block text-xs text-muted-foreground">Rank online and nearby events higher</span>
        </span>
        <input
          type="checkbox"
          checked={profile.remoteOnly}
          onChange={(e) => setProfile({ remoteOnly: e.target.checked })}
          className="h-4 w-4 accent-amber-500"
        />
      </label>
    </section>
  )
}
