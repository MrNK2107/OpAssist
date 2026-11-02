'use client'

import { Search } from 'lucide-react'
import { toggle } from '@/lib/radar/filters'
import type { RadarKind, RadarMode } from '@/lib/radar/types'
import { useRadarStore } from '@/stores/radar-store'
import { Chip, KIND_LABEL, MODE_LABEL } from './pieces'

const KINDS: RadarKind[] = ['hackathon', 'internship']
const MODES: RadarMode[] = ['online', 'hybrid', 'in-person']

export function FilterBar() {
  const f = useRadarStore((s) => s.filters)
  const set = useRadarStore((s) => s.setFilters)
  const city = useRadarStore((s) => s.profile.city)

  return (
    <div className="space-y-3 rounded-2xl border border-border bg-card p-4" role="group" aria-label="Filters">
      <div className="relative">
        <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" aria-hidden />
        <label htmlFor="radar-q" className="sr-only">
          Search listings
        </label>
        <input
          id="radar-q"
          type="search"
          value={f.query}
          onChange={(e) => set({ query: e.target.value })}
          placeholder="Search: title, organiser, skill or city"
          className="h-10 w-full rounded-xl border border-input bg-background pl-9 pr-3 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
        />
      </div>
      <div className="flex flex-wrap items-center gap-1.5">
        {KINDS.map((k) => (
          <Chip key={k} pressed={f.kinds.includes(k)} onClick={() => set({ kinds: toggle(f.kinds, k) })}>
            {KIND_LABEL[k]}s
          </Chip>
        ))}
        <span className="mx-1 h-4 w-px bg-border" aria-hidden />
        {MODES.map((m) => (
          <Chip key={m} pressed={f.modes.includes(m)} onClick={() => set({ modes: toggle(f.modes, m) })}>
            {MODE_LABEL[m]}
          </Chip>
        ))}
        <span className="mx-1 h-4 w-px bg-border" aria-hidden />
        <Chip pressed={f.freeOnly} onClick={() => set({ freeOnly: !f.freeOnly })}>
          Free entry
        </Chip>
        <Chip pressed={f.eligibleOnly} onClick={() => set({ eligibleOnly: !f.eligibleOnly })}>
          I&apos;m eligible
        </Chip>
        <Chip pressed={f.nearMeOnly} onClick={() => set({ nearMeOnly: !f.nearMeOnly })}>
          {city ? `Online or ${city}` : 'Online or my city'}
        </Chip>
      </div>
    </div>
  )
}
