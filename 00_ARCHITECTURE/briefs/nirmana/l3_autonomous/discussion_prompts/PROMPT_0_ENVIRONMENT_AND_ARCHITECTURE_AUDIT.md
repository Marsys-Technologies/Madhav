# KĀLA CAMPAIGN — STRATEGY-TO-ENVIRONMENT READINESS AUDIT  (v2.0 — supersedes v1)

You are running the **pre-flight audit and environment setup** for the L3 Kāla asset-elevation
campaign. The native considers this campaign critical and high-value: it must execute accurately,
without error, and at high implementation velocity.

**The purpose of this audit is not "is the infrastructure healthy".** It is:

> *Can the adopted strategy — product definition → data-plane architecture → L3 Kāla strategy →
> per-asset elevation — be implemented productively and efficiently in this environment, and what
> must be true, fixed, decided or built before it can?*

So you audit in two directions. **Top-down:** does every strategic obligation have an
implementation path, an owner, a proof and a place to land? **Bottom-up:** is every piece of
machinery the campaign depends on real, correct, and able to fail honestly? A healthy environment
that cannot deliver the strategy is NOT READY. So is an elegant strategy with no executable path.

**READ-ONLY except where marked REPAIR or BUILD.** You do not elevate assets, dispatch builds or
rebuild data. You produce a readiness certification and leave the environment provably ready.

## 0. Governing rules

1. **Measured, not inferred.** Every finding carries the command/query that reproduces it. Where
   something cannot be measured, say so and say what would measure it.
2. **Assume nothing you are told is still true** — including everything in §3. Re-verify.
3. **Your own verdicts obey F28 / CLAUDE.md §N.8:** every READY names the check that could have
   made it NOT READY. A readiness result that cannot fail is not a result.
4. **Where sources disagree — and they do — record every version and name which governs.** Do not
   smooth a contradiction into a summary.

---

## 1. The strategy cascade you are auditing against

Read these **in this order**; each layer inherits and narrows the one above. Do not reconstruct
their content from this prompt's shorthand — read them.

| Level | Artifact | Authority | What it fixes |
|---|---|---|---|
| **Product** | `00_ARCHITECTURE/MADHAV_PRODUCT_DEFINITION_v3_0.md` | CCD-010 | The promise: **Understand / Navigate / Account**; unit of value = an **earned distinction** (§1.3); question portfolio **P01–P24** (§2); **§3.10 Kāla: structure meeting time**; §5 investigator; §7 prediction (specific when earned, accountable when emitted); §8 life-event evidence, four pathways; §10 channel parity; §11 retained data plane (preserve first; eliminate stranded knowledge); **§12 concrete readings that define the standard**; §13 binding boundaries; **§14 proof of the product, not merely its machinery**. |
| **Data plane** | `briefs/nirmana/MADHAV_DATA_PLANE_VALUE_ARCHITECTURE_v2_0.md` | DP-SD-009 | §2 consumer requirements → data obligations; §3 six contributions, **five edge types — not an all-to-all build**; §5 the information that must survive every handoff; **§6.4 Kāla: temporalize the same structure**; **§7 cross-layer contracts DP01–DP18**; §8 intermediaries are part of the value chain (two managed doors + a raw evidence door); §10 preservation/rationalization hierarchy; §11 generation/freshness/efficient computation; **§12 proving journeys**; §13.3 what each layer plan must contain. |
| **Foundation** | `..._FOUNDATION_CONTRACT_AND_GATES_v1_0.md` + acceptance record | DP-SD-009 | Plane-wide invariants **F01–F28**; the **§8 gate matrix** with its "may not be claimed from" column; the **§9 brief-consumption workflow**. |
| **Asset obligations** | `..._ASSET_CONTRIBUTION_REGISTER_v2_0.md` | DP-SD-009 | Per-asset contribution, disposition codes and DP mapping for all `ka_*`. |
| **Brief contracts** | `..._LAYER_EXECUTION_BRIEF_CONTRACT_v1_0.md`, `..._ASSET_INTERFACE_EXECUTION_BRIEF_CONTRACT_v1_0.md` | DP-SD-009 | The required shape of a layer brief (10 sections) and of an asset/interface brief (8 sections). |
| **Layer** | `..._L3_KALA_STRATEGY_v1_0.md`, `..._L3_KALA_EXECUTION_BRIEF_v1_0.md`, `..._L3_ASTRA_REVIEW_RECORD_v1_0.md` | DP-SD-017 | L3-Q01–Q13; the ten logical data objects (§3); dependency/readiness lifecycle (§4); P0–P6 (§5); A01–A22 + H01 (§6.1); Kshetra's internal DAG (§6.2); computational vs declared edges (§6.3); waves W0–W8 (§6.4); acceptance states (§7); **U01–U11**. |
| **Amendments** | DP-SD-018 (unblock/resume), -019 (execution focus), -020 (automated cutover), **-021 (platform split: L3 → Claude Code, Pūrṇa → Codex)** | strategic ledger | Bounded authority and the execution venue. |
| **Campaign plans** | `MADHAV_DUAL_CAMPAIGN_EXECUTION_PLAN_v1_0.md` (v1.1), `l3_autonomous/MADHAV_L3_ASSET_ELEVATION_PLAN_v1_0.md` | DP-SD-021 | Partition rules, three streams, ten elevation dimensions D1–D10, native questions Q1–Q8. |
| **Asset briefs (native-authored)** | `l3_autonomous/briefs/` — **Gochara: `GOCHARA_FAMILY_ELEVATION_PLAN_v0_3.md`** (status `PROPOSAL_FOR_NATIVE_RULING`; v0.1/v0.2 retained SUPERSEDED; independent review `ASTRA_REVIEW_GOCHARA_PLAN_v0_2.md`, verdict PROCEED_WITH_AMENDMENTS; executed evidence in `evidence_gochara/` E1–E8). **Kshetra and Sangam briefs are still being authored by the native** — if present audit them, if absent record that and do not block. | native | The focused elevation decisions for the three hardest assets. A brief awaiting native ruling is a *proposal*: audit it, never treat it as ratified. |

