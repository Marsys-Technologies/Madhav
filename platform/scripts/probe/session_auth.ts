import { execSync } from 'node:child_process'
import { cert, getApps, initializeApp } from 'firebase-admin/app'
import { getAuth } from 'firebase-admin/auth'

function envOrSecret(name: string, secret: string): string {
  const current = process.env[name]
  if (current) return current
  const value = execSync(`gcloud secrets versions access latest --secret=${secret} --project=madhav-astrology`, { encoding: 'utf8' }).trim()
  if (!value) throw new Error(`Secret Manager:${secret} returned empty value`)
  return value
}

function firebaseApiKey(): string {
  if (process.env.NEXT_PUBLIC_FIREBASE_API_KEY) return process.env.NEXT_PUBLIC_FIREBASE_API_KEY
  const config = JSON.parse(execSync('firebase apps:sdkconfig WEB --project=madhav-astrology', { encoding: 'utf8' })) as { apiKey?: unknown }
  if (typeof config.apiKey !== 'string' || !config.apiKey) throw new Error('Firebase SDK config returned no apiKey')
  return config.apiKey
}

/** Resolves existing approved auth in memory and never writes the minted cookie. */
export async function mintFreshProbeSessionCookie(serviceUrl: string, uid: string, signal?: AbortSignal): Promise<string> {
  const credentials = JSON.parse(envOrSecret('FIREBASE_ADMIN_CREDENTIALS', 'firebase-admin-credentials'))
  const app = getApps().length > 0 ? getApps()[0]! : initializeApp({ credential: cert(credentials) })
  const customToken = await getAuth(app).createCustomToken(uid)
  const signIn = await fetch(`https://identitytoolkit.googleapis.com/v1/accounts:signInWithCustomToken?key=${firebaseApiKey()}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, signal, body: JSON.stringify({ token: customToken, returnSecureToken: true }) })
  const signed = await signIn.json() as { idToken?: string }
  if (!signed.idToken) throw new Error('Firebase sign-in did not return an ID token')
  const session = await fetch(`${serviceUrl.replace(/\/$/, '')}/api/auth/session`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, signal, body: JSON.stringify({ idToken: signed.idToken }) })
  const raw = (session.headers as Headers & { getSetCookie?: () => string[] }).getSetCookie?.() ?? session.headers.get('set-cookie') ?? ''
  const match = (Array.isArray(raw) ? raw.join('\n') : String(raw)).match(/__session=([^;]+)/)
  if (!session.ok || !match) throw new Error('Portal session mint failed')
  return match[1]
}
