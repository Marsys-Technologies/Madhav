// @vitest-environment node
//
// Retrieval Plane Elevation — plan R-1 item 3 ("single bootstrap").
//
// Proves BOTH states of the RETRIEVAL_SINGLE_BOOTSTRAP_ENABLED feature flag on
// /api/retrieval/capability/route.ts:
//
//   flag=true (forced ON via MARSYS_FLAG_RETRIEVAL_SINGLE_BOOTSTRAP_ENABLED=
//     true — code-complete and fully tested, PAUSED as the production default
//     pending D-4b quiet per master brief §I.6; see impl/w5-breaking)
//     — route.ts imports its registration list EXCLUSIVELY from
//     registry/catalog.ts's getCatalog(). After the W2b lane's catalog.ts
//     completeness fix (registerRouterCapabilities()/registerMaroCapabilities()/
//     registerD6SynergyCapabilities() now also fire from catalog.ts), the
//     single-bootstrap catalog is a superset of everything route.ts ever
//     hand-registered, PLUS the reverse gap (synth_compose_large_n,
//     marsys://tool/L-SPINE/query_spine_bundle).
//
//   flag=false (DEFAULT — the paused/current-production state, 2026-07-21)
//     — route.ts keeps its own hand-maintained per-wave registration list.
//     Byte-for-byte the same dispatch behavior the legacy path always had,
//     INCLUDING the documented gap: capabilities registered only via
//     registry/catalog.ts's import chain (currently
//     `marsys://tool/synthesis/compose_large_n` and
//     `marsys://tool/L-SPINE/query_spine_bundle`) are NOT reachable here.
//
// The flag defaults FALSE in feature_flags.ts DEFAULT_FLAGS — paused, not
// abandoned; see the "defaults" describe block below, which proves the
// flip-to-true path still works via explicit override, so the eventual
// production flip is a one-line, pre-verified change, never an untested one.

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { NextRequest } from 'next/server'

const ORIGINAL_ENV = { ...process.env }

function makeReq(body: unknown): NextRequest {
  return new NextRequest('http://localhost/api/retrieval/capability', {
    method: 'POST',
    headers: {
      'content-type': 'application/json',
      'x-mcp-internal-token': 'test-token',
    },
    body: JSON.stringify(body),
  })
}

/** Every registration entry point the legacy (flag=false) path hand-registers. */
const HAND_REGISTERED_GLOBAL_PROBE_URIS = [
  'marsys://tool/maro/orchestrate',
  'marsys://tool/maro/mcp_surface',
  'marsys://resource/maro/profiles',
  // synergy/pipeline + synergy/cross_layer are DB-backed (no-op here — see
  // the completeness assertion below, which checks registration presence
  // via listCapabilityUris() rather than dispatching them).
]

beforeEach(() => {
  vi.resetModules()
  process.env.MCP_INTERNAL_TOKEN = 'test-token'
  delete process.env.MARSYS_FLAG_RETRIEVAL_SINGLE_BOOTSTRAP_ENABLED
})

afterEach(() => {
  process.env = { ...ORIGINAL_ENV }
})

describe('RETRIEVAL_SINGLE_BOOTSTRAP_ENABLED — paused at false, flip pre-verified (2026-07-21)', () => {
  it('DEFAULT_FLAGS carries the flag as false (paused, not abandoned — see feature_flags.ts doc comment)', async () => {
    const { DEFAULT_FLAGS } = await import('@/lib/config/feature_flags')
    expect(DEFAULT_FLAGS.RETRIEVAL_SINGLE_BOOTSTRAP_ENABLED).toBe(false)
  })

  it('configService.getFlag reads false with no env override present', async () => {
    delete process.env.MARSYS_FLAG_RETRIEVAL_SINGLE_BOOTSTRAP_ENABLED
    const { configService } = await import('@/lib/config/index')
    expect(configService.getFlag('RETRIEVAL_SINGLE_BOOTSTRAP_ENABLED')).toBe(false)
  })

  it('configService.getFlag reads true when explicitly forced on via env (the flip stays live-verified while paused)', async () => {
    process.env.MARSYS_FLAG_RETRIEVAL_SINGLE_BOOTSTRAP_ENABLED = 'true'
    const { configService } = await import('@/lib/config/index')
    expect(configService.getFlag('RETRIEVAL_SINGLE_BOOTSTRAP_ENABLED')).toBe(true)
  })
})

