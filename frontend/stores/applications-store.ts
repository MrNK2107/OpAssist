import { create } from 'zustand'
import { api } from '@/lib/api'

interface Application {
  id: string
  user_id: string
  opportunity_id: string
  status: string
  applied_at: string | null
  notes: string | null
  opportunities?: Record<string, unknown>
}

interface ApplicationsState {
  applications: Application[]
  loading: boolean
  error: string | null
  fetchApplications: () => Promise<void>
  createApplication: (opportunityId: string, status?: string) => Promise<void>
  updateApplication: (id: string, status: string, notes?: string) => Promise<void>
  deleteApplication: (id: string) => Promise<void>
}

export const useApplicationsStore = create<ApplicationsState>((set) => ({
  applications: [],
  loading: false,
  error: null,

  fetchApplications: async () => {
    set({ loading: true, error: null })
    try {
      const data = await api.get<{ data: Application[] }>('/api/applications')
      set({ applications: data.data, loading: false })
    } catch (err) {
      set({ loading: false, error: err instanceof Error ? err.message : 'Failed to fetch applications' })
    }
  },

  createApplication: async (opportunityId, status = 'saved') => {
    try {
      const result = await api.post<{ data: Application }>('/api/applications', { opportunity_id: opportunityId, status })
      if (result.data) {
        set((state) => ({ applications: [...state.applications, result.data] }))
      } else {
        const data = await api.get<{ data: Application[] }>('/api/applications')
        set({ applications: data.data })
      }
    } catch (err) {
      set({ error: err instanceof Error ? err.message : 'Failed to create application' })
    }
  },

  updateApplication: async (id, status, notes) => {
    try {
      await api.put(`/api/applications/${id}`, { status, notes })
      // Update local state
      set((state) => ({
        applications: state.applications.map((a) =>
          a.id === id ? { ...a, status, notes: notes ?? a.notes } : a
        ),
      }))
    } catch (err) {
      set({ error: err instanceof Error ? err.message : 'Failed to update application' })
    }
  },

  deleteApplication: async (id) => {
    const previous = useApplicationsStore.getState().applications
    set((state) => ({
      applications: state.applications.filter((a) => a.id !== id),
    }))
    try {
      await api.delete(`/api/applications/${id}`)
    } catch (err) {
      set({ applications: previous, error: err instanceof Error ? err.message : 'Failed to delete application' })
    }
  },
}))
