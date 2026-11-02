// Deadline maths. Deadlines are calendar dates in IST; we compare whole days
// so "closes today" means the same thing everywhere in India.

export type Bucket = 'closed' | 'today' | 'this-week' | 'next-two-weeks' | 'later' | 'rolling'

export const BUCKET_ORDER: Bucket[] = ['today', 'this-week', 'next-two-weeks', 'later', 'rolling', 'closed']

export const BUCKET_LABEL: Record<Bucket, string> = {
  today: 'Closes today',
  'this-week': 'This week',
  'next-two-weeks': 'Next two weeks',
  later: 'Later',
  rolling: 'Rolling / no fixed date',
  closed: 'Closed',
}

const DAY = 86_400_000

/** Today's date in IST as YYYY-MM-DD. */
export function todayIST(now: Date = new Date()): string {
  return new Date(now.getTime() + 5.5 * 3600_000).toISOString().slice(0, 10)
}

function dayNumber(iso: string): number {
  const [y, m, d] = iso.split('-').map(Number)
  return Date.UTC(y, m - 1, d) / DAY
}

/** Whole days from `asOf` to `deadline` (0 = today, negative = past). */
export function daysUntil(deadline: string, asOf: string): number {
  return dayNumber(deadline) - dayNumber(asOf)
}

export function bucketFor(deadline: string | null, asOf: string): Bucket {
  if (!deadline) return 'rolling'
  const d = daysUntil(deadline, asOf)
  if (d < 0) return 'closed'
  if (d === 0) return 'today'
  if (d <= 7) return 'this-week'
  if (d <= 21) return 'next-two-weeks'
  return 'later'
}

export function countdownLabel(deadline: string | null, asOf: string): string {
  if (!deadline) return 'Rolling'
  const d = daysUntil(deadline, asOf)
  if (d < 0) return 'Closed'
  if (d === 0) return 'Closes today'
  if (d === 1) return '1 day left'
  return `${d} days left`
}

export function formatDate(iso: string): string {
  const [y, m, d] = iso.split('-').map(Number)
  return new Date(Date.UTC(y, m - 1, d)).toLocaleDateString('en-IN', {
    day: 'numeric',
    month: 'short',
    timeZone: 'UTC',
  })
}

export function groupByBucket<T extends { deadline: string | null }>(items: T[], asOf: string): Record<Bucket, T[]> {
  const groups = Object.fromEntries(BUCKET_ORDER.map((b) => [b, [] as T[]])) as Record<Bucket, T[]>
  for (const it of items) groups[bucketFor(it.deadline, asOf)].push(it)
  for (const b of BUCKET_ORDER) {
    groups[b].sort((a, z) => (a.deadline ?? '9999').localeCompare(z.deadline ?? '9999'))
  }
  return groups
}

/** Day-by-day counts for the next `days` days, for the radar strip. */
export function deadlineStrip<T extends { deadline: string | null }>(items: T[], asOf: string, days = 28) {
  const start = dayNumber(asOf)
  return Array.from({ length: days }, (_, i) => {
    const date = new Date((start + i) * DAY).toISOString().slice(0, 10)
    return { date, offset: i, items: items.filter((it) => it.deadline === date) }
  })
}
