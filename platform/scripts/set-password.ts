/**
 * One-time script: set a password for the astrologer account via Firebase Auth.
 * Replaces the former Supabase-auth approach (migrated to Firebase, 2026-04-28).
 *
 * Run: cd platform && npx tsx scripts/set-password.ts
 */
import * as path from 'node:path'
import * as dotenv from 'dotenv'
import { isDirectEntrypoint } from './lib/entrypoint'

dotenv.config({ path: path.join(process.cwd(), '.env.local') })

const EMAIL = process.env.SUPER_ADMIN_EMAIL!
// Password sourced from CLI arg or NEW_USER_PASSWORD env var.
// No literal fallback — refuses to run without an explicit credential.
const PASSWORD = process.argv[2] ?? process.env.NEW_USER_PASSWORD ?? ''

async function main() {
  if (!EMAIL) {
    console.error('SUPER_ADMIN_EMAIL not set in .env.local')
    process.exit(1)
  }
  if (!PASSWORD) {
    console.error(
      'Password required: pass as argv[2] (npx tsx scripts/set-password.ts <pw>) ' +
      'or set NEW_USER_PASSWORD in env. No literal fallback.'
    )
    process.exit(1)
  }

  // Initialise Firebase Admin SDK directly (avoids server-only guard in @/lib/firebase/server)
  const { initializeApp, getApps, cert } = await import('firebase-admin/app')
  const { getAuth } = await import('firebase-admin/auth')

  let serviceAccount: object = {}
  try {
    serviceAccount = JSON.parse(process.env.FIREBASE_ADMIN_CREDENTIALS ?? '{}')
  } catch {
    console.error('FIREBASE_ADMIN_CREDENTIALS is not valid JSON in .env.local')
    process.exit(1)
  }

  const app =
    getApps().length > 0
      ? getApps()[0]
      : initializeApp({ credential: cert(serviceAccount) })

  const auth = getAuth(app)

  // Look up user by email
  let uid: string
  try {
    const user = await auth.getUserByEmail(EMAIL)
    uid = user.uid
  } catch {
    console.error(`User not found in Firebase Auth: ${EMAIL}`)
    process.exit(1)
  }

  // Update password
  try {
    await auth.updateUser(uid, { password: PASSWORD })
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err)
    console.error('Failed to update password:', message)
    process.exit(1)
  }

  console.log(`✓ Password set for ${EMAIL}`)
  console.log(`  Login with: ${EMAIL} / ${PASSWORD}`)
}

// ─────────────────────────────────────────────────────────────────────────────────────────────
// `isDirectEntrypoint` is THE ONE SHARED IMPLEMENTATION, in `scripts/lib/entrypoint.ts`.
//
// It used to be a private copy of that function in this file. Nirmāṇa finding F-2 (M0-T60,
// re-filed by M0-T65 at EIGHT copies) is that a security-relevant predicate duplicated N times
// with no detector asserting the bodies agree is a defect on its own terms; ruling D-67 part 3
// granted the shared implementation. Task M0-T66.
//
// Imported, not mirrored, and that is safe here for the reason ruling D-9 actually gives:
// `scripts/lib/entrypoint.ts` imports only the three node builtins this file already imported
// for its own copy, and has no module-scope effect at all. This module's graph gains nothing.
//
// Re-exported so this module's public surface is exactly what it was.
export { isDirectEntrypoint }
// ─────────────────────────────────────────────────────────────────────────────────────────────

// Guard: only execute when this module IS the entrypoint — never as an import side effect.
//
// THE HAZARD IS RUNNING. `main()` initialises the Firebase Admin SDK from
// `FIREBASE_ADMIN_CREDENTIALS` and calls `auth.updateUser(uid, { password })` against the
// account named by `SUPER_ADMIN_EMAIL` — a live credential mutation, not a read. Both inputs
// are resolved at MODULE SCOPE (lines 15 and 18, the latter from `process.argv[2]`), so any
// process that imported this file with `.env.local` loadable would have reset that account's
// password to whatever its own argv[2] happened to be, or exited 1 through the tail below.
//
// This is the `isDirectEntrypoint` contract (Nirmāṇa M0-T60 / A3.4 operator rule 5), NOT the
// `IMPORT_ONLY !== '1'` contract the two CI gates use (M0-T50 / ruling D-49, documented at
// `scripts/audit/A3_env_matrix.md` Addendum A3.4). A gate's hazard is FAILING to run, so its safe
// default is RUN. This file's hazard is RUNNING, so its safe default is DO NOT RUN.
//
// Nirmāṇa WORK_QUEUE M0-T65, ruling D-74 part 1 (wave 1 of F-4 tier 1: the five scripts that were
// destructive or credential-touching on incidental import). Verified WITHOUT executing this file —
// D-74 parts 2 and 3 forbid running it — by structural assertion over this source plus behavioural
// tests of the identical idiom on a harmless stand-in module. See
// `scripts/__tests__/destructive_entrypoint_guards.test.ts`.
if (isDirectEntrypoint(import.meta.url, process.argv[1])) {
  main().catch(err => { console.error(err); process.exit(1) })
}