Also: root `CLAUDE.md` (all of §N), `l3_autonomous/STATE.md` + `EVENTS.jsonl`,
`platform/scripts/nirmana/README.md`.

### The proving journeys — the campaign's north star

The product defines its standard by concrete readings, and the architecture restates them as
end-to-end stories. **L3 exists to make these work.** They are the acceptance target the whole
campaign is judged by:

- **Product §12.1 / VA §12.1 "Financial promise and relief"** — *"When does my financial promise
  activate — and when does strain end?"* Window A nearer but carrying a retention constraint;
  Window B later with more coherent support; **actual reasons and shared dependencies, not "more
  planets agree"**; stop where the manifestation bridge is unqualified.
- **Product §12.2 / VA §12.1 "Named yoga, including Nīcha-bhaṅga Rāja Yoga"** — formation and
  cancellation *before* searching time; eligible activation routes, closest contact,
  better-supported windows, opposing conditions; **a participant's nearest transit is not the
  activation of the whole configuration.**
- **Product §12.3 / VA §12.1 "Historical challenge"** — *"You predicted a promotion. It did not
  happen."* Frozen issued claim, fit/misfit/unmatched activations, no hindsight leakage.

Plus the non-forecast cases VA §12.1 lists (deep structural question, exact lookup and escalation,
method/input comparison, calendar-to-inquiry context) and **excluded medical/mortality requests
remaining excluded through every intermediary** (Product P07, P24, §13).

---

## 2. Top-down audit — can the strategy be implemented here?

### T1. Traceability matrix (the central deliverable)

For **each of the 22 active `ka_*` identities plus protected `ka_gochara_sweep`**, one row:

`asset → contribution-register disposition + DP obligations → L3 strategy row (A-nn) and its
required transformation → L3-Q questions it improves → product questions (P-nn) it serves →
proving journey(s) it participates in → U-nn consumer interface(s) → receiving operator that exists
today → current position on the F13 and F14 ladders under the CURRENT definition.`

Then report the two failure classes this exists to find:

- **Orphan obligations** — a DP/F/U/Q obligation that no asset, packet or owner currently carries.
- **Orphan work** — planned or existing work that serves no stated obligation (VA §3.2: five edge
  types, *not an all-to-all build*; F03: counts are not value).

### T2. Proving-journey walk-through

For each proving journey, walk F02's end-to-end path **against the live system as it is today**:
`question → applicable concept → qualified rule → canonical fact → structural relationship →
temporal mechanism → manifestation or explicit gap → delivered finding`. Identify the **first
failing boundary** per journey (not the last symptom), which L3 asset(s) own it, and what evidence
shows it. This tells the campaign what to fix first for product value, as opposed to what is
merely first in the DAG. Use the canonical chart for read-only observation; aggregates only.

