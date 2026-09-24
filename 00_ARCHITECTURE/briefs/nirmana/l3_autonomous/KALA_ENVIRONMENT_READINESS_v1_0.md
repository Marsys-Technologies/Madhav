---
artifact: KALA_ENVIRONMENT_READINESS
canonical_id: KALA_ENVIRONMENT_READINESS
version: "1.1"
status: CURRENT
date: 2026-09-24
author: "L3 Kāla strategic session (madhav-a6), at the native's request"
question: "What must be set right in the L3 ecosystem and environment before asset elevation can fully execute?"
scope: "The environment only — infrastructure, build path, data state, guards, CI, proof and serving machinery. Brief content is explicitly out of scope; the native is elevating the briefs in a separate conversation."
method: >
  Live production reads (read-only, Cloud SQL proxy) for registry, throughput, row counts, guards,
  timeouts and generation tables; three parallel read-only sweeps of the build path, the CI and
  governance gates, and the serving surface; direct verification of every claim that entered the
  activity list. Nothing from memory.
headline: >
  The build path is healthier than believed — all 22 assets have conforming registered writers and
  seed rows. The environment is not: the native's own chart is missing its entire dependent spine,
  four assets are in a recorded error state, nothing in the layer is protected by any database
  guard, the L3 generation machinery does not exist, there is no determinism gate, and the
  writer-digest mechanism serialises the whole campaign.
---

# L3 Kāla — environment readiness, and the activities that must precede elevation

## 0. One good finding first

**All 22 assets have a conforming, registered writer.** Every one carries a module-level
`@register` on a `WriterBase` subclass, implements `run(ctx)` or `plan_substeps`+`run_substep`, and
**not one commits or closes `ctx.db_conn`** — the frozen orchestrator contract is intact across the
layer. All 22 have seed rows and all are `is_active`. The suspicion that `ka_avadhi`, `ka_taranga`
and `ka_graha_sancara` lacked a writer is a **false alarm**: they are at
`writers/ka_avadhi.py:175`, `writers/ka_taranga.py:74`, `writers/ka_graha_sancara.py:47`. Three
further assets (`ka_dasha_kala`, `ka_tulana`, `ka_gochara_resonance`) declare `@register` inside a
`_build_writer_class()` closure to dodge circular imports, but each module ends with a top-level
call, so the decorator fires on import.

The four assets with no `count_sql` — `ka_dasha_kala`, `ka_graha_sancara`, `ka_muhurta_seva`,
`ka_tulana` — are the four **service** assets, correct by design.

**So elevation is not blocked by the build path. It is blocked by the environment around it.**

---

## A. Data state — the chart that matters is not built

**The native's own chart is missing the entire dependent spine.** Live row counts,
chart `482012f1`:

| table | owner | rows on the native's chart | rows on the test chart (Abhinandan) |
|---|---|---|---|
| `kala_convergence` | Saṅgam | **0** | 17,957 |
| `kala_activation` | Kalasutra | **0** | 336,093 |
| `kala_obstruction` | Vighnakara | **0** | — |
| `kala_darshana` | Darshana | **0** | — |
| `kala_bhavishya` | Bhavishya | **0** | — |
| `kala_field` | Kṣetra | 8,570,075 | 2,412,882 |
| `kala_gochara_windows` | Gochara | 17,211 | 20,239 |

Those five were built on 2026-08-13 and wiped by the L2 rebuild cascade. The build system records
them correctly as `stale` — the honest-signal work is holding — but the data is gone. Of six charts
in the system, **only Abhinandan is built through the spine**; three charts are empty entirely.

**Activities**

| # | activity | why it blocks elevation |
|---|---|---|
| **E1** | **Rebuild the native's chart through the spine** (Saṅgam → Kalasutra/Vighnakara → Darshana → Jīvana/Bhaviṣya) — after E2–E5, not before | The baseline freeze runs the thirteen questions against *this* chart. Five spine tables are empty, so a baseline taken now records absence, and the ablation has no Arm A. Every "before" measurement is of an unbuilt layer |
| **E2** | **Adopt a cascade rule and a detector**: an L2 rebuild must either not reach `kala_*` or must mark the five dependents stale *and* refuse to serve them | The cascade is why this happened, and nothing prevents a recurrence mid-campaign |

