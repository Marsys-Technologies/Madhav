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
 *   Response: { ok: true, content: unknown } | { ok: false, error: string } |
 *     McpErrorEnvelope (entitlement_denied / validation — see R5.2 A1 gate below)
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
import { authorizeChartAccess, type Permission } from '@/lib/auth/authorizeChartAccess'
import { resolveMcpPrincipalRole } from '@/lib/mcp/auth'
import { buildEntitlementDenialEnvelope, buildErrorEnvelope } from '@/lib/mcp/epistemics'
import { query } from '@/lib/db/client'
import { validateServiceToken } from '@/lib/mcp/service_token'

// ── Per-call chart entitlement gate (R5.2 A1) ─────────────────────────────────
//
// This route previously dispatched to any registered capability handler with no
// per-chart authorization check — the highest-priority gap named in the R5.1
// punch-list. Every MCP caller now carries the same X-MCP-User / X-MCP-Key-Id
// principal headers already required by /api/mcp/primitives/[tool] (Layer 2),
// and per_chart capabilities are gated through the same authorizeChartAccess
// brain, returning the same distinct entitlement_denied envelope (never a bare
// 401, never an empty result masquerading as "no data").
//
// Short-TTL in-process cache: avoids a DB round trip on every single-chart-tool
// call within a burst (a synthesis/judgment call can fan out to a dozen
// capability calls in one query). TTL is intentionally short — this is a
// latency mitigation, not a source of truth; a revoked grant is visible again
// within one TTL window.
const ENTITLEMENT_CACHE_TTL_MS = 30_000
const entitlementCache = new Map<string, { permission: Permission; expiresAt: number }>()

async function resolveCachedPermission(userUid: string, chartId: string): Promise<Permission> {
  const cacheKey = `${userUid}:${chartId}`
  const cached = entitlementCache.get(cacheKey)
  const now = Date.now()
  if (cached && cached.expiresAt > now) return cached.permission

  const role = await resolveMcpPrincipalRole(userUid)
  const permission = await authorizeChartAccess({ principal: { uid: userUid, role }, chartId, db: { query } })
  entitlementCache.set(cacheKey, { permission, expiresAt: now + ENTITLEMENT_CACHE_TTL_MS })
  return permission
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
  registerD10PactCapabilities,
} from '@/lib/retrieval/registry/layers/register_d10_pact'
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
  // R5.1 C1 fix (same failure class as the D9 fix immediately above, caught live by
  // the independent verifier of commit 624f2934): pact_query (D10) was registered in
  // catalog.ts's per-wave import chain but NEVER added to this route's separate
  // bootstrap list — every live pact_query MCP call 404'd with "Unknown capability URI:
  // marsys://tool/L-PACT/pact_query" and the R5.1 C1 trimming/budget code for this tool
  // had never actually been exercised against real data. One-line fix, identical to D9's.
  registerD10PactCapabilities()

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

  // R5.2 A1 — per-call chart entitlement gate. Runs for every per_chart capability,
  // regardless of which of the ~35 call sites across platform-mcp reached this route.
  if (capability.scope === 'per_chart') {
    const chartId =
      (typeof safeArgs['chart_id'] === 'string' ? (safeArgs['chart_id'] as string) : undefined) ??
      request.headers.get('x-mcp-chart-id') ??
      null
    const userUid = request.headers.get('x-mcp-user')

    if (!chartId) {
      return NextResponse.json(
        buildErrorEnvelope({
          error_class: 'validation',
          message: 'CHART_REQUIRED',
          remediation: 'Supply chart_id in args or X-MCP-Chart-Id header for per-chart capabilities.',
        }),
        { status: 400 }
      )
    }
    if (!userUid) {
      // Fail closed: a per-chart capability call with no resolvable principal is denied,
      // never silently served. Distinct from a 401 leak — same denial shape as a real deny.
      return NextResponse.json(
        buildEntitlementDenialEnvelope({ chart_id: chartId, permission_required: 'view' }),
        { status: 401 }
      )
    }

    const permission = await resolveCachedPermission(userUid, chartId)
    if (permission === 'deny') {
      return NextResponse.json(
        buildEntitlementDenialEnvelope({ chart_id: chartId, permission_required: 'view' }),
        { status: 401 }
      )
    }
  }

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
