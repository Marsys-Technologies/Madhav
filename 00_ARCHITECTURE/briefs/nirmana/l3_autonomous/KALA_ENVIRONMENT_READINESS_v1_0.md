---
artifact: KALA_ENVIRONMENT_READINESS
canonical_id: KALA_ENVIRONMENT_READINESS
version: "1.6"
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
| **E4** | **INVERTED — this is now the highest-severity item in the document, and my first reading was backwards.** I called the stale `BUILD-PROTECTED` error inert residue. `platform/src/lib/build/plan.ts:590` treats **`state === 'error'` as a NEEDS-BUILD criterion**, not a barrier. So `ka_gochara_v3_century_materialize` is **`is_active = true`**, **selected for build**, and DELETEs `kala_gochara_windows … generation = '3.0'` in the same transaction as its staging write. `kala_gochara_authority` makes **`'3.0'` the authoritative served generation for the native's chart** (flipped 2026-08-11), and that chart holds **914 rows at `'3.0'`**. Migration 588 dropped all three protecting triggers and their functions — live, **0 triggers on any `kala_*` table, 0 rows in `build_protected_assets`**. **The next full-layer sweep of the native's chart deletes the 914 served gochara windows, and nothing in the database stops it.** It is a leaf asset (0 dependents), so only a sweep reaches it — narrower, not safe. **N-6a's `is_active=false` is not a tidy-up step; it is the only mitigation.** Escalated to the Gochara lane, whose asset and runbook step it is | live, verified |
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
| **E28** | **The merge queue is blocked, and my own refutation of that was wrong.** I disputed the claim by citing `governance-gates` SUCCESS on #2724/#2725/#2726 — **all three merged 2026-09-23, and the breaking commit `b6690928f` merged 2026-09-24T07:36:04Z.** My evidence predated the change by thirteen hours and could not have tested it; the only PR based after it is #2733, the fix. **Real cause:** two fixture tests in `test_nirmana_analysis_layer_pins.py` check a rewound pre-repair fixture against a baseline that now carries the repair successors — 2 failed / 60 passed at that baseline — while the tool's own `--check` stays green. **Every PR based on or merged onto main at or after that commit is red on those two tests until #2733 lands.** The part of my caution that held: nothing needs re-sealing on any other side, and the L0 lane confirms it |
| **E20** | **Publish a merge order.** Four branches carry unmerged Kāla work with interdependent migrations and a shared generated-digest file; `l3/kala-elevation-readiness` and `sangam/stage3` have diverged. Decide what merges first and in what order |
| **E21** | **One worktree per lane, asserted at first action.** Already earned the hard way: a shared checkout tangled four sessions' commits, and the root cause was a prompt naming an existing directory |
| **E22** | **Measure the cost.** The registry claims 24 minutes per chart; ≥7.5 hours was measured. No build time can be promised, and E1's rebuild cannot be scheduled, until one real measurement exists |

---

## G3. Three findings from measurement, not reading

### E29 — The DAG edge guard, run live: six hard violations on today's main

The guard runs `--self-test` only in CI and its live path skips without `DATABASE_URL`, so
**nothing in any gate has ever seen this.** Run read-only against the production registry, 130
writer assets checked:

| violation | note |
|---|---|
| `bo_laksana` reads `bodha_cgm_nodes` (`bo_bimba`) — not in `depends_on` closure | L2 |
| **`ka_bhavishya_lekha` reads `phala_anchors` (`ph_nimitta`)** | **L3 reading L4 — a layer inversion, an architectural question, not an edge to add** |
| `ka_gochara_resonance` reads `chart_dashas` (`ga_dashas`) | both producers measured **`lit`** on the canonical chart (483,870 / 53 rows), so adding these edges would not block the next resonance build |
| `ka_gochara_resonance` reads `ga_yoga_firings` (`ga_yoga`) | as above |
| `ka_kshetra` reads `kala_gochara_windows` (`ka_gochara`) | predicted from source by the Kṣetra stream — confirmed |
| `ka_sangam` reads `kala_vedha_gochara` (`ka_vedha_gochara`) | confirms a synergy-audit finding by an independent mechanism |

