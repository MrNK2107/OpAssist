import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatDate(date: string | Date): string {
  return new Date(date).toLocaleDateString('en-IN', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

export function daysUntil(date: string | Date): number {
  const target = new Date(date)
  const now = new Date()
  const diff = target.getTime() - now.getTime()
  return Math.ceil(diff / (1000 * 60 * 60 * 24))
}

export function getDeadlineStatus(date: string | Date): 'urgent' | 'soon' | 'normal' | 'passed' {
  const days = daysUntil(date)
  if (days < 0) return 'passed'
  if (days <= 3) return 'urgent'
  if (days <= 7) return 'soon'
  return 'normal'
}
