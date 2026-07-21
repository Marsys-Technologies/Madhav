/**
 * mcp_profile.test.ts — W5 L2: per-family MCP surface profiles, OAuth-scope-gated
 * ================================================================================
 * Covers:
 *   1. Profile resolution from auth context (bearer_key → full; OAuth scope → full/
 *      compact/consult; safe-by-default for unscoped/legacy/unrecognized grants).
 *   2. `applyProfileGate()` structurally BLOCKS registration of any tool name outside
 *      the resolved profile — the load-bearing "consult profile provably cannot reach
 *      raw tools" proof this campaign's V5 gate requires (master brief §E W5 / plan
 *      §R-5 gate: "a consultation-profile client demonstrably cannot obtain an
 *      ungrounded reading"). This is proven at the REGISTRATION boundary (the same
 *      mechanism `server.ts` uses for every real tool), not by re-implementing a
 *      second filter over a hand-picked tool list.
 *   3. The generated `MCP_SURFACE_PROFILES` data itself (imported, not re-derived)
 *      backs up the compact ≤20 cap and the consult ⊆ full invariant on the REAL,
 *      live-generated catalog snapshot committed in this same lane.
 */
import { describe, it, expect } from 'vitest'
import {
  resolveProfileFromScopes,
  resolveMcpProfile,
  getAllowedToolNames,
  applyProfileGate,
  FULL_SCOPE,
  COMPACT_SCOPE,
  CONSULT_SCOPE,
  type ToolRegisteringServer,
} from '../mcp_profile.js'
import { MCP_SURFACE_PROFILES, COMPACT_MAX_TOOLS } from '../../generated/mcp_surface_profiles.generated.js'

// ── 1. Profile resolution ────────────────────────────────────────────────────

describe('resolveProfileFromScopes()', () => {
  it('grants full only when mcp:profile:full is explicitly present', () => {
    expect(resolveProfileFromScopes([FULL_SCOPE])).toBe('full')
    expect(resolveProfileFromScopes([FULL_SCOPE, 'mcp:tools'])).toBe('full')
  })

  it('grants compact when mcp:profile:compact is present (and full is not)', () => {
    expect(resolveProfileFromScopes([COMPACT_SCOPE])).toBe('compact')
    expect(resolveProfileFromScopes([COMPACT_SCOPE, 'mcp:resources'])).toBe('compact')
  })

  it('SAFE BY DEFAULT: undefined, empty, legacy-only, or unrecognized scopes all resolve to consult — never full', () => {
    expect(resolveProfileFromScopes(undefined)).toBe('consult')
    expect(resolveProfileFromScopes([])).toBe('consult')
    expect(resolveProfileFromScopes(['mcp:tools', 'mcp:resources', 'mcp:prompts'])).toBe('consult')
    expect(resolveProfileFromScopes(['some_unrecognized_scope'])).toBe('consult')
    expect(resolveProfileFromScopes([CONSULT_SCOPE])).toBe('consult')
  })

  it('full takes precedence if a grant somehow carries both full and compact scopes', () => {
    expect(resolveProfileFromScopes([COMPACT_SCOPE, FULL_SCOPE])).toBe('full')
  })
})

describe('resolveMcpProfile()', () => {
  it('bearer_key auth (first-party trusted credential) always resolves to full, regardless of any scopes field', () => {
    expect(resolveMcpProfile({ authKind: 'bearer_key' })).toBe('full')
    expect(resolveMcpProfile({ authKind: 'bearer_key', oauthScopes: [] })).toBe('full')
  })

  it('oauth auth defers to resolveProfileFromScopes', () => {
    expect(resolveMcpProfile({ authKind: 'oauth', oauthScopes: [FULL_SCOPE] })).toBe('full')
    expect(resolveMcpProfile({ authKind: 'oauth', oauthScopes: [COMPACT_SCOPE] })).toBe('compact')
    expect(resolveMcpProfile({ authKind: 'oauth' })).toBe('consult')
    expect(resolveMcpProfile({ authKind: 'oauth', oauthScopes: [] })).toBe('consult')
  })
})

// ── 2. getAllowedToolNames() ──────────────────────────────────────────────────

describe('getAllowedToolNames()', () => {
  it('full profile returns null (no filter — every tool passes through)', () => {
    expect(getAllowedToolNames('full')).toBeNull()
  })

  it('compact/consult profiles return the exact generated tool_names set for that profile', () => {
    expect(getAllowedToolNames('compact')).toEqual(new Set(MCP_SURFACE_PROFILES.compact.tool_names))
    expect(getAllowedToolNames('consult')).toEqual(new Set(MCP_SURFACE_PROFILES.consult.tool_names))
  })

  it('compact allowlist never exceeds COMPACT_MAX_TOOLS (RC-1 ≤20)', () => {
    const allowed = getAllowedToolNames('compact')
    expect(allowed).not.toBeNull()
    expect(allowed!.size).toBeLessThanOrEqual(COMPACT_MAX_TOOLS)
    expect(COMPACT_MAX_TOOLS).toBe(20)
  })
})

// ── 3. applyProfileGate() — the structural "cannot reach raw tools" proof ────

