// RFC 5545 calendar export. Each deadline becomes an all-day event with two
// reminders (3 days and 1 day before) so it lands in Google, Apple or Outlook
// calendars without any account linking.

import { daysUntil } from './deadline'
import { safeHttpsUrl } from './normalize'
import { SNAPSHOT_DATE } from './seed'
import type { RadarOpportunity } from './types'

const CRLF = '\r\n'

/** Escape TEXT values (RFC 5545 section 3.3.11). CRLF, lone LF and lone CR all become an
 * escaped newline, so no input can end a content line and start a property of its own. */
export function escapeText(s: string): string {
  return s.replace(/\\/g, '\\\\').replace(/;/g, '\\;').replace(/,/g, '\\,').replace(/\r\n|\r|\n/g, '\\n')
}

/** Deadlines worth putting in a calendar: dated and not yet passed (today counts). */
export function exportableDeadlines<T extends { deadline: string | null }>(opps: T[], asOf: string): T[] {
  return opps.filter((o) => o.deadline !== null && daysUntil(o.deadline, asOf) >= 0)
}

const SEQUENCE_EPOCH = '2026-01-01'

/** Revision number for every event in a snapshot: days since a fixed epoch, so a newer
 * snapshot always carries a higher SEQUENCE and calendar apps replace the older copy. */
export function snapshotSequence(snapshotDate: string): number {
  return Math.max(0, daysUntil(snapshotDate, SEQUENCE_EPOCH))
}

/** Fold a content line to at most 75 octets per physical line (section 3.1). */
export function foldLine(line: string): string {
  const enc = new TextEncoder()
  if (enc.encode(line).length <= 75) return line
  const parts: string[] = []
  let cur = ''
  let curBytes = 0
  for (const ch of line) {
    const b = enc.encode(ch).length
    const limit = parts.length === 0 ? 75 : 74 // continuation lines start with a space
    if (curBytes + b > limit) {
      parts.push(cur)
      cur = ''
      curBytes = 0
    }
    cur += ch
    curBytes += b
  }
  parts.push(cur)
  return parts.join(`${CRLF} `)
}

function compactDate(iso: string): string {
  return iso.replace(/-/g, '')
}

function nextDay(iso: string): string {
  const [y, m, d] = iso.split('-').map(Number)
  return new Date(Date.UTC(y, m - 1, d + 1)).toISOString().slice(0, 10)
}

function stamp(now: Date): string {
  return now.toISOString().replace(/[-:]/g, '').replace(/\.\d{3}/, '')
}

export function buildIcs(
  opps: RadarOpportunity[],
  now: Date = new Date(),
  calName = 'OpAssist deadlines',
  snapshotDate: string = SNAPSHOT_DATE,
): string {
  const sequence = snapshotSequence(snapshotDate)
  const lastModified = `${compactDate(snapshotDate)}T000000Z`
  const lines: string[] = [
    'BEGIN:VCALENDAR',
    'VERSION:2.0',
    'PRODID:-//OpAssist//Deadline Radar//EN',
    'CALSCALE:GREGORIAN',
    'METHOD:PUBLISH',
    `X-WR-CALNAME:${escapeText(calName)}`,
    'X-WR-TIMEZONE:Asia/Kolkata',
  ]
  for (const o of opps) {
    if (!o.deadline) continue
    const kind = o.kind === 'hackathon' ? 'Registration' : 'Applications'
    const url = safeHttpsUrl(o.url) // URI values are not TEXT-escaped, so re-validate here too
    const desc = [
      `${o.organizer}`,
      o.reward ? `Reward: ${o.reward}` : '',
      o.eventDates ? `Dates: ${o.eventDates}` : '',
      url ? `Confirm details on the organiser page: ${url}` : 'Confirm details on the organiser page.',
    ]
      .filter(Boolean)
      .join('\n')
    lines.push(
      'BEGIN:VEVENT',
      // UID must not change when the deadline moves, or calendars keep the stale copy as well
      `UID:${o.id}@opassist`,
      `SEQUENCE:${sequence}`,
      `DTSTAMP:${stamp(now)}`,
      `LAST-MODIFIED:${lastModified}`,
      `DTSTART;VALUE=DATE:${compactDate(o.deadline)}`,
      `DTEND;VALUE=DATE:${compactDate(nextDay(o.deadline))}`,
      `SUMMARY:${escapeText(`${kind} close: ${o.title}`)}`,
      `DESCRIPTION:${escapeText(desc)}`,
      ...(url ? [`URL:${url}`] : []),
      'TRANSP:TRANSPARENT',
      'BEGIN:VALARM',
      'ACTION:DISPLAY',
      `DESCRIPTION:${escapeText(`${o.title} closes in 3 days`)}`,
      'TRIGGER:-P3D',
      'END:VALARM',
      'BEGIN:VALARM',
      'ACTION:DISPLAY',
      `DESCRIPTION:${escapeText(`${o.title} closes tomorrow`)}`,
      'TRIGGER:-P1D',
      'END:VALARM',
      'END:VEVENT',
    )
  }
  lines.push('END:VCALENDAR')
  return lines.map(foldLine).join(CRLF) + CRLF
}

/** Trigger a browser download of an .ics file. */
export function downloadIcs(opps: RadarOpportunity[], filename = 'opassist-deadlines.ics') {
  const blob = new Blob([buildIcs(opps)], { type: 'text/calendar;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  a.remove()
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}
