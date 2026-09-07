---
artifact: L2_W6_CLOSE_REPORT_v1_0.md
canonical_id: NIRMANA_V21_L2_W6_CLOSE_REPORT
version: "1.0-DRAFT"
status: SCAFFOLD — W4/W5/W6 have not run; this is C8.5 productive-wait prep, not a submitted
  capsule. Sections below are filled from W1–W3's actual, verified work; the W4/W5/W6-specific
  sections (build results, capsule refs, freeze event) are placeholders pending three external
  gates — the L1 freeze ceremony (E-gate for bo_laksana 15/21 + bo_laksana_rerank 15/24 unfrozen
  ancestors), the #1770 bo_sudarshana open question, and the #2258 bo_grounding manifest ruling.
produced_on: 2026-09-07 (drafted mid-campaign, cycle 817; finalized and re-dated at actual W6)
owner: L2 session (this file is mine alone — charter C5; not Conductor-owned)
---

# L2 — Bodha — W6 Close Report (DRAFT SCAFFOLD)

Per `NIRMANA_UNIFIED_ELEVATION_PLAN_v2_0.md` §4 the close report is the whole W6 ceremony.
Drafted ahead of W4/W5/W6 per the C8.5 productive-wait guidance, following L4's precedent
(`L4_W6_CLOSE_REPORT_v1_0.md`, same DRAFT-SCAFFOLD discipline). Everything below reflects
**verified, shipped** work as of this draft; nothing is asserted ahead of evidence. Line items
marked `[W4-PENDING]` / `[W5-PENDING]` / `[W6-PENDING]` are the placeholders the real ceremony
fills.

## 1. Assets and routes taken

