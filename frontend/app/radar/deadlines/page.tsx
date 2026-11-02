import type { Metadata } from 'next'
import { DeadlinesView } from '@/components/radar/deadlines-view'

export const metadata: Metadata = { title: 'Deadline radar · OpAssist' }

export default function DeadlinesPage() {
  return <DeadlinesView />
}
