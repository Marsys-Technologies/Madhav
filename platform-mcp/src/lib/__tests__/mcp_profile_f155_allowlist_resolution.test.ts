/**
 * mcp_profile_f155_allowlist_resolution.test.ts — F-155 ruled test (PARIŚEṢA V4)
 * ================================================================================
 * F-155: the compact/consult MCP surface-profile allowlists (`MCP_SURFACE_PROFILES`,
 * `platform-mcp/src/generated/mcp_surface_profiles.generated.ts`) used to carry the
 * registry's INTERNAL capability names (`cap.name`) where the request-time serving
 * gate (`applyProfileGate` below) matches the PUBLIC name a real `server.tool(...)`
 * call registers under. Fails closed — an unmatched name is simply never callable,
 * no security exposure — but under-serves.
 *
 * THE RULED TEST (not a re-derivation of the fix's own extractor — see below):
 * registers the REAL, FULL platform-mcp server surface (every `register*Tools()`
 * call site `server.ts` itself makes, in the same order) against a capturing fake
 * `McpServer`, applies the SAME two gates a live request applies
 * (`applyDeprecatedToolGate` then `applyProfileGate`), and asserts every name the
 * generated compact/consult allowlists declare is ACTUALLY present in that real,
 * gated registration set. This is deliberately independent of
 * `extract_registrar_capability_bridge.ts` (the fix's own source-text scanner) —
 * a bug in that scanner would not be caught by re-running the same scanner as the
 * test oracle, so this test instead exercises the real registration code path,
 * the same way a live MCP request does.
 *
 * Companion assertion: `prashna_ask` / `prashna_status` / `mcp_server_info` are
 * registered in `server.ts` BEFORE `applyProfileGate` runs (see that file's own
 * "W6 Task 7" / "W6 Part 3" / "EL-13" comments) — a deliberate PRE-GATE BYPASS,
 * not part of the retrieval-registry catalog the generated manifest is built
 * from. This test declares that exemption explicitly (asserts all three are
 * absent from the generated manifest's own tool_names, and that they nonetheless
 * pass the real gate under EVERY profile) rather than leaving it implicit.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import type { Principal } from '../../types.js'
import { applyDeprecatedToolGate } from '../deprecated_tool_gate.js'
import { applyProfileGate, type ToolRegisteringServer } from '../mcp_profile.js'
import { MCP_SURFACE_PROFILES } from '../../generated/mcp_surface_profiles.generated.js'

import { registerL0BrahmagyanTools } from '../../tools/l0_brahmagyan.js'
import { registerEphemerisTools } from '../../tools/l0_ephemeris.js'
import {
  registerReadClassicalText,
  registerReadChapter,
  registerListClassicalTexts,
  registerFindVersesAbout,
  registerSearchClassicalTexts,
} from '../../tools/read_classical_text.js'
import {
  registerComputeNatalPositionsTool,
  registerQuerySpecialLagnasTool,
} from '../../tools/retrieval/pyhora_natal.js'
import { registerHolisticBundleRetrievalTool } from '../../tools/retrieval/holistic_bundle.js'
import { registerKalaTemporalRetrievalTool } from '../../tools/retrieval/kala_temporal.js'
import { registerGocharaWindowsTools } from '../../tools/retrieval/register_gochara_windows.js'
import { registerRemedyTools } from '../../tools/retrieval/remedy_tools.js'
import { registerPhalaEventAnchorsTool } from '../../tools/phala_event_anchors.js'
import { registerMitigationMapTool } from '../../tools/phala_mitigation_map.js'
import { registerMuhurtaFinder } from '../../tools/muhurta_finder.js'
import { registerPhalaOutlookTool } from '../../tools/phala_outlook.js'
import { registerMimamsaLelIntakeTool } from '../../tools/mimamsa_lel_intake.js'
import { registerMechanismRetrodictionTool } from '../../tools/mechanism_retrodiction.js'
import { registerMimamsaOutcomeTool } from '../../tools/mimamsa_outcome.js'
import { registerRegistryBridgeTools } from '../../tools/registry_bridge.js'
import { registerP1GanitaTools } from '../../tools/register_p1_ganita.js'
import { registerP1ReferenceTools } from '../../tools/register_p1_reference.js'
import { registerP1SynthesisTools } from '../../tools/register_p1_synthesis.js'
import { registerP1AliasTools } from '../../tools/register_p1_aliases.js'
import { registerP2DashaLordTools } from '../../tools/register_p2_dasha_lord.js'
import { registerScanFetchTool } from '../../tools/scan_fetch_signals.js'
import { registerReadingNotesTool } from '../../tools/reading_notes.js'
import { registerChartSelectionTools } from '../../tools/chart_selection.js'
import { registerSessionTools } from '../../tools/session_tools.js'
import { registerVidhiPlanTool } from '../../tools/register_vidhi_plan.js'
import { registerDossierTool } from '../../tools/dossier.js'
import { registerPrashnaAskTool } from '../../tools/register_prashna_ask.js'
import { registerPrashnaStatusTool } from '../../tools/register_prashna_status.js'
import { registerServerInfoTool } from '../../tools/register_server_info.js'

const PRINCIPAL: Principal = { user_uid: 'f155-test-user', key_id: 'f155-test-key', role: 'super_admin' }

/** Bare name-capturing fake `McpServer` — mirrors the established idiom in
 *  `platform-mcp/src/__tests__/r6_0b_deadtools_smoke.test.ts` /
 *  `samapana_trackb_exhaustive.test.ts`, widened to just record names (this test
 *  never invokes a handler, only asserts on the REGISTERED NAME SET). */
