/**
 * /api/retrieval/capability — Registry capability dispatcher.
 *
 * Called by platform-mcp/src/tools/registry_bridge.ts for every D7/D8
 * consolidated MCP tool. The MCP server cannot import Next.js modules
 * directly (separate Node package), so it proxies capability calls here.
 *
 * Protocol:
 *   POST /api/retrieval/capability
 *   Body: { uri: string, args: Record<string, unknown> }
 *   Response: { ok: true, content: unknown, served_from_cache: boolean } | { ok: false, error: string }
 *
 * Bootstrap: all D-wave registrations (D5 fan-out, D6 synergy, D7 channel,
 * D8 assess-domain) are run once at module initialization. The registry is
 * an in-process singleton; registrations are idempotent.
 *
 * R6 bootstrap: registerD8AssessDomainCapabilities() wired alongside D5–D7.
 *
 * Caching (latency fix): capability results are cached in Redis
 * ('retrieval-bundle' namespace) keyed on (uri, stable-args-hash).
 * TTL is URI-class-dependent (classical texts: 1 hr; L1 data: 10 min;
 * L2/L3/L4/L5: 5 min). Cache misses fall through to compute and write-back.
 * served_from_cache is returned so callers can surface it.
 */

import 'server-only'
import { NextResponse } from 'next/server'
import { getCapability } from '@/lib/retrieval/registry'
import { buildKey, cacheGet, cacheSet } from '@/lib/cache/shared_cache'

// ── Service-to-service internal token gate ────────────────────────────────────

function validateServiceToken(request: Request): boolean {
  const token = request.headers.get('x-mcp-internal-token')
  const expected = process.env.MCP_INTERNAL_TOKEN
  if (!expected) {
    if (process.env.NODE_ENV === 'development') return true
    console.error('[api/retrieval/capability] MCP_INTERNAL_TOKEN not set in production')
    return false
  }
  return token === expected
}
import {
  registerD5FanoutCapabilities,
} from '@/lib/retrieval/registry/layers/register_d5_fanout'
import {
  registerL0Capabilities,
} from '@/lib/retrieval/registry/layers/L0_brahmagyan/index'
import {
  registerD6SynergyCapabilities,
} from '@/lib/retrieval/registry/layers/register_d6_synergy'
import {
  registerD7ChannelCapabilities,
} from '@/lib/retrieval/registry/layers/register_d7_channel'
import {
  registerD8AssessDomainCapabilities,
} from '@/lib/retrieval/registry/layers/register_d8_assess_domain'
import {
  registerRouterCapabilities,
} from '@/lib/retrieval/registry/layers/router_registration'
import {
  registerMaroCapabilities,
} from '@/lib/retrieval/registry/layers/dprofiles_registration'

// ── Bootstrap (runs once per process) ────────────────────────────────────────

let _bootstrapped = false

async function ensureBootstrapped(): Promise<void> {
  if (_bootstrapped) return
  // Set flag synchronously before any await — JS event loop guarantees
  // no other code runs between this line and the first await, so this
  // prevents duplicate registration even under concurrent first requests.
  _bootstrapped = true

  // Synchronous registrations first
  registerRouterCapabilities()
  registerMaroCapabilities()
  registerD6SynergyCapabilities()
  registerD7ChannelCapabilities()
  registerD8AssessDomainCapabilities()

  // D-B fix: register L0 + L1 capabilities (not included in D5 fanout)
  // L0: exports registerL0Capabilities() — must be called explicitly
  registerL0Capabilities()
  // L1: top-level registerCapability() calls fire on import (side-effect module)
  await import('@/lib/retrieval/registry/layers/L1_ganita/index')

  // D5 is async (dynamic imports of L2–L5 layer indexes)
  await registerD5FanoutCapabilities()
}

// ── Cache TTL by URI class ────────────────────────────────────────────────────

function capabilityTtlSeconds(uri: string): number {
  if (uri.includes('query_classical_texts')) return 3600  // classical texts: rare changes
  if (uri.startsWith('marsys://tool/L1/'))   return 600   // L1 positions/dashas: stable between rebuilds
  return 300                                               // L2/L3/L4/L5/D6/D7/D8: 5 min
}

// ── POST handler ─────────────────────────────────────────────────────────────

export async function POST(request: Request) {
  // Service-to-service gate — must be first; proxy.ts allowlists /api/retrieval/
  // only because this check is here. Remove this and you expose the retrieval
  // layer unauthenticated to the internet.
  if (!validateServiceToken(request)) {
    return NextResponse.json({ ok: false, error: 'Forbidden' }, { status: 403 })
  }

  let body: { uri?: string; args?: Record<string, unknown> }
  try {
    body = await request.json()
  } catch {
    return NextResponse.json(
      { ok: false, error: 'Invalid JSON body' },
      { status: 400 }
    )
  }

  const { uri, args } = body

  if (!uri || typeof uri !== 'string') {
    return NextResponse.json(
      { ok: false, error: 'Missing or invalid `uri` field' },
      { status: 400 }
    )
  }

  // Ensure all D-wave capabilities are registered before dispatch
  try {
    await ensureBootstrapped()
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err)
    console.error('[api/retrieval/capability] bootstrap failed:', msg)
    return NextResponse.json(
      { ok: false, error: `Registry bootstrap failed: ${msg}` },
      { status: 500 }
    )
  }

  const capability = getCapability(uri as Parameters<typeof getCapability>[0])
  if (!capability) {
    return NextResponse.json(
      { ok: false, error: `Unknown capability URI: ${uri}` },
      { status: 404 }
    )
  }

  const safeArgs = (args && typeof args === 'object') ? args : {}

  // ── Redis cache — L1 hit returns immediately; L2 miss falls to compute ──────
  const cacheKey = buildKey('retrieval-bundle', { uri, args: safeArgs })
  try {
    const cached = await cacheGet<unknown>('retrieval-bundle', cacheKey)
    if (cached !== undefined) {
      return NextResponse.json({ ok: true, content: cached, served_from_cache: true })
    }
  } catch {
    // Cache read failure is non-blocking — fall through to compute
  }

  try {
    const content = await capability.handler(safeArgs)
    // Fire-and-forget cache write — caller already has the result
    void cacheSet('retrieval-bundle', cacheKey, content, {
      ttlSeconds: capabilityTtlSeconds(uri),
    })
    return NextResponse.json({ ok: true, content, served_from_cache: false })
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err)
    console.error(`[api/retrieval/capability] handler error for ${uri}:`, msg)
    return NextResponse.json(
      { ok: false, error: `Capability handler error: ${msg}` },
      { status: 500 }
    )
  }
}