Plus one SOFT (`ka_gochara_resonance` reads `chart_facts`, no producer in closure). `ph_nimitta` is
**`stale` on both charts**, which sharpens the inversion question rather than settling it.

**Activity: make this a gate with a database, not a self-test,** and dispose of all six before any
unattended build.

### E30 — The generation serving is about to be flipped onto has no writer

Verified on `origin/main` **and** the Gochara branch: **no writer emits `'4.0'` into
`kala_gochara_windows`.** The only `'4.0'` in any source is a docstring at
`services/gochara_kernel/ledger.py:16`. `ka_gochara.py` writes `GENERATION_V2` throughout. Live, the
table holds `'3.0'` (1,830 rows) and `'v1'` (38,287 rows) and **no `'4.0'` at all.** Tranche-2 step 8
flips serving authority onto `'4.0'`, and serving reads this table — the flip would have **emptied
the served forecast.** Four step-7 gates could not see it. A gate and a refusal now stop it, but
**the projection writer is an unbuilt work package with no owner**, and it voids Kṣetra's option to
declare its edge after WP10 step 5.

### E31 — The structural blind spot behind E29

Running that guard required registry access **no executor session has**. Six hard violations sat in
production unobserved by every stream, not through a series of oversights but because **no lane in
the campaign can measure the thing the gate only self-tests.** Give one lane a read path, or the
next six will sit just as long.

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

### E4 — MITIGATED 2026-09-24, and exactly how far

**Action taken.** Under N-6a (the native's own ruling: century `is_active=false`, reversible,
nothing deleted) and the native's *"do what is necessary"* instruction, this session set
`ka_gochara_v3_century_materialize` to `is_active = false` on production. One scoped `UPDATE`
inside a transaction, with an in-transaction probe that would have refused the commit if the flag
had not landed. `UPDATE 1`.

| | before | after |
|---|---|---|
| `is_active` | `true` | **`false`** |
| served `'3.0'` rows, native's chart | 914 | **914** |
| served `'3.0'` rows, test chart | 916 | **916** |

Reversal, one statement:
`UPDATE asset_registry SET is_active = true WHERE asset_id = 'ka_gochara_v3_century_materialize';`

**What was deliberately NOT run: the generation-keyed trigger half of step 3.** It carries a
disclosed side effect — once installed, *any* legitimate write to `'3.0'` or `'v1'` is refused
until a release-authority session sets `app.allow_protected_sweep_rewrite = on` — and three streams
are working in flight. The `is_active` half alone removes the asset from build selection, which is
what closes the dispatch path, and it touches nobody else. The trigger half remains the native's or
a credentialed session's, inside the Gochara runbook.

**The applied half does not survive a re-seed — so the ranking inverts.** The Gochara lane caught
this and it is right. `asset_registry_seed.ts`'s `ON CONFLICT` sets
`is_active = CASE WHEN asset_registry.catalog_status = 'RETIRED' THEN asset_registry.is_active ELSE
EXCLUDED.is_active END`. Live `catalog_status` for the century writer is **`CURRENT`** — only
`ka_gochara_sweep` is `RETIRED` and thus protected — and its seed entry carries `is_active: true`.
**A re-seed silently re-arms it.** It is not automatic: no workflow and no npm script invokes the
seed, it is hand-run.

**Measured: no re-seed has touched this registry since 2026-09-23 21:07.** `health_probe` *is* in
the `ON CONFLICT` set list, the seed file does **not** contain
`expected_mean_node_rahu_longitude_deg`, and live carries it at `49.033044` — the key migration
1075 added at 21:07 yesterday. A re-seed would have wiped it. Corroborated by `asset_kind`, also
overwritten by the seed, omitted from the `ka_avadhi` and `ka_taranga` entries, and present live as
`data`. So re-arming is a real mechanism that has not yet fired.

