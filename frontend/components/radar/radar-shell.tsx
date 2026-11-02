'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { RadarMark, Wordmark } from '@/components/brand/radar-mark'
import { buttonVariants } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import { formatDate } from '@/lib/radar/deadline'
import { RADAR_OPPORTUNITIES, SNAPSHOT_DATE } from '@/lib/radar/seed'
import { useRadarStore } from '@/stores/radar-store'
import { useRadarHydration } from './hooks'

export const RADAR_TABS = [
  { href: '/radar', label: 'Matches' },
  { href: '/radar/deadlines', label: 'Deadline radar' },
  { href: '/radar/board', label: 'Board' },
] as const

export function RadarShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname()
  const hydrated = useRadarHydration()
  const tracked = useRadarStore((s) => Object.keys(s.board).length)

  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="sticky top-0 z-40 border-b border-border bg-background/90 backdrop-blur">
        <div className="mx-auto flex h-16 max-w-7xl items-center gap-4 px-4 sm:px-6">
          <Link href="/" className="flex items-center gap-2" aria-label="OpAssist home">
            <RadarMark className="h-8 w-8" />
            <Wordmark className="hidden sm:inline" />
          </Link>
          <nav aria-label="Radar sections" className="flex flex-1 items-center gap-1 overflow-x-auto">
            {RADAR_TABS.map((t) => {
              const active = pathname === t.href
              return (
                <Link
                  key={t.href}
                  href={t.href}
                  aria-current={active ? 'page' : undefined}
                  className={cn(
                    'whitespace-nowrap rounded-full px-3 py-1.5 text-sm font-medium transition-colors',
                    active ? 'bg-ink text-paper dark:bg-paper dark:text-ink' : 'text-muted-foreground hover:bg-secondary hover:text-foreground',
                  )}
                >
                  {t.label}
                  {t.href === '/radar/board' && hydrated && tracked > 0 && (
                    <span className="ml-1.5 rounded-full bg-primary px-1.5 font-mono text-[11px] text-primary-foreground">{tracked}</span>
                  )}
                </Link>
              )
            })}
          </nav>
          <Link href="/login" className="hidden text-sm font-medium text-muted-foreground hover:text-foreground md:inline">
            Sign in
          </Link>
          <Link href="/get-started" className={cn(buttonVariants({ size: 'sm' }), 'hidden sm:inline-flex')}>
            Save my radar
          </Link>
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-4 pb-16 pt-6 sm:px-6">{children}</main>
      <footer className="border-t border-border">
        <div className="mx-auto max-w-7xl px-4 py-6 text-xs text-muted-foreground sm:px-6">
          Demo snapshot of {RADAR_OPPORTUNITIES.length} public listings, hand-checked on {formatDate(SNAPSHOT_DATE)} {SNAPSHOT_DATE.slice(0, 4)}.
          Deadlines change: always confirm on the organiser&apos;s page before you apply. Your profile and board stay in this browser.
        </div>
      </footer>
    </div>
  )
}
