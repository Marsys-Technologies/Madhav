---
artifact: L5_STATE.md
canonical_id: NIRMANA_V21_L5_STATE
version: rolling
status: LIVE
session: L5
campaign_id: nirmana-elevation
charter: 00_ARCHITECTURE/briefs/nirmana/sessions/SESSION_CHARTER_V21.md
worktree: ~/nirmana-s/l5
---

# L5 — Mīmāṃsā session state

**Position:** `L5-W1` (ANALYZE, in flight)

**Mandate (plan §5, L5):** parked-P7 seam-keeping. STRUCTURAL mode re-documented as deliberate;
prediction provenance retention verified; journal/adjudication-log seams confirmed intact;
insight-embedding serve path noted for the future programme; **no calibration values invented
(§N.8 absolute)**. Routes mostly `verified_reuse`/`static`; `lel_events` is the user-authored
source disposition (L5 exception in the frozen manifest: `execution_obligation:
source_acceptance`). This layer's freeze closes the build arc.

## Standing context carried forward from the Conductor's stub (do not lose on rebase)

- **Coordination issue:** #1713 · **Adjudication:** new issue labeled `nirmana-adjudication`, then
  keep working (C3) · **Migration range:** 690–699 · **Branches:** `codex/nirmana-l5-*` · **PR
  prefix:** `L5:` · **Worktree:** `~/nirmana-s/l5`
- **Freeze predecessor:** L4 Phala must be frozen before L5's W6 ceremony (C2). Asset work is never
  held for this — only the ceremony.
- **Standing ruling D-CND-01** (binding on every Conform-stage check I author): a `count(*) = N` is
  permitted **only** as a conjunct of something that can fail on corruption it cannot see — a total
  content fingerprint, or named invariants (contiguity, tiling, distinctness, cross-table FULL-JOIN
  consistency, NULL/range guards). **Alone it is forbidden** (C12). `expected_volume_formula` is
  REQUIRED when a count equality is the volume assertion; not required alongside a total-content
  digest. Full reasoning + L0 evidence: `CAMPAIGN_STATE.md` → CONDUCTOR standing audit A-01.
  *L5 conformance:* none of the 15 integrity contracts being authored uses a bare count equality;
  all are relational/partition invariants per D-CND-03's `NOT EXISTS (… GROUP BY chart_id HAVING …)`
  shape, and every volume expectation lives in `expected_volume_formula` (migration 690).

## Asset table (15, from frozen definition + live `asset_registry`)

| asset | kind | domain/scope | table | rows (2026-09-05) | anc / unfrozen | route | status |
|---|---|---|---|---|---|---|---|
| lel_events | data (no writer) | chart/per_chart | — (source) | — | 0/0 **E-GATE OPEN** | TBD-W2 | W1 |
| mi_vistara | data | **shared/global** | mimamsa_export_log | 0 | 0/0 **E-GATE OPEN** | TBD-W2 | W1 |
| mi_jivanaghatana | data | chart/per_chart | mimamsa_event_provenance | 64 | 1/0 **E-GATE OPEN** | TBD-W2 | W1 |
| mi_kula | data | **shared/global** | mimamsa_signal_families | 11 | 6/3 | TBD-W2 | W1 |
| mi_bhara | data | chart/per_chart | **kala_field_weight_versions** | 1 | 36/26 | TBD-W2 | W1 |
| mi_sankalpa | data | chart/per_chart | mimamsa_intervention_ledger | 0 | 36/26 | TBD-W2 | W1 |
| mi_bhavisya | data | chart/per_chart | mimamsa_predictions | 195 | 59/49 | TBD-W2 | W1 |
| mi_abhilekha | **service** | chart/per_chart | mimamsa_journal | 0 | 60/50 | TBD-W2 | W1 |
| mi_pramana | data | chart/per_chart | mimamsa_calibration | 57 | 61/50 | TBD-W2 | W1 |
| mi_gunanaka | data | chart/per_chart | mimamsa_multipliers | 18 | 62/51 | TBD-W2 | W1 |
| mi_pariksha | data | chart/per_chart | mimamsa_qa_eval | 174 | 62/51 | TBD-W2 | W1 |
| mi_adhilepa | data | chart/per_chart | mimamsa_load_bearing | 9 | 63/52 | TBD-W2 | W1 |
| mi_sambandha | data | chart/per_chart | mimamsa_manifestation_grammar | 47 | 63/52 | TBD-W2 | W1 |
| mi_seva | **service** | chart/per_chart | mimamsa_preferences | 0 | 64/53 | TBD-W2 | W1 |
| mi_darshana | data | chart/per_chart | mimamsa_insight_units | 150 | 66/55 | TBD-W2 | W1 |

