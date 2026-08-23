---
artifact: NIRMANA_ELEVATION_PLAN_v4_0.md
version: 5.0
status: PROPOSED — plan only; nothing in v4.x/v5.0 is executed. Executed to date across the
  programme: migrations 588/589 (protection removal) only, carried from v3.0.
produced_on: 2026-08-23
grounded_at: >
  HEAD 6326cda7a (2026-08-22) + the v3.0 live-production measurement pass (2026-08-23)
  + a code-grounding pass (2026-08-23) that read the actual dispatch and execution path
  end to end: platform/src/app/api/cockpit/runs/route.ts, platform/src/lib/build/plan.ts,
  platform/src/lib/build/jobInvoker.ts, pipeline/orchestrator/{runner,asset_runner,
  global_runner,staleness,locks,main}.py, pipeline/dispatcher.py, and the legacy
  /api/build/* and /api/cockpit/refresh routes. Every loophole in §1.9 carries a
  file:line citation from that pass.
authoritative_side: claude
execution_mode: >
  AUTONOMOUS (native instruction, 2026-08-23). The remaining programme — Track M through the
  R5 freeze and the closing gate — is executed by a standing agent fleet with NO routine human
  gate. The native's decision authority is delegated to the ADHIKĀRIN agent under the written
  charter at 00_ARCHITECTURE/autonomy/CHARTER.md; a short enumerated list of Reserved Powers
  is PARKED rather than decided, and a shorter list of Hard Prohibitions is refused outright
  by every agent. Architecture, roster, anti-idle protocol and resource budget: §18.
scope_ruling: >
  SINGLE CHART (native instruction, 2026-08-23). The sole subject of this programme is
  chart 482012f1 — Abhisek Mohanty's chart, called "the native chart" throughout the
  corpus and "the chart" throughout this document. No other chart is in scope, measured,
  gated on, rebuilt, or rehearsed against: not 1c826d5a (Abhinandan), not cb73cd3d
  (Kiran Shenoy — v3.0's rehearsal chart), not acdf0d66 (Arunima), not any other.
  Cross-chart parity, multi-chart rollout, and rehearsal-chart discipline are removed
  from the programme, and I8 is rewritten accordingly (§6.10). Shared-domain (chart-
  independent) assets remain fully in scope — they are the foundation the chart stands on.
role: >
  The complete elevation programme for the Nirmāṇa Build Tracker, for one chart. v5.0
  keeps everything v3.0 established — the catalogue contract, the correctness &
  completeness programme, the per-asset plans, the tier treatments — and adds the four
  pillars v3.0 did not have: (I) a watertight Scope & Operations Model that lets the
  operator work at asset, layer, chart, or shared-substrate level while the system, not
  the operator, respects the shared/chart divide; (II) a Run-to-Completion Contract that
  makes "a dispatched build ends, fully accounted for" an orchestrator guarantee rather
  than a hope; and (III) a Foundation-First Execution Programme in which asset repair
  proceeds one layer at a time — all of L0 finished and frozen before L1 opens, and so on
  to L5 — so no downstream work is ever invalidated by later upstream work; and (IV) a
  Per-Asset Implementation Efficiency discipline (§19) that treats every asset's own
  computation as improvable — profile it, understand what it is actually doing, find the
  better algorithm — under an invariant that faster must mean identical.
supersedes: >
  NIRMANA_ELEVATION_PLAN_v3_0.md (2026-08-23) — retained in place, marked SUPERSEDED.
  Everything in v3.0 is carried forward except its multi-chart provisions, which the
  scope ruling above retires. v3.0's §13 (generated per-asset plans) remains the live
  generated surface until asset_plans.py / build_asset_control_workbook.py are re-run
  with the v4.1 columns (§15); do not hand-edit it.
companion_artifacts:
  - 00_ARCHITECTURE/NIRMANA_ELEVATION_PLAN_v3_0.md — superseded doctrine base; §13 still live
  - 00_ARCHITECTURE/control/NIRMANA_ASSET_CONTROL_WORKBOOK_v3_0.xlsx — to be regenerated as v4.1
  - 00_ARCHITECTURE/control/build_asset_control_workbook.py · asset_plans.py · measure_assets.py
  - 00_ARCHITECTURE/control/snapshots/20260823_pre_protection_removal/ — verified logical snapshot
  - 00_ARCHITECTURE/autonomy/CHARTER.md — the delegated-authority instrument (§18.3–18.4)
  - 00_ARCHITECTURE/autonomy/prompts/*.md — the six agent prompts
  - 00_ARCHITECTURE/autonomy/bin/nirmana-up.sh — tmux launcher; RUNBOOK.md — operator instructions
invariants:
  - I1 — Protection REMOVED 2026-08-23 (migrations 588 + 589). Carried from v3.0.
  - I2 — Snapshot discipline replaces protection. Any destructive operation on an
    irreplaceable corpus takes a verified logical snapshot first. With a single chart in
    scope and no rehearsal chart, this invariant carries more weight than it did in v3.0
    (§6.10). STANDING — ka_gochara_sweep's 38,287 v1 rows have no registered writer and
    cannot be regenerated; the 2026-08-23 snapshot is their only recovery path.
  - I3 — The FROZEN orchestrator writer contract (@register / WriterBase / run(ctx) /
    ctx.db_conn never committed by the writer) is preserved. The orchestrator INTERNALS
    changes here (single runner, run groups, continuation) require a freeze exception, which
    is **granted in advance and in writing** by the charter (§18.3) and scoped to
    orchestrator-internal files only. The writer-facing contract does not change — and a
    change to it remains a Hard Prohibition (§18.4): an agent that believes a writer needs a
    contract change STOPS and parks, exactly as CLAUDE.md §N.2 instructs a human to.
  - I4 — No campaign or rung closes on CI-green or code review alone. Live production
    verification always — against the chart for chart-domain assets, against the singleton
    for shared-domain assets — and, under autonomous execution, performed by an agent that
    did not do the work (I16).
  - I5 — Every status, grade, PASS, and `lit` has a real detector behind it or is null
    (CLAUDE.md §N.8 — all `§N.x` references in this document are to CLAUDE.md's Appendix N,
    the durable build standards, never to a section of this plan).
  - I6 — No registry row is ever DELETEd; lifecycle transitions only.
  - I7 — Floors are aspirational, never fabricated; a missing floor is set to the achieved
    count; a below-floor asset is decided explicitly, never left to sit.
  - I8 — REVISED for single-chart scope. **Rehearse small before wide.** There is no
    rehearsal chart. No destructive or first-ever operation runs at full asset scale on its
    first execution: it takes a verified snapshot (I2), is preceded by a `verify` dry run
    (§6.6), and executes first against ONE partition — one ayanamsha, one decade slice, one
    substep key — which is verified before the operation widens to the whole asset. Full
    text and rationale in §6.10.
  - I9 — One word, one meaning. "Shared" refers ONLY to chart-independence (asset domain).
    The build scope formerly named 'global' — "everything for this chart" — is renamed
    'chart'. No API, column, UI label, or doc may use "global" for anything else.
  - I10 — One control plane. Every build — shared-domain or chart-domain — is a build_runs
    row executed by the one orchestrator runner, visible to the cockpit, counted by the
    concurrency gates. No second runner, no state-mutating read endpoints, no write path to
    retired vocabulary tables (builds / build_events-as-control / build_checkpoints /
    build_dependencies / pyramid_layers).
  - I11 — Domain isolation. A shared-domain asset is written only by a shared-domain run
    holding the shared advisory lock. A chart-domain plan never CONTAINS a shared asset — it
    depends on shared assets as readiness gates. Structural corollary — a chart-scoped
    action can never destroy shared capital, and no two runs can co-write a shared table.
  - I12 — Run terminality. Every dispatched run reaches exactly one terminal state in
    bounded time, and every asset in its plan reaches exactly one terminal per-asset
    outcome, enumerated in the run report. "Silently missing" is a contract violation.
  - I13 — REVISED. **Strict layer sequencing.** Asset repair proceeds one layer at a time
    and only upward: L0 is completed and FROZEN before any L1 asset is touched, L1 before
    L2, and so on through L5. Within a layer, assets are taken in intra-layer topological
    wave order — first those depending on nothing else in that layer. A layer is FROZEN only
    when every asset in it passes the §8.3 gate (chart-domain assets on the chart,
    shared-domain assets on the singleton). No exceptions, no partial-layer advances, no
    "while we're in there" downstream edits. An asset's `rung` follows its LAYER; its
    `domain` decides only which run builds it.
  - I14 — NEW. **Track M is data-neutral.** The machinery campaigns (§14.1) change code,
    registry metadata, and the control plane — never an asset's data as repair. One
    carve-out, stated so the invariant is not quietly broken: a mechanism may be proven
    against reality on ONE partition of ONE R0 asset (I8), recorded as a rehearsal and
    re-done properly inside R0. No asset is repaired, and no layer advanced, outside its
    rung. This is what makes I13 airtight — the machinery can be built once, up front,
    without leaking into the layered campaign.
  - I15 — NEW. **Delegated authority, bounded and written.** Every decision this programme
    needs — promote-or-retire, floor resets, deferral records, rung freezes, destructive-op
    approval, the §6.6 double-confirm — is made by the ADHIKĀRIN agent under the charter
    (§18.3), not by the agent that wants the answer and not by a human in the loop. Authority
    is bounded: what the charter does not grant, ADHIKĀRIN PARKS (§18.4) — it never infers
    consent, and parking never stalls the fleet (I17).
  - I16 — NEW. **The builder never certifies its own work.** An asset's integrity verdict, a
    rung's freeze, and every acceptance criterion in §14 are established by PARĪKṢAKA reading
    live production, adversarially, with no access to the implementer's claims beyond the
    artifact itself. A rung freezes on PARĪKṢAKA's evidence plus ADHIKĀRIN's signature —
    never on KĀRAKA's report. This is I5's earned-signal doctrine applied to the fleet: an
    autonomous campaign that self-certifies reproduces, at the process level, exactly the
    unearned-`lit` defect it exists to cure.
  - I18 — NEW. **Faster must mean identical.** An implementation optimization is admissible
    only when the rebuilt output is proven equal to the pre-optimization output — digest
    equality, or equality within a tolerance the asset declares and justifies for
    floating-point work. Speed is never traded against data, and "it looks better now" is not
    a result. An improvement that changes what an asset produces is a correctness decision,
    not a performance one, and is parked rather than merged (§19.3).
  - I17 — NEW. **No unattended stall, and no busywork.** No agent waits on a human, and no
    agent sits idle while lawful work exists. PRAHARĪ enforces both edges: it detects
    silence, stalled runs, unanswered mailbox items and dead sessions, and it fills genuine
    wait (a 30-hour heavy build) from the Standing Queue (§18.6) — which contains ONLY
    layer-independent, data-neutral work, so anti-idle can never breach I13 or I14. A parked
    Reserved-Power item sets that thread aside; it never blocks the campaign.
changelog:
  - 5.0 (2026-08-23) — **PILLAR IV: per-asset implementation efficiency (§19, the YUKTI
    discipline)**, added on the native's instruction that every asset was designed for a
    purpose and may have a better implementation of that purpose. Two real gaps prompted it:
    (a) v3.0's §7 "Build-time optimization · six levers" was **silently dropped in the v4.0
    restructure** — its levers survive inside M2/M3/§11, but every one of them is orchestration
    (avoid work), and none makes the work itself cheaper; (b) all 128 generated per-asset
    "Rebuild time" plans are template output keyed on *median* wall clock, so 40 read "built
    once, publish digest", ~40 read "Fast (median Ns): no bespoke speed work", and not one
    names a hotspot or an algorithm — and median structurally hides the worst offenders
    (`ka_kshetra`: median minutes, worst 33.8 h). New invariant I18 (faster must mean
    identical). The rung method grows from five stages to six — **optimize now precedes
    repair**, because repairing on a slow implementation and optimizing afterwards pays the
    30-hour cost twice. Rung gate gains an efficiency item; §15's regeneration spec gains
    efficiency columns and must stop classifying by median; §16 gains an Efficiency sheet;
    the charter gains G11.
  - 4.2 (2026-08-23) — AUTONOMOUS EXECUTION. The remaining programme runs as a standing agent
    fleet with no routine human gate: new §18 (roster, delegated authority, reserved powers,
    anti-idle protocol, coordination substrate, resource budget), new invariants I15
    (bounded written authority), I16 (the builder never certifies its own work), I17 (no
    unattended stall and no busywork). I3's freeze exception is pre-granted in writing and
    scoped to orchestrator internals, with writer-contract changes reclassified as a Hard
    Prohibition; I4 now requires verification by an agent that did not do the work; §8.3's
    rung gate gains a countersigned freeze record; §7.7's closing gate runs unattended.
    Executable artifacts live in `00_ARCHITECTURE/autonomy/` — charter, six agent prompts,
    state schema, guards, and the tmux launcher.
  - 4.1b (2026-08-23) — First M0 slice executed and fed back. The workbook was regenerated
    as `NIRMANA_ASSET_CONTROL_WORKBOOK_v4_1.xlsx` (10 sheets, new Rung Board, six §15 columns
    on the Asset Register), §15's `ASSET_PLANS` block regenerated single-chart in place,
    v3.0 §13 marked superseded, and D-17…D-28 added to the Defect Register — all DB access
    read-only, nothing committed. Re-measurement corrected two figures this plan had asserted:
    the shared domain is **44 assets, not 42** (`ka_graha_sancara` and `ka_muhurta_seva`, both
    DRAFT with `scope='global'`, were missed — they are L3, so chart-domain is 84, not 86);
    and the §1.2 throughput reconciliation is **one row short on each side** (`lel_events`
    chart-side, `bg_gochara_citation_resolution` shared-side), not "three missing and one
    extra" — the shadow-row hypothesis was wrong and is withdrawn. Knock-on consequences
    followed through the plan: **R3 is a second mixed-domain rung** and dispatches as a run
    group (§6.2, §8.4), the §9 tier-G-vs-shared arithmetic is restated (44 shared = 40 G + 4 S
    probes, two of them outside L0), and §11's domain-coherence guard now names four unverified
    assets rather than two — the L3 probes being the likelier genuine violation. R0's opening
    baseline, from the Rung Board: 40 assets, 77.5 % conformant, 95 % lit, **0 % integrity-
    passed**, not frozen.
  - 4.1a (2026-08-23) — Consistency pass over the 4.1 revision: §1.2's asset counts
    reconciled against the registry (both sides of that reconciliation are corrected in 4.1b
    above); tier G distinguished from the shared domain and renamed per I9; tier-H rung spread
    corrected to three rungs; Track M acceptance criteria scoped to the I14 partition
    carve-out so no machinery campaign repairs asset data; §7.7's full-chart journey
    scheduled explicitly as the post-R5 closing gate rather than left unscheduled and
    I13-violating; `chart_id` partitioning moved out of R2 (it would re-lay frozen L1
    tables) into a post-ladder infra window; the rung board moved to M1, since retiring
    `pyramid_layers` depends on it; floors and integrity SQL confirmed as rung stage-2 work
    rather than M0's, resolving a §3-vs-§8.6 contradiction; §11's domain-coherence guard
    stated honestly as one that may fail first on the two shared L5 assets; the
    `ka_gochara_sweep`, F-52 and `ga_prashna` claims corrected against §1.5's measurements.
  - 4.1 (2026-08-23) — SINGLE-CHART SCOPE RULING (482012f1, Abhisek Mohanty) applied
    consistently: cross-chart parity discipline, multi-chart rollout, the chart-3 rehearsal
    subject, and the multi-chart cockpit view are removed; §6.7 becomes a single-chart
    invalidation protocol (retaining the shared-domain fix, which is the live half);
    §7.7 becomes the Full-Chart Rebuild Journey. I8 rewritten as partition-scale rehearsal
    (§6.10). LAYER SEQUENCING HARDENED: I13 restated as strict one-layer-at-a-time asset
    repair; new I14 makes Track M data-neutral so machinery work cannot leak into layers;
    the roadmap's per-asset work (integrity checks, floors, digests) moves out of the
    machinery track into the rungs (§14.4); each rung gains an explicit five-stage internal
    method (§8.6). Track M reduced from five campaigns to four.
  - 4.0 (2026-08-23) — Code-grounded loophole register (§1.9, L-01…L-12); three pillars —
    Scope & Operations Model (§6), Run-to-Completion Contract (§7), Foundation-First
    Execution Programme (§8); invariants I9–I13; roadmap restructured into Track M plus
    rungs with a full mapping from v3.0's Phases 0–6; decommission register (§7.6).
  - 3.0 and earlier — see NIRMANA_ELEVATION_PLAN_v3_0.md changelog (carried in full).
---

# Nirmāṇa Elevation Plan v5.0

> **Scope.** One chart: `482012f1`, Abhisek Mohanty — "the chart". Plus the shared
> (chart-independent) substrate every chart stands on. Nothing else.
> **Method.** Build the machinery once; then repair assets one layer at a time, L0 → L5,
> freezing each layer before the next opens.
> **Efficiency.** Every asset's own implementation is treated as improvable (§19) — profiled,
> understood, made faster under proof that the output is unchanged.
> **Execution.** Autonomous (§18). A standing six-role agent fleet runs the campaign with no
> routine human gate; ADHIKĀRIN holds the native's delegated decision authority under a
> written charter; PARĪKṢAKA certifies what KĀRAKA builds; PRAHARĪ guarantees the fleet
> neither stalls nor invents busywork.

## §0 — Grounding

Two grounding passes stand behind this document.

**The v3.0 measurement pass** (carried): live production reads on 2026-08-23 at HEAD
`6326cda7a` — chart state, completion rates, per-asset row counts vs floors, integrity-check
presence, verification-tier mix. The findings for the chart and for the shared substrate
remain the measured baseline. Findings about other charts are retained in v3.0 as history
and are out of scope here.

**The code-grounding pass**: the actual build dispatch and execution path was read end to
end — UI trigger → `/api/cockpit/runs` (route.ts, 507 lines) → `resolveBuildPlan`
(`lib/build/plan.ts`, 423 lines) → `invokeRunJob` (`lib/build/jobInvoker.ts`) → Cloud Run Job →
`pipeline/orchestrator/main.py` → `runner.py` (952 lines) / `global_runner.py` (191 lines) →
`asset_runner.py` (932 lines), plus the staleness propagator, the advisory locks, the legacy
`pipeline/dispatcher.py`, and the legacy `/api/build/{rebuild,rebuild-all,continue}` and
`/api/cockpit/refresh` routes. §1.9's loophole register cites file and line for every claim.

The pass also confirmed what must be **preserved**: the F-01 success-allowlist and
state-divergence cross-check (`runner.py:104–134, 523–559`), the RR-fix DB reconciliation at
rollup (`runner.py:663–761`), the upstream-success gate with loud BLOCKED semantics
(`runner.py:240–279`), orphan cleanup under the chart lock (`runner.py:861–885`), M-1
planned-until-lock, the M-14 SERIALIZABLE dispatch gate, protected-asset honesty in the
planner, the `incomplete` state, and the wave-parallel executor's correctness model. Nothing
in this plan weakens them.

---

## §1 — Diagnosis

§1.1, §1.3, §1.4, §1.6, §1.7 and §1.8 are carried from v3.0 unchanged: 45.6 % of build
attempts complete; the standing failures; the `has_substeps` false negative on 14 writers;
catalogue drift (47 DRAFT rows, 34 of them served; 13 assets with no detected consumer; 14
null `layer_index`); the resume/telemetry/DAG findings (10 heavy assets, 8 with no resume,
`completed_keys` passed by no caller, telemetry polluted to 16.9-day maxima, DAG 21 levels
deep and ~3 wide); and the unrebuildable v1 gochara corpus. §1.2 and §1.5 are restated below
for single-chart scope; §1.9 and §1.10 are the code-pass additions.

### 1.2 — Live state of the chart and the substrate (2026-08-23)

| scope | lit | stale | error | dormant | incomplete | rows |
|---|---|---|---|---|---|---|
| `482012f1` — the chart | 64 | 8 | 10 | 1 | 0 | **83** |
| shared substrate (chart-independent) | 42 | 0 | 1 | 0 | 0 | **43** |

*(The `lit`/`stale`/… figures above are throughput-row states as measured on 2026-08-23. The
registry-side asset counts they are reconciled against are corrected below — v4.1a's version of
this paragraph was wrong on both sides.)*

The single shared error is `bg_ephemeris_engine`, red since 2026-06-18 — 66 days at the time
of measurement, and the foundation of the foundation.

**The counts do not reconcile, and that is itself a finding.** The registry holds 128 assets:
**84 chart-domain** (L1 19 + L2 22 + L3 21 + L4 9 + L5 13) and **44 shared-domain** — L0's 40,
plus four shared assets that live in higher layers: `ka_graha_sancara` and `ka_muhurta_seva`
(L3 service probes, both DRAFT, both `scope='global'`) and `mi_kula` and `mi_vistara` (L5).
`asset_throughput` carries 83 chart-scoped rows and 43 shared rows, so **each side is short
exactly one row**:

| side | registry | throughput | missing |
|---|---|---|---|
| chart-domain | 84 | 83 | `lel_events` |
| shared-domain | 44 | 43 | `bg_gochara_citation_resolution` |

Both absentees are assets the catalogue *already knew* were anomalous — `lel_events` is the
prefix violator due for `SOURCE` reclassification (§1.6, R5), and
`bg_gochara_citation_resolution` is the CURRENT asset with no writer and no build on any chart
(§1.6, R0). The discrepancy therefore resolves cleanly into two known defects rather than
revealing new ones, which is the good outcome: nothing is unexplained. What remains true, and
is the point of recording it, is that **an asset with no throughput row is invisible to every
state query rather than reported as unbuilt** — it does not appear as red, amber, or dormant;
it simply is not there. M0's census closes both, and the CI conformance guard asserts
registry-to-throughput completeness so the class cannot recur.

### 1.5 — Correctness and completeness, on the chart

| finding | measurement |
|---|---|
| Verification tier of the chart's L1 facts | **112,589 of 139,471 (80.7 %) are `single`** — unverified; 9,320 (6.7 %) `two_pass_verified` |
| Assets with an `integrity_check_sql` | **0 of 128** — no asset has a post-build correctness gate |
| Assets below declared floor | **9**: `ga_sade_sati` 57 % (6,287 / 11,019), `bo_laksana` 83 %, `bo_samskara` 84 %, `bg_reference` 84 %, `ga_dashas` 90 % (483,859 / 536,471), `bg_concordance`, `bg_text_index`, `ga_sensitive`, `bg_sky_calendar` |
| Assets with rows but no floor | **48** — completeness is unmeasurable for them |
| Zero rows (chart-domain on the chart; shared-domain on the singleton) | **6**: `bg_sarvatobhadra_grid` (by design), **`ga_prashna` — an L1 asset that reads `lit` with zero rows: the live specimen of the unearned-`lit` defect**, `mi_abhilekha`, `mi_sankalpa`, `mi_seva`, `mi_vistara` |
| Accretion across build generations | `chart_facts`: 15 fact_keys under two `build_id`s; `bodha_msr_signals`: three `build_id`s (49,955 / 104 / 45) — inspected and found to be legitimate output of the table's registered co-writers, not stale residue |
| §N.5 derivation-ledger resolution | 2,000 / 2,000 sampled `constituent_facts_array` ids resolve to `chart_facts.fact_id` — **sound** |
| Deterministic-first audit | Three writers touch `genai`; all three are embeddings only (`bg_texts`, `bo_samskara`, `mi_darshana`) — **compliant**; `ph_phaladesa` bans generative narration by policy |

Two of these are doctrinal drift: `ga_dashas`' floor of 536,471 is the historical figure
CLAUDE.md §C.14 deliberately stopped hardcoding (DVA Ruling 16) — it lives on in the registry
and now reads as a 10 % shortfall; and a `single`-tier majority at L1 means most downstream
narration stands on unverified numbers, which §N.7 item 5 says no narration test can
compensate for.

**Retired from the programme by the scope ruling:** v3.0's cross-chart parity findings — 29
assets empty on chart 3, 5 empty on Abhinandan — and the cross-chart parity discipline they
motivated. They remain in v3.0 as measurement history.

### 1.9 — The loophole register *(code-cited; the structural reasons the shared/chart logic is not watertight)*

Each becomes a named defect (D-17…D-28) in the control workbook.

| # | Loophole | Evidence |
|---|---|---|
| **L-01** | **The word "global" means three different things.** `build_runs.scope='global'` means "everything for this chart, L1–L5" (`plan.ts:8,138`; the L0 GATE then strips brahmagyan, `runs/route.ts:166–170`). `asset_registry.scope='global'` means "chart-independent singleton" (`runner.py:465–467`). `/api/cockpit/refresh` treats `scope='global'` as "every asset in the registry, L0 included" (`refresh/route.ts:29–33`). Three semantics, one word, one product. | runs/route.ts:56 · plan.ts:138 · refresh/route.ts:29 |
| **L-02** | **A single shared asset cannot be rebuilt at all.** `scope='asset'` on a shared asset → 403 "Global assets must be built at scope=global" (`runs/route.ts:81–93`) — but `scope='global'` excludes brahmagyan by the L0 GATE (`:168–170`), and `scope='layer'`+`brahmagyan` rebuilds all 40. The path the error message recommends is a dead end. This is the measured cause of "globals can only be rebuilt in some narrow way", and it is what makes the 66-day `bg_ephemeris_engine` red awkward to clear. Corollary: the two non-L0 shared assets (`mi_kula`, `mi_vistara`) are rejected with the misleading code `FORBIDDEN_L0`. | runs/route.ts:81–93, 166–170 |
| **L-03** | **Two runners, two contracts.** Chart runs get the full machinery (build_runs row, DAG gating, substeps, watchdog timeouts, SSE events, F-01 verdicts). `--global-build` runs `global_runner.py`: no build_runs row, **no dependency gating** (walks `ORDER BY layer, sort_order`, `:84–91`), no substep support, no per-writer timeout, no cockpit visibility, and writers without an implementation are skipped as `deferred` with only a log line (`:155–158`). The foundation substrate — the very layer this programme must finish first — is built by the *primitive* runner. | global_runner.py · main.py:72–81 |
| **L-04** | **Shared writes are unguarded.** A chart run holds only the chart advisory lock (`locks.py`) yet builds any shared assets in its plan with `chart_id=None` (`runner.py:465–467`); a concurrent `--global-build` takes the `hashtext('global')` lock that the chart run never takes — so the two can write the same shared table at the same time. Global builds also have no build_runs row, so the 409 RUN_ACTIVE gate (`runs/route.ts:95–120`) and the `_MAX_CONCURRENT_RUNS` cap (`runner.py:813–822`) cannot see them at all. | locks.py · runner.py:465, 813 · global_runner.py:76–80 |
| **L-05** | **Substrate rebuilds leave the chart falsely green.** `global_runner.py` never calls `propagate_downstream_staleness` — a shared asset rebuilt through it relights without marking a single downstream asset on the chart stale. And the propagator itself updates only `WHERE chart_id = <run's chart>` (`staleness.py:90–99`), so shared-domain downstream (`chart_id IS NULL` rows — a `bg_*` asset depending on another `bg_*` asset) is never staled by anything: `WHERE chart_id = NULL` matches nothing, ever. Both halves bite a single-chart programme directly. | global_runner.py (no propagate call) · staleness.py:84–99 · runner.py:598–604 |
| **L-06** | **A zombie control plane is still wired to buttons.** `/api/build/rebuild`, `/rebuild-all`, `/continue` insert rows into `build_events`/`builds` — vocabulary the current orchestrator never reads (it polls `build_runs.stop/pause_requested_at`, `runner.py:213–225`). `pipeline/dispatcher.py` walks the legacy `build_dependencies` table (the A1..A22 scheme the cascade routes were already migrated OFF because it "no longer matches the bg_/ga_ asset IDs" — their own header comment). `/api/build/pyramid-layers` reads a fourth status source, `pyramid_layers`. An operator can click Rebuild and produce an event nothing will ever consume. | build/rebuild/route.ts · build/continue/route.ts · dispatcher.py:27–58 · pyramid-layers/route.ts |
| **L-07** | **"Refresh" mutates state.** `/api/cockpit/refresh` INSERTs `state='dormant'` throughput rows keyed `(chart_id, asset_id)` for every asset in scope — including **chart-scoped shadow rows for shared assets**, the exact spurious rows `runner.py`'s own comment (`:834–837`) warns shadow the correct shared row in the stats query. The v3.0 §10 "fake Refresh" is worse than fake: it is corrupting. | refresh/route.ts:44–52 |
| **L-08** | **Pre-flight treats unknown as ready.** `preflight()` skips any dependency with no throughput row — "absent entries are not our concern" (`plan.ts:248–250`). A never-built upstream passes the plan-time gate and is caught only mid-run by the orchestrator's own gate, converting a plannable refusal into a mid-run BLOCKED cascade. | plan.ts:248–250 |
| **L-09** | **Asset-scope operations bypass the machinery.** `computeWaves` returns `[[candidate]]` for scope='asset' (`plan.ts:283`); `preflight` checks only direct deps, no recursion (`:239`); `action='rebuild'` expands no downstream (`:396–399`). A single-asset rebuild neither re-derives its consumers nor prices them. | plan.ts:239, 283, 396–399 |
| **L-10** | **`action='cascade'` does not mean what an operator thinks.** It plans the downstream of everything currently *stale* in scope (`plan.ts:364–376`) — not the downstream of the thing just rebuilt. Combined with L-09 there is no single operation meaning "rebuild X and everything X feeds." | plan.ts:364–376 |
| **L-11** | **A chart-scoped action can destroy shared capital.** clear-before-build on a scope that includes shared assets executes unscoped `DELETE FROM <table>` (`runs/route.ts:301–304`) inside an operation the operator initiated *for the chart*. Guarded only by `force_l0` + super_admin — a courage check, not a semantic one. Under I11 this becomes structurally impossible instead. | runs/route.ts:255–304 |
| **L-12** | **Nothing guarantees a run finishes.** One-shot dispatch (`invokeRunJob` fires a single Cloud Run execution; no continuation on execution-ceiling death); default writer timeout 600 s against measured 30 h heavy builds unless `writer_timeout_seconds` is set per asset (`runner.py:89`; set on ~2 of 128); the substep resume machinery exists but `completed_keys` is passed by **no caller** (`asset_runner.py:397`); no transient-vs-deterministic error classification, so proxy drops and `/tmp` restarts (SAMPŪRTI specimens) fail assets permanently; SIGTERM drain window is 10 s. The 45.6 % completion rate is the sum of these. | jobInvoker.ts · runner.py:89 · asset_runner.py:397 |

### 1.10 — Why a full build of the chart has never run end to end

The failure is not one bug; it is a chain, and every link is above: dispatch is one-shot
(L-12), so any infrastructure death ends the run with the plan half-terminal; heavy writers
outlive their timeout budget and are marked error (L-12); a single error blocks its whole
downstream cone loudly — correct per the gate — but nothing retries the transient root;
assets missing from the plan resolver (`has_writer` gaps, catalogue drift — §1.6) are
silently absent rather than reported absent; a substrate build can be running unseen
alongside a chart run (L-04) and leaves the chart falsely green when it finishes (L-05); and
when the operator reaches for Rebuild/Continue to recover, three of those buttons feed the
zombie control plane (L-06) while Refresh corrupts the state it claims to read (L-07). The
Run-to-Completion Contract (§7) exists to break every link in this chain, and the Full-Chart
Rebuild Journey (§7.7) is its acceptance test.

---

## §2 — Target state

Nirmāṇa becomes a **content-addressed, partition-aware, self-healing build system with a
cost-honest cockpit, standing on a contract-conformant catalogue whose every `lit` is earned
by an integrity check** (v3.0, carried) — and, from the four pillars:

**Operable at any granularity through one scope model.** The operator selects *what* — an
asset, a set, a layer, the whole chart, the shared substrate; the system derives *where and
how*, splitting shared work from chart work automatically, sequencing them, and making it
impossible for the two to collide or for one to destroy the other.

**Guaranteed to terminate with full accounting.** A dispatched run ends in a terminal state
with every planned asset explained — completed, failed-with-cause, blocked-by-named-upstream,
skipped-with-reason, or withheld — and interrupted work continues itself without the operator
re-dispatching anything.

**Elevated one layer at a time.** L0 complete, correct, integrity-checked and frozen before
L1 is touched; L1 before L2; through L5 — so no derivation is ever built twice because
something beneath it moved afterwards.

**And cheaper to build, asset by asset** (§19): each writer's own computation is profiled,
understood and improved — set-based instead of row-by-row, reusing substrate instead of
recomputing it, coarse-to-fine instead of dense-grid — under proof that the output is
identical. This is the only kind of speed that helps a build which has never yet finished once.

**And executed autonomously** (§18): the fleet that does this work decides, verifies and
records without waiting on anyone, stops only at the short list of things it is not entitled
to settle, and hands those over with the surrounding work already finished.

---

## §3 — The Asset Catalogue Contract *(carried from v3.0 §3; two field additions)*

The contract, lifecycle model (tombstone-never-delete), semantic de-duplication invariant
(one authoritative producer per table × generation × natural-key partition), required-fields
matrix, consumer map, and SOURCE classification carry forward unchanged — including the two
fields v3.0 introduced, `target_floor` and `integrity_check_sql`, which move correctness from
a tribal expectation to a registration requirement. v4.1 adds two more:

- **`domain`** — `shared | chart`, derived 1:1 from today's `asset_registry.scope` but named
  per I9 and used by the planner as the split axis (§6.3). `scope` is retained as a legacy
  column until the rename migration, then dropped from serving paths.
- **`rung`** — the layer-ladder position R0–R5 (§8.4), derived from `layer`; recorded so the
  workbook, the per-asset plans, and the cockpit's rung board sequence the campaign without
  recomputing it.

All four are registration metadata, but they divide across the two tracks along a clean line.
**M0 establishes the contract and fills what is derivable without judgment**: the schema, the
CI conformance guard, and the values of `domain` and `rung` (both derived mechanically from
existing columns). **Each rung authors what requires knowing the asset**: its `target_floor`
(measured, per I7) and its `integrity_check_sql` (its own invariant) are written in that rung's
stage 2 (§8.6), because an asset's correctness invariant cannot be authored by a census.
Neither half touches asset data (I14).

---

## §4 — Correctness & completeness programme *(carried from v3.0 §4; applied per rung)*

The six disciplines carry forward in full:

1. **The integrity gate earns `lit`** — every data asset gets an `integrity_check_sql`
   expressing its own invariant; the orchestrator runs it after the writer commits; `lit` is
   written only on pass, `incomplete` on fail. Baseline: 0 of 128.
2. **Honest floors (I7)** — 48 assets get `target_floor` = achieved count; the 9 below-floor
   assets are each decided explicitly (`ga_dashas`' 536,471 is a stale historical figure;
   `ga_sade_sati` at 57 % is an incomplete build), and the 6 zero-row assets are each
   classified as by-design (floor 0 + a `volume_explanation`) or unbuilt — `ga_prashna`,
   which reads `lit` at zero rows, is the specimen of the second kind.
3. **Verification-tier programme for L1** — 80.7 % `single` is the correctness ceiling of the
   whole instrument; add a second derivation path per fact category so rows earn
   `two_pass_verified`; `single` remains a permitted, honest tier (S7 ruling) — the goal is
   to shrink it, not relabel it.
4. **Accretion guard** — delete-then-insert scope declared per writer as
   (chart_id × natural-key partition); the integrity check asserts single-row-per-key across
   `build_id`s. Baseline: 15 duplicated fact_keys on the chart.
5. **Derivation receipts for L3–L5** — every output row of an asset with ≥4 inputs records
   the upstream digests it was built from.
6. **Narration fidelity and determinism** — §N.7 golden tests for every narrative writer; a
   build-twice-compare-digests harness.

**What changes in v4.1 is when they are applied.** v3.0 ran them as programme-wide phases
across all 128 assets at once. Under I13/I14 they are the *content of each rung's gate*:
discipline 1, 2 and 4 are enforced for a layer's assets during that layer's rung; discipline 3
belongs to R1 (it is an L1 property); discipline 5 opens at R3, where the first ≥4-input
assets live; discipline 6's goldens are written per rung for that rung's narrative writers.
The **machinery** each discipline needs is built once in Track M (§14.1) and touches no data.

v3.0's seventh, implicit discipline — cross-chart parity — is **retired** by the scope ruling.
Its replacement is single-chart completeness: measured against honest floors, on the chart.

---

## §5 — Gochara: the transition strategy *(carried from v3.0 §5; single-chart)*

- **What exists.** v1 sweep (`ka_gochara_sweep`, RETIRED, 38,287 rows, daily-grid, ~30 h/chart,
  no writer — capital, not cache). v2/W2G (`ka_gochara`, validation surface, ±3 y, 5 bodies,
  degree-contact only, 54 rows, read by nothing). v3
  (`ka_gochara_v3_century_materialize`, 8 contact primitives, 27 classes, all shapes, full
  century in 270 decade slices, delta fingerprint folding the live scoring signature after
  F-52) — **serving the chart via `kala_gochara_authority`** (943 windows).
- **The strategy.** v1 stays as the frozen benchmark generation (I2 — and note that the only
  chart still *serving* v1 is out of scope now, which makes the corpus pure capital, not a
  serving dependency). v3 is the authority and the only writer elevated further. v2 is
  honestly a validation artefact: either promote its row to DRAFT with that stated, or retire
  it with `SUPERSEDED_BY(v3)`; either way its `count_sql` stops claiming v3's rows.
- **Slices as capital.** v3's per-slice delta fingerprint is the proven pattern §6.7 and the
  receipts discipline generalise: receipts per partition, rebuild only mismatches, never burn
  on suspicion. It is also the model for I8's partition-scale rehearsal (§6.10).
- **The open decision.** F-52 changed the live scoring signature, leaving the materialized
  century stale against it; no rematerialization has been dispatched. R3 either rematerializes v3 under the determinism
  harness or records the deferral so the cockpit stops showing green.
- **Protection.** Removed (I1). If ever reinstated, key it on (table, generation), never on
  `asset_id` — the old guard was keyed to `ka_gochara` while the writer was the v3
  materializer, and blocked the authoritative writer outright (D-02).

**Retired by the scope ruling:** v3.0's "chart 3 gets an authority row and a v3 build".

---

## §6 — Pillar I · The Scope & Operations Model

The design rule throughout: **the operator chooses what; the system derives where and how.**
Flexibility at every granularity is delivered by making the shared/chart divide a property
the planner respects automatically — never a mode the operator must select correctly.

### 6.1 — Two orthogonal axes, one word each (I9)

| Axis | Values | Who sets it | Meaning |
|---|---|---|---|
| **Domain** | `shared` · `chart` | The registry, per asset (from today's `scope` column) | Where the data lives: chart-independent singleton vs belonging to the chart. Never chosen at dispatch time. |
| **Selection** | `asset` · `asset_set` · `layer` · `chart` · `substrate` · `everything` | The operator | What is being pointed at. `layer` is the campaign's primary operation (§8). |

Plus an **action** (§6.6). There is no chart axis: one chart is in scope, and `chart`
selection means that chart. The rename lands as: `build_runs.scope` value `'global'` →
`'chart'`; new selection values `'substrate'` and `'everything'`; `/api/cockpit/refresh`'s
private scope vocabulary deleted with the endpoint's write path (L-07). A compatibility
window maps the old value on read; no new write of `'global'`-as-chart is accepted after M1.

### 6.2 — The split rule (the heart of the model)

Every operation resolves through one pure function:

```
resolve(selection, action) →
    shared_subplan  — the selected assets whose domain = shared, topologically ordered
    chart_subplan   — the selected assets whose domain = chart, topologically ordered
```

and dispatches as a **run group**: the shared-domain run (chart_id = NULL) first, then the
chart run, linked by a `group_id` on `build_runs`. Rules:

1. **Shared first.** The chart run is gated on the shared run reaching a terminal state. If
   the shared run fails, the chart run downgrades per policy — chart assets whose upstream
   closure is unaffected still run; affected ones are BLOCKED loudly (existing semantics).
2. **A selection with no shared part dispatches no shared run** (and vice versa). R0's layer
   selection is pure shared domain; R1, R2 and R4's are pure chart domain. **Two rungs are
   genuinely mixed and dispatch as run groups**: R3 (21 chart-domain assets plus the shared
   probes `ka_graha_sancara` and `ka_muhurta_seva`) and R5 (13 chart-domain assets plus
   `mi_kula` and `mi_vistara`). The `everything` selection and any `asset_set` spanning both
   domains are the other run-group cases. A mixed rung is not a special case to handle — it is
   the split rule doing exactly its job, and it is why the rule exists rather than a
   layer-equals-domain shortcut.
3. **The resolution is previewed and priced before dispatch** (§6.9) — always, including what
   is excluded and why.

### 6.3 — Chart plans never contain shared assets (I11)

Today a chart plan carries shared assets and the runner re-points them with
`eff() → chart_id=None` (`runner.py:465–467`) — the root of L-04 and L-11. Under v4.1 the
planner puts shared assets **only** into shared runs. For a chart run, a shared dependency is
a **readiness gate** — it must be `lit`/`service_ok`, exactly like today's out-of-plan seeding
(`runner.py:472–484`) — never plan membership. Consequences, all structural rather than
procedural:

- `eff()` is deleted; a run's `chart_id` is the chart_id of every asset in it.
- No two runs can co-write a shared table (L-04 closed by construction, together with §6.4).
- A chart-scoped clear can never touch a shared table (L-11 closed by construction);
  clearing shared capital requires a substrate selection under §6.6's rules.
- The L0 GATE stops being a special-case filter (`runs/route.ts:168–170`) and becomes a
  visible property of the split: a `chart` selection simply *contains no shared assets*, and
  the preview says so — "substrate verified fresh · not rebuilt by this operation".

### 6.4 — One runner, one lock discipline (I10)

`global_runner.py` is retired (tombstoned per I6 practice: kept in tree one release with a
hard failure message naming its replacement, then deleted). A shared-domain build becomes an
ordinary `build_runs` row with `chart_id = NULL` executed by `runner.py` — DAG-gated,
substep-capable, timed out, heartbeated, SSE-visible, reconciled at rollup, counted by
`_MAX_CONCURRENT_RUNS`, visible to the 409 gate (whose query drops its `chart_id=$1` filter
for shared runs), and — critically for L-05 — **running the staleness propagator like any
other run**. This single change is what makes R0 (the L0 rung) executable at all: the layer
this programme must finish first is currently built by the runner that has none of the
machinery.

| Run kind | Takes | Blocks |
|---|---|---|
| Shared run | `pg_advisory_lock(hashtext('shared'))` exclusive | Other shared runs; a chart run whose upstream closure intersects the shared plan (deferred with a visible "waiting on substrate build" state, not a silent 409) |
| Chart run | `pg_try_advisory_lock(hashtext(chart_id))` (today's) | Other runs on the chart |

A chart run already running when a shared rebuild is requested finishes first; the shared run
queues behind a `shared_barrier` that waits for in-flight chart runs to drain. Deadlock-free
because neither side holds-and-waits: each queues before acquiring.

### 6.5 — Rebuilding a single shared asset becomes legal (closes L-02)

Selection `asset` on a shared asset resolves to a one-asset shared run. Requirements, in
order: super_admin; a verified snapshot (I2) when the action is destructive; partition-scale
first execution (I8, §6.10); the asset's `integrity_check_sql` runs after commit and gates
`lit`; on relight with a changed digest, the invalidation protocol (§6.7) runs. The
`FORBIDDEN_L0` rejections and their dead-end guidance are deleted; the authorization matrix
(§6.8) replaces them. `bg_ephemeris_engine`'s 66-day red, `bg_reference`'s below-floor
rebuild, and every one of R0's forty assets become independently executable — which is
exactly what a layer-at-a-time campaign on the substrate requires.

### 6.6 — Operation semantics, defined once

For any selection S (already split by domain):

| Action | Meaning (per subplan) | Downstream obligation |
|---|---|---|
| `verify` | Run integrity checks + probes over S; write verdicts, never data. The cheap first answer to "is this green real?" and the mandatory dry run before any clear (I8). | None. |
| `build` | Fill gaps: assets in S that are dormant/error/incomplete/absent. Skip lit. | None. |
| `update` | S's stale + dormant assets, plus downstream-of-stale within S. | In-scope only (today's semantics, kept). |
| `rebuild` | Every asset in S, unconditionally. | Mark the full downstream closure stale — **always**, including shared-domain downstream (§6.7). Preview shows the closure and its price. |
| `rebuild+cascade` | S ∪ transitive downstream closure of S, split by domain, sequenced shared→chart, waves within each. **The operation that does not exist today (L-09/L-10).** In the ladder it is rarely needed — a frozen rung below means the closure is usually empty. | Self-contained: the closure is in the plan. |
| `clear+rebuild` | Snapshot (I2) → `verify` dry run → clear S within its domain scoping → rebuild, partition-first (I8). Chart-domain clears are chart-scoped by construction; shared clears require a substrate selection plus double-confirm. | As `rebuild`. |

`action='cascade'` as currently implemented (downstream-of-stale, L-10) is renamed
`update --downstream` internally and folded into `update`; the word "cascade" is reserved for
`rebuild+cascade`.

### 6.7 — Invalidation protocol when the substrate moves (closes L-05)

When a shared asset relights:

1. **Digest compare** (once M3's content addressing lands; until then a `substrate_version`
   bump reads as always-changed): identical output digest → no-op, nothing downstream is
   staled. This is what makes substrate rebuilds safe to run routinely, and it is the
   mechanism that protects a frozen rung from a later cosmetic rebuild beneath it.
2. **Changed** → one staleness sweep marks the transitive downstream closure
   `stale:upstream-content` in **both** directions the current code misses: the chart's
   downstream (works today only when the shared asset was built inside a chart run — after
   §6.4 every shared run propagates), and **shared-domain downstream** via a
   `chart_id IS NULL` branch (the WHERE clause that today can never match, L-05). Events are
   emitted per affected asset so the cockpit shows the amber immediately.
3. **Priced, not auto-executed.** The sweep marks; it does not dispatch. The cockpit shows
   the fan-out with re-derivation cost (gochara's per-slice delta fingerprint is the model —
   receipts per partition, rebuild only mismatches) and the operator dispatches `update`.

The sweep is written to iterate a chart set of one rather than hardcoding a single chart_id —
one line of forward-compatibility, no scope creep, so that if the programme's scope ever
widens again it is configuration rather than a redesign.

### 6.8 — Authorization, by domain not by layer

| Capability | admin | super_admin |
|---|---|---|
| Chart-domain build/update/rebuild/verify, any selection | ✔ | ✔ |
| Chart-domain clear+rebuild | ✔ (chart-scoped by construction) | ✔ |
| Shared-domain `verify` | ✔ (read-only) | ✔ |
| Shared-domain build/update/rebuild | ✖ — honest "requires super_admin" | ✔ |
| Shared clear, L0 clear | ✖ | ✔ + double-confirm + verified snapshot |
| `everything` selection | ✖ | ✔ |

Misleading codes (`FORBIDDEN_L0` on an L5 shared asset) are replaced by domain-accurate ones
(`SHARED_DOMAIN_SUPERADMIN`).

### 6.9 — The Operations Console (UX of the model)

One surface replaces the scattered buttons: a selection tree (substrate / chart → layer →
asset, with asset-set multi-select), an action picker limited to the legal actions for that
selection, and a **resolution preview** that always shows, before dispatch: the run group
(which runs, which order), the plan waves, the price, the downstream closure, what is
*excluded* and why (protected, withheld, already lit, wrong domain for this role, wrong rung
under I13), and the shared-readiness gates that will be checked. Refresh becomes a pure read
(re-poll + cache-bust header; the dormant-INSERT of L-07 deleted). Every legacy button either
re-points here or 410s (§7.6).

**The rung guard in the UI.** Because I13 forbids working a layer before the one beneath is
frozen, the Console marks out-of-rung selections plainly — the action is not silently
disabled, it is refused with the reason ("L2 opens when L1 is frozen; L1 is at 14/19
integrity-passed") and a link to the rung board. Machinery-track and `verify` operations are
never rung-restricted.

### 6.10 — I8 rewritten: rehearse small before wide

v3.0 kept a whole separate chart (cb73cd3d) as a crash-test dummy so that a destructive or
first-ever operation never ran first against a canonical chart. The scope ruling removes that
chart. The safety it provided does not disappear; it is carried by three substitutes, applied
to every destructive or first-run operation on the chart or the substrate:

1. **Verified snapshot first (I2).** Not "a backup exists" — a snapshot whose restore has been
   verified, taken before the operation, referenced by the run.
2. **`verify` dry run (§6.6).** Integrity checks and probes over the target set, written as
   verdicts, before anything is cleared or overwritten. A `verify` that fails is a refusal to
   proceed, not a warning.
3. **Partition-scale first execution.** The operation runs first against exactly one
   partition — one ayanamsha of the fourteen L1/L2 ayanamsha-partitioned writers, one
   `{system}:{aya}` slice of `ga_dashas`, one `{event_class}::{decade}` slice of gochara v3,
   one `stage{n}:{event_class}:{slice}` of `ka_kshetra` — which is verified (row counts,
   integrity check, spot-checked values) before the operation widens to the whole asset.

The partition machinery for this already exists and is measured (v3.0 §6): every heavy writer
declares its partitions, and gochara v3's per-slice delta fingerprint proves the pattern. The
rehearsal therefore costs minutes, not the 30 h a whole-asset mistake costs — and unlike a
rehearsal chart, it exercises *the real data*, which is a stronger test, not a weaker one.

If a disposable rehearsal chart is ever wanted back, it is an additive configuration change
(a chart set of two, with one marked non-serving), not a redesign of anything here.

---

## §7 — Pillar II · The Run-to-Completion Contract

### 7.1 — The contract

A dispatched run group ends — in bounded time — in exactly one terminal state, with five
guarantees:

1. **Terminality** (I12): `completed | failed | stopped`; pause is non-terminal and
   watchdogged; no run stays `planned`/`running` beyond its watchdog horizon.
2. **Accounting**: every asset in the plan reaches exactly one terminal per-asset outcome —
   `complete · failed:<class> · blocked:<upstream> · timeout:<budget> · skipped:<reason> ·
   withheld:<reason>` — and the run report enumerates all of them. An asset missing from the
   report is a contract violation the watchdog raises, not a silent gap.
3. **Continuation**: an interrupted run (execution ceiling, SIGTERM, crash, proxy death)
   resumes itself without operator action and without redoing committed work.
4. **Bounded retry**: transient failures retry automatically within policy; deterministic
   failures fail fast, once, loudly.
5. **Honest report**: the terminal state tells a returning operator what finished, what
   failed and why, which single root fault explains which blocked cone, and the one next
   action that unblocks the most.

### 7.2 — Continuation as an orchestrator guarantee (the core of L-12)

- **Run-level.** The orchestrator knows its execution deadline (Cloud Run task timeout via
  env). At `deadline − drain_margin` it stops dispatching new assets, drains in-flight
  substeps, marks the run `continuing`, and re-invokes the job with the same `run_id`
  (multi-dispatch continuation — v3.0 §11 item 5, now normative). On start-up with a
  `continuing` run, completed assets are seeded from `build_run_assets` terminal states —
  the machinery `_schedule_parallel` already has for out-of-plan deps — so nothing re-runs.
  A generation counter on the run bounds continuations (default 10) so a poisoned run cannot
  loop forever.
- **Substep-level.** The shared `ResumableWriter` (v3.0 §6 tier H) is the vehicle:
  `completed_keys` — today passed by no caller (`asset_runner.py:397`) — is wired from the
  substep register for every `has_substeps` writer, so a continued run re-enters a heavy
  asset at its first unfinished partition. §N.3 idempotency makes re-entry safe.
- **Crash-level.** Today's orphan cleanup (error-marking `building` rows under the chart
  lock) is kept, then improved: an orphaned run met by a fresh dispatch is *continued*, not
  merely error-marked. The reaper's job shifts from "declare it dead" to "declare it dead,
  then relaunch it once."

### 7.3 — Error taxonomy and bounded retry

Every asset failure is classified at the point of capture (exception type + SQLSTATE + infra
signal): `transient-infra` (Cloud SQL proxy drop after ~8 min of heavy writes, `/tmp` restart
loops — the SAMPŪRTI specimens), `transient-db` (serialization failure, connection reset, lock
timeout), `timeout` (watchdog budget), `deterministic` (writer bug, data-contract violation,
integrity-check failure), `blocked-upstream`. Policy: `transient-*` retries in-run with
exponential backoff, default 2 retries; `timeout` retries only if the budget was the global
default rather than a per-asset one (a per-asset budget exceeded is a real signal, not noise);
`deterministic` and integrity failures never retry. The class is written to
`build_run_assets` and the run report, so the 45.6 % is decomposable from here on.

### 7.4 — Timeout honesty

`writer_timeout_seconds` becomes a registration requirement for tier H and M assets (the §3 required-fields
matrix, v3.0 §3.4), derived from cleaned telemetry as p99 × safety factor — not guessed. The 600 s global
default remains only as the floor for unregistered light writers. The watchdog heartbeat moves
to `clock_timestamp()`; the `NOW()`-in-transaction reap of `ka_kshetra` at 301/308 substeps is
the standing specimen of why.

### 7.5 — Plan honesty (nothing silently absent)

The run report reconciles three sets and must explain every difference: (a) assets the
selection *named*, (b) assets the resolver *planned*, (c) assets the run *executed*.
Writer-gap enforcement (already present, `runner.py:137–179`) is joined by resolver-exclusion
reporting: an asset dropped for `has_writer=false`, DRAFT status, protection, domain
authorization, or rung restriction appears as `excluded:<reason>` rather than vanishing.
"It missed some assets" stops being possible as a *silent* outcome.

### 7.6 — Decommission register (closes L-06, L-07)

Each legacy surface gets the `/api/build/start` treatment — 410 with a pointer — or a
re-point to the real control plane, plus a removal migration for its dead tables:

| Surface | Disposition |
|---|---|
| `/api/build/rebuild`, `/rebuild-all`, `/continue` | 410 → Operations Console actions (`rebuild`, `chart`-selection rebuild, run-group continue) |
| `/api/cockpit/refresh` write path | Deleted; endpoint becomes a pure read |
| `pipeline/dispatcher.py` + `build_checkpoints`, `build_events`-as-control, `builds`, `build_dependencies` | Retired per I6 lifecycle: writers removed, tables tombstoned with `data_disposition`, dropped after one release |
| `/api/build/pyramid-layers` + `pyramid_layers` table | Re-pointed to an `asset_throughput`-derived layer rollup (one status source), with the LayerTower component migrated to the rung board |
| `global_runner.py`, `--global-build` | Retired (§6.4); the flag prints the replacement command and exits 2 |

Exit criterion: a grep for the retired vocabulary in serving code returns only tombstones.

### 7.7 — The Full-Chart Rebuild Journey (the acceptance test)

"Rebuild the chart from the substrate up and reach fully lit, unattended" becomes a **named,
tested flow** rather than an aspiration: one standing run-group template — verify substrate
(all shared assets lit and integrity-passed; `verify`, no rebuild) → chart-domain layers L1→L5
as gated waves, each asset's `lit` earned by its integrity check → a terminal completeness
report (rows vs floor per asset, verification-tier mix at L1, every non-`complete` outcome
with its class and named root).

**When it runs — and why not earlier.** A full L1→L5 rebuild is precisely what I13 forbids
outside the ladder, so the journey is *not* M2's acceptance test and is not run during Track M.
It is the programme's **closing gate, executed after R5 freezes** (§14.2), when every layer it
traverses has already been repaired and frozen. What M2 proves instead is the *contract* —
terminality, accounting, continuation, retry — at rehearsal scale, on one partition of one R0
asset under the I14 carve-out. The journey then composes proven parts rather than testing
unproven ones, which is also why it is expected to pass on the first attempt rather than
becoming another multi-day recovery.

Each rung is a partial instance of the same shape (verify what is beneath → build this layer in
waves → report), so by R5 the motion has been practised six times.

**Acceptance (I4/I16, live, on the chart, unattended):** the journey is dispatched by
SŪTRADHĀRA, runs with zero manual re-dispatch and zero agent intervention, and is certified by
PARĪKṢAKA — the run report is evidence, not testimony; every asset is accounted for (I12); a deliberately injected transient fault —
proxy killed mid-heavy-write — is retried and the run still lands clean; a deliberately
injected deterministic fault fails exactly one asset, blocks exactly its cone, and the report
names the root. Both fault injections run at partition scale (I8), against one partition of one
asset, so the test itself is cheap and safe.

### 7.8 — Objectives

From the 45.6 % baseline: ≥ 95 % of assets complete on first dispatch of a full-chart
journey; 100 % of runs terminal with full accounting (I12 — binary, not a percentage); zero
manual re-dispatches in the journey; mean human interventions per full build → 0.

---

## §8 — Pillar III · The Foundation-First Execution Programme

### 8.1 — The doctrine

Data changes percolate downward. Rebuild L2 before L1 is final and the L1 change
re-invalidates everything L2 just built; the work is done twice and the second time is not
cheaper. So: **start at the foundation; within a layer, take first the assets that depend on
nothing else in that layer; finish the layer completely; freeze it; only then open the next.**
I13 makes it an invariant with no partial advances, and I14 keeps the machinery track from
quietly violating it.

### 8.2 — Two tracks, and the line between them

Machinery (the scope model, the run contract, integrity-gate and digest engines) is
layer-independent. Building it per layer would rebuild the orchestrator six times; climbing
the ladder without it would repair data on machinery known to lose work. So the programme is:

- **Track M (machinery)** — M0–M3 (§14.1), built once, up front. **Data-neutral by
  invariant (I14):** code, registry metadata, control plane. Not one asset's data is repaired
  here. Where a mechanism needs proving against reality, it is proven on a *single partition
  of a single R0 asset* (I8) — a rehearsal, not a repair.
- **The Ladder (rungs R0–R5)** — the asset campaign proper, strictly one layer at a time,
  each rung executed with the finished machinery and closed by its gate.

The line is bright and testable: if a task changes rows in an asset's target table, it belongs
to a rung, not to Track M. Implementation optimization (§19) sits on the rung side of that line
even though it changes code rather than data — because it is inseparable from the asset's
rebuild, and because proving it output-identical requires running that asset.

### 8.3 — The rung gate (what "frozen" means)

Rung Rn is FROZEN when, for **every** asset in layer n — on the chart for chart-domain assets,
on the singleton for shared-domain assets:

1. **Registration conforms** to the §3 contract: `domain`, `rung`, `target_floor`,
   `integrity_check_sql`, `writer_timeout_seconds` where required, `has_substeps` derived from
   the writer class, partition declaration where co-written, consumers recorded.
2. **State is earned**: `lit` / `service_ok` / explicitly-declared `dormant`, written only
   after the integrity gate passed (I5) — never asserted.
3. **Completeness holds**: rows ≥ floor, floors honest per I7 (every below-floor asset
   decided, not left).
4. **Digest published**: output digest (or `substrate_version` for R0 before M3's digest
   engine lands), so a later identical rebuild is provably a no-op and cannot gratuitously
   stale this rung's downstream.
5. **Efficiency pass closed** (§19): every asset in the layer has been profiled, its hotspot
   named, and either optimized with an output-identity proof (I18) or explicitly recorded as
   *examined, already efficient* with the measurement that says so. An asset whose build cost
   was never measured cannot freeze — "we did not look" is not a finding.
6. **Freeze record written and countersigned** into the workbook's Rung Board:
   measurements, digests, date, and the decisions taken (stale floors reset, assets retired,
   deferrals recorded) — carrying PARĪKṢAKA's independent verification evidence and
   ADHIKĀRIN's signature (I16). A freeze asserted by the agent that did the repair is not a
   freeze; the Rung Board rejects a record missing either signature.

**The no-wasted-work guarantee follows.** Once Rn is frozen, work on Rn+1 can only be
invalidated by an Rn change that *changes an output digest* — which after M3 is a deliberate,
priced act (§6.7), scoped by partition receipts to the minimum cone, never a side effect of
someone rebuilding upstream for unrelated reasons.

### 8.4 — The rungs

| Rung | Layer · domain | Assets | Opens when | Campaign content |
|---|---|---|---|---|
| **R0** | L0 Brahmagyan · shared | 40 | Track M complete | The whole substrate, finished. The 6 P0s first — `bg_ephemeris_engine` (66-day red) at the very front, since every L1 computation stands on it — then floors and integrity checks for all 40, real known-answer service probes for the layer's probe assets (v3.0 tier S), `substrate_version`/digest published per asset. Note that `rung` follows *layer*, not domain: four shared-domain assets live in higher layers — `ka_graha_sancara` and `ka_muhurta_seva` (R3), `mi_kula` and `mi_vistara` (R5) — and are not touched here, even though they are substrate. R0 is L0, exactly. |
| **R1** | L1 Gaṇita · chart | 19 | R0 frozen | The correctness core. `ga_prashna`'s zero-row unearned `lit` and `ga_sade_sati`'s 57 % are the two headline repairs; `ga_dashas`' stale 536,471 floor is reset to measured; the verification-tier programme opens here (§4, discipline 3) because `single`-tier L1 facts are the ceiling on everything above; heavy resume is proven on `ga_dashas` / `ga_vichara` / `ga_strength`. |
| **R2** | L2 Bodha · chart | 22 | R1 frozen | 13 P0s including the DRAFT-but-served promotions; the accretion guard goes live on the `chart_facts` co-writers (15 duplicated fact_keys is the measured baseline); `bo_laksana` / `bo_samskara` 60,000 floors re-measured. (Table partitioning is explicitly NOT done here — see §13 item 3.) |
| **R3** | L3 Kāla · chart + shared | 23 | R2 frozen | **A mixed-domain rung** (§6.2): 21 chart-domain assets plus the two shared service probes `ka_graha_sancara` and `ka_muhurta_seva`, both DRAFT — promote or retire them, and give each a real known-answer probe with an SLO (tier S treatment, §9). The gochara transition executed per §5 (v2 reclassified, F-52 rematerialization decided and recorded either way); `ka_kshetra` and `ka_sangam` under the shared `ResumableWriter`; derivation receipts (§4, discipline 5) open here — this is where the first ≥4-input assets live. |
| **R4** | L4 Phala · chart | 9 | R3 frozen | All nine are P0 DRAFT assets — the layer is effectively unbuilt and is the cleanest rung in the ladder: promote or retire each, then build under the full machinery. Narration-fidelity goldens for `ph_phaladesa` (whose no-generative-narration policy must be asserted by a test, not a comment). |
| **R5** | L5 Mīmāṃsā · chart + shared | 15 | R4 frozen | The second mixed-domain rung. The `mi_*` cluster blocked from one root — unblock, then build; zero-row-by-design assets recorded honestly with `target_floor = 0` and a `volume_explanation` rather than left reading dormant; `lel_events` reclassified `SOURCE`; the layer's two shared-domain members (`mi_kula`, `mi_vistara`) built as a shared run within this rung — domain decides *which run*, rung decides *when*. |

Asset counts and P0 inventories are v3.0 §13's, carried. The regenerated workbook (§15) gives
each asset its rung and within-rung wave.

### 8.5 — Order within a rung

Intra-layer topological waves over `depends_on` restricted to the layer — wave 0 is exactly
the operator's stated preference: the assets that depend on nothing else in that layer (and,
for chart-domain rungs, on nothing outside it that is not already frozen). Then wave 1, and so
on. Ties inside a wave are broken by (P0 first, then cheapest-first from cleaned telemetry) so
blocking defects clear early and progress is visible honestly. The planner already computes
these waves correctly for layer scope (`plan.ts:294–308`) — the ladder consumes what exists.

### 8.6 — The six stages of every rung (the repeatable method)

Each rung runs the same six stages, so the campaign is one motion practised six times:

1. **Intake** — re-measure the layer against production (`measure_assets.py` scoped to the
   rung): rows, floors, states, integrity presence, telemetry. The rung starts from fact.
2. **Conform** — complete the §3 registration for this layer's assets only: floors set to
   achieved (I7), `integrity_check_sql` authored per asset, timeouts derived, `has_substeps`
   corrected, partitions declared, consumers recorded. Registry metadata only — no writer runs.
3. **Optimize** (§19) — before spending the rebuild, make the rebuild cheaper. Profile each
   asset's actual run, read its writer and work out what it is really computing, name the
   hotspot, and improve it under an output-identity proof (I18). An asset too broken to profile
   is first made runnable at partition scale, then profiled. This stage sits *before* repair
   deliberately: repairing on a slow implementation and optimizing afterwards pays the same
   30-hour cost twice, and the partition rehearsal I8 already requires doubles as the proving
   ground for the optimization.
4. **Repair** — wave by wave (§8.5), P0s first: fix, rebuild, or retire each asset, now on the
   improved implementation. Every destructive step is snapshot-first, `verify`-dry-run,
   partition-first (I8).
5. **Verify** — integrity checks pass for every asset; completeness ≥ floor; probes green with
   SLOs; digests published; every optimization's identity proof independently re-checked (I16 —
   PARĪKṢAKA re-runs the comparison, it does not read KĀRAKA's); the layer's downstream is
   *not* newly staled by anything this rung did beyond what was intended and priced.
6. **Freeze** — write the freeze record (§8.3, item 6); flip the rung board; the next rung opens.

Stage 2 is deliberately inside the rung rather than in Track M: authoring an asset's integrity
invariant requires knowing what that asset is *supposed* to contain, which is exactly the
understanding stage 1 produces and stage 3 exercises.

---

## §9 — Per-asset elevation, by tier *(carried from v3.0 §6; applied inside rungs)*

The five treatments carry forward unchanged — **G** shared substrate (40; renamed from v3.0's
"global substrate" per I9, same membership), **H** heavy partitioned (10), **M** medium
deterministic (66), **S** service probe (8), **X** generation-bearing (4) — as do the measured
partition granularities: fourteen L1/L2 writers
partition by ayanamsha, `ga_dashas` by `{system}:{aya}`, `bg_reference` by
`{system}:{ayanamsha}`, `ka_kshetra` by `stage{n}:{event_class}:{slice}`, gochara v3 by
`{event_class}::{decade}`, `ka_sangam` by `near + lifetime:{i}`.

Two v4.1 notes.

**Tiers are cross-cutting; rungs are sequential.** A tier is *how* an asset is treated; the rung
decides *when*. Tier H's ten assets are spread across three layers, so tier-H work happens three
times — five assets in R1 (`ga_dashas`, `ga_vichara`, `ga_sensitive`, `ga_strength`,
`ga_vargas`), three in R2 (`bo_laksana`, `bo_laksana_rerank`, `bo_samskara`), two in R3
(`ka_kshetra`, `ka_sangam`) — each time using the one shared `ResumableWriter` built in Track M.

**Tier G and the shared domain are close but not identical**, and the difference matters for
§6.4's watchdog. The shared domain has **44** members; tier G has 40 — the 38 shared L0 assets
that are data, plus the two shared L5 assets (`mi_kula`, `mi_vistara`). The other **four**
shared-domain assets are tier S service probes: `bg_ephemeris_engine` and `bg_panchanga` in L0,
`ka_graha_sancara` and `ka_muhurta_seva` in L3. So: every G asset is shared, but four shared
assets are probes rather than substrate — and half of those sit outside L0 entirely, which is
why the domain axis and the layer axis must stay separate (I13). Tier G's treatment gains §6.7
(digest-compare, invalidation sweep, priced fan-out) as the standard consequence of any G
rebuild, and — because they now run under the one runner (§6.4) — every shared asset, G and S
alike, must declare `writer_timeout_seconds` or a probe SLO.

**Tiers also select optimization techniques (§19.5).** Tier H's partitions are candidates for
intra-asset parallelism and for coarse-to-fine algorithmic redesign; tier M's long tail is where
the cheap systemic sweep pays (indexes, batching, set-based rewrites); tier G's assets are the
substrate that other writers should be *reading* rather than recomputing — `bg_gochara_arcs`
being the exemplar. The tier tells you which technique to reach for first.

Those partition declarations are also what I8 rehearsal (§6.10) consumes. They are already
measured and declared, which is why partition-first execution needs no new *analysis* — but the
dispatch path that runs a single named partition is M2 work, built alongside the `completed_keys`
wiring (§7.2), not something that exists today.

---

## §10 — Orchestrator elevation *(v3.0 §8, extended; freeze exception; writer contract unchanged)*

Everything v3.0 listed — one staleness engine, content-digest freshness with early cutoff,
graded staleness (`fresh · stale:upstream-content · stale:code · stale:config`), integrity gate
after commit, error taxonomy + retry, shared resumability with `completed_keys` wired and plan
totals persisted, `clock_timestamp()` heartbeat, one state vocabulary across DB/Python/TS,
registry lifecycle operations, `has_substeps` derived at registration,
`asset_throughput_state_audit` as the event spine — plus, from the pillars:

single runner for both domains, `global_runner.py` retired (§6.4) · run groups with `group_id`
and shared-first gating (§6.2) · shared advisory-lock discipline with the `shared_barrier`
(§6.4) · chart plans stripped of shared assets, `eff()` deleted (§6.3) · the invalidation
sweep with its `chart_id IS NULL` branch, and staleness propagation running for shared runs at
all (§6.7, closing both halves of L-05) · deadline-aware self-continuation with a generation
counter (§7.2) · failure classification at capture (§7.3) · resolver-exclusion reporting into
the run report (§7.5) · pre-flight treating an unknown dependency as NOT ready (closes L-08;
the one-line inversion at `plan.ts:249`) · the rung guard as a planner-level refusal with a
reason (§6.9).

---

## §11 — DAG elevation *(carried from v3.0 §9; one addition)*

Edge provenance · declared-vs-read audit · shape guards in CI (no cycles, no orphans, every
`depends_on` target active and non-DRAFT — zero dangling edges today; lock it in) · critical
path published · scope explicit in the graph · blast radius on pull request.

Addition: the CI shape guard also asserts **domain coherence** — a shared asset may depend only
on shared assets, because a chart-independent writer cannot read per-chart data without
silently binding itself to one chart. This holds by construction across L0. It is *not* yet
verified for the **four** shared assets that live above L0 — `ka_graha_sancara` and
`ka_muhurta_seva` (L3), `mi_kula` and `mi_vistara` (L5) — all of which sit in layers whose
other members have chart-domain upstreams, so the guard may well fail on them the first time it
runs. That is the point of asserting it: a failure there is a registration defect resolved in
the owning rung (R3 or R5) — either the declared domain is wrong or an edge is — not a reason to
weaken the rule. The two L3 probes are the more likely genuine finding, since a service probe
that reads per-chart data to answer "am I healthy?" is not chart-independent at all.

---

## §12 — UX elevation *(v3.0 §10, extended; multi-chart view retired)*

Carried in full: never disagree with the planner (amber stale-with-data) · collapse cascades to
their root · price every action before it is taken, partition-aware · provenance panel
(digests, writer version, generation, authority, *why stale*) · honest progress with real
denominators · completeness % and verification-tier mix per asset · run timeline from the audit
spine · service-health lane · fix-or-remove the fake Refresh · sweep the small dishonesties.

The pillars' surfaces:

- **The Operations Console** (§6.9) — the single trigger surface; every legacy button re-points
  or 410s (§7.6); out-of-rung selections refused with a reason, never silently greyed.
- **The resolution preview** — run group, waves, price, downstream closure, exclusions with
  reasons — before every dispatch.
- **The run report** (§7.1) as a first-class screen: per-asset terminal outcomes grouped by
  root cause; one-click continue, retry-failed-transient, rebuild-failed-cone.
- **The substrate lane** — shared-domain state shown once, with the chart's consumption
  freshness beside it ("built against substrate v41, current v42 — 9 assets affected, est.
  12 min"), which is the visible form of the L-05 fix.
- **The rung board** — the ladder as a cockpit object: per rung, conformant % · lit % ·
  integrity-passed % · frozen-or-not · current wave · the freeze record when closed. It
  replaces the LayerTower's `pyramid_layers` source (§7.6) and is the operator's answer to
  "where are we".

**Retired by the scope ruling:** the multi-chart view. What replaces it is the substrate lane
plus the rung board — one chart, one substrate, one ladder.

---

## §13 — Infrastructure and database *(carried from v3.0 §11)*

Not the bottleneck: 18 of 21 DAG levels are narrower than the worker pool; the job is already
8 Gi / 4 CPU. The ranked items and their v4.1 homes:

| # | Item | Verdict | Home |
|---|---|---|---|
| 1 | Real volume for the hash spill directory (`/tmp` on Cloud Run is tmpfs; zero volume mounts exist) | **DO IT** | M2 |
| 2 | Connection pooler (parallelism capped by `runs × (1+workers) ≤ ~33`, not CPU) | HIGH | Ladder-era, sized for run groups |
| 3 | `chart_id` partitioning on the largest tables — `DROP PARTITION` rebuilds | HIGH | Post-ladder infra window — the largest tables are L1's (`chart_facts`, `ga_dashas`), and re-laying them out during R2 would be asset-data work on a frozen rung (I13). Deferred until R5 freezes, then executed as a schema migration under snapshot with digest re-verification of every affected rung |
| 4 | Autovacuum tuning on high-churn build tables | worth doing | Post-ladder infra window, with item 3 |
| 5 | Multi-dispatch continuation — in code | do it | M2 (normative via §7.2) |
| 6 | Per-substep tracing and build metrics | worth doing | Progressive, from M2 |
| 7 | CPU/memory sizing | not the bottleneck | defer |
| 8 | Per-chart databases | not applicable at one chart | dropped from the programme |
| 9 | Rehearsal chart formalised | superseded by I8 partition rehearsal (§6.10) | dropped |
| 10 | Determinism harness | do it | M3 |

Run groups do not change the connection-budget arithmetic — `runs × (1 + workers) ≤ ~33` now
counts shared runs too, which I10 makes automatic rather than a thing to remember.

---

## §14 — Roadmap · Track M, then the Ladder

Everything closes on live production verification against the chart (I4). The freeze exception
(I3) is needed from M1 onward for orchestrator internals; M0 needs none.

### 14.1 — Track M (machinery; data-neutral by I14; sequential)

| # | Campaign | Content | Acceptance (live) |
|---|---|---|---|
| **M0** | **Catalogue reconciliation** *(= v3.0 Phase 0 + the v4.1 columns)* | Six-source census (`asset_registry` · `@register()` · `asset_registry_seed.ts` · migrations · `asset_throughput` · `CAPABILITY_MANIFEST.json`); the §3 contract authored as an enforceable per-kind specification including `domain` and `rung`; lifecycle + tombstone fields; semantic de-duplication with declared co-writer partitions; layer-position, kind, and `has_substeps` repair; consumer map; DRAFT-but-served and zero-consumer resolutions; registered-but-dead flagged; telemetry repair (close orphaned rows, recompute medians, backfill `estimated_seconds`); migrations 588/589 registered with the tracked runner; CI guards merged and **blocking**; baseline frozen | v3.0 Phase 0's exit criteria verbatim — three-way diff, contract violations, prefix mismatches, dangling/DRAFT edges, multi-producer partitions, throughput rows on inactive assets, retired-without-disposition, active-without-coverage, unresolved zero-consumer findings all zero, CI blocking — **plus** every asset carrying `domain` and `rung`, and the CI domain-coherence assertion (§11) green |
| **M1** | **Scope & operations model** | The rename (I9) behind a compat window; the split-rule resolver and run groups; chart plans stripped of shared assets; single runner with `global_runner.py` retired; lock discipline and `shared_barrier`; single-shared-asset rebuild path; authorization matrix; pre-flight unknown-is-not-ready (L-08); Operations Console v1 with the resolution preview and the rung guard; **the rung board** (its data comes from the registry and `asset_throughput`, so it ships with the Console rather than after it — and the decommission of `pyramid_layers` depends on it existing); the decommission register executed (§7.6) | A single shared asset is rebuilt alone and relights — proven on one partition of one R0 asset (I8, I14 carve-out) · an `everything` selection dispatches as substrate-run then chart-run, both visible in the cockpit · a chart run and a substrate build can no longer overlap on a shared table, proven by attempting it · every surface in §7.6's table reaches its stated disposition, with no serving code left referencing the retired vocabulary · a selection that would jump a rung is refused with its reason |
| **M2** | **Run-to-completion** | Deadline-aware continuation with the generation counter; `completed_keys` wired through the shared `ResumableWriter`; single-named-partition dispatch (what I8 rehearsal executes on); error taxonomy and bounded retry; per-writer timeout budgets from cleaned telemetry; `clock_timestamp()` heartbeat; plan-honesty reporting; run report v1; the spill-directory volume | All of it proven on **one partition of one R0 asset** (I14 carve-out — no other layer's data is touched, and R0 itself has not opened): that run is killed mid-substep and completes itself unattended with no work redone · an injected proxy drop self-heals · an injected deterministic fault fails that asset and blocks exactly its cone · the run report accounts for 100 % of the plan (I12). The contract at full-chart scale is proven only by §7.7, after R5 |
| **M3** | **Gates, digests, determinism** *(mechanisms only — I14)* | The integrity-gate engine (runs `integrity_check_sql` after commit, writes `lit` only on pass, `incomplete` on fail) and its enforcement switch; floor tooling (measure → propose → record, never fabricate); output-digest computation and upstream-digest freshness with early cutoff; graded staleness; the §6.7 digest-compare and invalidation sweep; the determinism harness; **the profiling and output-identity harness §19 depends on** (per-substep timing, `EXPLAIN (ANALYZE, BUFFERS)` capture, and partition-level digest comparison as a single reusable tool); the cockpit's completeness %, tier-mix and substrate lane | Proven on **one partition of one R0 asset** (I14 carve-out): a deliberately corrupted partition fails its integrity check and cannot reach `lit`; rebuilding that partition unchanged produces an identical digest and stales nothing downstream; the determinism harness passes for it. The engines are then dormant-but-armed until R0 opens and starts authoring real checks (§8.6 stage 2) |

M0 opens immediately. Track M is deliberately finished before R0 rather than interleaved: the
substrate rung is where the machinery's absence hurts most (L-03 — L0 is built by the primitive
runner today), so the ladder's first step is also the machinery's first real customer.

### 14.2 — The Ladder

R0 → R1 → R2 → R3 → R4 → R5, as specified in §8.4, each executed by the six-stage method
(§8.6 — note stage 3, the efficiency pass, runs *before* the rung's rebuild), each closed by the
gate (§8.3), each recorded on the rung board. No rung opens early;
no rung is left partially frozen; nothing above a rung is touched while it is open.

Standing debris from v3.0's Phase 1 lands in its proper rung rather than as a bulk pass:
`bg_ephemeris_engine`'s image fix and the substrate's other P0s in **R0**; `ga_prashna` and
`ga_sade_sati` in **R1**; completion of `ka_gochara_sweep`'s lifecycle exit in **R3** — its
registry row already reads RETIRED, but the zombie throughput rows behind its standing "no
writer registered" red, and its `data_disposition`, are still outstanding — together with the
F-52 decision. Migration-588/589 registration and the spill volume are
machinery and sit in M0/M2.

**The closing gate.** When R5 freezes, the Full-Chart Rebuild Journey (§7.7) runs once, end to
end, unattended: substrate verified, L1→L5 rebuilt in waves, every `lit` earned, one terminal
report. It is the programme's final acceptance and the first time a full-chart rebuild is
attempted — deliberately last, because by then every layer it crosses is frozen and every
mechanism it uses has been proven. Its result, with the completeness and tier-mix figures
measured against §1.5's baseline, is what closes the campaign.

### 14.3 — Continuous tracks

The DAG audit (§11) runs from M0 and gates every rung — no rung freezes with dangling or
over-declared edges in its layer. Operator experience is progressive rather than a final phase:
Console and rung board in M1 (the board is a prerequisite for retiring `pyramid_layers`, §7.6),
run report in M2, completeness %/tier-mix/substrate lane in M3, provenance panel and run
timeline during R1–R2, the polish sweep after R5. The cockpit is elevated *with* the campaign,
which is also what keeps each rung's progress honest while it is being worked.

### 14.4 — v3.0 → v4.1 mapping (nothing dropped except by the scope ruling)

| v3.0 | v4.1 home |
|---|---|
| Phase 0 — all 15 steps | M0 |
| Phase 1 — runtime debris, parity, chart-3 designation | Machinery debris → M0/M2; asset debris → its rung (R0/R1/R3); chart-3 designation and cross-chart parity **retired by the scope ruling**; the rehearsal need it served → I8 partition rehearsal (§6.10) |
| Phase 2 — truth and safety | Mechanisms → M3; per-asset integrity checks, floors and completeness → each rung's stages 2 and 4; UI truth items → M1/M3 |
| Phase 3 — content-addressed freshness | Engine → M3; per-asset digest publication → each rung's stage 4; L1 verification-tier programme → R1 |
| Phase 4 — receipts, retry, continuation, partitioning, autovacuum | Retry + continuation + ResumableWriter → M2; derivation receipts → R3; `chart_id` partitioning + autovacuum → post-ladder infra window (§13 item 3) |
| v3.0 §7 — build-time optimization, six levers | Absorbed: skip-if-unchanged + early cutoff → M3; partition-scoped invalidation → receipts (R3); retry → M2; multi-dispatch continuation → M2/§7.2; timeout right-sizing → §7.4; critical-path shortening → §11. **All six are orchestration; the implementation half they never covered is now §19** |
| Phase 5 — DAG management, pooler | Continuous track (§14.3); pooler at ladder start |
| Phase 6 — operator experience | Progressive (§14.3) |
| Phases' multi-chart provisions | Retired by the scope ruling |

---

## §15 — Per-asset plans *(generated section — regeneration spec)*

v3.0 §13 — the 128 per-asset plans between the `ASSET_PLANS` markers, each with its
three-dimension plan and quantified benefit — remains the live generated surface and is not
duplicated here. Track M0 re-runs `measure_assets.py` **scoped to the chart and the substrate**
and extends `asset_plans.py` + `build_asset_control_workbook.py` to emit, per asset:

- **domain** — shared | chart
- **rung** — R0–R5
- **within-rung wave** — intra-layer topological position (§8.5)
- **continuation class** — resumable-substep | restartable-light | probe-only
- **rehearsal partition** — the partition key an I8 first execution uses for this asset
- **timeout source** — registered | telemetry-derived | default
- **build cost baseline** — p50 AND p90 wall clock, rows, rows/sec (§19.4)
- **bound class** — round-trip | I/O | CPU | algorithmic | not-a-build (§19.4 step 3)
- **hotspot** — the measured dominant cost, named; null until profiled
- **technique proposed / applied** — from §19.5's catalogue
- **identity proof** — digest-equal | tolerance-equal(declared) | sorted-digest-equal | none
- **speedup achieved** — measured delta, or `examined: already efficient` with its measurement

**One correction the regeneration must make:** the current "Rebuild time" dimension is derived
from *median* wall clock and emits one of three templates, which is why 40 assets read "built
once, publish digest" and ~40 read "no bespoke speed work" (§19.1). `asset_plans.py` must
classify on p90 and worst-case as well as median, and must emit a null hotspot rather than a
reassuring sentence for any asset that has not actually been profiled — an unprofiled asset
should read as unknown, not as fine.

and to write the regenerated §13 into this file's own `ASSET_PLANS` markers, at which point
v3.0's copy is annotated "superseded by v4.1 §15". Columns measuring other charts are dropped;
the derivation stays single-sourced, so the workbook's Asset Plans sheet and this section
cannot disagree.

<!-- ASSET_PLANS:BEGIN -->
*Generated by build_control_workbook_v4_1.py (Track M0, §15) from live production measurements, single-chart scope; identical to the workbook's Asset Plans sheet. Do not hand-edit between the markers.*


### L0 · Brahmagyan — 40 assets · 6 non-conformant · 3 P0 · 0 heavy

*Global reference substrate — chart-independent, built once, reused by every chart.* Publish a substrate version + content digest per asset so every chart records what it consumed. Repair the service probes — this layer holds most of them, and one sat red for 66 days. Cost here is paid once and amortises across every chart, so it is the cheapest layer to make honest.


#### `bg_reference` — G · Global substrate · P0 · Blocking defect · CURRENT

**What:** The holy grail of L0 — structured properties of every classical Jyotish concept across 15 specialized typed tables.  
**Now:** global · lit · 1,242 rows / floor 1,485

**domain:** shared · **rung:** R0 · **within-rung wave:** 0 · **continuation class:** resumable-substep · **rehearsal partition:** `{system}:{ayanamsha}` · **timeout source:** registered *(10800s differs from the column default (600s))*


**§19 efficiency ledger** · **p50:** null · **p90:** null · **worst:** null · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count = expected volume formula AND no duplicate natural keys`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• Below floor: 1,242 of 1,485 (84%). Either the floor is stale (re-measure and reset) or the build is incomplete — decide explicitly, never let the gap sit. |
| Rebuild time | • Built once, reused by every chart. Publish `substrate_version` + output digest; per-chart consumers record the version they read, so a no-op rebuild here never cascades.<br>• Substep key `{system}:{ayanamsha}`: add per-substep input digests so a partial substrate change re-runs only the affected partition.<br>• **Not profiled.** Measured baseline only: p50 unmeasured. Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • `has_substeps` is false in the registry while the writer plans substeps: derive the flag from the writer class (Phase 0.6a). Until then the §N.8 completeness gate is silently disabled for this asset.<br>• Keep out of per-chart plans but expose completion to the per-chart readiness gate uniformly (the migration-563 class of bug, made structural).<br>• Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 2 direct dependant(s) stop invalidating when this asset rebuilds to identical content.<br>• A partial build can no longer be promoted to green. |

#### `bg_vidhi_floors` — G · Global substrate · P0 · Blocking defect · DRAFT

**What:** Per-intent-class acharya floor + machine band header + ordered floor items — the compiled scope_tuple->contract input (D-2 Lane V-1).  
**Now:** global · lit · 286 rows / floor 11 · median 0s, worst 1s

**domain:** shared · **rung:** R0 · **within-rung wave:** 0 · **continuation class:** restartable-light · **rehearsal partition:** `n/a — single-shot, whole-asset is the unit` · **timeout source:** default *(600s equals the asset_registry column default and the runner fallback (_WRITER_TIMEOUT_SECONDS) — indistinguishable from never set)*


**§19 efficiency ledger** · **p50:** 0s · **p90:** 1s · **worst:** 1s · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count = expected volume formula AND no duplicate natural keys`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8). |
| Rebuild time | • Built once, reused by every chart. Publish `substrate_version` + output digest; per-chart consumers record the version they read, so a no-op rebuild here never cascades.<br>• **Not profiled.** Measured baseline only: p50 0s · p90 1s · worst 1s · 5 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Layer position: set `layer_index = L0`, derive `layer_name` from the locked lexicon (Phase 0.5a).<br>• Keep out of per-chart plans but expose completion to the per-chart readiness gate uniformly (the migration-563 class of bug, made structural). |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it. |

#### `bg_vidhi_primitives` — G · Global substrate · P0 · Blocking defect · DRAFT

**What:** Versioned vidhi primitive atoms — definition, live-tool mapping+args, fallback face, known_gap CR pointer  
**Now:** global · lit · 52 rows / floor 48 · median 0s, worst 0s

**domain:** shared · **rung:** R0 · **within-rung wave:** 0 · **continuation class:** restartable-light · **rehearsal partition:** `n/a — single-shot, whole-asset is the unit` · **timeout source:** default *(600s equals the asset_registry column default and the runner fallback (_WRITER_TIMEOUT_SECONDS) — indistinguishable from never set)*


**§19 efficiency ledger** · **p50:** 0s · **p90:** 0s · **worst:** 0s · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count = expected volume formula AND no duplicate natural keys`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8). |
| Rebuild time | • Built once, reused by every chart. Publish `substrate_version` + output digest; per-chart consumers record the version they read, so a no-op rebuild here never cascades.<br>• **Not profiled.** Measured baseline only: p50 0s · p90 0s · worst 0s · 5 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Layer position: set `layer_index = L0`, derive `layer_name` from the locked lexicon (Phase 0.5a).<br>• Keep out of per-chart plans but expose completion to the per-chart readiness gate uniformly (the migration-563 class of bug, made structural). |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 1 direct dependant(s) stop invalidating when this asset rebuilds to identical content. |

#### `bg_ephemeris_engine` — S · Service probe · P1 · High · CURRENT

**What:** Swiss Ephemeris (pyswisseph) with DE441 JPL file providing sidereal planetary positions from 9999 BCE to 9999 CE  
**Now:** service · global state error

**domain:** shared · **rung:** R0 · **within-rung wave:** 0 · **continuation class:** probe-only · **rehearsal partition:** `n/a — service probe` · **timeout source:** default *(600s equals the asset_registry column default and the runner fallback (_WRITER_TIMEOUT_SECONDS) — indistinguishable from never set)*


**§19 efficiency ledger** · **p50:** null · **p90:** null · **worst:** null · **rows/sec:** null · **bound class:** not-a-build · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: service probe — there is no build to measure (structural). rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Real liveness + correctness probe with an SLO (not just "responds"): exercise one known-answer query and compare against a pinned expected value; alert on drift or timeout.<br>• Currently in error — repair first (Phase 1), then the probe becomes the regression guard. |
| Rebuild time | • Not a build; nothing to speed up. Exclude from build plans and ETA math. |
| Re-architecture & alignment | • Keep out of per-chart plans but expose completion to the per-chart readiness gate uniformly (the migration-563 class of bug, made structural).<br>• Move to the service lane with `health_probe` + `provides_apis`; `count_sql` must be null. |
| Expected benefit | • A degraded service surfaces in minutes, not months (one sat red for 66 days). |

#### `bg_panchanga` — S · Service probe · P1 · High · CURRENT

**What:** Deterministic panchang computation service (swisseph DE441, Lahiri ayanamsha, Drik-parity)  
**Now:** service · global state lit

**domain:** shared · **rung:** R0 · **within-rung wave:** 0 · **continuation class:** probe-only · **rehearsal partition:** `n/a — service probe` · **timeout source:** default *(600s equals the asset_registry column default and the runner fallback (_WRITER_TIMEOUT_SECONDS) — indistinguishable from never set)*


**§19 efficiency ledger** · **p50:** null · **p90:** null · **worst:** null · **rows/sec:** null · **bound class:** not-a-build · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: service probe — there is no build to measure (structural). rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Real liveness + correctness probe with an SLO (not just "responds"): exercise one known-answer query and compare against a pinned expected value; alert on drift or timeout. |
| Rebuild time | • Not a build; nothing to speed up. Exclude from build plans and ETA math. |
| Re-architecture & alignment | • Keep out of per-chart plans but expose completion to the per-chart readiness gate uniformly (the migration-563 class of bug, made structural).<br>• Move to the service lane with `health_probe` + `provides_apis`; `count_sql` must be null. |
| Expected benefit | • A degraded service surfaces in minutes, not months (one sat red for 66 days). |

#### `bg_ghatana` — G · Global substrate · P2 · Medium · CURRENT

**What:** Life-event ontology (27 event classes keyed to LEL categories, DR-13 shape-extended 2026-07-19: point/interval/chain temporal shapes, gain-vs-loss evidence_requ  
**Now:** global · lit · 39 rows · median 3s, worst 3s

**domain:** shared · **rung:** R0 · **within-rung wave:** 0 · **continuation class:** restartable-light · **rehearsal partition:** `n/a — single-shot, whole-asset is the unit` · **timeout source:** registered *(10800s differs from the column default (600s))*


**§19 efficiency ledger** · **p50:** 3s · **p90:** 3s · **worst:** 3s · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count = expected volume formula AND no duplicate natural keys`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• Set `target_floor` = 39 (achieved on native; floors are aspirational, never fabricated — §N.4). |
| Rebuild time | • Built once, reused by every chart. Publish `substrate_version` + output digest; per-chart consumers record the version they read, so a no-op rebuild here never cascades.<br>• **Not profiled.** Measured baseline only: p50 3s · p90 3s · worst 3s · 1 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Keep out of per-chart plans but expose completion to the per-chart readiness gate uniformly (the migration-563 class of bug, made structural).<br>• Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 5 direct dependant(s) stop invalidating when this asset rebuilds to identical content. |

#### `bg_transit_rules` — G · Global substrate · P2 · Medium · CURRENT

**What:** Classical transit rules (favourable/unfavourable/vedha houses) from BPHS Ch.29 and Phaladeepika Ch.26.  
**Now:** global · lit · 75 rows / floor 50

**domain:** shared · **rung:** R0 · **within-rung wave:** 0 · **continuation class:** restartable-light · **rehearsal partition:** `n/a — single-shot, whole-asset is the unit` · **timeout source:** registered *(10800s differs from the column default (600s))*


**§19 efficiency ledger** · **p50:** null · **p90:** null · **worst:** null · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count = expected volume formula AND no duplicate natural keys`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8). |
| Rebuild time | • Built once, reused by every chart. Publish `substrate_version` + output digest; per-chart consumers record the version they read, so a no-op rebuild here never cascades.<br>• **Not profiled.** Measured baseline only: p50 unmeasured. Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Keep out of per-chart plans but expose completion to the per-chart readiness gate uniformly (the migration-563 class of bug, made structural).<br>• Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 5 direct dependant(s) stop invalidating when this asset rebuilds to identical content. |

#### `bg_class_lifetime_counts` — G · Global substrate · P3 · Standard · CURRENT

**What:** ṢAḌ-DARŚANA W2 (ADJUDICATION-2): N_e — the expected lifetime count of each brahma_event_ontology event class over a 100-year modelled timeline from birth, assum  
**Now:** global · lit · 6 rows

**domain:** shared · **rung:** R0 · **within-rung wave:** 0 · **continuation class:** restartable-light · **rehearsal partition:** `n/a — single-shot, whole-asset is the unit` · **timeout source:** default *(600s equals the asset_registry column default and the runner fallback (_WRITER_TIMEOUT_SECONDS) — indistinguishable from never set)*


**§19 efficiency ledger** · **p50:** null · **p90:** null · **worst:** null · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count = expected volume formula AND no duplicate natural keys`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8). |
| Rebuild time | • Built once, reused by every chart. Publish `substrate_version` + output digest; per-chart consumers record the version they read, so a no-op rebuild here never cascades.<br>• **Not profiled.** Measured baseline only: p50 unmeasured. Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • `brahma_class_priors` has 2 co-writers: declare this writer's natural-key partition in the registry so the (table × generation × partition) uniqueness invariant is checkable (§3.3).<br>• Keep out of per-chart plans but expose completion to the per-chart readiness gate uniformly (the migration-563 class of bug, made structural).<br>• Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 1 direct dependant(s) stop invalidating when this asset rebuilds to identical content. |

#### `bg_class_priors` — G · Global substrate · P3 · Standard · CURRENT

**What:** Ranked salience class-prior weights for composite query-time ranking  
**Now:** global · lit · 177 rows · median 10s, worst 10s

**domain:** shared · **rung:** R0 · **within-rung wave:** 0 · **continuation class:** restartable-light · **rehearsal partition:** `n/a — single-shot, whole-asset is the unit` · **timeout source:** registered *(10800s differs from the column default (600s))*


**§19 efficiency ledger** · **p50:** 10s · **p90:** 10s · **worst:** 10s · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count = expected volume formula AND no duplicate natural keys`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• Set `target_floor` = 177 (achieved on native; floors are aspirational, never fabricated — §N.4). |
| Rebuild time | • Built once, reused by every chart. Publish `substrate_version` + output digest; per-chart consumers record the version they read, so a no-op rebuild here never cascades.<br>• **Not profiled.** Measured baseline only: p50 10s · p90 10s · worst 10s · 1 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • `brahma_class_priors` has 2 co-writers: declare this writer's natural-key partition in the registry so the (table × generation × partition) uniqueness invariant is checkable (§3.3).<br>• Keep out of per-chart plans but expose completion to the per-chart readiness gate uniformly (the migration-563 class of bug, made structural).<br>• Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 1 direct dependant(s) stop invalidating when this asset rebuilds to identical content. |

#### `bg_cohort` — G · Global substrate · P3 · Standard · CURRENT

**What:** Synthetic (not real-person) reference population of ~10,000 birth charts' Lahiri-sidereal graha + Lagna positions (sign/nakshatra grain) — the statistical base-  
**Now:** global · lit · 10,000 rows / floor 10,000

**domain:** shared · **rung:** R0 · **within-rung wave:** 0 · **continuation class:** restartable-light · **rehearsal partition:** `n/a — single-shot, whole-asset is the unit` · **timeout source:** default *(600s equals the asset_registry column default and the runner fallback (_WRITER_TIMEOUT_SECONDS) — indistinguishable from never set)*


**§19 efficiency ledger** · **p50:** null · **p90:** null · **worst:** null · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count = expected volume formula AND no duplicate natural keys`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8). |
| Rebuild time | • Built once, reused by every chart. Publish `substrate_version` + output digest; per-chart consumers record the version they read, so a no-op rebuild here never cascades.<br>• **Not profiled.** Measured baseline only: p50 unmeasured. Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Keep out of per-chart plans but expose completion to the per-chart readiness gate uniformly (the migration-563 class of bug, made structural).<br>• No detected serving consumer (Phase 0.8c): record the missing consumer or retire with a disposition.<br>• Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 1 direct dependant(s) stop invalidating when this asset rebuilds to identical content. |

#### `bg_compendium_index` — G · Global substrate · P3 · Standard · CURRENT

**What:** Cross-reference index over the 15 classical texts — chapter summaries, topic-coverage map, significance scores  
**Now:** global · lit · 9,538 rows / floor 9,538

**domain:** shared · **rung:** R0 · **within-rung wave:** 1 · **continuation class:** restartable-light · **rehearsal partition:** `n/a — single-shot, whole-asset is the unit` · **timeout source:** registered *(10800s differs from the column default (600s))*


**§19 efficiency ledger** · **p50:** null · **p90:** null · **worst:** null · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count = expected volume formula AND no duplicate natural keys`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8). |
| Rebuild time | • Built once, reused by every chart. Publish `substrate_version` + output digest; per-chart consumers record the version they read, so a no-op rebuild here never cascades.<br>• **Not profiled.** Measured baseline only: p50 unmeasured. Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Keep out of per-chart plans but expose completion to the per-chart readiness gate uniformly (the migration-563 class of bug, made structural).<br>• Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it. |

#### `bg_concordance` — G · Global substrate · P3 · Standard · CURRENT

**What:** Cross-school chunk-pointer index per (topic, school) — chunk refs for L1+ synthesis at query-time  
**Now:** global · lit · 720 rows / floor 800

**domain:** shared · **rung:** R0 · **within-rung wave:** 2 · **continuation class:** restartable-light · **rehearsal partition:** `n/a — single-shot, whole-asset is the unit` · **timeout source:** registered *(10800s differs from the column default (600s))*


**§19 efficiency ledger** · **p50:** null · **p90:** null · **worst:** null · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count = expected volume formula AND no duplicate natural keys`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• Below floor: 720 of 800 (90%). Either the floor is stale (re-measure and reset) or the build is incomplete — decide explicitly, never let the gap sit. |
| Rebuild time | • Built once, reused by every chart. Publish `substrate_version` + output digest; per-chart consumers record the version they read, so a no-op rebuild here never cascades.<br>• **Not profiled.** Measured baseline only: p50 unmeasured. Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Keep out of per-chart plans but expose completion to the per-chart readiness gate uniformly (the migration-563 class of bug, made structural).<br>• No detected serving consumer (Phase 0.8c): record the missing consumer or retire with a disposition.<br>• Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it. |

#### `bg_dasha_systems` — G · Global substrate · P3 · Standard · CURRENT

**What:** Classical dasha system definitions — sequence rules, computation methods, conditions for use  
**Now:** global · lit · 20 rows / floor 18

**domain:** shared · **rung:** R0 · **within-rung wave:** 1 · **continuation class:** restartable-light · **rehearsal partition:** `n/a — single-shot, whole-asset is the unit` · **timeout source:** registered *(10800s differs from the column default (600s))*


**§19 efficiency ledger** · **p50:** null · **p90:** null · **worst:** null · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count = expected volume formula AND no duplicate natural keys`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8). |
| Rebuild time | • Built once, reused by every chart. Publish `substrate_version` + output digest; per-chart consumers record the version they read, so a no-op rebuild here never cascades.<br>• **Not profiled.** Measured baseline only: p50 unmeasured. Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Keep out of per-chart plans but expose completion to the per-chart readiness gate uniformly (the migration-563 class of bug, made structural).<br>• Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it. |

#### `bg_dignity_reference` — G · Global substrate · P3 · Standard · CURRENT

**What:** Planetary dignity and state reference: exaltation/debilitation/own-sign boundaries, naisargika friendship matrix, avastha schemes, combustion orbs, motion state  
**Now:** global · lit · 151 rows / floor 151

**domain:** shared · **rung:** R0 · **within-rung wave:** 0 · **continuation class:** restartable-light · **rehearsal partition:** `n/a — single-shot, whole-asset is the unit` · **timeout source:** registered *(10800s differs from the column default (600s))*


**§19 efficiency ledger** · **p50:** null · **p90:** null · **worst:** null · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count = expected volume formula AND no duplicate natural keys`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8). |
| Rebuild time | • Built once, reused by every chart. Publish `substrate_version` + output digest; per-chart consumers record the version they read, so a no-op rebuild here never cascades.<br>• **Not profiled.** Measured baseline only: p50 unmeasured. Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Keep out of per-chart plans but expose completion to the per-chart readiness gate uniformly (the migration-563 class of bug, made structural).<br>• Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it. |

#### `bg_doshas` — G · Global substrate · P3 · Standard · CURRENT

**What:** Classical dosha definitions — formation rules, effects, severity, cancellation conditions  
**Now:** global · lit · 79 rows / floor 50

**domain:** shared · **rung:** R0 · **within-rung wave:** 1 · **continuation class:** restartable-light · **rehearsal partition:** `n/a — single-shot, whole-asset is the unit` · **timeout source:** registered *(10800s differs from the column default (600s))*


**§19 efficiency ledger** · **p50:** null · **p90:** null · **worst:** null · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count = expected volume formula AND no duplicate natural keys`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8). |
| Rebuild time | • Built once, reused by every chart. Publish `substrate_version` + output digest; per-chart consumers record the version they read, so a no-op rebuild here never cascades.<br>• **Not profiled.** Measured baseline only: p50 unmeasured. Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Keep out of per-chart plans but expose completion to the per-chart readiness gate uniformly (the migration-563 class of bug, made structural).<br>• Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it. |

#### `bg_ephemeris` — G · Global substrate · P3 · Standard · CURRENT

**What:** Swiss Ephemeris DE441 — raw astronomical positions for all grahas  
**Now:** global · lit · 825,084 rows / floor 825,084

**domain:** shared · **rung:** R0 · **within-rung wave:** 0 · **continuation class:** restartable-light · **rehearsal partition:** `n/a — single-shot, whole-asset is the unit` · **timeout source:** registered *(10800s differs from the column default (600s))*


**§19 efficiency ledger** · **p50:** null · **p90:** null · **worst:** null · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count = expected volume formula AND no duplicate natural keys`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8). |
| Rebuild time | • Built once, reused by every chart. Publish `substrate_version` + output digest; per-chart consumers record the version they read, so a no-op rebuild here never cascades.<br>• **Not profiled.** Measured baseline only: p50 unmeasured. Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Keep out of per-chart plans but expose completion to the per-chart readiness gate uniformly (the migration-563 class of bug, made structural).<br>• Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 4 direct dependant(s) stop invalidating when this asset rebuilds to identical content. |

#### `bg_formula_constants` — G · Global substrate · P3 · Standard · CURRENT

**What:** Canonical formula constants registry — combustion orbs, obstruction thresholds, magnitude tiers, dignity scores, house weights, attention budget, and engineerin  
**Now:** global · lit · 17 rows · median 2s, worst 2s

**domain:** shared · **rung:** R0 · **within-rung wave:** 0 · **continuation class:** restartable-light · **rehearsal partition:** `n/a — single-shot, whole-asset is the unit` · **timeout source:** registered *(10800s differs from the column default (600s))*


**§19 efficiency ledger** · **p50:** 2s · **p90:** 2s · **worst:** 2s · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count = expected volume formula AND no duplicate natural keys`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• Set `target_floor` = 17 (achieved on native; floors are aspirational, never fabricated — §N.4). |
| Rebuild time | • Built once, reused by every chart. Publish `substrate_version` + output digest; per-chart consumers record the version they read, so a no-op rebuild here never cascades.<br>• **Not profiled.** Measured baseline only: p50 2s · p90 2s · worst 2s · 1 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Keep out of per-chart plans but expose completion to the per-chart readiness gate uniformly (the migration-563 class of bug, made structural).<br>• Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 3 direct dependant(s) stop invalidating when this asset rebuilds to identical content. |

#### `bg_gochara_arcs` — G · Global substrate · P3 · Standard · CURRENT

**What:** W2G (GOCHARA-2.0, item 19)  
**Now:** global · lit · 34,553 rows / floor 34,553

**domain:** shared · **rung:** R0 · **within-rung wave:** 0 · **continuation class:** resumable-substep · **rehearsal partition:** `body` · **timeout source:** registered *(1800s differs from the column default (600s))*


**§19 efficiency ledger** · **p50:** null · **p90:** null · **worst:** null · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count = expected volume formula AND no duplicate natural keys`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8). |
| Rebuild time | • Built once, reused by every chart. Publish `substrate_version` + output digest; per-chart consumers record the version they read, so a no-op rebuild here never cascades.<br>• Substep key `body`: add per-substep input digests so a partial substrate change re-runs only the affected partition.<br>• **Not profiled.** Measured baseline only: p50 unmeasured. Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Keep out of per-chart plans but expose completion to the per-chart readiness gate uniformly (the migration-563 class of bug, made structural).<br>• No detected serving consumer (Phase 0.8c): record the missing consumer or retire with a disposition.<br>• Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 1 direct dependant(s) stop invalidating when this asset rebuilds to identical content. |

#### `bg_gochara_citation_resolution` — G · Global substrate · P3 · Standard · CURRENT

**What:** MR-25 (PARIṢKĀRA): maps gochara citation strings (gochara_grammar/citations.py constants + primitives.py families) to classical_text_chunks verse_refs  
**Now:** global · — · 14 rows / floor 4

**domain:** shared · **rung:** R0 · **within-rung wave:** 1 · **continuation class:** restartable-light · **rehearsal partition:** `n/a — single-shot, whole-asset is the unit` · **timeout source:** registered *(60s differs from the column default (600s))*


**§19 efficiency ledger** · **p50:** null · **p90:** null · **worst:** null · **rows/sec:** null · **bound class:** not-a-build · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: no registered writer — nothing builds this asset (structural). rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count = expected volume formula AND no duplicate natural keys`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8). |
| Rebuild time | • Built once, reused by every chart. Publish `substrate_version` + output digest; per-chart consumers record the version they read, so a no-op rebuild here never cascades.<br>• No registered writer: nothing builds this asset, so there is no build cost to profile. Bound class `not-a-build` (§19.4 step 3) — hotspot is null by structure, not by omission. |
| Re-architecture & alignment | • Registered but never built: provision a writer, demote to DRAFT, or retire with a disposition (Phase 0.8a).<br>• Keep out of per-chart plans but expose completion to the per-chart readiness gate uniformly (the migration-563 class of bug, made structural).<br>• Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it. |

#### `bg_kota_chakra_rings` — G · Global substrate · P3 · Standard · CURRENT

**What:** ADJUDICATION-9: the Kota-Chakra fort-chakra ring partition (stambha/durgantara/prakara/bahya, 1-indexed distance from janma nakshatra), moved from an inline wri  
**Now:** global · lit · 27 rows / floor 27

**domain:** shared · **rung:** R0 · **within-rung wave:** 0 · **continuation class:** restartable-light · **rehearsal partition:** `n/a — single-shot, whole-asset is the unit` · **timeout source:** registered *(60s differs from the column default (600s))*


**§19 efficiency ledger** · **p50:** null · **p90:** null · **worst:** null · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count = expected volume formula AND no duplicate natural keys`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8). |
| Rebuild time | • Built once, reused by every chart. Publish `substrate_version` + output digest; per-chart consumers record the version they read, so a no-op rebuild here never cascades.<br>• **Not profiled.** Measured baseline only: p50 unmeasured. Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Keep out of per-chart plans but expose completion to the per-chart readiness gate uniformly (the migration-563 class of bug, made structural).<br>• No detected serving consumer (Phase 0.8c): record the missing consumer or retire with a disposition.<br>• Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 1 direct dependant(s) stop invalidating when this asset rebuilds to identical content. |

#### `bg_kp_sublord_division` — G · Global substrate · P3 · Standard · CURRENT

**What:** ADJUDICATION-7 Part 1: the canonical 249-fold Krishnamurti Paddhati sub-lord division of the sidereal zodiac  
**Now:** global · lit · 249 rows / floor 249 · median 1s, worst 1s

**domain:** shared · **rung:** R0 · **within-rung wave:** 0 · **continuation class:** restartable-light · **rehearsal partition:** `n/a — single-shot, whole-asset is the unit` · **timeout source:** registered *(120s differs from the column default (600s))*


**§19 efficiency ledger** · **p50:** 1s · **p90:** 1s · **worst:** 1s · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count = expected volume formula AND no duplicate natural keys`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8). |
| Rebuild time | • Built once, reused by every chart. Publish `substrate_version` + output digest; per-chart consumers record the version they read, so a no-op rebuild here never cascades.<br>• **Not profiled.** Measured baseline only: p50 1s · p90 1s · worst 1s · 1 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Keep out of per-chart plans but expose completion to the per-chart readiness gate uniformly (the migration-563 class of bug, made structural).<br>• No detected serving consumer (Phase 0.8c): record the missing consumer or retire with a disposition.<br>• Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 1 direct dependant(s) stop invalidating when this asset rebuilds to identical content. |

#### `bg_medical_mappings` — G · Global substrate · P3 · Standard · CURRENT

**What:** Classical Ayurvedic graha → dosha/dhatu/organ/body-part mappings per BPHS Ch.18, Ashtanga Hridayam, Charaka Samhita  
**Now:** global · lit · 21 rows / floor 9

**domain:** shared · **rung:** R0 · **within-rung wave:** 0 · **continuation class:** restartable-light · **rehearsal partition:** `n/a — single-shot, whole-asset is the unit` · **timeout source:** registered *(10800s differs from the column default (600s))*


**§19 efficiency ledger** · **p50:** null · **p90:** null · **worst:** null · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count = expected volume formula AND no duplicate natural keys`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8). |
| Rebuild time | • Built once, reused by every chart. Publish `substrate_version` + output digest; per-chart consumers record the version they read, so a no-op rebuild here never cascades.<br>• **Not profiled.** Measured baseline only: p50 unmeasured. Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Keep out of per-chart plans but expose completion to the per-chart readiness gate uniformly (the migration-563 class of bug, made structural).<br>• Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it. |

#### `bg_muhurta_lattice` — G · Global substrate · P3 · Standard · CURRENT

**What:** Global chart-independent muhūrta factor lattice — Agnivāsa states, combination-yoga spans (Sarvārtha-siddhi, Amṛta-siddhi, Ravi/Guru-Puṣya, Tripuṣkara/Dvipuṣkar  
**Now:** global · lit · 164,886 rows / floor 91,477

**domain:** shared · **rung:** R0 · **within-rung wave:** 0 · **continuation class:** resumable-substep · **rehearsal partition:** `year:{year}` · **timeout source:** default *(600s equals the asset_registry column default and the runner fallback (_WRITER_TIMEOUT_SECONDS) — indistinguishable from never set)*


**§19 efficiency ledger** · **p50:** null · **p90:** null · **worst:** null · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count = expected volume formula AND no duplicate natural keys`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8). |
| Rebuild time | • Built once, reused by every chart. Publish `substrate_version` + output digest; per-chart consumers record the version they read, so a no-op rebuild here never cascades.<br>• Substep key `year:{year}`: add per-substep input digests so a partial substrate change re-runs only the affected partition.<br>• **Not profiled.** Measured baseline only: p50 unmeasured. Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Keep out of per-chart plans but expose completion to the per-chart readiness gate uniformly (the migration-563 class of bug, made structural).<br>• Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it. |

#### `bg_nakshatra` — G · Global substrate · P3 · Standard · CURRENT

**What:** Global nakshatra reference — 28 nakshatras (incl  
**Now:** global · lit · 2,857 rows / floor 2,857

**domain:** shared · **rung:** R0 · **within-rung wave:** 0 · **continuation class:** restartable-light · **rehearsal partition:** `n/a — single-shot, whole-asset is the unit` · **timeout source:** registered *(10800s differs from the column default (600s))*


**§19 efficiency ledger** · **p50:** null · **p90:** null · **worst:** null · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count = expected volume formula AND no duplicate natural keys`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8). |
| Rebuild time | • Built once, reused by every chart. Publish `substrate_version` + output digest; per-chart consumers record the version they read, so a no-op rebuild here never cascades.<br>• **Not profiled.** Measured baseline only: p50 unmeasured. Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Keep out of per-chart plans but expose completion to the per-chart readiness gate uniformly (the migration-563 class of bug, made structural).<br>• Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 1 direct dependant(s) stop invalidating when this asset rebuilds to identical content. |

#### `bg_nakshatra_medical` — G · Global substrate · P3 · Standard · CURRENT

**What:** 27 nakshatras → body-part correspondences per Ashtanga Hridayam / BPHS  
**Now:** global · lit · 27 rows / floor 27

**domain:** shared · **rung:** R0 · **within-rung wave:** 0 · **continuation class:** restartable-light · **rehearsal partition:** `n/a — single-shot, whole-asset is the unit` · **timeout source:** default *(600s equals the asset_registry column default and the runner fallback (_WRITER_TIMEOUT_SECONDS) — indistinguishable from never set)*


**§19 efficiency ledger** · **p50:** null · **p90:** null · **worst:** null · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count = expected volume formula AND no duplicate natural keys`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8). |
| Rebuild time | • Built once, reused by every chart. Publish `substrate_version` + output digest; per-chart consumers record the version they read, so a no-op rebuild here never cascades.<br>• **Not profiled.** Measured baseline only: p50 unmeasured. Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Keep out of per-chart plans but expose completion to the per-chart readiness gate uniformly (the migration-563 class of bug, made structural).<br>• Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it. |

#### `bg_ontology` — G · Global substrate · P3 · Standard · CURRENT

**What:** Canonical entity vocabulary — grahas, signs, houses, nakshatras, dashas, domains + synonyms  
**Now:** global · lit · 737 rows / floor 623

**domain:** shared · **rung:** R0 · **within-rung wave:** 0 · **continuation class:** restartable-light · **rehearsal partition:** `n/a — single-shot, whole-asset is the unit` · **timeout source:** registered *(10800s differs from the column default (600s))*


**§19 efficiency ledger** · **p50:** null · **p90:** null · **worst:** null · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count = expected volume formula AND no duplicate natural keys`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8). |
| Rebuild time | • Built once, reused by every chart. Publish `substrate_version` + output digest; per-chart consumers record the version they read, so a no-op rebuild here never cascades.<br>• **Not profiled.** Measured baseline only: p50 unmeasured. Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Keep out of per-chart plans but expose completion to the per-chart readiness gate uniformly (the migration-563 class of bug, made structural).<br>• Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 3 direct dependant(s) stop invalidating when this asset rebuilds to identical content. |

#### `bg_parihara_rules` — G · Global substrate · P3 · Standard · CURRENT

**What:** Global chart-independent parihāra (doṣa-cancellation) graph, per-activity muhūrta factor-quality rules, and the Muhūrta Factor Census + corpus-gap register  
**Now:** global · lit · 449 rows / floor 447

**domain:** shared · **rung:** R0 · **within-rung wave:** 0 · **continuation class:** restartable-light · **rehearsal partition:** `n/a — single-shot, whole-asset is the unit` · **timeout source:** default *(600s equals the asset_registry column default and the runner fallback (_WRITER_TIMEOUT_SECONDS) — indistinguishable from never set)*


**§19 efficiency ledger** · **p50:** null · **p90:** null · **worst:** null · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count = expected volume formula AND no duplicate natural keys`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8). |
| Rebuild time | • Built once, reused by every chart. Publish `substrate_version` + output digest; per-chart consumers record the version they read, so a no-op rebuild here never cascades.<br>• **Not profiled.** Measured baseline only: p50 unmeasured. Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Keep out of per-chart plans but expose completion to the per-chart readiness gate uniformly (the migration-563 class of bug, made structural).<br>• Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it. |

#### `bg_phaladeepika_latta` — G · Global substrate · P3 · Standard · CURRENT

**What:** ADJUDICATION-11 Part 4: Phaladeepika Adh  
**Now:** global · lit · 8 rows / floor 8

**domain:** shared · **rung:** R0 · **within-rung wave:** 0 · **continuation class:** restartable-light · **rehearsal partition:** `n/a — single-shot, whole-asset is the unit` · **timeout source:** registered *(60s differs from the column default (600s))*


**§19 efficiency ledger** · **p50:** null · **p90:** null · **worst:** null · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count = expected volume formula AND no duplicate natural keys`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8). |
| Rebuild time | • Built once, reused by every chart. Publish `substrate_version` + output digest; per-chart consumers record the version they read, so a no-op rebuild here never cascades.<br>• **Not profiled.** Measured baseline only: p50 unmeasured. Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Keep out of per-chart plans but expose completion to the per-chart readiness gate uniformly (the migration-563 class of bug, made structural).<br>• Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 1 direct dependant(s) stop invalidating when this asset rebuilds to identical content. |

#### `bg_prashna_rules` — G · Global substrate · P3 · Standard · CURRENT

**What:** Static horary astrology rules — Prashna lagna methods, Tajik yogas, significators, fructification rules, and special techniques.  
**Now:** global · lit · 41 rows / floor 41

**domain:** shared · **rung:** R0 · **within-rung wave:** 0 · **continuation class:** restartable-light · **rehearsal partition:** `n/a — single-shot, whole-asset is the unit` · **timeout source:** registered *(10800s differs from the column default (600s))*


**§19 efficiency ledger** · **p50:** null · **p90:** null · **worst:** null · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count = expected volume formula AND no duplicate natural keys`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8). |
| Rebuild time | • Built once, reused by every chart. Publish `substrate_version` + output digest; per-chart consumers record the version they read, so a no-op rebuild here never cascades.<br>• **Not profiled.** Measured baseline only: p50 unmeasured. Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Declare `target_table` (or `clear_tables` if it writes several) so clear/rebuild and size reporting stop guessing from `count_sql`.<br>• Keep out of per-chart plans but expose completion to the per-chart readiness gate uniformly (the migration-563 class of bug, made structural).<br>• Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it. |

#### `bg_remedies` — G · Global substrate · P3 · Standard · CURRENT

**What:** Classical remedies: mantras, gemstones, charity, vrata, yantras, puja, tantric, ayurvedic, vastu, behavioral  
**Now:** global · lit · 336 rows / floor 266

**domain:** shared · **rung:** R0 · **within-rung wave:** 0 · **continuation class:** restartable-light · **rehearsal partition:** `n/a — single-shot, whole-asset is the unit` · **timeout source:** registered *(10800s differs from the column default (600s))*


**§19 efficiency ledger** · **p50:** null · **p90:** null · **worst:** null · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count = expected volume formula AND no duplicate natural keys`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8). |
| Rebuild time | • Built once, reused by every chart. Publish `substrate_version` + output digest; per-chart consumers record the version they read, so a no-op rebuild here never cascades.<br>• **Not profiled.** Measured baseline only: p50 unmeasured. Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Keep out of per-chart plans but expose completion to the per-chart readiness gate uniformly (the migration-563 class of bug, made structural).<br>• Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it. |

#### `bg_rules` — G · Global substrate · P3 · Standard · CURRENT

**What:** Classical rules extracted from text chunks via Python regex patterns — verse-traceable  
**Now:** global · lit · 3,003 rows / floor 2,912

**domain:** shared · **rung:** R0 · **within-rung wave:** 1 · **continuation class:** restartable-light · **rehearsal partition:** `n/a — single-shot, whole-asset is the unit` · **timeout source:** registered *(10800s differs from the column default (600s))*


**§19 efficiency ledger** · **p50:** null · **p90:** null · **worst:** null · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count = expected volume formula AND no duplicate natural keys`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8). |
| Rebuild time | • Built once, reused by every chart. Publish `substrate_version` + output digest; per-chart consumers record the version they read, so a no-op rebuild here never cascades.<br>• **Not profiled.** Measured baseline only: p50 unmeasured. Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Keep out of per-chart plans but expose completion to the per-chart readiness gate uniformly (the migration-563 class of bug, made structural).<br>• Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 3 direct dependant(s) stop invalidating when this asset rebuilds to identical content. |

#### `bg_sarvatobhadra_grid` — G · Global substrate · P3 · Standard · CURRENT

**What:** ADJUDICATION-11: school-tagged Sarvatobhadra Chakra grid reference table, registered DELIBERATELY EMPTY  
**Now:** global · lit · 0 rows

**domain:** shared · **rung:** R0 · **within-rung wave:** 0 · **continuation class:** restartable-light · **rehearsal partition:** `n/a — single-shot, whole-asset is the unit` · **timeout source:** default *(600s equals the asset_registry column default and the runner fallback (_WRITER_TIMEOUT_SECONDS) — indistinguishable from never set)*


**§19 efficiency ledger** · **p50:** null · **p90:** null · **worst:** null · **rows/sec:** null · **bound class:** not-a-build · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: no registered writer — nothing builds this asset (structural). rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count = expected volume formula AND no duplicate natural keys`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8). |
| Rebuild time | • Built once, reused by every chart. Publish `substrate_version` + output digest; per-chart consumers record the version they read, so a no-op rebuild here never cascades.<br>• No registered writer: nothing builds this asset, so there is no build cost to profile. Bound class `not-a-build` (§19.4 step 3) — hotspot is null by structure, not by omission. |
| Re-architecture & alignment | • Keep out of per-chart plans but expose completion to the per-chart readiness gate uniformly (the migration-563 class of bug, made structural).<br>• Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 1 direct dependant(s) stop invalidating when this asset rebuilds to identical content. |

#### `bg_sign_medical` — G · Global substrate · P3 · Standard · CURRENT

**What:** Kalapurusha (Cosmic Man) zodiacal body-map: 12 signs → body-part / organ-systems / element / dosha (BPHS Ch.4 + Ashtanga Hridayam)  
**Now:** global · lit · 12 rows / floor 12

**domain:** shared · **rung:** R0 · **within-rung wave:** 0 · **continuation class:** restartable-light · **rehearsal partition:** `n/a — single-shot, whole-asset is the unit` · **timeout source:** registered *(10800s differs from the column default (600s))*


**§19 efficiency ledger** · **p50:** null · **p90:** null · **worst:** null · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count = expected volume formula AND no duplicate natural keys`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8). |
| Rebuild time | • Built once, reused by every chart. Publish `substrate_version` + output digest; per-chart consumers record the version they read, so a no-op rebuild here never cascades.<br>• **Not profiled.** Measured baseline only: p50 unmeasured. Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Layer position: set `layer_index = L0`, derive `layer_name` from the locked lexicon (Phase 0.5a).<br>• Keep out of per-chart plans but expose completion to the per-chart readiness gate uniformly (the migration-563 class of bug, made structural).<br>• Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it. |

#### `bg_sky_calendar` — G · Global substrate · P3 · Standard · CURRENT

**What:** Chart-independent global sky-event diary: sign ingresses (9 grahas), planetary stations (5 classical planets), solar/lunar eclipse timing, and Jupiter-Saturn do  
**Now:** global · lit · 31,059 rows / floor 31,064

**domain:** shared · **rung:** R0 · **within-rung wave:** 0 · **continuation class:** restartable-light · **rehearsal partition:** `n/a — single-shot, whole-asset is the unit` · **timeout source:** default *(600s equals the asset_registry column default and the runner fallback (_WRITER_TIMEOUT_SECONDS) — indistinguishable from never set)*


**§19 efficiency ledger** · **p50:** null · **p90:** null · **worst:** null · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count = expected volume formula AND no duplicate natural keys`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• Below floor: 31,059 of 31,064 (100%). Either the floor is stale (re-measure and reset) or the build is incomplete — decide explicitly, never let the gap sit. |
| Rebuild time | • Built once, reused by every chart. Publish `substrate_version` + output digest; per-chart consumers record the version they read, so a no-op rebuild here never cascades.<br>• **Not profiled.** Measured baseline only: p50 unmeasured. Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Keep out of per-chart plans but expose completion to the per-chart readiness gate uniformly (the migration-563 class of bug, made structural).<br>• No detected serving consumer (Phase 0.8c): record the missing consumer or retire with a disposition.<br>• Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 1 direct dependant(s) stop invalidating when this asset rebuilds to identical content. |

#### `bg_text_index` — G · Global substrate · P3 · Standard · CURRENT

**What:** Measurement of retrieval index health — distinct topic tags across embedded + indexed chunks  
**Now:** global · lit · 361 rows / floor 400

**domain:** shared · **rung:** R0 · **within-rung wave:** 1 · **continuation class:** restartable-light · **rehearsal partition:** `n/a — single-shot, whole-asset is the unit` · **timeout source:** registered *(10800s differs from the column default (600s))*


**§19 efficiency ledger** · **p50:** null · **p90:** null · **worst:** null · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count = expected volume formula AND no duplicate natural keys`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• Below floor: 361 of 400 (90%). Either the floor is stale (re-measure and reset) or the build is incomplete — decide explicitly, never let the gap sit.<br>• Embeddings are a deterministic transform (permitted). Pin the model id + dimension in the output digest so a model change invalidates correctly. |
| Rebuild time | • Built once, reused by every chart. Publish `substrate_version` + output digest; per-chart consumers record the version they read, so a no-op rebuild here never cascades.<br>• **Not profiled.** Measured baseline only: p50 unmeasured. Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • `classical_text_chunks` has 2 co-writers: declare this writer's natural-key partition in the registry so the (table × generation × partition) uniqueness invariant is checkable (§3.3).<br>• Keep out of per-chart plans but expose completion to the per-chart readiness gate uniformly (the migration-563 class of bug, made structural).<br>• Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it. |

#### `bg_texts` — G · Global substrate · P3 · Standard · CURRENT

**What:** Indexed verse chunks from BPHS, Jaimini Sutram, KP Reader, Tajaka, Phaladeepika, etc.  
**Now:** global · lit · 10,667 rows / floor 10,651

**domain:** shared · **rung:** R0 · **within-rung wave:** 0 · **continuation class:** restartable-light · **rehearsal partition:** `n/a — single-shot, whole-asset is the unit` · **timeout source:** registered *(10800s differs from the column default (600s))*


**§19 efficiency ledger** · **p50:** null · **p90:** null · **worst:** null · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count = expected volume formula AND no duplicate natural keys`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• Embeddings are a deterministic transform (permitted). Pin the model id + dimension in the output digest so a model change invalidates correctly. |
| Rebuild time | • Built once, reused by every chart. Publish `substrate_version` + output digest; per-chart consumers record the version they read, so a no-op rebuild here never cascades.<br>• **Not profiled.** Measured baseline only: p50 unmeasured. Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • `classical_text_chunks` has 2 co-writers: declare this writer's natural-key partition in the registry so the (table × generation × partition) uniqueness invariant is checkable (§3.3).<br>• Keep out of per-chart plans but expose completion to the per-chart readiness gate uniformly (the migration-563 class of bug, made structural).<br>• Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 4 direct dependant(s) stop invalidating when this asset rebuilds to identical content. |

#### `bg_transit_engine` — G · Global substrate · P3 · Standard · CURRENT

**What:** L0 average graha motion parameters — daily motion, zodiac period, sign residence  
**Now:** global · lit · 9 rows / floor 9

**domain:** shared · **rung:** R0 · **within-rung wave:** 0 · **continuation class:** restartable-light · **rehearsal partition:** `n/a — single-shot, whole-asset is the unit` · **timeout source:** default *(600s equals the asset_registry column default and the runner fallback (_WRITER_TIMEOUT_SECONDS) — indistinguishable from never set)*


**§19 efficiency ledger** · **p50:** null · **p90:** null · **worst:** null · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count = expected volume formula AND no duplicate natural keys`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8). |
| Rebuild time | • Built once, reused by every chart. Publish `substrate_version` + output digest; per-chart consumers record the version they read, so a no-op rebuild here never cascades.<br>• **Not profiled.** Measured baseline only: p50 unmeasured. Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Keep out of per-chart plans but expose completion to the per-chart readiness gate uniformly (the migration-563 class of bug, made structural).<br>• Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it. |

#### `bg_vastu_directions` — G · Global substrate · P3 · Standard · CURRENT

**What:** Classical Vastu Shastra direction–graha associations: 8 compass directions each mapped to a ruling graha, secondary graha, element, favorable color, and classic  
**Now:** global · lit · 32 rows / floor 32

**domain:** shared · **rung:** R0 · **within-rung wave:** 0 · **continuation class:** restartable-light · **rehearsal partition:** `n/a — single-shot, whole-asset is the unit` · **timeout source:** registered *(10800s differs from the column default (600s))*


**§19 efficiency ledger** · **p50:** null · **p90:** null · **worst:** null · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count = expected volume formula AND no duplicate natural keys`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8). |
| Rebuild time | • Built once, reused by every chart. Publish `substrate_version` + output digest; per-chart consumers record the version they read, so a no-op rebuild here never cascades.<br>• **Not profiled.** Measured baseline only: p50 unmeasured. Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Keep out of per-chart plans but expose completion to the per-chart readiness gate uniformly (the migration-563 class of bug, made structural).<br>• Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it. |

#### `bg_vedha_malefic_scale` — G · Global substrate · P3 · Standard · CURRENT

**What:** ADJUDICATION-11 Part 4: Phaladeepika Adh  
**Now:** global · lit · 5 rows / floor 5

**domain:** shared · **rung:** R0 · **within-rung wave:** 0 · **continuation class:** restartable-light · **rehearsal partition:** `n/a — single-shot, whole-asset is the unit` · **timeout source:** registered *(60s differs from the column default (600s))*


**§19 efficiency ledger** · **p50:** null · **p90:** null · **worst:** null · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count = expected volume formula AND no duplicate natural keys`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8). |
| Rebuild time | • Built once, reused by every chart. Publish `substrate_version` + output digest; per-chart consumers record the version they read, so a no-op rebuild here never cascades.<br>• **Not profiled.** Measured baseline only: p50 unmeasured. Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Keep out of per-chart plans but expose completion to the per-chart readiness gate uniformly (the migration-563 class of bug, made structural).<br>• Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 1 direct dependant(s) stop invalidating when this asset rebuilds to identical content. |

#### `bg_yogas` — G · Global substrate · P3 · Standard · CURRENT

**What:** Classical yoga definitions — formation rules, significations, classical citations  
**Now:** global · lit · 691 rows / floor 250

**domain:** shared · **rung:** R0 · **within-rung wave:** 1 · **continuation class:** restartable-light · **rehearsal partition:** `n/a — single-shot, whole-asset is the unit` · **timeout source:** registered *(10800s differs from the column default (600s))*


**§19 efficiency ledger** · **p50:** null · **p90:** null · **worst:** null · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count = expected volume formula AND no duplicate natural keys`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8). |
| Rebuild time | • Built once, reused by every chart. Publish `substrate_version` + output digest; per-chart consumers record the version they read, so a no-op rebuild here never cascades.<br>• **Not profiled.** Measured baseline only: p50 unmeasured. Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Keep out of per-chart plans but expose completion to the per-chart readiness gate uniformly (the migration-563 class of bug, made structural).<br>• Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it. |

### L1 · Gaṇita — 19 assets · 7 non-conformant · 1 P0 · 5 heavy

*Computed chart facts — the authority every higher layer references, never restates.* The authority layer: everything above references its fact ids. Content digests here have the highest leverage in the system — a no-op L1 rebuild currently invalidates the entire DAG above it. Several writers carry substep plans and none of them can resume.


#### `ga_vichara` — H · Heavy partitioned · P0 · Blocking defect · DRAFT

**What:** Judgment layer over ga_structural: functional-lordship valence pass, varga-ratification matrix + divergence signals, continuous varga-consistency index, and lev  
**Now:** native lit · abhinandan lit · chart3 lit · rows 8,249 / 8,247 / 8,240 · median 30s, worst 36m · 25.7% of 70 attempts complete

**domain:** chart · **rung:** R1 · **within-rung wave:** 0 · **continuation class:** resumable-substep · **rehearsal partition:** `ayanamsha_{a}` · **timeout source:** registered *(10800s differs from the column default (600s))*


**§19 efficiency ledger** · **p50:** 30s · **p90:** 15m · **worst:** 36m · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8). |
| Rebuild time | • No resume today — a 36m run is lost entirely on interruption. Adopt the shared `ResumableWriter` mixin (Phase 4) so committed substeps survive.<br>• Partition key `ayanamsha_{a}`: record the digest of the inputs each partition consumed. A rule/config change then re-runs only the partitions that read it.<br>• Persist the substep plan total at plan time so progress has a real denominator and the watchdog a true liveness signal.<br>• Only 25.7% of 70 attempts complete — most wall-clock is human re-dispatch. Error taxonomy + retry (Phase 4) is the fix, not faster code.<br>• **Not profiled.** Measured baseline only: p50 30s · p90 15m · worst 36m · 70 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 names this among the ten heavy assets where the efficiency pass concentrates. |
| Re-architecture & alignment | • Layer position: set `layer_index = L1`, derive `layer_name` from the locked lexicon (Phase 0.5a).<br>• Promote to CURRENT or record why it remains DRAFT (Phase 0.8b) — it is built and read by 10 serving surface(s), so it is authoritative in practice. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 1 direct dependant(s) stop invalidating when this asset rebuilds to identical content.<br>• Interruption stops costing up to 36m of committed work.<br>• Completion rate rises from 25.7% as transient failures self-heal. |

#### `ga_dashas` — H · Heavy partitioned · P1 · High · CURRENT

**What:** Vimshottari dasha timeline: MD × AD × PD rows per ayanamsha  
**Now:** native lit · abhinandan lit · chart3 incomplete · rows 483,859 / 471,767 / 505,348 (floor 536,471) · median 10m, worst 89m · 46.3% of 121 attempts complete

**domain:** chart · **rung:** R1 · **within-rung wave:** 1 · **continuation class:** resumable-substep · **rehearsal partition:** `{system}:{aya}` · **timeout source:** registered *(10800s differs from the column default (600s))*


**§19 efficiency ledger** · **p50:** 10m · **p90:** 48m · **worst:** 89m · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• Below floor: 483,859 of 536,471 (90%). Either the floor is stale (re-measure and reset) or the build is incomplete — decide explicitly, never let the gap sit. |
| Rebuild time | • No resume today — a 89m run is lost entirely on interruption. Adopt the shared `ResumableWriter` mixin (Phase 4) so committed substeps survive.<br>• Partition key `{system}:{aya}`: record the digest of the inputs each partition consumed. A rule/config change then re-runs only the partitions that read it.<br>• Persist the substep plan total at plan time so progress has a real denominator and the watchdog a true liveness signal.<br>• Watchdog: the `NOW()` heartbeat defect reaps long substeps; switch to `clock_timestamp()` before the next full rebuild (Phase 2). Classify transient failures for auto-retry — 46.3% completion today.<br>• Fan-out 13: content addressing pays back most here — today any rebuild of this asset, even a no-op, invalidates all 13 dependants.<br>• Only 46.3% of 121 attempts complete — most wall-clock is human re-dispatch. Error taxonomy + retry (Phase 4) is the fix, not faster code.<br>• **Not profiled.** Measured baseline only: p50 10m · p90 48m · worst 89m · 121 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 names this among the ten heavy assets where the efficiency pass concentrates. |
| Re-architecture & alignment | • Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 13 direct dependant(s) stop invalidating when this asset rebuilds to identical content.<br>• Interruption stops costing up to 89m of committed work.<br>• Completion rate rises from 46.3% as transient failures self-heal. |

#### `ga_positions` — M · Medium deterministic · P1 · High · CURRENT

**What:** Natal graha positions per ayanamsha (sidereal/tropical longitude, sign, nakshatra)  
**Now:** native lit · abhinandan lit · chart3 lit · rows 890 / 890 / 890 (floor 50) · median 4s, p90 58s (recorded worst 406.1h is an unclosed-run artefact — D-13) · 81.8% of 66 attempts complete

**domain:** chart · **rung:** R1 · **within-rung wave:** 0 · **continuation class:** restartable-light · **rehearsal partition:** `n/a — single-shot, whole-asset is the unit` · **timeout source:** registered *(10800s differs from the column default (600s))*


**§19 efficiency ledger** · **p50:** 4s · **p90:** 58s · **worst:** 406.1h · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it. p50/p90 read from telemetry flagged POLLUTED (D-13, unclosed run rows).*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `exactly one row per (chart_id, fact_key) across build_ids; verification_pass_status populated`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• Verification tier: 80.7% of native chart_facts are `single` (unverified). Add a second derivation path for this writer's fact categories so rows earn `two_pass_verified`; emit tiers only via `verification_vocab` constants.<br>• Accretion guard: 15 fact_keys already exist under two build_ids on the native chart. Make the delete-then-insert scope (chart_id × this writer's fact_keys) explicit and assert single-row-per-key in the integrity check. |
| Rebuild time | • Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• Fan-out 30: content addressing pays back most here — today any rebuild of this asset, even a no-op, invalidates all 30 dependants.<br>• **Not profiled.** Measured baseline only: p50 4s · p90 58s · recorded worst 406.1h is a D-13 unclosed-run artefact · 66 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • `chart_facts` has 5 co-writers: declare this writer's natural-key partition in the registry so the (table × generation × partition) uniqueness invariant is checkable (§3.3).<br>• Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 30 direct dependant(s) stop invalidating when this asset rebuilds to identical content.<br>• Facts move from `single` toward `two_pass_verified`; downstream narration inherits a verified base. |

#### `ga_sade_sati` — M · Medium deterministic · P1 · High · CURRENT

**What:** Saturn transit-over-natal-Moon Sade Sati + Dhaiya window calculations per ayanamsha  
**Now:** native lit · abhinandan lit · chart3 lit · rows 6,287 / 6,280 / 6,120 (floor 11,019) · median 71s, p90 9m (recorded worst 105.2h is an unclosed-run artefact — D-13) · 40.2% of 127 attempts complete

**domain:** chart · **rung:** R1 · **within-rung wave:** 4 · **continuation class:** restartable-light · **rehearsal partition:** `n/a — single-shot, whole-asset is the unit` · **timeout source:** registered *(10800s differs from the column default (600s))*


**§19 efficiency ledger** · **p50:** 71s · **p90:** 9m · **worst:** 105.2h · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it. p50/p90 read from telemetry flagged POLLUTED (D-13, unclosed run rows).*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• Below floor: 6,287 of 11,019 (57%). Either the floor is stale (re-measure and reset) or the build is incomplete — decide explicitly, never let the gap sit. |
| Rebuild time | • Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• Only 40.2% of 127 attempts complete — most wall-clock is human re-dispatch. Error taxonomy + retry (Phase 4) is the fix, not faster code.<br>• **Not profiled.** Measured baseline only: p50 71s · p90 9m · recorded worst 105.2h is a D-13 unclosed-run artefact · 127 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Declare `target_table` (or `clear_tables` if it writes several) so clear/rebuild and size reporting stop guessing from `count_sql`.<br>• Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 1 direct dependant(s) stop invalidating when this asset rebuilds to identical content.<br>• Completion rate rises from 40.2% as transient failures self-heal. |

#### `ga_sensitive` — H · Heavy partitioned · P1 · High · CURRENT

**What:** Per-chart sensitive point positions computed from the catalog × ayanamshas  
**Now:** native lit · abhinandan lit · chart3 lit · rows 8,565 / 8,565 / 8,565 (floor 8,610) · median 4m, worst 6.4h · 61.6% of 73 attempts complete

**domain:** chart · **rung:** R1 · **within-rung wave:** 1 · **continuation class:** resumable-substep · **rehearsal partition:** `ayanamsha:{aya}` · **timeout source:** registered *(10800s differs from the column default (600s))*


**§19 efficiency ledger** · **p50:** 4m · **p90:** 31m · **worst:** 6.4h · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• Below floor: 8,565 of 8,610 (99%). Either the floor is stale (re-measure and reset) or the build is incomplete — decide explicitly, never let the gap sit. |
| Rebuild time | • No resume today — a 6.4h run is lost entirely on interruption. Adopt the shared `ResumableWriter` mixin (Phase 4) so committed substeps survive.<br>• Partition key `ayanamsha:{aya}`: record the digest of the inputs each partition consumed. A rule/config change then re-runs only the partitions that read it.<br>• Persist the substep plan total at plan time so progress has a real denominator and the watchdog a true liveness signal.<br>• Watchdog: the `NOW()` heartbeat defect reaps long substeps; switch to `clock_timestamp()` before the next full rebuild (Phase 2). Classify transient failures for auto-retry — 61.6% completion today.<br>• **Not profiled.** Measured baseline only: p50 4m · p90 31m · worst 6.4h · 73 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 names this among the ten heavy assets where the efficiency pass concentrates. |
| Re-architecture & alignment | • Declare `target_table` (or `clear_tables` if it writes several) so clear/rebuild and size reporting stop guessing from `count_sql`.<br>• Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 4 direct dependant(s) stop invalidating when this asset rebuilds to identical content.<br>• Interruption stops costing up to 6.4h of committed work. |

#### `ga_strength` — H · Heavy partitioned · P1 · High · CURRENT

**What:** Shadbala, ashtakavarga, and bhava bala per ayanamsha  
**Now:** native lit · abhinandan lit · chart3 lit · rows 13,621 / 13,621 / 13,621 (floor 11,936) · median 2m, worst 13.1h · 65.3% of 75 attempts complete

**domain:** chart · **rung:** R1 · **within-rung wave:** 2 · **continuation class:** restartable-light · **rehearsal partition:** `n/a — single-shot, whole-asset is the unit` · **timeout source:** registered *(10800s differs from the column default (600s))*


**§19 efficiency ledger** · **p50:** 2m · **p90:** 5m · **worst:** 13.1h · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8). |
| Rebuild time | • Single-shot writer (no substep plan) with p90 5m: add a `plan_substeps` partition by ayanamsha so it becomes resumable and receipt-bearing; until then any interruption is a total loss.<br>• Watchdog: the `NOW()` heartbeat defect reaps long substeps; switch to `clock_timestamp()` before the next full rebuild (Phase 2). Classify transient failures for auto-retry — 65.3% completion today.<br>• Fan-out 5: content addressing pays back most here — today any rebuild of this asset, even a no-op, invalidates all 5 dependants.<br>• **Not profiled.** Measured baseline only: p50 2m · p90 5m · worst 13.1h · 75 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 names this among the ten heavy assets where the efficiency pass concentrates. |
| Re-architecture & alignment | • Declare `target_table` (or `clear_tables` if it writes several) so clear/rebuild and size reporting stop guessing from `count_sql`.<br>• Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 5 direct dependant(s) stop invalidating when this asset rebuilds to identical content.<br>• Interruption stops costing up to 13.1h of committed work. |

#### `ga_panchanga` — M · Medium deterministic · P2 · Medium · CURRENT

**What:** Natal panchanga (tithi, vara, nakshatra, yoga, karana) per ayanamsha  
**Now:** native lit · abhinandan lit · chart3 lit · rows 437 / 417 / 415 (floor 221) · median 3s, worst 56s · 74.6% of 67 attempts complete

**domain:** chart · **rung:** R1 · **within-rung wave:** 1 · **continuation class:** restartable-light · **rehearsal partition:** `n/a — single-shot, whole-asset is the unit` · **timeout source:** registered *(10800s differs from the column default (600s))*


**§19 efficiency ledger** · **p50:** 3s · **p90:** 43s · **worst:** 56s · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `exactly one row per (chart_id, fact_key) across build_ids; verification_pass_status populated`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• Verification tier: 80.7% of native chart_facts are `single` (unverified). Add a second derivation path for this writer's fact categories so rows earn `two_pass_verified`; emit tiers only via `verification_vocab` constants.<br>• Accretion guard: 15 fact_keys already exist under two build_ids on the native chart. Make the delete-then-insert scope (chart_id × this writer's fact_keys) explicit and assert single-row-per-key in the integrity check. |
| Rebuild time | • Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• Fan-out 5: content addressing pays back most here — today any rebuild of this asset, even a no-op, invalidates all 5 dependants.<br>• **Not profiled.** Measured baseline only: p50 3s · p90 43s · worst 56s · 67 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • `chart_facts` has 5 co-writers: declare this writer's natural-key partition in the registry so the (table × generation × partition) uniqueness invariant is checkable (§3.3).<br>• Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 5 direct dependant(s) stop invalidating when this asset rebuilds to identical content.<br>• Facts move from `single` toward `two_pass_verified`; downstream narration inherits a verified base. |

#### `ga_structural` — M · Medium deterministic · P2 · Medium · CURRENT

**What:** GA8 T1 structural layer: aspects (Parāśarī + Jaimini + Tājik), yogas, doshas, graha avasthās, argala/virodha-argala, dispositor chains, composite states, kāraka  
**Now:** native lit · abhinandan lit · chart3 lit · rows 98,542 / 98,662 / 98,446 (floor 77,821) · median 2m, worst 38m · 40.6% of 128 attempts complete

**domain:** chart · **rung:** R1 · **within-rung wave:** 3 · **continuation class:** resumable-substep · **rehearsal partition:** `ayanamsha_{id}` · **timeout source:** registered *(10800s differs from the column default (600s))*


**§19 efficiency ledger** · **p50:** 2m · **p90:** 3m · **worst:** 38m · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8). |
| Rebuild time | • Has a substep plan (`ayanamsha_{id}`) but runs in 2m — resumption is irrelevant here; per-substep input digests still matter because they give partition-scoped early cutoff downstream.<br>• Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• Fan-out 6: content addressing pays back most here — today any rebuild of this asset, even a no-op, invalidates all 6 dependants.<br>• Only 40.6% of 128 attempts complete — most wall-clock is human re-dispatch. Error taxonomy + retry (Phase 4) is the fix, not faster code.<br>• **Not profiled.** Measured baseline only: p50 2m · p90 3m · worst 38m · 128 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Declare `target_table` (or `clear_tables` if it writes several) so clear/rebuild and size reporting stop guessing from `count_sql`.<br>• Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 6 direct dependant(s) stop invalidating when this asset rebuilds to identical content.<br>• Completion rate rises from 40.6% as transient failures self-heal. |

#### `ga_vargas` — H · Heavy partitioned · P2 · Medium · CURRENT

**What:** D1–D60 divisional chart positions per ayanamsha  
**Now:** native lit · abhinandan lit · chart3 lit · rows 23,542 / 23,542 / 23,542 (floor 22,092) · median 2m, worst 59m · 69.6% of 69 attempts complete

**domain:** chart · **rung:** R1 · **within-rung wave:** 1 · **continuation class:** resumable-substep · **rehearsal partition:** `ayanamsha` · **timeout source:** registered *(10800s differs from the column default (600s))*


**§19 efficiency ledger** · **p50:** 2m · **p90:** 10m · **worst:** 59m · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8). |
| Rebuild time | • No resume today — a 59m run is lost entirely on interruption. Adopt the shared `ResumableWriter` mixin (Phase 4) so committed substeps survive.<br>• Partition key `ayanamsha`: record the digest of the inputs each partition consumed. A rule/config change then re-runs only the partitions that read it.<br>• Persist the substep plan total at plan time so progress has a real denominator and the watchdog a true liveness signal.<br>• Fan-out 6: content addressing pays back most here — today any rebuild of this asset, even a no-op, invalidates all 6 dependants.<br>• **Not profiled.** Measured baseline only: p50 2m · p90 10m · worst 59m · 69 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 names this among the ten heavy assets where the efficiency pass concentrates. |
| Re-architecture & alignment | • Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 6 direct dependant(s) stop invalidating when this asset rebuilds to identical content.<br>• Interruption stops costing up to 59m of committed work. |

#### `ga_ayurdaya` — M · Medium deterministic · P3 · Standard · CURRENT

**What:** Ayurdaya / longevity (LCA-16): ALL THREE classical methods (Pindayu, Nisargayu, Amsayu) method-attributed, with the classical applicability rule served alongsid  
**Now:** native lit · abhinandan lit · chart3 lit · rows 130 / 130 / 130 · median 4s, worst 19s · 59.1% of 22 attempts complete

**domain:** chart · **rung:** R1 · **within-rung wave:** 0 · **continuation class:** resumable-substep · **rehearsal partition:** `ayanamsha_{aya}` · **timeout source:** registered *(10800s differs from the column default (600s))*


**§19 efficiency ledger** · **p50:** 4s · **p90:** 18s · **worst:** 19s · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `exactly one row per (chart_id, fact_key) across build_ids; verification_pass_status populated`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• Verification tier: 80.7% of native chart_facts are `single` (unverified). Add a second derivation path for this writer's fact categories so rows earn `two_pass_verified`; emit tiers only via `verification_vocab` constants.<br>• Accretion guard: 15 fact_keys already exist under two build_ids on the native chart. Make the delete-then-insert scope (chart_id × this writer's fact_keys) explicit and assert single-row-per-key in the integrity check. |
| Rebuild time | • Has a substep plan (`ayanamsha_{aya}`) but runs in 4s — resumption is irrelevant here; per-substep input digests still matter because they give partition-scoped early cutoff downstream.<br>• Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• **Not profiled.** Measured baseline only: p50 4s · p90 18s · worst 19s · 22 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Layer position: set `layer_index = L1`, derive `layer_name` from the locked lexicon (Phase 0.5a).<br>• `chart_facts` has 5 co-writers: declare this writer's natural-key partition in the registry so the (table × generation × partition) uniqueness invariant is checkable (§3.3).<br>• Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• Facts move from `single` toward `two_pass_verified`; downstream narration inherits a verified base. |

#### `ga_condition` — M · Medium deterministic · P3 · Standard · CURRENT

**What:** Unified dignity, avastha (baladi/jagradadi/deeptaadi/lajjitaadi/sayanadi), motion state, combustion, naisargika/tatkalika/panchadha friendship, graha yuddha, an  
**Now:** native lit · abhinandan lit · chart3 lit · rows 2,880 / 2,895 / 2,880 (floor 2,880) · median 29s, worst 5m · 50.5% of 101 attempts complete

**domain:** chart · **rung:** R1 · **within-rung wave:** 2 · **continuation class:** resumable-substep · **rehearsal partition:** `ayanamsha_{id}` · **timeout source:** registered *(10800s differs from the column default (600s))*


**§19 efficiency ledger** · **p50:** 29s · **p90:** 4m · **worst:** 5m · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8). |
| Rebuild time | • Has a substep plan (`ayanamsha_{id}`) but runs in 29s — resumption is irrelevant here; per-substep input digests still matter because they give partition-scoped early cutoff downstream.<br>• Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• **Not profiled.** Measured baseline only: p50 29s · p90 4m · worst 5m · 101 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 4 direct dependant(s) stop invalidating when this asset rebuilds to identical content. |

#### `ga_medical` — M · Medium deterministic · P3 · Standard · CURRENT

**What:** Per-chart Ayurvedic Jyotish indication summary: dosha aggravation, organ watch, body-part watch, and indication_strength derived from ga_condition condition_sco  
**Now:** native lit · abhinandan lit · chart3 lit · rows 45 / 45 / 45 (floor 45) · median 1s, worst 10s · 66.7% of 75 attempts complete

**domain:** chart · **rung:** R1 · **within-rung wave:** 3 · **continuation class:** resumable-substep · **rehearsal partition:** `ayanamsha_{aya}` · **timeout source:** registered *(10800s differs from the column default (600s))*


**§19 efficiency ledger** · **p50:** 1s · **p90:** 7s · **worst:** 10s · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8). |
| Rebuild time | • Has a substep plan (`ayanamsha_{aya}`) but runs in 1s — resumption is irrelevant here; per-substep input digests still matter because they give partition-scoped early cutoff downstream.<br>• Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• **Not profiled.** Measured baseline only: p50 1s · p90 7s · worst 10s · 75 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it. |

#### `ga_nakshatra` — M · Medium deterministic · P3 · Standard · CURRENT

**What:** Per-chart parallel nakshatra chart: placement+attribute JOIN from bg_nakshatra, KP sub-lords (star/sub/sub-sub/prana) per body and house cusp, the 4-limbed KP s  
**Now:** native lit · abhinandan lit · chart3 lit · rows 2,847 / 2,858 / 1,813 (floor 1,802) · median 14s, worst 7m · 72.7% of 66 attempts complete

**domain:** chart · **rung:** R1 · **within-rung wave:** 1 · **continuation class:** resumable-substep · **rehearsal partition:** `ayanamsha:{ay} + cross_ayanamsha` · **timeout source:** registered *(10800s differs from the column default (600s))*


**§19 efficiency ledger** · **p50:** 14s · **p90:** 3m · **worst:** 7m · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `exactly one row per (chart_id, fact_key) across build_ids; verification_pass_status populated`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• Verification tier: 80.7% of native chart_facts are `single` (unverified). Add a second derivation path for this writer's fact categories so rows earn `two_pass_verified`; emit tiers only via `verification_vocab` constants.<br>• Accretion guard: 15 fact_keys already exist under two build_ids on the native chart. Make the delete-then-insert scope (chart_id × this writer's fact_keys) explicit and assert single-row-per-key in the integrity check. |
| Rebuild time | • Has a substep plan (`ayanamsha:{ay} + cross_ayanamsha`) but runs in 14s — resumption is irrelevant here; per-substep input digests still matter because they give partition-scoped early cutoff downstream.<br>• Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• **Not profiled.** Measured baseline only: p50 14s · p90 3m · worst 7m · 66 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • `chart_facts` has 5 co-writers: declare this writer's natural-key partition in the registry so the (table × generation × partition) uniqueness invariant is checkable (§3.3).<br>• Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 4 direct dependant(s) stop invalidating when this asset rebuilds to identical content.<br>• Facts move from `single` toward `two_pass_verified`; downstream narration inherits a verified base. |

#### `ga_prashna` — M · Medium deterministic · P3 · Standard · CURRENT

**What:** Per-prashna-chart horary judgment: Prashna-Lagna by each method, querent/quesited significators, Tajik Ithasala/Eesarpha analysis, and fructification timing  
**Now:** native lit · abhinandan lit · chart3 lit · rows 0 / 0 / 0 · median 1s, worst 6s · 77.0% of 61 attempts complete

**domain:** chart · **rung:** R1 · **within-rung wave:** 1 · **continuation class:** resumable-substep · **rehearsal partition:** `ayanamsha_{id}` · **timeout source:** registered *(10800s differs from the column default (600s))*


**§19 efficiency ledger** · **p50:** 1s · **p90:** 4s · **worst:** 6s · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• **Unearned `lit`:** throughput says lit on 3 chart(s) while the table holds zero rows — a live §N.8 specimen. The integrity gate (§4.1) must fail this; then decide: empty by design (record in `volume_explanation`, floor 0) or never built (rebuild). |
| Rebuild time | • Has a substep plan (`ayanamsha_{id}`) but runs in 1s — resumption is irrelevant here; per-substep input digests still matter because they give partition-scoped early cutoff downstream.<br>• Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• **Not profiled.** Measured baseline only: p50 1s · p90 4s · worst 6s · 61 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it. |

#### `ga_sensitive_degree` — M · Medium deterministic · P3 · Standard · CURRENT

**What:** Per-graha sensitive-degree facts (LCA-10): mrityu-bhaga, neecha-bhanga, kartari, sarvatobhadra-vedha, khareshwara (22nd drekkana + 64th navamsa), pushkara-bhaga  
**Now:** native lit · abhinandan lit · chart3 lit · rows 275 / 275 / 275 · median 22s, worst 56s · 60.0% of 25 attempts complete

**domain:** chart · **rung:** R1 · **within-rung wave:** 0 · **continuation class:** resumable-substep · **rehearsal partition:** `ayanamsha_{aya}` · **timeout source:** registered *(10800s differs from the column default (600s))*


**§19 efficiency ledger** · **p50:** 22s · **p90:** 44s · **worst:** 56s · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `exactly one row per (chart_id, fact_key) across build_ids; verification_pass_status populated`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• Verification tier: 80.7% of native chart_facts are `single` (unverified). Add a second derivation path for this writer's fact categories so rows earn `two_pass_verified`; emit tiers only via `verification_vocab` constants.<br>• Accretion guard: 15 fact_keys already exist under two build_ids on the native chart. Make the delete-then-insert scope (chart_id × this writer's fact_keys) explicit and assert single-row-per-key in the integrity check. |
| Rebuild time | • Has a substep plan (`ayanamsha_{aya}`) but runs in 22s — resumption is irrelevant here; per-substep input digests still matter because they give partition-scoped early cutoff downstream.<br>• Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• **Not profiled.** Measured baseline only: p50 22s · p90 44s · worst 56s · 25 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Layer position: set `layer_index = L1`, derive `layer_name` from the locked lexicon (Phase 0.5a).<br>• `chart_facts` has 5 co-writers: declare this writer's natural-key partition in the registry so the (table × generation × partition) uniqueness invariant is checkable (§3.3).<br>• Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• Facts move from `single` toward `two_pass_verified`; downstream narration inherits a verified base. |

#### `ga_tajaka` — M · Medium deterministic · P3 · Standard · CURRENT

**What:** Vārṣaphal annual chart per varsha (solar-return year): Muntha position, Vārṣeśa (year-lord) by tajik_classical + panchavargiya methods with candidate scoring, a  
**Now:** native lit · abhinandan lit · chart3 lit · rows 240 / 235 / 305 (floor 240) · median 14s, worst 54s · 63.4% of 82 attempts complete

**domain:** chart · **rung:** R1 · **within-rung wave:** 2 · **continuation class:** restartable-light · **rehearsal partition:** `n/a — single-shot, whole-asset is the unit` · **timeout source:** registered *(10800s differs from the column default (600s))*


**§19 efficiency ledger** · **p50:** 14s · **p90:** 34s · **worst:** 54s · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8). |
| Rebuild time | • Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• **Not profiled.** Measured baseline only: p50 14s · p90 34s · worst 54s · 82 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 1 direct dependant(s) stop invalidating when this asset rebuilds to identical content. |

#### `ga_transit_anchors` — M · Medium deterministic · P3 · Standard · CURRENT

**What:** Natal position anchors for Gochara (transit) analysis: stores each graha's natal sign, natal degree absolute, and house-from-Moon for each ayanamsha  
**Now:** native lit · abhinandan lit · chart3 lit · rows 45 / 45 / 45 (floor 45) · median 1s, worst 13s · 77.0% of 61 attempts complete

**domain:** chart · **rung:** R1 · **within-rung wave:** 1 · **continuation class:** resumable-substep · **rehearsal partition:** `ayanamsha_{aya}` · **timeout source:** registered *(10800s differs from the column default (600s))*


**§19 efficiency ledger** · **p50:** 1s · **p90:** 8s · **worst:** 13s · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8). |
| Rebuild time | • Has a substep plan (`ayanamsha_{aya}`) but runs in 1s — resumption is irrelevant here; per-substep input digests still matter because they give partition-scoped early cutoff downstream.<br>• Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• **Not profiled.** Measured baseline only: p50 1s · p90 8s · worst 13s · 61 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it. |

#### `ga_vastu` — M · Medium deterministic · P3 · Standard · CURRENT

**What:** Maps each classical graha to its ruling Vastu direction (per bg_vastu_directions) and computes direction_impact (weakened / neutral / strengthened) using condit  
**Now:** native lit · abhinandan lit · chart3 lit · rows 40 / 40 / 40 (floor 40) · median 1s, worst 14s · 66.7% of 75 attempts complete

**domain:** chart · **rung:** R1 · **within-rung wave:** 3 · **continuation class:** resumable-substep · **rehearsal partition:** `ayanamsha_{id}` · **timeout source:** registered *(10800s differs from the column default (600s))*


**§19 efficiency ledger** · **p50:** 1s · **p90:** 7s · **worst:** 14s · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8). |
| Rebuild time | • Has a substep plan (`ayanamsha_{id}`) but runs in 1s — resumption is irrelevant here; per-substep input digests still matter because they give partition-scoped early cutoff downstream.<br>• Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• **Not profiled.** Measured baseline only: p50 1s · p90 7s · worst 14s · 75 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it. |

#### `ga_yoga` — M · Medium deterministic · P3 · Standard · CURRENT

**What:** Per-chart yoga firing table: evaluates classical Nabhasa and other yoga formation rules against L1 chart_facts  
**Now:** native lit · abhinandan lit · chart3 lit · rows 63 / 69 / 80 (floor 5) · median 6s, worst 36m · 42.5% of 120 attempts complete

**domain:** chart · **rung:** R1 · **within-rung wave:** 4 · **continuation class:** resumable-substep · **rehearsal partition:** `ayanamsha_{a}` · **timeout source:** registered *(10800s differs from the column default (600s))*


**§19 efficiency ledger** · **p50:** 6s · **p90:** 22s · **worst:** 36m · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8). |
| Rebuild time | • Has a substep plan (`ayanamsha_{a}`) but runs in 6s — resumption is irrelevant here; per-substep input digests still matter because they give partition-scoped early cutoff downstream.<br>• Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• Only 42.5% of 120 attempts complete — most wall-clock is human re-dispatch. Error taxonomy + retry (Phase 4) is the fix, not faster code.<br>• **Not profiled.** Measured baseline only: p50 6s · p90 22s · worst 36m · 120 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 1 direct dependant(s) stop invalidating when this asset rebuilds to identical content.<br>• Completion rate rises from 42.5% as transient failures self-heal. |

### L2 · Bodha — 22 assets · 12 non-conformant · 11 P0 · 3 heavy

*Derivation & synthesis — signals, mechanisms, contradictions, gestalt.* Broad, shallow and cheap per asset, but deep in fan-out. The win is early cutoff: most L2 rebuilds produce identical rows and should stop propagating. Three writers here have their completeness gate silently disabled.


#### `bo_arudha` — M · Medium deterministic · P0 · Blocking defect · DRAFT

**What:** Arudha Lagna bhava-relation, AL conjunctions, and A2/A11 (dhana/labha arudha) tenancy — pure L2 derivation over existing ga_structural/ga_positions facts; emits  
**Now:** native lit · abhinandan lit · chart3 lit · rows 25 / 24 / 20 (floor 15) · median 1s, worst 8s · 68.4% of 19 attempts complete

**domain:** chart · **rung:** R2 · **within-rung wave:** 0 · **continuation class:** restartable-light · **rehearsal partition:** `n/a — single-shot, whole-asset is the unit` · **timeout source:** default *(600s equals the asset_registry column default and the runner fallback (_WRITER_TIMEOUT_SECONDS) — indistinguishable from never set)*


**§19 efficiency ledger** · **p50:** 1s · **p90:** 7s · **worst:** 8s · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `every constituent_facts_array id resolves to chart_facts.fact_id (§N.5); one row per signal_id per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• §N.5: every signal must reference L1 `fact_id`s, never restate values — keep the constituent-facts resolution check (100% on sample today) as a blocking integrity gate. Declare this writer's natural-key partition of the shared table so co-writers cannot overwrite each other. |
| Rebuild time | • Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• **Not profiled.** Measured baseline only: p50 1s · p90 7s · worst 8s · 19 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Layer position: set `layer_index = L2`, derive `layer_name` from the locked lexicon (Phase 0.5a).<br>• Promote to CURRENT or record why it remains DRAFT (Phase 0.8b) — it is built and read by 36 serving surface(s), so it is authoritative in practice.<br>• `bodha_msr_signals` has 7 co-writers: declare this writer's natural-key partition in the registry so the (table × generation × partition) uniqueness invariant is checkable (§3.3). |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it. |

#### `bo_cdlm_summary` — M · Medium deterministic · P0 · Blocking defect · DRAFT

**What:** Per-chart cross-domain linkage strength summary aggregated from bodha_cdlm_cells  
**Now:** native lit · abhinandan lit · chart3 stale · rows 5 / 5 / 5 (floor 1) · median 1s, worst 17s · 53.1% of 81 attempts complete

**domain:** chart · **rung:** R2 · **within-rung wave:** 0 · **continuation class:** restartable-light · **rehearsal partition:** `n/a — single-shot, whole-asset is the unit` · **timeout source:** registered *(10800s differs from the column default (600s))*


**§19 efficiency ledger** · **p50:** 1s · **p90:** 10s · **worst:** 17s · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• §N.7 narration fidelity: every sentence restates a cited fact_id it reads, never re-derives; add a golden-value test for the narration layer (verified fact ≠ verified prose). |
| Rebuild time | • Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• **Not profiled.** Measured baseline only: p50 1s · p90 10s · worst 17s · 81 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Layer position: set `layer_index = L2`, derive `layer_name` from the locked lexicon (Phase 0.5a).<br>• Declare `target_table` (or `clear_tables` if it writes several) so clear/rebuild and size reporting stop guessing from `count_sql`. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it. |

#### `bo_cgm_motifs` — M · Medium deterministic · P0 · Blocking defect · CURRENT

**What:** Recurring structural patterns detected over the CGM graph: mutual reception, stellium, parivartana chains  
**Now:** native lit · abhinandan lit · chart3 stale · rows 600 / 606 / 605 · median 3s, worst 2m · 37.4% of 123 attempts complete

**domain:** chart · **rung:** R2 · **within-rung wave:** 0 · **continuation class:** restartable-light · **rehearsal partition:** `n/a — single-shot, whole-asset is the unit` · **timeout source:** registered *(10800s differs from the column default (600s))*


**§19 efficiency ledger** · **p50:** 3s · **p90:** 66s · **worst:** 2m · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8). |
| Rebuild time | • Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• Only 37.4% of 123 attempts complete — most wall-clock is human re-dispatch. Error taxonomy + retry (Phase 4) is the fix, not faster code.<br>• **Not profiled.** Measured baseline only: p50 3s · p90 66s · worst 2m · 123 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Layer position: set `layer_index = L2`, derive `layer_name` from the locked lexicon (Phase 0.5a).<br>• Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 2 direct dependant(s) stop invalidating when this asset rebuilds to identical content.<br>• Completion rate rises from 37.4% as transient failures self-heal. |

#### `bo_cgm_paths` — M · Medium deterministic · P0 · Blocking defect · CURRENT

**What:** Dispositor chain paths and structural path analysis over CGM graph  
**Now:** native lit · abhinandan lit · chart3 stale · rows 45 / 45 / 45 (floor 9) · median 2s, worst 20m · 56.2% of 80 attempts complete

**domain:** chart · **rung:** R2 · **within-rung wave:** 0 · **continuation class:** restartable-light · **rehearsal partition:** `n/a — single-shot, whole-asset is the unit` · **timeout source:** registered *(10800s differs from the column default (600s))*


**§19 efficiency ledger** · **p50:** 2s · **p90:** 10s · **worst:** 20m · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8). |
| Rebuild time | • Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• **Not profiled.** Measured baseline only: p50 2s · p90 10s · worst 20m · 80 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Layer position: set `layer_index = L2`, derive `layer_name` from the locked lexicon (Phase 0.5a).<br>• Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 3 direct dependant(s) stop invalidating when this asset rebuilds to identical content. |

#### `bo_chart_gestalt` — M · Medium deterministic · P0 · Blocking defect · DRAFT

**What:** Per-chart gestalt: defining threads, central dynamics, domain verdict map, zoom spine — pointer-only, no verdicts stored  
**Now:** native lit · abhinandan lit · chart3 stale · rows 5 / 5 / 5 (floor 1) · median 2s, worst 53s · 40.0% of 95 attempts complete

**domain:** chart · **rung:** R2 · **within-rung wave:** 0 · **continuation class:** restartable-light · **rehearsal partition:** `n/a — single-shot, whole-asset is the unit` · **timeout source:** registered *(10800s differs from the column default (600s))*


**§19 efficiency ledger** · **p50:** 2s · **p90:** 9s · **worst:** 53s · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• §N.7 narration fidelity: every sentence restates a cited fact_id it reads, never re-derives; add a golden-value test for the narration layer (verified fact ≠ verified prose). |
| Rebuild time | • Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• Only 40.0% of 95 attempts complete — most wall-clock is human re-dispatch. Error taxonomy + retry (Phase 4) is the fix, not faster code.<br>• DAG depth 12: sits in the serial tail. Audit its 5 declared edges for ones never actually read (Phase 5) — every removed edge is pure wall-clock.<br>• **Not profiled.** Measured baseline only: p50 2s · p90 9s · worst 53s · 95 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Layer position: set `layer_index = L2`, derive `layer_name` from the locked lexicon (Phase 0.5a).<br>• Declare `target_table` (or `clear_tables` if it writes several) so clear/rebuild and size reporting stop guessing from `count_sql`. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• Completion rate rises from 40.0% as transient failures self-heal. |

#### `bo_laksana_rerank` — H · Heavy partitioned · P0 · Blocking defect · DRAFT

**What:** Post-CGM structural re-rank pass: writes real CGM centrality (pagerank/eigenvector/betweenness/harmonic) onto each MSR signal's graph_node_strength_contribution  
**Now:** native lit · abhinandan lit · chart3 stale · rows 10,824 / 10,868 / 100 (floor 1) · median 4m, worst 21m · 63.6% of 22 attempts complete

**domain:** chart · **rung:** R2 · **within-rung wave:** 0 · **continuation class:** resumable-substep · **rehearsal partition:** `aya_{ayanamsha}` · **timeout source:** default *(600s equals the asset_registry column default and the runner fallback (_WRITER_TIMEOUT_SECONDS) — indistinguishable from never set)*


**§19 efficiency ledger** · **p50:** 4m · **p90:** 20m · **worst:** 21m · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `every constituent_facts_array id resolves to chart_facts.fact_id (§N.5); one row per signal_id per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• §N.5: every signal must reference L1 `fact_id`s, never restate values — keep the constituent-facts resolution check (100% on sample today) as a blocking integrity gate. Declare this writer's natural-key partition of the shared table so co-writers cannot overwrite each other. |
| Rebuild time | • No resume today — a 21m run is lost entirely on interruption. Adopt the shared `ResumableWriter` mixin (Phase 4) so committed substeps survive.<br>• Partition key `aya_{ayanamsha}`: record the digest of the inputs each partition consumed. A rule/config change then re-runs only the partitions that read it.<br>• Persist the substep plan total at plan time so progress has a real denominator and the watchdog a true liveness signal.<br>• **Not profiled.** Measured baseline only: p50 4m · p90 20m · worst 21m · 22 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 names this among the ten heavy assets where the efficiency pass concentrates. |
| Re-architecture & alignment | • `has_substeps` is false in the registry while the writer plans substeps: derive the flag from the writer class (Phase 0.6a). Until then the §N.8 completeness gate is silently disabled for this asset.<br>• Layer position: set `layer_index = L2`, derive `layer_name` from the locked lexicon (Phase 0.5a).<br>• Promote to CURRENT or record why it remains DRAFT (Phase 0.8b) — it is built and read by 36 serving surface(s), so it is authoritative in practice.<br>• `bodha_msr_signals` has 7 co-writers: declare this writer's natural-key partition in the registry so the (table × generation × partition) uniqueness invariant is checkable (§3.3). |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• Interruption stops costing up to 21m of committed work.<br>• A partial build can no longer be promoted to green. |

#### `bo_nakshatra_semantic` — M · Medium deterministic · P0 · Blocking defect · DRAFT

**What:** Own-star identity, dispositor chain, tara bala, and gandanta/end-degree flagging per graha — pure L2 derivation over existing ga_positions/ga_nakshatra facts; e  
**Now:** native lit · abhinandan lit · chart3 lit · rows 45 / 45 / 45 (floor 45) · median 1s, worst 12s · 82.4% of 17 attempts complete

**domain:** chart · **rung:** R2 · **within-rung wave:** 0 · **continuation class:** restartable-light · **rehearsal partition:** `n/a — single-shot, whole-asset is the unit` · **timeout source:** default *(600s equals the asset_registry column default and the runner fallback (_WRITER_TIMEOUT_SECONDS) — indistinguishable from never set)*


**§19 efficiency ledger** · **p50:** 1s · **p90:** 10s · **worst:** 12s · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `every constituent_facts_array id resolves to chart_facts.fact_id (§N.5); one row per signal_id per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• §N.5: every signal must reference L1 `fact_id`s, never restate values — keep the constituent-facts resolution check (100% on sample today) as a blocking integrity gate. Declare this writer's natural-key partition of the shared table so co-writers cannot overwrite each other. |
| Rebuild time | • Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• **Not profiled.** Measured baseline only: p50 1s · p90 10s · worst 12s · 17 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Layer position: set `layer_index = L2`, derive `layer_name` from the locked lexicon (Phase 0.5a).<br>• Promote to CURRENT or record why it remains DRAFT (Phase 0.8b) — it is built and read by 36 serving surface(s), so it is authoritative in practice.<br>• `bodha_msr_signals` has 7 co-writers: declare this writer's natural-key partition in the registry so the (table × generation × partition) uniqueness invariant is checkable (§3.3). |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it. |

#### `bo_special_lagna` — M · Medium deterministic · P0 · Blocking defect · DRAFT

**What:** Domain-scoped corroboration from the four canonical special/upapada lagnas (Indu, Sree, Ghati, Hora) — pure L2 derivation over existing ga_sensitive facts; emit  
**Now:** native lit · abhinandan lit · chart3 lit · rows 20 / 20 / 20 (floor 20) · median 0s, worst 9s · 68.8% of 16 attempts complete

**domain:** chart · **rung:** R2 · **within-rung wave:** 0 · **continuation class:** restartable-light · **rehearsal partition:** `n/a — single-shot, whole-asset is the unit` · **timeout source:** default *(600s equals the asset_registry column default and the runner fallback (_WRITER_TIMEOUT_SECONDS) — indistinguishable from never set)*


**§19 efficiency ledger** · **p50:** 0s · **p90:** 4s · **worst:** 9s · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `every constituent_facts_array id resolves to chart_facts.fact_id (§N.5); one row per signal_id per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• §N.5: every signal must reference L1 `fact_id`s, never restate values — keep the constituent-facts resolution check (100% on sample today) as a blocking integrity gate. Declare this writer's natural-key partition of the shared table so co-writers cannot overwrite each other. |
| Rebuild time | • Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• **Not profiled.** Measured baseline only: p50 0s · p90 4s · worst 9s · 16 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Layer position: set `layer_index = L2`, derive `layer_name` from the locked lexicon (Phase 0.5a).<br>• Promote to CURRENT or record why it remains DRAFT (Phase 0.8b) — it is built and read by 36 serving surface(s), so it is authoritative in practice.<br>• `bodha_msr_signals` has 7 co-writers: declare this writer's natural-key partition in the registry so the (table × generation × partition) uniqueness invariant is checkable (§3.3). |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it. |

#### `bo_sudarshana` — M · Medium deterministic · P0 · Blocking defect · DRAFT

**What:** Tri-frame (Lagna/Chandra/Sūrya) house assignment per graha — pure L2 derivation over existing ga_positions facts; emits sudarshana_agreement MSR signals (confir  
**Now:** native lit · abhinandan lit · chart3 lit · rows 45 / 45 / 45 (floor 45) · median 1s, worst 10s · 78.6% of 14 attempts complete

**domain:** chart · **rung:** R2 · **within-rung wave:** 0 · **continuation class:** restartable-light · **rehearsal partition:** `n/a — single-shot, whole-asset is the unit` · **timeout source:** default *(600s equals the asset_registry column default and the runner fallback (_WRITER_TIMEOUT_SECONDS) — indistinguishable from never set)*


**§19 efficiency ledger** · **p50:** 1s · **p90:** 10s · **worst:** 10s · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `every constituent_facts_array id resolves to chart_facts.fact_id (§N.5); one row per signal_id per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• §N.5: every signal must reference L1 `fact_id`s, never restate values — keep the constituent-facts resolution check (100% on sample today) as a blocking integrity gate. Declare this writer's natural-key partition of the shared table so co-writers cannot overwrite each other. |
| Rebuild time | • Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• **Not profiled.** Measured baseline only: p50 1s · p90 10s · worst 10s · 14 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Layer position: set `layer_index = L2`, derive `layer_name` from the locked lexicon (Phase 0.5a).<br>• Promote to CURRENT or record why it remains DRAFT (Phase 0.8b) — it is built and read by 36 serving surface(s), so it is authoritative in practice.<br>• `bodha_msr_signals` has 7 co-writers: declare this writer's natural-key partition in the registry so the (table × generation × partition) uniqueness invariant is checkable (§3.3). |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it. |

#### `bo_vargottama_dhana` — M · Medium deterministic · P0 · Blocking defect · DRAFT

**What:** Cross-frame (D1/D9) vargottama confirmation and complete 2nd/11th-house (dhana/labha) tenancy analysis — pure L2 derivation over existing ga_vargas/ga_positions  
**Now:** native lit · abhinandan lit · chart3 lit · rows 14 / 16 / 15 (floor 10) · median 1s, worst 8s · 80.0% of 15 attempts complete

**domain:** chart · **rung:** R2 · **within-rung wave:** 0 · **continuation class:** restartable-light · **rehearsal partition:** `n/a — single-shot, whole-asset is the unit` · **timeout source:** default *(600s equals the asset_registry column default and the runner fallback (_WRITER_TIMEOUT_SECONDS) — indistinguishable from never set)*


**§19 efficiency ledger** · **p50:** 1s · **p90:** 7s · **worst:** 8s · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `every constituent_facts_array id resolves to chart_facts.fact_id (§N.5); one row per signal_id per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• §N.5: every signal must reference L1 `fact_id`s, never restate values — keep the constituent-facts resolution check (100% on sample today) as a blocking integrity gate. Declare this writer's natural-key partition of the shared table so co-writers cannot overwrite each other. |
| Rebuild time | • Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• **Not profiled.** Measured baseline only: p50 1s · p90 7s · worst 8s · 15 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Layer position: set `layer_index = L2`, derive `layer_name` from the locked lexicon (Phase 0.5a).<br>• Promote to CURRENT or record why it remains DRAFT (Phase 0.8b) — it is built and read by 36 serving surface(s), so it is authoritative in practice.<br>• `bodha_msr_signals` has 7 co-writers: declare this writer's natural-key partition in the registry so the (table × generation × partition) uniqueness invariant is checkable (§3.3). |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it. |

#### `bo_yantra_mechanism` — M · Medium deterministic · P0 · Blocking defect · DRAFT

**What:** Named, valenced CGM subgraph — promotes CGM motifs + dispositor/house-lordship chain-and-circuit detection into first-class mechanisms with real edge-strength p  
**Now:** native lit · abhinandan lit · chart3 stale · rows 615 / 633 / 620 (floor 1) · median 13s, worst 2m · 68.2% of 22 attempts complete

**domain:** chart · **rung:** R2 · **within-rung wave:** 0 · **continuation class:** restartable-light · **rehearsal partition:** `n/a — single-shot, whole-asset is the unit` · **timeout source:** default *(600s equals the asset_registry column default and the runner fallback (_WRITER_TIMEOUT_SECONDS) — indistinguishable from never set)*


**§19 efficiency ledger** · **p50:** 13s · **p90:** 2m · **worst:** 2m · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8). |
| Rebuild time | • Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• **Not profiled.** Measured baseline only: p50 13s · p90 2m · worst 2m · 22 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Layer position: set `layer_index = L2`, derive `layer_name` from the locked lexicon (Phase 0.5a).<br>• Promote to CURRENT or record why it remains DRAFT (Phase 0.8b) — it is built and read by 8 serving surface(s), so it is authoritative in practice. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it. |

#### `bo_laksana` — H · Heavy partitioned · P1 · High · CURRENT

**What:** MARSYS Signal Register — grounded signals derived from exhaustive L1 structural enumeration (ga_structural) × L1 chart_facts; primary table bodha_msr_signals  
**Now:** native lit · abhinandan lit · chart3 lit · rows 49,955 / 50,021 / 49,730 (floor 60,000) · median 3m, worst 19.2h · 41.2% of 136 attempts complete

**domain:** chart · **rung:** R2 · **within-rung wave:** 0 · **continuation class:** resumable-substep · **rehearsal partition:** `aya_{ayanamsha}` · **timeout source:** registered *(10800s differs from the column default (600s))*


**§19 efficiency ledger** · **p50:** 3m · **p90:** 21m · **worst:** 19.2h · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `every constituent_facts_array id resolves to chart_facts.fact_id (§N.5); one row per signal_id per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• Below floor: 49,955 of 60,000 (83%). Either the floor is stale (re-measure and reset) or the build is incomplete — decide explicitly, never let the gap sit.<br>• §N.5: every signal must reference L1 `fact_id`s, never restate values — keep the constituent-facts resolution check (100% on sample today) as a blocking integrity gate. Declare this writer's natural-key partition of the shared table so co-writers cannot overwrite each other. |
| Rebuild time | • No resume today — a 19.2h run is lost entirely on interruption. Adopt the shared `ResumableWriter` mixin (Phase 4) so committed substeps survive.<br>• Partition key `aya_{ayanamsha}`: record the digest of the inputs each partition consumed. A rule/config change then re-runs only the partitions that read it.<br>• Persist the substep plan total at plan time so progress has a real denominator and the watchdog a true liveness signal.<br>• Watchdog: the `NOW()` heartbeat defect reaps long substeps; switch to `clock_timestamp()` before the next full rebuild (Phase 2). Classify transient failures for auto-retry — 41.2% completion today.<br>• Fan-out 20: content addressing pays back most here — today any rebuild of this asset, even a no-op, invalidates all 20 dependants.<br>• Only 41.2% of 136 attempts complete — most wall-clock is human re-dispatch. Error taxonomy + retry (Phase 4) is the fix, not faster code.<br>• **Not profiled.** Measured baseline only: p50 3m · p90 21m · worst 19.2h · 136 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 names this among the ten heavy assets where the efficiency pass concentrates. |
| Re-architecture & alignment | • `bodha_msr_signals` has 7 co-writers: declare this writer's natural-key partition in the registry so the (table × generation × partition) uniqueness invariant is checkable (§3.3).<br>• Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 20 direct dependant(s) stop invalidating when this asset rebuilds to identical content.<br>• Interruption stops costing up to 19.2h of committed work.<br>• Completion rate rises from 41.2% as transient failures self-heal. |

#### `bo_samskara` — H · Heavy partitioned · P1 · High · CURRENT

**What:** Vertex AI 768-dim vector embeddings — one per MSR signal  
**Now:** native lit · abhinandan lit · chart3 lit · rows 50,104 / 50,102 / 49,875 (floor 60,000) · median 13m, worst 2.6h · 43.7% of 103 attempts complete

**domain:** chart · **rung:** R2 · **within-rung wave:** 1 · **continuation class:** resumable-substep · **rehearsal partition:** `aya_{ayanamsha}` · **timeout source:** registered *(10800s differs from the column default (600s))*


**§19 efficiency ledger** · **p50:** 13m · **p90:** 25m · **worst:** 2.6h · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• Below floor: 50,104 of 60,000 (84%). Either the floor is stale (re-measure and reset) or the build is incomplete — decide explicitly, never let the gap sit.<br>• Embeddings are a deterministic transform (permitted). Pin the model id + dimension in the output digest so a model change invalidates correctly. |
| Rebuild time | • No resume today — a 2.6h run is lost entirely on interruption. Adopt the shared `ResumableWriter` mixin (Phase 4) so committed substeps survive.<br>• Partition key `aya_{ayanamsha}`: record the digest of the inputs each partition consumed. A rule/config change then re-runs only the partitions that read it.<br>• Persist the substep plan total at plan time so progress has a real denominator and the watchdog a true liveness signal.<br>• Watchdog: the `NOW()` heartbeat defect reaps long substeps; switch to `clock_timestamp()` before the next full rebuild (Phase 2). Classify transient failures for auto-retry — 43.7% completion today.<br>• Only 43.7% of 103 attempts complete — most wall-clock is human re-dispatch. Error taxonomy + retry (Phase 4) is the fix, not faster code.<br>• **Not profiled.** Measured baseline only: p50 13m · p90 25m · worst 2.6h · 103 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 names this among the ten heavy assets where the efficiency pass concentrates. |
| Re-architecture & alignment | • Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 3 direct dependant(s) stop invalidating when this asset rebuilds to identical content.<br>• Interruption stops costing up to 2.6h of committed work.<br>• Completion rate rises from 43.7% as transient failures self-heal. |

#### `bo_bimba` — M · Medium deterministic · P2 · Medium · CURRENT

**What:** CGM node registry — one node per signal; carries composite_centrality, pagerank, betweenness, VECTOR(768) embedding and igraph-computed metrics  
**Now:** native lit · abhinandan lit · chart3 lit · rows 385 / 356 / 360 (floor 140) · median 16s, worst 73s · 40.5% of 126 attempts complete

**domain:** chart · **rung:** R2 · **within-rung wave:** 1 · **continuation class:** restartable-light · **rehearsal partition:** `n/a — single-shot, whole-asset is the unit` · **timeout source:** registered *(10800s differs from the column default (600s))*


**§19 efficiency ledger** · **p50:** 16s · **p90:** 38s · **worst:** 73s · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8). |
| Rebuild time | • Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• Fan-out 8: content addressing pays back most here — today any rebuild of this asset, even a no-op, invalidates all 8 dependants.<br>• Only 40.5% of 126 attempts complete — most wall-clock is human re-dispatch. Error taxonomy + retry (Phase 4) is the fix, not faster code.<br>• **Not profiled.** Measured baseline only: p50 16s · p90 38s · worst 73s · 126 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 8 direct dependant(s) stop invalidating when this asset rebuilds to identical content.<br>• Completion rate rises from 40.5% as transient failures self-heal. |

#### `bo_karanajala` — M · Medium deterministic · P2 · Medium · CURRENT

**What:** Causal Graph Model — valenced directed edges between CGM nodes; pre-computed igraph metrics stored as flat columns  
**Now:** native lit · abhinandan lit · chart3 lit · rows 849 / 838 / 830 (floor 300) · median 18s, worst 18m · 40.9% of 127 attempts complete

**domain:** chart · **rung:** R2 · **within-rung wave:** 2 · **continuation class:** restartable-light · **rehearsal partition:** `n/a — single-shot, whole-asset is the unit` · **timeout source:** registered *(10800s differs from the column default (600s))*


**§19 efficiency ledger** · **p50:** 18s · **p90:** 2m · **worst:** 18m · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8). |
| Rebuild time | • Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• Fan-out 10: content addressing pays back most here — today any rebuild of this asset, even a no-op, invalidates all 10 dependants.<br>• Only 40.9% of 127 attempts complete — most wall-clock is human re-dispatch. Error taxonomy + retry (Phase 4) is the fix, not faster code.<br>• **Not profiled.** Measured baseline only: p50 18s · p90 2m · worst 18m · 127 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 10 direct dependant(s) stop invalidating when this asset rebuilds to identical content.<br>• Completion rate rises from 40.9% as transient failures self-heal. |

#### `bo_pratijna` — M · Medium deterministic · P2 · Medium · CURRENT

**What:** Per-event-class promise registry: promised/denied/conditional verdicts with grade, supporting and contradicting signal IDs, varga confirmation, derivation audit  
**Now:** native lit · abhinandan lit · chart3 lit · rows 135 / 135 / 135 · median 16s, worst 71s · 37.3% of 118 attempts complete

**domain:** chart · **rung:** R2 · **within-rung wave:** 0 · **continuation class:** restartable-light · **rehearsal partition:** `n/a — single-shot, whole-asset is the unit` · **timeout source:** registered *(10800s differs from the column default (600s))*


**§19 efficiency ledger** · **p50:** 16s · **p90:** 36s · **worst:** 71s · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8). |
| Rebuild time | • Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• Fan-out 5: content addressing pays back most here — today any rebuild of this asset, even a no-op, invalidates all 5 dependants.<br>• Only 37.3% of 118 attempts complete — most wall-clock is human re-dispatch. Error taxonomy + retry (Phase 4) is the fix, not faster code.<br>• **Not profiled.** Measured baseline only: p50 16s · p90 36s · worst 71s · 118 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Layer position: set `layer_index = L2`, derive `layer_name` from the locked lexicon (Phase 0.5a).<br>• Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 5 direct dependant(s) stop invalidating when this asset rebuilds to identical content.<br>• Completion rate rises from 37.3% as transient failures self-heal. |

#### `bo_sangati` — M · Medium deterministic · P2 · Medium · CURRENT

**What:** Cross-Domain Linkage Matrix — computed_linkage cells, domain rollups, pattern clusters, evolution gradients; primary table bodha_cdlm_cells  
**Now:** native lit · abhinandan lit · chart3 lit · rows 280 / 75 / 75 (floor 70) · median 12s, worst 25m · 39.7% of 126 attempts complete

**domain:** chart · **rung:** R2 · **within-rung wave:** 3 · **continuation class:** restartable-light · **rehearsal partition:** `n/a — single-shot, whole-asset is the unit` · **timeout source:** registered *(10800s differs from the column default (600s))*


**§19 efficiency ledger** · **p50:** 12s · **p90:** 35s · **worst:** 25m · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• Cross-chart asymmetry (280 vs 75): confirm it is chart-driven, not a partial build on one chart. |
| Rebuild time | • Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• Fan-out 12: content addressing pays back most here — today any rebuild of this asset, even a no-op, invalidates all 12 dependants.<br>• Only 39.7% of 126 attempts complete — most wall-clock is human re-dispatch. Error taxonomy + retry (Phase 4) is the fix, not faster code.<br>• **Not profiled.** Measured baseline only: p50 12s · p90 35s · worst 25m · 126 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 12 direct dependant(s) stop invalidating when this asset rebuilds to identical content.<br>• Completion rate rises from 39.7% as transient failures self-heal. |

#### `bo_anveshana` — M · Medium deterministic · P3 · Standard · CURRENT

**What:** Discovery engine: non-obviousness + graph-mining + embedding outliers + bodha_discoveries + anomalies.  
**Now:** native lit · abhinandan lit · chart3 stale · rows 3,774 / 4,909 / 5,222 (floor 500) · median 31s, worst 9m · 41.6% of 101 attempts complete

**domain:** chart · **rung:** R2 · **within-rung wave:** 5 · **continuation class:** restartable-light · **rehearsal partition:** `n/a — single-shot, whole-asset is the unit` · **timeout source:** registered *(10800s differs from the column default (600s))*


**§19 efficiency ledger** · **p50:** 31s · **p90:** 3m · **worst:** 9m · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8). |
| Rebuild time | • Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• Only 41.6% of 101 attempts complete — most wall-clock is human re-dispatch. Error taxonomy + retry (Phase 4) is the fix, not faster code.<br>• **Not profiled.** Measured baseline only: p50 31s · p90 3m · worst 9m · 101 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 3 direct dependant(s) stop invalidating when this asset rebuilds to identical content.<br>• Completion rate rises from 41.6% as transient failures self-heal. |

#### `bo_drishti` — M · Medium deterministic · P3 · Standard · CURRENT

**What:** Question-lens table: template + wildcard graph-sweep + ranks-never-caps, per question domain.  
**Now:** native lit · abhinandan lit · chart3 stale · rows 60 / 60 / 60 (floor 60) · median 2m, worst 15m · 55.3% of 85 attempts complete

**domain:** chart · **rung:** R2 · **within-rung wave:** 4 · **continuation class:** restartable-light · **rehearsal partition:** `n/a — single-shot, whole-asset is the unit` · **timeout source:** registered *(10800s differs from the column default (600s))*


**§19 efficiency ledger** · **p50:** 2m · **p90:** 3m · **worst:** 15m · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8). |
| Rebuild time | • Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• **Not profiled.** Measured baseline only: p50 2m · p90 3m · worst 15m · 85 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 2 direct dependant(s) stop invalidating when this asset rebuilds to identical content. |

#### `bo_pramana_mapa` — M · Medium deterministic · P3 · Standard · CURRENT

**What:** Per-build synthesis quality scorecard — citation density, whole-chart coverage, derivation compliance, layer separation score; keyed by (chart_id, build_id)  
**Now:** native stale · abhinandan lit · chart3 error · rows 1 / 1 / 1 (floor 1) · median 4s, worst 28s · 42.2% of 102 attempts complete

**domain:** chart · **rung:** R2 · **within-rung wave:** 6 · **continuation class:** restartable-light · **rehearsal partition:** `n/a — single-shot, whole-asset is the unit` · **timeout source:** registered *(10800s differs from the column default (600s))*


**§19 efficiency ledger** · **p50:** 4s · **p90:** 19s · **worst:** 28s · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8). |
| Rebuild time | • Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• Only 42.2% of 102 attempts complete — most wall-clock is human re-dispatch. Error taxonomy + retry (Phase 4) is the fix, not faster code.<br>• DAG depth 12: sits in the serial tail. Audit its 8 declared edges for ones never actually read (Phase 5) — every removed edge is pure wall-clock.<br>• **Not profiled.** Measured baseline only: p50 4s · p90 19s · worst 28s · 102 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 1 direct dependant(s) stop invalidating when this asset rebuilds to identical content.<br>• Completion rate rises from 42.2% as transient failures self-heal. |

#### `bo_samvada` — M · Medium deterministic · P3 · Standard · CURRENT

**What:** UCD — read-side conceptual digest (join of A8/A11/A12/A13 chart_summaries via vw_chart_digest + query_ucd)  
**Now:** native stale · abhinandan lit · chart3 error · rows 5 / 5 / 5 (floor 5) · median 0s, worst 2s · 42.6% of 101 attempts complete

**domain:** chart · **rung:** R2 · **within-rung wave:** 7 · **continuation class:** restartable-light · **rehearsal partition:** `n/a — single-shot, whole-asset is the unit` · **timeout source:** registered *(10800s differs from the column default (600s))*


**§19 efficiency ledger** · **p50:** 0s · **p90:** 2s · **worst:** 2s · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• §N.7 narration fidelity: every sentence restates a cited fact_id it reads, never re-derives; add a golden-value test for the narration layer (verified fact ≠ verified prose). |
| Rebuild time | • Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• Only 42.6% of 101 attempts complete — most wall-clock is human re-dispatch. Error taxonomy + retry (Phase 4) is the fix, not faster code.<br>• DAG depth 13: sits in the serial tail. Audit its 5 declared edges for ones never actually read (Phase 5) — every removed edge is pure wall-clock.<br>• **Not profiled.** Measured baseline only: p50 0s · p90 2s · worst 2s · 101 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• Completion rate rises from 42.6% as transient failures self-heal. |

#### `bo_upaya` — M · Medium deterministic · P3 · Standard · CURRENT

**What:** Remediation Map — ALL 6 RM tables; primary table bodha_rm_resonances (resonance targets that remedies key off) + bodha_rm_remedy_prescriptions + 4 ancillary tab  
**Now:** native lit · abhinandan lit · chart3 error · rows 180 / 180 / 180 (floor 180) · median 9s, worst 17m · 38.9% of 131 attempts complete

**domain:** chart · **rung:** R2 · **within-rung wave:** 4 · **continuation class:** restartable-light · **rehearsal partition:** `n/a — single-shot, whole-asset is the unit` · **timeout source:** registered *(10800s differs from the column default (600s))*


**§19 efficiency ledger** · **p50:** 9s · **p90:** 68s · **worst:** 17m · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8). |
| Rebuild time | • Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• Only 38.9% of 131 attempts complete — most wall-clock is human re-dispatch. Error taxonomy + retry (Phase 4) is the fix, not faster code.<br>• **Not profiled.** Measured baseline only: p50 9s · p90 68s · worst 17m · 131 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 4 direct dependant(s) stop invalidating when this asset rebuilds to identical content.<br>• Completion rate rises from 38.9% as transient failures self-heal. |

### L3 · Kāla — 23 assets · 10 non-conformant · 8 P0 · 2 heavy

*Time — dashas, transits, windows, the field; the heaviest layer by compute.* Where the wall-clock lives. Two assets have individually exceeded 33 hours. Partition receipts and shared resumability convert interruption from total loss into bounded rework, and the generation/authority model belongs here.


#### `ka_bhavishya_lekha` — M · Medium deterministic · P0 · Blocking defect · DRAFT

**What:** Probabilistic forward projections (3-year horizon)  
**Now:** native lit · abhinandan lit · chart3 error · rows 100 / 100 / 0 · median 0s, worst 2s · 37.8% of 127 attempts complete

**domain:** chart · **rung:** R3 · **within-rung wave:** 5 · **continuation class:** restartable-light · **rehearsal partition:** `n/a — single-shot, whole-asset is the unit` · **timeout source:** registered *(10800s differs from the column default (600s))*


**§19 efficiency ledger** · **p50:** 0s · **p90:** 2s · **worst:** 2s · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• Set `target_floor` = 100 (achieved on native; floors are aspirational, never fabricated — §N.4).<br>• Chart 3 holds zero rows — the rehearsal chart is incomplete for this asset; rebuild there first (Phase 1) so it can serve as the test subject.<br>• Derivation ledger: 4 declared inputs — record which upstream digests each output row was built from (partition receipt) so a wrong answer is traceable to the input that produced it.<br>• §N.7 narration fidelity: every sentence restates a cited fact_id it reads, never re-derives; add a golden-value test for the narration layer (verified fact ≠ verified prose). |
| Rebuild time | • Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• Only 37.8% of 127 attempts complete — most wall-clock is human re-dispatch. Error taxonomy + retry (Phase 4) is the fix, not faster code.<br>• DAG depth 15: sits in the serial tail. Audit its 4 declared edges for ones never actually read (Phase 5) — every removed edge is pure wall-clock.<br>• **Not profiled.** Measured baseline only: p50 0s · p90 2s · worst 2s · 127 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Promote to CURRENT or record why it remains DRAFT (Phase 0.8b) — it is built and read by 6 serving surface(s), so it is authoritative in practice. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 1 direct dependant(s) stop invalidating when this asset rebuilds to identical content.<br>• Completion rate rises from 37.8% as transient failures self-heal. |

#### `ka_gochara_sweep` — X · Generation-bearing · P0 · Blocking defect · SUPERSEDED_BY

**What:** D-5 Lane G-4: birth->birth+100y daily-grid gochara (transit) intensity sweep (lambda_e via G-3's services/gochara_intensity), shape-aware (point/interval/chain   
**Now:** native error · abhinandan error · chart3 error · rows 16,297 / 19,323 / 2,667 · median 2.1h, worst 35.6h · 9.6% of 94 attempts complete

**domain:** chart · **rung:** R3 · **within-rung wave:** — · **continuation class:** resumable-substep · **rehearsal partition:** `{event_class}:year:{idx}` · **timeout source:** registered *(21600s differs from the column default (600s))*


**§19 efficiency ledger** · **p50:** 2.1h · **p90:** 6.0h · **worst:** 35.6h · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `one authoritative generation per chart via kala_gochara_authority; no window with end < start`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• RETIRED and unrebuildable: no registered writer. Correctness = the verified 2026-08-23 snapshot; chart 3 still serves these v1 rows (no authority row). Record `data_disposition = RETAINED_AS_CAPITAL`. |
| Rebuild time | • Has a substep plan (`{event_class}:year:{idx}`) but runs in 2.1h — resumption is irrelevant here; per-substep input digests still matter because they give partition-scoped early cutoff downstream.<br>• Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• Only 9.6% of 94 attempts complete — most wall-clock is human re-dispatch. Error taxonomy + retry (Phase 4) is the fix, not faster code.<br>• **Not profiled.** Measured baseline only: p50 2.1h · p90 6.0h · worst 35.6h · 94 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Lifecycle: execute the supported retire operation — clear residual throughput rows, set `superseded_by` and `data_disposition`; never DELETE the registry row (I6).<br>• Generation-bearing: model generation + per-chart authority as first-class registry/UI concepts; one count and one freshness per generation (Phase 2). |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• Completion rate rises from 9.6% as transient failures self-heal. |

#### `ka_jivana_parva` — M · Medium deterministic · P0 · Blocking defect · DRAFT

**What:** Life-arc biographical chapter artifact  
**Now:** native lit · abhinandan lit · chart3 stale · rows 100 / 100 / 109 · median 0s, worst 3s · 36.3% of 124 attempts complete

**domain:** chart · **rung:** R3 · **within-rung wave:** 5 · **continuation class:** restartable-light · **rehearsal partition:** `n/a — single-shot, whole-asset is the unit` · **timeout source:** registered *(10800s differs from the column default (600s))*


**§19 efficiency ledger** · **p50:** 0s · **p90:** 2s · **worst:** 3s · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• Set `target_floor` = 100 (achieved on native; floors are aspirational, never fabricated — §N.4).<br>• Derivation ledger: 5 declared inputs — record which upstream digests each output row was built from (partition receipt) so a wrong answer is traceable to the input that produced it.<br>• §N.7 narration fidelity: every sentence restates a cited fact_id it reads, never re-derives; add a golden-value test for the narration layer (verified fact ≠ verified prose). |
| Rebuild time | • Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• Only 36.3% of 124 attempts complete — most wall-clock is human re-dispatch. Error taxonomy + retry (Phase 4) is the fix, not faster code.<br>• DAG depth 15: sits in the serial tail. Audit its 5 declared edges for ones never actually read (Phase 5) — every removed edge is pure wall-clock.<br>• **Not profiled.** Measured baseline only: p50 0s · p90 2s · worst 3s · 124 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Promote to CURRENT or record why it remains DRAFT (Phase 0.8b) — it is built and read by 5 serving surface(s), so it is authoritative in practice. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• Completion rate rises from 36.3% as transient failures self-heal. |

#### `ka_kala_darshana` — M · Medium deterministic · P0 · Blocking defect · DRAFT

**What:** Display-ready temporal view  
**Now:** native lit · abhinandan lit · chart3 stale · rows 750 / 750 / 0 · median 0s, worst 4s · 39.3% of 122 attempts complete

**domain:** chart · **rung:** R3 · **within-rung wave:** 4 · **continuation class:** restartable-light · **rehearsal partition:** `n/a — single-shot, whole-asset is the unit` · **timeout source:** registered *(10800s differs from the column default (600s))*


**§19 efficiency ledger** · **p50:** 0s · **p90:** 3s · **worst:** 4s · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• Set `target_floor` = 750 (achieved on native; floors are aspirational, never fabricated — §N.4).<br>• Chart 3 holds zero rows — the rehearsal chart is incomplete for this asset; rebuild there first (Phase 1) so it can serve as the test subject.<br>• §N.7 narration fidelity: every sentence restates a cited fact_id it reads, never re-derives; add a golden-value test for the narration layer (verified fact ≠ verified prose). |
| Rebuild time | • Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• Only 39.3% of 122 attempts complete — most wall-clock is human re-dispatch. Error taxonomy + retry (Phase 4) is the fix, not faster code.<br>• DAG depth 14: sits in the serial tail. Audit its 3 declared edges for ones never actually read (Phase 5) — every removed edge is pure wall-clock.<br>• **Not profiled.** Measured baseline only: p50 0s · p90 3s · worst 4s · 122 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Promote to CURRENT or record why it remains DRAFT (Phase 0.8b) — it is built and read by 4 serving surface(s), so it is authoritative in practice. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 3 direct dependant(s) stop invalidating when this asset rebuilds to identical content.<br>• Completion rate rises from 39.3% as transient failures self-heal. |

#### `ka_kalasutra` — M · Medium deterministic · P0 · Blocking defect · DRAFT

**What:** Bounded activation artifact (1 row per signal×ayanamsha)  
**Now:** native lit · abhinandan lit · chart3 stale · rows 335,403 / 336,093 / 1,055 · median 33s, worst 41m · 39.8% of 123 attempts complete

**domain:** chart · **rung:** R3 · **within-rung wave:** 3 · **continuation class:** restartable-light · **rehearsal partition:** `n/a — single-shot, whole-asset is the unit` · **timeout source:** registered *(10800s differs from the column default (600s))*


**§19 efficiency ledger** · **p50:** 33s · **p90:** 11m · **worst:** 41m · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• Set `target_floor` = 335,403 (achieved on native; floors are aspirational, never fabricated — §N.4). |
| Rebuild time | • Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• Only 39.8% of 123 attempts complete — most wall-clock is human re-dispatch. Error taxonomy + retry (Phase 4) is the fix, not faster code.<br>• DAG depth 13: sits in the serial tail. Audit its 3 declared edges for ones never actually read (Phase 5) — every removed edge is pure wall-clock.<br>• **Not profiled.** Measured baseline only: p50 33s · p90 11m · worst 41m · 123 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Promote to CURRENT or record why it remains DRAFT (Phase 0.8b) — it is built and read by 12 serving surface(s), so it is authoritative in practice. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 2 direct dependant(s) stop invalidating when this asset rebuilds to identical content.<br>• Completion rate rises from 39.8% as transient failures self-heal. |

#### `ka_sangam` — H · Heavy partitioned · P0 · Blocking defect · DRAFT

**What:** Rigor-scored intersection windows (Mode A daśā-prior funnel + Mode B off-daśā sweep)  
**Now:** native lit · abhinandan lit · chart3 stale · rows 14,868 / 17,957 / 2,540 · median 8m, worst 2.8h · 43.1% of 116 attempts complete

**domain:** chart · **rung:** R3 · **within-rung wave:** 2 · **continuation class:** resumable-substep · **rehearsal partition:** `near + lifetime:{i}` · **timeout source:** registered *(10800s differs from the column default (600s))*


**§19 efficiency ledger** · **p50:** 8m · **p90:** 40m · **worst:** 2.8h · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• Set `target_floor` = 14,868 (achieved on native; floors are aspirational, never fabricated — §N.4).<br>• Derivation ledger: 10 declared inputs — record which upstream digests each output row was built from (partition receipt) so a wrong answer is traceable to the input that produced it. |
| Rebuild time | • Private resume copy with a hand-bumped `_RESUME_VERSION`: migrate to the shared mixin and replace the whole-build fingerprint with per-substep INPUT digests, so a mismatch replans only the changed partitions instead of everything.<br>• Partition key `near + lifetime:{i}`: record the digest of the inputs each partition consumed. A rule/config change then re-runs only the partitions that read it.<br>• Persist the substep plan total at plan time so progress has a real denominator and the watchdog a true liveness signal.<br>• Watchdog: the `NOW()` heartbeat defect reaps long substeps; switch to `clock_timestamp()` before the next full rebuild (Phase 2). Classify transient failures for auto-retry — 43.1% completion today.<br>• Fan-out 11: content addressing pays back most here — today any rebuild of this asset, even a no-op, invalidates all 11 dependants.<br>• Only 43.1% of 116 attempts complete — most wall-clock is human re-dispatch. Error taxonomy + retry (Phase 4) is the fix, not faster code.<br>• DAG depth 12: sits in the serial tail. Audit its 10 declared edges for ones never actually read (Phase 5) — every removed edge is pure wall-clock.<br>• **Not profiled.** Measured baseline only: p50 8m · p90 40m · worst 2.8h · 116 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 names this among the ten heavy assets where the efficiency pass concentrates. |
| Re-architecture & alignment | • Promote to CURRENT or record why it remains DRAFT (Phase 0.8b) — it is built and read by 4 serving surface(s), so it is authoritative in practice. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 11 direct dependant(s) stop invalidating when this asset rebuilds to identical content.<br>• Interruption stops costing up to 2.8h of committed work.<br>• Completion rate rises from 43.1% as transient failures self-heal. |

#### `ka_vighnakara` — M · Medium deterministic · P0 · Blocking defect · DRAFT

**What:** Obstruction/counter-indicator detector  
**Now:** native lit · abhinandan lit · chart3 stale · rows 536 / 741 / 6 · median 14s, worst 32m · 40.2% of 117 attempts complete

**domain:** chart · **rung:** R3 · **within-rung wave:** 3 · **continuation class:** restartable-light · **rehearsal partition:** `n/a — single-shot, whole-asset is the unit` · **timeout source:** registered *(10800s differs from the column default (600s))*


**§19 efficiency ledger** · **p50:** 14s · **p90:** 31s · **worst:** 32m · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• Set `target_floor` = 536 (achieved on native; floors are aspirational, never fabricated — §N.4).<br>• Derivation ledger: 4 declared inputs — record which upstream digests each output row was built from (partition receipt) so a wrong answer is traceable to the input that produced it. |
| Rebuild time | • Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• Fan-out 5: content addressing pays back most here — today any rebuild of this asset, even a no-op, invalidates all 5 dependants.<br>• Only 40.2% of 117 attempts complete — most wall-clock is human re-dispatch. Error taxonomy + retry (Phase 4) is the fix, not faster code.<br>• DAG depth 13: sits in the serial tail. Audit its 4 declared edges for ones never actually read (Phase 5) — every removed edge is pure wall-clock.<br>• **Not profiled.** Measured baseline only: p50 14s · p90 31s · worst 32m · 117 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Promote to CURRENT or record why it remains DRAFT (Phase 0.8b) — it is built and read by 3 serving surface(s), so it is authoritative in practice. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 5 direct dependant(s) stop invalidating when this asset rebuilds to identical content.<br>• Completion rate rises from 40.2% as transient failures self-heal. |

#### `ka_yojaka` — M · Medium deterministic · P0 · Blocking defect · DRAFT

**What:** Classifies each L2 signal into a signature_class, binds the RATIFIED class template, stores concrete activation predicates for ka_sangam/ka_vighnakara to search  
**Now:** native lit · abhinandan lit · chart3 error · rows 50,104 / 50,171 / 49,875 · median 36s, worst 2m · 49.0% of 104 attempts complete

**domain:** chart · **rung:** R3 · **within-rung wave:** 0 · **continuation class:** restartable-light · **rehearsal partition:** `n/a — single-shot, whole-asset is the unit` · **timeout source:** registered *(10800s differs from the column default (600s))*


**§19 efficiency ledger** · **p50:** 36s · **p90:** 77s · **worst:** 2m · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• Set `target_floor` = 50,104 (achieved on native; floors are aspirational, never fabricated — §N.4).<br>• Derivation ledger: 7 declared inputs — record which upstream digests each output row was built from (partition receipt) so a wrong answer is traceable to the input that produced it. |
| Rebuild time | • Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• Only 49.0% of 104 attempts complete — most wall-clock is human re-dispatch. Error taxonomy + retry (Phase 4) is the fix, not faster code.<br>• **Not profiled.** Measured baseline only: p50 36s · p90 77s · worst 2m · 104 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Promote to CURRENT or record why it remains DRAFT (Phase 0.8b) — it is built and read by 4 serving surface(s), so it is authoritative in practice. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 3 direct dependant(s) stop invalidating when this asset rebuilds to identical content.<br>• Completion rate rises from 49.0% as transient failures self-heal. |

#### `ka_dasha_kala` — S · Service probe · P1 · High · DRAFT

**What:** Lazy-pruning tree-walk over chart_dashas (level-4 Sookshma) with cross-system agreement scoring  
**Now:** service · global state n/a · median 1s, worst 26s · 42.3% of 111 attempts complete

**domain:** chart · **rung:** R3 · **within-rung wave:** 0 · **continuation class:** probe-only · **rehearsal partition:** `n/a — service probe` · **timeout source:** registered *(10800s differs from the column default (600s))*


**§19 efficiency ledger** · **p50:** 1s · **p90:** 5s · **worst:** 26s · **rows/sec:** null · **bound class:** not-a-build · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: service probe — there is no build to measure (structural). rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Real liveness + correctness probe with an SLO (not just "responds"): exercise one known-answer query and compare against a pinned expected value; alert on drift or timeout. |
| Rebuild time | • Not a build; nothing to speed up. Exclude from build plans and ETA math. |
| Re-architecture & alignment | • Move to the service lane with `health_probe` + `provides_apis`; `count_sql` must be null. |
| Expected benefit | • A degraded service surfaces in minutes, not months (one sat red for 66 days). |

#### `ka_gochara` — X · Generation-bearing · P1 · High · CURRENT

**What:** Primary per-chart gochara window materializer (GOCHARA-UTKARSA)  
**Now:** native lit · abhinandan lit · chart3 — · rows 943 / 941 / 0 · median 0s, worst 6.5h · 54.1% of 61 attempts complete

**domain:** chart · **rung:** R3 · **within-rung wave:** 1 · **continuation class:** resumable-substep · **rehearsal partition:** `event_class` · **timeout source:** registered *(1800s differs from the column default (600s))*


**§19 efficiency ledger** · **p50:** 0s · **p90:** 2s · **worst:** 6.5h · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `one authoritative generation per chart via kala_gochara_authority; no window with end < start`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• Chart 3 holds zero rows — the rehearsal chart is incomplete for this asset; rebuild there first (Phase 1) so it can serve as the test subject.<br>• F-52 consequence: every materialized v2 row is stale under the live scoring signature and no rebuild has been dispatched — rematerialize under the determinism harness, or mark stale honestly in the UI. |
| Rebuild time | • Has a substep plan (`event_class`) but runs in 0s — resumption is irrelevant here; per-substep input digests still matter because they give partition-scoped early cutoff downstream.<br>• Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• **Not profiled.** Measured baseline only: p50 0s · p90 2s · worst 6.5h · 61 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Generation-bearing: model generation + per-chart authority as first-class registry/UI concepts; one count and one freshness per generation (Phase 2).<br>• Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 3 direct dependant(s) stop invalidating when this asset rebuilds to identical content. |

#### `ka_graha_sancara` — S · Service probe · P1 · High · DRAFT

**What:** Ephemeris-at-T service: sidereal positions for all 9 grahas at any datetime  
**Now:** service · global state lit · median 0s, worst 2s · 54.2% of 59 attempts complete

**domain:** shared · **rung:** R3 · **within-rung wave:** 0 · **continuation class:** probe-only · **rehearsal partition:** `n/a — service probe` · **timeout source:** registered *(10800s differs from the column default (600s))*


**§19 efficiency ledger** · **p50:** 0s · **p90:** 1s · **worst:** 2s · **rows/sec:** null · **bound class:** not-a-build · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: service probe — there is no build to measure (structural). rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Real liveness + correctness probe with an SLO (not just "responds"): exercise one known-answer query and compare against a pinned expected value; alert on drift or timeout. |
| Rebuild time | • Not a build; nothing to speed up. Exclude from build plans and ETA math. |
| Re-architecture & alignment | • Keep out of per-chart plans but expose completion to the per-chart readiness gate uniformly (the migration-563 class of bug, made structural).<br>• Move to the service lane with `health_probe` + `provides_apis`; `count_sql` must be null. |
| Expected benefit | • A degraded service surfaces in minutes, not months (one sat red for 66 days). |

#### `ka_kshetra` — H · Heavy partitioned · P1 · High · CURRENT

**What:** ṢAḌ-DARŚANA W2: the ten-stage point-process temporal field  
**Now:** native stale · abhinandan lit · chart3 error · rows 8,599,775 / 2,412,882 / 0 · median 39m, worst 33.8h · 11.9% of 126 attempts complete

**domain:** chart · **rung:** R3 · **within-rung wave:** 1 · **continuation class:** resumable-substep · **rehearsal partition:** `stage{n}:{event_class}:{slice}` · **timeout source:** registered *(86400s differs from the column default (600s))*


**§19 efficiency ledger** · **p50:** 39m · **p90:** 2.2h · **worst:** 33.8h · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• Cross-chart asymmetry (8,599,775 vs 2,412,882): confirm it is chart-driven, not a partial build on one chart.<br>• Chart 3 holds zero rows — the rehearsal chart is incomplete for this asset; rebuild there first (Phase 1) so it can serve as the test subject.<br>• Derivation ledger: 8 declared inputs — record which upstream digests each output row was built from (partition receipt) so a wrong answer is traceable to the input that produced it.<br>• DHARA engine (analytic) replaced the sampled engine mid-August; `_RESUME_VERSION` is at 7. Add a build-twice determinism check at the stage level — the content hash (F-149) already exists, so compare digests across two clean builds. |
| Rebuild time | • Private resume copy with a hand-bumped `_RESUME_VERSION`: migrate to the shared mixin and replace the whole-build fingerprint with per-substep INPUT digests, so a mismatch replans only the changed partitions instead of everything.<br>• Partition key `stage{n}:{event_class}:{slice}`: record the digest of the inputs each partition consumed. A rule/config change then re-runs only the partitions that read it.<br>• Persist the substep plan total at plan time so progress has a real denominator and the watchdog a true liveness signal.<br>• Watchdog: the `NOW()` heartbeat defect reaps long substeps; switch to `clock_timestamp()` before the next full rebuild (Phase 2). Classify transient failures for auto-retry — 11.9% completion today.<br>• Only 11.9% of 126 attempts complete — most wall-clock is human re-dispatch. Error taxonomy + retry (Phase 4) is the fix, not faster code.<br>• **Not profiled.** Measured baseline only: p50 39m · p90 2.2h · worst 33.8h · 126 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 names this among the ten heavy assets where the efficiency pass concentrates. |
| Re-architecture & alignment | • Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 2 direct dependant(s) stop invalidating when this asset rebuilds to identical content.<br>• Interruption stops costing up to 33.8h of committed work.<br>• Completion rate rises from 11.9% as transient failures self-heal. |

#### `ka_muhurta_seva` — S · Service probe · P1 · High · DRAFT

**What:** Deterministic panchāṅga/muhūrta scoring service  
**Now:** service · global state lit · median 0s, worst 4s · 54.2% of 59 attempts complete

**domain:** shared · **rung:** R3 · **within-rung wave:** 1 · **continuation class:** probe-only · **rehearsal partition:** `n/a — service probe` · **timeout source:** registered *(10800s differs from the column default (600s))*


**§19 efficiency ledger** · **p50:** 0s · **p90:** 1s · **worst:** 4s · **rows/sec:** null · **bound class:** not-a-build · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: service probe — there is no build to measure (structural). rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Real liveness + correctness probe with an SLO (not just "responds"): exercise one known-answer query and compare against a pinned expected value; alert on drift or timeout. |
| Rebuild time | • Not a build; nothing to speed up. Exclude from build plans and ETA math. |
| Re-architecture & alignment | • Keep out of per-chart plans but expose completion to the per-chart readiness gate uniformly (the migration-563 class of bug, made structural).<br>• Move to the service lane with `health_probe` + `provides_apis`; `count_sql` must be null. |
| Expected benefit | • A degraded service surfaces in minutes, not months (one sat red for 66 days). |

#### `ka_tulana` — S · Service probe · P1 · High · DRAFT

**What:** Serve-time QT-4 ranking engine  
**Now:** service · global state n/a · median 0s, worst 1s · 37.3% of 118 attempts complete

**domain:** chart · **rung:** R3 · **within-rung wave:** 5 · **continuation class:** probe-only · **rehearsal partition:** `n/a — service probe` · **timeout source:** registered *(10800s differs from the column default (600s))*


**§19 efficiency ledger** · **p50:** 0s · **p90:** 1s · **worst:** 1s · **rows/sec:** null · **bound class:** not-a-build · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: service probe — there is no build to measure (structural). rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Real liveness + correctness probe with an SLO (not just "responds"): exercise one known-answer query and compare against a pinned expected value; alert on drift or timeout. |
| Rebuild time | • Not a build; nothing to speed up. Exclude from build plans and ETA math. |
| Re-architecture & alignment | • Move to the service lane with `health_probe` + `provides_apis`; `count_sql` must be null. |
| Expected benefit | • A degraded service surfaces in minutes, not months (one sat red for 66 days). |

#### `ka_avadhi` — M · Medium deterministic · P3 · Standard · CURRENT

**What:** Per-dasha-period dossiers: for each chart, dasha system, MD/AD/PD level, stores lord condition (refs to chart_facts), activated promise-register IDs (from bodha  
**Now:** native lit · abhinandan lit · chart3 error · rows 1,169 / 1,160 / 1,291 · median 14s, worst 15m · 45.3% of 95 attempts complete

**domain:** chart · **rung:** R3 · **within-rung wave:** 0 · **continuation class:** restartable-light · **rehearsal partition:** `n/a — single-shot, whole-asset is the unit` · **timeout source:** registered *(10800s differs from the column default (600s))*


**§19 efficiency ledger** · **p50:** 14s · **p90:** 26s · **worst:** 15m · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8). |
| Rebuild time | • Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• Only 45.3% of 95 attempts complete — most wall-clock is human re-dispatch. Error taxonomy + retry (Phase 4) is the fix, not faster code.<br>• **Not profiled.** Measured baseline only: p50 14s · p90 26s · worst 15m · 95 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Layer position: set `layer_index = L3`, derive `layer_name` from the locked lexicon (Phase 0.5a).<br>• Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 1 direct dependant(s) stop invalidating when this asset rebuilds to identical content.<br>• Completion rate rises from 45.3% as transient failures self-heal. |

#### `ka_gochara_resonance` — X · Generation-bearing · P3 · Standard · CURRENT

**What:** D-5 Lane G-1: per-chart x event-class classical-prior-weighted target sets (bhavas, lords, karakas, mechanism nodes, sensitive degrees, arudhas, yoga constituen  
**Now:** native lit · abhinandan lit · chart3 lit · rows 762 / 750 / 77 · median 0s, worst 17s · 78.3% of 23 attempts complete

**domain:** chart · **rung:** R3 · **within-rung wave:** 0 · **continuation class:** restartable-light · **rehearsal partition:** `n/a — single-shot, whole-asset is the unit` · **timeout source:** default *(600s equals the asset_registry column default and the runner fallback (_WRITER_TIMEOUT_SECONDS) — indistinguishable from never set)*


**§19 efficiency ledger** · **p50:** 0s · **p90:** 17s · **worst:** 17s · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `one authoritative generation per chart via kala_gochara_authority; no window with end < start`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8). |
| Rebuild time | • Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• **Not profiled.** Measured baseline only: p50 0s · p90 17s · worst 17s · 23 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Generation-bearing: model generation + per-chart authority as first-class registry/UI concepts; one count and one freshness per generation (Phase 2).<br>• Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 4 direct dependant(s) stop invalidating when this asset rebuilds to identical content. |

#### `ka_gochara_v3_century_materialize` — X · Generation-bearing · P3 · Standard · CURRENT

**What:** GOCHARA-UTKARSA W3.4 heavy writer: plan_substeps returns 60 substeps (6 event classes x 10 decade slices spanning birth-century 1984-2084)  
**Now:** native error · abhinandan stale · chart3 — · rows 914 / 916 / 0 · median 2m, worst 58m

**domain:** chart · **rung:** R3 · **within-rung wave:** 1 · **continuation class:** resumable-substep · **rehearsal partition:** `{event_class}::{decade}` · **timeout source:** registered *(3600s differs from the column default (600s))*


**§19 efficiency ledger** · **p50:** 2m · **p90:** 34m · **worst:** 58m · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `one authoritative generation per chart via kala_gochara_authority; no window with end < start`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• Chart 3 holds zero rows — the rehearsal chart is incomplete for this asset; rebuild there first (Phase 1) so it can serve as the test subject.<br>• Derivation ledger: 6 declared inputs — record which upstream digests each output row was built from (partition receipt) so a wrong answer is traceable to the input that produced it.<br>• F-52 consequence: every materialized v2 row is stale under the live scoring signature and no rebuild has been dispatched — rematerialize under the determinism harness, or mark stale honestly in the UI. |
| Rebuild time | • Has a substep plan (`{event_class}::{decade}`) but runs in 2m — resumption is irrelevant here; per-substep input digests still matter because they give partition-scoped early cutoff downstream.<br>• Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• **Not profiled.** Measured baseline only: p50 2m · p90 34m · worst 58m · 7 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Generation-bearing: model generation + per-chart authority as first-class registry/UI concepts; one count and one freshness per generation (Phase 2).<br>• No detected serving consumer (Phase 0.8c): record the missing consumer or retire with a disposition.<br>• Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it. |

#### `ka_kota_chakra` — M · Medium deterministic · P3 · Standard · CURRENT

**What:** ṢAḌ-DARŚANA W3 item 16: transiting grahas mapped to the kota's stambha/durgantara/prakara/bahya rings relative to the janma nakshatra, with entry/exit windows a  
**Now:** native lit · abhinandan dormant · chart3 — · rows 588 / 585 / 0 · median 1s, worst 3s · 27.3% of 11 attempts complete

**domain:** chart · **rung:** R3 · **within-rung wave:** 0 · **continuation class:** restartable-light · **rehearsal partition:** `n/a — single-shot, whole-asset is the unit` · **timeout source:** registered *(120s differs from the column default (600s))*


**§19 efficiency ledger** · **p50:** 1s · **p90:** 3s · **worst:** 3s · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• Chart 3 holds zero rows — the rehearsal chart is incomplete for this asset; rebuild there first (Phase 1) so it can serve as the test subject. |
| Rebuild time | • Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• **Not profiled.** Measured baseline only: p50 1s · p90 3s · worst 3s · 11 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 1 direct dependant(s) stop invalidating when this asset rebuilds to identical content. |

#### `ka_moorti_nirnaya` — M · Medium deterministic · P3 · Standard · CURRENT

**What:** ṢAḌ-DARŚANA W3 item 4: the classical gold/silver/copper/iron quality of a transiting graha's stay in a sign, determined by the Moon's nakshatra at the moment of  
**Now:** native lit · abhinandan lit · chart3 — · rows 72 / 72 / 0 · median 1s, worst 4s · 33.3% of 12 attempts complete

**domain:** chart · **rung:** R3 · **within-rung wave:** 0 · **continuation class:** restartable-light · **rehearsal partition:** `n/a — single-shot, whole-asset is the unit` · **timeout source:** registered *(120s differs from the column default (600s))*


**§19 efficiency ledger** · **p50:** 1s · **p90:** 3s · **worst:** 4s · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• Chart 3 holds zero rows — the rehearsal chart is incomplete for this asset; rebuild there first (Phase 1) so it can serve as the test subject. |
| Rebuild time | • Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• **Not profiled.** Measured baseline only: p50 1s · p90 3s · worst 4s · 12 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 1 direct dependant(s) stop invalidating when this asset rebuilds to identical content. |

#### `ka_sudarshana_varsha` — M · Medium deterministic · P3 · Standard · CURRENT

**What:** ṢAḌ-DARŚANA W3 item 17: the rotating annual house-per-year progression of the tri-lagna framework (Janma/Chandra/Sūrya Lagna), full 120-year lifespan  
**Now:** native lit · abhinandan — · chart3 — · rows 120 / 0 / 0 · median 2s, worst 2s

**domain:** chart · **rung:** R3 · **within-rung wave:** 0 · **continuation class:** restartable-light · **rehearsal partition:** `n/a — single-shot, whole-asset is the unit` · **timeout source:** registered *(60s differs from the column default (600s))*


**§19 efficiency ledger** · **p50:** 2s · **p90:** 2s · **worst:** 2s · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• Chart 3 holds zero rows — the rehearsal chart is incomplete for this asset; rebuild there first (Phase 1) so it can serve as the test subject. |
| Rebuild time | • Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• **Not profiled.** Measured baseline only: p50 2s · p90 2s · worst 2s · 6 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it. |

#### `ka_taranga` — M · Medium deterministic · P3 · Standard · CURRENT

**What:** Monthly activation waveform (1950–2100): convolution of dasha × transit × promise for each domain and event class  
**Now:** native lit · abhinandan lit · chart3 error · rows 92,412 / 92,412 / 92,412 · median 22s, worst 41m · 39.4% of 109 attempts complete

**domain:** chart · **rung:** R3 · **within-rung wave:** 1 · **continuation class:** restartable-light · **rehearsal partition:** `n/a — single-shot, whole-asset is the unit` · **timeout source:** registered *(10800s differs from the column default (600s))*


**§19 efficiency ledger** · **p50:** 22s · **p90:** 54s · **worst:** 41m · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• Derivation ledger: 5 declared inputs — record which upstream digests each output row was built from (partition receipt) so a wrong answer is traceable to the input that produced it. |
| Rebuild time | • Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• Only 39.4% of 109 attempts complete — most wall-clock is human re-dispatch. Error taxonomy + retry (Phase 4) is the fix, not faster code.<br>• DAG depth 13: sits in the serial tail. Audit its 5 declared edges for ones never actually read (Phase 5) — every removed edge is pure wall-clock.<br>• **Not profiled.** Measured baseline only: p50 22s · p90 54s · worst 41m · 109 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Layer position: set `layer_index = L3`, derive `layer_name` from the locked lexicon (Phase 0.5a).<br>• Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• Completion rate rises from 39.4% as transient failures self-heal. |

#### `ka_tithi_pravesha` — M · Medium deterministic · P3 · Standard · CURRENT

**What:** ṢAḌ-DARŚANA W3 item 13: the lunar-return counterpart to Tājika Vārṣaphala (ga_tajaka) — the annual chart cast for the instant the transiting Moon returns to its  
**Now:** native lit · abhinandan lit · chart3 — · rows 120 / 120 / 0 · median 2s, worst 2s · 33.3% of 12 attempts complete

**domain:** chart · **rung:** R3 · **within-rung wave:** 0 · **continuation class:** restartable-light · **rehearsal partition:** `n/a — single-shot, whole-asset is the unit` · **timeout source:** registered *(120s differs from the column default (600s))*


**§19 efficiency ledger** · **p50:** 2s · **p90:** 2s · **worst:** 2s · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• Chart 3 holds zero rows — the rehearsal chart is incomplete for this asset; rebuild there first (Phase 1) so it can serve as the test subject. |
| Rebuild time | • Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• **Not profiled.** Measured baseline only: p50 2s · p90 2s · worst 2s · 12 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 1 direct dependant(s) stop invalidating when this asset rebuilds to identical content. |

#### `ka_vedha_gochara` — M · Medium deterministic · P3 · Standard · CURRENT

**What:** ṢAḌ-DARŚANA W3 item 5 (closes R-19, CLOSED-PARTIAL-BY-DESIGN per ADJUDICATION-11): three classical vedha (obstruction) mechanisms applied to a chart's currently  
**Now:** native lit · abhinandan dormant · chart3 — · rows 176 / 178 / 0 · median 3s, worst 3s · 27.3% of 11 attempts complete

**domain:** chart · **rung:** R3 · **within-rung wave:** 0 · **continuation class:** restartable-light · **rehearsal partition:** `n/a — single-shot, whole-asset is the unit` · **timeout source:** registered *(120s differs from the column default (600s))*


**§19 efficiency ledger** · **p50:** 3s · **p90:** 3s · **worst:** 3s · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• Chart 3 holds zero rows — the rehearsal chart is incomplete for this asset; rebuild there first (Phase 1) so it can serve as the test subject.<br>• Derivation ledger: 6 declared inputs — record which upstream digests each output row was built from (partition receipt) so a wrong answer is traceable to the input that produced it. |
| Rebuild time | • Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• **Not profiled.** Measured baseline only: p50 3s · p90 3s · worst 3s · 11 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 1 direct dependant(s) stop invalidating when this asset rebuilds to identical content. |

### L4 · Phala — 9 assets · 9 non-conformant · 9 P0 · 0 heavy

*Deterministic outcome shaping — phala, remedies, rectification.* Deterministic and inexpensive, but structurally serial — it sits at DAG depths 16–20 and gates all of L5. The win is edge hygiene: removing declared-but-unread dependencies shortens the critical path.


#### `ph_muhurta` — M · Medium deterministic · P0 · Blocking defect · DRAFT

**What:** Personalized auspicious windows: chart-strength + live-transit scored, personal-danger-avoiding, prediction-fused (rides ph_nimitta windows), honest no-good-win  
**Now:** native lit · abhinandan lit · chart3 — · rows 134 / 49 / 0 · median 1s, worst 38s · 43.0% of 107 attempts complete

**domain:** chart · **rung:** R4 · **within-rung wave:** 1 · **continuation class:** restartable-light · **rehearsal partition:** `n/a — single-shot, whole-asset is the unit` · **timeout source:** registered *(10800s differs from the column default (600s))*


**§19 efficiency ledger** · **p50:** 1s · **p90:** 14s · **worst:** 38s · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• Set `target_floor` = 134 (achieved on native; floors are aspirational, never fabricated — §N.4).<br>• Chart 3 holds zero rows — the rehearsal chart is incomplete for this asset; rebuild there first (Phase 1) so it can serve as the test subject.<br>• Derivation ledger: 8 declared inputs — record which upstream digests each output row was built from (partition receipt) so a wrong answer is traceable to the input that produced it. |
| Rebuild time | • Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• Only 43.0% of 107 attempts complete — most wall-clock is human re-dispatch. Error taxonomy + retry (Phase 4) is the fix, not faster code.<br>• DAG depth 17: sits in the serial tail. Audit its 8 declared edges for ones never actually read (Phase 5) — every removed edge is pure wall-clock.<br>• **Not profiled.** Measured baseline only: p50 1s · p90 14s · worst 38s · 107 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Promote to CURRENT or record why it remains DRAFT (Phase 0.8b) — it is built and read by 4 serving surface(s), so it is authoritative in practice. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 2 direct dependant(s) stop invalidating when this asset rebuilds to identical content.<br>• Completion rate rises from 43.0% as transient failures self-heal. |

#### `ph_nimitta` — M · Medium deterministic · P0 · Blocking defect · DRAFT

**What:** Predictive anchors: 8 derivation axes (graph-causal, discovery-seeded, embedding-precedent, dāśā+school consensus, ayanāṃśa-robustness, subsystem) + 5 elevation  
**Now:** native lit · abhinandan lit · chart3 error · rows 139 / 56 / 0 · median 2s, worst 68s · 42.2% of 109 attempts complete

**domain:** chart · **rung:** R4 · **within-rung wave:** 0 · **continuation class:** restartable-light · **rehearsal partition:** `n/a — single-shot, whole-asset is the unit` · **timeout source:** registered *(10800s differs from the column default (600s))*


**§19 efficiency ledger** · **p50:** 2s · **p90:** 46s · **worst:** 68s · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• Set `target_floor` = 139 (achieved on native; floors are aspirational, never fabricated — §N.4).<br>• Chart 3 holds zero rows — the rehearsal chart is incomplete for this asset; rebuild there first (Phase 1) so it can serve as the test subject.<br>• Derivation ledger: 9 declared inputs — record which upstream digests each output row was built from (partition receipt) so a wrong answer is traceable to the input that produced it.<br>• §N.7 narration fidelity: every sentence restates a cited fact_id it reads, never re-derives; add a golden-value test for the narration layer (verified fact ≠ verified prose). |
| Rebuild time | • Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• Fan-out 10: content addressing pays back most here — today any rebuild of this asset, even a no-op, invalidates all 10 dependants.<br>• Only 42.2% of 109 attempts complete — most wall-clock is human re-dispatch. Error taxonomy + retry (Phase 4) is the fix, not faster code.<br>• DAG depth 16: sits in the serial tail. Audit its 9 declared edges for ones never actually read (Phase 5) — every removed edge is pure wall-clock.<br>• **Not profiled.** Measured baseline only: p50 2s · p90 46s · worst 68s · 109 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Promote to CURRENT or record why it remains DRAFT (Phase 0.8b) — it is built and read by 16 serving surface(s), so it is authoritative in practice. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 10 direct dependant(s) stop invalidating when this asset rebuilds to identical content.<br>• Completion rate rises from 42.2% as transient failures self-heal. |

#### `ph_phaladesa` — M · Medium deterministic · P0 · Blocking defect · DRAFT

**What:** Domain result declaration: 7 domains × 1 row  
**Now:** native stale · abhinandan lit · chart3 error · rows 13 / 13 / 0 · median 1s, worst 8s · 39.1% of 110 attempts complete

**domain:** chart · **rung:** R4 · **within-rung wave:** 4 · **continuation class:** restartable-light · **rehearsal partition:** `n/a — single-shot, whole-asset is the unit` · **timeout source:** registered *(10800s differs from the column default (600s))*


**§19 efficiency ledger** · **p50:** 1s · **p90:** 6s · **worst:** 8s · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• Set `target_floor` = 13 (achieved on native; floors are aspirational, never fabricated — §N.4).<br>• Chart 3 holds zero rows — the rehearsal chart is incomplete for this asset; rebuild there first (Phase 1) so it can serve as the test subject.<br>• Derivation ledger: 7 declared inputs — record which upstream digests each output row was built from (partition receipt) so a wrong answer is traceable to the input that produced it.<br>• §N.7 narration fidelity: every sentence restates a cited fact_id it reads, never re-derives; add a golden-value test for the narration layer (verified fact ≠ verified prose). |
| Rebuild time | • Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• Only 39.1% of 110 attempts complete — most wall-clock is human re-dispatch. Error taxonomy + retry (Phase 4) is the fix, not faster code.<br>• DAG depth 20: sits in the serial tail. Audit its 7 declared edges for ones never actually read (Phase 5) — every removed edge is pure wall-clock.<br>• **Not profiled.** Measured baseline only: p50 1s · p90 6s · worst 8s · 110 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Promote to CURRENT or record why it remains DRAFT (Phase 0.8b) — it is built and read by 2 serving surface(s), so it is authoritative in practice. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 1 direct dependant(s) stop invalidating when this asset rebuilds to identical content.<br>• Completion rate rises from 39.1% as transient failures self-heal. |

#### `ph_pramana` — M · Medium deterministic · P0 · Blocking defect · DRAFT

**What:** Unified machine-evaluable falsifiers for every L4 prediction + the L5 onboarding contract + evaluation-staging (no scoring) + portfolio/reverse-calibration chan  
**Now:** native stale · abhinandan lit · chart3 — · rows 139 / 56 / 0 · median 1s, worst 38s · 40.2% of 107 attempts complete

**domain:** chart · **rung:** R4 · **within-rung wave:** 3 · **continuation class:** restartable-light · **rehearsal partition:** `n/a — single-shot, whole-asset is the unit` · **timeout source:** registered *(10800s differs from the column default (600s))*


**§19 efficiency ledger** · **p50:** 1s · **p90:** 17s · **worst:** 38s · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• Set `target_floor` = 139 (achieved on native; floors are aspirational, never fabricated — §N.4).<br>• Chart 3 holds zero rows — the rehearsal chart is incomplete for this asset; rebuild there first (Phase 1) so it can serve as the test subject.<br>• Derivation ledger: 6 declared inputs — record which upstream digests each output row was built from (partition receipt) so a wrong answer is traceable to the input that produced it. |
| Rebuild time | • Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• Only 40.2% of 107 attempts complete — most wall-clock is human re-dispatch. Error taxonomy + retry (Phase 4) is the fix, not faster code.<br>• DAG depth 19: sits in the serial tail. Audit its 6 declared edges for ones never actually read (Phase 5) — every removed edge is pure wall-clock.<br>• **Not profiled.** Measured baseline only: p50 1s · p90 17s · worst 38s · 107 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Promote to CURRENT or record why it remains DRAFT (Phase 0.8b) — it is built and read by 2 serving surface(s), so it is authoritative in practice. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 2 direct dependant(s) stop invalidating when this asset rebuilds to identical content.<br>• Completion rate rises from 40.2% as transient failures self-heal. |

#### `ph_pratikara` — M · Medium deterministic · P0 · Blocking defect · DRAFT

**What:** Managed remedy program: economics/feasibility tiers, sequenced+conflict-free schedule, muhūrta-timed initiation, severity-proportional, cross-tradition choice,   
**Now:** native stale · abhinandan lit · chart3 — · rows 536 / 741 / 0 · median 3s, worst 73s · 43.0% of 107 attempts complete

**domain:** chart · **rung:** R4 · **within-rung wave:** 1 · **continuation class:** restartable-light · **rehearsal partition:** `n/a — single-shot, whole-asset is the unit` · **timeout source:** registered *(10800s differs from the column default (600s))*


**§19 efficiency ledger** · **p50:** 3s · **p90:** 52s · **worst:** 73s · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• Set `target_floor` = 536 (achieved on native; floors are aspirational, never fabricated — §N.4).<br>• Chart 3 holds zero rows — the rehearsal chart is incomplete for this asset; rebuild there first (Phase 1) so it can serve as the test subject.<br>• Derivation ledger: 4 declared inputs — record which upstream digests each output row was built from (partition receipt) so a wrong answer is traceable to the input that produced it.<br>• §N.7 narration fidelity: every sentence restates a cited fact_id it reads, never re-derives; add a golden-value test for the narration layer (verified fact ≠ verified prose). |
| Rebuild time | • Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• Only 43.0% of 107 attempts complete — most wall-clock is human re-dispatch. Error taxonomy + retry (Phase 4) is the fix, not faster code.<br>• DAG depth 17: sits in the serial tail. Audit its 4 declared edges for ones never actually read (Phase 5) — every removed edge is pure wall-clock.<br>• **Not profiled.** Measured baseline only: p50 3s · p90 52s · worst 73s · 107 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Promote to CURRENT or record why it remains DRAFT (Phase 0.8b) — it is built and read by 6 serving surface(s), so it is authoritative in practice. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 2 direct dependant(s) stop invalidating when this asset rebuilds to identical content.<br>• Completion rate rises from 43.0% as transient failures self-heal. |

#### `ph_rectification` — M · Medium deterministic · P0 · Blocking defect · DRAFT

**What:** Birth-time rectification via PyJHora ascendant scan (±90 min, 5-min steps, 5 ayanamshas) scored against pre-2020 LEL events  
**Now:** native lit · abhinandan lit · chart3 — · rows 186 / 186 / 0 · median 1s, worst 34s · 43.0% of 107 attempts complete

**domain:** chart · **rung:** R4 · **within-rung wave:** 1 · **continuation class:** restartable-light · **rehearsal partition:** `n/a — single-shot, whole-asset is the unit` · **timeout source:** registered *(10800s differs from the column default (600s))*


**§19 efficiency ledger** · **p50:** 1s · **p90:** 20s · **worst:** 34s · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• Set `target_floor` = 186 (achieved on native; floors are aspirational, never fabricated — §N.4).<br>• Chart 3 holds zero rows — the rehearsal chart is incomplete for this asset; rebuild there first (Phase 1) so it can serve as the test subject. |
| Rebuild time | • Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• Only 43.0% of 107 attempts complete — most wall-clock is human re-dispatch. Error taxonomy + retry (Phase 4) is the fix, not faster code.<br>• DAG depth 17: sits in the serial tail. Audit its 1 declared edges for ones never actually read (Phase 5) — every removed edge is pure wall-clock.<br>• **Not profiled.** Measured baseline only: p50 1s · p90 20s · worst 34s · 107 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Promote to CURRENT or record why it remains DRAFT (Phase 0.8b) — it is built and read by 3 serving surface(s), so it is authoritative in practice. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• Completion rate rises from 43.0% as transient failures self-heal. |

#### `ph_sankrama` — M · Medium deterministic · P0 · Blocking defect · DRAFT

**What:** Grounded multi-hop cross-domain dynamics: lag from real activation windows + graph-bridge mechanism, A→B→C cascades, cross-domain conflicts, trajectory + mitiga  
**Now:** native lit · abhinandan lit · chart3 — · rows 2,510 / 475 / 0 · median 4s, worst 4m · 43.0% of 107 attempts complete

**domain:** chart · **rung:** R4 · **within-rung wave:** 1 · **continuation class:** restartable-light · **rehearsal partition:** `n/a — single-shot, whole-asset is the unit` · **timeout source:** registered *(10800s differs from the column default (600s))*


**§19 efficiency ledger** · **p50:** 4s · **p90:** 2m · **worst:** 4m · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• Set `target_floor` = 2,510 (achieved on native; floors are aspirational, never fabricated — §N.4).<br>• Cross-chart asymmetry (2,510 vs 475): confirm it is chart-driven, not a partial build on one chart.<br>• Chart 3 holds zero rows — the rehearsal chart is incomplete for this asset; rebuild there first (Phase 1) so it can serve as the test subject. |
| Rebuild time | • Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• Only 43.0% of 107 attempts complete — most wall-clock is human re-dispatch. Error taxonomy + retry (Phase 4) is the fix, not faster code.<br>• DAG depth 17: sits in the serial tail. Audit its 2 declared edges for ones never actually read (Phase 5) — every removed edge is pure wall-clock.<br>• **Not profiled.** Measured baseline only: p50 4s · p90 2m · worst 4m · 107 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Promote to CURRENT or record why it remains DRAFT (Phase 0.8b) — it is built and read by 3 serving surface(s), so it is authoritative in practice. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 2 direct dependant(s) stop invalidating when this asset rebuilds to identical content.<br>• Completion rate rises from 43.0% as transient failures self-heal. |

#### `ph_sodhana` — M · Medium deterministic · P0 · Blocking defect · DRAFT

**What:** Anomaly registry: 5 deterministic detectors (confidence inflation, magnitude drift, falsifier absent, ledger gap, layer leakage)  
**Now:** native lit · abhinandan lit · chart3 — · rows 97 / 41 / 0 · median 0s, worst 11s · 40.2% of 107 attempts complete

**domain:** chart · **rung:** R4 · **within-rung wave:** 1 · **continuation class:** restartable-light · **rehearsal partition:** `n/a — single-shot, whole-asset is the unit` · **timeout source:** registered *(10800s differs from the column default (600s))*


**§19 efficiency ledger** · **p50:** 0s · **p90:** 5s · **worst:** 11s · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• Set `target_floor` = 97 (achieved on native; floors are aspirational, never fabricated — §N.4).<br>• Chart 3 holds zero rows — the rehearsal chart is incomplete for this asset; rebuild there first (Phase 1) so it can serve as the test subject. |
| Rebuild time | • Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• Only 40.2% of 107 attempts complete — most wall-clock is human re-dispatch. Error taxonomy + retry (Phase 4) is the fix, not faster code.<br>• DAG depth 17: sits in the serial tail. Audit its 2 declared edges for ones never actually read (Phase 5) — every removed edge is pure wall-clock.<br>• **Not profiled.** Measured baseline only: p50 0s · p90 5s · worst 11s · 107 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Promote to CURRENT or record why it remains DRAFT (Phase 0.8b) — it is built and read by 2 serving surface(s), so it is authoritative in practice. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 2 direct dependant(s) stop invalidating when this asset rebuilds to identical content.<br>• Completion rate rises from 40.2% as transient failures self-heal. |

#### `ph_suddha_sodhana` — M · Medium deterministic · P0 · Blocking defect · DRAFT

**What:** Cleansed disposition: one row per phala_anchors entry, classified as clean/flagged/staged_revision  
**Now:** native lit · abhinandan lit · chart3 — · rows 139 / 56 / 0 · median 1s, worst 32s · 40.2% of 107 attempts complete

**domain:** chart · **rung:** R4 · **within-rung wave:** 2 · **continuation class:** restartable-light · **rehearsal partition:** `n/a — single-shot, whole-asset is the unit` · **timeout source:** registered *(10800s differs from the column default (600s))*


**§19 efficiency ledger** · **p50:** 1s · **p90:** 11s · **worst:** 32s · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• Set `target_floor` = 139 (achieved on native; floors are aspirational, never fabricated — §N.4).<br>• Chart 3 holds zero rows — the rehearsal chart is incomplete for this asset; rebuild there first (Phase 1) so it can serve as the test subject. |
| Rebuild time | • Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• Only 40.2% of 107 attempts complete — most wall-clock is human re-dispatch. Error taxonomy + retry (Phase 4) is the fix, not faster code.<br>• DAG depth 18: sits in the serial tail. Audit its 2 declared edges for ones never actually read (Phase 5) — every removed edge is pure wall-clock.<br>• **Not profiled.** Measured baseline only: p50 1s · p90 11s · worst 32s · 107 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Promote to CURRENT or record why it remains DRAFT (Phase 0.8b) — it is built and read by 1 serving surface(s), so it is authoritative in practice. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 2 direct dependant(s) stop invalidating when this asset rebuilds to identical content.<br>• Completion rate rises from 40.2% as transient failures self-heal. |

### L5 · Mīmāṃsā — 15 assets · 10 non-conformant · 10 P0 · 0 heavy

*Calibration & judgment — prediction/outcome loop, scoring, review.* The deepest and most cascade-prone layer: eight of its assets were recently blocked by a single upstream fault. Cascade-root collapse and honest partial states matter more here than raw speed.


#### `mi_abhilekha` — S · Service probe · P0 · Blocking defect · DRAFT

**What:** Journal + re-sync service: surfaces due predictions for native feedback, ingests answers as LEL events, triggers L5-only recompute  
**Now:** service · global state n/a · median 0s, worst 2s · 42.6% of 94 attempts complete

**domain:** chart · **rung:** R5 · **within-rung wave:** 2 · **continuation class:** probe-only · **rehearsal partition:** `n/a — service probe` · **timeout source:** registered *(10800s differs from the column default (600s))*


**§19 efficiency ledger** · **p50:** 0s · **p90:** 1s · **worst:** 2s · **rows/sec:** null · **bound class:** not-a-build · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: service probe — there is no build to measure (structural). rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Real liveness + correctness probe with an SLO (not just "responds"): exercise one known-answer query and compare against a pinned expected value; alert on drift or timeout. |
| Rebuild time | • Not a build; nothing to speed up. Exclude from build plans and ETA math. |
| Re-architecture & alignment | • Promote to CURRENT or record why it remains DRAFT (Phase 0.8b) — it is built and read by 1 serving surface(s), so it is authoritative in practice.<br>• Move to the service lane with `health_probe` + `provides_apis`; `count_sql` must be null. |
| Expected benefit | • A degraded service surfaces in minutes, not months (one sat red for 66 days). |

#### `mi_adhilepa` — M · Medium deterministic · P0 · Blocking defect · DRAFT

**What:** L5 learned-weight overlay on L1–L4 base values; 4 adjustment tables + load-bearing sensitivity map (G3)  
**Now:** native error · abhinandan lit · chart3 error · rows 112,270 / 112,481 / 0 · median 10s, worst 14m · 39.3% of 107 attempts complete

**domain:** chart · **rung:** R5 · **within-rung wave:** 4 · **continuation class:** restartable-light · **rehearsal partition:** `n/a — single-shot, whole-asset is the unit` · **timeout source:** registered *(10800s differs from the column default (600s))*


**§19 efficiency ledger** · **p50:** 10s · **p90:** 24s · **worst:** 14m · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• Chart 3 holds zero rows — the rehearsal chart is incomplete for this asset; rebuild there first (Phase 1) so it can serve as the test subject.<br>• Derivation ledger: 5 declared inputs — record which upstream digests each output row was built from (partition receipt) so a wrong answer is traceable to the input that produced it. |
| Rebuild time | • Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• Only 39.3% of 107 attempts complete — most wall-clock is human re-dispatch. Error taxonomy + retry (Phase 4) is the fix, not faster code.<br>• DAG depth 24: sits in the serial tail. Audit its 5 declared edges for ones never actually read (Phase 5) — every removed edge is pure wall-clock.<br>• **Not profiled.** Measured baseline only: p50 10s · p90 24s · worst 14m · 107 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Promote to CURRENT or record why it remains DRAFT (Phase 0.8b) — it is built and read by 1 serving surface(s), so it is authoritative in practice. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 2 direct dependant(s) stop invalidating when this asset rebuilds to identical content.<br>• Completion rate rises from 39.3% as transient failures self-heal. |

#### `mi_bhavisya` — M · Medium deterministic · P0 · Blocking defect · DRAFT

**What:** Time-indexed prospective predictions with confidence + falsifiers  
**Now:** native error · abhinandan lit · chart3 — · rows 278 / 112 / 0 · median 2s, worst 16s · 41.0% of 105 attempts complete

**domain:** chart · **rung:** R5 · **within-rung wave:** 1 · **continuation class:** restartable-light · **rehearsal partition:** `n/a — single-shot, whole-asset is the unit` · **timeout source:** registered *(10800s differs from the column default (600s))*


**§19 efficiency ledger** · **p50:** 2s · **p90:** 6s · **worst:** 16s · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• Chart 3 holds zero rows — the rehearsal chart is incomplete for this asset; rebuild there first (Phase 1) so it can serve as the test subject.<br>• Derivation ledger: 6 declared inputs — record which upstream digests each output row was built from (partition receipt) so a wrong answer is traceable to the input that produced it. |
| Rebuild time | • Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• Only 41.0% of 105 attempts complete — most wall-clock is human re-dispatch. Error taxonomy + retry (Phase 4) is the fix, not faster code.<br>• DAG depth 21: sits in the serial tail. Audit its 6 declared edges for ones never actually read (Phase 5) — every removed edge is pure wall-clock.<br>• **Not profiled.** Measured baseline only: p50 2s · p90 6s · worst 16s · 105 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Promote to CURRENT or record why it remains DRAFT (Phase 0.8b) — it is built and read by 8 serving surface(s), so it is authoritative in practice. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 3 direct dependant(s) stop invalidating when this asset rebuilds to identical content.<br>• Completion rate rises from 41.0% as transient failures self-heal. |

#### `mi_darshana` — M · Medium deterministic · P0 · Blocking defect · DRAFT

**What:** LLM-ready pre-composed insight units with embeddings + provenance chains + trust metadata (R1–R6)  
**Now:** native error · abhinandan lit · chart3 error · rows 115 / 35 / 0 · median 1s, worst 6s · 36.1% of 108 attempts complete

**domain:** chart · **rung:** R5 · **within-rung wave:** 5 · **continuation class:** resumable-substep · **rehearsal partition:** `insight_units | embeddings` · **timeout source:** registered *(10800s differs from the column default (600s))*


**§19 efficiency ledger** · **p50:** 1s · **p90:** 5s · **worst:** 6s · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• Cross-chart asymmetry (115 vs 35): confirm it is chart-driven, not a partial build on one chart.<br>• Chart 3 holds zero rows — the rehearsal chart is incomplete for this asset; rebuild there first (Phase 1) so it can serve as the test subject.<br>• Derivation ledger: 8 declared inputs — record which upstream digests each output row was built from (partition receipt) so a wrong answer is traceable to the input that produced it.<br>• §N.7 narration fidelity: every sentence restates a cited fact_id it reads, never re-derives; add a golden-value test for the narration layer (verified fact ≠ verified prose).<br>• Embeddings are a deterministic transform (permitted). Pin the model id + dimension in the output digest so a model change invalidates correctly. |
| Rebuild time | • Has a substep plan (`insight_units \| embeddings`) but runs in 1s — resumption is irrelevant here; per-substep input digests still matter because they give partition-scoped early cutoff downstream.<br>• Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• Only 36.1% of 108 attempts complete — most wall-clock is human re-dispatch. Error taxonomy + retry (Phase 4) is the fix, not faster code.<br>• DAG depth 25: sits in the serial tail. Audit its 8 declared edges for ones never actually read (Phase 5) — every removed edge is pure wall-clock.<br>• **Not profiled.** Measured baseline only: p50 1s · p90 5s · worst 6s · 108 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Promote to CURRENT or record why it remains DRAFT (Phase 0.8b) — it is built and read by 4 serving surface(s), so it is authoritative in practice. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• Completion rate rises from 36.1% as transient failures self-heal. |

#### `mi_gunanaka` — M · Medium deterministic · P0 · Blocking defect · DRAFT

**What:** Empirical multiplier weights learned from calibration outcomes  
**Now:** native error · abhinandan lit · chart3 — · rows 13 / 10 / 0 · median 0s, worst 2s · 41.1% of 107 attempts complete

**domain:** chart · **rung:** R5 · **within-rung wave:** 3 · **continuation class:** restartable-light · **rehearsal partition:** `n/a — single-shot, whole-asset is the unit` · **timeout source:** registered *(10800s differs from the column default (600s))*


**§19 efficiency ledger** · **p50:** 0s · **p90:** 2s · **worst:** 2s · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• Chart 3 holds zero rows — the rehearsal chart is incomplete for this asset; rebuild there first (Phase 1) so it can serve as the test subject. |
| Rebuild time | • Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• Only 41.1% of 107 attempts complete — most wall-clock is human re-dispatch. Error taxonomy + retry (Phase 4) is the fix, not faster code.<br>• DAG depth 23: sits in the serial tail. Audit its 3 declared edges for ones never actually read (Phase 5) — every removed edge is pure wall-clock.<br>• **Not profiled.** Measured baseline only: p50 0s · p90 2s · worst 2s · 107 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Promote to CURRENT or record why it remains DRAFT (Phase 0.8b) — it is built and read by 7 serving surface(s), so it is authoritative in practice. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 2 direct dependant(s) stop invalidating when this asset rebuilds to identical content.<br>• Completion rate rises from 41.1% as transient failures self-heal. |

#### `mi_kula` — G · Global substrate · P0 · Blocking defect · DRAFT

**What:** Signal-family registry + negative-control battery — the governing catalogue of what influences a reading  
**Now:** global · lit · 15 rows · median 0s, worst 2s · 88.4% of 43 attempts complete

**domain:** shared · **rung:** R5 · **within-rung wave:** 0 · **continuation class:** restartable-light · **rehearsal partition:** `n/a — single-shot, whole-asset is the unit` · **timeout source:** registered *(10800s differs from the column default (600s))*


**§19 efficiency ledger** · **p50:** 0s · **p90:** 1s · **worst:** 2s · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count = expected volume formula AND no duplicate natural keys`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8). |
| Rebuild time | • Built once, reused by every chart. Publish `substrate_version` + output digest; per-chart consumers record the version they read, so a no-op rebuild here never cascades.<br>• **Not profiled.** Measured baseline only: p50 0s · p90 1s · worst 2s · 43 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Promote to CURRENT or record why it remains DRAFT (Phase 0.8b) — it is built and read by 1 serving surface(s), so it is authoritative in practice.<br>• Keep out of per-chart plans but expose completion to the per-chart readiness gate uniformly (the migration-563 class of bug, made structural). |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 4 direct dependant(s) stop invalidating when this asset rebuilds to identical content. |

#### `mi_pariksha` — M · Medium deterministic · P0 · Blocking defect · DRAFT

**What:** Answer quality evaluation runs — automated + human QA over synthesis outputs  
**Now:** native error · abhinandan lit · chart3 error · rows 1,664 / 6 / 0 · median 2s, worst 33s · 39.6% of 106 attempts complete

**domain:** chart · **rung:** R5 · **within-rung wave:** 3 · **continuation class:** resumable-substep · **rehearsal partition:** `retrodiction | control_windows | …(7)` · **timeout source:** registered *(10800s differs from the column default (600s))*


**§19 efficiency ledger** · **p50:** 2s · **p90:** 9s · **worst:** 33s · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• Cross-chart asymmetry (1,664 vs 6): confirm it is chart-driven, not a partial build on one chart.<br>• Chart 3 holds zero rows — the rehearsal chart is incomplete for this asset; rebuild there first (Phase 1) so it can serve as the test subject. |
| Rebuild time | • Has a substep plan (`retrodiction \| control_windows \| …(7)`) but runs in 2s — resumption is irrelevant here; per-substep input digests still matter because they give partition-scoped early cutoff downstream.<br>• Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• Only 39.6% of 106 attempts complete — most wall-clock is human re-dispatch. Error taxonomy + retry (Phase 4) is the fix, not faster code.<br>• DAG depth 23: sits in the serial tail. Audit its 3 declared edges for ones never actually read (Phase 5) — every removed edge is pure wall-clock.<br>• **Not profiled.** Measured baseline only: p50 2s · p90 9s · worst 33s · 106 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Promote to CURRENT or record why it remains DRAFT (Phase 0.8b) — it is built and read by 2 serving surface(s), so it is authoritative in practice. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 2 direct dependant(s) stop invalidating when this asset rebuilds to identical content.<br>• Completion rate rises from 39.6% as transient failures self-heal. |

#### `mi_pramana` — M · Medium deterministic · P0 · Blocking defect · DRAFT

**What:** Prediction outcome calibration records — confidence score vs outcome mapping  
**Now:** native error · abhinandan lit · chart3 — · rows 63 / 0 / 0 · median 0s, worst 4s · 41.0% of 105 attempts complete

**domain:** chart · **rung:** R5 · **within-rung wave:** 2 · **continuation class:** resumable-substep · **rehearsal partition:** `match | score | …(3)` · **timeout source:** registered *(10800s differs from the column default (600s))*


**§19 efficiency ledger** · **p50:** 0s · **p90:** 4s · **worst:** 4s · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• Chart 3 holds zero rows — the rehearsal chart is incomplete for this asset; rebuild there first (Phase 1) so it can serve as the test subject.<br>• Derivation ledger: 4 declared inputs — record which upstream digests each output row was built from (partition receipt) so a wrong answer is traceable to the input that produced it. |
| Rebuild time | • Has a substep plan (`match \| score \| …(3)`) but runs in 0s — resumption is irrelevant here; per-substep input digests still matter because they give partition-scoped early cutoff downstream.<br>• Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• Only 41.0% of 105 attempts complete — most wall-clock is human re-dispatch. Error taxonomy + retry (Phase 4) is the fix, not faster code.<br>• DAG depth 22: sits in the serial tail. Audit its 4 declared edges for ones never actually read (Phase 5) — every removed edge is pure wall-clock.<br>• **Not profiled.** Measured baseline only: p50 0s · p90 4s · worst 4s · 105 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Promote to CURRENT or record why it remains DRAFT (Phase 0.8b) — it is built and read by 11 serving surface(s), so it is authoritative in practice. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 4 direct dependant(s) stop invalidating when this asset rebuilds to identical content.<br>• Completion rate rises from 41.0% as transient failures self-heal. |

#### `mi_sambandha` — M · Medium deterministic · P0 · Blocking defect · DRAFT

**What:** Per-native grammar of how each signal/house/karaka expresses — which channel fires for THIS person (G2)  
**Now:** native error · abhinandan lit · chart3 — · rows 24 / 23 / 0 · median 0s, worst 5s · 40.0% of 105 attempts complete

**domain:** chart · **rung:** R5 · **within-rung wave:** 4 · **continuation class:** restartable-light · **rehearsal partition:** `n/a — single-shot, whole-asset is the unit` · **timeout source:** registered *(10800s differs from the column default (600s))*


**§19 efficiency ledger** · **p50:** 0s · **p90:** 2s · **worst:** 5s · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• Chart 3 holds zero rows — the rehearsal chart is incomplete for this asset; rebuild there first (Phase 1) so it can serve as the test subject. |
| Rebuild time | • Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• Only 40.0% of 105 attempts complete — most wall-clock is human re-dispatch. Error taxonomy + retry (Phase 4) is the fix, not faster code.<br>• DAG depth 24: sits in the serial tail. Audit its 3 declared edges for ones never actually read (Phase 5) — every removed edge is pure wall-clock.<br>• **Not profiled.** Measured baseline only: p50 0s · p90 2s · worst 5s · 105 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Promote to CURRENT or record why it remains DRAFT (Phase 0.8b) — it is built and read by 2 serving surface(s), so it is authoritative in practice. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 1 direct dependant(s) stop invalidating when this asset rebuilds to identical content.<br>• Completion rate rises from 40.0% as transient failures self-heal. |

#### `mi_sankalpa` — M · Medium deterministic · P0 · Blocking defect · DRAFT

**What:** Unified intervention ledger — every elected act (upāya · yajña · elected activity) with its adjudication record, predicted differential, performance attestation  
**Now:** native dormant · abhinandan — · chart3 — · rows 0 / 0 / 0 · median 1s, worst 2s · 50.0% of 10 attempts complete

**domain:** chart · **rung:** R5 · **within-rung wave:** 0 · **continuation class:** restartable-light · **rehearsal partition:** `n/a — single-shot, whole-asset is the unit` · **timeout source:** registered *(300s differs from the column default (600s))*


**§19 efficiency ledger** · **p50:** 1s · **p90:** 2s · **worst:** 2s · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• Zero rows on the native chart. Either the asset is empty by design (record it in `volume_explanation`) or it has never been built — the cockpit must not render this as lit. |
| Rebuild time | • Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• DAG depth 12: sits in the serial tail. Audit its 1 declared edges for ones never actually read (Phase 5) — every removed edge is pure wall-clock.<br>• **Not profiled.** Measured baseline only: p50 1s · p90 2s · worst 2s · 10 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Promote to CURRENT or record why it remains DRAFT (Phase 0.8b) — it is built and read by 2 serving surface(s), so it is authoritative in practice. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it. |

#### `mi_seva` — S · Service probe · P1 · High · DRAFT

**What:** Serve-time contribution-control gateway: effective-value resolution, toggle gates, transit-current binding, MCP parity  
**Now:** service · global state n/a · median 0s, worst 2s · 40.2% of 97 attempts complete

**domain:** chart · **rung:** R5 · **within-rung wave:** 5 · **continuation class:** probe-only · **rehearsal partition:** `n/a — service probe` · **timeout source:** registered *(10800s differs from the column default (600s))*


**§19 efficiency ledger** · **p50:** 0s · **p90:** 2s · **worst:** 2s · **rows/sec:** null · **bound class:** not-a-build · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: service probe — there is no build to measure (structural). rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Real liveness + correctness probe with an SLO (not just "responds"): exercise one known-answer query and compare against a pinned expected value; alert on drift or timeout. |
| Rebuild time | • Not a build; nothing to speed up. Exclude from build plans and ETA math. |
| Re-architecture & alignment | • Move to the service lane with `health_probe` + `provides_apis`; `count_sql` must be null. |
| Expected benefit | • A degraded service surfaces in minutes, not months (one sat red for 66 days). |

#### `lel_events` — M · Medium deterministic · P3 · Standard · SOURCE

**What:** Per-chart user-authored life-event corpus (occurrence + recording dates, chart-state index)  
**Now:** native — · abhinandan — · chart3 — · rows 64 / 0 / 0

**domain:** chart · **rung:** R5 · **within-rung wave:** 0 · **continuation class:** restartable-light · **rehearsal partition:** `n/a — single-shot, whole-asset is the unit` · **timeout source:** default *(600s equals the asset_registry column default and the runner fallback (_WRITER_TIMEOUT_SECONDS) — indistinguishable from never set)*


**§19 efficiency ledger** · **p50:** null · **p90:** null · **worst:** null · **rows/sec:** null · **bound class:** not-a-build · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: no registered writer — nothing builds this asset (structural). rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• Chart 3 holds zero rows — the rehearsal chart is incomplete for this asset; rebuild there first (Phase 1) so it can serve as the test subject. |
| Rebuild time | • No completed-run telemetry: p50 and p90 are both unmeasured, so even the §19.4 build-cost baseline is null here — measure before planning anything.<br>• No registered writer: nothing builds this asset, so there is no build cost to profile. Bound class `not-a-build` (§19.4 step 3) — hotspot is null by structure, not by omission. |
| Re-architecture & alignment | • Contract-conformant. Inherits the platform-wide changes: content digest, graded staleness, shared resumability. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it. |

#### `mi_bhara` — M · Medium deterministic · P3 · Standard · DRAFT

**What:** Stage 9 of the temporal-field pipeline: fits the hazard field's weights against this chart's recorded life events (blocked forward-chaining CV, shrinkage to the  
**Now:** native error · abhinandan error · chart3 — · rows 7 / 0 / 0 · median 2s, worst 10m · 53.1% of 64 attempts complete

**domain:** chart · **rung:** R5 · **within-rung wave:** 0 · **continuation class:** restartable-light · **rehearsal partition:** `n/a — single-shot, whole-asset is the unit` · **timeout source:** registered *(10800s differs from the column default (600s))*


**§19 efficiency ledger** · **p50:** 2s · **p90:** 5s · **worst:** 10m · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• Set `target_floor` = 7 (achieved on native; floors are aspirational, never fabricated — §N.4).<br>• Chart 3 holds zero rows — the rehearsal chart is incomplete for this asset; rebuild there first (Phase 1) so it can serve as the test subject. |
| Rebuild time | • Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• DAG depth 12: sits in the serial tail. Audit its 1 declared edges for ones never actually read (Phase 5) — every removed edge is pure wall-clock.<br>• **Not profiled.** Measured baseline only: p50 2s · p90 5s · worst 10m · 64 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Contract-conformant. Inherits the platform-wide changes: content digest, graded staleness, shared resumability. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it. |

#### `mi_jivanaghatana` — M · Medium deterministic · P3 · Standard · DRAFT

**What:** LEL — held-out event log isolated from generation; ground truth for prediction calibration  
**Now:** native lit · abhinandan lit · chart3 — · rows 64 / 0 / 0 · median 0s, worst 23s · 78.8% of 52 attempts complete

**domain:** chart · **rung:** R5 · **within-rung wave:** 0 · **continuation class:** restartable-light · **rehearsal partition:** `n/a — single-shot, whole-asset is the unit` · **timeout source:** registered *(10800s differs from the column default (600s))*


**§19 efficiency ledger** · **p50:** 0s · **p90:** 2s · **worst:** 23s · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• Chart 3 holds zero rows — the rehearsal chart is incomplete for this asset; rebuild there first (Phase 1) so it can serve as the test subject. |
| Rebuild time | • Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• **Not profiled.** Measured baseline only: p50 0s · p90 2s · worst 23s · 52 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Contract-conformant. Inherits the platform-wide changes: content digest, graded staleness, shared resumability. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 3 direct dependant(s) stop invalidating when this asset rebuilds to identical content. |

#### `mi_vistara` — G · Global substrate · P3 · Standard · DRAFT

**What:** Audit log of all synthesis export events (PDF, JSON, MCP bundles)  
**Now:** global · lit · 0 rows · median 0s, worst 2s · 86.4% of 44 attempts complete

**domain:** shared · **rung:** R5 · **within-rung wave:** 0 · **continuation class:** restartable-light · **rehearsal partition:** `n/a — single-shot, whole-asset is the unit` · **timeout source:** registered *(10800s differs from the column default (600s))*


**§19 efficiency ledger** · **p50:** 0s · **p90:** 1s · **worst:** 2s · **rows/sec:** null · **bound class:** null · **hotspot:** null · **technique:** null · **target:** null · **speedup achieved:** null · **identity proof:** null · **profiled:** no  
*Basis: NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); hotspot, technique, target, achieved and identity proof are null until it runs (§19.4 step 1, §15). bound class: not profiled — §19.4 step 1: no measured hotspot, no classification. rows/sec: no per-run row count exists (build_run_assets has no rows column) and p50 spans all charts — not derivable from current telemetry; M3 profile supplies it.*

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count = expected volume formula AND no duplicate natural keys`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• Structural-mode L5 asset: zero rows is by design until outcome data accrues. Record that in `volume_explanation` and set `target_floor = 0` so the cockpit renders "0 rows (by design)" rather than dormant. |
| Rebuild time | • Built once, reused by every chart. Publish `substrate_version` + output digest; per-chart consumers record the version they read, so a no-op rebuild here never cascades.<br>• **Not profiled.** Measured baseline only: p50 0s · p90 1s · worst 2s · 44 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Keep out of per-chart plans but expose completion to the per-chart readiness gate uniformly (the migration-563 class of bug, made structural). |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it. |
<!-- ASSET_PLANS:END -->

---

## §16 — Control workbook

`NIRMANA_ASSET_CONTROL_WORKBOOK_v4_1.xlsx`, regenerated in M0: v3.0's nine sheets with the
per-chart columns collapsed to the chart plus the substrate, the six §15 columns added to the
Asset Register, a new **Rung Board** sheet (per-rung conformance / lit / integrity-passed /
frozen state — the source for §12's rung board and the home of each freeze record), a new
**Efficiency** sheet (per asset: p50/p90 baseline, rows/sec, bound class, hotspot, technique,
target, achieved, identity proof — the §19 ledger), and the loophole register L-01…L-12 folded
into the Defect Register as D-17…D-28. Generated, never
hand-edited; re-run after each Track-M campaign and at each rung freeze.

---

## §17 — Risks, coordination, and adjacent debris

- **Freeze exception** (I3) gates M1–M3 orchestrator internals; M0 needs none. The writer
  contract is untouched throughout — every mechanism here lives orchestrator-side.
- **The rename (I9) is the riskiest migration class.** `scope='global'` is written by the runs
  route and read by the planner, the runner, and the workbook tooling. It ships behind a compat
  window with both values readable, one deploy apart from the writer flip, and is exercised on
  a `verify` dispatch before any building dispatch.
- **No rehearsal chart** is the scope ruling's real cost. I8's three substitutes (§6.10) are
  the mitigation, and they are stronger in one respect — they exercise the real data — and
  weaker in another: a mistake lands on the only chart there is. This makes I2's verified
  snapshot non-negotiable rather than advisory, and makes stage 3 of every rung (§8.6) the
  place where discipline is actually tested. If the cost ever reads as too high, a disposable
  rehearsal chart is an additive configuration change, not a redesign.
- **Run groups change dispatch shape**; the M-14 SERIALIZABLE gate must extend to group level
  (two overlapping groups dispatched at once) — covered in M1 acceptance.
- **Continuation re-enters committed work** (§7.2); §N.3 idempotency is the safety net and the
  determinism harness (M3) the detector. Until M3, continued runs are verified by row count +
  integrity check rather than digest equality.
- **The ladder is long, and the temptation to jump is real.** I13's guard is deliberately in
  three places — the planner (refusal with a reason), the Console (§6.9), and the rung board —
  because a discipline enforced only in a document is not enforced.
- **Autonomy's characteristic failure is not a crash, it is a confident wrong answer** that
  nothing catches because the thing that would have caught it is the same agent. I16 is the
  structural mitigation and it is worth more than any amount of prompt caution: builder,
  verifier and signatory are three different agents, and the verifier is pointed at the
  database rather than at the builder's account of the database.
- **Delegated authority drifts** unless it is written down before it is used. Every ADHIKĀRIN
  ruling is appended with its evidence and binds later agents as precedent (§18.3); a ruling
  that reverses an earlier one must say so. Drift then shows up as a contradiction in the
  ledger, which is auditable, rather than as an inconsistency in behaviour, which is not.
- **Anti-idle is the most likely way I13 gets breached** — an agent with nothing to do is an
  agent looking for the next layer. §18.6 closes it by making idle-time work pullable only
  from a pre-authorized, layer-independent Standing Queue, with additions gated by ADHIKĀRIN.
- **A parked item is not a failure**, and the fleet must never treat it as one by working
  around the fence. PARKED entries are the campaign's honest surface for "only the native can
  settle this"; an agent that decides a reserved question because parking felt like failure
  has broken I15 more seriously than any wrong build.
- **Optimization is the easiest place to lose data quietly.** A writer rewritten for speed that
  produces subtly different rows is worse than a slow writer, and the difference will not show
  up as an error — it shows up as a number nobody questions. I18's identity proof is the whole
  defence, and it is why §19 could not ship before M3's determinism harness existed.
- **Premature and misdirected optimization** is the other failure: an autonomous fleet will
  happily spend a week making a 3-second step faster. §19.4 step 1 (no measured hotspot, no
  optimization) and §19.6's concentration on the ten heavy assets are the controls.
- **Coordination**: claim a lease and migration numbers in `CAMPAIGN_COORDINATION.md` before
  any shared write; PARIPRAŚNA P3 coordination is unchanged from v3.0. Under autonomy the
  lease is claimed by SŪTRADHĀRA and released by LEKHAKA at the unit of work, never held
  across a rung.
- **Adjacent governance debris**, carried verbatim from v3.0 §15 — not in scope but on the
  path: `CURRENT_STATE` §2 is behind reality for three campaigns; three campaigns wrote no
  SESSION_LOG entries; the production MCP key in `.codex/config.toml` is unrotated (P0-2);
  `CAMPAIGN_COORDINATION.md` on `main` is behind the live branch; this plan's own artifacts are
  uncommitted.

---

## §18 — Autonomous execution *(new in v4.2)*

### 18.1 — What "no human gates" means, and the one thing it cannot mean

The campaign runs unattended: no step waits on Abhisek, no rung waits for a review window, and
nothing pauses because a question was asked. Every decision this plan calls for — promote or
retire a DRAFT asset, reset a stale floor, record a deferral, approve a clear, sign a rung
freeze — has an authority that is awake and reachable in-process: the **ADHIKĀRIN** agent,
holding the native's authority under a written charter (§18.3).

What it cannot mean is that *no* decision is reserved. Three classes of act cannot be
delegated to any agent without the delegation becoming meaningless:

- acts that are **irreversible and uninsurable** — the standing example is `ka_gochara_sweep`'s
  38,287 v1 rows, which have no writer and whose only recovery is one snapshot (I2);
- acts that **leave the mandate** — anything outside chart `482012f1` and the shared substrate,
  anything touching production credentials, anything altering the frozen writer contract (I3);
- acts that **spend past a ceiling** the native set (§18.9).

For these the charter's answer is not "decide carefully" but **PARK**: set the item aside with
a written decision request, and carry on with everything else. Parking is not blocking — I17
makes it the fleet's cheapest operation. The practical result is a campaign that runs for weeks
without Abhisek, and hands him a short, specific list of things only he can settle, each with
the evidence already gathered and the work around it already done.

### 18.2 — The roster

Six roles. Sanskrit names follow the corpus convention (§N.1's external lexicon discipline).

| Agent | Role | Model · effort | Lifetime | Writes to |
|---|---|---|---|---|
| **SŪTRADHĀRA** — the conductor | Owns `CAMPAIGN_STATE.json`; sequences Track M then the rungs; enforces I13/I14 at dispatch; spawns KĀRAKA per task; the one interactive pane Abhisek can talk to | Opus 5 · high | Long-lived | State, work queue, git branch |
| **ADHIKĀRIN** — the authority | Stands in for the native. Answers every clarification, adjudicates every decision, unblocks, grants charter-scoped approvals, countersigns freezes, PARKS reserved powers | Opus 5 · high | Long-lived | `DECISIONS.jsonl`, `PARKED.jsonl`, signatures |
| **KĀRAKA** — the implementers | Write code, migrations, integrity SQL, writers; profile and optimize implementations (§19); run builds. Spawned per task, worktree-isolated when they touch files in parallel. Never certify their own output | Opus 5 · high | Per task | Code, migrations, build dispatch |
| **PARĪKṢAKA** — the verifier | Independent adversarial verification against live production: integrity checks, completeness, digests, **optimization output-identity proofs (I18)**, acceptance criteria, rung-gate evidence. Reads the artifact and the database, not the builder's report | Opus 5 · high | Long-lived | `VERDICTS.jsonl`, gate evidence |
| **PRAHARĪ** — the monitor | Liveness, stall detection, run-state polling, mailbox SLA, anti-idle dispatch from the Standing Queue, fleet restart. Rule-driven, not judgment-driven; escalates ambiguity | Sonnet · medium | Long-lived loop | `HEARTBEAT.jsonl`, wake signals |
| **LEKHAKA** — the scribe | Run ledger, session log, freeze records, workbook regeneration, `CURRENT_STATE`/memory updates, the daily digest Abhisek reads | Sonnet · medium | Long-lived | Ledgers, workbook, docs |

KĀRAKA is plural by design and the only role that scales with load; the concurrency cap is the
connection budget (§18.9), not the agent count.

### 18.3 — Delegated authority: what ADHIKĀRIN may decide

The charter (`00_ARCHITECTURE/autonomy/CHARTER.md`) is the instrument; §18.3 is its summary.
ADHIKĀRIN holds standing authority to decide, without asking anyone:

1. **Catalogue dispositions** — promote a DRAFT asset to CURRENT, retire it with a
   `data_disposition`, or reclassify it `SOURCE`, for any of the 47 DRAFT rows and the 13
   zero-consumer assets, on the evidence M0's census produces.
2. **Floors and integrity invariants** — set any `target_floor` to its measured achieved count
   (I7), reset a floor found to be a stale historical figure, accept or reject an
   `integrity_check_sql` a KĀRAKA proposes, and classify a zero-row asset as by-design or
   unbuilt.
3. **The freeze exception, pre-granted** — orchestrator-internal changes named in §10 are
   authorized in advance. ADHIKĀRIN confirms a specific change falls inside that scope; it may
   not widen the scope.
4. **Destructive operations within the mandate** — approve a `clear+rebuild` on the chart or on
   shared assets, including the L0 double-confirm, provided I2's verified snapshot exists and
   I8's `verify` dry run and partition-scale first execution have both passed. The snapshot's
   restore verification is a *precondition it must check*, not a claim it may accept.
5. **Deferrals** — record a deferral (the F-52 rematerialization decision is the named case)
   with its reason, so the cockpit stops showing green on an undecided question.
6. **Rung freezes** — countersign a freeze on PARĪKṢAKA's evidence (I16), or refuse one and
   send the rung back with named gaps.
7. **Optimizations (G11)** — approve an implementation optimization, bounded strictly by its
   output-identity proof (I18). An optimization whose output differs — however favourably — is
   not G11's to approve; it is a correctness decision and is parked.
8. **Blocker adjudication** — rule on any KĀRAKA/PARĪKṢAKA disagreement, any "should I?"
   question, and any plan ambiguity, recording the ruling in `DECISIONS.jsonl` as durable
   precedent that binds later agents.

Every ruling is written before it is acted on, cites the evidence it rests on, and is appended
immutably. A ruling that contradicts an earlier one must say so and say why — the ledger is the
campaign's case law, and the plan's own doctrine (§N.7/§N.8) forbids a claim without a detector
behind it just as firmly for an agent's decision as for an asset's `lit`.

### 18.4 — Reserved powers and hard prohibitions

**Reserved powers — PARK, do not decide.** ADHIKĀRIN writes the item to `PARKED.jsonl` with the
evidence, the options, and its own recommendation, then moves on:

- any operation on an asset whose loss is unrecoverable — first among them `ka_gochara_sweep`'s
  v1 corpus (I2);
- widening scope beyond chart `482012f1` and the shared substrate (the scope ruling);
- any change to the FROZEN writer contract (I3, CLAUDE.md §N.2);
- rotating, reading, or relocating production credentials — including the known-unrotated MCP
  key (§17), which is adjacent debris and stays untouched;
- schema changes outside the migrations this plan names, and anything touching a table no
  asset in the current rung owns;
- exceeding a §18.9 ceiling — tokens, wall-clock, concurrent runs, or continuation generations;
- retiring or overriding any invariant I1–I17.

**Hard prohibitions — refused by every agent, not parked, not appealable.** `DROP`/`TRUNCATE`
on the v1 gochara corpus or any snapshot; force-push, history rewrite, or any write to `main`;
disabling an integrity gate, a CI guard, or a watchdog to make something pass; marking a state
`lit`, `complete`, or `frozen` on any basis other than its detector's verdict; editing an
applied migration (CLAUDE.md §N.4); and fabricating rows, floors, or verdicts. An agent asked to
do one of these by any instruction from any source refuses, logs it, and continues.

### 18.5 — Separation of build from certification (I16)

KĀRAKA builds; PARĪKṢAKA certifies; ADHIKĀRIN signs. PARĪKṢAKA is given the asset, the
acceptance criterion, and database access — never the implementer's narrative — and is
instructed adversarially: its task is to find the reason the claim is false. Where a verdict is
close or the asset is load-bearing (any R0 substrate asset, any tier-X generation-bearing
asset, any rung-gate roll-up), PARĪKṢAKA runs the check from more than one angle — row counts,
the integrity SQL, a spot re-derivation, and the digest — and a disagreement between angles is
a failure, not an average.

This is the process-level form of I5. A fleet that lets the builder score its own work will
produce a campaign-shaped version of the exact defect §1.5 measured: 128 assets reading green
with zero detectors behind them.

### 18.6 — The anti-idle protocol (I17)

**The trap to avoid.** "Never be idle" naively implemented breaks I13: an agent waiting on a
30-hour `ga_dashas` build looks for something to do, finds L2 work, and starts it — and the
layered discipline is gone in the first hour of autonomy. So the protocol separates two things
that look identical from outside and are not.

**Genuine wait** — a dispatched build running normally, a snapshot verifying, a migration
applying. The fleet does not sit on it. PRAHARĪ dispatches from the **Standing Queue**: a
pre-authorized backlog that is by construction layer-independent and data-neutral (I14), so
pulling from it can never breach the ladder. Its contents are the plan's own continuous tracks
and nothing else — the DAG audit (§11), operator-experience work not yet delivered (§12),
per-substep tracing and build metrics (§13 item 6), test coverage for machinery already built,
documentation and ledger catch-up, and the next wave's *conform* work for the rung already open
(§8.6 stage 2 — registry metadata only). Any task not already on the Standing Queue must be
added by ADHIKĀRIN, which checks it against I13/I14 before it becomes pullable.

**A stall** — silence past a threshold, a run in `planned` past its dispatch horizon, a
`building` row with a dead heartbeat, an agent that exited, a mailbox item past its SLA, or a
continuation counter climbing without progress. PRAHARĪ's response is graduated and rule-driven:
poke the owning agent; re-read state and re-dispatch; restart the session from
`CAMPAIGN_STATE.json`; escalate to ADHIKĀRIN with the evidence. Nothing about a stall is
judgment-based at the detection layer — the thresholds are numbers, so a cheap model can run
the loop honestly and only ambiguity is escalated.

**The parked item** never stalls anything: the thread it belongs to is set aside and the
campaign continues down every other path that does not depend on it.

### 18.7 — Coordination substrate

Agents coordinate through the filesystem, on the campaign branch, because a durable, greppable,
append-only record is what this corpus's governance already demands of humans and because it
survives any agent dying mid-sentence:

- `autonomy/state/CAMPAIGN_STATE.json` — the single source of truth for track, rung, wave,
  stage, and open threads. Written only by SŪTRADHĀRA, under a lockfile; read by everyone.
- `autonomy/state/*.jsonl` — append-only ledgers: `DECISIONS`, `VERDICTS`, `PARKED`,
  `HEARTBEAT`, `WORK_QUEUE`, `STANDING_QUEUE`, `RUN_LEDGER`. Append-only means a lost race
  costs a duplicate line, never a lost record.
- `autonomy/mailbox/to_<agent>/` — one file per message, claimed by rename. Transient,
  git-ignored; the durable trace of anything that mattered is in the ledgers.
- Git: a dedicated campaign branch, never `main`; one commit per completed unit of work with
  the ledger lines that justify it; the `CAMPAIGN_COORDINATION.md` lease claimed before any
  shared write, exactly as §17 requires of a human campaign.

### 18.8 — When the fleet itself fails

The campaign must survive its own operators dying. Every long-lived agent is restartable from
`CAMPAIGN_STATE.json` plus the ledgers alone — no agent holds unrecorded state, and any agent
that would need to may not proceed until it has written what it knows. PRAHARĪ restarts a dead
session; if PRAHARĪ dies, SŪTRADHĀRA restarts it; if SŪTRADHĀRA dies, PRAHARĪ restarts it, and
their mutual watch is the only cycle in the design. If both are gone the tmux session is
relaunched and the fleet reconstructs its position from the files — the same recovery story the
orchestrator itself gets in §7.2, applied one level up.

### 18.9 — Resource budget and ceilings

| Resource | Ceiling | Enforced by |
|---|---|---|
| Concurrent build runs | `runs × (1 + workers) ≤ 33` connections (default 6 × 5 = 30) | SŪTRADHĀRA at dispatch; the orchestrator's own `_MAX_CONCURRENT_RUNS` is the backstop |
| Concurrent KĀRAKA agents | 4, worktree-isolated when writing files in parallel | SŪTRADHĀRA |
| Per-asset wall clock | `writer_timeout_seconds`, telemetry-derived (§7.4) | Orchestrator watchdog |
| Run continuations | 10 generations (§7.2) | Orchestrator |
| Spend | Three ceilings, whichever binds first: the raw four-class token total (audit), **output tokens** (the runaway tripwire — at ~97 % cache_read the raw sum is dominated by the cheapest class and is a poor loop detector), and **USD cost** (the one that means money, null until `state/PRICING.json` carries per-model per-class rates). Each stored beside a written definition — an integer whose units are undefined spreads 270× across conventions and enforces nothing | `bin/spend_meter.py` → `state/SPEND.jsonl`; PRAHARĪ compares, never estimates. **No meter, no spend claim** — an estimate is fabrication (H6) and an unmetered "OK" is a green with no detector (H4). Breach is a Reserved Power → PARK |
| Destructive operations | Snapshot verified + `verify` passed + partition rehearsal passed, per operation | ADHIKĀRIN, as precondition not claim |

### 18.10 — What Abhisek sees

Nothing is required of him; everything is available to him. LEKHAKA writes a digest at each
rung boundary and on any parked item — what moved, what froze, what is parked and why, what it
costs so far. The `PARKED.jsonl` file is the only thing that ever wants him, and it is designed
to be answerable in one sitting. The conductor's pane stays interactive: he can interrupt,
ask, or redirect at any moment, and the fleet absorbs it as an ADHIKĀRIN-level ruling — an
autonomous campaign he can steer, not one he must watch.


---

## §19 — Pillar IV · Per-asset implementation efficiency *(the YUKTI discipline; new in v5.0)*

### 19.1 — The gap this closes, stated plainly

Two things were wrong and both are this plan's own fault.

**v3.0's §7 — "Build-time optimization · six levers" — was dropped in the v4.0 restructure.**
Its levers survive individually (content addressing and early cutoff in M3, partition-scoped
invalidation in the receipts discipline, retry and continuation in §7, timeout right-sizing in
§7.4, critical-path shortening in §11), so nothing was lost in substance. But the section that
held them as a coherent programme disappeared, and nobody noticed until the native asked.

**More seriously: every one of those six levers is orchestration.** Each of them makes the
system *avoid* work — skip what has not changed, invalidate only the affected partition, do not
redo what a prior run completed. Not one makes the work itself cheaper. That distinction is
invisible until you notice what §1.10 says: a full build of this chart **has never completed
once**. Content addressing helps the second build. Partition receipts help the second build.
Digests help the second build. The campaign's actual cost is the first one — and the plan, as
written, had nothing to say about it.

**And the per-asset speed advice is template output.** All 128 generated "Rebuild time" plans
are derived by `asset_plans.py` from *median* wall clock: 40 assets read "built once, publish
`substrate_version` + output digest", roughly 40 read "Fast (median Ns): no bespoke speed work",
8 read "not a build". Not one names a hotspot, a query, or an algorithm. Worse, median is the
wrong statistic for this population: `ka_kshetra`'s median is minutes and its worst case is
**33.8 hours**; `ka_gochara_sweep` ran ~30 h per chart. A classifier keyed on median
systematically exempts the assets that most need attention.

### 19.2 — Two kinds of speed

| | Avoided work (Pillars I–III) | Cheaper work (**this pillar**) |
|---|---|---|
| Question | "Must we rebuild this at all?" | "Given that we must, how fast can it be?" |
| Mechanism | Digests, receipts, early cutoff, resume, retry | Better algorithm, better query, better data flow |
| Helps | The second and later builds | The **first** build, every forced rebuild, every cold chart |
| Ceiling | Perfect skipping still costs a full build once | Bounded only by the computation's true cost |
| Status before v5.0 | Fully specified | Absent |

Both are needed. The programme's shape makes the second one urgent: the ladder deliberately
rebuilds every asset once, layer by layer, and that first pass is where the 45.6 % completion
rate and the multi-day heavies actually bite.

### 19.3 — The invariant: faster must mean identical (I18)

An optimization is admissible only with a proof that the output did not change:

- **Deterministic assets** — digest equality between the pre- and post-optimization build of the
  same partition. This is what M3's determinism harness was built for; §19 is its first heavy
  consumer.
- **Floating-point assets** (ephemeris-derived positions, strengths, sensitive degrees) — equality
  within a tolerance the asset **declares and justifies** in its registry row. An undeclared
  tolerance is not a tolerance; it is a silent data change.
- **Row-order-insensitive assets** — equality of the sorted digest, with the insensitivity itself
  declared rather than assumed.

If an optimization changes the output — even in a way that looks better — it is not an
optimization. It is a correctness decision about what the asset should contain, and it is
**parked** (§18.4) for the native rather than merged by whoever noticed it. This is the same
discipline as I5 pointed at performance: a speedup without a detector behind its identity claim
is null.

### 19.4 — The method, per asset

1. **Profile before opining.** Instrument the real run: wall clock per substep, rows per second,
   time in DB versus Python versus ephemeris calls, `EXPLAIN (ANALYZE, BUFFERS)` on every query
   the writer issues. No optimization is proposed without a measured hotspot — the failure mode
   here is a week spent making a 3-second step 40 % faster.
2. **Read the writer and ask what it is actually computing.** This is the step that pays, and it
   is judgment, not tooling: what does this asset exist to produce, and is the code producing it
   the long way round? The native's framing is exact — *understanding the code problem* is often
   worth more than any micro-optimization.
3. **Classify the ceiling.** Round-trip-bound (many small queries), I/O-bound (large scans,
   missing indexes, spill), CPU-bound (dense numeric work), or algorithmically dense (the shape
   of the computation is wrong). The class determines which techniques in §19.5 apply, and
   protects against applying a CPU fix to a round-trip problem.
4. **Change one thing; prove identical; re-measure.** One technique at a time, each with its
   own identity proof (I18) and its own measured delta, on the rehearsal partition (I8) before
   the full asset. Bundled changes cannot be attributed, and an unattributed speedup cannot be
   defended or reverted.
5. **Record the outcome — including "already efficient".** An asset examined and found sound
   gets that written down with its measurement, so no later pass re-litigates it. Under §8.3
   item 5, an unmeasured asset cannot freeze; a measured-and-left-alone asset can.

### 19.5 — Technique catalogue, grounded in this codebase

**Round-trip bound** — the most common and the most rewarding. N+1 query patterns collapsed into
set-based SQL; per-row `INSERT` replaced by batched insert or `COPY`; per-row commits replaced by
per-substep commits (the orchestrator already owns the transaction, §N.2); lookups hoisted out of
loops into a single pre-fetched dict.

**I/O bound** — index coverage for the writer's own reads *and* for its `count_sql` and
`integrity_check_sql` (both now run every build, §4); streaming results instead of materializing
full sets in memory; the real spill volume (§13 item 1) so hash joins stop dying on tmpfs.

**CPU bound** — vectorized numeric work (`numpy`) instead of per-row Python loops for ephemeris
and strength math; memoizing pure functions across substeps; hoisting invariants out of inner
loops. Note §N.4's deterministic-first rule: this is all Python-side computation, which is
exactly where it belongs.

**Recomputation of substrate** — the highest-leverage class. An asset that recomputes what a
shared L0 asset already holds is paying for the substrate twice. The plan's own exemplar is
`bg_gochara_arcs`: the whole epoch in ~48 seconds, computed once, reused forever. Every writer
that calls the ephemeris in a loop is a candidate to read a materialized arc instead.

**Intra-asset parallelism** — fourteen L1/L2 writers partition by ayanamsha into five independent
substeps; `ga_dashas` by `{system}:{aya}`; `ka_kshetra` by `stage{n}:{event_class}:{slice}`. These
partitions are already declared and measured (§9). Where they are genuinely independent, they can
run concurrently within the asset, bounded by the connection budget (§18.9).

**Algorithmic redesign** — the biggest wins and the rarest. This programme already contains its
own proof: gochara v1 was a daily-grid sweep at ~30 h per chart; v3 computes a full century in
270 decade slices with per-slice delta fingerprints, using 8 contact primitives over 27 classes.
That is not a faster loop — it is a different algorithm for the same question. Coarse-to-fine
search instead of dense enumeration is the generalizable pattern, and several of the ten heavy
assets look like candidates for it.

### 19.6 — Targets, set honestly

No target is invented here. For each asset: measure the baseline (p50 and p90, not median alone),
identify the hotspot, derive the target from what the hotspot could plausibly become, and record
the achieved figure next to it. Where the honest answer is "this is near its floor", that is the
recorded result.

What can be said without fabrication is where the money is: **ten assets are heavy** (p90 ≥ 30 min,
median ≥ 10 min, or a substep plan ≥ 5 min), and they dominate the campaign's wall clock. The
efficiency pass concentrates there — R1's five (`ga_dashas`, `ga_vichara`, `ga_sensitive`,
`ga_strength`, `ga_vargas`), R2's three (`bo_laksana`, `bo_laksana_rerank`, `bo_samskara`) and
R3's two (`ka_kshetra`, `ka_sangam`) — while the long tail of medium-deterministic assets gets
the cheap systemic fixes (indexes, batching, set-based rewrites) applied as a sweep rather than
one investigation each.

### 19.7 — Where it runs

Rung stage 3, before repair (§8.6) — and never outside the open rung (I13). Optimizing an L2
writer while R1 is open is the same violation as rebuilding an L2 asset early, and for the same
reason: the work may be invalidated by what R1 does beneath it.

The convergence with I8 is worth naming. The rehearsal partition that I8 already requires before
any destructive operation is also the ideal optimization workbench: small enough to iterate on in
minutes, real enough to profile honestly, and already the thing whose output identity is being
checked. One mechanism, two purposes.

### 19.8 — Under autonomous execution

KĀRAKA profiles and optimizes. **PARĪKṢAKA verifies identity, not speed** — it re-runs the
comparison itself and treats a speed claim with no identity proof as a FAIL, not an
INCONCLUSIVE (I16). ADHIKĀRIN approves optimizations under charter power **G11**, whose bound is
the identity proof: an optimization that changes output is not G11's to approve, it is parked.
LEKHAKA records baseline, technique, delta and proof in the workbook's Efficiency sheet (§16).

The failure mode to guard against in an autonomous fleet is enthusiastic micro-optimization —
agents are good at making things marginally faster and will happily do it forever. §19.4 step 1
is the guard: no measured hotspot, no optimization, and the Standing Queue never contains
optimization work (it is rung work by §19.7, not layer-independent filler).


---

*End of NIRMANA_ELEVATION_PLAN_v4_0.md (v5.0) — PROPOSED. Single chart: 482012f1.
Executed to date: migrations 588 and 589 only.*
