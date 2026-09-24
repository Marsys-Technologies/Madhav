---
artifact: MADHAV_DATA_PLANE_ASSET_INTERFACE_EXECUTION_BRIEF
canonical_id: KA_MOORTI_NIRNAYA_ELEVATION_BRIEF
version: "1.0"
status: DRAFT_FOR_INDEPENDENT_REVIEW      # → PROPOSED_FOR_NATIVE_RULING after the Fable 5.1 review
approval_record: "<none yet>"
parent_layer_contract: "MADHAV_DATA_PLANE_L3_KALA_EXECUTION_BRIEF_v1_0.md / DP-SD-017 / commit 793972c754b106688097dbc54536c1a9c270a793"
foundation_contract: MADHAV_DATA_PLANE_FOUNDATION_CONTRACT_AND_GATES_v1_0.md
synergy_binding: KALA_SYNERGY_BINDING_v1_0.md   # adopted by reference
asset_or_interface_ids: ["ka_moorti_nirnaya", "G21 (F4 grant on bg_transit_moorti — the unguarded read that fails the whole build)", "SC-1 (build-time date.today() horizon)", "SC-8 / IP (ingress-instant grading DEMAND on the position reference — ka_graha_sancara brief §4.3)", "Gochara w22_moorti_nirnaya + Kṣetra S1 consumers"]
goal_objective: "Make the mūrti grading survive its own dependencies and say what it measures: an L0-table lookup (cited) keyed by the Moon's nakṣatra on the ingress DATE (an approximation of the ingress INSTANT the rule is defined on), over a declared horizon, with a missing grant or table producing an F06 'unavailable' row rather than a failed build — so that the two integrators that already read it (Gochara century, Kṣetra S1) consume a stamped, rebuildable input."
source_revision: "9feac52d7 (l3/kala-layer-briefs)"
accepted_upstream_contract: "L1 chart_facts MOON longitude_sidereal at lahiri_chitrapaksha (fact id carried; 670(d)); L0 ephemeris_daily tropical noon-UT knots; L0 bg_transit_moorti (migration 401; 27 rows; Phaladeepika Ch.26 / BPHS Ch.28 cited) — READ WITHOUT A GRANT GUARD; the grant itself is G21 / migration 1073 (PR #2717), not on this base"
implementation_owner: "<one writer, named at stage 3 — not the author>"
independent_review_owner: "Fable 5.1 review agent, fresh context; report at briefs/reviews/REVIEW_KA_MOORTI_NIRNAYA_v1_0.md"
release_authority: "NONE"
may_touch: ["platform/python-sidecar/services/ka_moorti_nirnaya/{logic,writer}.py", "platform/python-sidecar/tests/**/test_ka_moorti_nirnaya*.py", "one additive DDL migration on kala_moorti_nirnaya (requested_horizon, claim_grain, grading_basis) — or qualification JSONB (§10.3)", "interface packet only: platform/src/lib/retrieval/registry/layers/L3_kala/query_moorti_nirnaya.ts:81 (as_of default), platform-mcp/src/tools/kala_views/now.ts:498-550"]
must_not_touch: ["bg_transit_moorti, brahmagyan/** (L0 — the grant is a migration owned by G21/PR #2717; this brief adds the guard, not the grant)", "ephemeris_daily / bg_ephemeris (L0)", "services/gochara_v3/context.py:487-530, mechanisms/w22_moorti_nirnaya.py (Gochara-owned readers — a contradiction between them is raised, not edited)", "Kṣetra S1 (its own stream)", "supabase/migrations/525_kala_moorti_nirnaya.sql, migration 670 (applied)", "WriterBase / orchestrator contract"]
target_state_data_plane: "PRODUCER_READY (stage 3); DATA_ACCEPTED when a rebuild succeeds on production (grant present) and 670 (a)–(h) returns TRUE with stamps; CONSUMER_INTEGRATED when now.ts/query_moorti_nirnaya and Gochara's context prefetch read the stamped rows"
target_state_campaign: "ANALYZED → ENRICHED at stage 3; blueprint §4: 'cannot rebuild' today (G21)"
wave: "W2 (foundation)"
shape: single asset, rows (chart × graha × sign-run over a rolling −60/+400-day horizon; 8 grahas, Moon excluded by design)
evidence_base: >
  Source read directly on 9feac52d7 [V]; migration 525, migration 670 ka_moorti_nirnaya contract
  (a)–(h) [V]; blueprint v5.0 §3.5 row 10 / §4 / §5.3 G21 / §16.2 (WP9) [A]; no database query.
