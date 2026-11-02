import type { Metadata } from 'next'
import { BoardView } from '@/components/radar/board-view'

export const metadata: Metadata = { title: 'Application board · OpAssist' }

export default function BoardPage() {
  return <BoardView />
}