## Decisions log

- **D-L5-01** (2026-09-05) — Bootstrap complete: worktree `~/nirmana-s/l5` at `origin/main`
  `20323fae4`; charter read from the shared checkout (C1: sessions/ not yet on main);
  `NIRMANA_HOLD` absent (standing authorization); coordination issue = **#1713**; no open
  `nirmana-adjudication` issues at open. DB read path = read-only postgres MCP.
- **D-L5-03** (2026-09-05) — Filed adjudication **#1719** (cross-layer). Chose to raise it at W1
  rather than at my own W4 because it is on every layer's critical path and the fix lives in
  Conductor-owned shared surfaces (C5). Explicitly did NOT route around it by relaxing C2.2 —
  weakening a gate to make something pass is a hard-floor violation (C3 / prompt §3.4).
- **D-L5-02** (2026-09-05) — E-gate queried live (C10 batch variant), not assumed. Three assets
  open TODAY: `lel_events`, `mi_vistara`, `mi_jivanaghatana`. The other 12 wait on L1–L4 ancestor
  freezes; the C10 query is the calendar, re-run every loop.

## Findings (pre-W1, from the live registry read — carried into W1 for confirmation)

- **F-L5-A (all 15):** `integrity_check_sql IS NULL` for every L5 asset — the layer has zero
  integrity gates. Per C12 an absent check is not a failing check; but a route to terminal needs
  *some* real detector. To be triaged in W2 (MUST vs NOW vs LATER per asset).
- **F-L5-B (all 15):** `catalog_status = 'DRAFT'` for every L5 asset.
- **F-L5-C:** `expected_volume_formula` populated on `mi_jivanaghatana` only
  (`FILE_COUNT('01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md','EVT')`); NULL on the other 14 — per C12
  a NULL derived-volume input is the defect when a volume claim is being made. Most L5 floors are
  `0` (honest, §N.4) so no volume claim is currently being made — confirm in W1.
- **F-L5-D:** `mi_bhara`'s `target_table` is **`kala_field_weight_versions`** — an L3-owned table
  written by an L5 asset. Cross-layer write-set; flag to Conductor if it collides with L3's W3.
- **F-L5-E:** `mi_kula` and `mi_vistara` are `domain='shared'`, `scope='global'` — per WP-3, chart
  and layer scopes exclude `domain='shared'` unless explicitly included. Dispatch mechanics for
  these two differ from the rest; `mi_vistara` is a nominated canary, so resolve this in W2.