does_not_authorize: any code, migration, grant, build or serving change.
changelog:
  - "1.0 (2026-09-24): first issue; awaiting independent review."
---

# `ka_moorti_nirnaya` elevation brief — the ingress grade, guarded and dated honestly

## §0 — The recommendation, in one paragraph

`ka_moorti_nirnaya` grades each sign-ingress of eight grahas (`MOORTI_GRAHAS`, Moon excluded by
declared design, `logic.py:23-29` [V]) as svarṇa/rajata/tāmra/loha by the Moon's nakṣatra offset
from the natal Moon at the ingress, looked up **verbatim** in L0's `bg_transit_moorti`
(`writer.py:164-170` [V]; Phaladeepika 26 / BPHS 28), over a `date.today()` −60/+400-day horizon
(`:203-205` [V]) at one ayanāṃśa offset. Its integrity contract is the best in the layer —
(a)–(h) including `moorti_computed` **re-derived** rather than self-reported (670 `:1079-1090`,
§N.8) — and its DDL enforces the computed/uncomputed consistency (525 `:92-100`). Three things are
wrong. (1) `_fetch_moorti_table` has **no guard**: no SAVEPOINT, no try/except (`:164-170`); with
the F4 grant on `bg_transit_moorti` missing on the build role (G21; migration 1073 / PR #2717 not
on this base), the SELECT raises and the **whole asset build fails** — blueprint §4: *"cannot
rebuild"*. An L0 permission defect becomes an L3 outage instead of an F06 `unavailable`. (2) The
rule is defined at the ingress **instant**; the writer grades at the ingress **date** using the
Moon's noon-UT knot (`moon_nak_by_date[start_date]`, `:225-227,:240-262` [V]). The Moon moves ~one
nakṣatra per day, so for an ingress far from noon UT the offset can be off by one and the grade
by one tier — a `date_grain` approximation of an instant rule (blueprint §16.2 WP9: *"ingress-
instant grading"*), undeclared on the row: `moorti_computed=true` reads as *computed at the
ingress*. (3) The horizon is the server's build date (SC-1), unstamped, and the wrapper's `as_of`
defaults to the server's date (`query_moorti_nirnaya.ts:81`). Also: Gochara's `context.py:487-530`
prefetches every row for `w22_moorti_nirnaya` while `w22`'s own docstring says the data is *"NOT
plumbed into ClassContext"* (`:162`) — a contradiction inside the consumer. Recommendation:
**`ENRICH_CORRECT` + `QUALIFY_LIMIT`** — SAVEPOINT + try/except around the L0 read → a build that
writes `completeness_state='unavailable'`, `reason='l0_table_unreadable'` rows (or an honest
refusal preserving the prior partition — §10.1) instead of failing; `grading_basis='ingress_date_
noon_ut'` and `claim_grain='date_grain'` stamped now, with an **ingress-instant grading DEMAND**
on the position reference (the Graha Sañcāra brief's route/kernel) for a later generation;
`requested_horizon` + coverage; `as_of` in the chart's zone. Decisions: failure mode and the
instant DEMAND (§10).

---

## §1 — Already established

| record | says | delta on this base |
|---|---|---|
| Register §5 (ka_moorti_nirnaya row) | contact overlay (ingress quality) | — |
| Blueprint §3.5 row 10 (`:326`), §4 (`:398`), §5.3 G21, §16.2 (`:908`) | **unguarded read, grant missing (F4)**; *cannot rebuild*; `try/except + SAVEPOINT boundary → F06 unavailable; ingress-instant grading (kernel, WP9); coverage = requested horizon; overlay stamps`; consumers: century v3 (actual input), Kṣetra S1 (ruled 4) | this brief |
| Migration 525 (`:64-100`) | DDL: `moorti_name ∈ {swarna, rajata, tamra, loha}`, `quality_tier 1..4`, `nakshatra_offset 1..27`, `moorti_computed` + **consistency CHECK** (computed ⇔ all grade fields non-null), DATE windows, truncation flags, `UNIQUE(chart, ayanamsha, graha, window_start)` | no horizon/grain/basis column |
| Migration 670 (`:1017-1220`) (a)–(h) | grade = L0 row; offset key resolves; offset is a restatement of the two indices; janma fact id resolves to this chart; runs tile the horizon; `moorti_computed` re-derived (§N.8); same horizon per chart; labels restate `reference_signs` | strong; (f) already asserts the flag honestly — but "computed" ≠ "computed at the instant" (§3) |
| `logic.py:38-52` | *start-truncated runs are not graded because their TRUE ingress is unknown — grading on the horizon's first day would pass off "Moon's nakṣatra on the day we started scanning" as "at ingress"* | the same reasoning applies one step further: the ingress *date* is not the ingress *instant* |
| Gochara `context.py:487-530` vs `w22_moorti_nirnaya.py:28,:153-162` | prefetch exists (`window_start/end, moorti_name, moorti_computed`, ordered) vs *"NOT plumbed into ClassContext"* | contradiction — raised (§4.7) |
| Seed (`asset_registry_seed.ts:2557-2572`) | `depends_on: ['ga_positions', 'bg_ephemeris', 'bg_transit_rules']` | the L0 table is `bg_transit_moorti` (migration 401), seeded by `bg_transit_rules` — declared via its writer, acceptable |
| `now.ts:498-550` | serves current rows; `moorti_computed=false` rows carry null grade fields **verbatim, never backfilled** (`:520-521`) | good; preserved |

---

## §2 — Current-state evidence (contract §2)

### 2.1 Registration [V]
`storage_type: 'postgres_table'`, `target_table: 'kala_moorti_nirnaya'`, `scope: 'per_chart'`,
`catalog_status: 'CURRENT'`; 71 rows live [A]. Cost: one ephemeris range read (9 bodies incl.
Moon × ~461 days) + one swisseph call; cheap.

### 2.2 The code [V]
- **Inputs**: natal Moon fact (`:69-73`, `:121-136`); `bg_transit_moorti` read **unguarded**
  (`:164-170`: bare cursor, no SAVEPOINT/try; on an empty table → honest refusal `:196-200`; on a
  permission error → exception propagates); `ephemeris_daily` tropical (`:76-80`); one offset at
  `today` (`:138-142`, `:207`).
- **Horizon**: `HORIZON_BACK_DAYS=60`, `FORWARD=400` (`:66-67`) around `date.today()` (`:203-205`);
  `_has_complete_daily_series` per body incl. Moon (`:108-118`) else refusal.
- **Rows** (`:228-290`): per graha `detect_sign_runs`; `moorti_computed = not start_truncated`
  (`:238`); the Moon's nakṣatra **on the ingress date** from `moon_nak_by_date` (`:225-227`);
  `nakshatra_offset_from_janma` (`logic.py:126-134`, 1..27); L0 row copied verbatim
  (`moorti_name, quality_tier, phala_brief, classical_citation`); a missing Moon knot for that
  date → `moorti_computed=False` (`:262-266`, honest gap).
- **Write**: DELETE by chart after the full candidate is assembled (`:302-308`), INSERT
  `ON CONFLICT DO NOTHING` (`:103`); never commits.

### 2.3 Consumers (grep `kala_moorti`, tests/seed/generated excluded) [V]
| consumer | reads | role |
|---|---|---|
| `query_moorti_nirnaya.ts` | rows; `MAX_LIMIT 50` + `truncated`/`total_matching`; `as_of` default `new Date()` (`:81`) | served `relevance_navigation` |
| `now.ts:498-550` | current rows; nulls verbatim | served |
| `gochara_v3/context.py:487-530` | all rows by chart+ayanāṃśa (`window_start/end, moorti_name, moorti_computed`) for `w22_moorti_nirnaya` | `applicability` (century v3 actual input) — while `w22:162` says not plumbed |
| Kṣetra S1 (blueprint: ruled 4) | mūrti grade as applicability | `applicability` |
| Kāla writers, L4 | none | — |

**Live-path statement.** Served ×2; consumed by Gochara's context prefetch (and, per ruling 4, by
Kṣetra S1); **not rebuildable** today on the build role (G21).

### 2.4 Epistemic class
| field | class | authority | note |
|---|---|---|---|
| sign-run windows, `target_sign` | `COMPUTED_FACT_CONFIGURATION` | L0 knots | `date_grain`, `noon_ut_knot`, single offset |
| `moon_nakshatra_idx_at_ingress` | computed **on the ingress date** | L0 Moon knot | approximates the instant value; ±1 nakṣatra possible |
| `nakshatra_offset` | restatement (670(c)) | this logic | — |
| `moorti_name`, `quality_tier`, `phala_brief`, `classical_citation` | `QUALIFIED_RULE`, `verse_cited` | L0 `bg_transit_moorti` | copied verbatim — correct |
| `moorti_computed` | earned flag (670(f)) | this writer | means "run start inside horizon and Moon knot present", **not** "graded at the instant" |
| horizon | server build date | this writer | undeclared |

### 2.5 Ladders
`PLAN_REVIEWED`; W2 source accepted; **rebuild blocked** (G21). t3: no event.

---

## §3 — The failure (contract §3): one falsifiable problem

| field | content |
|---|---|
| Observed behavior | Click Build on a role without SELECT on `bg_transit_moorti`: `_fetch_moorti_table` raises inside the writer's transaction, the orchestrator records the asset failed, and the chart's prior 71 rows — which the writer deliberately does not delete before the candidate is complete — survive by accident of ordering, with no row anywhere saying "L0 unreadable". Separately, take Mars ingressing Aries at 22:00 UT on date D: the writer keys the grade on the Moon's nakṣatra at **noon UT of D** — ten hours earlier, up to ~5° of Moon motion — and if the Moon crosses a nakṣatra boundary in those hours the stored `nakshatra_offset` and `moorti_name` are one step off, with `moorti_computed=true` |
| Evidence | `writer.py:164-170,:196-200,:203-207,:225-227,:238-266,:302-308`; `logic.py:38-52`; 525 `:92-100`; 670 (f) `:1079-1090`; blueprint §4 `:398` [V]/[A] |
| Expected contract | F06 (a dependency failure is an `unavailable` state, never a build outage — and never a fabricated grade); §N.8 (a `computed` flag names exactly what was computed); B1 (`claim_grain` declared; an instant rule graded at date grain is `algorithmic_approximation`); SC-1 (horizon declared); SC-8 (the grading instant comes from the position reference, one computation); B5 |
| Defect class | **unguarded dependency** (outage instead of state) + **grain mismatch undeclared** (date-grain grade of an instant rule) + **wrong context** (build-date horizon; server-date `as_of`) + **consumer contradiction** (Gochara) |
| Impact | the asset cannot be rebuilt on production until an L0 grant lands, and would fail loudly rather than degrade; a fraction of grades (ingresses far from noon UT with the Moon near a nakṣatra boundary) are one tier off and unmarked; Gochara's century reads rows whose grain it cannot see |
| Non-claim | the fraction of off-by-one grades is **not measured** (needs the instant computation to compare); no claim the L0 table is wrong; the 71-row count and "cannot rebuild" are [A] |

---

## §4 — The semantic delta (contract §4)

1. **L3-Q served.** Q05 (an ingress grade as one qualified voice beside other overlays); Q-K06.
2. **Guard (F06).** `_fetch_moorti_table` inside `SAVEPOINT sp_moorti_l0` + try/except; on
   failure: **§10.1** — either (a) write the sign-runs with `completeness_state='unavailable'`,
   `reason='l0_bg_transit_moorti_unreadable'`, grade fields null (the 525 CHECK already permits
   `moorti_computed=false` with nulls; `reason` is the new field), or (b) refuse with the prior
   partition preserved and the reason in `notes`. Recommendation (a): the sign-runs are real L0
   facts and a consumer can still see *that* an ingress happened. Never a fabricated grade.
3. **Grain and basis declared (B1/B2).** Every row: `claim_grain='date_grain'`, `time_basis=
   'noon_ut_knot'`, `grading_basis='moon_nakshatra_on_ingress_date'`, `source_qualification`:
   the L0 lookup `'verse_cited'` (carrying `classical_citation`), the date-grain keying
   `'algorithmic_approximation'`; `moorti_computed` keeps its 670(f) meaning and the new basis
   field carries the honest caveat.
4. **Ingress-instant grading — a DEMAND, not a fabrication.** A later generation grades at the
   ingress instant: the sign-ingress root-find and the Moon's longitude at that instant from the
   position reference (Graha Sañcāra brief §4.3 — the served route's `bg_ephemeris_engine`
   computation or its shared kernel; MEAN node irrelevant here; Swiss/Moshier observed). Until
   that reference is landed, this brief **does not** add a second swisseph integration here
   (SC-8: no rival computations); it stamps the approximation and records the DEMAND with
   `grading_basis` set to switch to `'moon_nakshatra_at_ingress_instant'` when it lands. The
   comparison of the two bases on the canonical chart is the ablation (§4.10) and the first
   measurement of the off-by-one fraction.
5. **Horizon declared (SC-1/B5).** As the Kota brief §4.2: `as_of` from `ctx.config` (chart-zone
   today by default), `requested_horizon` on every row, per-build `coverage` with
   `partitions_searched=[8 grahas + Moon]`, `exclusions` (refused bodies; uncomputed runs with
   reason), `unsearched_regions` (spans dropped on a horizon move), `completion_detector=
   '_has_complete_daily_series'`.
6. **`as_of` (SC-1) at the wrapper** in the chart's zone, echoed.
7. **Gochara contradiction raised.** `context.py:487-530` prefetches; `w22:162` says not plumbed
   — Gochara's owner reconciles; this brief's rows gain `grading_basis` so that reconciliation
   can decide whether a date-grain grade is admissible as a century input.
8. **Old vs new.** Positive: rebuild with grant → 71-ish rows with stamps + coverage. Negative:
   grant missing → rows `unavailable` with reason (today: build fails). Boundary: an ingress at
   23:50 UT with the Moon 0.2° before a nakṣatra boundary at noon → today graded on the earlier
   nakṣatra; after (instant generation) on the later; the row says which basis. Missing: Moon knot
   absent for the date → `moorti_computed=false` (unchanged) + reason. Duplicated: n/a.
9. **Simpler baseline.** The rows as they are, with the grant.
10. **Ablation.** Grade the canonical chart's ingresses under both bases: the set of rows whose
    tier differs is the measured off-by-one fraction; if it is zero over the horizon, the instant
    generation is decorative for this native and the brief says so.

---

## §5 — Preservation, fences, migration, rollback

- `PRESERVE`: the verbatim L0 lookup; `moorti_computed` semantics (670(f)); the start-truncation
  rule (`logic.py:38-52`); the honest Moon-gap handling; assemble-before-delete; the 525 CHECK;
  `now.ts`'s null carriage.
- `ENRICH_CORRECT`: the guard; `as_of` from config.
- `QUALIFY_LIMIT`: `claim_grain`, `grading_basis`, `source_qualification`, `requested_horizon`,
  coverage, `reason`.
- **DEMAND**: ingress-instant grading via the position reference (Graha Sañcāra brief); the F4
  grant (G21 / migration 1073, PR #2717) — both outside `may_touch`.
- **Migration**: one additive DDL (stamps + `reason`) or JSONB (§10.3); the 525 consistency CHECK
  is unchanged.
- Fences: L0 untouched; Gochara readers untouched; Kṣetra S1 untouched.
- Rollback: additive; the guard only widens the set of buildable situations.

---

## §6 — Lenses A–J

| lens | answer |
|---|---|
| A | `ka_moorti_nirnaya`, L3 rows; epistemic: L0/L1 facts + cited L0 rule applied at date grain; placement correct; `ENRICH_CORRECT + QUALIFY_LIMIT` |
| B | declared edges real (`bg_transit_rules` seeds the table); no hidden read; fan-out: two served, Gochara context, Kṣetra S1 |
| C | invariants: 670 (a)–(h); every row names basis + horizon; an unreadable L0 → `unavailable` rows, never an exception past the writer; grade = L0 row (a). Golden: canonical chart on a fixed fixture; boundary: ingress near a Moon nakṣatra boundary |
| D | the instant computation (DEMAND); the grant (G21) |
| E | served ×2; Gochara (contradictory internally); Kṣetra S1 |
| F | `grading_basis`, `completeness_state`, `reason`, coverage machine-readable |
| G | cheap; justified no-change |
| H | idempotent; savepoint boundary; refusal on incomplete series; no credentials |
| I | files in `may_touch`; W2; one additive DDL; DEMANDs named with owners |
| J | this brief; §7; review; the two-basis comparison when available |

---

## §7 — Proof matrix (tier `[U]` unit, `[I]` DB fixture, `[S]` served, `[X]` gated on the DEMAND)

| proof | tier | fixture / command | expected | invariant | detector fails when… | evidence path |
|---|---|---|---|---|---|---|
| Positive | I | fixture with grant; `as_of` fixed; rebuild; 670 | rows with `grading_basis`, `requested_horizon`, coverage; 670 TRUE | (a)–(h) + stamps | absent / FALSE | integrity SQL |
| Negative (guard) | I | revoke SELECT on `bg_transit_moorti` in the fixture role; rebuild | build **succeeds**; rows `completeness_state='unavailable'`, `reason='l0_bg_transit_moorti_unreadable'`, grade nulls; 525 CHECK holds | F06 | exception propagates (today) / a grade fabricated | writer test |
| Relevant influence | U | natal Moon nakṣatra +1 | every `nakshatra_offset` −1 (mod 27); tiers per L0 table | isolation | offset unchanged | unit |
| Irrelevant control | S | `as_of` UTC vs chart zone, same instant | same current rows | zone-invariant | differs | wrapper test |
| Duplication | I | rebuild twice, same `as_of` | identical rows | idempotent | accretion | writer test |
| Context | I | Moon knot missing for one ingress date | that row `moorti_computed=false` + `reason='moon_knot_missing'` | honest gap | graded / no reason | writer test |
| Boundary | U | Moon at noon UT 0.1° before a nakṣatra boundary on the ingress date | grade keyed on the earlier nakṣatra; `grading_basis='…_on_ingress_date'` | declared basis | basis absent | unit |
| Boundary (instant) | X | same fixture graded at the ingress instant | grade keyed on the later nakṣatra; basis `'…_at_ingress_instant'` | DEMAND landed | — (gated) | ablation record |
| Delivery | S | sentinel `grading_basis` on one row | reaches `now.ts` and `query_moorti_nirnaya` envelope | survives | absent | MCP/route test |
| Revision | I | `bg_transit_moorti` row for offset 5 changed in fixture; rebuild | that tier changes; others fixed; 670(a) TRUE | L0 authority | stale copy | writer test |
| Value | S | frozen Q-K06 question | a grade with citation, basis, horizon; baseline gives grade + citation | — | no basis | baseline |
| Evaluation | — | `not_applicable` | — | — | — | — |

Binding: **OFFERS** B1 (`claim_grain`, `time_basis`, `inclusivity='closed_closed'`), B2
(`completeness_state` incl. `unavailable` with reason, `epistemic_class`, `source_qualification`
split, `operator_role='applicability'`), B3 (`window_ref` with `generation` = FORMULA_VERSION +
horizon + basis), B5 (`coverage`). B4: per-graha `independence_group` (`declared_lineage`; eight
grahas from one ephemeris + one Moon reference — declared, not nine witnesses). **DEMANDS** the
ingress-instant computation from the position reference (SC-8) and the L0 grant (G21).
**Asset-local:** `grading_basis`, `reason`, `moorti_computed`, `requested_horizon`, truncation flags.

---

## §8 — Prioritization

(1) the guard (the build outage; unblocks rebuild the moment the grant lands, and degrades
honestly until then) → (2) basis + grain stamps (the unmarked approximation) → (3) horizon +
coverage → (4) `as_of` at the wrapper → (5) the instant DEMAND (waits on the Graha Sañcāra
reference) → (6) Gochara's internal contradiction to its owner. T0; W2; consumers: Gochara
century (applicability), Kṣetra S1.

---

## §9 — Disposition and target state

`ENRICH_CORRECT` + `QUALIFY_LIMIT`. Data-plane: `PRODUCER_READY` after §7 `[U]`/`[I]`;
`DATA_ACCEPTED` when a production rebuild succeeds under the grant and 670 TRUE with stamps;
`CONSUMER_INTEGRATED` when the served surfaces and Gochara's prefetch carry `grading_basis`.
Campaign: `ANALYZED → ENRICHED`. Non-claims: no `VALUE_EVALUATED`; the off-by-one fraction is
unmeasured until the instant basis exists; the grant is not this brief's to land.

**Walkthrough (ordinary period).** "What is the quality of Jupiter's current sign transit?" →
one current row: Jupiter in Taurus since D, `moorti_name='rajata'`, `quality_tier=2`, the L0
citation, `grading_basis='moon_nakshatra_on_ingress_date'`, `claim_grain='date_grain'`,
`requested_horizon` shown. The reader gets a cited grade and knows it was keyed on a date.

---

## §10 — Decisions for the native

| # | decision | recommendation |
|---|---|---|
| 1 | **Guard failure mode: write `unavailable` sign-run rows with reason (a), or refuse preserving the prior partition (b)?** | (a) — the ingress facts are real; only the grade is unavailable |
| 2 | **Record the ingress-instant grading DEMAND on the position reference (no second swisseph integration here)** | yes; measure the off-by-one fraction when it lands |
| 3 | Stamp home: columns (`grading_basis`, `reason`, horizon) vs JSONB | columns — Gochara filters on them |
| 4 | Route the Gochara `context.py`/`w22` contradiction to its owner | yes |

---

## §11 — Not verified here

1. The live grant state on `bg_transit_moorti` and whether migration 1073 / PR #2717 has landed
   since this base — "cannot rebuild" is the blueprint's record [A].
2. The 71-row count; the 670 live result.
3. The fraction of ingresses whose date-grain grade differs from the instant grade — unmeasurable
   without the instant computation.
4. Whether Kṣetra S1 reads this table on its branch (ruling 4 recorded in the blueprint) — not
   checked on `stage3`.
5. No database query; no test run.
