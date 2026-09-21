---
artifact: KALA_EXECUTION_DESIGN
version: "1.0"
status: DRAFT
date: 2026-09-22
canonical_id: KALA_EXECUTION_DESIGN
scope: >
  PROMPT_0_ENVIRONMENT_AND_ARCHITECTURE_AUDIT.md §5 — the implementability/velocity execution
  design for the L3 Kāla asset-elevation campaign (deliverable #9 of the KĀLA READINESS AUDIT).
  This is a design document (planning/writing only): no build was dispatched, no DML was run, no
  file outside this document was written.
produced_by: L3 Kāla readiness audit (autonomous, Claude Code), read-only design subagent, cycle 6
method: >
  Built entirely on already-completed audit deliverables — KALA_STRATEGY_TRACEABILITY_MATRIX_v1_0
  (T1), KALA_PROVING_JOURNEYS_BASELINE_v1_0 (T2), KALA_ACCEPTANCE_REGIME_MAPPING_v1_0 (T3), F2.md
  (t3 inheritance quantification), T5.md (strategy-internal tensions), DOMAIN_C.md
  (orchestrator/build-path proof), DOMAIN_D.md (generation/W1 substrate), DOMAIN_H.md (hub
  invalidation), DATA_LOSS_DIAGNOSIS.md (CASCADE hazard) — plus MADHAV_L3_ASSET_ELEVATION_PLAN_v1_0
  and MADHAV_DATA_PLANE_FOUNDATION_CONTRACT_AND_GATES_v1_0 §9. No new DB queries or code reads were
  performed beyond locating the §9 workflow text and confirming the "two identical retries" phrase
  is not literally present in the corpus (see §8). Every claim below cites its source; where a
  number could not be found read-only, that is stated rather than invented, per CLAUDE.md §N.8.
conductor_verification: >
  Cycle 6 conductor independently re-confirmed the 22/22 ka_* writer count, build_runs state
  distribution, and the FK CASCADE type underpinning §3's rebuild-order requirement, all matching
  this document's cited sources exactly (see AUDIT_STATE.md cycle 6 spot-verification log).
---

# KĀLA EXECUTION DESIGN — the velocity design (§5)

## 1. Critical path and its slack

The elevation plan's own live-registry dependency tiers (`MADHAV_L3_ASSET_ELEVATION_PLAN_v1_0.md`
§3, lines 98–110):

```
T0 (11): avadhi, dasha_kala, gochara_resonance, graha_sancara, kota_chakra, moorti_nirnaya,
         muhurta_seva, sudarshana_varsha, tithi_pravesha, vedha_gochara, yojaka
T1 (3):  gochara, century, kshetra
T2 (1):  sangam
T3 (3):  kalasutra, taranga, vighnakara
T4 (1):  kala_darshana
T5 (3):  bhavishya_lekha, jivana_parva, tulana
```

"Critical path six deep. Fan-out: sangam→7, yojaka→4, kala_darshana→3, vighnakara→3,
gochara_resonance→3, dasha_kala→3." — matches the prompt's own T0(11)→T1(3)→T2(sangam)→T3(3)→
T4(kala_darshana)→T5(3) shape exactly.

**Re-derivation, using the actual depends_on sets recorded in T5 (`_work/T5.md` Tension 6, citing
F3):** `ka_sangam` depends on `{ka_yojaka, ka_dasha_kala, ka_gochara, ka_muhurta_seva, bo_laksana,
ga_dashas, ga_strength, ga_positions, ga_tajaka, bg_transit_rules}` (T5 Tension 6, F3:37 — 10
edges, not 0, resolving the F3 seed/live disagreement in favour of "live" for this purpose).
`ka_vighnakara` depends on `{ka_sangam, ka_muhurta_seva, ga_positions, bg_dignity_reference,
ka_yojaka}` (F3:38). `ka_kala_darshana` reads `kala_convergence` (from `ka_sangam`) joined to
obstructions (from `ka_vighnakara`) (T5 Tension 6 table, row 2). `ka_bhavishya_lekha` depends on
`{ka_kala_darshana, ka_vighnakara, ka_sangam, bo_laksana}` (F3:42). `ka_jivana_parva` depends on
`{ka_kala_darshana, ka_dasha_kala, ka_sangam, ka_yojaka, ga_dashas}` (F3:41). `ka_taranga`
composes `kala_convergence` (from `ka_sangam`) with `bodha_pratijna` (F3/Tension 6 row 3).

