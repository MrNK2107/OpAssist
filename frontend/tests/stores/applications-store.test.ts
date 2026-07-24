import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockGet, mockPost, mockPut, mockDelete } = vi.hoisted(() => ({
  mockGet: vi.fn(),
  mockPost: vi.fn(),
  mockPut: vi.fn(),
  mockDelete: vi.fn(),
}))

vi.mock('@/lib/api', () => ({
  api: {
    get: mockGet,
    post: mockPost,
    put: mockPut,
    delete: mockDelete,
  },
}))

import { useApplicationsStore } from '@/stores/applications-store'

describe('ApplicationsStore', () => {
  beforeEach(() => {
    useApplicationsStore.setState({
      applications: [],
      loading: false,
      error: null,
    })
    vi.clearAllMocks()
  })

  it('initializes with empty state', () => {
    const state = useApplicationsStore.getState()
    expect(state.applications).toEqual([])
    expect(state.loading).toBe(false)
    expect(state.error).toBeNull()
  })

  it('fetchApplications loads data on success', async () => {
    const apps = [{ id: '1', user_id: 'u1', opportunity_id: 'opp-1', status: 'saved', applied_at: null, notes: null }]
    mockGet.mockResolvedValueOnce({ data: apps })

    await useApplicationsStore.getState().fetchApplications()

    const state = useApplicationsStore.getState()
    expect(state.applications).toEqual(apps)
    expect(state.loading).toBe(false)
  })

  it('fetchApplications sets error on failure', async () => {
    mockGet.mockRejectedValueOnce(new Error('Failed to fetch'))

    await useApplicationsStore.getState().fetchApplications()

    const state = useApplicationsStore.getState()
    expect(state.error).toBe('Failed to fetch')
  })

  it('createApplication adds to list', async () => {
    const newApp = { id: '2', user_id: 'u1', opportunity_id: 'opp-2', status: 'saved', applied_at: null, notes: null }
    mockPost.mockResolvedValueOnce({ data: newApp })

    await useApplicationsStore.getState().createApplication('opp-2')

    const state = useApplicationsStore.getState()
    expect(state.applications).toContainEqual(newApp)
  })

  it('updateApplication updates status locally', async () => {
    useApplicationsStore.setState({
      applications: [{ id: '1', user_id: 'u1', opportunity_id: 'opp-1', status: 'saved', applied_at: null, notes: null }],
    })
    mockPut.mockResolvedValueOnce({})

    await useApplicationsStore.getState().updateApplication('1', 'applied')

    const state = useApplicationsStore.getState()
    expect(state.applications[0].status).toBe('applied')
  })

  it('deleteApplication removes and rolls back on error', async () => {
    useApplicationsStore.setState({
      applications: [{ id: '1', user_id: 'u1', opportunity_id: 'opp-1', status: 'saved', applied_at: null, notes: null }],
    })
    mockDelete.mockRejectedValueOnce(new Error('Delete failed'))

    await useApplicationsStore.getState().deleteApplication('1')

    const state = useApplicationsStore.getState()
    expect(state.applications).toHaveLength(1)
    expect(state.error).toBe('Delete failed')
  })
})
