---
artifact: SARVA_SIDDHI_TRUTH_TABLE
version: 1.0
status: CURRENT — campaign work order
produced_during: SARVA-SIDDHI campaign, W-0 (truth pass)
produced_on: 2026-07-24
governing: BRIEF_SARVA_SIDDHI_v1_0.md §0.2 ("truth before work") + §0.4 (165/300 question)
role: >
  Live-probed verdict for all 16 items named in BRIEF_SARVA_SIDDHI_v1_0.md before any W-1..W-4
  dispatch is sized or scoped. Three parallel Opus agents ran read-only DB queries, source
  grep, PR/commit history, and (where OAuth-reachable) live MCP tool calls against chart_id
  482012f1-710e-4a25-994a-93821f5871aa. No files were edited during W-0. Supersedes the
  Tier-C accept-as-dark list in PRE_DARPANA_READINESS_v1_1.md — those rulings are rescinded
  per native order; every REAL-OPEN/PARTIAL row below gets a real fix in W-1..W-4.
---

# SARVA-SIDDHI Truth Table — W-0 verdicts

## Cluster 1 — Gochara / temporal core (CR-131 and the "165/300" question)

**Verdict: REAL-OPEN.** The native's recollection ("scoring moved event-driven, then a
successful full execution followed") is **not supported** — corrected, not confirmed.

- `ka_gochara_sweep` for 482012f1: **16 build_run attempts total, zero successful completions
  — including every run after the D-4b event-driven reconciliation** (which landed
  2026-07-21 23:11 IST; memoization commit `103b6607` landed 2026-07-21 05:13). Failure modes:
  `orphaned_by_crash` (orchestrator died mid-flight) and `BLOCKED: upstream timeout` at the
  1800s/21600s job budget. The two most recent post-D-4b runs both died at exactly 360 min on
  the 6h budget.
- Substep frontier: **165/300 done, 135 remaining**, keyed `event_class:year:N` (N=0..99 ×
  3 classes). Per-class frontier is uneven: career_advancement 88/100, major_gain 76/100,
  **marriage 1/100** (only year 63 done — this is the bulk of remaining work, not evenly
  spread).
- Measured real speedup post-memoization: **~4.65 min/substep (≈5-6x)**, not the brief's
  assumed "~600x faster". Real remaining wall-clock: 135 × 4.65 ≈ **~10.5 hours** — exceeds
  one 6h job budget by itself, so T-2 **must** be ≥2 resumable dispatches, sized from this
  measured rate, not the brief's inherited estimate.
- `kala_gochara_windows` live: 3,148 rows, span **1949-12-31 → 2037-09-30** (not the brief's
  assumed 2026-2055). By event_class: career_advancement 3,094, marriage 52, major_gain 2
  (confirmed exactly against prior-session memory). By decade: 1950s 203, 1960s-80s ~475/ea,
  1990s 412, 2000s 231, 2010s 426, 2020s 364, 2030s 80.
- **New risk flagged for T-2 sizing**: substeps are keyed 0..99 anchored near the ~1950 epoch;
  at face value this design tops out around **~2049, short of birth+100y = 2084**. T-2 must
  confirm/fix the substep→year mapping before dispatch, not just resume the existing plan.
- DATABASE_URL gap on the three gochara serving tools (`gochara_activation_get`,
  `gochara_forecast_get`, `gochara_election_avoidance_get`): **REAL-OPEN, unchanged** since the
  prior PRE-DARPANA session. All three return `backing_data_reachable:false`,
  `empty_reason:"...DATABASE_URL not set..."`. Confirmed isolated to these three tools (control
  call to `ganita_chart_facts_get` returned real data — not a general MCP outage).
- **Write access: read-only confirmed** (`transaction_read_only=on`, user `amjis_app`). An
  agent session cannot INSERT a `build_runs` row directly — T-2 re-dispatch requires either the
  authenticated cockpit web API (as A-3 found) or new credentials; this is a genuine
  infrastructure constraint, not a code gap, and W-1/T-2 must investigate/resolve it explicitly
  rather than assume it away.

## Cluster 2 — Suspected stale register drift (CR-68, CR-16)

**Both confirmed STALE-CLOSED — register drift, no code work needed. Close here.**

- **CR-68** (`mechanism_retrodiction_get`) — shipped in **PR #688** (merged 2026-07-21,
  `5f27d9d2`, "D-4b B-5 mechanism_retrodiction surface"). Tool registered, wired through
  `tool_name_bridge.ts`, backing capability implemented, real data present (39 pre-2020 LEL
  events, 45,882 dasha rows for 482012f1). **Register still says OPEN** in
  `registry_data.ts:214`, `cr_status.ts:74`, and migration `462`'s seed — this is the drift.
  Register-reconciliation action: flip CR-68 to resolved, repoint the `lel_retrodiction`
  primitive's `live_tool` from `mimamsa_lel_query` to `mechanism_retrodiction_get`.