So the **true critical path for the chokepoint chain** is: T0 (`ka_yojaka`, `ka_dasha_kala`,
`ka_muhurta_seva`) → T2 (`ka_sangam`) → T3 (`ka_vighnakara`, then `ka_taranga` in parallel) → T4
(`ka_kala_darshana`) → T5 (`ka_bhavishya_lekha`, `ka_jivana_parva`). This is 5 hops from T0; the
plan's stated "six deep" is consistent if `ka_gochara` (T1) is counted as gating `ka_sangam` per
the *declared* DAG edge.

**Slack finding #1 — the T1→T2 hop is contested, not real, per T5 Tension 7.** `ka_sangam`'s code
imports `services.ka_gochara.service.KaGocharaService` (`writers/ka_sangam.py:36`), but that module
is explicitly a **different, unregistered service** retained "as a backward-compat alias" — the
registered `ka_gochara` writer's materialized table (`kala_gochara_windows_v2`) is confirmed by
STRAT itself as "**not** Sangam's current transit input" (STRAT:283, quoted in T5 Tension 7).
**Consequence for the critical path: `ka_gochara`'s own elevation does not gate `ka_sangam`'s
technical readiness at all** — the declared DAG edge is hollow. This is real, measured slack: work
on `ka_gochara` (table-identity reconciliation per Tension 1's five-way disagreement) can proceed
entirely in parallel with, or after, `ka_sangam`'s freeze, without blocking it.

**Slack finding #2 — `ka_kshetra` and the century materialiser (both T1) are not on the chokepoint
chain at all.** Neither asset appears as a depends_on target of `ka_sangam`, `ka_vighnakara`,
`ka_kala_darshana`, `ka_bhavishya_lekha`, or `ka_jivana_parva` in any depends_on set cited above.
`ka_kshetra` (14,113 LOC, 8.6M rows, held on Q4) and the century materialiser (10,921 LOC combined,
held on Q1) are **large, expensive, and independently blocking work — but neither is on the path to
unblocking the sangam→vighnakara→kala_darshana→bhavishya_lekha/jivana_parva chain.** They can run
as a fully parallel stream (Stream C, per the elevation plan's own §4) with zero critical-path
slack cost if delayed.

**What cannot be stated: elapsed-time slack.** Per the elevation plan's own §6 item 2, "No
per-asset cost exists. Nobody has carried an asset through this path under t3... every sizing here
is structural" — and F2.md's own gap list confirms `observed_at`/`recorded_at` deltas were never
pulled. **This document reports topological slack only** (which nodes are off the chokepoint
chain) and explicitly does not invent a time-based float, per §6 below and CLAUDE.md §N.8.

**A prerequisite blocker sits ahead of the whole critical path, not on it:** per T2's headline
finding, `kala_convergence` (`ka_sangam`'s own table) and `kala_activation` (`ka_kalasutra`'s) are
**0 rows for the canonical chart right now** despite both writers having run once and written real
data (335,403 / 14,868 rows) before a foreign-key CASCADE silently erased them
(`DATA_LOSS_DIAGNOSIS.md` — see §3 below). No amount of critical-path resequencing produces a
correct `Accepted N/22` until this is either re-built with rebuild-order protection, or explicitly
gated (§3).

## 2. What is genuinely serial vs. never-gated

**Genuinely serial** (confirmed mechanisms, not policy statements):

1. **Per-chart advisory lock** — `pg_try_advisory_lock(hashtext(chart_id))`, non-blocking,
   session-scoped, confirmed live on a disposable Postgres 15 instance (`DOMAIN_C.md` §1: Session
   B blocked on the same chart, Session C succeeded on a different chart, Session D succeeded once
   A's connection closed — `f`/`t`/`t` exactly as predicted). **Only one build can run against the
   canonical chart_id at a time**, regardless of how many streams or sessions exist.
2. **Fleet cap = 6 concurrent runs, across ALL charts** (`runner.py:95`, `_MAX_CONCURRENT_RUNS`,
   default 6; budget math: Cloud SQL `max_connections=50`, 6×5≤~33 — `DOMAIN_C.md` §2). Enforced
   *before* the chart lock; a run over cap exits `3` (defer) without touching any state.
3. **Merge queue** — elevation plan §4: "Sessions open PRs into an integration branch; one
   integrator merges to main." `DUAL_CAMPAIGN_EXECUTION_PLAN_v1_0.md` §6: "Merge queue only; no
   lease; run the generators; rebase-and-regenerate on conflict."
4. **The single L3 layer pin** `layers.L3.writer_inventory_sha256` — "one hash over all 22
   writers; every L3 source PR shifts it. One integrator re-pins." (elevation plan §4).
5. **Generated-artifact regeneration** — "28 of 40 recent commits touch `src/generated/`. Resolve
   by regenerating, never hand-editing." (elevation plan §4), backed by the real CI mechanism:
   `provenance_inventory.py --check` fails CI on any digest mismatch (`DOMAIN_H.md` §8).
6. **Production leases** — `DUAL_CAMPAIGN_EXECUTION_PLAN_v1_0.md` §6: "Claim a lease in §1 bound
   to the operation and the SHA policy you choose; hold ≤ the operation; release with evidence;
   never revive an expired row."

**Never gated** (confirmed ungated, can run in unlimited parallel):

1. **C2.2 analysis/route work** — `asset_analysis_accepted` + `optimization_verdict_accepted`.
   `egate.sql`'s own text: "Neither is ever gated (C2), so this is always work you can do right
   now" (quoted in elevation plan §4).
2. **All D1/D2 contract work** (field/producer contract, structure preservation) — elevation plan
   §4: "all D1/D2 analysis work is ungated and can proceed in parallel while waiting on upstream
   freezes."
3. **Disposable-DB proofs** — Domain C's own method (a throwaway local Postgres instance, started,
   used ~10 seconds, fully torn down) is a reusable pattern: any asset's lock/constraint/schema
   proof work can be done this way without touching the fleet cap or the chart lock at all.
4. **Consumer fixtures** — implied by the gate matrix's "Integrated ... may not be claimed from
   producer tests alone" (`FOUNDATION_CONTRACT_AND_GATES_v1_0.md` §8): fixture-based consumer-side
   proof is local, DB-write-free work and does not contend for the build lane.

**Sizing implication — streams to the serial lane, not DAG width.** The three elevation-plan
streams (Frontier 9, Spine 11, Kshetra+Century 2) all target builds for the *same* canonical chart.
Per finding #1 above, **real build concurrency on this one chart is 1, not 6** — the fleet cap of 6
is a cross-chart budget the campaign barely touches while it works one chart. The design
consequence: **stream count should track available analysis/contract throughput (unbounded), not
available build throughput (1 chart-lane).** A stream that finishes its D1/D2/C2.2 work early
should **queue for the single shared build lane** rather than dispatch a second concurrent build
for the canonical chart, which `DOMAIN_C.md` §1 shows will simply be deferred with exit code 3 —
wasted dispatch overhead, not real parallelism.

## 3. Rework avoidance

**Hub-first freeze order.** Elevation plan §4: "Freeze hubs before dependents. One owner per hub,
named." `DOMAIN_H.md` independently confirms and sharpens this with file:line importer evidence
across all 7 named hubs, and identifies `ka_gochara` and `ka_sangam` as the two highest-risk single
assets — each depends on 3 of the 7 hubs (`DOMAIN_H.md` §9, "Combined blast radius"). Two hub edges
cross into supposedly-sealed layers: `services/ka_dasha_kala` reaches `ph_nimitta` (L4) via
`services/ph_nimitta/dasha_consensus.py:106,163`, and `services/ka_graha_sancara` reaches the same
L4 layer via `brahmagyan/phala/muhurta.py:729` (`DOMAIN_H.md` §2, §4, §9). The elevation plan's own
rule follows directly: "Never edit `transit_search.py` or `services/ka_dasha_kala` in-stream —
both sit inside already-frozen L0/L4 digest closures. Any change is a coordinated cross-stream
invalidation with a named owner." (§4). This design adopts that rule as written and extends it: any
edit to `services/ka_graha_sancara/engine.py` needs the same named-owner cross-layer sign-off,
since it shares the identical L4 blast-radius shape.

**Contract-first for Sangam's output.** `ka_sangam` is the confirmed chokepoint (7 of 21 depend on
it — elevation plan Tier S table; T5 Tension 6: "ka_sangam is the common ancestor of five of the
eight integrators"). Its writer still carries two unremediated, unannotated defects at the exact
lines the register cites — first-domain-only selection and missing-dignity→0.5 (T5 Tension 4,
`writers/ka_sangam.py:333,348,352-353,360,362`, verified present). Given this, T3–T5 work
(`ka_vighnakara`, `ka_taranga`, `ka_kala_darshana`, `ka_bhavishya_lekha`, `ka_jivana_parva`) should
proceed against a **declared, fixed contract for `kala_convergence`'s shape and independence
semantics** (columns, domain/dignity handling, and the scope of the existing
`independent_current_count()` de-correlation detector, which T5 Tension 6 shows is currently blind
to asset provenance) — not against whatever the writer happens to emit today. This lets downstream
D1/D2 work (never-gated per §2) proceed now without needing to be re-derived once `ka_sangam`'s
writer is actually repaired and re-run.

**Never-edit-in-stream rules for cross-layer hubs.** As above: `transit_search.py`,
`services/ka_dasha_kala`, and (this design's addition) `services/ka_graha_sancara`'s L4-reaching
surface all require a named cross-layer owner before any in-stream edit.

**Generated-artifact regenerate-don't-hand-edit rule.** Elevation plan §4 states this happened
live three times already. `DOMAIN_H.md` §8 confirms the actual enforcement mechanism:
`provenance_inventory.py --check` recomputes every writer's digest from its full transitive local-
import closure (`_local_import_files`/`get_writer_source_hash`, `asset_runner.py:335-413`,
confirmed by content-level trace) and fails CI on mismatch against the checked-in
`src/generated/nirmana-writer-digests.json`. The design requirement: every hub-edit PR must run the
regeneration command as its last step before merge; a manual edit to the generated JSON is
indistinguishable from tampering to this gate and must never be attempted.

**The CASCADE/rebuild-order hazard — explicitly in scope for sequencing, though the CASCADE itself
is not.** `DATA_LOSS_DIAGNOSIS.md` proves, with a decisive join
(`kala_activation ⋈ bodha_msr_signals` on `cb73cd3d`, §4.4), that `kala_activation`,
`kala_convergence`, `kala_bhavishya`, `kala_darshana`, and `kala_obstruction` (migration
`403_kala_signal_fk_cascade.sql`) all carry `ON DELETE CASCADE` on `signal_id →
bodha_msr_signals.signal_id`. Because `bodha_msr_signals` mints fresh `signal_id` UUIDs on every L2
rebuild (per §N.3), **any L3 rebuild of `ka_sangam`/`ka_kalasutra`/etc. is silently erased the next
time L2 Bodha rebuilds MSR signals for the same chart** — exactly what already happened to the
canonical chart (100% signal turnover, `bo_laksana`/`bo_laksana_rerank` rebuilt 2026-09-08/09-11,
nearly a month after the L3 writers' 2026-08-13 run) and partially to a second chart (`cb73cd3d`).
The diagnosis states plainly: "nothing actually enforces that lockstep coupling" and no gate
currently distinguishes `state='stale' AND rows=0` from ordinary staleness (§4.1, §6).

**Design requirement (in scope, distinct from the CASCADE fix itself, which is not):** any rebuild
of `ka_sangam`, `ka_kalasutra`, or the other three CASCADE-linked assets must be **sequenced after,
and its acceptance held provisional against, the most recent `bo_laksana`/`bo_laksana_rerank`
`asset_throughput.last_built_at` for that chart** — i.e. either (a) verify no L2 MSR rebuild is
imminent/in-flight before dispatching the L3 rebuild and re-verify immediately before emitting any
acceptance event, or (b) treat every acceptance event for these five assets as provisional until a
"stale AND empty" gate (the diagnosis's own recommended remediation (c)) exists and reports clean.
Without one of these, a design that simply "rebuilds sangam once" reproduces the exact defect this
audit found, on a delay determined by L2's own rebuild cadence, not L3's.

## 4. Reuse of accepted evidence — F2's inheritance options, quantified

F2.md partitions the 22 active identities into three evidence tiers (`_work/F2.md`, "Per-asset
ancestor closure table"): **12 assets** reached an ancestor `asset_frozen` event
(`ka_dasha_kala, ka_gochara, ka_gochara_resonance, ka_graha_sancara, ka_kota_chakra,
ka_moorti_nirnaya, ka_muhurta_seva, ka_sudarshana_varsha, ka_tithi_pravesha, ka_tulana,
ka_vedha_gochara, ka_yojaka`); **7 assets** have mid-pipeline evidence only (`ka_avadhi,
ka_bhavishya_lekha, ka_jivana_parva, ka_kala_darshana, ka_kshetra, ka_sangam, ka_taranga`);
**3 assets** have zero campaign evidence ever (`ka_gochara_v, ka_kalasutra, ka_vighnakara`).

| Option | Builds required | Freezes required | Elapsed lane time |
|---|---|---|---|
| **A — re-freeze every ancestor under t3** | 12 assets: cheapest tier *if* code hasn't drifted, but ~30% of all L3 ancestor evidence is `source_kind=server_reconstructed`, not a live build receipt (`git_commit=66, server_reconstructed=32, build_run=8` — F2.md §method item 7) — a defensible re-freeze needs an actual re-run for that fraction. 7 mid-pipeline assets: full remaining pipeline (`implementation_accepted`+`integrity_verified`+`asset_frozen`) freshly earned. 3 zero-evidence assets: full pipeline from `asset_analysis_accepted` onward. | Every one of the 22 earns a fresh 5-event chain under t3 (highest event-count cost of the three options). | **COULD NOT VERIFY** — F2.md flags `observed_at`/`recorded_at` deltas as never pulled; no time figure exists. |
| **B — native ruling naming admissible ancestor evidence, no re-run** | **0 builds** for the 12 `asset_frozen` assets — pure governance action. Does **not** reduce build cost for the other 10 (7 mid-pipeline + 3 zero-evidence) at all — they have no ancestor evidence strong enough to inherit regardless of ruling generosity. | **0 new freeze events** for the 12; **1 governance document** instead. The other 10 still need Option A/C1's full chain. | Near-zero for the 12 (a ruling, not a rebuild); **unchanged/COULD NOT VERIFY** for the other 10. Carries real staleness risk: the 12 `asset_frozen` events are 11–17+ days old at t3's freeze and 11 further days stale as of this audit, and F1's own admission-scoping bug plus F3's DAG disagreements are independent evidence the codebase moved under some of these assets since freeze (F2.md §Option B). |
| **C1 — tiered (inherit the 12, run A in full for the other 10)** | 10 assets' full builds only — the schema-supported middle ground, mapping directly onto the measured 12/7/3 partition. | 10 assets' full 5-event chains; 12 assets get Option B's near-zero governance cost. | Cost = Option A's cost for 10 assets; risk = Option B's staleness risk, but scoped to the 12 where the ancestor evidence is strongest. |
| **C2 — re-verify (not rebuild) the 12** | 0 full rebuilds for the 12; 1 lightweight `integrity_verified`-equivalent check per asset instead, run fresh under t3 against the existing frozen artifact. Needs a cheap/fast verifier to exist separately from the full build path — **COULD NOT VERIFY whether one currently does** (F2.md, explicit). | 1 fresh `integrity_verified` event per asset (not a full 5-event chain). | Middle cost between A and B — directly answers the code-drift risk Option B carries, at less cost than Option A, contingent on the unverified lightweight-verifier assumption. |
| **C3 — binary scope: inherit only the 12, the other 10 earn from scratch, no selective admissibility** | Same as C1's 10-asset requirement. | Same as C1. | Removes Option B's "selective admissibility" ambiguity risk by making the inheritance boundary evidence-shaped rather than a per-asset judgment call. |

**Load-bearing caveat that applies to every option (F2.md, independently corroborated by T3):**
none of A/B/C1–C3 touch F13's `consumed → effect_traceable → served → value_evaluated` rungs.
`KALA_ACCEPTANCE_REGIME_MAPPING_v1_0.md` (T3) independently confirms **zero admissible event types
exist for `CONSUMER_INTEGRATED` or `VALUE_EVALUATED` in the current schema, for any layer** — the
gap is structural, not L3-specific. Whichever F2 option the native picks, it can only move an asset
to `DATA_ACCEPTED` at best; a second, separate receipt-design decision is required before `Accepted
N/22` can honestly move past that under the execution brief's own delivery target. This document
does not choose an option, per the F2 finding's own instruction.

## 5. Decision latency — the native ruling queue, ordered by work unblocked

1. **F2 (t3 inheritance)** — blocks *every one* of the 22 assets from carrying any admissible
   campaign evidence at all under the current frozen definition (`t3-2026-09-11-8b884eac`): "under
   t3 there are ZERO L3 asset events of any type" (T3 §1). This is the single largest velocity
   lever named in the audit charter itself (PROMPT_0 §3 F2: "Do not choose... treat it accordingly").
2. **Q4 — is `ka_kshetra`'s continuous-field model the right abstraction to preserve?** Gates
   whether ~14,113 LOC + the P0/P1/P2/P6 performance-programme spend on the single largest asset
   investment in the layer (8.6M rows, currently read by no confirmed served surface — PARK-5) is
   money well spent or should be redirected. Asked early because it is a spend/don't-spend gate on
   the layer's single biggest line item, and per §1's slack finding, resolving it late costs nothing
   to the chokepoint chain but everything to Stream C's own schedule.
3. **Q1 — full century materialisation vs. qualified compact substrate.** Unblocks ~11k LOC of
   `gochara_v3` work and resolves T5 Tension 2's closed loop (the register forbids the only branch
   STRAT would count as elevation for this exact asset).
4. **Q8 — the honest truncation policy, cross-asset.** One ruling answers six assets at once
   (`vighnakara, darshana, kalasutra, avadhi, jivana_parva, sangam` — elevation plan §5), each
   currently carrying an unremediated hard cap (top-500/750, default-eight, ten-row, unordered
   `LIMIT 1`). Highest per-ruling leverage of the eight questions.
5. **Q3 — what counts as an independent witness (sangam/sudarshana)?** Prerequisite to trusting any
   convergence-derived score downstream — T5 Tension 6 shows `ka_kala_darshana`, `ka_taranga`,
   `ka_bhavishya_lekha`, and `ka_jivana_parva` all inherit `ka_sangam`'s convergence score, and only
   `ka_sangam` itself carries a de-correlation detector, one that "is blind to asset provenance."
   Should be resolved before §3's contract-first freeze of `kala_convergence`'s shape is declared
   final.
6. **Q2 — retire or wire `ka_kota_chakra`/`ka_tithi_pravesha`/`ka_sudarshana_varsha`?** Resolves a
   portfolio-scope question for the T0 tier and the T1 matrix's own "orphan work" finding (full
   dedicated consumer surfaces with no owning U-id) — moderate leverage, does not block any other
   asset's start.
7. **Q7 — nearest vs. strongest, for tulana/muhurta_seva/kalasutra.** Unblocks the D8
   consumer-integration proof for three assets whose current receiving-operator status is itself
   unclear or contested (`ka_tulana`'s consumer confirmed NOT-FOUND by F5).
8. **Q6 — Taranga's monthly-resolution/class-specific-meaning contract.** Lower urgency: `ka_taranga`
   already has real canonical-chart data (92,412 rows) and a live consumer, so this only refines its
   own qualification — it does not gate any other asset's start.
9. **Q5 — Bhavishya's prospective-claim boundary.** Last: `ka_bhavishya_lekha` is T5 (downstream of
   `ka_sangam`/`ka_kala_darshana`/`ka_vighnakara`), currently has 0 canonical-chart rows (nothing yet
   to protect under D7), and answering this early unblocks nothing else.
10. **T4/T5-surfaced questions, lowest priority, resolve as encountered rather than queued
    up front:** Tension 1's five-way `ka_gochara` table-identity dispute (which acceptance
    instrument — cockpit `count_sql` vs migration-1018 digest — is authoritative), Tension 5's
    REG:155 split (should the annotated NULL→0.5 half and the still-unremediated top-750 half be
    tracked as two obligations, not one), and Tension 9's REG line-anchor drift (a governance-hygiene
    fix, blocking nothing).

The campaign should never idle on a decision lower in this list while a higher one sits open — per
the audit charter's own instruction (PROMPT_0 §5.5).

## 6. Measured unit cost — what the first end-to-end asset build must record

No per-asset time exists under t3: the elevation plan states this directly ("No per-asset cost
exists. Nobody has carried an asset through this path under t3... The pathfinder produces the first
real number" — §6 item 2), and F2.md's own recommended-next-measurement list confirms
`observed_at`/`recorded_at` deltas were never pulled (§"What this audit recommends measuring
next", item 1). The elevation plan names the pathfinder asset explicitly: **P0 — `ka_graha_sancara`
end-to-end → 1/22** (§7).

This design specifies exactly what that one asset's run must record, using instrumentation surfaces
already confirmed to exist (not proposed net-new schema):

- **Per-stage elapsed time.** Timestamp the emission of each campaign event for this one asset —
  `asset_analysis_accepted → optimization_verdict_accepted → implementation_accepted →
  integrity_verified → asset_frozen` — using the real `nirmana_elevation_campaign_events` schema
  (payload/timing columns confirmed to exist, T3 §1). This directly closes F2's own flagged gap.
- **CI/build minutes.** `build_runs.started_at → ended_at` (columns confirmed live,
  `DOMAIN_C.md` §3 information_schema dump) for every `build_run` touching `ka_graha_sancara`,
  plus whatever the generated-artifact regeneration step (`provenance_inventory.py`, `DOMAIN_H.md`
  §8) adds to CI minutes for this asset's PR.
- **Lane occupancy.** `asset_throughput.last_built_at` deltas, plus a count of how many times a
  dispatch attempt for this chart_id received `sys.exit(3)` (fleet-cap or chart-lock defer,
  `DOMAIN_C.md` §1–§2) before it actually acquired the lane — a real, directly observable occupancy
  metric, not an estimate.
- **Retries.** Count of `SAVEPOINT`-scoped substep retries (`_drive_substeps`, `DOMAIN_C.md` §7)
  and run-level `failed → re-dispatch` cycles from `build_runs.state`, **split into distinct-fix
  retries vs. identical-input retries** — the split this design's §8 anti-stall rule depends on
  being measurable rather than merely asserted.

**Concrete record shape:** one row per asset, appended to the durable state/event ledger the audit
charter's §6 setup already calls for, carrying: `t_analysis_accepted, t_verdict_accepted,
t_implementation_accepted, t_integrity_verified, t_frozen, total_build_run_minutes,
total_ci_minutes, lane_defer_count, substep_retry_count, distinct_retry_count`. Once
`ka_graha_sancara` produces one complete row, every later sizing statement ("this asset is like
graha_sancara but N× the LOC") becomes measured-relative rather than invented — the exact bar the
elevation plan and F2 both set and neither has yet met.

## 7. The §9 brief-consumption workflow as the operating loop

`MADHAV_DATA_PLANE_FOUNDATION_CONTRACT_AND_GATES_v1_0.md` §9 (lines 144–154), quoted in full:

1. Verify strategic brief authority, status, branch/base, accepted upstream contracts and no
   unresolved meaning/safety/adoption decision hidden in execution scope.
2. Open a new bounded goal for exactly one stage or packet; update the execution ledger. Never
   reuse FOUNDATION for L0.
3. Reconcile current repository/generated/live evidence proportionately before mutation; protect
   shared/foreign worktrees.
4. Produce a field-level demand/offer and preservation map before choosing physical changes.
5. Implement only owned scope in dependency order; preserve frozen contracts and current campaign
   gates.
6. Execute focused proof for applicable F/DP obligations and separate proof tiers/states.
7. Obtain independent review where the approved brief requires it; retain findings and corrections.
8. Return a terminal packet with commits, changed surfaces, raw checks, release evidence,
   residuals and next strategic decisions.
9. **Stop in `WAITING_FOR_STRATEGIC_BRIEF`. Activity, checks or deployment never self-authorize the
   next stage.**

Mapped onto this campaign as the operating loop: step 1 = confirm the relevant native-authored
asset brief (Kshetra/Sangam, or Gochara's `GOCHARA_FAMILY_ELEVATION_PLAN_v0_3.md`) is ratified, not
a `PROPOSAL_FOR_NATIVE_RULING`. Step 2 = one packet per asset or hub-freeze, matching
`DUAL_CAMPAIGN_EXECUTION_PLAN_v1_0.md` §5 item 4 ("One branch per packet"). Step 3 = re-run the
relevant slice of F3's four-way DAG reconciliation for the asset in scope before touching it, given
F3's own confirmed live disagreements. Step 4 = the D1/D2 contract work this design's §2 confirms is
never-gated. Step 5 = the hub-first/contract-first sequencing of §3. Step 6 = target a *named* F13
rung, not a blanket "it works" (T3's rung discipline). Step 7 = `DUAL_CAMPAIGN_EXECUTION_PLAN_v1_0.md`
§5 item 5, "independent verification is a different session... mirroring Pūrṇa's builders never
self-certify." Step 8 = the report format at `DUAL_CAMPAIGN_EXECUTION_PLAN_v1_0.md` §5 item 7
("Accepted N/22 · Δ · Phase-0 scorecard · current packet · exact blocker · evidence ids").

**Step 9 is the loop's terminal guarantee, and this design treats it as load-bearing, not
ceremonial:** a packet that completes step 8 cleanly does **not** license opening the next packet.
The next packet's own step-1 brief-authority check must be independently satisfied every time —
momentum, a green terminal packet, or a fully-worked cone is never itself a form of authorization
to proceed to the next stage. This is the same discipline §8 below states from the anti-stall side.

## 8. Anti-stall and honesty rules

**Structural blockage is a terminal state for a cone, not a wait state.**
`MADHAV_DUAL_CAMPAIGN_EXECUTION_PLAN_v1_0.md` §5 item 2 (lines 373–375), quoted exactly:
> "Structurally blocked" is a terminal state for a cone, not a wait state. If a packet's exit
> depends on an unopened gate, the packet records `BLOCKED_STRUCTURAL(<gate>)` and stops; the
> conductor picks a different cone. No adjacent-work manufacturing.

Applied concretely: a packet working `ka_bhavishya_lekha` that discovers `ka_sangam` is empty for
the canonical chart (T2's headline finding) records `BLOCKED_STRUCTURAL(ka_sangam)` and stops. It
does not improvise a substitute data source, narrow its own scope to "just the D1 contract review"
and report that as progress toward the blocked asset, or silently start on an unrelated asset
without recording the block.

**Two identical retries maximum.** This exact phrase was searched for across the nirmana briefs,
`AUTONOMY_RESILIENCE_PATTERN_v1_0.md`, and `BUILD_GUARANTOR_AUTONOMOUS_MODE_v1_0.md` and was **not
found verbatim** — flagged rather than invented, per CLAUDE.md §N.8. The closest confirmed adjacent
doctrine: `BUILD_GUARANTOR_AUTONOMOUS_MODE_v1_0.md:36`, "(no identical retry); the loop records
what it changed," and `:57`, "Bounded retries (§B). `MAX_FIX_ATTEMPTS=5` → park. No infinite
loops."; and `AUTONOMY_RESILIENCE_PATTERN_v1_0.md:44`, "Park only after 6 distinct attempts (not 5
identical retries)." These establish the same underlying principle the prompt names — retries must
be *distinct* attempts, not repetitions of the same failed action, and are bounded rather than
infinite — even though the specific "two" figure and its exact source document were not located
read-only. This design adopts the principle as stated in the prompt and makes it auditable rather
than asserted: §6's `substep_retry_count` vs. `distinct_retry_count` split exists precisely so a
future reviewer can check whether a "retry" was actually a different attempt or the same attempt
counted twice.

**No manufactured work.** Ties directly to the same DUAL_CAMPAIGN rule ("No adjacent-work
manufacturing") and to F03, quoted in the audit charter itself: "F03: counts are not value"
(PROMPT_0 §2, T1). The T1 traceability matrix's own "orphan work" finding is the concrete evidence
for why this matters in practice: `ka_kota_chakra` and `ka_moorti_nirnaya` both have full,
high-confidence, dedicated consumer surfaces built with **no U-id obligation ever named for them**
(`KALA_STRATEGY_TRACEABILITY_MATRIX_v1_0.md`, "Orphan work — Frontier," item 1). Real, working code
was produced that serves no traceable obligation. A design that rewards visible busy-ness — new
files, new tests, new consumer wiring — over obligation-satisfaction would produce more of exactly
this pattern. The rule this design enforces: before a packet starts, its work must trace to a named
row in the T1 matrix (an A-nn/DP/U-nn obligation) or a named Q-question from the elevation plan; if
it cannot, it is manufactured work, however plausible it looks in isolation.
