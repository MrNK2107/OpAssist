'use client'

import Link from 'next/link'
import { ChevronLeft, ChevronRight, Trash2, CalendarPlus } from 'lucide-react'
import { cn } from '@/lib/utils'
import { columns, STAGES } from '@/lib/radar/board'
import { downloadIcs, exportableDeadlines } from '@/lib/radar/ics'
import { byId } from '@/lib/radar/seed'
import { useRadarStore } from '@/stores/radar-store'
import { Countdown, KIND_LABEL } from './pieces'
import { useRadarHydration, useToday } from './hooks'

const STAGE_TONE = ['border-t-muted-foreground/40', 'border-t-marigold', 'border-t-ink dark:border-t-paper', 'border-t-fit']

export function BoardView() {
  const hydrated = useRadarHydration()
  const asOf = useToday()
  const board = useRadarStore((s) => s.board)
  const step = useRadarStore((s) => s.step)
  const untrack = useRadarStore((s) => s.untrack)
  const note = useRadarStore((s) => s.note)
  const cols = columns(board)
  const total = Object.keys(board).length
  const withDeadline = exportableDeadlines(
    Object.keys(board)
      .map(byId)
      .filter((o): o is NonNullable<typeof o> => Boolean(o)),
    asOf,
  )

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="font-display text-3xl font-extrabold tracking-tight sm:text-4xl">Application board</h1>
          <p className="mt-1 max-w-xl text-sm text-muted-foreground">
            Track what you are going for, from shortlist to result. Move cards with the arrows; notes stay with the card.
          </p>
        </div>
        <button
          type="button"
          disabled={withDeadline.length === 0}
          onClick={() => downloadIcs(withDeadline, 'opassist-my-board.ics')}
          className="inline-flex h-9 items-center gap-1.5 rounded-lg bg-primary px-3 text-sm font-semibold text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
        >
          <CalendarPlus className="h-4 w-4" aria-hidden /> Board deadlines to calendar
        </button>
      </div>

      {hydrated && total === 0 ? (
        <div className="rounded-2xl border border-dashed border-border p-10 text-center">
          <p className="font-display text-lg font-bold">Your board is empty</p>
          <p className="mt-1 text-sm text-muted-foreground">Press Track on any match to start your shortlist.</p>
          <Link href="/radar" className="mt-4 inline-block rounded-lg bg-ink px-4 py-2 text-sm font-semibold text-paper dark:bg-paper dark:text-ink">
            Find matches
          </Link>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {STAGES.map((stage, i) => (
            <section
              key={stage.id}
              aria-labelledby={`col-${stage.id}`}
              className={cn('flex min-h-[220px] flex-col rounded-2xl border border-border border-t-4 bg-secondary/40', STAGE_TONE[i])}
            >
              <header className="flex items-baseline justify-between px-4 pb-2 pt-3">
                <h2 id={`col-${stage.id}`} className="font-display font-bold">
                  {stage.label}
                </h2>
                <span className="font-mono text-xs text-muted-foreground">{cols[stage.id].length}</span>
              </header>
              <p className="px-4 text-xs text-muted-foreground">{stage.hint}</p>
              <ul className="flex flex-1 flex-col gap-2 p-3">
                {cols[stage.id].map((card) => {
                  const o = byId(card.id)
                  if (!o) return null
                  return (
                    <li key={card.id} className="rounded-xl border border-border bg-card p-3 shadow-sm">
                      <div className="flex items-center justify-between gap-2">
                        <span className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">{KIND_LABEL[o.kind]}</span>
                        <Countdown deadline={o.deadline} asOf={asOf} />
                      </div>
                      <a href={o.url} target="_blank" rel="noopener noreferrer" className="mt-1 block text-sm font-semibold leading-snug hover:underline">
                        {o.title}
                      </a>
                      <p className="truncate text-xs text-muted-foreground">{o.organizer}</p>
                      <label htmlFor={`note-${card.id}`} className="sr-only">
                        Note for {o.title}
                      </label>
                      <textarea
                        id={`note-${card.id}`}
                        value={card.note}
                        onChange={(e) => note(card.id, e.target.value)}
                        placeholder="Note: teammate, idea, resume version…"
                        rows={2}
                        className="mt-2 w-full resize-none rounded-lg border border-input bg-background px-2 py-1 text-xs placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                      />
                      <div className="mt-2 flex items-center justify-between">
                        <div className="flex gap-1">
                          <button
                            type="button"
                            onClick={() => step(card.id, -1)}
                            disabled={i === 0}
                            aria-label={`Move ${o.title} back to ${STAGES[Math.max(0, i - 1)].label}`}
                            className="flex h-7 w-7 items-center justify-center rounded-md border border-border hover:bg-secondary disabled:opacity-30"
                          >
                            <ChevronLeft className="h-4 w-4" aria-hidden />
                          </button>
                          <button
                            type="button"
                            onClick={() => step(card.id, 1)}
                            disabled={i === STAGES.length - 1}
                            aria-label={`Move ${o.title} forward to ${STAGES[Math.min(STAGES.length - 1, i + 1)].label}`}
                            className="flex h-7 w-7 items-center justify-center rounded-md border border-border hover:bg-secondary disabled:opacity-30"
                          >
                            <ChevronRight className="h-4 w-4" aria-hidden />
                          </button>
                        </div>
                        <button
                          type="button"
                          onClick={() => untrack(card.id)}
                          aria-label={`Remove ${o.title} from board`}
                          className="flex h-7 w-7 items-center justify-center rounded-md text-muted-foreground hover:bg-urgent/10 hover:text-urgent"
                        >
                          <Trash2 className="h-4 w-4" aria-hidden />
                        </button>
                      </div>
                    </li>
                  )
                })}
              </ul>
            </section>
          ))}
        </div>
      )}
    </div>
  )
}
