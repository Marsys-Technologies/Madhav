/**
 * parity_check.test.ts — GT-36 (RETRIEVAL_PLANE_ELEVATION_PLAN_v1_0.md §1.5, §3 R-0.5).
 *
 * S-4 disposition record: before this file existed, `checkParity()` /
 * `runParityCheck()` had NO caller anywhere in the repo — no CI workflow step, no npm
 * script, no test (confirmed by repo-wide grep). Its concern (MCP tool exports vs the
 * Consume Chat capability registry) is NOT covered by
 * `scripts/manifest/parity_validator.ts`, which validates a different pair of surfaces
 * entirely (CANONICAL_ARTIFACTS_v1_0.md / CAPABILITY_MANIFEST.json / FILE_REGISTRY drift —
 * governance-doc bookkeeping, not tool/URI parity). So per the plan's R-0.5 instruction
 * ("first confirm parity_check is even in the enforcement path before fixing it"), the
 * disposition here is FIX + WIRE, not delete:
 *
 *   1. Prove the GT-36 degenerate-both-empty auto-pass bug is fixed
 *      (buildParityResult() now forces passed=false whenever bridge_error is set, even
 *      when both URI sets are empty — previously only the populated case hard-failed).
 *   2. BE the CI gate itself — this file is wired into .github/workflows/ci.yml's
 *      unit-tests job as a dedicated named step (mirrors the existing WP-1.7 /
 *      whitelist_resolution_invariant.test.ts convention of a named `npx vitest run
 *      <this file>` step so a regression is unmistakable in CI logs, not buried in the
 *      general `npm test` run).
 *
 * Scope note: the live-gate suite below intentionally does NOT assert
 * `result.passed === true`. A live probe run during S-4 investigation found the
 * hand-maintained MCP_TOOL_TO_URI map in mcp_capability_bridge.ts has drifted badly from
 * the real Consume Chat registry (47 mapped vs 118 real capabilities; 89 missing_in_mcp,
 * 18 extra_in_mcp as of 2026-07-19) — a large, pre-existing backlog unrelated to GT-36's
 * bridge-failure bug. Reconciling that map is separate, larger scope (tracked
 * out-of-band); hard-gating on it here would immediately red CI over unrelated work. What
 * IS gated hard: the bridge module must import cleanly (bridge_error === null) — that is
 * the exact invariant GT-36 was about.
 */
import { describe, it, expect } from 'vitest'
import './catalog' // populate the real Consume Chat registry (side-effect import; WP-1.7 convention)
import { checkParity, buildParityResult, getMcpExportedUris } from './parity_check'
import type { CapabilityUri } from './types'

describe('GT-36 — bridge-failure invariant (pure decision function)', () => {
  it('a failed bridge import is a hard failure even when both URI sets are empty (the degenerate auto-pass bug)', () => {
    const result = buildParityResult(
      new Set<CapabilityUri>(),
      new Set<CapabilityUri>(),
      'bridge import threw: simulated failure'
    )
    expect(result.bridge_error).not.toBeNull()
    expect(result.passed).toBe(false)
    expect(result.missing_in_mcp).toEqual([])
    expect(result.extra_in_mcp).toEqual([])
  })

  it('a failed bridge import is a hard failure in the normal populated case too (pre-existing correct behavior, unchanged)', () => {
    const consumeUris = new Set<CapabilityUri>(['marsys://tool/L0/resolve_entity'])
    const result = buildParityResult(consumeUris, new Set<CapabilityUri>(), 'bridge import threw: simulated failure')
    expect(result.passed).toBe(false)
    expect(result.missing_in_mcp).toEqual(['marsys://tool/L0/resolve_entity'])
  })

  it('a successful bridge with matching URI sets passes and bridge_error is null', () => {
    const uris = new Set<CapabilityUri>(['marsys://tool/L0/resolve_entity'])
    const result = buildParityResult(uris, uris, null)
    expect(result.bridge_error).toBeNull()
    expect(result.passed).toBe(true)
  })

  it('a successful bridge with a real URI mismatch still fails (unaffected by the GT-36 fix)', () => {
    const consumeUris = new Set<CapabilityUri>(['marsys://tool/L0/a', 'marsys://tool/L0/b'])
    const mcpUris = new Set<CapabilityUri>(['marsys://tool/L0/a'])
    const result = buildParityResult(consumeUris, mcpUris, null)
    expect(result.passed).toBe(false)
    expect(result.bridge_error).toBeNull()
    expect(result.missing_in_mcp).toEqual(['marsys://tool/L0/b'])
  })

  it('the true degenerate case (both empty, bridge healthy) still passes — only a FAILED bridge forces failure', () => {
    const result = buildParityResult(new Set<CapabilityUri>(), new Set<CapabilityUri>(), null)
    expect(result.bridge_error).toBeNull()
    expect(result.passed).toBe(true)
  })
})

describe('GT-36 — live CI gate (real registry + real bridge, no mocks)', () => {
  it('the MCP capability bridge module imports cleanly (bridge_error is null against the real module)', async () => {
    const { bridgeError, uris } = await getMcpExportedUris()
    expect(bridgeError).toBeNull()
    expect(uris.size).toBeGreaterThan(0)
  })

  it('runs the real checkParity() end-to-end and never silently fabricates a pass while the bridge is broken', async () => {
    const result = await checkParity()
    // Hard gate: the bridge must load. This is the exact GT-36 invariant.
    expect(result.bridge_error).toBeNull()
    // Reported, not hard-failed: URI-set drift is a separate, pre-existing, larger
    // backlog (see file header) — surfaced here so it stays visible in CI logs.
    if (!result.passed) {
      console.warn(
        `[parity_check gate] URI drift present (separate from GT-36; not hard-gated here) — ` +
          `mcp=${result.mcp_count} consume=${result.consume_count} ` +
          `missing_in_mcp=${result.missing_in_mcp.length} extra_in_mcp=${result.extra_in_mcp.length}`
      )
    }
  })
})
