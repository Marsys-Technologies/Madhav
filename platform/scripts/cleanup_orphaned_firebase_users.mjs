/**
 * cleanup_orphaned_firebase_users.mjs
 *
 * Finds Firebase Auth accounts with no matching profiles row and deletes them.
 * Pass --dry-run to list without deleting.
 *
 * Run:  node --env-file=.env.local scripts/cleanup_orphaned_firebase_users.mjs [--dry-run]
 */

import { initializeApp, getApps, cert } from 'firebase-admin/app'
import { getAuth } from 'firebase-admin/auth'
import pg from 'pg'

const DRY_RUN = process.argv.includes('--dry-run')
console.log(`Mode: ${DRY_RUN ? 'DRY RUN (no deletions)' : 'LIVE (will delete)'}`)

// ── Firebase init ─────────────────────────────────────────────────────────────
const serviceAccount = JSON.parse(process.env.FIREBASE_ADMIN_CREDENTIALS ?? '{}')
const app = getApps().length > 0 ? getApps()[0] : initializeApp({ credential: cert(serviceAccount) })
const auth = getAuth(app)

// ── Postgres init ─────────────────────────────────────────────────────────────
const pool = new pg.Pool({ connectionString: process.env.DATABASE_URL })

// ── List all Firebase users ───────────────────────────────────────────────────
const firebaseUsers = new Map() // email → uid
let pageToken
do {
  const result = await auth.listUsers(1000, pageToken)
  for (const u of result.users) {
    if (u.email) firebaseUsers.set(u.email.toLowerCase(), u.uid)
  }
  pageToken = result.pageToken
} while (pageToken)

console.log(`Firebase accounts found: ${firebaseUsers.size}`)
for (const [email, uid] of firebaseUsers) {
  console.log(`  ${email}  (uid=${uid})`)
}

if (firebaseUsers.size === 0) {
  console.log('Nothing to check.')
  await pool.end()
  process.exit(0)
}

// ── Find which emails have a profile ─────────────────────────────────────────
const emailList = Array.from(firebaseUsers.keys())
const placeholders = emailList.map((_, i) => `$${i + 1}`).join(',')
const { rows: profileRows } = await pool.query(
  `SELECT lower(email) AS email FROM profiles WHERE lower(email) IN (${placeholders})`,
  emailList
)
const profileEmails = new Set(profileRows.map((r) => r.email))

console.log(`\nProfile rows for those emails: ${profileRows.length}`)
for (const r of profileRows) console.log(`  ${r.email} ✓`)

const orphans = emailList.filter((e) => !profileEmails.has(e))
console.log(`\nOrphaned Firebase accounts (no profile row): ${orphans.length}`)

if (orphans.length === 0) {
  console.log('No orphans found. All Firebase accounts have matching profiles.')
} else {
  for (const email of orphans) {
    const uid = firebaseUsers.get(email)
    if (DRY_RUN) {
      console.log(`  [DRY RUN] Would delete: ${email}  (uid=${uid})`)
    } else {
      await auth.deleteUser(uid)
      console.log(`  Deleted: ${email}  (uid=${uid})`)
    }
  }
  if (DRY_RUN) console.log('\nDry run complete. Re-run without --dry-run to apply.')
  else console.log('\nDone.')
}

await pool.end()
