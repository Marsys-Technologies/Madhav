/**
 * Test helper: stands in for firebase-admin so the REAL `getServerUser()` /
 * `verifySessionCookie()` in `lib/firebase/server.ts` run in a unit test.
 *
 * `server.ts` loads the Admin SDK with `require()` (lazily, to survive build-time
 * page-data collection), and `vi.mock` does not intercept `require`. So this helper
 * patches the already-loaded CJS module objects instead, and hands back a restore
 * function. The fake `verifySessionCookie` is the exported `verifySessionCookieMock`,
 * so each test decides whether the cookie "verifies".
 */
import { createRequire } from 'node:module'
import { vi } from 'vitest'

export const verifySessionCookieMock = vi.fn()

interface PatchedProp {
  target: Record<string, unknown>
  key: string
  original: PropertyDescriptor | undefined
}

export function installFakeFirebaseAdmin(): () => void {
  const req = createRequire(import.meta.url)
  const appMod = req('firebase-admin/app') as Record<string, unknown>
  const authMod = req('firebase-admin/auth') as Record<string, unknown>
  const patched: PatchedProp[] = []

  const patch = (target: Record<string, unknown>, key: string, value: unknown) => {
    patched.push({ target, key, original: Object.getOwnPropertyDescriptor(target, key) })
    Object.defineProperty(target, key, { value, writable: true, enumerable: true, configurable: true })
  }

  const fakeAuth = { verifySessionCookie: verifySessionCookieMock }
  patch(appMod, 'getApps', () => [{ name: 'fake-app' }])
  patch(authMod, 'getAuth', () => fakeAuth)

  return () => {
    for (const { target, key, original } of patched.reverse()) {
      if (original) Object.defineProperty(target, key, original)
      else delete target[key]
    }
  }
}
