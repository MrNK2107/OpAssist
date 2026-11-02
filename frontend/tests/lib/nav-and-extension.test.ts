import { describe, it, expect } from 'vitest'
import fs from 'node:fs'
import path from 'node:path'
import { navItems } from '@/lib/nav-config'

const FRONTEND = path.resolve(__dirname, '..', '..')
const EXTENSION = path.resolve(FRONTEND, '..', 'extension')

describe('nav-config', () => {
  it('has unique hrefs and labels', () => {
    expect(new Set(navItems.map((n) => n.href)).size).toBe(navItems.length)
    expect(new Set(navItems.map((n) => n.label)).size).toBe(navItems.length)
  })

  it.each(navItems.map((n) => [n.href]))('route %s has a page', (href) => {
    // Pages live in the (dashboard) route group, or at the top level for public ones like /radar.
    const candidates = [path.join(FRONTEND, 'app', '(dashboard)', href, 'page.tsx'), path.join(FRONTEND, 'app', href, 'page.tsx')]
    expect(candidates.some((p) => fs.existsSync(p)), `${candidates.join(' or ')} missing`).toBe(true)
  })
})

describe('browser extension manifest', () => {
  const manifest = JSON.parse(fs.readFileSync(path.join(EXTENSION, 'manifest.json'), 'utf8'))

  it('is a Manifest V3 extension with required fields', () => {
    expect(manifest.manifest_version).toBe(3)
    expect(manifest.name).toBeTruthy()
    expect(manifest.version).toMatch(/^\d+(\.\d+){0,3}$/)
    expect(manifest.description.length).toBeLessThanOrEqual(132)
    expect(manifest.background.service_worker).toBeTruthy()
    // MV2-only keys must not be present
    expect(manifest).not.toHaveProperty('browser_action')
    expect(manifest.background).not.toHaveProperty('scripts')
  })

  it('references only files that exist', () => {
    const refs: string[] = [
      manifest.action.default_popup,
      manifest.background.service_worker,
      ...Object.values(manifest.icons as Record<string, string>),
      ...manifest.content_scripts.flatMap((c: { js?: string[]; css?: string[] }) => [...(c.js ?? []), ...(c.css ?? [])]),
    ]
    for (const ref of refs) {
      expect(fs.existsSync(path.join(EXTENSION, ref)), `${ref} missing`).toBe(true)
    }
  })

  it('can reach the default local API (backend CORS only allows the web app)', () => {
    for (const file of ['background/service-worker.js', 'popup/popup.js']) {
      const src = fs.readFileSync(path.join(EXTENSION, file), 'utf8')
      const m = src.match(/DEFAULT_API_URL\s*=\s*'([^']+)'/)
      expect(m, `${file} has DEFAULT_API_URL`).not.toBeNull()
      const origin = new URL(m![1]).origin
      expect(manifest.host_permissions).toContain(`${origin}/*`)
    }
  })

  it('injects content scripts only on hosts it has permission for', () => {
    const matches: string[] = manifest.content_scripts.flatMap((c: { matches: string[] }) => c.matches)
    for (const m of matches) expect(manifest.host_permissions).toContain(m)
  })
})