describe('flag=true (forced on via override) — single bootstrap exclusively from catalog.ts', () => {
  beforeEach(() => {
    process.env.MARSYS_FLAG_RETRIEVAL_SINGLE_BOOTSTRAP_ENABLED = 'true'
  })

  for (const uri of HAND_REGISTERED_GLOBAL_PROBE_URIS) {
    it(`still dispatches ${uri} (present via catalog.ts after the completeness fix)`, async () => {
      const { POST } = await import('../route')
      const res = await POST(makeReq({ uri, args: {} }))
      expect(res.status).toBe(200)
      const json = await res.json()
      expect(json.ok).toBe(true)
    })
  }

  it('serves synth_compose_large_n — the reverse gap is closed under single bootstrap', async () => {
    const { POST } = await import('../route')
    const res = await POST(
      makeReq({ uri: 'marsys://tool/synthesis/compose_large_n', args: {} })
    )
    // per_chart scope with no chart_id supplied — must NOT be the "unknown
    // capability" 404; it should reach the real per-chart validation gate
    // instead (400 CHART_REQUIRED), proving the capability IS registered.
    expect(res.status).not.toBe(404)
    const json = await res.json()
    if (res.status !== 200) {
      const message = JSON.stringify(json)
      expect(message).not.toMatch(/Unknown capability URI/)
    }
  })

  it('serves query_spine_bundle — W5 L5\'s new capability, registered only via catalog.ts', async () => {
    const { POST } = await import('../route')
    const res = await POST(
      makeReq({ uri: 'marsys://tool/L-SPINE/query_spine_bundle', args: {} })
    )
    expect(res.status).not.toBe(404)
    const json = await res.json()
    if (res.status !== 200) {
      const message = JSON.stringify(json)
      expect(message).not.toMatch(/Unknown capability URI/)
    }
  })

  it('unknown URI still 404s (single-bootstrap path preserves the not-found behavior)', async () => {
    const { POST } = await import('../route')
    const res = await POST(makeReq({ uri: 'marsys://tool/does/not/exist', args: {} }))
    expect(res.status).toBe(404)
  })
})

describe('flag=false (forced via explicit env override — also the current default) — legacy hand-maintained path stays reachable', () => {
  beforeEach(() => {
    process.env.MARSYS_FLAG_RETRIEVAL_SINGLE_BOOTSTRAP_ENABLED = 'false'
  })

  for (const uri of HAND_REGISTERED_GLOBAL_PROBE_URIS) {
    it(`still dispatches ${uri} (route.ts's own hand-registered list, unchanged)`, async () => {
      const { POST } = await import('../route')
      const res = await POST(makeReq({ uri, args: {} }))
      expect(res.status).toBe(200)
      const json = await res.json()
      expect(json.ok).toBe(true)
    })
  }

  it('does NOT serve synth_compose_large_n — the pre-existing documented gap is preserved', async () => {
    const { POST } = await import('../route')
    const res = await POST(
      makeReq({ uri: 'marsys://tool/synthesis/compose_large_n', args: {} })
    )
    expect(res.status).toBe(404)
    const json = await res.json()
    expect(json.ok).toBe(false)
    expect(json.error).toContain('Unknown capability URI')
  })

  it('does NOT serve query_spine_bundle — W5 L5\'s capability is dormant under the paused default until the flip', async () => {
    const { POST } = await import('../route')
    const res = await POST(
      makeReq({ uri: 'marsys://tool/L-SPINE/query_spine_bundle', args: {} })
    )
    expect(res.status).toBe(404)
    const json = await res.json()
    expect(json.ok).toBe(false)
    expect(json.error).toContain('Unknown capability URI')
  })

  it('unknown URI still 404s exactly as the legacy path always did (no change to the not-found path)', async () => {
    const { POST } = await import('../route')
    const res = await POST(makeReq({ uri: 'marsys://tool/does/not/exist', args: {} }))
    expect(res.status).toBe(404)
  })
})