All 22 `bo_*` assets routed at W2 (`L2_W2_DECIDE_v1_0.md`, 22 routes / 14 MUST / 25 NOW /
8 LATER, three adjudications #1716/#1720/#1726 all since ruled). 9 route `changed`, 13 route
`rebuild_only`. **No `verified_reuse`** (20 of 22 `state='stale'` on the canonical chart, and
the layer has never been rebuilt coherently as a unit — no build evidence to reuse); no
`probe`/`producer_covered`/`static`/`empty`/`retired` (all 22 are `asset_kind='data'` with a
live writer and live consumer, W1 finding E12).

| asset_id | W2 route | W3 outcome (verified as of this draft) | terminal state |
|---|---|---|---|
| `bo_laksana` | changed | salience-truth writer corrections MERGED (#1741: six unwritten columns bound into INSERT, AV bhinna feed, argala live, vargottama L1 authority, honest NULLs for cancellation/neechabhanga, C1 corroboration fabrication removed) — writer, not data; rebuild held | `[W4-PENDING]` — canary-adjacent; double-gated (#1770 snapshot-restorable precondition now satisfied; L1 freeze E-gate 15/21 open) |
| `bo_karanajala` | changed | B7/A13 addressed in the W3 wave (consensus-count constant + §N.5 argala re-derivation) | `[W4-PENDING]` |
| `bo_samskara` | changed | re-key on `embedding_input_summary` shipped — kills the 100% Vertex re-embed cost coupling to `bo_laksana` rebuilds | `[W4-PENDING]` |
| `bo_samvada` | changed | B8 `count_sql` + B9 phantom-columns fixed; owns the D-SYNTHESIS rollups (migration 662 wave) | `[W4-PENDING]` |
| `bo_sudarshana` | changed | D5 percentile setter + C1 sibling fixed (#1755 wave) | `[W4-PENDING]` — dispatch additionally held on the #1770 co-writer question (posted loop ~676, unruled) |
| `bo_nakshatra_semantic` | changed | D5 + C1 sibling fixed | `[W4-PENDING]` |
| `bo_arudha` | changed | D5 + C1 sibling fixed | `[W4-PENDING]` |
| `bo_special_lagna` | changed | D5 + C1 sibling fixed | `[W4-PENDING]` |
| `bo_vargottama_dhana` | changed | D5 + A5 (vargottama amplification smuggled through `class_prior`) fixed | `[W4-PENDING]` |
| `bo_laksana_rerank` | rebuild_only | agreement-line writer complete (migration 662): `cross_system_consensus_count` / `contradicts_signals_array` populate at dispatch | `[W4-PENDING]` — E-gate 15/24 unfrozen ancestors |
| `bo_bimba` | rebuild_only | E1 registry correction (130× wrong `expected_volume_formula`) in the 660-wave | `[W4-PENDING]` |
| `bo_sangati` | rebuild_only | E8 divergence (535 vs 280) deliberately deferred to W5 investigation, not pre-fixed | `[W4-PENDING]`, then `[W5-PENDING]` E8 |
| `bo_drishti` | rebuild_only | — | `[W4-PENDING]` |
| `bo_anveshana` | rebuild_only | D1 was a serving defect: tail lane plumbed TS-side (see §3 D-SALIENCE) | `[W4-PENDING]` |
| `bo_cgm_motifs` | rebuild_only | — | `[W4-PENDING]` |
| `bo_cgm_paths` | rebuild_only | — | `[W4-PENDING]` |
| `bo_chart_gestalt` | rebuild_only | E6 registry correction | `[W4-PENDING]` |
| `bo_cdlm_summary` | rebuild_only | registry correction | `[W4-PENDING]` |
| `bo_pratijna` | rebuild_only | — | `[W4-PENDING]` |
| `bo_upaya` | rebuild_only | `expected_volume_formula` shipped (migration 760, #2021); `contradiction_factor` self-activates once B1's column populates | `[W4-PENDING]` |
| `bo_pramana_mapa` | rebuild_only | B10 verified no-work (six flags carry real detectors, `notes.n8_detectors`) | `[W4-PENDING]` |
| `bo_yantra_mechanism` | rebuild_only | — | `[W4-PENDING]` |

**Not in the 22 (net-new, born mid-campaign):** `bo_grounding` — the D-GROUNDING tier writer
(#2258, native ruling D-NATIVE-09). Matcher + writer + tests shipped (PR #2379); registration
deferred because the receipt spine pins L2 to the frozen manifest's 22 assets — disposition
(manifest amendment / pins extension / hold-to-close) is with the Conductor. Its terminal
state at W6 follows that ruling, not this table.

## 2. Findings ledger outcome

- W1: 47 findings triaged at W2 (14 MUST / 25 NOW / 8 LATER). MUST-tier items closed or
  writer-complete in W3 waves per §1; `[W5-PENDING]` re-triage of any MUST whose fix can only
  be proven on post-rebuild data.
- Cross-layer findings filed by L2, both upheld and campaign-shaping: #1770 (CASCADE blast
  radius 864,733 rows / 12 tables / 3 layers → campaign-wide hold, D-CND-15/16; ruled order:
  L2 MSR rebuild first, L3 re-runs after) and the #1748 grading correction that seeded it.
- Data-integrity findings surfaced during the grounding lane (cycle 810, on `#2258`):
  (1) `sutravali_rules.yoga_canonical_id` tag-matching is unreliable as a standalone sruti
  signal (verified live for `sunapha`); (2) `ga_yoga_firings.constituent_fact_ids` is
  systemically stale — 0/40 resolve (pre-#1747-scheme rows). Both shaped the matcher design
  (structural antecedent comparison, not tag joins; honest pratyaksa-heavy v1).
- W5 cross-asset mechanical checks authored AND run (PR #2384, `l2_scripts/
  l2_w5_mechanical_checks.sql`): 5 PASS / 3 honest-red, every red on a documented defect —
  X2 §N.5 11,355/210,697 constituent fact_ids unresolved (the #1747 trail); X3 159 dangling
  `bodha_triangulation.signal_ids`; X8 20 dangling `constituent_signals_array` refs. All
  three expected to clear at the held rebuilds; `[W5-PENDING]` re-run must show them green.
- LATER-tier ledger: L-03 `bg_concordance` repair handed to L0's backlog with evidence
  (charter C5 write-set boundary), not routed around.

## 3. Pillar movement (the five doctrines)

- **D-GROUNDING (P3):** movement = the tier machinery now EXISTS: D-NATIVE-09 detector order
  (sruti→yukti→pratyaksa, first-earned wins, honest downgrade), matcher rehearsed live —
  canonical chart: `yoga_dosha_firing` 29/26/8 sruti/yukti/pratyaksa of 63; `msr_signal`
  0/189/49,915 of 50,104 (0-sruti is honest: `rule_ids`/`text_chunk_ids` currently empty).
  Fabricated-citation floor held: exact-set-equality sruti (a subset-match bug was caught by
  a unit test pre-ship). `[W4-PENDING]` stored `bodha_grounding_matches` rows (behind #2258).
  Ruled sruti definition (#1726 condition 3) recorded in `L2_STATE.md` for verbatim carry.
- **D-SYNTHESIS (P4):** rollup writers complete (`bo_samvada` wave + migration 662 agreement
  line on `bo_laksana_rerank`); singular-verdict voice + stored adjudication preserved.
  `[W4-PENDING]` populated `system_convergence_count` / `cross_system_consensus_count` /
  `contradicts_signals_array` on live rows (data lands at rerank dispatch, gated on L1 freeze).
- **D-SALIENCE (P5):** the largest verified movement, and it is LIVE, not writer-only:
  `tail_watch` shipped AS DATA (#1776 MERGED — `buildTailWatch()` live in four served L2
  query modules, reading 50,104 signals + 2,918 canonical anomalies today), hard-floor
  trim-immunity in `response_budget.ts`; salience-truth writer corrections merged (#1741);
  percentile-in-class setters fixed across the D5 sibling group. `[W4-PENDING]` corrected
  salience VALUES in stored rows (behind the held `bo_laksana` rebuild).
- **D-TIME (P6):** no L2 write-set movement by design — L2's temporal terms live in the
  query-time ranker (already running); the Temporal Concordance Contract is L3/L4 write-set.
  No claim made here.
- **D-SERVICE (P8):** serving siblings partially landed with the tail lane (four query
  modules + trim-proofing #1760, umbrella density #1779); consensus chip + `resolve_grounding`
  spine extension + lens drill are `[W4-PENDING]`-adjacent (they serve data that exists only
  after the gated dispatches).

## 4. Cost actuals `[W6-PENDING — full ledger at close]`

Verified-to-date highlights (full per-wave ledger assembled at the real W6 from `L2_STATE.md`
COST LEDGER + PR timestamps): W1 five read-only subagent lanes ≈ one cycle; W3 spans cycles
3–817+ including two lane-death recoveries (~4h50m and the 00:14Z–05:05Z outage) and a
~47-cycle merge-queue stall absorbed without work loss. The `bo_samskara` re-key is the
layer's largest cost AVOIDANCE (kills the 100% Vertex re-embed on every `bo_laksana` rebuild);
the 50,104-signal re-rank remains the layer's largest pending COST (monster/solo slot at
dispatch, per the founding prompt). Forecast slice: `[W6-PENDING]`.

## 5. Backlog handed downstream

- **To L0:** L-03 `bg_concordance` repair (bigint[]/text chunk-id mismatch; per-text grouping;
  `match_confidence` formula) — with W1 evidence attached.
- **To L1:** `ga_yoga_firings.constituent_fact_ids` staleness (0/40 resolve, pre-#1747 rows) —
  degrades yukti detection for `yoga_dosha_firing` grounding until L1's own rebuild.
- **To L3+:** ruled rebuild order from #1770 stands — L2 MSR rebuild FIRST, L3 re-runs after
  as scheduled work; the 864,733-row CASCADE closure is the standing reason nothing here
  dispatches casually.
- **To the calibration loop (L5):** `bodha_grounding_matches` tier distributions, once stored,
  are a fresh calibration input class (honest-tier priors), flagged for mi_* consumption.
- **To serving:** consensus chip, `resolve_grounding` spine extension, lens drill — specced in
  the mandate, blocked on populated data.

## 6. Freeze ceremony `[W6-PENDING]`

Requires, in order: all 22 terminal (capsule or valid disposition receipt) · `bo_grounding`
disposition per the #2258 ruling · Conductor ordering ack · freeze event submitted ·
closure-safe sync verified · this report finalized (version bumped off -DRAFT, placeholders
resolved) · `L2_STATE.md` final. Until then this file is a scaffold and claims nothing about
W4/W5/W6.