### T3. The two acceptance regimes — state the mapping

Two vocabularies are in play and have already caused a reconciliation error:

- **Campaign events** in `nirmana_evidence.nirmana_elevation_campaign_events`
  (`asset_analysis_accepted`, `optimization_verdict_accepted`, `implementation_accepted`,
  `build_run_authorized`, `accepted_rebuild_observed`, `integrity_verified`, `asset_frozen`, …)
  scoped by `definition_revision`.
- **Delivery/evidence states** — F13 (present → qualified → consumed → effect traceable → served →
  value evaluated), F14 / gate matrix §8 (strategy agreed → producer ready → integrated → deployed
  → consumer value demonstrated → empirically evaluated), and the L3 strategy §7 target
  `LAYER_DATA_ACCEPTED + CONSUMER_INTEGRATED + DEPLOYED_ACCEPTED + VALUE_EVALUATED`.

Produce the **explicit mapping**: which campaign event is admissible evidence for which gate, and
which gates have **no** campaign event (so need another receipt). In particular: does `asset_frozen`
evidence anything beyond data/integrity acceptance? If `CONSUMER_INTEGRATED` and `VALUE_EVALUATED`
have no event type, say so — the campaign then needs a designed receipt for them before any asset
can honestly count toward `Accepted N/22`. Respect the gate matrix's "may not be claimed from".

### T4. Brief conformance

- The L3 execution brief against the **layer brief contract** (10 sections) and VA §13.3's eight
  required contents.
- Each native-authored asset brief against the **asset/interface brief contract** (8 sections:
  admission and exact authority; current-state evidence; failure or missing capability; semantic
  change and expected distinction; preservation/migration/history/rollback; focused proof matrix;
  implementation and review discipline; terminal evidence packet).
Report gaps as *questions for the native*, not as edits. The briefs are theirs.

### T5. Strategy-internal tensions to surface (do not resolve)

Already observed; verify and add any others you find:

- Strategy §6.1 assigns `ka_gochara → kala_gochara_windows_v2`; the seed assigns that table to the
  century materialiser, and retired `ka_gochara_sweep` shares `kala_gochara_windows` with active
  `ka_gochara`.
- The contribution register says of the century materialiser: *"eager century-wide work is not
  itself required user value"* — while strategy §6.1 says a hold "cannot earn elevation by
  deferral". These bear directly on native question Q1.
- VA §6.4: `ka_kshetra` should be *"a mechanism-qualified candidate substrate, not … a universal
  authority"*, and *"the six-view design is not a target constraint."* Bears on Q4.
- Register on `ka_sangam`: *"consume full configuration/domains/conditions, not first domain or
  missing-dignity 0.5"*; on `ka_kala_darshana`: *"global top-750 and NULL→0.5 are not complete
  personalized search."* Bears on Q3/Q8.
- F08: never count shared-input convergence as independent evidence — check every L3 integrator.

### T6. Boundaries and purposes

Confirm the campaign's environment enforces, not merely states: the four purposes (F15 —
event-free generation / permitted historical inquiry / protected evaluation / proposal-only future
conditioning); knowledge-time not just event-date firewalls (F16–F18); issued-claim freezing
(F17); L1 authority (F27); frozen orchestrator (F26); safety exclusions surviving every L3
consumer surface; **no L4/L5 elevation and no empirical-performance claim** (strategy §7).

---

## 3. Bottom-up audit — confirmed findings to re-verify and act on

Measured in the days before commissioning. **Re-measure each; do not inherit.**

**F1 — `egate.sql` admits superseded evidence (CRITICAL · REPAIR AUTHORIZED).**
`platform/scripts/nirmana/egate.sql` pins its asset list to the frozen definition, but its `frozen`
and `route` CTEs read the events table with **no `definition_revision` filter**, so evidence from
five superseded definitions is reported as current clearance. It showed `ka_sangam`/`ka_kshetra`/
`ka_avadhi` as `OPEN-PENDING-PIN` when under the current definition they have no route and
unfrozen ancestors. An F28/§N.8 defect in the tool that decides W4 eligibility.
→ Verify; **repair** with a regression test that fails on stale-definition admission; coordinate
per charter C5 (`platform/scripts/nirmana/README.md`). Then **sweep every sibling** —
`capsule_audit.sql`, `l1_integrity_check_dry_run.sql`, `nrec`, the dispatcher's gate reads.

