/**
 * One-time script: set a password for the astrologer account via Firebase Auth.
 * Replaces the former Supabase-auth approach (migrated to Firebase, 2026-04-28).
 *
 * Run: cd platform && npx tsx scripts/set-password.ts
 */
import * as path from 'node:path'
import * as dotenv from 'dotenv'

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

main().catch(err => { console.error(err); process.exit(1) })
