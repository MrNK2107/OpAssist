import { describe, it, expect, vi, beforeEach } from 'vitest'

describe('firebase client without config', () => {
  beforeEach(() => {
    vi.resetModules()
    vi.unstubAllEnvs()
    for (const k of ['API_KEY', 'PROJECT_ID', 'APP_ID']) vi.stubEnv(`NEXT_PUBLIC_FIREBASE_${k}`, '')
  })

  it('imports without throwing and reports not configured', async () => {
    const fb = await import('@/lib/firebase')
    expect(fb.firebaseConfigured).toBe(false)
    expect(fb.auth.currentUser).toBeNull()
    expect(() => fb.getFirebaseAuth()).toThrow(/not configured/)
  })

  it('auth store initialises as signed out instead of crashing', async () => {
    const { useAuthStore } = await import('@/stores/auth-store')
    useAuthStore.getState().initialize()
    expect(useAuthStore.getState().loading).toBe(false)
    expect(useAuthStore.getState().user).toBeNull()
  })

  it('sign-in surfaces a readable error', async () => {
    const { useAuthStore } = await import('@/stores/auth-store')
    await expect(useAuthStore.getState().signIn('a@b.c', 'x')).rejects.toThrow(/not configured/)
    expect(useAuthStore.getState().error).toMatch(/NEXT_PUBLIC_FIREBASE/)
  })
})