**F2 — the t3 inheritance question (BLOCKING · NATIVE DECISION).**
Lineage: five superseded definitions, then `t3-2026-09-11-8b884eac` frozen. Frozen **under t3**:
L0 0/40 · L1 0/19 · L2 8/22 · L3 0/23 · L4 0/9 · L5 0/15 (counting any definition it *looks* like
40/19/22/13). Under t3 no L3 asset has any event, and essentially none can satisfy C2.1.
→ Per L3 asset: ancestor closure and how many ancestors are frozen under t3. Present options —
re-freeze upstream under t3, or an explicit evidenced inheritance ruling — with cost, risk, and
the F09/F13 implications of each. **Do not choose.** This is the largest single velocity lever in
the campaign; treat it accordingly.

**F3 — three sources disagree on the DAG.** Seed vs live `asset_registry` vs frozen manifest:
`ka_sangam` 0 vs 10 deps; `ka_kalasutra` 0 vs 3; `ka_muhurta_seva` 1 vs 0; `ka_vighnakara` 4 vs 5.
→ Authoritative **four-way** reconciliation for all 23 identities — seed · live registry · frozen
manifest · **actual code reads** — with target table and owner. Type every discrepancy
(computation / scheduling / validation / serving / unresolved dynamic). Cross-check
`pipeline/orchestrator/dag_edge_guard.py`. The native's asset briefs depend on this.

**F4 — builder privilege coverage is partial.** Migration 1070 restored the orchestrator core, but
as `data_plane_builder`: 258/431 public relations inaccessible; `mimamsa_*` 0/37, `phala_*` 0/20,
`chart_*` 4/15 writable; `kala_*` 39/41, `bodha_*` 28/36.
→ Full privilege matrix: every pipeline role × every relation any L3 writer **or its import
closure** touches. Find every gap that would fail an L3 build before it is hit. Report non-L3
gaps to their owners; do not widen.

**F5 — divergent implementations at the consumer boundary (UNVERIFIED).** Reported, not traced:
`call_ephemeris_at_t` has its own swisseph integration and never imports
`services/ka_graha_sancara/engine.py`; `call_dasha_eligibility` queries `chart_dashas` directly and
never imports `KaDashaKalaService`.
→ Trace and settle; then check **all 22**: does the registered writer/service sit on the live
consumer path? This decides whether D8 / `CONSUMER_INTEGRATED` is reachable per asset, and feeds T1.

**F6 — deployment lag.** At commissioning MCP, sidecar and the **builder image** sat at
`09d998940` while main was ahead. The builder image executes every writer.
→ Exact source SHA per surface; L3-relevant delta vs main; whether the path-gated deploy will ever
rebuild the pipeline image without `force_all`. A stale builder silently runs stale writers.

**F7 — data is not a clean slate.** `kala_activation_predicates` ~50,678 rows with 79 unmatched
same-chart MSR refs; `ka_kshetra` ~8.6M rows while a served surface hard-codes "field empty"
(PARK-5); `kala_field_snapshots` 0 rows; canonical `ganita_dashas_get` returning
`ga_dashas_replacement_in_progress`.
→ Per-asset physical census for chart `482012f1-710e-4a25-994a-93821f5871aa`: rows, build/
generation identity, oldest/newest, which definition era produced them. Aggregates only.

**F8 — open defect fixes not landed.** PR #2695 (dispatcher hardcoded stale writer-digest path;
`call_dasha_eligibility` wrong default ayanamsha) is blocked on a Pūrṇa-owned
`BEYOND_ACARYA_ACCEPTANCE_v5.json` baseline. Until it lands, `dispatch_frozen_rebuild.py` would
write a provenance receipt asserting code identity that never ran.
→ Confirm current state; the campaign must not dispatch through that script unpatched.

## 4. Bottom-up audit — domains

For each: what you checked, the exact command/query, the result, and `READY` / `NOT READY` /
`NEEDS DECISION` with the evidence that could have made it fail.

