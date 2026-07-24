import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockGet, mockPost, mockDelete } = vi.hoisted(() => ({
  mockGet: vi.fn(),
  mockPost: vi.fn(),
  mockDelete: vi.fn(),
}))

vi.mock('@/lib/api', () => ({
  api: {
    get: mockGet,
    post: mockPost,
    delete: mockDelete,
  },
}))

import { useBookmarksStore } from '@/stores/bookmarks-store'

describe('BookmarksStore', () => {
  beforeEach(() => {
    useBookmarksStore.setState({
      bookmarks: [],
      loading: false,
      error: null,
    })
    vi.clearAllMocks()
  })

  it('initializes with empty state', () => {
    const state = useBookmarksStore.getState()
    expect(state.bookmarks).toEqual([])
    expect(state.loading).toBe(false)
    expect(state.error).toBeNull()
  })

  it('fetchBookmarks loads bookmarks on success', async () => {
    const bookmarks = [{ id: '1', user_id: 'u1', opportunity_id: 'opp-1', notes: null }]
    mockGet.mockResolvedValueOnce({ data: bookmarks })

    await useBookmarksStore.getState().fetchBookmarks()

    const state = useBookmarksStore.getState()
    expect(state.bookmarks).toEqual(bookmarks)
    expect(state.loading).toBe(false)
  })

  it('fetchBookmarks sets error on failure', async () => {
    mockGet.mockRejectedValueOnce(new Error('Network error'))

    await useBookmarksStore.getState().fetchBookmarks()

    const state = useBookmarksStore.getState()
    expect(state.error).toBe('Network error')
    expect(state.loading).toBe(false)
  })

  it('addBookmark optimistically adds bookmark', async () => {
    const newBookmark = { id: '2', user_id: 'u1', opportunity_id: 'opp-2', notes: null }
    mockPost.mockResolvedValueOnce({ data: newBookmark })

    await useBookmarksStore.getState().addBookmark('opp-2')

    const state = useBookmarksStore.getState()
    expect(state.bookmarks).toContainEqual(newBookmark)
  })

  it('removeBookmark removes and rolls back on error', async () => {
    useBookmarksStore.setState({ bookmarks: [{ id: '1', user_id: 'u1', opportunity_id: 'opp-1', notes: null }] })
    mockDelete.mockRejectedValueOnce(new Error('Delete failed'))

    await useBookmarksStore.getState().removeBookmark('1')

    const state = useBookmarksStore.getState()
    expect(state.bookmarks).toHaveLength(1)
    expect(state.error).toBe('Delete failed')
  })

  it('checkBookmark returns true when bookmarked', async () => {
    mockGet.mockResolvedValueOnce({ is_bookmarked: true })

    const result = await useBookmarksStore.getState().checkBookmark('opp-1')

    expect(result).toBe(true)
  })

  it('checkBookmark returns false on error', async () => {
    mockGet.mockRejectedValueOnce(new Error('error'))

    const result = await useBookmarksStore.getState().checkBookmark('opp-1')

    expect(result).toBe(false)
  })
})