- **CR-16** (`ganita_special_lagnas_get` chart_id mode) — fixed in **PR #594 / D-2** (commit
  `20e2da8e`). `register_p1_aliases.ts:1549-1590` accepts optional `chart_id`, serves stored
  facts entitlement-gated. 245 real `special_lagna` facts for 482012f1. **Register still says
  OPEN** in `registry_data.ts:97` (despite that same row's `tool_args` already showing
  `chart_id: '{chart_id}'`) and `cr_status.ts:43`. Register-reconciliation action: flip CR-16
  to resolved.

## Cluster 3 — Remaining Tier-C CR premises (re-confirmed live)

| CR | Verdict | Finding |
|---|---|---|
| **CR-130** (Jaimini spiritual yoga family) | **PARTIAL** | Parashari `pravrajya_yoga` detector already exists and fires correctly (L0 catalog `l0_yogas.py:860` + L1 firing `ga_yoga_writer.py:1043`; 0 rows for this native is a correct-negative, no 4+ stellium). The **Jaimini karakāṃśa** spiritual family (`jaimini_karakamsha_jupiter/venus/sun`, `l0_yogas.py:1146+`) exists in the L0 **catalog only** — zero L1 firing detector, not even a catalog row in the firings table. Real work: build the Jaimini firing detector — the Parashari half needs no work. |
| **CR-61** (arudha/UL ranking) | **STALE-CLOSED** | Landed via V-5 emitter, PR #585. Live `bodha_signals_get(signal_type_class=arudha)` returns real ranked rows (`arudha:AL_conjunction:JUP/VEN` salience 0.5148, `ARUDHA_A11_tenancy`, `ARUDHA_A2_tenancy`) with `computed_salience`+`valence`. Register predates the wave. Close as register-drift. |
| **CR-64** (nakshatra-semantic ranking) | **STALE-CLOSED** | Same V-5 wave. Live `bodha_signals_get(signal_type_class=nakshatra_semantic)` → 9 ranked rows with dispositor_chain/tara/gandanta/salience/valence. Minor residual noted (16.7% orphan constituent refs, reader description still DRAFT) but the ranking itself is live — close core CR as register-drift, file the residual separately if native wants it tracked. |
| **CR-24** (mechanism chain/circuit motifs first-class) | **PARTIAL** | Named-valenced object built (`bo_yantra_mechanism.py`, promotes `bodha_cgm_motifs`→`bodha_yantra_mechanisms` 1:1 with real valence + cycle detection). BUT (a) no dedicated MCP serving tool — reachable only via `bodha_graph_traverse_get` subgraph traversal; (b) this native's chart legitimately has no literal 10→8→12→10 circuit (writer's own comments confirm the real structure here is a `convergent_dispositor_chain`; correct-negative). Real work: surface a dedicated serving face over the already-built table. |
| **CR-73** (bespoke dosha cancellation) | **PARTIAL** | False-positive doshas already suppressed via B9 gating (`catalog_only_rows_present`, `fire_reason:"requires_pass"` on all 22 dosha_label rows) — harm mitigated. But real per-dosha cancellation/bhaṅga adjudication exists for **only** Neecha Bhanga Raja Yoga; the kemadruma-vs-Anapha contradiction the register cites is suppressed, not resolved. Real work: bespoke cancellation checks beyond NBRY. |
| **CR-30** (KP cusp/sub-lord dedicated face) | **REAL-OPEN** | No dedicated KP tool exists — `kp_query`/`query_kp_ruling_planets` were PHANTOM-DROPPED (migration 024 archived, no engine backs them). KP data (`cusp_lord`/`sub_lord`) does exist at L1 (`facts_store.ts`, `types.ts`) but is reachable only via the general `ganita_chart_facts_get` category route. Real work: dedicated first-class KP face over existing L1 data — no new computation needed, a serving/routing fix. |

## Summary — register corrections vs. real work

**Close as register-drift (no code, reconcile registers only):** CR-68, CR-16, CR-61, CR-64.
**Real work required (rescinded from accept-as-dark, no accept-as-dark remains per native
order):** CR-131/T-2 (gochara materialization + DATABASE_URL + substep-span check), CR-37,
CR-66, CR-67, CR-69, CR-130 (Jaimini half only), CR-24 (serving face only), CR-73 (beyond
NBRY), CR-30 (dedicated face). §N.6 disclosure repairs (`phala_predictive_anchors_get`
empty_reason, `yoga_activation_scan` floor wiring) remain real work as scoped in A-6.

This table is the work order for W-1..W-4; dispatch below is sized from it.