**A. Campaign evidence integrity** — definition lineage; every event type by
`definition_revision`; the `definition_superseded_mid_campaign` event; any tool besides `egate.sql`
admitting stale evidence; whether `capsule_audit.sql` §1/§2 pass and can genuinely fail.
**B. Acceptance machinery** — `nrec`; the executor/verifier split at the HTTP route
(`requiredPrincipalFor`) and DB trigger (`nirmana_elevation_guard_server_reconstructed_insert`);
`--include-email` (its absence is a silent 403); token minting for `amjis-nirmana-executor` and
`amjis-nirmana-verifier` **by the identity that will run the campaign**, not merely a project owner.
**C. Orchestrator and build path** — per-chart advisory lock, fleet cap, `build_runs` lifecycle,
`_verify_registry_still_matches_manifest`, `_verify_sidecar_code_matches_manifest`, writer
registration, substep plans. **Prove end-to-end on a disposable database or non-canonical chart.**
**D. Generation / W1 substrate** — 1035/1036 functions and their `session_user =
'data_plane_builder'` gates; real head tables (`l1_data_plane_generation_heads`,
`l2_data_plane_generation_heads`); what a first-ever generation can and cannot roll back to (F09).
**E. Release and delivery** — deploy-gate path patterns; the `deployment-outcome` earned signal;
pipeline-image rebuild triggers; migration ranges (L3 **1070–1119**, 1070 consumed); merge queue;
generated-artifact regeneration protocol and which PRs must regenerate what.
**F. Consumer surfaces** — `registry/layers/L3_kala/**`, `platform-mcp/src/tools/kala_views/**`,
`kala_temporal.ts`, `kala_timeline.ts`, `promise_spine.ts`; live vs dark vs divergent (F5);
**channel parity across Portal Paripraśna, managed MCP `prashna_ask` and raw MCP** (Product §10,
VA §8.3, F11); which U01–U11 are testable today.
**G. Cross-campaign safety** — Pūrṇa's territory and cadence; lease protocol on
`origin/campaign-coordination`; shared surfaces; the `L3-REQ`/`PA-REQ` interlock; that Pūrṇa's
live acceptance depends on L3 receipts (23 SCUs bind to `ka_*`).
**H. Hub and invalidation hazards** — `pipeline/transit_search.py` (Kshetra, Sangam, gochara
family **and frozen L0 `bg_sky_calendar`**), `services/ka_dasha_kala` (inside L4 `ph_nimitta`),
`ka_temporal`, `ka_graha_sancara`, `gochara_grammar`/`gochara_intensity`, `kala_trigger`,
`taranga_kernel`. Confirm `asset_runner.py::_local_import_files` closure behaviour and state
exactly what editing each hub invalidates. Note P3/P4 collide with this.
**I. Source inventory** — ~113 unmerged L3 branches; content-level (not ancestry-level) check of
what is genuinely not on main — an earlier "stranded work" claim was wrong because PR #2607
re-delivered the content.
**J. Session and tooling** — stream worktrees; permissions; **transcript persistence** (a session
launched from inside another inherits `CLAUDE_CODE_CHILD_SESSION` and silently becomes
non-resumable — set `CLAUDE_CODE_FORCE_SESSION_PERSISTENCE=1`); credential routes; backup/restore.

---

## 5. Implementability and velocity design (BUILD AUTHORIZED — design documents, not asset work)

The native wants **high velocity without compromising quality**. Velocity here is a design
property, not effort. Produce an evidence-based execution design covering:

1. **Critical path.** The L3-internal tiers are roughly T0(11) → T1(3) → T2(`ka_sangam`) → T3(3) →
   T4(`ka_kala_darshana`) → T5(3); Sangam has fan-out 7. Re-derive from the F3 reconciliation and
   state the true critical path and its slack.
2. **What is genuinely serial** — the per-chart build lock, the merge queue, the single L3 layer
   pin (`layers.L3.writer_inventory_sha256`), generated-artifact regeneration, production leases —
   versus **what is never gated** (C2.2 analysis/route work; all D1/D2 contract work; disposable-DB
   proofs; consumer fixtures). Size parallel streams to the serial lane's measured throughput, not
   to the DAG's width.
3. **Rework avoidance.** Hub-first freeze order; **contract-first for Sangam's output** so T3–T5
   source can proceed against a fixed contract; never-edit-in-stream rules for cross-layer hubs;
   the generated-artifact regenerate-don't-hand-edit rule.
4. **Reuse of accepted evidence** (DP-SD-019: no recurring full audits). For F2, quantify what
   each inheritance option saves or costs in builds, freezes and elapsed lane time.
5. **Decision latency.** A queue of native rulings ordered by how much work each unblocks
   (F2 first; then Q1–Q8 of the elevation plan; then anything T4/T5 surface). The campaign should
   never idle on a decision that could have been asked for earlier.