- **F-L5-G (mandate item 1 — the layer's most important open question).** The L5 seal
  (`L5_SEAL_AND_SHIP_REPORT_v1_0.md`, 2026-06-27) justifies the STRUCTURAL honesty label on two
  claims that have BOTH gone stale:
  1. Its stated STRUCTURAL→EMPIRICAL precondition #1 was "L4 Phala layer sealed". **L4 sealed
     2026-06-29**, two days later (CLAUDE.md §E, `L4_PHALA_CLOSE_v1_0.md`). So the seal's framing
     now reads as *unfinished work whose blocker has cleared* — the opposite of the "deliberate"
     framing this campaign's L5 mandate requires. The honest current justification is that no real
     prediction→outcome data exists and **P7 is PARKED by native ruling**, not that L4 is unsealed.
  2. Its evidence sentence — "all 9 multipliers carry `promotion_status='prior_only'`… `gate_passed
     =false` for all 9" — is **factually false live**. `482012f1` now has 7 `prior_only` and
     **2 `promoted` with `gate_passed=true`, `held_out_validity='pass'`, `confidence_high=true`**
     (`LL1:fam_graha_natal` n=271; `LL1:fam_transit` n=14), `updated_at 2026-08-13` — i.e. a harness
     cycle ran AFTER the seal. `1c826d5a` still has 9/9 `prior_only`.
  **The determination that matters (§N.8):** are those `n_observations` prediction→**real lived
  outcome** observations (genuine empirical calibration → the seal's label is stale in the
  permissive direction, a documentation MUST), or prediction→**self-score** observations with no
  outcome ever recorded (→ two multipliers wear an empirical badge they did not earn, a correctness
  MUST and the §N.8 defect class exactly)? Either way a MUST; W1 Batch C (`mi_gunanaka`) and Batch A
  (`mi_pramana`) have both been tasked with the trace. **Nothing may be filled or corrected either
  way — determine and document only.**
- **F-L5-H:** the seal counts 12 `mi_*` assets and 50 `mimamsa_predictions` rows; the frozen
  manifest carries 14 `mi_*` + `lel_events` = 15, and predictions are now 195 across two charts.
  Drift to reconcile in the close report, not a defect on its face.
- **F-L5-F:** `mi_abhilekha` and `mi_seva` are `asset_kind='service'` with `service_health IS NULL`
  — no current probe. C12's service addendum makes a GREEN probe the "lit" condition.

## Per-chart census (2026-09-05, live — grounds W2 floor-setting per §N.4 and volume derivation per C12)

Chart A = `482012f1…` (canonical native) · Chart B = `1c826d5a…` (Abhinandan).

| table | A | B | reading |
|---|---|---|---|
| mimamsa_predictions | 139 | 56 | both charts real |
| mimamsa_qa_eval | 168 | 6 | heavily A-weighted |
| mimamsa_insight_units | 115 | 35 | both real |
| mimamsa_manifestation_grammar | 24 | 23 | symmetric |
| mimamsa_load_bearing | 4 | 5 | symmetric, small |
| **mimamsa_calibration** | 57 | **0** | A-only |
| **mimamsa_event_provenance** | 64 | **0** | A-only |

**F-L5-I — the two A-only tables are honestly A-only, not a build failure.** `mi_jivanaghatana`
derives from the **Life Event Log**, which is the *native's own* life events; chart B has no LEL, so
0 rows is the correct answer, not a gap. `mimamsa_calibration` follows downstream (no events → no
calibration). Consequence for W2: **a per-chart floor is the wrong shape for these two assets** —
setting `target_floor=64` would make chart B permanently and falsely "under-built". Floors here must
be chart-conditional or left at the honest `0` (§N.4: floors are aspirational, never fabricated).
This also means `lel_events`' `source_acceptance` disposition is intrinsically single-chart, which
is a point in favour of it being a disposition rather than a build.

## Held items

- **H-L5-01 — ALL 12 non-canary assets + the two gating events for all 15.** Adjudication issue
  **#1719** filed with the Conductor: `asset_analysis_accepted` and `optimization_verdict_accepted`
  are structurally L0-only in the deployed evidence ingress
  (`platform/src/lib/nirmana-elevation/definitions.ts:1223-1231` throws when `input.layer !== 'L0'`;
  the digest fn and receipt schema carry two further `L0` literals; the generated receipt module is
  L0-only with no generator script). Charter C2.2 requires both events before W4, so **no L1–L5
  asset can enter W4 until this lands** — this blocks all five layer sessions, not just L5.
  Recommended Option A (generalize the receipt spine, Conductor-owned per C5). Not blocking W1/W2,
  which continue.

## Cost ledger

| item | wall-clock | notes |
|---|---|---|
| bootstrap + registry/E-gate read | ~10 min | — |
| W1 fan-out (4 read-only SAs, 15 assets) | in flight | — |
| dispatch/evidence-path study + #1719 | ~20 min | found the campaign's top blocker |
| seal re-read + live multiplier check | ~10 min | found F-L5-G (STRUCTURAL staleness) |

## Heartbeat

- 2026-09-05 — F-L5-G surfaced and routed to the two owning W1 subagents (no duplication).
- 2026-09-05 — L5-W1 opened; 4 read-only analysis subagents dispatched over the 15 assets.
