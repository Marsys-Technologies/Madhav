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
 *   Response: { ok: true, content: unknown } | { ok: false, error: string }
 *
 * Bootstrap: all D-wave registrations (D5 fan-out, D6 synergy, D7 channel,
 * D8 assess-domain) are run once at module initialization. The registry is
 * an in-process singleton; registrations are idempotent.
 *
 * R6 bootstrap: registerD8AssessDomainCapabilities() wired alongside D5–D7.
 */

import 'server-only'
import { NextResponse } from 'next/server'
import { getCapability } from '@/lib/retrieval/registry'

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
  registerD9JudgmentCapabilities,
} from '@/lib/retrieval/registry/layers/register_d9_judgment'
import {
  registerRouterCapabilities,
} from '@/lib/retrieval/registry/layers/router_registration'
import {
  registerMaroCapabilities,
} from '@/lib/retrieval/registry/layers/dprofiles_registration'

// ── Bootstrap (runs once at module init) ─────────────────────────────────────

let _bootstrapped = false

async function ensureBootstrapped(): Promise<void> {
  if (_bootstrapped) return
  _bootstrapped = true

  // Synchronous registrations first
  registerRouterCapabilities()
  registerMaroCapabilities()
  registerD6SynergyCapabilities()
  registerD7ChannelCapabilities()
  registerD8AssessDomainCapabilities()
  // R5 W3 (design §28.1): judgment_query — verified missing from this bootstrap list
  // during MCP-registration verification (the exact P1/W2-alias-gap failure class,
  // recurring one layer up: a capability registered in catalog.ts's per-wave import
  // chain but NOT in this route's own separate bootstrap list is unreachable via the
  // live HTTP path platform-mcp actually calls).
  registerD9JudgmentCapabilities()

  // D-B fix: register L0 + L1 capabilities (not included in D5 fanout)
  // L0: exports registerL0Capabilities() — must be called explicitly
  registerL0Capabilities()
  // L1: top-level registerCapability() calls fire on import (side-effect module)
  await import('@/lib/retrieval/registry/layers/L1_ganita/index')

  // D5 is async (dynamic imports of L2–L5 layer indexes)
  await registerD5FanoutCapabilities()
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

  try {
    const content = await capability.handler(safeArgs)
    return NextResponse.json({ ok: true, content })
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err)
    console.error(`[api/retrieval/capability] handler error for ${uri}:`, msg)
    return NextResponse.json(
      { ok: false, error: `Capability handler error: ${msg}` },
      { status: 500 }
    )
  }
}
