#!/usr/bin/env node
/**
 * get_session_cookie.mjs — emit a valid __session cookie for eval use
 *
 * Uses the Firebase Admin SDK to:
 * 1. Create a custom token for the super-admin user (looked up by email)
 * 2. Exchange it for an ID token via the Firebase REST API
 * 3. Create a session cookie via the Admin SDK
 *
 * Prints the raw cookie value to stdout.
 * All credentials read from .env.local (dotenv).
 * SUPER_ADMIN_EMAIL is REQUIRED (env or .env.local): there is no default account.
 */

import { readFileSync } from 'fs'
import { resolve, dirname } from 'path'
import { fileURLToPath } from 'url'

const __dirname = dirname(fileURLToPath(import.meta.url))

// ── minimal .env.local parser ──────────────────────────────────────────────
function loadEnv(path) {
  try {
    const lines = readFileSync(path, 'utf8').split('\n')
    for (const line of lines) {
      const trimmed = line.trim()
      if (!trimmed || trimmed.startsWith('#')) continue
      const eqIdx = trimmed.indexOf('=')
      if (eqIdx === -1) continue
      const key = trimmed.slice(0, eqIdx).trim()
      const val = trimmed.slice(eqIdx + 1).trim()
      if (!process.env[key]) process.env[key] = val
    }
  } catch { /* ignore */ }
}

loadEnv(resolve(__dirname, '../.env.local'))

const FIREBASE_ADMIN_CREDENTIALS = process.env.FIREBASE_ADMIN_CREDENTIALS
const FIREBASE_API_KEY = process.env.NEXT_PUBLIC_FIREBASE_API_KEY
const SUPER_ADMIN_EMAIL = process.env.SUPER_ADMIN_EMAIL
const SESSION_DURATION_MS = 60 * 60 * 24 * 14 * 1000

if (!SUPER_ADMIN_EMAIL) {
  console.error('SUPER_ADMIN_EMAIL not set (env or .env.local): it is required, there is no default account')
  process.exit(1)
}
if (!FIREBASE_ADMIN_CREDENTIALS) {
  console.error('FIREBASE_ADMIN_CREDENTIALS not set in .env.local')
  process.exit(1)
}
if (!FIREBASE_API_KEY) {
  console.error('NEXT_PUBLIC_FIREBASE_API_KEY not set in .env.local')
  process.exit(1)
}

// ── Firebase Admin init ────────────────────────────────────────────────────
const { initializeApp, getApps, cert } = await import('firebase-admin/app')
const { getAuth } = await import('firebase-admin/auth')

const serviceAccount = JSON.parse(FIREBASE_ADMIN_CREDENTIALS)
const app = getApps().length > 0 ? getApps()[0] : initializeApp({ credential: cert(serviceAccount) })
const auth = getAuth(app)

// ── 1. Look up UID by email ────────────────────────────────────────────────
let uid
try {
  const userRecord = await auth.getUserByEmail(SUPER_ADMIN_EMAIL)
  uid = userRecord.uid
} catch (err) {
  console.error('Could not look up user by email:', err.message)
  process.exit(1)
}

// ── 2. Create custom token ─────────────────────────────────────────────────
const customToken = await auth.createCustomToken(uid, { email: SUPER_ADMIN_EMAIL })

// ── 3. Exchange custom token for ID token (Firebase REST) ─────────────────
const signInRes = await fetch(
  `https://identitytoolkit.googleapis.com/v1/accounts:signInWithCustomToken?key=${FIREBASE_API_KEY}`,
  {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ token: customToken, returnSecureToken: true }),
  }
)
if (!signInRes.ok) {
  const err = await signInRes.text()
  console.error('signInWithCustomToken failed:', err)
  process.exit(1)
}
const { idToken } = await signInRes.json()

// ── 4. Create session cookie via Admin SDK ─────────────────────────────────
const sessionCookie = await auth.createSessionCookie(idToken, { expiresIn: SESSION_DURATION_MS })

// ── Output ─────────────────────────────────────────────────────────────────
process.stdout.write(sessionCookie)
