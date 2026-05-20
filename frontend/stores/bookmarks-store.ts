import { create } from 'zustand'
import { api } from '@/lib/api'

interface Bookmark {
  id: string
  user_id: string
  opportunity_id: string
  notes: string | null
  opportunities?: Record<string, unknown>
}

interface BookmarksState {
  bookmarks: Bookmark[]
  loading: boolean
  error: string | null
  fetchBookmarks: () => Promise<void>
  addBookmark: (opportunityId: string, notes?: string) => Promise<void>
  removeBookmark: (bookmarkId: string) => Promise<void>
  checkBookmark: (opportunityId: string) => Promise<boolean>
}

export const useBookmarksStore = create<BookmarksState>((set) => ({
  bookmarks: [],
  loading: false,
  error: null,

  fetchBookmarks: async () => {
    set({ loading: true, error: null })
    try {
      const data = await api.get<{ data: Bookmark[] }>('/api/bookmarks')
      set({ bookmarks: data.data, loading: false })
    } catch (err) {
      set({ loading: false, error: err instanceof Error ? err.message : 'Failed to fetch bookmarks' })
    }
  },

  addBookmark: async (opportunityId, notes) => {
    try {
      const result = await api.post<{ data: Bookmark }>('/api/bookmarks', { opportunity_id: opportunityId, notes })
      // Optimistic update - add the new bookmark to local state
      if (result.data) {
        set((state) => ({ bookmarks: [...state.bookmarks, result.data] }))
      } else {
        // Fallback: refresh list
        const data = await api.get<{ data: Bookmark[] }>('/api/bookmarks')
        set({ bookmarks: data.data })
      }
    } catch (err) {
      set({ error: err instanceof Error ? err.message : 'Failed to add bookmark' })
    }
  },

  removeBookmark: async (bookmarkId) => {
    // Optimistic update - remove locally first
    const previousBookmarks = useBookmarksStore.getState().bookmarks
    set((state) => ({
      bookmarks: state.bookmarks.filter((b) => b.id !== bookmarkId),
    }))
    try {
      await api.delete(`/api/bookmarks/${bookmarkId}`)
    } catch (err) {
      // Rollback on error
      set({ bookmarks: previousBookmarks, error: err instanceof Error ? err.message : 'Failed to remove bookmark' })
    }
  },

  checkBookmark: async (opportunityId) => {
    try {
      const data = await api.get<{ is_bookmarked: boolean }>(
        `/api/bookmarks/check/${opportunityId}`
      )
      return data.is_bookmarked
    } catch {
      return false
    }
  },
}))
