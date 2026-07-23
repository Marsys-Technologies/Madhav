/**
 * retrieval/holistic_bundle.ts — BRAHMA-BO-2-9: B.11 Whole-Chart-Read composite tool
 *
 * B.11 Whole-Chart-Read discipline: every query routes through L2.5 Holistic
 * Synthesis first (MSR + CDLM + CGM + RM) before producing a domain-specific answer.
 *
 * This tool reads DIRECTLY from chart_facts (L1 + L2 bodha.* categories):
 *   1. ganita.positions   — L1 planet positions (Lahiri ayanamsha)
 *   2. bodha.signals      — L2 MSR signals (SCAFFOLD: 569 signals, all UNGROUNDED)
 *   3. bodha.domain_links — L2 CDLM cross-domain linkages
 *   4. bodha.resonance    — L2 RM resonance patterns
 *   5. bodha.graph        — L2 CGM edges (optional — enriches context)
 *
 * Tool name:  holistic_bundle
 * Input:      { chart_id?: string, include_graph?: boolean }
 * Output:     {
 *               positions, signals, domain_links, resonance, graph_edges?,
 *               grounding_status: 'SCAFFOLD',
 *               b11_floor_passed: boolean,
 *               provenance_envelope
 *             }
 *
 * Grounding status notice: ALL signals in this bundle carry:
 *   rule_id: null, grounding_status: 'UNGROUNDED'
 *   grounding_note: 'Scaffold pass — awaiting WS-3 rule_base'
 * This is a scaffold bundle. The l2-bodha-grounded session (after tag
 * ws3-rule-base-complete) re-derives with real rule IDs.
 *
 * Wiring: registerHolisticBundleRetrievalTool(server) in server.ts
 * Note: bo_2-8.ts (holistic_bundle via sidecar) remains registered in parallel.
 *
 * BRAHMA-BO-2-9 / l2-bodha-scaffold
 */

import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { z } from 'zod'
import { callPlatformBundle } from '../../client.js'
import type { Principal, McpEnvelopeError } from '../../types.js'
import { finalizeMcpBudget, type TrimmableSection } from '../../lib/response_budget.js'

// R5.2 A2 (punch #3, estate-wide budget sweep): this tool's default call measured 544KB
// on the native chart (worst offender in the estate) — envelope.bundle_entries carries the
// full un-ceilinged 8-subsystem scaffold dump. This tool is already documented elsewhere
// (register_p1_aliases.ts DEFERRED list) as the legacy path being superseded by
// bodha_bundle_get; applying the shared budget trimmer here rather than a deeper rewrite
// keeps the fix minimal and reversible pending that replacement.
const HOLISTIC_BUNDLE_BUDGET_KB = 30

// Live-verification fix (post-first-deploy): the platform bundle endpoint nests
// bundle_entries under `envelope`, not at the result's top level — the first version of
// this section read the wrong path and silently found nothing to trim (confirmed live:
// 544KB in, 544KB out, trim_report showed the hard-cap fallback firing on zero actual
// cuts). Reads both locations defensively so this doesn't silently break again if the
// nesting ever flips back.
function bundleEntriesSection(): TrimmableSection<Record<string, unknown>> {
  const locate = (c: Record<string, unknown>): { holder: Record<string, unknown>; arr: unknown[] } | null => {
    const nested = c['envelope'] as Record<string, unknown> | undefined
    if (nested && Array.isArray(nested['bundle_entries'])) {
      return { holder: nested, arr: nested['bundle_entries'] as unknown[] }
    }
    if (Array.isArray(c['bundle_entries'])) {
      return { holder: c, arr: c['bundle_entries'] as unknown[] }
    }
    return null
  }
  return {
    path: 'bundle_entries', label: 'bundle_entries', minKeep: 2,
    getArray: (c) => locate(c)?.arr,
    setArray: (c, kept) => {
      const loc = locate(c)
      if (loc) loc.holder['bundle_entries'] = kept
    },
    // SC-17 fix: 'bodha_bundle_get' was never registered as an MCP tool (a planned rename
    // that never shipped) — recovering via it 404'd exactly when data was withheld. The
    // live, registered tool for the full multi-subsystem bundle is THIS tool itself,
    // 'bodha_bundle_get' (registered below via registerHolisticBundleRetrievalTool).
    recover: { instrument: 'bodha_bundle_get', hint: 'full multi-subsystem bundle — call again (this call trimmed bundle_entries to fit the MCP response budget).' },
  }
}

// CR-14/39 (D-2 V-3): per-subsystem sub-error detection. The bundle endpoint may fold a failing
// subsystem into bundle_entries while still returning a 200/ok top-level envelope. This scans every
// entry (at either nesting location) for an error marker and returns the named, failing subsystems.
// Pure + exported so a test can drive it against a synthetic partial-ok bundle (anti-vacuous: the
// induced sub-error must actually be caught, §F1.7 anti-vacuous tests).
export type BundleSubError = { subsystem: string; error: string }