---

## B. Build path — four recorded failures stop a rebuild today

From `asset_throughput`, the native's chart, verbatim:

| asset | state | recorded cause |
|---|---|---|
| `ka_kshetra` | **error** | `worker_crash: OperationalError: the connection is lost` (2026-09-11) |
| `ka_avadhi` | **error** | `post-write integrity check failed: integrity_check_sql → False` (2026-09-10) |
| `ka_gochara_v3_century_materialize` | **error** | `BUILD-PROTECTED: kala_gochara_windows row(s) for chart_id 482012f1…` (2026-08-21) |
| `ka_gochara_sweep` | error | `no writer registered` — expected; retired and `is_active=false` |

**Activities**

| # | activity | evidence |
|---|---|---|
| **E3** | **Raise or scope the idle-in-transaction timeout for the build role.** `amjis_app` carries `idle_in_transaction_session_timeout=600s` and `statement_timeout=1800s`; Kṣetra's substeps exceed ten minutes of open transaction and the server kills the connection. Note `data_plane_builder` — the post-cutover role — currently has **no timeout configuration at all**, which is the opposite error | live `pg_roles` |
| **E4** | **Clear the stale BUILD-PROTECTED error on the century writer.** The guard it names **no longer exists**: `build_protected_assets` has **0 rows** and there are **0 triggers on any `kala_*` table** (migration 588 dropped them). The error is six-week-old residue blocking an asset that is otherwise ready | live |
| **E5** | **Resolve `ka_avadhi`'s integrity contract.** `kala_avadhi` holds 1,169 rows against a `target_floor` of 1,169, yet `integrity_check_sql` returns False. Either the contract is wrong or the data is — both are elevation-blocking, and a floor met by a failing contract is exactly the earned-signal defect class | live |
| **E6** | **Seed hygiene**: `ka_avadhi` and `ka_taranga` omit `asset_kind` entirely; `ka_kalasutra`, `ka_sangam` and `ka_vighnakara` carry no `catalog_status`; eight rows sit at `DRAFT`. Harmless today, load-bearing the moment any build or cockpit path filters on them | seed rows |

---

## C. Protection — nothing in the layer is protected by anything

