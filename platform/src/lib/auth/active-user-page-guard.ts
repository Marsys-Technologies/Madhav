import 'server-only'
import { redirect } from 'next/navigation'
import { getServerUserWithProfile } from '@/lib/auth/access-control'

/**
 * Page-level "verified, active user" guard (SS N-376 / PR-S4).
 *
 * `proxy.ts` only checks that the `__session` cookie LOOKS right (it does not
 * verify the signature), so a page that loads data must verify the session
 * itself. This is the generic counterpart of `requireSuperAdminPage` and applies
 * the same rule every authenticated layout in the repo applies
 * (`dashboard/layout.tsx`, `panchang/layout.tsx`, ...):
 *
 *   no verified session   -> /login
 *   no profile row        -> /login
 *   profile not active    -> /login
 *
 * No role or ownership check: any verified, active user passes. Callers that
 * need more (owner, super_admin) layer it on top.
 *
 * `loginPath` is where a refused visitor is sent (default `/login`). A caller may
 * pass `/login?next=<encoded same-origin path>` so the login page can return the
 * visitor to the page; the login page validates `next` itself (safeNextPath).
 *
 * Verification is real (`getServerUserWithProfile` -> firebase-admin
 * `verifySessionCookie(cookie, checkRevoked=true)` + the `profiles` row).
 */
export async function requireActiveUserPage(loginPath: string = '/login') {
  const ctx = await getServerUserWithProfile()
  if (!ctx) redirect(loginPath)
  if (ctx.profile.status !== 'active') redirect(loginPath)
  return ctx
}
