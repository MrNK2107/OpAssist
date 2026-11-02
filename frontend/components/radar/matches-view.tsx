'use client'

import { useMemo, useState } from 'react'
import { applyFilters } from '@/lib/radar/filters'
import { formatDate } from '@/lib/radar/deadline'
import { rankOpportunities, snapshotAge, STALE_AFTER_DAYS } from '@/lib/radar/match'
import { RADAR_OPPORTUNITIES, SNAPSHOT_DATE } from '@/lib/radar/seed'
import { useRadarStore } from '@/stores/radar-store'
import { FilterBar } from './filter-bar'
import { MatchCard } from './match-card'
import { ProfilePanel } from './profile-panel'
import { useToday } from './hooks'

const PAGE = 20

export function MatchesView() {
  const asOf = useToday()
  const profile = useRadarStore((s) => s.profile)
  const filters = useRadarStore((s) => s.filters)
  const board = useRadarStore((s) => s.board)
  const track = useRadarStore((s) => s.track)
  const resetFilters = useRadarStore((s) => s.resetFilters)
  const [limit, setLimit] = useState(PAGE)
  const [showProfile, setShowProfile] = useState(false)

  const ranked = useMemo(
    () => rankOpportunities(profile, applyFilters(RADAR_OPPORTUNITIES, filters, profile), asOf),
    [profile, filters, asOf],
  )
  const strong = ranked.filter((m) => m.label === 'Strong fit').length

  return (
    <div className="grid gap-6 lg:grid-cols-[320px_minmax(0,1fr)]">
      <button
        type="button"
        onClick={() => setShowProfile((v) => !v)}
        aria-expanded={showProfile}
        aria-controls="profile-aside"
        className="flex items-center justify-between gap-3 rounded-2xl border border-border bg-card px-4 py-3 text-left lg:hidden"
      >
        <span className="min-w-0">
          <span className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground">Your profile</span>
          <span className="block truncate text-sm font-medium">
            {[profile.skills.slice(0, 3).join(', ') || 'No skills yet', profile.year ? `Year ${profile.year}` : null, profile.city]
              .filter(Boolean)
              .join(' · ')}
          </span>
        </span>
        <span className="shrink-0 text-sm font-semibold text-amber-700 dark:text-amber-400">{showProfile ? 'Done' : 'Edit'}</span>
      </button>
      <aside id="profile-aside" className={`${showProfile ? '' : 'hidden'} lg:sticky lg:top-24 lg:block lg:self-start`}>
        <ProfilePanel />
      </aside>
      <div className="min-w-0 space-y-4">
        <div>
          <h1 className="font-display text-3xl font-extrabold tracking-tight sm:text-4xl">Ranked for you</h1>
          <p className="mt-1 text-sm text-muted-foreground" aria-live="polite">
            <span className="font-mono font-bold text-foreground">{ranked.length}</span> open listings match your filters ·{' '}
            <span className="font-mono font-bold text-fit">{strong}</span> strong fits. Every score shows its reasons.
          </p>
          <p className="mt-1 text-xs text-muted-foreground">
            Listings hand-checked on <time dateTime={SNAPSHOT_DATE}>{formatDate(SNAPSHOT_DATE)} {SNAPSHOT_DATE.slice(0, 4)}</time>
            {snapshotAge(asOf) > STALE_AFTER_DAYS
              ? '. That is over a month ago: listings without a fixed deadline are hidden and none count as verified.'
              : '.'}
          </p>
        </div>
        <FilterBar />
        {ranked.length === 0 ? (
          <div className="rounded-2xl border border-dashed border-border p-10 text-center">
            <p className="font-display text-lg font-bold">Nothing on the radar with these filters</p>
            <p className="mt-1 text-sm text-muted-foreground">Try turning off &ldquo;I&apos;m eligible&rdquo; or adding a mode back.</p>
            <button type="button" onClick={resetFilters} className="mt-4 rounded-lg bg-ink px-4 py-2 text-sm font-semibold text-paper dark:bg-paper dark:text-ink">
              Reset filters
            </button>
          </div>
        ) : (
          <>
            <ol className="space-y-3">
              {ranked.slice(0, limit).map((m) => (
                <li key={m.opportunity.id}>
                  <MatchCard match={m} asOf={asOf} tracked={Boolean(board[m.opportunity.id])} onTrack={() => track(m.opportunity.id)} />
                </li>
              ))}
            </ol>
            {ranked.length > limit && (
              <button
                type="button"
                onClick={() => setLimit((l) => l + PAGE)}
                className="w-full rounded-xl border border-border py-3 text-sm font-semibold hover:bg-secondary"
              >
                Show {Math.min(PAGE, ranked.length - limit)} more
              </button>
            )}
          </>
        )}
      </div>
    </div>
  )
}
