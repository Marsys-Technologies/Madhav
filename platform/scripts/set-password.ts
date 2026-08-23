/**
 * One-time script: set a password for the astrologer account via Firebase Auth.
 * Replaces the former Supabase-auth approach (migrated to Firebase, 2026-04-28).
 *
 * Run: cd platform && npx tsx scripts/set-password.ts
 */
import * as path from 'node:path'
import * as dotenv from 'dotenv'
import { realpathSync } from 'node:fs'
import { resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

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

/**
 * Is THIS module the process entrypoint, or was it merely imported by something else?
 *
 * Exported so the question has a real, directly-testable detector behind it rather than an
 * inline expression nothing can exercise (CLAUDE.md §N.8).
 *
 * Compares the module's own URL against `process.argv[1]`, the path the runtime was told to
 * execute. Both sides are normalised through `realpathSync` where possible, so a symlinked
 * checkout, a `./`-prefixed spelling, or a `/tmp` → `/private/tmp` style realpath difference
 * does not make a direct run look like an import. Any failure to resolve either side answers
 * `false`: the safe direction is "assume imported", because a wrongly-false answer makes the
 * documented direct invocation exit having done nothing — loud, and recoverable — while a
 * wrongly-true answer changes a live Firebase Auth account's password as an import side
 * effect.
 *
 * MIRRORED, NOT IMPORTED, from `scripts/migrate.ts`, `scripts/seed/asset_registry_seed.ts` and
 * `scripts/pariprashna/ledger_writer_worker.ts`, which carry the same function. Deliberately a
 * copy: Nirmāṇa ruling D-9 standing-instructs agents not to import from `scripts/migrate.ts`,
 * and this file must not acquire a module graph it did not have before. Behaviour is intended to
 * stay identical to those copies; `scripts/__tests__/destructive_entrypoint_guards.test.ts`
 * asserts the bodies agree.
 */
export function isDirectEntrypoint(moduleUrl: string, argv1: string | undefined): boolean {
  if (!argv1) return false
  let modulePath: string
  try {
    modulePath = fileURLToPath(moduleUrl)
  } catch {
    return false
  }
  const entryPath = resolve(argv1)
  if (modulePath === entryPath) return true
  try {
    return realpathSync(modulePath) === realpathSync(entryPath)
  } catch {
    return false
  }
}

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