function makeCapturingServer(): { server: McpServer; names: Set<string> } {
  const names = new Set<string>()
  const server = {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    tool: (name: string, ..._rest: any[]) => {
      names.add(name)
    },
  } as unknown as McpServer
  return { server, names }
}

/**
 * Registers the REAL, FULL platform-mcp tool surface — same call list, same order,
 * as `server.ts`'s request handler (minus resources/prompts, which are a different
 * registration surface `applyProfileGate` does not gate). `deprecatedGate` and
 * `profileGate` are applied at the SAME two points `server.ts` applies them: the
 * deprecated-name gate first (unconditional, every profile), then
 * `registerPrashnaAskTool`/`registerPrashnaStatusTool`/`registerServerInfoTool`
 * (the documented pre-gate bypass), THEN the profile gate, THEN everything else.
 */
function registerFullServerSurface(server: McpServer, profile: 'full' | 'compact' | 'consult') {
  applyDeprecatedToolGate(server as unknown as ToolRegisteringServer)

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  registerPrashnaAskTool(server as any, PRINCIPAL, profile)
  registerPrashnaStatusTool(
    server as unknown as import('../../tools/register_prashna_status.js').PrashnaStatusRegisteringServer,
  )
  registerServerInfoTool(server)

  applyProfileGate(server as unknown as ToolRegisteringServer, profile)

  registerL0BrahmagyanTools(server)
  registerEphemerisTools(server)
  registerReadClassicalText(server, () => PRINCIPAL)
  registerReadChapter(server, () => PRINCIPAL)
  registerListClassicalTexts(server, () => PRINCIPAL)
  registerFindVersesAbout(server, () => PRINCIPAL)
  registerSearchClassicalTexts(server, () => PRINCIPAL)
  registerComputeNatalPositionsTool(server)
  registerQuerySpecialLagnasTool(server)
  registerHolisticBundleRetrievalTool(server, () => PRINCIPAL)
  registerKalaTemporalRetrievalTool(server, PRINCIPAL)
  registerGocharaWindowsTools(server, PRINCIPAL)
  registerRemedyTools(server, () => PRINCIPAL)
  registerPhalaEventAnchorsTool(server, PRINCIPAL)
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  registerMitigationMapTool(server as any, PRINCIPAL)
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  registerMuhurtaFinder(server as any, () => PRINCIPAL)
  registerPhalaOutlookTool(server, PRINCIPAL)
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  registerMimamsaLelIntakeTool(server as any, PRINCIPAL)
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  registerMechanismRetrodictionTool(server as any, PRINCIPAL)
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  registerMimamsaOutcomeTool(server as any, PRINCIPAL)
  registerRegistryBridgeTools(server, PRINCIPAL)
  registerP1GanitaTools(server, PRINCIPAL)
  registerP1ReferenceTools(server, PRINCIPAL)
  registerP1SynthesisTools(server, PRINCIPAL)
  registerP1AliasTools(server, PRINCIPAL)
  registerP2DashaLordTools(server, PRINCIPAL)
  registerScanFetchTool(server, PRINCIPAL)
  registerReadingNotesTool(server)
  registerChartSelectionTools(server, PRINCIPAL)
  registerSessionTools(server, PRINCIPAL)
  registerVidhiPlanTool(server, PRINCIPAL)
  registerDossierTool(server, PRINCIPAL)
}

