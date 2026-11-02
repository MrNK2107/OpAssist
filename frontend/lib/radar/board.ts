// Application tracker board: pure state transitions, persisted by the store.

export type Stage = 'shortlist' | 'preparing' | 'applied' | 'result'

export const STAGES: { id: Stage; label: string; hint: string }[] = [
  { id: 'shortlist', label: 'Shortlisted', hint: 'Worth a look' },
  { id: 'preparing', label: 'Preparing', hint: 'Team, idea, resume' },
  { id: 'applied', label: 'Applied', hint: 'Submitted, waiting' },
  { id: 'result', label: 'Heard back', hint: 'Shortlist, offer or no' },
]

export interface BoardCard {
  id: string
  stage: Stage
  addedAt: string
  note: string
}

export type Board = Record<string, BoardCard>

export function addCard(board: Board, id: string, now: Date = new Date()): Board {
  if (board[id]) return board
  return { ...board, [id]: { id, stage: 'shortlist', addedAt: now.toISOString(), note: '' } }
}

export function removeCard(board: Board, id: string): Board {
  if (!board[id]) return board
  const next = { ...board }
  delete next[id]
  return next
}

export function moveCard(board: Board, id: string, stage: Stage): Board {
  const card = board[id]
  if (!card || card.stage === stage) return board
  return { ...board, [id]: { ...card, stage } }
}

/** Move one column left (-1) or right (+1), clamped to the board. */
export function stepCard(board: Board, id: string, dir: -1 | 1): Board {
  const card = board[id]
  if (!card) return board
  const i = STAGES.findIndex((s) => s.id === card.stage)
  const j = Math.max(0, Math.min(STAGES.length - 1, i + dir))
  return moveCard(board, id, STAGES[j].id)
}

export function setNote(board: Board, id: string, note: string): Board {
  const card = board[id]
  if (!card) return board
  return { ...board, [id]: { ...card, note: note.slice(0, 280) } }
}

export function columns(board: Board): Record<Stage, BoardCard[]> {
  const cols = { shortlist: [], preparing: [], applied: [], result: [] } as Record<Stage, BoardCard[]>
  for (const c of Object.values(board)) cols[c.stage].push(c)
  for (const s of STAGES) cols[s.id].sort((a, b) => a.addedAt.localeCompare(b.addedAt))
  return cols
}
