---
artifact: L1_STATE.md
canonical_id: NIRMANA_V21_L1_STATE
version: rolling
status: LIVE
campaign_id: nirmana-elevation
session: L1
layer: L1 — Gaṇita
owner: the L1 session (this file is yours alone — charter C5)
last_updated: 2026-09-05 — W1 COMPLETE (19/19); PR #1736 open (campaign critical path)
---

# L1 — Gaṇita — SESSION STATE

Rebased onto the CONDUCTOR stub (its bootstrap facts and standing rulings retained verbatim below).
Charter C9: this file is your memory — update it every loop, commit it with
every PR and at every milestone, so re-pasting your prompt into a fresh session is safe at any
moment.

**Read order on ANY start:** `SESSION_CHARTER_V21.md` → this file → `git fetch origin main` →
your `nirmana-adjudication` issues → continue.

- **Coordination issue:** #1713 (run-slot claims, freeze-ordering acks, monster scheduling)
- **Adjudication:** open a new issue labeled `nirmana-adjudication`, then keep working (C3)
- **Migration range:** 650–659 (yours alone, collision-free by construction)
- **Branch namespace:** `codex/nirmana-l1-*` · **PR title prefix:** `L1:`
- **Worktree:** `~/nirmana-s/l1`
- **Standing ruling D-CND-01 (read before your first Conform-stage check):** a `count(*) = N` is
  permitted only as a conjunct of something that can fail on corruption it cannot see — a total
  content fingerprint, or named invariants (contiguity, tiling, distinctness, cross-table
  FULL-JOIN consistency, NULL/range guards). Alone it is forbidden (C12). `expected_volume_formula`
  is REQUIRED when a count equality is the volume assertion; not required alongside a total-content
  digest. Full reasoning + the L0 evidence: `CAMPAIGN_STATE.md` → CONDUCTOR standing audit A-01.
- **Freeze predecessor:** L0 Brahmagyan must be frozen before your W6 ceremony (C2; asset work is never held)

## Position

**L1-W1 ANALYZE — COMPLETE (19/19 assets).** W2 DECIDE in progress.

**Critical-path assignment in flight:** PR **#1736** — the evidence-spine generalisation, authored
by L1 per the Conductor's ruling on #1715. It unblocks E-gate condition 2 for **88 assets across
L1–L5**, not just L1. No L1 W2 *acceptance event* may be written until it is merged and deployed
(ruling, explicit); W1/W2 *analysis and decisions* are unaffected and continue.

## E-gate (C2/C10) — measured live 2026-09-05

All five L0 ancestors of L1 are already `asset_frozen` (`bg_kp_sublord_division`, `bg_nakshatra`,
`bg_panchanga`, `bg_prashna_rules`, `bg_reference`), so L1 is gated only on its own DAG.

| tier | assets | unfrozen ancestors |
|---|---|---|
| T0 | `ga_positions` | **0 — condition 1 OPEN** |
| T1 | `ga_ayurdaya` `ga_dashas` `ga_nakshatra` `ga_panchanga` `ga_prashna` `ga_sensitive` `ga_sensitive_degree` `ga_transit_anchors` `ga_vargas` | 1 |
| T2 | `ga_strength` | 2 |
| T3 | `ga_condition` `ga_tajaka` | 3 |
| T4 | `ga_medical` `ga_vastu` | 4 |
| T5 | `ga_structural` | 7 |
| T6 | `ga_sade_sati` `ga_yoga` | 8 |
| T7 | `ga_vichara` | 9 |

