'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { ArrowRight, Check, CalendarPlus, SlidersHorizontal, SquareKanban, Sparkles, AlertTriangle } from 'lucide-react'
import { RadarMark, Wordmark } from '@/components/brand/radar-mark'
import { buttonVariants } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import { FALLBACK_STATS, ILLUSTRATIVE_NOTE, fetchLandingStats, formatCount, totalLabel, type LandingStats, type LandingType } from '@/lib/landing-stats'
import { RADAR_OPPORTUNITIES, SNAPSHOT_DATE } from '@/lib/radar/seed'
import { formatDate } from '@/lib/radar/deadline'

const CATEGORY_CARDS: { type: LandingType; name: string; blurb: string }[] = [
  { type: 'hackathon', name: 'Hackathons', blurb: 'Devfolio, Unstop, Devpost, MLH, college fests' },
  { type: 'internship', name: 'Internships', blurb: 'Internshala, LinkedIn, company career pages' },
  { type: 'job', name: 'Fresher jobs', blurb: 'Naukri, Cutshort, Wellfound, Instahyre' },
  { type: 'scholarship', name: 'Scholarships', blurb: 'Buddy4Study, government and private schemes' },
  { type: 'oss', name: 'Open source', blurb: 'GSoC, LFX, good-first-issue repos' },
  { type: 'ambassador', name: 'Ambassador programs', blurb: 'Campus roles at tech companies' },
]

const COMPARE: { name: string; good: string; gap: string }[] = [
  { name: 'Unstop', good: 'Huge catalogue of competitions, quizzes and college fests, with registration on-site.', gap: 'Listings only from organisers who post there; ranking is by popularity, not by you.' },
  { name: 'Devfolio', good: 'The home of Indian hackathons, with great builder profiles and project galleries.', gap: 'Hackathons only. No internships, scholarships or deadline view across platforms.' },
  { name: 'Internshala', good: 'The largest internship marketplace for Indian students, with one-click apply.', gap: 'Internships and courses only. Hackathons and open source live elsewhere.' },
  { name: 'LinkedIn', good: 'Recruiter reach and a professional network that matters later.', gap: 'Built for experienced hires. Student eligibility (year, team, fee) is buried in text.' },
]

const SAMPLE = {
  score: 95,
  title: 'AI Engineering & Open-Source Intern',
  org: 'Part-time · Remote',
  reasons: ['Asks for Python, AI/ML and LLMs, which you have', 'Remote, so it fits around classes', 'Open to 2nd-year students like you'],
  caution: 'Only 1-2 openings, so apply early',
}

function HeroRadar() {
  const blips = [
    { x: 268, y: 118, c: 'hsl(var(--fit))', r: 7 },
    { x: 150, y: 96, c: 'hsl(var(--marigold))', r: 5 },
    { x: 300, y: 250, c: 'hsl(var(--marigold))', r: 5 },
    { x: 110, y: 260, c: 'hsl(40 30% 94% / 0.5)', r: 4 },
    { x: 220, y: 320, c: 'hsl(var(--fit))', r: 5 },
    { x: 70, y: 170, c: 'hsl(40 30% 94% / 0.4)', r: 3 },
  ]
  return (
    <svg viewBox="0 0 400 400" className="h-full w-full" aria-hidden>
      {[180, 135, 90, 45].map((r) => (
        <circle key={r} cx="200" cy="200" r={r} fill="none" stroke="hsl(38 92% 50% / 0.18)" strokeWidth="1" />
      ))}
      <line x1="20" y1="200" x2="380" y2="200" stroke="hsl(38 92% 50% / 0.12)" />
      <line x1="200" y1="20" x2="200" y2="380" stroke="hsl(38 92% 50% / 0.12)" />
      <g className="radar-sweep" style={{ transformOrigin: '200px 200px' }}>
        <path d="M200 200 L200 20 A180 180 0 0 1 355.9 110 Z" fill="url(#sweep)" />
        <line x1="200" y1="200" x2="355.9" y2="110" stroke="hsl(38 92% 55%)" strokeWidth="2" strokeLinecap="round" />
      </g>
      <defs>
        <linearGradient id="sweep" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0" stopColor="hsl(38 92% 50% / 0)" />
          <stop offset="1" stopColor="hsl(38 92% 50% / 0.35)" />
        </linearGradient>
      </defs>
      {blips.map((b, i) => (
        <g key={i}>
          <circle cx={b.x} cy={b.y} r={b.r * 2.4} fill={b.c} opacity="0.15" />
          <circle cx={b.x} cy={b.y} r={b.r} fill={b.c} />
        </g>
      ))}
      <circle cx="200" cy="200" r="5" fill="hsl(38 92% 55%)" />
    </svg>
  )
}