beforeEach(() => {
  vi.unstubAllGlobals()
  process.env['SERVICE_TOKEN'] = 'f155-test-service-token'
})

describe('F-155 — MCP profile allowlists resolve against the real registration set', () => {
  it.each(['compact', 'consult'] as const)(
    'every %s-profile allowlist name is actually registered and reachable through the real gate — ZERO unresolved names',
    (profile) => {
      const { server, names } = makeCapturingServer()
      registerFullServerSurface(server, profile)

      const allowlist = MCP_SURFACE_PROFILES[profile].tool_names
      expect(allowlist.length).toBeGreaterThan(0) // sanity: the fixture isn't accidentally empty

      const unresolved = allowlist.filter((n) => !names.has(n))
      expect(
        unresolved,
        `${profile} allowlist names with NO real, gated server.tool() registration: ${JSON.stringify(unresolved)}`,
      ).toEqual([])
    },
  )

  it('the "full" profile allowlist also resolves (the profile gate is a no-op for full, but the generated manifest should still be honest)', () => {
    const { server, names } = makeCapturingServer()
    registerFullServerSurface(server, 'full')
    const allowlist = MCP_SURFACE_PROFILES.full.tool_names
    expect(allowlist.length).toBeGreaterThan(0)
    const unresolved = allowlist.filter((n) => !names.has(n))
    expect(unresolved).toEqual([])
  })

  // ── Companion assertion: the 3 pre-gate-bypass tools' exemption, declared explicitly ──

  const PRE_GATE_BYPASS_TOOLS = ['prashna_ask', 'prashna_status', 'mcp_server_info'] as const

  it('the 3 documented pre-gate-bypass tools (prashna_ask, prashna_status, mcp_server_info) are absent from the generated manifest under every profile — they are not part of the retrieval-registry catalog it is built from', () => {
    for (const profile of ['full', 'compact', 'consult'] as const) {
      for (const name of PRE_GATE_BYPASS_TOOLS) {
        expect(
          MCP_SURFACE_PROFILES[profile].tool_names.includes(name),
          `${name} unexpectedly appears in the generated ${profile} manifest — the pre-gate ` +
            'bypass exemption below assumes it does not (see server.ts "W6 Task 7"/"W6 Part 3"/"EL-13")',
        ).toBe(false)
      }
    }
  })

  it('the 3 pre-gate-bypass tools nonetheless register successfully under EVERY profile (registered before applyProfileGate runs, per server.ts)', () => {
    for (const profile of ['full', 'compact', 'consult'] as const) {
      const { server, names } = makeCapturingServer()
      registerFullServerSurface(server, profile)
      for (const name of PRE_GATE_BYPASS_TOOLS) {
        expect(names.has(name), `${name} missing from the real registration set under profile=${profile}`).toBe(true)
      }
    }
  })
})