`build_protected_assets`: **0 rows.** Triggers on `kala_*` tables: **0**. The three protected
classes — the retired sweep snapshot (16,297 `v1` rows live on the native's chart), issued claims
and observations, retained outcomes — are protected **by convention alone**. The Clear path was
separately shown to reach 40,117 rows including that snapshot.

| # | activity |
|---|---|
| **E7** | **Install real protection before any unattended build.** Per the delegated decision D-I this rides the cutover's own protected-object map (BEFORE-trigger guard + protected owner), not a new mechanism — but the map must actually name the three classes, and today nothing does |

---

## D. Generation infrastructure — the released hold is unbuilt work

The native released the W1 hold. The machinery does not exist. Live tables:
`l1_data_plane_generations`, `l1_data_plane_generation_heads`, `l1_data_plane_generation_partitions`,
`l2_data_plane_generation_heads`, `l2_data_plane_generation_partitions`,
`l2_data_plane_generation_runs`, `l2_data_plane_manifest_attestations`. **There is no `l3_*`
equivalent of any of them.**

| # | activity |
|---|---|
| **E8** | **Build the L3 generation, publication and manifest tables** to the frozen FOUNDATION_SAFETY §6 design, reusing the L1/L2 machinery as the template it already is. Nothing reaches `DATA_ACCEPTED` without it, and "rollback" is aspiration until a selected head can be repointed |

---

## E. CI — what will actually block a Kāla PR, and what cannot

Four required checks, all in `ci.yml`: **typecheck**, **unit-tests**, **secret-scan**,
**governance-gates**. Everything else fails the run but not the merge.

**E9 is the constraint that shapes the whole campaign.** The required `governance-gates` job runs
`provenance_inventory --check` and `nirmana_analysis_layer_pins --check`. Any change to a Python
writer makes both stale, and regenerating the writer-digest inventory **shifts roughly 24 unrelated
writers' digests** (the codebase says so in two places). There are 123 digest entries in one
generated file and one pins file. **Two concurrent writer elevations will collide on those
generated files every time.**

| # | activity | why |
|---|---|---|
| **E9** | **Decide the campaign's concurrency model against the digest/pin mechanism** — serialise writer-touching lanes, or batch regeneration at a merge train, or split the generated files per layer. Without this, 22 elevations means 22 pin conflicts | required job; ~24 collateral digests per regeneration |
| **E10** | **Build the determinism gate.** There is **no build-twice-and-diff job anywhere.** Idempotency is asserted only by in-memory `FakeConn` unit tests with no database. "Wipe and rebuild freely" is a preference, not a property | grep across all 20 workflows |
| **E11** | **Give the DB-dependent guards a database in the required job.** `dag_edge_guard` and `kala_derivation_completeness_guard` run `--self-test` only; their real scans need `DATABASE_URL` and live in a scheduled advisory workflow. The required job runs `-m "not integration"`, so every DB-marked test skips | ci.yml |
| **E12** | **Fix or retire `icr-pr-gate`.** It is `continue-on-error: true` as a "permanent design decision" while remaining a **named required check** — a green tick that cannot go red. That is the earned-signal defect, in branch protection itself | ci.yml |
| **E13** | **Decide what the baseline ratchets mean.** `drift_detector` passes at ≤79 violations, `schema_validator` at ≤43. Pre-existing rot passes green indefinitely; only growth fails. Acceptable as a ratchet, dangerous as a permanent amnesty — set a burn-down or say plainly that it is permanent | ci.yml |
| **E14** | **Make `db-integration-tests` required, or accept that migrations can regress unblocked.** It is deliberately not a required check today | ci.yml:257 |
| **E15** | **Extend the governance gate to `00_ARCHITECTURE/briefs/**`** and make a YAML parse failure a violation in its own right. The glob is `00_ARCHITECTURE/*.md`, non-recursive, and `drift_detector` uses a hardcoded top-level file list — every artifact this campaign produces is unvalidated and drift-invisible | verified twice |

---

## F. Proof infrastructure — the instrument does not exist

| # | activity |
|---|---|
| **E16** | **Freeze the baseline** (already authorised; prompt staged). Thirteen questions, three proving cases, one ordinary period, run against current serving. Until it exists every wave closes on *changed*, not *elevated*. **Sequencing note: E1 first** — a baseline taken against the empty spine measures absence |
| **E17** | **Give the Python side a disposable-database fixture.** `conftest.py` has no DB fixture at all; the only real-Postgres path is a GitHub Actions service container in a non-required job, and the disposable-DSN guard that exists is TypeScript-only. Asset elevation cannot prove a write path without one |
| **E18** | **Create ordinary-period fixtures.** The product's own control case has none |

---

## G2. Serving — 16 of the outputs reach a person; the largest does not

Better than the blueprint implied. **Reachable today:** activation, activation_predicates,
convergence, obstruction, darshana, jīvana_parva, bhaviṣya, avadhi, taraṅga, kota_chakra,
sudarśana_varṣa, mūrti_nirṇaya, vedha_gochara, tithi_praveśa, gochara_windows,
gochara_resonance_map — sixteen.

**Not reachable:** `kala_field` — the layer's largest asset, 8,570,075 rows on the native's chart —
has **no read path anywhere**, and the codebase says so itself
(`platform-mcp/src/lib/kala_ritual_resonance.ts:494`: *"no serving capability exists over any
`kala_field*` table"*). `kala_field_windows` is read only behind a flag that is **off by default**,
and only for a provenance string. `kala_field_snapshots` / `_skill` sit on a raw-door whitelist with
no capability, and the snapshots table is empty. `kala_gochara_windows_v2` appears only in
migrations. `kala_field_salience` reaches a person as five averaged scalars.

| # | activity | evidence |
|---|---|---|
| **E23** | **Give `kala_field` a read path.** The best-elevated asset in the layer is invisible to the product; an elevation the person cannot reach is not one | code comment + zero capability |
| **E24** | **Publish the six orphaned capabilities.** `kota_chakra`, `sudarshana_varsha`, `moorti_nirnaya`, `vedha_gochara`, `tithi_pravesha`, `paddhati_profile` are **registered but have no public `kala_*` alias** in `tool_name_bridge.ts`. Registered is not reachable | bridge |
| **E25** | **Declare `density_contract` and `empty_reason` on the L3 capabilities.** **Zero of 15** declare a density contract; `empty_reason` is implemented in **one of 15**. The budget trimmer protects `empty_reason` as an immune honesty field — immunity helps only a field that is emitted, so today L3 fields can be silently dropped | `types.ts:207`; grep |
| **E26** | **Build the served-evidence sentinel.** Two briefs assign it to L3 explicitly. The one L3 sentinel that exists mocks the database and stops at the capability handler — no ranking, no trimmer, no synthesis. **L3 can prove a field leaves SQL; it cannot prove it reaches a reader** | `consumer_sentinel_dp_sd_017.test.ts` |
| **E27** | **Make the ownership boundary mechanical.** "L3 never edits `kala_views/`" is prose in four documents and **there is no `CODEOWNERS` file in the repository**. Nothing prevents a crossing | verified absent |

---

## G. Process hygiene — three collisions in one day, with the cure already written

| # | activity |
|---|---|
| **E19** | **Wire `reserve_migration_number.py`.** A purpose-built migration-number allocator exists at `platform/scripts/governance/reserve_migration_number.py`, written 2026-09-23, and is **invoked by nothing** — not CI, not `package.json`. Three number collisions occurred across three streams in the following 24 hours. This is the cheapest item on the list |
| **E28** | **Pins hygiene, not a blocker — and a claim to stop repeating.** 54 of the 57 commits pinned in main's `nirmana-analysis-layer-pins.json` are **not ancestors of main**, several unreachable entirely, and a bare local `--check` fails. A peer concluded from this that *"every PR entering the merge queue fails the pins test."* **That is false:** `governance-gates` is SUCCESS on PRs #2724, #2725 and #2726 — all merged today — and passes on the open #2727. The CI event path validates a narrower set than a local run. Worth cleaning; worth not "fixing" a gate that is not broken |
| **E20** | **Publish a merge order.** Four branches carry unmerged Kāla work with interdependent migrations and a shared generated-digest file; `l3/kala-elevation-readiness` and `sangam/stage3` have diverged. Decide what merges first and in what order |
| **E21** | **One worktree per lane, asserted at first action.** Already earned the hard way: a shared checkout tangled four sessions' commits, and the root cause was a prompt naming an existing directory |
| **E22** | **Measure the cost.** The registry claims 24 minutes per chart; ≥7.5 hours was measured. No build time can be promised, and E1's rebuild cannot be scheduled, until one real measurement exists |

---

## H. Sequence

Nothing else can be measured until the chart is built, and the chart cannot be built until the four
recorded failures clear.

1. **E3, E4, E5** — clear the build blockers (timeout, stale guard error, integrity contract).
2. **E7** — protection, before anything unattended runs.
3. **E1 + E22** — rebuild the native's chart through the spine, and measure it while it runs.
4. **E16** — freeze the baseline against a built chart.
5. **E9, E19, E20** — the campaign's mechanics: concurrency model, number allocator, merge order.
6. **E10, E11, E15** — the gates that make the rest provable.
7. **E8** — generation infrastructure, on the W1 path.
8. Everything else in parallel.

**E19 costs an hour and prevents a recurring failure. E4 is a `DELETE` of a stale error string. E3
is one role setting.** Those three could be done today.
