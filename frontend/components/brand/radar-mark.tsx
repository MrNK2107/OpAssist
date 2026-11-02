import { cn } from '@/lib/utils'

/**
 * The OpAssist mark: an ink tile with a marigold radar sweep and one blip.
 * The blip is the opportunity that fits you; the sweep is OpAssist looking.
 */
export function RadarMark({ className, animated = false, title }: { className?: string; animated?: boolean; title?: string }) {
  return (
    <svg
      viewBox="0 0 32 32"
      className={cn('h-9 w-9 shrink-0', className)}
      role={title ? 'img' : undefined}
      aria-hidden={title ? undefined : true}
      aria-label={title}
    >
      <rect width="32" height="32" rx="8" fill="hsl(228 45% 10%)" />
      <circle cx="16" cy="16" r="10" fill="none" stroke="hsl(38 92% 50% / 0.35)" strokeWidth="1.2" />
      <circle cx="16" cy="16" r="5.5" fill="none" stroke="hsl(38 92% 50% / 0.55)" strokeWidth="1.2" />
      <g className={animated ? 'radar-sweep' : undefined}>
        <path d="M16 16 L16 6 A10 10 0 0 1 24.66 11 Z" fill="hsl(38 92% 50% / 0.35)" />
        <line x1="16" y1="16" x2="24.66" y2="11" stroke="hsl(38 92% 55%)" strokeWidth="1.6" strokeLinecap="round" />
      </g>
      <circle cx="16" cy="16" r="1.6" fill="hsl(38 92% 55%)" />
      <circle cx="21.5" cy="9.6" r="2" fill="hsl(160 60% 50%)" />
    </svg>
  )
}

export function Wordmark({ className, onDark = false }: { className?: string; onDark?: boolean }) {
  return (
    <span className={cn('font-display text-lg font-bold tracking-tight', className)}>
      Op<span className={onDark ? 'text-amber-400' : 'text-amber-700 dark:text-amber-400'}>Assist</span>
    </span>
  )
}
