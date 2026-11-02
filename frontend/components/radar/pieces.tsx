'use client'

import { cn } from '@/lib/utils'
import { countdownLabel, daysUntil } from '@/lib/radar/deadline'
import type { RadarMode, RadarKind, MatchResult } from '@/lib/radar/types'

export function Chip({
  pressed,
  onClick,
  children,
  className,
}: {
  pressed: boolean
  onClick: () => void
  children: React.ReactNode
  className?: string
}) {
  return (
    <button
      type="button"
      aria-pressed={pressed}
      onClick={onClick}
      className={cn(
        'inline-flex items-center gap-1 rounded-full border px-3 py-1 text-xs font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring',
        pressed
          ? 'border-ink bg-ink text-paper dark:border-paper dark:bg-paper dark:text-ink'
          : 'border-border bg-card text-muted-foreground hover:border-foreground/30 hover:text-foreground',
        className,
      )}
    >
      {children}
    </button>
  )
}

const LABEL_TONE: Record<MatchResult['label'], string> = {
  'Strong fit': 'text-fit',
  'Good fit': 'text-amber-700 dark:text-amber-400',
  Stretch: 'text-muted-foreground',
}

/** Circular score dial: the number is the match score out of 100. */
export function ScoreDial({ score, label }: { score: number; label: MatchResult['label'] }) {
  const r = 22
  const c = 2 * Math.PI * r
  const stroke = label === 'Strong fit' ? 'hsl(var(--fit))' : label === 'Good fit' ? 'hsl(var(--marigold))' : 'hsl(var(--muted-foreground))'
  return (
    <div className="flex w-16 shrink-0 flex-col items-center">
      <span className="sr-only">{`Match score ${score} out of 100, ${label}`}</span>
      <div className="relative h-14 w-14">
        <svg viewBox="0 0 56 56" className="h-14 w-14 -rotate-90" aria-hidden>
          <circle cx="28" cy="28" r={r} fill="none" stroke="hsl(var(--border))" strokeWidth="5" />
          <circle
            cx="28"
            cy="28"
            r={r}
            fill="none"
            stroke={stroke}
            strokeWidth="5"
            strokeLinecap="round"
            strokeDasharray={`${(score / 100) * c} ${c}`}
          />
        </svg>
        <span className="absolute inset-0 flex items-center justify-center font-mono text-sm font-bold" aria-hidden>
          {score}
        </span>
      </div>
      <span aria-hidden className={cn('mt-1 text-center text-[11px] font-semibold leading-tight', LABEL_TONE[label])}>
        {label}
      </span>
    </div>
  )
}

export function Countdown({ deadline, asOf, className }: { deadline: string | null; asOf: string; className?: string }) {
  const d = deadline ? daysUntil(deadline, asOf) : null
  const tone =
    d === null
      ? 'bg-secondary text-muted-foreground'
      : d <= 3
        ? 'bg-urgent/10 text-red-700 dark:text-red-300'
        : d <= 7
          ? 'bg-primary/15 text-amber-800 dark:text-amber-300'
          : 'bg-secondary text-foreground'
  return (
    <span className={cn('inline-flex items-center rounded-full px-2 py-0.5 font-mono text-[11px] font-bold', tone, className)}>
      {countdownLabel(deadline, asOf)}
    </span>
  )
}

export const MODE_LABEL: Record<RadarMode, string> = { online: 'Online', hybrid: 'Hybrid', 'in-person': 'In person' }
export const KIND_LABEL: Record<RadarKind, string> = { hackathon: 'Hackathon', internship: 'Internship' }

export function Tag({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <span className={cn('inline-flex items-center rounded-md border border-border px-1.5 py-0.5 text-[11px] font-medium text-muted-foreground', className)}>
      {children}
    </span>
  )
}