export function collectBundleSubErrors(result: Record<string, unknown>): BundleSubError[] {
  const nested = result['envelope'] as Record<string, unknown> | undefined
  const entries =
    (nested && Array.isArray(nested['bundle_entries']) ? nested['bundle_entries'] : undefined) ??
    (Array.isArray(result['bundle_entries']) ? result['bundle_entries'] : undefined) ??
    []
  const out: BundleSubError[] = []
  for (const e of entries as unknown[]) {
    if (!e || typeof e !== 'object') continue
    const entry = e as Record<string, unknown>
    const status = String(entry['status'] ?? entry['grounding_status'] ?? '').toUpperCase()
    const failed =
      entry['ok'] === false ||
      entry['is_error'] === true ||
      entry['isError'] === true ||
      entry['error'] != null ||
      status === 'ERROR' || status === 'FAILED' || status === 'FAIL'
    if (!failed) continue
    const subsystem = String(
      entry['subsystem'] ?? entry['name'] ?? entry['source'] ?? entry['key'] ?? entry['category'] ?? 'unknown',
    )
    const errObj = entry['error']
    const error =
      typeof errObj === 'string' ? errObj
      : errObj && typeof errObj === 'object' && typeof (errObj as Record<string, unknown>)['message'] === 'string'
        ? (errObj as Record<string, unknown>)['message'] as string
        : `sub-tool reported status=${status || 'error'}`
    out.push({ subsystem, error })
  }
  return out
}

// REMEDIATION D7: NATIVE_CHART_ID removed. chart_id is now REQUIRED from caller.
// chart_agnostic_gate RULE-1/RULE-4: no default on chart_id.
// R2.1 (2026-06-30): Repointed from direct pg.Pool to callPlatformPrimitive —
// registry = served surface. No local Pool instantiation.

// ── Tool registration ──────────────────────────────────────────────────────────

export function registerHolisticBundleRetrievalTool(server: McpServer, getPrincipal: () => Principal): void {
  // REMEDIATION D7: chart_id is now REQUIRED (no default fallback to native chart).
  // chart_agnostic_gate RULE-1: per_chart scope → chart_id in required_inputs.
  // R2.1: delegates to callPlatformPrimitive('holistic_bundle', params) — no local Pool.
  server.tool(
    'bodha_bundle_get',
    {
      chart_id: z.string().uuid().describe(
        'Chart UUID. Required — no default chart.'
      ),
      include_graph: z.boolean().optional().default(false).describe(
        'Include bodha.graph (CGM edge set) in the bundle. Default: false.'
      ),
    },
    async ({ chart_id, include_graph = false }) => {
      if (!chart_id) {
        return {
          content: [{ type: 'text' as const, text: JSON.stringify({ error: 'chart_id is required', tool: 'bodha_bundle_get' }, null, 2) }],
          isError: true,
        }
      }

      try {
        // D-C fix: route through bundle endpoint (not surgical primitives)
        const { status, envelope } = await callPlatformBundle(
          'holistic_bundle',
          { chart_id, include_graph },
          getPrincipal(),
        )

        if (status !== 200 || !envelope.ok) {
          return {
            content: [{
              type: 'text' as const,
              text: JSON.stringify({
                status: 'ERROR',
                error: (envelope as McpEnvelopeError).error?.message ?? status,
                chart_id,
                grounding_status: 'SCAFFOLD',
                b11_floor_passed: false,
              }, null, 2),
            }],
            isError: true,
          }
        }

        const resultObj = envelope.result as Record<string, unknown>

        // CR-14/39 (D-2 V-3, ledger row 28): a top-level 200/ok envelope could still carry a
        // per-subsystem FAILURE folded into bundle_entries — the prior code passed that through as
        // success (silent partial-ok), so a B.11 whole-chart-read could report a hole as if it were
        // complete. Scan every bundle_entry for an error marker; if ANY sub-tool failed, surface an
        // explicit sub_errors section AND downgrade to non-ok (isError). An honest whole-chart read
        // never hides a missing subsystem behind an ok envelope.
        const subErrors = collectBundleSubErrors(resultObj)

        // W3-L5 (budget unification, W-8): the sub_errors annotations below are now written
        // BEFORE the budget pass runs (previously they were appended AFTER — an un-measured
        // attachment, the exact gap finalizeMcpBudget's self-verifying re-measurement exists
        // to close) so the final trim decision accounts for the true full content, not a
        // pre-annotation snapshot of it.
        if (subErrors.length > 0) {
          resultObj['status'] = 'PARTIAL_ERROR'
          resultObj['b11_floor_passed'] = false
          resultObj['sub_errors'] = subErrors
          resultObj['sub_errors_note'] =
            `${subErrors.length} subsystem(s) failed inside the bundle. This is NOT a complete ` +
            'whole-chart read (B.11) — the failing subsystems are named in sub_errors; do not treat ' +
            'the served sections as exhaustive. Retry, or call the named subsystem tool directly.'
        }

        const budgeted = finalizeMcpBudget(resultObj, {
          maxKb: HOLISTIC_BUNDLE_BUDGET_KB,
          sections: [bundleEntriesSection()],
        })

        if (subErrors.length > 0) {
          return {
            content: [{ type: 'text' as const, text: JSON.stringify(budgeted) }],
            isError: true,
          }
        }

        return {
          content: [{
            type: 'text' as const,
            // Compact, not pretty-printed — the budget mechanism measures compact bytes;
            // indentation is exactly the kind of gap the C1 live-verifier already caught
            // once for other tools (a response that "should" be under budget by the
            // trimmer's own measurement but ships larger over the actual wire).
            text: JSON.stringify(budgeted),
          }],
        }
      } catch (err) {
        const msg = err instanceof Error ? err.message : String(err)
        return {
          content: [{
            type: 'text' as const,
            text: JSON.stringify({
              status: 'ERROR',
              error: msg,
              chart_id,
              grounding_status: 'SCAFFOLD',
              b11_floor_passed: false,
            }, null, 2),
          }],
          isError: true,
        }
      }
    }
  )
}