describe('flag=true (forced on) vs flag=false (default) — mechanical completeness diff (no missing, no duplicated)', () => {
  it('the single-bootstrap (flag=true) registered URI set is a strict superset of the legacy default (flag=false) set, with the exact known GT-40 divergence', async () => {
    // ── Pass 1: flag=false (forced off) — bootstrap route.ts's hand-maintained
    // list, snapshot the registry.
    vi.resetModules()
    process.env.MCP_INTERNAL_TOKEN = 'test-token'
    process.env.MARSYS_FLAG_RETRIEVAL_SINGLE_BOOTSTRAP_ENABLED = 'false'
    {
      const { POST } = await import('../route')
      await POST(makeReq({ uri: 'marsys://tool/maro/mcp_surface', args: {} }))
    }
    const { listCapabilityUris: listFalse } = await import('@/lib/retrieval/registry')
    const falseUris = listFalse()

    // ── Pass 2: flag=true (forced on via override — paused as the default,
    // see feature_flags.ts) — bootstrap exclusively from catalog.ts, snapshot
    // the registry.
    vi.resetModules()
    process.env.MCP_INTERNAL_TOKEN = 'test-token'
    process.env.MARSYS_FLAG_RETRIEVAL_SINGLE_BOOTSTRAP_ENABLED = 'true'
    {
      const { POST } = await import('../route')
      await POST(makeReq({ uri: 'marsys://tool/maro/mcp_surface', args: {} }))
    }
    const { listCapabilityUris: listTrue } = await import('@/lib/retrieval/registry')
    const trueUris = listTrue()

    // No duplicates in either set (Map-backed registry guarantees this structurally;
    // asserted explicitly per this lane's instructions, not just trusted).
    expect(new Set(falseUris).size).toBe(falseUris.length)
    expect(new Set(trueUris).size).toBe(trueUris.length)

    // No missing: every URI the legacy path served (flag=false) is still served
    // under single bootstrap (flag=true, forced on) — mechanically diffed, not hand-listed.
    const trueSet = new Set(trueUris)
    const missingUnderSingleBootstrap = falseUris.filter((uri) => !trueSet.has(uri))
    expect(
      missingUnderSingleBootstrap,
      `URIs served under the legacy path (flag=false) but MISSING under single bootstrap (flag=true, forced on):\n${missingUnderSingleBootstrap.join('\n')}`
    ).toHaveLength(0)

    // No duplicated capability EITHER direction: the only URIs present under
    // single bootstrap (flag=true, forced on) but absent under the legacy path (flag=false)
    // are the known reverse-gap set — a full symmetric mechanical diff, not a
    // spot check. This set is EXPECTED TO GROW over time now that
    // single-bootstrap is the production default (W5 L0): new capabilities
    // registered in catalog.ts going forward are not backported to the
    // legacy route.ts dual-list, which is a deprecated fallback path only
    // reachable via an explicit env override. Each addition here must be a
    // deliberately reviewed, real capability — never an accidental omission
    // from catalog.ts — so this asserts an exact known set (updated per
    // addition) rather than "at least" or "any", to keep the growth visible
    // and reviewed at merge time.
    //   - 'marsys://tool/synthesis/compose_large_n' — the original reverse
    //     gap, present since before the D-5 unpark flip.
    //   - 'marsys://tool/L-SPINE/query_spine_bundle' — W5 L5's new spine-
    //     bundle capability, registered only in catalog.ts (the modern path).
    const falseSet = new Set(falseUris)
    const trueOnly = trueUris.filter((uri) => !falseSet.has(uri))
    expect(trueOnly.sort()).toEqual([
      'marsys://tool/L-SPINE/query_spine_bundle',
      'marsys://tool/synthesis/compose_large_n',
    ])

    // The forward-divergent items (5 GT-40 originals + 1 newly-found —
    // marsys://tool/router/route was ALSO unreachable via catalog.ts before the
    // W2b completeness fix): present in both sets (the legacy path always
    // hand-registered them; catalog.ts now also registers them post-fix, so
    // they survive the flag switch either way).
    const forwardDivergentItems = [
      'marsys://tool/synergy/pipeline',
      'marsys://tool/synergy/cross_layer',
      'marsys://tool/maro/orchestrate',
      'marsys://tool/maro/mcp_surface',
      'marsys://resource/maro/profiles',
      'marsys://tool/router/route',
    ]
    for (const uri of forwardDivergentItems) {
      expect(falseUris, `${uri} missing from flag=false set`).toContain(uri)
      expect(trueUris, `${uri} missing from flag=true set`).toContain(uri)
    }
  })
})