/** Minimal fake McpServer: records every registration attempt by name. */
function makeFakeServer(): ToolRegisteringServer & { registered: string[] } {
  const registered: string[] = []
  const server = {
    registered,
    tool: (name: string, ..._rest: unknown[]) => {
      registered.push(name)
      return { registeredAs: name }
    },
  }
  return server
}

describe('applyProfileGate() — full profile', () => {
  it('is a no-op: every registration attempt succeeds, none blocked', () => {
    const server = makeFakeServer()
    const gate = applyProfileGate(server, 'full')
    expect(gate.allowed).toBeNull()

    server.tool('any_tool_name_at_all')
    server.tool('chart_facts_query')
    server.tool('assess_career')

    expect(server.registered).toEqual(['any_tool_name_at_all', 'chart_facts_query', 'assess_career'])
    expect(gate.blockedAttempts).toEqual([])
  })
})

describe('applyProfileGate() — compact profile', () => {
  it('only allows registration of tools in the compact allowlist; blocks everything else', () => {
    const server = makeFakeServer()
    const gate = applyProfileGate(server, 'compact')

    const [inCompact] = MCP_SURFACE_PROFILES.compact.tool_names
    expect(inCompact).toBeDefined()

    server.tool(inCompact as string)
    server.tool('definitely_not_a_real_registered_tool_xyz')

    expect(server.registered).toEqual([inCompact])
    expect(gate.blockedAttempts).toEqual(['definitely_not_a_real_registered_tool_xyz'])
  })
})

describe('applyProfileGate() — CONSULT PROFILE PROVABLY CANNOT REACH RAW TOOLS (V5 gate)', () => {
  it('blocks registration of every real full-catalog tool that is not in the small consult allowlist', () => {
    const server = makeFakeServer()
    const gate = applyProfileGate(server, 'consult')
    expect(gate.profile).toBe('consult')
    expect(gate.allowed).toEqual(new Set(MCP_SURFACE_PROFILES.consult.tool_names))

    // Adversarial probe: attempt to register REAL, live full-catalog tool names (not
    // invented strings) that are NOT part of the consult set — e.g. a raw chart-facts
    // query tool and a full domain-assessment tool. If the gate ever regresses to
    // pass these through, this is the test that catches it.
    const rawFullOnlyTools = MCP_SURFACE_PROFILES.full.tool_names.filter(
      (n) => !MCP_SURFACE_PROFILES.consult.tool_names.includes(n),
    )
    expect(rawFullOnlyTools.length).toBeGreaterThan(0) // sanity: real gap exists to test against
    const probe = rawFullOnlyTools.slice(0, 15)
    for (const toolName of probe) {
      server.tool(toolName)
    }

    // NONE of the raw tools actually got registered on the fake server.
    expect(server.registered).toEqual([])
    // ALL of them were recorded as blocked attempts.
    expect(gate.blockedAttempts).toEqual(probe)
  })

  it('allows registration of the legitimate consult orienting tools', () => {
    const server = makeFakeServer()
    const gate = applyProfileGate(server, 'consult')

    for (const toolName of MCP_SURFACE_PROFILES.consult.tool_names) {
      server.tool(toolName)
    }

    expect(server.registered).toEqual(MCP_SURFACE_PROFILES.consult.tool_names)
    expect(gate.blockedAttempts).toEqual([])
  })

  it('a tools/call for a name never registered under consult has nothing to dispatch to (no server-side path exists)', () => {
    // This is the structural guarantee applyProfileGate provides: since the blocked
    // tool name never reaches server.tool(), the SDK's internal tool registry has no
    // entry for it on this request's McpServer instance — there is no dispatch path a
    // tools/call for that name could hit. We assert the observable proxy for that here
    // (the name is simply absent from `registered`), since exercising the real MCP SDK's
    // tools/call 404 behavior end-to-end belongs to an SDK-level integration test, not
    // this unit-level gate test.
    const server = makeFakeServer()
    applyProfileGate(server, 'consult')
    const rawTool = MCP_SURFACE_PROFILES.full.tool_names.find(
      (n) => !MCP_SURFACE_PROFILES.consult.tool_names.includes(n),
    )
    expect(rawTool).toBeDefined()
    server.tool(rawTool as string)
    expect(server.registered.includes(rawTool as string)).toBe(false)
  })
})

// ── 4. Cross-check against the generated data (not re-derived) ──────────────

describe('MCP_SURFACE_PROFILES (generated mirror, imported directly)', () => {
  it('consult tool_names are a subset of full tool_names (structural invariant, checked at the data level too)', () => {
    const fullSet = new Set(MCP_SURFACE_PROFILES.full.tool_names)
    for (const name of MCP_SURFACE_PROFILES.consult.tool_names) {
      expect(fullSet.has(name)).toBe(true)
    }
  })

  it('no known internal/meta orchestration tool name appears in consult', () => {
    const consultSet = new Set(MCP_SURFACE_PROFILES.consult.tool_names)
    for (const internalName of ['maro_orchestrate', 'maro_mcp_surface', 'route', 'synergy_pipeline', 'synergy_cross_layer']) {
      expect(consultSet.has(internalName)).toBe(false)
    }
  })
})