*A false proof caught before it left this session:* I first offered live `target_floor` 914 against
seed 0 as evidence the seed had not run. **`target_floor` is not in the `ON CONFLICT` set list**, so
that divergence proves nothing — the same shape as every other error this week, a test that looks
decisive and is out of scope.

**So, for the native, plainly:** the half applied here closes the dispatch path today but is one
hand-run seed from undone; **the half left unapplied is the durable one**, and makes the `'3.0'`
DELETE fail loudly instead of silently succeeding. Its cost is refusing every legitimate `'3.0'`
and `'v1'` write until a release-authority session lifts it. A third option neither lane will take
unilaterally: set `is_active: false` on the century entry **in the seed file**, which is the seed
owner's file.

**This session did hold a write path for both halves** — `amjis_app` has `UPDATE` on
`asset_registry`, `DELETE` on `kala_gochara_windows`, `TRIGGER` privilege, and **owns** that table.
Only one half was run, by choice, not by limitation.

**Decided 2026-09-24 under delegation — D-O in `KALA_DELEGATED_DECISIONS_v1_0.md` v2.0.** The
third option is taken: `is_active: false` is now on the century entry in
`asset_registry_seed.ts`, with the reason at the line. The re-arm mechanism above is closed at its
source; a re-seed now writes the same value production holds. The trigger half stays unapplied and
stays the native's, inside the Gochara runbook. E4 status: **MITIGATED; durable against re-seed once PR #2734 merges.** The seed line is on
`fix/century-seed-is-active-false` (one commit off `main`, `68eaa04c6`), auto-merge armed through the
queue. Until it lands, a re-seed run from `main` would still re-arm the writer; the Gochara lane
records E-014 as "seed fix pending merge" for the same reason. Their `step03_reversal.sql` will
note that its `is_active = true` restore is no longer lasting once this line is on `main`.
Still open only for the trigger half, which is a runbook item, not an environment defect.

**Two corrections to the Gochara lane's E-014, both verified.** The recovery dump is **not** "one
untracked file on this machine": it is committed and pushed at
`origin/campaign/nirmana-autonomous`, 16,214,137 bytes, matching their figure exactly. It is absent
from `main` — durability is fine, discoverability is not. And migration 588 removed protection
**deliberately**, on the native's 2026-08-23 instruction, its own text requiring any reinstatement
to be keyed on `(table, generation)`. So the trigger half is a narrow, deliberate reversal of a
standing native instruction for two generations only, and should be put to the native as that.

### The three items I called "could be done today" — all three retracted

I closed v1.0 saying E19, E4 and E3 could be done today. Checking each before doing it:

- **E4 was backwards** (above). The error was never a barrier, so clearing it would have removed
  nothing — and the danger it appeared to hold back was already live the whole time.
- **E15 would break the build.** A recursive glob over `00_ARCHITECTURE/briefs` covers 1,023 `.md`
  files: 439 conformant, 211 with no byte-0 frontmatter, 373 with frontmatter missing a required
  key or unparseable. That is **~584 new violations against a `schema_validator` baseline of 43** —
  the required gate turns red and every PR blocks. Even the narrow campaign-only glob adds 48
  (36 of 84 in `l3_autonomous/`, 12 of 29 in its `briefs/`). It needs a staged rollout or a
  new-files-only rule.
- **E19 is not a wiring job.** The allocator *computes and prints* a claim row; its own docstring
  states it never writes to any governance file and that the append is a conductor action on a
  separate coordination branch. The real fix is a guard that fails a PR adding a migration whose
  number is unclaimed — a larger change than "wire the script".

**The pattern is worth keeping.** Three items were labelled cheap from reading what they were, not
from checking what doing them would cause. One of the three was not merely not-cheap; it was
pointing the wrong way at a live data-loss risk.