6. **Measured unit cost.** No per-asset time exists under t3. Define exactly what the first
   end-to-end asset must record (elapsed per stage, CI minutes, lane occupancy, retries) so every
   later estimate is measured rather than invented.
7. **The §9 brief-consumption workflow as the operating loop** — including its final step: stop in
   `WAITING_FOR_STRATEGIC_BRIEF`; activity never self-authorizes the next stage.
8. **Anti-stall and honesty rules** carried from the execution package: structural blockage is a
   terminal state for a cone, not a wait state; two identical retries maximum; no manufactured work.

## 6. Environment setup (REPAIR/BUILD AUTHORIZED)

1. Fix **F1** with its regression test; sweep siblings.
2. A **definition-scoped readiness query** the campaign can trust — per asset: ancestors frozen
   under the current definition, route recorded under it, physical data state, position on the
   F13/F14 ladders, gate verdict. It must be able to report NOT READY.
3. **Stream worktrees** per the dual-campaign plan §4, settings and persistence correct.
4. **Verified credential runbook** — per operation (dispatch, generation, acceptance minting,
   read-only verification): identity, secret, exposure-free loading, and a tested proof.
5. **Backup + rollback runbook, tested.**
6. **Lane protocol** — one build lane, leases, migration sub-ranges per stream, regeneration rule,
   hub-edit protocol.
7. **Per-asset packet template** conformant to the asset/interface brief contract and the ten
   elevation dimensions, pre-filled per asset from T1 so executing sessions start from the
   obligation, not from the code.
8. **Durable state/event ledger** for three streams, with the reporting contract
   (`Accepted N/22`, delta, per-stream, blockers) and the Phase-0/campaign metric separation.

## 7. Deliverables (all under `l3_autonomous/audit/`)

1. `KALA_STRATEGY_TRACEABILITY_MATRIX_v1_0.md` — T1, with orphan obligations and orphan work.
2. `KALA_PROVING_JOURNEYS_BASELINE_v1_0.md` — T2, first failing boundary per journey.
3. `KALA_ACCEPTANCE_REGIME_MAPPING_v1_0.md` — T3, events ↔ gates, and the missing receipts.
4. `KALA_BRIEF_CONFORMANCE_v1_0.md` — T4, as questions for the native.
5. `KALA_ENVIRONMENT_READINESS_AUDIT_v1_0.md` — domains A–J and findings F1–F8, with severity/owner.
6. `KALA_DAG_RECONCILIATION_v1_0.md` — F3, four-way.
7. `KALA_PRIVILEGE_MATRIX_v1_0.md` — F4.
8. `KALA_DATA_CENSUS_v1_0.md` — F7, aggregates only.
9. `KALA_EXECUTION_DESIGN_v1_0.md` — §5, the velocity design.
10. `KALA_CAMPAIGN_RUNBOOK_v1_0.md` — §6 setup.
11. **Readiness verdict — GO / GO-WITH-CONDITIONS / NO-GO** — with conditions and owners, stated
    separately for *strategy implementability* and *environment readiness*. A NO-GO is a perfectly
    good outcome if it is true.
12. **The native's decision list**, ordered by work unblocked — F2 first.

## 8. Conduct

- Read-only by default; REPAIR/BUILD items above are the only exceptions. Other defects are
  **reported, not fixed**, unless inside L3 territory and independently verified.
- Never weaken a gate, guard or test to make something pass. A guard that blocks you is working.
- No production mutation. Prove build-path claims on a disposable database or non-canonical chart.
- Never print a credential, connection string or private chart narrative.
- Migrations 1033–1069 are not yours. Do not touch `deploy.yml`, Pūrṇa ownership scripts, any
  Pūrṇa PR, or the `WATCHDOG_SECRET` incident on revision `amjis-web-02826-huf` (human-owned).
- The native's briefs and the adopted strategy are **not yours to edit**. Surface tensions as
  questions. New meaning, doctrine, product or scope decisions return to Strategy.
- Do not invent Jyotish doctrine. A missing method qualification is a real requirement for its
  authority, never a gap to fill plausibly.
- Shell: this repo runs zsh. `"refs/heads/$b:refs/heads/$b"` parses `:r` as a modifier and silently
  mangles refspecs — use `${b}`. `$(...)` does not word-split. Quote globs (`--include='*.py'`).
- Truthfulness outranks readiness. F03 applies to this audit too: its value is the distinctions it
  earns, not its page count.
