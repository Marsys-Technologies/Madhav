---
artifact: L1_STATE.md
canonical_id: NIRMANA_V21_L1_STATE
version: rolling
status: LIVE
campaign_id: nirmana-elevation
session: L1
layer: L1 — Gaṇita
owner: the L1 session (this file is yours alone — charter C5)
last_updated: 2026-09-05 — W3 in flight; 4 PRs open incl. the campaign critical path
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

**L1-W3 IMPLEMENT — in flight.** W1 + W2 COMPLETE. W1 complete (19/19). `L1_W2_DECIDE_v1_0.md` published:
8 `changed` / 11 `rebuild_only` / 0 `verified_reuse`, all 139 findings triaged.
W3 IMPLEMENT next; **no W2 acceptance event written** (held on #1736 per ruling).

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

- **D-L1-11** — W2 routes assigned on one question: *does the rebuild need changed writer code?*
  8 `changed`, 11 `rebuild_only`. **`verified_reuse` rejected for all 19** — it requires proven
  integrity, and 0/19 carry `integrity_check_sql`, so claiming it would be an unearned signal (§N.8).
  Five MUST findings are serving-side; their assets stay `rebuild_only` because routing them
  `changed` would assert a writer change that does not exist.
- **D-L1-12** — Independently re-verified F-A1 (`ga_vargas`) from production before broadcasting it,
  rather than relaying a subagent claim into a cross-layer alarm. Lagna Δ **0.0000°**; Sun Δ 0.2324°
  and Moon Δ 2.7169° — two bodies with 12× different daily motion, both off by the same **0.229 day
  = 5h30m**. Filed as cross-layer notice **#1747** with a sequencing question for L2–L5.
- **D-L1-13** — Found the frozen definition can never be superseded again (174 events / 11 runs block
  it; no side door). Consequence: **`depends_on` is immutable campaign-wide**, so all 11 L1 DAG
  corrections are NEVER-LATER-documented. Filed **#1744** — including the correction that my first
  read ("any registry change bricks the asset") was **wrong**: only `layer` and `depends_on` are
  pinned against the manifest, so D-CND-03's integrity-contract work is unaffected. Mitigating the
  one DAG defect with live consequences (`ga_dashas`/`ga_vargas` MVCC race) by **sequential
  single-asset dispatch** at W4 rather than by pretending the graph is accurate.
- **D-L1-14** — #1729 ruled: L2 implements, L1 supplies weights. Delivered a 13-member proposal, and
  argued the table's **shape** is wrong as well as its numbers — 5 statuses describe the *absence* of
  a value (`floored`, `not_defined_for_nodes`, `scope_cap_sentinel`, `skipped_malformed_source`,
  `external_computation_required`) and should be EXCLUDED from salience rather than weighted;
  scoring an N/A at 0.60 is a category error, not caution (§N.7 item 6).
- **D-L1-15** — **Dropped** the mandate's status-vocabulary normalization from W3 scope entirely
  (superseding the D-L1-9 hold). Once #1729 makes aliases resolve through `verification_vocab`,
  which spelling a writer emits stops mattering, so the cleanup has no purpose. Recorded as
  cosmetic-backlog, not as blocked work — the Conductor was explicit that L1 should hold nothing
  for it.

- **D-L1-16** — W3 batch 1 (**PR #1756**, migration 650): registry truth — 3 `count_sql`
  completions (categories written AND served but counted by nobody), 11 floors set to the measured
  minimum across all three built charts, 2 `target_table`, `ga_vichara` DRAFT→CURRENT, and
  `ga_prashna`'s R-1 dormancy made machine-readable. Dry-run against production inside
  BEGIN/ROLLBACK before shipping. Floors deliberately NOT set for the 6 assets whose routed fix can
  still change their count — a test asserts that, so a later edit cannot quietly fill them in.
- **D-L1-17** — **Found and fixed a defect I had just introduced, plus a pre-existing one.** L5's
  #1757 revealed the seed *executes* `expected_volume_formula`. My first draft used
  `ROWS_PER_AYANAMSHA` / `DIRECTIONS` / `BHAVA_CUSPS` — all outside the seed's 16-name
  `ALLOWED_VARS`, so it would have hard-failed `runSeed`. Rewrote as `<literal> * AYANAMSHAS`
  (inside the grammar, and evaluating to the true live count). Auditing all 128 assets against that
  grammar then found **three formulas on `main` that already break `runSeed`**: `ga_vichara` (mine,
  fixed), `bg_kp_sublord_division` (L0) and `bo_pratijna` (L2) — reported on #1757, not touched.
- **D-L1-18** — W3 batch 2 (**PR #1766**): `ga_vargas` computed every graha for an instant 5h30m
  after birth. PyJHora's own docstring states the two-JD convention; the writer passed the local-time
  JD to `sidereal_longitude`, which requires UTC. **Verified against the L1 authority before writing
  the fix**: `jd_ut - tz/24` reproduces `chart_facts` Sun 291.9626 and Moon 327.0552 EXACTLY.
  Scope checked not assumed — `ga_dashas` uses the same primitive but converts correctly, and no
  other `ga_writer` builds a JD this way. Four tests, two mutation-proven. F-A2/F-A3 deliberately
  deferred to W3 batch 3 (they need a migration) so `ga_vargas` rebuilds once, not twice.
- **D-L1-19** — #1744 ruled (D-CND-09): `depends_on` and `layer` immutable, everything else mutable
  before acceptance; sequential single-asset dispatch **granted** for the `ga_dashas`/`ga_vargas`
  race, as two separate slot claims. Posted L1's **11 DAG corrections in both-directions form** to
  #1734 for the Phase-Z register, with per-row verification status — 4 re-derived from writer source
  by me, the rest carried from W1 with `file:line`. Register note added: three L1 assets declare
  `ga_positions` and then re-derive positions, which is §N.5 inverted *within* L1 — and is exactly
  how `ga_vargas` came to hold a different D1 from the authority it declares a dependency on.
- **D-L1-20** — #1729 ruled: delivered the 13-member weight proposal, arguing the rescale table's
  **shape** is wrong as well as its numbers (5 statuses describe the absence of a value and should
  be EXCLUDED from salience, not weighted). #1750 opened to hand L2 three verified serving-side
  defects in its own write-set — the ṣaḍbala selector (still wrong on 2 of 3 charts; the 2026-07-28
  fix and its re-verification were both run on the only chart where it cannot manifest), the AV
  multiplier saturating at 1.15 for 12/12 houses because SARVA bindus (23–34) feed BHINNA bands
  (0–8), and the formula-version label. All three re-verified by me before filing.

## Held items

- **All W2 acceptance events** — held on PR #1736 merging + deploying (ruling on #1715, explicit).
  Route *decisions* are not held and are proceeding.
- **All W5 `integrity_verified`** — held on L4's #1723 Part B (detector placeholder guard) landing.
- ~~Status-vocabulary normalization~~ — **no longer held; dropped from scope** per D-L1-15.
- No upstream C6 capability holds: L0 declared none.

## CAPABILITIES LANDED

Charter C6 — announced here on `main`; consumers poll this section. **Nothing below is LANDED yet**;
each line names the PR it lands with, so a downstream session can tell "announced" from "available".

| capability | consumers | lands with | status |
|---|---|---|---|
| Layer-generic analysis-receipt spine (unblocks C2 cond 2 for all of L1–L5) | L2 L3 L4 L5 | PR **#1736** | IN REVIEW |
| `chart_divisionals` longitude correction — **~22% of varga sign assignments change on rebuild** | L2 L3 L4 | `ga_vargas` W3 | ANNOUNCED (#1747) |
| D-SALIENCE source-fact contract — exact `fact_category` names, live counts, and the vargottama multiplier-vs-increment units trap; plus the finding that **cancellation modifiers have no L1 source at all** | L2 (salience completion) | published now | **AVAILABLE** — `L1_W1_ANALYSIS_BATCH_C.md` |
| `ga_condition.varga_dignity_composite` populated (NULL on 100% today) | L2 | `ga_condition` W3 | ANNOUNCED |
| 19 L1 `integrity_check_sql` contracts (D-CND-03) | campaign verification | W3 | ANNOUNCED |

**L1 consumes no new upstream capability** — L0 declared none, and #1723's detector guard is a gate
L1 must satisfy rather than a feature it consumes.

## Cost ledger

| item | wall-clock | notes |
|---|---|---|
| bootstrap + grounding + 3 blocker analyses | ~35 min | E-gate, floors, pins all measured live |
| W2 DECIDE (19 routes, 139 findings) | ~20 min | incl. 2 further cross-layer findings |
| W3 batch 1 — registry truth (#1756) | ~35 min | incl. production dry-run + mutation-tested guards |
| W3 batch 2 — ga_vargas instant (#1766) | ~25 min | incl. live proof against the L1 authority |
| W1 ANALYZE (19 assets, 5 parallel subagents) | ~21 min wall / ~1.2M subagent tokens | fully parallel |
| PR #1736 (campaign critical path) | ~45 min | incl. generator, tests, live 6-layer acceptance |

## Heartbeat

- 2026-09-05 — **W1 + W2 COMPLETE; W3 in flight.** PR #1736 (critical path, in review) + #1740 (W1 docs) open.
  Issues: #1715 ruled→authoring, #1729 ruled→weights delivered, #1744 + #1747 filed, #1727 closed as
  dup of #1723; #1744 ruled and closed. PRs open: **#1736** (critical path, awaiting Conductor
  merge), #1740 (W1+W2 docs), #1756 (registry truth), #1766 (ga_vargas instant). **No slot
  claimed** — nothing is dispatchable while C2 cond 2 is shut, and holding a slot idle is
  forbidden (C5).