Canary `ga_positions`: **cond 1 ✅ · cond 2 ❌ (#1715 → PR #1736) · cond 3 ✅.**
Manifest waves: W0=1, W1=9, W2=3, W3=3, W4=2, W5=1.

## Asset table (19 assets)

Live counts vs declared floor, canonical chart `482012f1`. Routes are W2 *proposals* from W1 —
none accepted yet (blocked on #1736).

| asset_id | live / floor | proposed route | headline W1 finding |
|---|---:|---|---|
| ga_positions | 890 / 50 | rebuild_only | layer root; canary |
| ga_vargas | 23,542 / 22,092 | **changed** | **MUST: longitudes computed for the wrong instant (F-A)** |
| ga_dashas | 483,859 / **536,471** | rebuild_only | floor decomposed to 5 named causes, sums exactly (F-A) |
| ga_nakshatra | 2,847 / 1,802 | rebuild_only | `ganita_nakshatra_get` does not serve it (F-B18) |
| ga_panchanga | 437 / 221 | **changed** | **MUST: `*_arambha_iso` stores the anga END (F-B24)** |
| ga_sensitive | 8,565 / **8,610** | rebuild_only | deficit = floor-vintage mismatch, not a defect (F-B) |
| ga_sensitive_degree | 275 / 0 | rebuild_only | derives to 335; `count_sql` omits 60 served rows (F-B) |
| ga_strength | 13,621 / 11,936 | **changed** | **MUST: ṣaḍbala selector still wrong on 2 of 3 charts (F-C)** |
| ga_structural | 98,542 / 77,821 | rebuild_only | owns argala 41,760 — unconsumed; undercounts self ~5,157 (F-C) |
| ga_condition | 2,880 / 2,880 | **changed** | **MUST: `varga_dignity_composite` NULL on 135/135 served (F-C)** |
| ga_yoga | 63 / 5 | **changed** | citations exist (233/233) but no surface joins them (F-D1) |
| ga_vichara | 8,249 / 0 | rebuild_only | real and mis-labeled: DRAFT → CURRENT (F-D) |
| ga_sade_sati | 6,287 / **11,019** | rebuild_only | reconciles to the row; stale floor from a since-fixed writer (F-D) |
| ga_transit_anchors | 45 / 45 | **changed** | AV transit gating does NOT live here — serve-time TS (F-D) |
| ga_ayurdaya | 130 / 0 | rebuild_only | `get_ayurdaya.ts` omits `fact_value_jsonb` (F-E) |
| ga_medical | 45 / 45 | **changed** | **MUST: build-fatal gate passes for a wrong reason (F-E)** |
| ga_vastu | 40 / 40 | rebuild_only | highest leverage: L0 direction remedies never joined (F-E) |
| ga_tajaka | 240 / 240 | rebuild_only | floor is a wall-clock literal; already wrong on 2/3 charts (F-E) |
| ga_prashna | 0 / 0 | **dormant disposition** | R-1: facility is live-mounted; 5 orphaned served rows (F-E) |

Cross-cutting: **0/19 carry `integrity_check_sql`**; `expected_volume_formula` NULL on 6;
`ga_vichara` is `catalog_status=DRAFT` with 8,249 live rows.

## Decisions log

- **D-L1-1** — Worktree `~/nirmana-s/l1` from `origin/main` `20323fae4`; state rebased onto the
  Conductor stub. Basis: C4/C9.
- **D-L1-2** — Found the evidence spine hardcoded to L0 (4 sites); filed **#1715** rather than
  touching a Conductor-owned lib (C5). Ruled Option A, **L1 assigned to author**. → PR #1736.
- **D-L1-3** — Three assets below floor. Per C12 ("derive, never pick") each was assigned a
  first-principles derivation before routing, not resolved as "stale floor". All three now
  derived: `ga_dashas` (5 causes, sum exact), `ga_sade_sati` (reconciles to the row),
  `ga_sensitive` (floor-vintage mismatch). **None is a build regression.**
- **D-L1-4** — C2 condition 3 verified green for L1: 19/19 registry pins match the frozen manifest
  (self-testing checker: reproduces all 128 manifest fingerprints before it will report), and
  `provenance_inventory --check` exits 0. Incidental campaign-wide finding reported to the
  Conductor: `bg_parihara_rules` is the one drifted pin (L0-owned, untouched).
- **D-L1-5** — Found the `integrity_verified` detector cannot execute chart-scoped SQL (81 assets,
  L1–L5). Filed **#1727**; **closed as duplicate of L4's #1723**, whose ruling (D-CND-03) is
  *stronger* than my proposal — chart-partitioned `NOT EXISTS` invariants, no bind placeholders.
  Correction recorded on the issue rather than left standing. **L1 owns authoring 19 real
  integrity contracts** as W3 work.
- **D-L1-6** — Recorded that fixing the detector unblocks but does not EARN the signal: with
  `integrity_check_sql` NULL the fallback passes on `count > 0`, so `ga_dashas` would assert
  integrity on `483,859 > 0` (§N.8).
- **D-L1-7** — Scope sweep for further L0-only assumptions came back clean apart from #1723
  (`accepted_rebuild_observed` is already scope-aware, `definitions.ts:2277-2278`). Also: the
  legacy `run_l1_ganita_build.py` bypasses the orchestrator and must NOT be used for W4 — all 19
  L1 writers are confirmed orchestrator-native (`@register` + `WriterBase`).
- **D-L1-8** — Found `VERIFICATION_RESCALE` scores `single` (0.60) and its own declared alias
  `single_pass` (0.85) differently, on 85.2% of the chart's facts. Filed **#1729** (D-SALIENCE,
  L1→L2 feed).
- **D-L1-9** — **Deliberately did NOT do the mandate's vocabulary normalization.** Doing it first
  would silently demote 10,316 rows 0.85 → 0.60 — a salience regression shipped as a cosmetic
  cleanup (plan §6.2 "never silently better", in reverse). **HELD on #1729.**
- **D-L1-10** — W1 complete, 19/19, via five read-only subagents on disjoint asset sets. ~139
  findings (F-A1…F-E28). Deliverables `L1_W1_ANALYSIS_BATCH_A…E.md`. Every below-floor asset got
  a derivation; every uncertainty is registered as uncertainty rather than resolved by guess.

## Held items

- **All W2 acceptance events** — held on PR #1736 merging + deploying (ruling on #1715, explicit).
  Route *decisions* are not held and are proceeding.
- **All W5 `integrity_verified`** — held on L4's #1723 Part B (detector placeholder guard) landing.
- **Status-vocabulary normalization** — held on #1729 per D-L1-9.
- No upstream C6 capability holds: L0 declared none.

## CAPABILITIES LANDED

*(none yet — PR #1736 will announce the layer-generic receipt spine here once merged, since L2–L5
all consume it.)*

## Cost ledger

| item | wall-clock | notes |
|---|---|---|
| bootstrap + grounding + 3 blocker analyses | ~35 min | E-gate, floors, pins all measured live |
| W1 ANALYZE (19 assets, 5 parallel subagents) | ~21 min wall / ~1.2M subagent tokens | fully parallel |
| PR #1736 (campaign critical path) | ~45 min | incl. generator, tests, live 6-layer acceptance |

## Heartbeat

- 2026-09-05 — W1 COMPLETE 19/19. PR #1736 open, CI running. #1715 (mine, ruled, authoring),
  #1729 (mine, open), #1727 (mine, closed as dup of #1723). W2 in progress. No slot claimed —
  nothing is dispatchable while cond 2 is shut, and I will not hold a slot idle (C5).
