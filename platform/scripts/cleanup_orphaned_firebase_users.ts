/**
 * cleanup_orphaned_firebase_users.ts
 *
 * Finds Firebase Auth accounts that have no matching row in the profiles table
 * (orphans left by failed user-creation attempts) and deletes them.
 *
 * Run:  npx ts-node -r tsconfig-paths/register scripts/cleanup_orphaned_firebase_users.ts
 *   or: npx tsx scripts/cleanup_orphaned_firebase_users.ts
 *
 * Pass --dry-run to list orphans without deleting.
 */

import { adminAuth } from '../src/lib/firebase/server'
import { query } from '../src/lib/db/client'

const DRY_RUN = process.argv.includes('--dry-run')

async function main() {
  console.log(`Mode: ${DRY_RUN ? 'DRY RUN (no deletions)' : 'LIVE (will delete)'}`)

  // Fetch all Firebase users (paginated)
  const firebaseEmails: Map<string, string> = new Map() // email → uid
  let pageToken: string | undefined
  do {
    const result = await adminAuth.listUsers(1000, pageToken)
    for (const u of result.users) {
      if (u.email) firebaseEmails.set(u.email.toLowerCase(), u.uid)
    }
    pageToken = result.pageToken
  } while (pageToken)

  console.log(`Firebase accounts found: ${firebaseEmails.size}`)

  if (firebaseEmails.size === 0) {
    console.log('Nothing to check.')
    return
  }

  // Check which emails have a profile row
  const emailList = Array.from(firebaseEmails.keys())
  const placeholders = emailList.map((_, i) => `$${i + 1}`).join(',')
  const { rows: profileRows } = await query<{ email: string }>(
    `SELECT lower(email) AS email FROM profiles WHERE lower(email) IN (${placeholders})`,
    emailList
  )
  const profileEmails = new Set(profileRows.map((r) => r.email))

  const orphans = emailList.filter((e) => !profileEmails.has(e))
  console.log(`Orphaned Firebase accounts (no profile row): ${orphans.length}`)

  if (orphans.length === 0) {
    console.log('No orphans. All Firebase accounts have matching profiles.')
    return
  }

  for (const email of orphans) {
    const uid = firebaseEmails.get(email)!
    if (DRY_RUN) {
      console.log(`[DRY RUN] Would delete: ${email} (uid=${uid})`)
    } else {
      await adminAuth.deleteUser(uid)
      console.log(`Deleted: ${email} (uid=${uid})`)
    }
  }

  console.log(DRY_RUN ? 'Dry run complete. Re-run without --dry-run to apply.' : 'Done.')
}

main().catch((err) => {
  console.error('Fatal:', err)
  process.exit(1)
})
