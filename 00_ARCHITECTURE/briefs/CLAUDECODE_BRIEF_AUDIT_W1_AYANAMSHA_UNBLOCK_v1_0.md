---
canonical_id: CLAUDECODE_BRIEF_AUDIT_W1_AYANAMSHA_UNBLOCK
version: 1.0
status: READY-FOR-EXECUTION — Wave 1 of the system-audit fix plan; the highest-leverage fix
created: 2026-07-01
author: Cowork (from the live MCP audit) — for execution by Claude Code
parent: MCP_SYSTEM_AUDIT_FIX_PLAN_v1_0 (Wave 1) · evidence in MCP_SYSTEM_AUDIT_FINDINGS_v1_0 (§C.1)
frozen_seam: RETRIEVAL_MCP_UNIFIED_AUDIT_AND_SYNC_CONTRACT §4 (retrieval FROZEN; MCP adapts)
verification_basis: live MCP connector probes 2026-07-01 (documented below with exact before/after)
hard_constraints:
  - build gate (platform-mcp + platform tsc exit 0); prod-verify after merge; VITEST not jest
  - retrieval stays chart-agnostic + FROZEN; do NOT change stored data or the seal — this is a QUERY/DEFAULT fix
  - reverse-citation before any delete
acceptance_criteria: see §5
---

# CLAUDE CODE BRIEF — WAVE 1: AYANAMSHA UNBLOCK (F-006 / F-011 / F-031)

> The single highest-leverage fix in the audit. The entire L2 insight surface returns EMPTY on default calls
> because tools default to ayanamsha `'LAHIRI'` while the signals are stored under `'lahiri_chitrapaksha'` — the
> join returns 0 rows. Proven live: same call, same chart, `LAHIRI` → 0 signals; `lahiri_chitrapaksha` → 12,954
> signals. This is a query/default alignment fix. It does NOT touch stored data or the retrieval seal.

## §1 — The evidence (live, reproducible)
- `get_signals(482012f1)` with DEFAULT ayanamsha → `msr_signal_count: 0`, `top_signals: []`.
- `get_signals(482012f1, ayanamsha_id="lahiri_chitrapaksha")` → **12,954 signals**, 90 yogas, 22 doshas,
  1,034 contradictions, full convergence_domains.
- `get_chart_quality` scorecard content self-reports `ayanamsha_id: "lahiri_chitrapaksha"` while its embedded
  orientation_context reports `ayanamsha_id: "LAHIRI"` (empty). The mismatch is visible in one response.
- Affected (all empty on default, all expected to light up): get_signals, get_chart_orientation,
  get_domain_reading, get_temporal_windows, get_chart_quality's orientation block, and every reasoning-unit /
  domain tool that flows through the signal store.

## §2 — Diagnose the fix layer FIRST (don't guess)
The default could live in (a) the MCP tool schema defaults (`platform-mcp/src/tools/registry_bridge.ts` — the
`ayanamsha_id` default in each tool's input schema, seen as `'LAHIRI'`), or (b) the registry capability /
serving query in `platform/src/lib/retrieval/` that filters signals by ayanamsha, or (c) both. Determine:
1. What ayanamsha value is the signal store actually keyed on? Confirm `bodha_msr_signals` (or the served view)
   stores `lahiri_chitrapaksha` (the scorecard says so; verify in the serving query's WHERE/JOIN).
2. Where does the request's ayanamsha get its default + how is it compared to the stored value — exact vs
   normalized? Find the comparison site.

## §3 — The fix (alias + standardize; the safe, seam-respecting approach)
Prefer an ALIAS/normalization layer over blindly flipping every default (aliasing is backward-compatible and
fixes the whole vocabulary problem F-031 at once):
1. **Canonical id + alias map:** establish `lahiri_chitrapaksha` as the canonical stored id, and a normalization
   map so `LAHIRI`, `lahiri`, `Lahiri`, `lahiri_chitrapaksha`, `true_chitra`/`true_citra` (verify which is
   canonical) all resolve to the canonical value the store uses — applied at the serving/query boundary BEFORE
   the ayanamsha filter. This closes F-006 AND F-031 (the vocabulary chaos across tools: compute_natal_positions
   uses `lahiri`, query_calibration uses `true_chitra`, get_signals uses `LAHIRI` — no single vocabulary today).
2. **Default:** make the effective default resolve to the canonical stored id, so a NO-ayanamsha call returns
   data. (Whether you change the literal default or let the alias layer map the existing `'LAHIRI'` default to
   canonical — either works; the alias approach means you don't have to touch every tool's schema.)
3. Do this at the layer that owns the ayanamsha comparison (per §2). If it's the registry serving query, this is
   a retrieval-side change — coordinate per §4 (it's a query normalization, not a seal/data change, so it should
   be within-fork-safe, but confirm it doesn't alter chart-agnostic guarantees).
4. Do NOT rebuild or re-key stored data. Do NOT change the sealed signal counts. This is purely making the read
   path speak the same ayanamsha vocabulary the data is stored in.

## §4 — Seam note
This is a SERVING/normalization fix, not a data or contract change. If the fix lands in `lib/retrieval` (the
frozen layer), it's a query-normalization refinement (not an entitlement or capability-shape change) — keep it
minimal and confirm the chart-agnostic gate stays green. If it can be done purely in the MCP tool layer
(defaults + a normalization helper before the registry call), prefer that (keeps retrieval untouched). Choose
the layer that actually owns the comparison; document which.

## §5 — VERIFICATION PHASE (mandatory; prove on prod)
**V1 — Build gate:** platform-mcp + platform `npm run build` exit 0; typecheck-mcp CI green.
**V2 — Unit test:** the alias/normalization map (all known ayanamsha spellings → canonical); a default-call test
  asserting the ayanamsha resolves to the stored value.
**V3 — Deploy + revision match:** deployed amjis-mcp revision SHA == merged SHA.
**V4 — The behavioral proof (the whole point) on PROD, via the live connector, ≥2 charts:**
  - `get_signals(<chart>)` with NO ayanamsha arg → returns >0 signals (was 0). Assert ~12,954 for 482012f1.
  - `get_chart_orientation(<chart>)` default → non-empty digest + top_signals + convergence_domains.
  - `get_domain_reading` + `get_temporal_windows` default → non-empty (or confirm any still-empty one has a
    DIFFERENT root cause, not ayanamsha).
  - Explicit `LAHIRI`, `lahiri`, `lahiri_chitrapaksha` ALL now return the SAME non-empty result (alias works).
  - Re-run on the non-native chart 1c826d5a → non-empty + DISTINCT from native (chart-agnostic intact).
**V5 — No-regression:** the deterministic tools (compute_natal_positions etc.) still work; stored signal counts
  unchanged (scorecard still 64,765) — we changed the READ, not the data.
**On ANY V-failure:** remediation loop; no done-claim until V1–V5 pass on prod.

## §6 — Acceptance criteria
- A default (no-ayanamsha) call to the L2 insight tools returns data on prod (F-006 closed).
- One canonical ayanamsha vocabulary + alias normalization; LAHIRI/lahiri/lahiri_chitrapaksha all resolve
  (F-011, F-031 closed).
- Stored data + seal counts UNCHANGED (read-path-only fix); retrieval chart-agnostic gate green; Vitest;
  prod revision == merged SHA. Re-run the connector probe as the witness.

*End of CLAUDECODE_BRIEF_AUDIT_W1_AYANAMSHA_UNBLOCK v1.0. This flips the product from sealed-but-empty to
serving. After it lands, re-audit Wave 5 (salience + synthesis) on fully-lit data.*
