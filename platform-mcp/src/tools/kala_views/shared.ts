/**
 * kala_views/shared.ts — ṢAḌ-DARŚANA W0.4 (SHAD_DARSHANA_BRIEF_v2_0.md §3 W0.4 · §2 file map).
 * ==========================================================================
 * Small internal support module for THIS lane's two facades (`kala_priority_get`,
 * `kala_explain_get`) — not one of the eight kala_* tools itself. Mirrors the existing
 * `callRegistryCap` pattern already duplicated per-registration-file in this codebase
 * (register_p1_aliases.ts, registry_bridge.ts's `callRegistryCapability`) rather than
 * reaching into either of those files' private (non-exported) helpers — this file's own
 * copy is the third, deliberately-kept-local instance of that pattern, scoped to the two
 * facades that share it so they don't duplicate it a fourth/fifth time between themselves.
 *
 * Also carries the shared MCP response-budget wiring for the two facades: the kala_envelope
 * hardFloor evidence section (CLAUDE.md §N.6) plus the generic auto-detected sections
 * (response_budget.ts), matching the `dualOutput` pattern every other registration file in
 * this package already uses.
 */

import type { Principal } from '../../types.js'
import {
  finalizeMcpBudget,
  autoDetectTrimmableSections,
  type TrimmableSection,
} from '../../lib/response_budget.js'
import { kalaEvidenceTrimmableSection, type ArgumentReading } from '../../lib/kala_envelope.js'

// ── Registry capability caller ──────────────────────────────────────────────────────

const PLATFORM_URL = (process.env['PLATFORM_URL'] ?? 'http://localhost:3000').replace(/\/$/, '')
const MCP_INTERNAL_TOKEN = process.env['MCP_INTERNAL_TOKEN'] ?? ''

/**
 * Call a registry capability via the platform's /api/retrieval/capability endpoint — the
 * SAME path `kala_priority_ranking_get` (register_p1_aliases.ts) and `pact_query`
 * (registry_bridge.ts) already use to reach `marsys://tool/L3/call_priority_ranking` and
 * `marsys://tool/L-PACT/pact_query` respectively. This lane's two facades wrap those exact
 * capabilities (W0: no new computation) — calling the SAME underlying URIs, not a second
 * implementation of either.
 */
export async function callKalaRegistryCap(
  uri: string,
  args: Record<string, unknown>,
  principal: Principal,
): Promise<unknown> {
  const res = await fetch(`${PLATFORM_URL}/api/retrieval/capability`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-MCP-Internal-Token': MCP_INTERNAL_TOKEN,
      'X-MCP-User': principal.user_uid,
      'X-MCP-Key-Id': principal.key_id,
    },
    body: JSON.stringify({ uri, args }),
    signal: AbortSignal.timeout(25_000),
  })
  if (!res.ok) {
    const text = await res.text().catch(() => '')
    throw new Error(`[kala_views] capability '${uri}' failed (${res.status}): ${text.slice(0, 300)}`)
  }
  const data = (await res.json()) as { ok: boolean; content?: unknown; error?: string }
  if (!data.ok) {
    throw new Error(`[kala_views] capability '${uri}' error: ${data.error ?? 'unknown'}`)
  }
  return data.content
}

/** Defensive unwrap — `/api/retrieval/capability` returns `{ok, content}`; `content` is the
 *  actual capability payload. Handles a caller that already unwrapped (belt-and-suspenders,
 *  mirrors register_p1_aliases.ts's `unwrapCapabilityPayload`). */
export function unwrapKalaPayload(data: unknown): Record<string, unknown> {
  if (data && typeof data === 'object' && !Array.isArray(data)) {
    const obj = data as Record<string, unknown>
    if ('is_error' in obj && 'content' in obj && obj['content'] && typeof obj['content'] === 'object') {
      return obj['content'] as Record<string, unknown>
    }
    return obj
  }
  return {}
}

// ── Dual output + budget wiring ─────────────────────────────────────────────────────

const KALA_VIEWS_RESPONSE_BUDGET_KB = 40

const DUAL_OUTPUT_TEXT_THRESHOLD_BYTES = 50_000

/**
 * Applies the kala_envelope hardFloor evidence section (`reading.evidence` — §N.6: the
 * densest, most-actionable layer is protected first) plus the generic auto-detected
 * sections (raw substrate passthrough arrays this facade did not hand-declare), then
 * returns the MCP dual-output shape. Mirrors register_p1_aliases.ts's `dualOutput`.
 */
export function kalaBudgetedDualOutput<T extends Record<string, unknown> & { reading: ArgumentReading }>(
  content: T,
  toolName: string,
): { structuredContent: { type: 'object'; object: unknown }; content: Array<{ type: 'text'; text: string }> } {
  const sections: TrimmableSection<T>[] = [
    kalaEvidenceTrimmableSection<T>({
      instrument: toolName,
      hint: 'full evidence list for this reading (this response kept a lean, budget-trimmed slice).',
    }),
    ...autoDetectTrimmableSections(content, toolName),
  ]
  const finalized = finalizeMcpBudget(content, { maxKb: KALA_VIEWS_RESPONSE_BUDGET_KB, sections })
  const structuredContent = { type: 'object' as const, object: finalized }
  const json = JSON.stringify(finalized)
  if (Buffer.byteLength(json, 'utf8') > DUAL_OUTPUT_TEXT_THRESHOLD_BYTES) {
    return { structuredContent, content: [{ type: 'text' as const, text: '[large payload — see structuredContent]' }] }
  }
  return { structuredContent, content: [{ type: 'text' as const, text: json }] }
}

export function kalaErrorOutput(tool: string, msg: string, extra?: Record<string, unknown>) {
  return {
    structuredContent: { type: 'object' as const, object: { ok: false, error: msg, tool, ...extra } },
    content: [{ type: 'text' as const, text: JSON.stringify({ ok: false, error: msg, tool, ...extra }) }],
    isError: true as const,
  }
}

/** Rounds to 3 decimals for display — never invents precision the underlying scalar
 *  doesn't have; just keeps composed prose from carrying float noise. */
export function round3(n: number | null | undefined): number | null {
  if (n === null || n === undefined || Number.isNaN(n)) return null
  return Math.round(n * 1000) / 1000
}
