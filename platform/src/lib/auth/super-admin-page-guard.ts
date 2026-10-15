import 'server-only'
import { redirect } from 'next/navigation'
import { getServerUserWithProfile } from '@/lib/auth/access-control'

/**
 * Page-level super_admin guard (SS N-373 / PR-S1, item 2).
 *
 * A guard that lives ONLY in a layout does not protect a data-loading page
 * beneath it: Next.js layouts are not re-run on every RSC request, so a crafted
 * request (`Next-Router-State-Tree`) can reach the page without its layout (see
 * the repo's own comment at app/clients/[id]/layout.tsx). Every data-loading
 * page under a super_admin-only layout therefore calls this ITSELF, as the
 * first statement and before any data is loaded.
 *
 * The rule and the redirects are exactly the ones `app/cockpit/layout.tsx` and
 * `app/information/layout.tsx` apply, so layout and page can never disagree:
 *   no verified session   -> /login
 *   profile not active    -> /login
 *   role !== super_admin  -> /dashboard
 *
 * Verification is real (`getServerUserWithProfile` -> firebase-admin
 * `verifySessionCookie(cookie, checkRevoked=true)` + the `profiles` row), never
 * the cookie-shape check proxy.ts does.
 */
export async function requireSuperAdminPage() {
  const ctx = await getServerUserWithProfile()
  if (!ctx) redirect('/login')
  if (ctx.profile.status !== 'active') redirect('/login')
  if (ctx.profile.role !== 'super_admin') redirect('/dashboard')
  return ctx
}