function SampleMatch() {
  return (
    <div className="w-full max-w-sm rounded-2xl border border-paper/10 bg-paper p-4 text-ink shadow-2xl shadow-black/40">
      <div className="flex items-start gap-3">
        <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full border-4 border-emerald-600 font-mono text-sm font-bold">{SAMPLE.score}</div>
        <div className="min-w-0">
          <div className="text-[11px] font-semibold uppercase tracking-wider text-emerald-700">Strong fit · example</div>
          <div className="font-display font-bold leading-snug">{SAMPLE.title}</div>
          <div className="text-xs text-ink/60">{SAMPLE.org}</div>
        </div>
      </div>
      <ul className="mt-3 space-y-1 text-[13px]">
        {SAMPLE.reasons.map((r) => (
          <li key={r} className="flex gap-1.5">
            <Check className="mt-0.5 h-3.5 w-3.5 shrink-0 text-emerald-700" aria-hidden />
            {r}
          </li>
        ))}
        <li className="flex gap-1.5 text-ink/60">
          <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0 text-amber-600" aria-hidden />
          {SAMPLE.caution}
        </li>
      </ul>
    </div>
  )
}

const FEATURES = [
  {
    icon: Sparkles,
    title: 'Matches that explain themselves',
    body: 'Tell OpAssist your skills, year and city. Every listing gets a score, and every score shows its reasons: which skills it asks for, whether you can go solo, whether you need to travel.',
    href: '/radar',
    cta: 'See your matches',
  },
  {
    icon: SlidersHorizontal,
    title: 'Eligibility before excitement',
    body: 'Filter by year of study, team size, entry fee and online vs your city. Things you cannot enter are hidden by default, with the reason shown when you look.',
    href: '/radar',
    cta: 'Try the filters',
  },
  {
    icon: CalendarPlus,
    title: 'A deadline radar, not a list',
    body: 'See the next four weeks of closing dates at a glance, then send them to Google, Apple or Outlook Calendar as an .ics file with reminders three days and one day before.',
    href: '/radar/deadlines',
    cta: 'Open the radar',
  },
  {
    icon: SquareKanban,
    title: 'One board for every application',
    body: 'Shortlisted, preparing, applied, heard back. Track hackathons and internships side by side, with notes for teammates, ideas and which resume you sent.',
    href: '/radar/board',
    cta: 'Start a board',
  },
]

