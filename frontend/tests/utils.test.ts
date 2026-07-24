import { describe, it, expect } from 'vitest'
import { cn, formatDate, daysUntil, getDeadlineStatus } from '@/lib/utils'

describe('cn', () => {
  it('merges class names', () => {
    expect(cn('foo', 'bar')).toBe('foo bar')
  })

  it('handles conditional classes', () => {
    expect(cn('base', false && 'hidden', 'visible')).toBe('base visible')
  })

  it('merges tailwind classes', () => {
    expect(cn('px-4', 'px-2')).toBe('px-2')
  })
})

describe('formatDate', () => {
  it('formats a date string', () => {
    const result = formatDate('2026-06-10')
    expect(result).toContain('Jun')
    expect(result).toContain('2026')
  })

  it('formats a Date object', () => {
    const result = formatDate(new Date('2026-01-15'))
    expect(result).toContain('Jan')
  })
})

describe('daysUntil', () => {
  it('returns positive for future dates', () => {
    const future = new Date()
    future.setDate(future.getDate() + 5)
    expect(daysUntil(future)).toBe(5)
  })

  it('returns negative for past dates', () => {
    const past = new Date()
    past.setDate(past.getDate() - 3)
    expect(daysUntil(past)).toBeLessThan(0)
  })

  it('returns 0 for today', () => {
    expect(daysUntil(new Date())).toBe(0)
  })
})

describe('getDeadlineStatus', () => {
  it('returns urgent for <= 3 days', () => {
    const date = new Date()
    date.setDate(date.getDate() + 2)
    expect(getDeadlineStatus(date)).toBe('urgent')
  })

  it('returns soon for <= 7 days', () => {
    const date = new Date()
    date.setDate(date.getDate() + 5)
    expect(getDeadlineStatus(date)).toBe('soon')
  })

  it('returns normal for > 7 days', () => {
    const date = new Date()
    date.setDate(date.getDate() + 14)
    expect(getDeadlineStatus(date)).toBe('normal')
  })

  it('returns passed for past dates', () => {
    const date = new Date()
    date.setDate(date.getDate() - 1)
    expect(getDeadlineStatus(date)).toBe('passed')
  })
})
