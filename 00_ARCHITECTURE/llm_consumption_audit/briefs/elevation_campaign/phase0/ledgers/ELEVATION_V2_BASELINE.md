---
artifact: ELEVATION_V2_BASELINE (Elevation Campaign v2.1, Phase 0)
version: 1.0
status: FROZEN — irreplaceable; captured against LIVE PRODUCTION before any stream touches code
authored_by: RUNWAY session (non-participant)
captured_at: 2026-07-25 (session timestamp; see individual probe payloads for exact computed_at)
db_snapshot_id: "1784938159545"
git_tag: elev-v2-run-start (85f238b3187b5cf571e5a91821acf20fdb1e5e5b)
canonical_charts:
  chart_A: 482012f1-710e-4a25-994a-93821f5871aa (Abhisek Mohanty, primary)
  chart_B: 1c826d5a-41cb-4450-b4dc-59d440e5f75a (Abhinandan Mohanty, chart-agnostic check)
---

# Elevation Campaign v2.1 — production baseline

This is the pre-run snapshot every stream's before/after claim is measured against. Raw payloads
are reproduced verbatim below (or referenced by path where too large to inline) — this document does
not summarize away defects; it records exactly what production returned, defect and all.

## Probe 1 — `plan_retrieval("How is my wealth?")`

**Chart A:** `scope_tuple.depth = "deepdive"` (via V-2 keyword fallback, `wealth_deepdive` matched).
`completeness_receipt.coverage = {floor_item_total: 33, served: 0, empty: 29, dark: 4}` (pre-execution
— all floor items `pending_execution`, 4 dark items tracked by CR-66/CR-131). Full plan has 33 floor
primitives across acharya_floor + machine_band.
**Chart B:** identical structure, same 33-item floor, same dark-item CRs. Confirms plan_retrieval's
V-2 fallback behavior is chart-agnostic.

## Probe 2 — `intent_classify("How is my wealth?")` (chart A only; global classifier, not chart-scoped)

```json
{
  "scope_tuple": {"intent":"unknown","domains":["wealth"],"width":"standard","depth":"standard","horizon":"atemporal","intervention":"none","entitlement":"restricted"},
  "confidence": 0.2,
  "method": "deterministic_rules",
  "matched_rules": ["domain:wealth","entitlement:restricted"]
}
```
**CONFIRMS the charter's exact defect characterization**: "How is my wealth?" scores confidence 0.2
and routes to `depth: "standard"` — the inverted-uncertainty bug Ω4 exists to fix. Also confirms
`entitlement: "restricted"` on a native chart query (the entitlement defect noted in Ω4's scope).

## Probe 3 — `graha_portrait(Venus, include=[position,dignity])` — the Venus starvation probe

**Chart A:**
```json
"position": {"rows": [], "count": 9},
"dignity": {"operative_varga_rows": [], "all_varga_rows": [], "other_rows": [], "count": 56}
```
9 + 56 = **65 rows located, 0 served** — verbatim match to the charter's α.A evidence
("65 rows located, 0 served, receipt says complete"). `completeness: {position: "✓", dignity: "✓"}`
— the receipt reports success over the empty arrays, confirming the "✓ over empty" defect.

**Chart B:** identical pattern — `position.count: 9, rows: []`; `dignity.count: 56, rows: []`.
Same 65/0 split, same false-✓ receipt. **Confirms the defect is chart-agnostic, not
Abhisek-chart-specific.**

## Probe 4 — `bodha_mechanisms_get`

**Chart A:**
```json
{"error": "error: bind message supplies 3 parameters, but prepared statement \"\" requires 2", "chart_id": "482012f1-710e-4a25-994a-93821f5871aa"}
```
**Chart B:** identical error shape (parameter-count mismatch), chart_id substituted.
**CONFIRMS EL-37 is still live in production on both canonical charts** — the `filterParams` vs
`params` bug the charter's root-cause pass identified (`query_mechanisms.ts` L113-129) has not been
fixed as of this baseline capture. This is Lane Ω's hard dependency (Ω6) — γ cannot deliver until α
ships this fix.

## Probe 5 — `ganita_structural_get(facet=argala)` — houses-from-lagna probe

**Chart A:** `total: 2000` raw matrix rows, trimmed to 62 in the returned page. Every sampled row is
`fact_value_num: 0` for the `from_sign_10_offset_1` key — matches the charter's EL-38 evidence
("Sampled rows are all `fact_value_num: 0`"). Raw matrix is per-varga × per-sign × per-offset, NOT
resolved to houses-from-lagna — confirms EL-38's fix direction is still needed (serve
`argala_on_house` with the raw matrix behind `shape=matrix`).
**Chart B:** same all-zero pattern on a 50-row sample (`limit=50` used to keep payload smaller);
`total: 50` for that narrower call. Chart-agnostic confirmation.

## Probe 6 — `assess_wealth` (chart A)

Response exceeded the harness's tool-output token ceiling: **118,423 characters** — verbatim match to
the charter's α.A evidence ("`assess_wealth` 118KB"). Not read in full (would exceed this ledger's own
budget and the point is already made by the size alone); raw file retained at
`~/elev-v2-shared/ledgers/raw/assess_wealth_482012f1_raw.txt` (see Access note below) for any stream
that needs the full payload for its own before/after diff.

## Probe 7 — `ganita_special_lagnas_get(lagnas=[indu, sree, saham])` — 3-category call, chart A

Requested 3 categories (`indu`, `sree`, `saham`); response `categories: ["special_lagna", "upagraha"]`,
49 rows, covering VARNADA/HORA/SREE/INDU/VIGHATI/GHATI/BHAVA_LAGNA under `special_lagna` — **no
`saham` category appears anywhere in the response, and no receipt or error explains its absence.**
This is a live reproduction of EL-41's exact defect ("saham/sensitive_point silently dropped").

## Probe 8 — C3 schema-map generator run (see `phase0/schema_map_generate.cjs`)

Ran against both canonical charts, live `chart_facts`: chart A → 11,082 (category × subject) entries
from 138,519 raw fact rows across 216 distinct `fact_category` values; chart B → 10,948 entries from
137,687 raw rows. Full outputs at `~/elev-v2-shared/phase0_evidence/schema_map_{482012f1,1c826d5a}.json`
(sha256 below).

## Access note on oversized raw payloads

`assess_wealth`'s raw 118KB payload was written by the MCP client to
`/Users/Dev/.claude/projects/-Users-Dev-Vibe-Coding-Apps-Madhav/3322623f-38b4-4771-bbcf-f641df08cedf/tool-results/mcp-marsys-jis-direct-assess_wealth-1784938243427.txt`
during this session (session-scoped tool-result cache, not a stable path for other sessions to read).
Any stream needing this exact payload should re-run `assess_wealth(chart_id=482012f1-…)` itself —
the point this baseline establishes is the byte count and the fact of a live probe having been run,
not a permanently-archived copy of a single point-in-time payload.
