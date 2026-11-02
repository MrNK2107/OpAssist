// Client state for the Radar: profile, filters and tracker board.
// Stored in this browser only (localStorage), so the Radar works with no
// account. Signing in moves tracking to the server-side applications API.

import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'
import { addCard, moveCard, removeCard, setNote, stepCard, type Board, type Stage } from '@/lib/radar/board'
import { DEFAULT_FILTERS, type RadarFilters } from '@/lib/radar/filters'
import { SAMPLE_PROFILE } from '@/lib/radar/seed'
import type { StudentProfile } from '@/lib/radar/types'

interface RadarState {
  profile: StudentProfile
  /** False until the visitor edits the sample profile. */
  customised: boolean
  filters: RadarFilters
  board: Board
  setProfile: (patch: Partial<StudentProfile>) => void
  resetProfile: () => void
  setFilters: (patch: Partial<RadarFilters>) => void
  resetFilters: () => void
  track: (id: string) => void
  untrack: (id: string) => void
  move: (id: string, stage: Stage) => void
  step: (id: string, dir: -1 | 1) => void
  note: (id: string, note: string) => void
}

const memoryStorage = () => {
  const m = new Map<string, string>()
  return {
    getItem: (k: string) => m.get(k) ?? null,
    setItem: (k: string, v: string) => void m.set(k, v),
    removeItem: (k: string) => void m.delete(k),
  }
}

export const useRadarStore = create<RadarState>()(
  persist(
    (set) => ({
      profile: SAMPLE_PROFILE,
      customised: false,
      filters: DEFAULT_FILTERS,
      board: {},
      setProfile: (patch) => set((s) => ({ profile: { ...s.profile, ...patch }, customised: true })),
      resetProfile: () => set({ profile: SAMPLE_PROFILE, customised: false }),
      setFilters: (patch) => set((s) => ({ filters: { ...s.filters, ...patch } })),
      resetFilters: () => set({ filters: DEFAULT_FILTERS }),
      track: (id) => set((s) => ({ board: addCard(s.board, id) })),
      untrack: (id) => set((s) => ({ board: removeCard(s.board, id) })),
      move: (id, stage) => set((s) => ({ board: moveCard(s.board, id, stage) })),
      step: (id, dir) => set((s) => ({ board: stepCard(s.board, id, dir) })),
      note: (id, note) => set((s) => ({ board: setNote(s.board, id, note) })),
    }),
    {
      name: 'opassist-radar-v1',
      version: 1,
      skipHydration: true,
      storage: createJSONStorage(() => {
        try {
          return typeof window !== 'undefined' && window.localStorage ? window.localStorage : memoryStorage()
        } catch {
          return memoryStorage()
        }
      }),
      partialize: (s) => ({ profile: s.profile, customised: s.customised, filters: s.filters, board: s.board }),
      merge: (persisted, current) => {
        const p = (persisted ?? {}) as Partial<RadarState>
        return {
          ...current,
          ...p,
          profile: { ...current.profile, ...p.profile },
          filters: { ...current.filters, ...p.filters },
          board: p.board ?? current.board,
        }
      },
    },
  ),
)
