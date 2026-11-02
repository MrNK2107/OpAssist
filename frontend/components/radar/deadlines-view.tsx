'use client'

import { useMemo } from 'react'
import Link from 'next/link'
import { CalendarPlus, Plus, Check } from 'lucide-react'
import { cn } from '@/lib/utils'
import { BUCKET_LABEL, BUCKET_ORDER, deadlineStrip, formatDate, groupByBucket } from '@/lib/radar/deadline'
import { applyFilters } from '@/lib/radar/filters'
import { downloadIcs, exportableDeadlines } from '@/lib/radar/ics'
import { RADAR_OPPORTUNITIES } from '@/lib/radar/seed'
import type { RadarOpportunity } from '@/lib/radar/types'
import { useRadarStore } from '@/stores/radar-store'
import { Countdown, KIND_LABEL, MODE_LABEL } from './pieces'
import { useToday } from './hooks'

const WEEKDAY = ['S', 'M', 'T', 'W', 'T', 'F', 'S']

function Strip({ items, asOf }: { items: RadarOpportunity[]; asOf: string }) {
  const days = deadlineStrip(items, asOf, 28)
  const max = Math.max(1, ...days.map((d) => d.items.length))
  return (
    <figure className="rounded-2xl border border-border bg-ink p-4 text-paper sm:p-6">
      <figcaption className="flex flex-wrap items-baseline justify-between gap-2">
        <span className="font-display text-lg font-bold">Next 4 weeks</span>
        <span className="text-xs text-paper/60">Each bar is one day. Taller means more deadlines.</span>
      </figcaption>
      <div className="mt-5 grid grid-cols-[repeat(28,minmax(0,1fr))] items-end gap-[3px] sm:gap-1" style={{ height: 120 }}>
        {days.map((d) => {
          const n = d.items.length
          const h = n === 0 ? 4 : 16 + (n / max) * 96
          const wk = d.offset < 7
          return (
            <div key={d.date} className="flex h-full flex-col justify-end" title={`${formatDate(d.date)}: ${n} deadline${n === 1 ? '' : 's'}`}>
              <div
                className={cn('w-full rounded-sm', n === 0 ? 'bg-paper/15' : wk ? 'bg-urgent' : 'bg-marigold')}
                style={{ height: h }}
              />
            </div>
          )
        })}
      </div>
      <div className="mt-2 grid grid-cols-[repeat(28,minmax(0,1fr))] gap-[3px] font-mono text-[9px] text-paper/50 sm:gap-1 sm:text-[10px]" aria-hidden>
        {days.map((d) => {
          const [y, m, dd] = d.date.split('-').map(Number)
          const wd = new Date(Date.UTC(y, m - 1, dd)).getUTCDay()
          return (
            <span key={d.date} className={cn('text-center', d.offset === 0 && 'font-bold text-marigold')}>
              {d.offset % 7 === 0 ? dd : WEEKDAY[wd]}
            </span>
          )
        })}
      </div>
      <p className="sr-only">
        {days
          .filter((d) => d.items.length)
          .map((d) => `${formatDate(d.date)}: ${d.items.length}`)
          .join('; ')}
      </p>
      <div className="mt-4 flex flex-wrap gap-4 text-xs text-paper/70">
        <span className="inline-flex items-center gap-1.5">
          <span className="h-2.5 w-2.5 rounded-sm bg-urgent" /> This week
        </span>
        <span className="inline-flex items-center gap-1.5">
          <span className="h-2.5 w-2.5 rounded-sm bg-marigold" /> Later
        </span>
      </div>
    </figure>
  )
}

export function DeadlinesView() {
  const asOf = useToday()
  const profile = useRadarStore((s) => s.profile)
  const filters = useRadarStore((s) => s.filters)
  const board = useRadarStore((s) => s.board)
  const track = useRadarStore((s) => s.track)

  const items = useMemo(() => applyFilters(RADAR_OPPORTUNITIES, filters, profile), [filters, profile])
  const groups = useMemo(() => groupByBucket(items, asOf), [items, asOf])
  const upcoming = BUCKET_ORDER.filter((b) => b !== 'closed' && b !== 'rolling').flatMap((b) => groups[b])
  const boardOpps = exportableDeadlines(
    RADAR_OPPORTUNITIES.filter((o) => board[o.id]),
    asOf,
  )

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="font-display text-3xl font-extrabold tracking-tight sm:text-4xl">Deadline radar</h1>
          <p className="mt-1 max-w-xl text-sm text-muted-foreground">
            Every closing date that passes your filters on{' '}
            <Link href="/radar" className="font-medium text-foreground underline underline-offset-2">
              Matches
            </Link>
            . Export to Google, Apple or Outlook Calendar with reminders 3 days and 1 day before.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            disabled={boardOpps.length === 0}
            onClick={() => downloadIcs(boardOpps, 'opassist-my-board.ics')}
            className="inline-flex h-9 items-center gap-1.5 rounded-lg border border-border px-3 text-sm font-semibold hover:bg-secondary disabled:opacity-50"
          >
            <CalendarPlus className="h-4 w-4" aria-hidden /> My board ({boardOpps.length})
          </button>
          <button
            type="button"
            disabled={upcoming.length === 0}
            onClick={() => downloadIcs(upcoming, 'opassist-deadlines.ics')}
            className="inline-flex h-9 items-center gap-1.5 rounded-lg bg-primary px-3 text-sm font-semibold text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
          >
            <CalendarPlus className="h-4 w-4" aria-hidden /> All {upcoming.length} to calendar
          </button>
        </div>
      </div>

      <Strip items={items} asOf={asOf} />

      <div className="gap-6 lg:columns-2">
        {BUCKET_ORDER.filter((b) => b !== 'closed' && groups[b].length > 0).map((b) => (
          <section key={b} aria-labelledby={`b-${b}`} className="mb-6 break-inside-avoid rounded-2xl border border-border bg-card">
            <h2 id={`b-${b}`} className="flex items-center justify-between border-b border-border px-4 py-3 font-display font-bold">
              {BUCKET_LABEL[b]}
              <span className="font-mono text-xs text-muted-foreground">{groups[b].length}</span>
            </h2>
            <ul className="divide-y divide-border">
              {groups[b].map((o) => (
                <li key={o.id} className="flex items-center gap-3 px-4 py-2.5">
                  <div className="w-12 shrink-0 text-center font-mono text-xs font-bold">{o.deadline ? formatDate(o.deadline) : '—'}</div>
                  <div className="min-w-0 flex-1">
                    <a href={o.url} target="_blank" rel="noopener noreferrer" className="block truncate text-sm font-semibold hover:underline">
                      {o.title}
                    </a>
                    <div className="truncate text-xs text-muted-foreground">
                      {KIND_LABEL[o.kind]} · {MODE_LABEL[o.mode]} · {o.organizer}
                    </div>
                  </div>
                  <Countdown deadline={o.deadline} asOf={asOf} className="hidden sm:inline-flex" />
                  <button
                    type="button"
                    onClick={() => track(o.id)}
                    disabled={Boolean(board[o.id])}
                    aria-label={board[o.id] ? `${o.title} is on your board` : `Track ${o.title}`}
                    className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md border border-border hover:bg-secondary disabled:border-transparent disabled:text-fit"
                  >
                    {board[o.id] ? <Check className="h-4 w-4" aria-hidden /> : <Plus className="h-4 w-4" aria-hidden />}
                  </button>
                </li>
              ))}
            </ul>
          </section>
        ))}
      </div>
    </div>
  )
}
