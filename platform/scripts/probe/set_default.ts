#!/usr/bin/env npx tsx
/**
 * probe/set_default.ts — point the dedicated acceptance principal's OWN AI Console Default at the
 * granted, system-owned local-CLI route (Purna owner-surrogate ruling OSR-007; migration 1119
 * grants only `claude_code`).
 *
 * It authenticates exactly as the probe principal (`probe-service-account`, role `guest`) using the
 * same in-memory session mint as `ask.ts`, then calls the ordinary user endpoint
 * `PUT /api/ai-console/default`. It changes only that principal's own default: it cannot grant a
 * CLI, cannot touch another user, and never prints or stores the session cookie or any credential.
 *
 * The session cookie and ID token are only ever sent to the production web origin below; there is no
 * flag to point them elsewhere, and redirects are refused.
 *
 * Usage: npx tsx scripts/probe/set_default.ts [--cli claude_code]
 */
import { mintFreshProbeSessionCookie } from './session_auth'

const PROBE_UID = process.env.PROBE_UID ?? 'probe-service-account'
export const PROBE_SERVICE_ORIGIN = 'https://amjis-web-qm256lasva-el.a.run.app'
const ALLOWED_CLIS = new Set(['claude_code'])

export function parseArgs(argv: readonly string[]): { cliId: string } {
  let cliId = 'claude_code'
  for (let i = 0; i < argv.length; i += 1) {
    if (argv[i] === '--cli') cliId = argv[++i] ?? ''
    else throw new Error(`unknown argument: ${argv[i]}`)
  }
  if (!ALLOWED_CLIS.has(cliId)) throw new Error('--cli must be: claude_code')
  return { cliId }
}

export function defaultChoiceBody(cliId: string): { choice: { kind: 'local_cli'; cliId: string; modelId: null } } {
  return { choice: { kind: 'local_cli', cliId, modelId: null } }
}

async function main(): Promise<void> {
  const { cliId } = parseArgs(process.argv.slice(2))
  console.error(`[set_default] minting fresh session for uid=${PROBE_UID}`)
  const cookie = await mintFreshProbeSessionCookie(PROBE_SERVICE_ORIGIN, PROBE_UID)
  const response = await fetch(`${PROBE_SERVICE_ORIGIN}/api/ai-console/default`, {
    method: 'PUT',
    redirect: 'error',
    headers: { 'Content-Type': 'application/json', Origin: PROBE_SERVICE_ORIGIN, Cookie: `__session=${cookie}` },
    body: JSON.stringify(defaultChoiceBody(cliId)),
  })
  const text = await response.text()
  // The endpoint returns only the chosen ref or a coded error; still print only status + code.
  let code = ''
  try { const parsed = JSON.parse(text) as { error?: string | { code?: string } }; const e = parsed.error; code = typeof e === 'string' ? e : e?.code ?? '' } catch { /* non-JSON */ }
  console.error(`[set_default] PUT /api/ai-console/default -> HTTP ${response.status}${code ? ` (${code})` : ''}`)
  if (!response.ok) process.exitCode = 1
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((error: unknown) => { console.error('[set_default] fatal:', error instanceof Error ? error.message : 'failed'); process.exitCode = 1 })
}