export default function Home() {
  const [stats, setStats] = useState<LandingStats>(FALLBACK_STATS)

  useEffect(() => {
    let cancelled = false
    fetchLandingStats().then((s) => {
      if (!cancelled) setStats(s)
    })
    return () => {
      cancelled = true
    }
  }, [])

  const verified = RADAR_OPPORTUNITIES.filter((o) => o.verified).length

  return (
    <div className="min-h-screen bg-background text-foreground">
      <div className="bg-ink text-paper">
        <header className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
          <Link href="/" className="flex items-center gap-2.5" aria-label="OpAssist home">
            <RadarMark className="h-9 w-9 ring-1 ring-paper/10 rounded-lg" />
            <Wordmark onDark className="text-xl text-paper" />
          </Link>
          <nav aria-label="Main" className="hidden items-center gap-8 md:flex">
            <Link href="#features" className="text-sm text-paper/70 hover:text-paper">
              Features
            </Link>
            <Link href="#opportunities" className="text-sm text-paper/70 hover:text-paper">
              Categories
            </Link>
            <Link href="#compare" className="text-sm text-paper/70 hover:text-paper">
              Compare
            </Link>
          </nav>
          <div className="flex items-center gap-3">
            <Link href="/login" className="hidden text-sm font-medium text-paper/70 hover:text-paper sm:inline">
              Sign in
            </Link>
            <Link href="/radar" className={cn(buttonVariants({ size: 'sm' }))}>
              Open the radar
            </Link>
          </div>
        </header>
      </div>

      <main>
        <div className="bg-ink text-paper">
          <section className="mx-auto grid max-w-7xl items-center gap-10 px-4 pb-20 pt-10 sm:px-6 md:pt-16 lg:grid-cols-[1.1fr_1fr] lg:px-8">
            <div>
              <p className="inline-flex items-center gap-2 rounded-full border border-paper/15 px-3 py-1 text-xs font-medium text-paper/80">
                <span className="h-1.5 w-1.5 rounded-full bg-fit" aria-hidden />
                For college students in India
              </p>
              <h1 className="mt-5 font-display text-4xl font-extrabold leading-[1.05] tracking-tight sm:text-5xl lg:text-6xl">
                Every hackathon and internship worth your time, <span className="text-marigold">ranked for you.</span>
              </h1>
              <p className="mt-5 max-w-xl text-lg text-paper/70">
                OpAssist pulls opportunities from the platforms you already check, works out which ones you can actually enter, and tells you why each one fits. Then it keeps the deadlines on your calendar.
              </p>
              <div className="mt-8 flex flex-wrap gap-3">
                <Link href="/radar" className={cn(buttonVariants({ size: 'lg' }), 'gap-2')}>
                  Try it now, no sign-up
                  <ArrowRight className="h-4 w-4" aria-hidden />
                </Link>
                <Link
                  href="/get-started"
                  className={cn(buttonVariants({ variant: 'outline', size: 'lg' }), 'border-paper/20 bg-transparent text-paper hover:bg-paper/10 hover:text-paper')}
                >
                  Create a free account
                </Link>
              </div>
              <p className="mt-6 text-sm text-paper/60">
                Demo radar: <span className="font-mono font-bold text-paper">{RADAR_OPPORTUNITIES.length}</span> real listings,{' '}
                <span className="font-mono font-bold text-paper">{verified}</span> hand-checked on {formatDate(SNAPSHOT_DATE)}.
              </p>
            </div>
            <div className="relative mx-auto aspect-square w-full max-w-[480px]">
              <HeroRadar />
              <div className="absolute inset-x-0 bottom-0 flex justify-center px-2 sm:justify-end">
                <SampleMatch />
              </div>
            </div>
          </section>

          <section id="stats" aria-label="Platform numbers" className="border-t border-paper/10">
            <div className="mx-auto grid max-w-7xl grid-cols-3 gap-4 px-4 py-8 sm:px-6 lg:px-8">
              {[
                { label: totalLabel(stats.live), value: formatCount(stats.total, stats.live) },
                { label: 'Categories', value: String(CATEGORY_CARDS.length) },
                { label: 'Scraper refresh', value: '4–8h' },
              ].map((item) => (
                <div key={item.label}>
                  <div className="font-mono text-2xl font-bold text-marigold sm:text-3xl">{item.value}</div>
                  <div className="mt-1 text-xs text-paper/60 sm:text-sm">{item.label}</div>
                </div>
              ))}
            </div>
            {!stats.live && (
              <p data-testid="stats-illustrative-note" className="mx-auto max-w-7xl px-4 pb-6 text-xs text-paper/50 sm:px-6 lg:px-8">
                {ILLUSTRATIVE_NOTE}
              </p>
            )}
          </section>
        </div>

      <section id="features" className="mx-auto max-w-7xl scroll-mt-8 px-4 py-20 sm:px-6 lg:px-8">
        <h2 className="max-w-2xl font-display text-3xl font-extrabold tracking-tight sm:text-4xl">Stop checking six tabs. Start applying to the right three.</h2>
        <div className="mt-10 grid gap-5 md:grid-cols-2">
          {FEATURES.map((f) => (
            <article key={f.title} className="flex flex-col rounded-2xl border border-border bg-card p-6">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/15 text-amber-700 dark:text-amber-300">
                <f.icon className="h-5 w-5" aria-hidden />
              </div>
              <h3 className="mt-4 font-display text-xl font-bold">{f.title}</h3>
              <p className="mt-2 flex-1 text-muted-foreground">{f.body}</p>
              <Link href={f.href} className="mt-4 inline-flex items-center gap-1 text-sm font-semibold hover:underline">
                {f.cta} <ArrowRight className="h-4 w-4" aria-hidden />
              </Link>
            </article>
          ))}
        </div>
      </section>

      <section id="opportunities" className="border-y border-border bg-secondary/40">
        <div className="mx-auto max-w-7xl px-4 py-20 sm:px-6 lg:px-8">
          <h2 className="font-display text-3xl font-extrabold tracking-tight">Everything a student applies to, in one feed</h2>
          <p className="mt-2 max-w-2xl text-muted-foreground">Signed-in members get the full scraped feed across six categories, refreshed every few hours.</p>
          <div className="mt-8 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {CATEGORY_CARDS.map((type) => (
              <Link
                key={type.type}
                href={`/opportunities?type=${type.type}`}
                className="group rounded-2xl border border-border bg-card p-5 transition-colors hover:border-foreground/30"
              >
                <div className="flex items-baseline justify-between">
                  <span className="font-display text-lg font-bold">{type.name}</span>
                  <span className="font-mono text-sm text-muted-foreground">{formatCount(stats.byType[type.type], stats.live)}</span>
                </div>
                <p className="mt-1 text-sm text-muted-foreground">{type.blurb}</p>
              </Link>
            ))}
          </div>
          {!stats.live && (
            <p className="mt-6 text-xs text-muted-foreground">{ILLUSTRATIVE_NOTE}</p>
          )}
        </div>
      </section>

      <section id="compare" className="mx-auto max-w-7xl scroll-mt-8 px-4 py-20 sm:px-6 lg:px-8">
        <h2 className="font-display text-3xl font-extrabold tracking-tight">Where OpAssist fits</h2>
        <p className="mt-2 max-w-2xl text-muted-foreground">
          These platforms are good at what they do, and you will still apply through them. OpAssist sits on top: it finds the listing, checks you can enter, and keeps the date.
        </p>
        <div className="mt-8 grid gap-4 md:grid-cols-2">
          {COMPARE.map((c) => (
            <article key={c.name} className="rounded-2xl border border-border bg-card p-5">
              <h3 className="font-display text-lg font-bold">{c.name}</h3>
              <p className="mt-2 text-sm">
                <span className="font-semibold text-fit">Great at: </span>
                {c.good}
              </p>
              <p className="mt-1 text-sm text-muted-foreground">
                <span className="font-semibold text-foreground">Leaves open: </span>
                {c.gap}
              </p>
            </article>
          ))}
        </div>
      </section>

      <section className="bg-ink text-paper">
        <div className="mx-auto flex max-w-7xl flex-col items-start gap-6 px-4 py-16 sm:px-6 md:flex-row md:items-center md:justify-between lg:px-8">
          <div>
            <h2 className="font-display text-3xl font-extrabold tracking-tight">Your next win closes soon.</h2>
            <p className="mt-2 text-paper/70">Open the radar, set your skills, and see what fits in under a minute.</p>
          </div>
          <Link href="/radar" className={cn(buttonVariants({ size: 'lg' }), 'gap-2')}>
            Open the radar <ArrowRight className="h-4 w-4" aria-hidden />
          </Link>
        </div>
      </section>
      </main>

      <footer className="border-t border-border">
        <div className="mx-auto grid max-w-7xl gap-8 px-4 py-12 sm:px-6 md:grid-cols-4 lg:px-8">
          <div className="md:col-span-2">
            <div className="flex items-center gap-2">
              <RadarMark className="h-8 w-8" />
              <Wordmark />
            </div>
            <p className="mt-3 max-w-sm text-sm text-muted-foreground">
              The opportunity radar for Indian college students. Always confirm dates on the organiser&apos;s page before you apply.
            </p>
          </div>
          <div>
            <h3 className="text-sm font-semibold">Product</h3>
            <ul className="mt-3 space-y-2 text-sm">
              <li><Link href="/radar" className="text-muted-foreground hover:text-foreground">Radar</Link></li>
              <li><Link href="/radar/deadlines" className="text-muted-foreground hover:text-foreground">Deadline radar</Link></li>
              <li><Link href="/radar/board" className="text-muted-foreground hover:text-foreground">Application board</Link></li>
              <li><Link href="/opportunities" className="text-muted-foreground hover:text-foreground">Full feed</Link></li>
            </ul>
          </div>
          <div>
            <h3 className="text-sm font-semibold">Account</h3>
            <ul className="mt-3 space-y-2 text-sm">
              <li><Link href="/login" className="text-muted-foreground hover:text-foreground">Sign in</Link></li>
              <li><Link href="/get-started" className="text-muted-foreground hover:text-foreground">Sign up</Link></li>
              <li><Link href="/dashboard" className="text-muted-foreground hover:text-foreground">Dashboard</Link></li>
            </ul>
          </div>
        </div>
      </footer>
    </div>
  )
}
