'use client'

import { Check, AlertTriangle, CalendarPlus, ExternalLink, Plus, SquareKanban } from 'lucide-react'
import { cn } from '@/lib/utils'
import { formatDate } from '@/lib/radar/deadline'
import { downloadIcs } from '@/lib/radar/ics'
import type { MatchResult } from '@/lib/radar/types'
import { Countdown, KIND_LABEL, MODE_LABEL, ScoreDial, Tag } from './pieces'

export function MatchCard({
  match,
  asOf,
  tracked,
  onTrack,
}: {
  match: MatchResult
  asOf: string
  tracked: boolean
  onTrack: () => void
}) {
  const o = match.opportunity
  return (
    <article
      className={cn(
        'group flex gap-4 rounded-2xl border border-border bg-card p-4 transition-shadow hover:shadow-[0_6px_24px_-12px_hsl(var(--ink)/0.25)] sm:p-5',
        !match.eligible && 'opacity-70',
      )}
      aria-labelledby={`t-${o.id}`}
    >
      <ScoreDial score={match.score} label={match.label} />
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center gap-1.5">
          <Tag className={o.kind === 'internship' ? 'border-fit/40 text-fit' : 'border-amber-500/40 text-amber-800 dark:text-amber-300'}>
            {KIND_LABEL[o.kind]}
          </Tag>
          <Tag>
            {MODE_LABEL[o.mode]}
            {o.city && o.mode !== 'online' ? ` · ${o.city}` : ''}
          </Tag>
          <Countdown deadline={o.deadline} asOf={asOf} />
          {o.deadline && <span className="text-[11px] text-muted-foreground">closes {formatDate(o.deadline)}</span>}
        </div>
        <h2 id={`t-${o.id}`} className="mt-2 font-display text-lg font-bold leading-snug">
          {o.title}
        </h2>
        <p className="mt-0.5 truncate text-sm text-muted-foreground">
          {o.organizer}
          {o.reward && !/^not (stated|listed)/i.test(o.reward) ? ` · ${o.reward}` : ''}
        </p>

        <div className="mt-3 grid gap-x-6 gap-y-1 sm:grid-cols-2">
          {match.reasons.length > 0 && (
            <ul aria-label="Why this fits" className="space-y-1">
              {match.reasons.map((r) => (
                <li key={r} className="flex items-start gap-1.5 text-sm">
                  <Check className="mt-0.5 h-4 w-4 shrink-0 text-fit" aria-hidden />
                  <span>{r}</span>
                </li>
              ))}
            </ul>
          )}
          {match.cautions.length > 0 && (
            <ul aria-label="Check before applying" className="space-y-1">
              {match.cautions.map((c) => (
                <li key={c} className="flex items-start gap-1.5 text-sm text-muted-foreground">
                  <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-amber-600" aria-hidden />
                  <span>{c}</span>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="mt-4 flex flex-wrap items-center gap-2">
          <button
            type="button"
            onClick={onTrack}
            disabled={tracked}
            className={cn(
              'inline-flex h-8 items-center gap-1.5 rounded-lg px-3 text-xs font-semibold transition-colors',
              tracked ? 'bg-fit/10 text-fit' : 'bg-ink text-paper hover:bg-ink/90 dark:bg-paper dark:text-ink',
            )}
          >
            {tracked ? <SquareKanban className="h-3.5 w-3.5" aria-hidden /> : <Plus className="h-3.5 w-3.5" aria-hidden />}
            {tracked ? 'On your board' : 'Track'}
          </button>
          {o.deadline && (
            <button
              type="button"
              onClick={() => downloadIcs([o], `${o.id}.ics`)}
              className="inline-flex h-8 items-center gap-1.5 rounded-lg border border-border px-3 text-xs font-semibold hover:bg-secondary"
            >
              <CalendarPlus className="h-3.5 w-3.5" aria-hidden />
              Add to calendar
            </button>
          )}
          <a
            href={o.url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex h-8 items-center gap-1.5 rounded-lg px-2 text-xs font-semibold text-muted-foreground hover:text-foreground"
          >
            Organiser page
            <ExternalLink className="h-3.5 w-3.5" aria-hidden />
            <span className="sr-only">(opens in a new tab)</span>
          </a>
        </div>
      </div>
    </article>
  )
}
