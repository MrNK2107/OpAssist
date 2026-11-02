import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

const { authState } = vi.hoisted(() => ({
  authState: { currentUser: null as null | { getIdToken: () => Promise<string> } },
}))

vi.mock('@/lib/firebase', () => ({ auth: authState }))

import { api, apiFetch } from '@/lib/api'

function jsonResponse(body: unknown, init: ResponseInit = {}) {
  return new Response(JSON.stringify(body), {
    status: 200,
    headers: { 'Content-Type': 'application/json' },
    ...init,
  })
}

describe('apiFetch', () => {
  const fetchMock = vi.fn()

  beforeEach(() => {
    authState.currentUser = null
    fetchMock.mockReset()
    vi.stubGlobal('fetch', fetchMock)
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('GETs the API base URL without auth header when signed out', async () => {
    fetchMock.mockResolvedValue(jsonResponse({ ok: true }))

    await expect(apiFetch('/api/opportunities')).resolves.toEqual({ ok: true })

    const [url, init] = fetchMock.mock.calls[0]
    expect(url).toBe('http://localhost:8000/api/opportunities')
    expect(init.method).toBe('GET')
    expect(init.body).toBeUndefined()
    expect(init.headers).not.toHaveProperty('Authorization')
  })

  it('adds a Bearer token when a user is signed in', async () => {
    authState.currentUser = { getIdToken: () => Promise.resolve('tok-123') }
    fetchMock.mockResolvedValue(jsonResponse([]))

    await api.get('/api/bookmarks')

    expect(fetchMock.mock.calls[0][1].headers.Authorization).toBe('Bearer tok-123')
  })

  it('serialises JSON bodies for POST/PUT and uses the right verb', async () => {
    fetchMock.mockImplementation(async () => jsonResponse({ id: '1' }))

    await api.post('/api/applications', { status: 'saved' })
    await api.put('/api/applications/1', { status: 'applied' })
    await api.delete('/api/applications/1')

    const calls = fetchMock.mock.calls.map(([, init]) => [init.method, init.body])
    expect(calls).toEqual([
      ['POST', JSON.stringify({ status: 'saved' })],
      ['PUT', JSON.stringify({ status: 'applied' })],
      ['DELETE', undefined],
    ])
  })

  it('resolves undefined for 204 No Content instead of failing to parse', async () => {
    fetchMock.mockResolvedValue(new Response(null, { status: 204 }))

    await expect(api.delete('/api/bookmarks/1')).resolves.toBeUndefined()
  })

  it('throws the FastAPI "detail" message on error responses', async () => {
    fetchMock.mockResolvedValue(jsonResponse({ detail: 'Not authenticated' }, { status: 401 }))

    await expect(api.get('/api/profile')).rejects.toThrow('Not authenticated')
  })

  it('falls back to statusText when the error body is not JSON', async () => {
    fetchMock.mockResolvedValue(new Response('<html>oops</html>', { status: 502, statusText: 'Bad Gateway' }))

    await expect(api.get('/api/x')).rejects.toThrow('Bad Gateway')
  })
})
