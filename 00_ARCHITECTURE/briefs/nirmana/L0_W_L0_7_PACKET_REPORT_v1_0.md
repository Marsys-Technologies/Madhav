---
artifact: L0_W_L0_7_PACKET_REPORT
version: 1.5
status: FIXTURE_BUILT_GATE_MAPPING_HELD
packet: W-L0-7 (consumer-perturbation harness)
session: NIRMANA_L0_BRAHMAGYAN_EXECUTION_20260921
branch: l0/brahmagyan-exec
date: 2026-09-26
amendments: >
  v1.1 (2026-09-26) — strategy item 1 (BLOCKING cross-packet collision): the v1.0
  baseline froze R3's pre-registration on sunapha's pre-1123 sutravali link set
  {7ede2ed9…, a5d58ce9…} while W-L0-3's migration 1123 proves 7ede2ed9… a false
  parenthetical attribution and replaces the set with {a5d58ce9…, cf36fd63…}. Fixed:
  state pin declared, R3 re-expressed against the post-1123 set as the real target,
  re-measure gate added, full pin audit of every production-read value added, FK
  mechanics of the perturbation declared, R2's two post-states spelled out.
  v1.2 (2026-09-26) — R3 prediction corrected before any harness run (pre-registration
  discipline): v1.1 predicted classical_sources_jsonb goes NULL; mechanism read shows
  it does NOT — the fact's own citations survive; only catalog_ids and rule_ids empty
  out. Fixture-construction disclosure added (schema source, synthesized yoga_label
  facts, catalog seed source, 1123 patch-apply oracle).
  v1.3 (2026-09-26) — guarded-contract discovery, disclosed before fixture build:
  migrations 1035/1036's mutation guards and capture triggers probed LIVE in
  production; production has never admitted a data-plane generation (the fixture is
  the first execution of the decorated path). Two findings handed up unfixed:
  F-W-L0-7-1 (L2 open-before-bind order; harness primes one bind per R3 run),
  F-W-L0-7-2 (fact_category_ownership gap — graha_position/yoga_label and 11 more
  production categories unowned; the guarded path cannot admit the writes that
  produced production's own chart_facts). Seeding design finalised around both:
  chart_facts seeded pre-trigger + synthesized capture-snapshot rows; ga_yoga's
  generation REAL via the R1 baseline (ordering constraint R1 before R3).
  v1.4 (2026-09-26) — two corrections to v1.3, found while deriving the builder:
  (1) the L2 bind builds its pg_temp shadows from `l1_data_plane_row_snapshots`
  (1036:861-877), NOT `l1_data_plane_fact_snapshots` — v1.3 named the wrong
  snapshot table; the synthesized capture artifacts target row_snapshots (with
  fact_snapshots dual-written for fidelity, as the real capture does).
  (2) The handoff summary's claim of a prior 1.06 GB JSONL fixture-data export
  is a confabulation — no such export exists on disk; the fixture builder
  produces all reference-data exports fresh. Also established: synthesized
  completed generations are guard-respecting by construction (INSERT in empty
  'building' state → declare partition_contexts → insert generation_partitions
  → UPDATE to 'complete' → insert head; the guard permits exactly this path,
  1035:383-440), and `l1_data_plane_generation_partitions` carries an FK to
  `l1_data_plane_partition_contexts` (declaration precedes receipt).
  v1.5 (2026-09-26) — fixture builder COMPLETE (commits 8d24b37e0, a4b7a251c;
  33/33 gates, two consecutive fresh-DB runs; rehearsal DB madhav_l0w7_fixture).
  1123 oracle green both directions (state-A 87b69704… == old_digest == production;
  rolled-back state-B == f1d56d0c… new_digest; bg_rules contract accepted as-is,
  no constant patch). Correction to v1.2 item 4's predicted verify string:
  'not_a_yoga_qualifier' appears nowhere in migration 1123 — measured post-patch
  distribution is no_concept_reference_in_window×2,986 / ambiguous_reference×7 /
  reference_not_in_catalog×2 / linked×7; remedy drift spellings 0 post-patch.
  1120 disclosed-skipped (member tables outside the 27-table fixture set — it
  would refuse at 1120:55-60); 1121/1122/1123 applied verbatim. Post-1122
  bo_laksana closure = 12 ga_* (no diff vs probe); 11 generations synthesized.
  New findings F-W-L0-7-3 (175,949/421,096 production chart_facts rows are
  multi-valued and would fail the capture CHECK) and F-W-L0-7-4
  (classical_text_chunks.chapter is a page number; sunapha citations carry no
  chunk_id — linkage is by text). Builder's first-pass notes cited a nonexistent
  brief/branch and falsely declared 1120–1123 absent — corrected in
  REHEARSAL_NOTES v1.1; every builder number accepted here was re-verified
  against the fixture DB first.
---

# W-L0-7 Packet Report — Consumer-perturbation harness

## Packet scope (strategy §4.2 W-L0-7)

The strategy's detector, verbatim: "a shared instrument, not an L0 judgement: on a
disposable snapshot, perturb a named L0 fact (a rule row, an alias, a constant) and run a
fixed set of L1–L3 readings; the detector is that the consuming reading **moves**, and
moves in the way the fact predicts. A consumer that does not move has not consumed.
Findings land in L1–L5's plans. Detector for the packet itself: the harness exists, runs
in CI, and shows at least one L2 reading moving when `bg_yogas` is perturbed."

Depends on W-L0-1 and W-L0-2 (both closed). Verifies L0's CONSUMERS; never judges an L0
asset. Any consumer that fails to move is recorded as a finding for L1–L5's plans — it is
never repaired in this lane.

## HELD item, flagged up front (strategy instruction 2026-09-25)

This packet's "moves as the fact predicts" detector is a **domain-correctness detector by
construction** — it is D4-shaped (template §4.1: "feed a case that must not fire; check it
doesn't") at the consumer level. The synced certification standard
(`ASSET_ELEVATION_TEMPLATE_v1_0.md` v1.1, §4) makes `Dom` an always-applies gate with
`NO_DETECTOR` blocking certification, while native Decision 11 (2026-09-25) assigned
domain correctness to the reasoning layer above the data plane — and the template cites
Decision 11 zero times. The strategy session holds this ruling **[OPEN]**.

Per that instruction: the **baseline measurement** and **harness construction**
(authorized 2026-09-26) are ruling-independent and proceed. The harness's **gate
mapping**, any **`Dom`-coverage claim**, and any **certification verdict** are HELD until
the ruling lands. Template v1.1 §4 was read before this design, as instructed.

## State pin — declared 2026-09-26 (strategy item 1: the v1.0 baseline carried an unstated pin)

**The defect.** v1.0 froze R3's prediction on sunapha's production link set
`{7ede2ed9-ceec-5fe5-910f-242b2face906, a5d58ce9-5331-5db4-a803-41d9530e45fc}` — measured
against **pre-1123 production (state A)** — without naming that state. W-L0-3's migration
1123, authored in the same session, proves `7ede2ed9…` a false parenthetical attribution
(killed → `no_concept_reference_in_window`), keeps `a5d58ce9…`, and adds
`cf36fd63-ba97-5ead-ad17-de9054fc051f` (newly resolved). Post-1123 sunapha's link set is
**`{a5d58ce9…, cf36fd63…}`** — count stays 2, identity changes (verified against 1123's
backfill table and its DOWN block, which restores `7ede2ed9…`).

**The pin, declared.** Every production-read value in this baseline was measured against
**state A (pre-1123 production, 2026-09-26)**. **Migration 1123 is named as the event
that invalidates the R3 pre-registration.** The harness's reference target is the
**post-1123 state B**: the disposable snapshot applies the held migrations on the fixture
— the established rehearsal precedent (1123/1124 rehearsed green against a throwaway
instance in W-L0-5's gate set, 2026-09-25) — so the instrument never asserts on
`7ede2ed9…`, a row this lane has already disproved. A harness asserting a prediction
pinned to a disproved link would be a detector certifying a known falsehood — the §N.8
defect class.

**Re-measure gate.** Before any assertion, the fixture builder verifies the snapshot's
state structurally: `unlinked_reason` column present AND sunapha's link set exactly
`{a5d58ce9…, cf36fd63…}`. If a snapshot is ever built without 1123 applied, R3's
pre-registration is re-derived from 1123's backfill table before the harness runs, and
the deviation is reported, not silently absorbed.

**Pin audit — every production-read value in this baseline × do 1120–1124 change it**
(grepped across all five held migrations, 2026-09-26):

| value | used by | changed by | verdict |
|---|---|---|---|
| `brahma_yoga_catalog` row `sunapha` + its `classical_citations` | perturbation target, R2, C0 | nothing — 1120/1121/1122/1124: 0 refs; 1123 refs are read-only digest guards (:108, :148) | pin-safe |
| `ga_yoga_firings` row (482012f1…, surya_siddhanta_classical, sunapha) | R1, R2 | nothing — 0 refs in all five | pin-safe |
| `chart_facts` (R1's writer input) | R1 | nothing — 0 refs in all five | pin-safe |
| sunapha's `sutravali_rules` link set | R3 | **1123** (backfill: −`7ede2ed9…`, +`cf36fd63…`) | **COLLISION — fixed by this section** |
| `sutravali_rules.school` / `qualification_state` | not read by R3's bridge (it reads `yoga_canonical_id`, `rule_id` only) | 1124 adds the columns | pin-safe |
| `brahma_dosha_catalog` id set (R3's dosha leg) | R3 | 1124 refs are read-only joins/guards; the UPDATE targets `bg_parihara_rules` | pin-safe |
| `classical_text_chunks` (R3's chunk validation) | R3 | 1123/1124 refs are read-only witness guards | pin-safe |
| `brahma_ontology` | not read by the frozen reading set | 1121 (relation-type class), 1123 (synonyms) — both additive | out of set, noted |

## Reading set — enumerated from the W-L0-2 declared-use register, mechanism verified against code (2026-09-26)

`bg_yogas` produces exactly one table: `brahma_yoga_catalog`
(`l0_declared_use_register_v1.json`, producer_files.bg_yogas). Its consumers, fixed as the
reading set:

| id | layer | reading | mechanism (verified) | register entry |
|---|---|---|---|---|
| R1 | L1 writer | `ga_yoga_writer.py` per-chart firing build → `ga_yoga_firings` | `_load_yoga_catalog` (ga_yoga_writer.py:160) loads every catalog row; the catalog loop evaluates each row's `formation_rule_jsonb` and writes firing rows | writer_side_reads: ga_yoga ← brahma_yoga_catalog |
| R2 | L1 serve | `get_yoga_firings` capability | `LEFT JOIN brahma_yoga_catalog c ON c.canonical_id = f.yoga_canonical_id` (get_yoga_firings.ts:208) selecting `c.classical_citations AS catalog_classical_citations` (:195) | serve_time_reads: interpretation |
| R3 | L2 writer | `bo_laksana.py` classical-source bridge | `_build_classical_catalog_lookup` (bo_laksana.py:1588) preloads catalog ids + `sutravali_rules.yoga_canonical_id`; `_build_classical_sources` (:1684) bridges L1 facts whose `fact_subject` is a catalog id (categories in `_YOGA_DOSHA_CATS`, :1582) | writer_side_reads: bo_laksana ← brahma_yoga_catalog |
| R4 | L1 writer (optional leg) | `ga_structural_writer.py` yoga label pass (Kemadruma branch) | writer_side_reads: ga_structural ← brahma_yoga_catalog. **Optional:** kemadruma is one of the 11 duplicate canonical_ids in W-L0-9 seam 1 (dosha AND yoga); this leg's reading shape may change with the W-L0-9 ruling [OPEN], so it is not in the frozen core set |
| C0 | L0 own serve (control) | `query_yoga_catalog` capability | paginated catalog query; sanity leg that the perturbation landed — NOT a consumer judgement | serve_time_reads: interpretation |
| L3 | — | **none — verified empty leg** | register records no `ka_*` read of `brahma_yoga_catalog`; grep of `L3_kala/` serve surfaces and of all `ga_yoga_firings` TS readers confirms no L3 consumer; strategy's third-way check (2026-09-26) confirms the full consumer list is exactly R1/R2/R3/C0 + excluded R4. An honest empty leg, not a gap — L0 is a reference layer and lack of a reader is not redundancy | — |

Second-order expansion pool (readers of the L1 product `ga_yoga_firings`, not of the
catalog directly; outside the register's bg_* scope, named for completeness, NOT in the
frozen set): `register_d8_assess_domain.ts`, `register_d9_judgment.ts`,
`get_yoga_dosha.ts`, `source_query_availability.ts`, `tool_name_bridge.ts`,
`editorial.ts`.

The frozen core set is **R1, R2, R3, C0** — small, deterministic, each with a named
mechanism and a pre-registered prediction below.

## Perturbation — identified, prediction written before any run

**Withdraw the `brahma_yoga_catalog` row `canonical_id = 'sunapha'` on the disposable
snapshot** (DELETE; the snapshot is rebuilt per harness run — no production change).

**FK mechanics, declared** (probed 2026-09-26): `sutravali_rules`, `ga_yoga_firings` and
`brahma_yoga_catalog` carry **no foreign-key constraints at all** — referential integrity
is maintained by the writers and the registry digest contracts, not by the database. The
DELETE is therefore mechanically clean: no FK blocks it, nothing cascades. This is itself
the reason the harness must exist: nothing at the database level stops a consumer from
serving a withdrawn fact.

Why this row — four grounded criteria (read-only production probes, 2026-09-26):

1. **Catalog-loop evaluated.** `sunapha` appears nowhere in `ga_yoga_writer.py` as code —
   its firing path is the plain `formation_rule_jsonb` catalog loop, the simplest
   predictable mechanism. `DETECTOR_INSERT_IDS` (ga_yoga_writer.py:2411) is exactly
   {`dhana_yoga_house_lords`, `raja_yoga_kendra_trikona`, `sarasvati_yoga`,
   `lakshmi_yoga`, `vipareeta_raja_yoga`} — sunapha is not a detector id.
2. **Carries classical citations** (`has_citations = true`) — R2's join has something to
   lose. School: parashari; category: other; `formation_rule_jsonb` present.
3. **Referenced by `sutravali_rules.yoga_canonical_id`** — state A: exactly 2 rules
   (`7ede2ed9…`, `a5d58ce9…`); **state B (the harness reference): exactly 2 rules
   (`a5d58ce9…`, `cf36fd63…`)**, per 1123's replay-verified backfill. R3's rule-join leg
   has something to lose in both states; the pin section above governs which set is
   asserted.
4. **Fires on the native chart** `482012f1-710e-4a25-994a-93821f5871aa` under exactly one
   ayanamsha — `surya_siddhanta_classical`, one row,
   `strength_label = computed_extension` — giving R1 a narrow, exact prediction on the
   established fixture chart (the WP-1.3(f) integration tests use the same chart).

## Predicted movement — pre-registered against state B; the harness PASS is exactly these movements

Harness sequence (the ordering is part of the prediction): **(0)** build snapshot, apply
held migrations, verify the state-B structural gate; **(1)** baseline: run
`ga_yoga_writer` for the fixture chart → firings; run `bo_laksana` → bridged rows;
snapshot R1/R2/R3/C0 outputs; **(2)** PERTURB — DELETE the sunapha catalog row; **(3)**
C0 read; **(4)** R2 read against the STALE firings (no writer rerun yet); **(5)** R1
writer rerun; **(6)** R2 read again; **(7)** R3 `bo_laksana` rebuild; **(8)** verdict
against this matrix; findings out, unfixed, to L1–L5's plans.

- **C0 (control, step 3):** `query_yoga_catalog` no longer returns `sunapha` — confirms
  the perturbation landed before any consumer is judged.
- **R2 stale-window (step 4):** `get_yoga_firings` for the fixture chart still returns
  the sunapha firing row (the firing is L1's own data, not yet rebuilt), but its
  `catalog_classical_citations` moves from the seeded citations to **NULL** (LEFT JOIN
  miss). Movement is in the citation field exactly; row presence must NOT move in this
  window — a named non-movement control. This is the production stale-read window: L1
  firings are rebuilt on writer runs, not on catalog changes.
- **R1 (step 5):** after the `ga_yoga_writer` rerun on the perturbed snapshot,
  `ga_yoga_firings` loses exactly the `(fixture_chart, surya_siddhanta_classical,
  sunapha)` row and nothing else; every other firing row is byte-identical (the writer
  is deterministic; the catalog loop simply never evaluates sunapha). A firing that
  survives the withdrawal has not consumed the catalog — or consumed a cache; either is
  a finding.
- **R2 post-rerun (step 6):** the sunapha firing row is now absent from the served
  response entirely — the second, distinct post-state.
- **R3 (step 7):** a `bo_laksana` rebuild on the perturbed snapshot: L1 facts with
  `fact_subject = 'sunapha'` (categories `yoga_label` / `yoga_fires`) move in their
  classical-source bridge. **Corrected prediction (v1.2, before any run):**
  `classical_sources_jsonb` does **NOT** go NULL. `_build_classical_sources`
  (bo_laksana.py:1676-1734) builds the JSONB from four legs — `catalog_ids`,
  `rule_ids`, `text_chunk_ids`, `citations` — and returns `(None, None)` only when
  **all four** are empty (:1719). The `citations` leg is fed by the fact's own
  `fvj.classical_citations` — written at label-pass time by `ga_structural_writer`
  (:2465-2491), which copies the catalog row's citations into the fact's
  `fact_value_jsonb` — so sunapha's facts carry `['bphs:30', 'saravali:38']`
  independently of the catalog row's survival. The exact movement is therefore:
  `catalog_ids: ['sunapha'] → []`; `rule_ids: {a5d58ce9…, cf36fd63…} → []` (the
  **post-1123** set, per the state pin); `citations: ['bphs:30', 'saravali:38']`
  **unchanged**; `classical_sources_jsonb` keeps its citations leg and loses its two
  bridge legs. The 2 sutravali rules lose their parent join (their
  `yoga_canonical_id = 'sunapha'` no longer resolves to a catalog row).
  Named non-movement control — now consistent with the corrected mechanism:
  `_corroboration_count_by_text` (bo_laksana.py:1644-1673) reads exactly that same
  fact-own `fvj.classical_citations` leg and never the catalog, so the per-text
  corroboration count stays at 2 and does NOT move. (v1.1 had predicted a NULL
  `classical_sources_jsonb`, which its own non-movement control already contradicted
  — both read the citations leg; corrected here before measurement, disclosed.)

A consumer that does not move has not consumed → finding for L1–L5's plans, recorded, not
repaired here.

## CI vehicle — named

The established disposable-snapshot pattern: `pgvector/pgvector:pg15` service → extensions
+ supabase-convention roles → schema restore → `npx tsx scripts/migrate.ts` → live scans
(`.github/workflows/fresh_chart_smoke.yml:72-81, 191-221`). The harness reuses this
vehicle: same service, plus a fixture slice (fixture-chart `chart_facts`, the
`brahma_yoga_catalog` / `brahma_dosha_catalog` / `sutravali_rules` reference rows, and
the chunk witnesses the bridge validates), then the sequenced run above. Construction
authorized 2026-09-26 on these terms: build harness + fixture + CI; no gate mapping, no
`Dom` claim, no certification verdict until the ruling; findings to L1–L5 unfixed.

## Fixture construction — disclosed (v1.2, 2026-09-26)

Everything the fixture is made of, and where each piece comes from, stated before the
fixture exists — so a later reader can audit the instrument's inputs rather than trust
its outputs:

1. **Schema source.** Local rehearsal uses DDL derived from read-only production probes
   (`information_schema.columns`, `pg_constraint`, `pg_constraint` FK edges — probed
   2026-09-26, 16 tables: `asset_registry`, `brahma_yoga_catalog`,
   `brahma_dosha_catalog`, `brahma_class_priors`, `brahma_ontology`,
   `brahma_remedy_corpus`, `brahma_dasha_systems`, `chart_facts`, `chart_vichara`,
   `classical_texts`, `classical_text_chunks`, `ga_yoga_firings`, `sutravali_rules`,
   `yoga_families`, `yoga_family_members`, `bodha_msr_signals`), preserving column
   nullability/defaults, CHECK constraints (including the `NOT VALID`
   `chart_facts.verification_pass_status` vocabulary CHECK, preserved as `NOT VALID`)
   and the five production FK edges. Production DDL cannot be pg_dumped locally (no
   local credential by design — all production access is via the read-only MCP query
   tool). **The CI vehicle swaps in the real thing:** the `fresh_chart_smoke.yml`
   pattern pg_dumps production `--schema-only` through cloud-sql-proxy, so CI's schema
   is production's own. One deliberate deviation from the smoke pattern, disclosed:
   **`scripts/migrate.ts` is NOT run** — the fixture must sit at state A pre-patch
   (production lacks 1120–1124's effects, which is exactly the base needed), and
   migrate.ts cannot bootstrap an empty database (the 0000 seed files fake-mark ~80
   foundational migrations).
2. **`yoga_label` fact rows are synthesized, not written by `ga_structural_writer`.**
   The writer itself is NOT run (it is an L1 writer; the harness freezes the L1 fact
   layer by design). The fixture inserts the rows in ga_structural's exact emitted
   shape (:2465-2491): `fact_category='yoga_label'`, `fact_subject=<canonical_id>`,
   `fact_key='yoga_name'`, `fact_value_text=<name_en>`, `fact_value_jsonb` carrying
   `classical_citations` copied from the catalog row, `yoga_group`,
   `uncatalogued: false`, `fire_reason`; `verification_pass_status='single_pass'`
   (inside the NOT VALID vocabulary CHECK); source label
   `brahma_yoga_catalog.label_pass/...`. If ga_structural's emission shape changes,
   this synthesis must be re-derived — a stated maintenance pin.
3. **Catalog seed source.** `brahma_yoga_catalog` is seeded by importing the writer's
   own seed list (`brahmagyan/l0_yogas.py` — the same source production's rows were
   written from), not by hand-transcribing rows. The contract the fixture must
   satisfy: all 17 state-A link targets named by 1123's guards (`parijata`,
   `particular`, `raja`, `sunapha`, `neecha_bhanga`, `durudhura`, `katanidhi`,
   `ubhayachari`, and the nine single-link targets) resolve in the seeded catalog.
4. **1123 patch-apply oracle.** Production's `asset_registry` integrity contract for
   `bg_rules` carries the pre-1123 digest
   (`87b69704…`). The fixture cannot apply migration 1123 verbatim — its guards
   demand the production contract digest — so it is applied through the established
   test pattern (`tests/unit/migrations/l0_rules_link_accountability.test.ts:221-270`):
   compute the fixture's state-A digest with the migration's own digest SQL; verify it
   equals the migration's `old_digest` guard — if it does not, the fixture's
   `sutravali_rules` construction is wrong and the build fails before any reading
   runs; then simulate state B in a rolled-back transaction, verify the fixture
   produces the migration's `new_digest` (`f1d56d0c…`); patch the asset_registry
   contract constants; apply 1123; then re-verify the structural gate (`unlinked_reason`
   present, sunapha's link set exactly `{a5d58ce9…, cf36fd63…}`, 7 linked of 3,002,
   2,966 bulk-labelled, 29 `not_a_yoga_qualifier`, the remedy-corpus drift counts
   BPHS×193 / Phaladeepika×11 / Tajaka×3 / bphs_jaimini×1 / 1 Muhurta-Chintamani
   classical_tradition row). The same patch-apply covers 1120–1122 and 1124 if the
   fixture needs their effects; 1124 remains HELD on the 76-vs-75 reconciliation and
   is NOT in the fixture's migration set unless that gate lifts.
5. **Fixture chart facts.** A non-canonical fixture `chart_id` (never
   `CANONICAL_CHART_ID` — avoids ga_yoga_writer's FORENSIC guard at :2786) with
   `chart_facts` graha-position rows arranged so sunapha fires under
   `surya_siddhanta_classical` (Moon in the 4th, a non-Sun planet in the 2nd from the
   Moon, no planet in the 12th, lagna set), plus the synthesized `yoga_label` row.
   Arrangement is derived from `formation_rule_jsonb.requires[0].relation =
   planet_not_sun_in_2nd_from_moon` (l0_yogas.py:145-153) — the fixture chart is built
   to satisfy the rule, not copied from production chart data.

Local PG for rehearsal: Homebrew PostgreSQL 17.10, `localhost:55433`, superuser `Dev`,
extensions `vector`/`pgcrypto`/`uuid-ossp` present; throwaway database `madhav_l0w7`,
dropped when the lane closes.

## Guarded-contract discovery — disclosed (v1.3, 2026-09-26)

Machinery mapping for the fixture surfaced a fact class v1.2 did not know: the reads and
writes this harness exercises sit behind the data-plane contract machinery (migrations
1035/1036), and that machinery has never run in production. Everything below was verified
by structural probe on 2026-09-26 (pg_trigger / pg_proc / information_schema), never from
`_migrations_applied`. Methodological note for future probes: `information_schema.triggers`
is privilege-filtered — a SELECT-only role sees only `asset_registry`'s trigger; structural
trigger probes must use `pg_trigger`.

**Guards are LIVE.** `l1_data_plane_mutation_guard` + `l1_data_plane_capture` on
`chart_facts`, `chart_vichara`, `ga_yoga_firings` (and 9 more L1 tables);
`l1_data_plane_mutation_guard` on `chart_dashas`; `l2_data_plane_mutation_guard` +
`l2_data_plane_capture` on `bodha_msr_signals`; `nirmana_registry_receipt_invalidation` on
`asset_registry` — all `tgenabled='O'`. `brahma_yoga_catalog` and `sutravali_rules` are
trigger-free: the perturbation DELETE itself needs no machinery. The L1 guard admits
chart_facts writes only for 11 assets with a matching `fact_category_ownership` row, inside
a fully admitted generation (GUCs + `l1_data_plane_partition_contexts` + generation
`status='building'` + `build_runs.state='running'` + `build_run_assets.state='building'`),
as `session_user='data_plane_builder'`; every other mutation raises.

**Production has never admitted a generation.** `l1_data_plane_generations` = 0,
`l2_data_plane_run_intents` = 0, `data_plane_l2_producer_generations` = 0 — against
chart_facts = 421,096 rows, ga_yoga_firings = 202, bodha_msr_signals = 150,724, all
predating the machinery. Consequence, disclosed prominently: **the fixture is the first
environment where the decorated contract path executes end-to-end.** The harness may
therefore surface defects in the contract path itself (open/complete/grants/guard
allowlists), not only consumer movement. Those are findings for the owning layer's plan
(L1/L2 data plane), recorded and handed up — never repaired in this lane, under the same
rule as consumer findings.

**F-W-L0-7-1 — L2 open-before-bind order (finding, handed up unfixed).** Production
`open_l2_data_plane_generation(uuid,text,text,text,integer,text,text,text,text,jsonb,jsonb,text)`
requires `pg_temp.l2_data_plane_bind_receipt` to pre-exist (live function definition probed;
it raises `requires an exact-input bind receipt`), but the bo_laksana decorator calls open
BEFORE bind. The integration test
`platform/tests/integration/data_plane_protected_roles.db.test.ts:278-287` proves the
canonical order is bind-then-open. **Decision:** the harness primes ONE
`bind_l2_exact_inputs(chart_id, vector)` call per R3 run before invoking the writer —
behaviour-neutral (the decorator's own bind drops and recreates identical temp shadows from
the same vector), disclosed here, and flagged to the L2 plan as a decorator/migration
ordering defect candidate. Not fixed here.

**F-W-L0-7-2 — fact_category_ownership gap (finding, handed up unfixed).** The live guard
requires an `fact_category_ownership(fact_category, owning_asset_id)` row for every
chart_facts INSERT. The ownership table holds 69 rows and covers NONE of the position/yoga
categories production actually carries: `graha_position` (1,290 rows), `yoga_label` (125),
`saham_position` (8,400), `karaka_chara_position` (1,575), `special_lagna` (735),
`upagraha_position` (630), `aprakasha_position` (525), `swamsa_position` (360),
`karakamsa_position` (45), `esoteric_point_sri_yantra_position` (45), `upapada_lagna` (40),
`panchanga_yoga` (12), `panchanga_special_yoga_combinations` (15) — all present in
chart_facts, all unowned. Consequence: the guarded path as deployed cannot admit the writes
that produced production's own chart_facts contents for these categories — consistent with
zero admitted generations ever. Handed to the L1/data-plane plan, unfixed. The fixture does
NOT route around it by adding ownership rows — that would change the system under test.

**Seeding design — final, shaped by both findings.**

- *Unprotected tables seeded directly* (no guards): the v1.2 reference/catalog/registry
  set plus `asset_registry` (with production's integrity-contract rows, so the L0 pins
  `open_l1_data_plane_generation` checks — release `l0.semantic.2026-09-13.1` and the
  contract digests — resolve exactly as in production). The 1123 patch-apply oracle
  (v1.2 item 4) is unchanged.
- *`charts` seeded directly* (trigger-free; `open_l1_data_plane_generation` reads the row —
  birth_date/time/lat/lng/timezone_id/house_system NOT NULL — to build
  `base_context_jsonb`).
- *`chart_facts` seeded directly BEFORE 1035/1036 install their triggers* (the guards never
  see the seed inserts — admitted-context seeding is impossible under F-W-L0-7-2), followed
  by direct `l1_data_plane_row_snapshots` rows for those facts (corrected v1.4 — the L2
  bind shadows from row_snapshots, not fact_snapshots), attached to the synthesized
  generations below and carrying the capture-equivalent derived fields
  (`l1_data_plane_capture_row`'s formulas: context_id, calculation_context_jsonb,
  grain_jsonb, source_dependencies_jsonb, epistemic_class, missingness_state,
  verification_class, unit, semantic_payload_jsonb, source_row_jsonb, semantic_digest;
  1035:722-940), with `l1_data_plane_fact_snapshots` dual-written for fidelity exactly as
  the real capture dual-writes (1035:923-952). Disclosed as **synthesized capture
  artifacts**,
  standing in for the capture the blocked admitted path cannot perform; without them the
  L2 bind's pg_temp `chart_facts` shadow would be empty and R3's pre-registered mechanism
  (v1.2: shadowed citations survive the perturbation) could not run.
- *11 synthesized completed L1 generations* — the bo_laksana upstream closure
  (`asset_registry.depends_on`, probed: ga_condition, ga_dashas, ga_nakshatra, ga_panchanga,
  ga_positions, ga_sade_sati, ga_sensitive, ga_strength, ga_structural, ga_vargas,
  ga_vichara — 12 with ga_yoga) minus ga_yoga — each `status='complete'` with a mutually
  consistent `base_context_jsonb` and a synthetic, disclosed 64-hex
  `semantic_output_digest`, plus `l1_data_plane_generation_heads` rows.
- *The 12th generation, ga_yoga, is NOT synthesized.* R1's baseline run produces it through
  the real decorated path (`GaYogaWriter`, ga_yoga.py:33-65, `@register("ga_yoga")` +
  `@l1_producer_contract`, real psycopg, `dry_run=False`, as `data_plane_builder`), which
  also yields honest capture snapshots of `ga_yoga_firings`. **Ordering constraint: R1
  baseline runs before R3 baseline**, so the ga_yoga head exists when the L2 bind resolves
  the upstream vector.
- *`build_runs` + `build_run_assets` seeded per run* (integration-test precedent; DDL
  extracted from `supabase/migrations/171_build_runs.sql`).
- *Fixture schema additions beyond v1.2's 16 tables:* `charts`, `fact_category_ownership`
  (seeded with production's 69 rows verbatim — the gap preserved, not repaired), and the 9
  empty probe-derived L1 tables 1035's static triggers require (`chart_dashas`,
  `chart_divisionals`, `ga_condition_composite`, `ga_transit_anchors`,
  `l1_tajik_varsha_year_lords`, `ga_medical`, `ga_vastu_planet_direction_map`,
  `ga_prashna_lagna`, `ga_prashna_judgment`). Roles created before applying 1035/1036:
  `data_plane_builder`, `data_plane_verifier`, `data_plane_migrator`,
  `data_plane_l1_owner`, `data_plane_l2_owner`, `amjis_app`. Migrations 1035 + 1036 + 596
  applied verbatim — 1036's capture installer skips missing tables, 1035 does not, hence
  the 9 tables.
- *R1/R3 are invoked through the decorated adapters, unchanged* (`BoLaksanaWriter`,
  bo_laksana.py:3355-3357, `@l2_producer("bo_laksana")`). No consumer code is modified;
  no guard, trigger, or contract function is altered in the fixture.

## Certification-template position (v1.1 §4, read 2026-09-26)

This packet certifies under the 8-gate template. Anticipated conditional disposals, to be
recorded with reasons at certification: **Narr** N/A (the harness emits no prose); **Dens**
judged at certification time. **Dom: HELD** per the flag above — no `Dom` coverage is
claimed by this packet until the strategy ruling resolves `Dom` vs Decision 11.

## What this report does NOT contain

- No gate mapping, no `Dom`-coverage claim, no certification verdict (HELD, strategy
  ruling pending).
- No consumer repairs — consumer findings belong to L1–L5's plans.
- No repair of F-W-L0-7-1 (L2 open-before-bind) or F-W-L0-7-2 (ownership-registry gap) —
  both handed to the L1/L2 data-plane plan; the fixture preserves the ownership gap
  verbatim rather than routing around it.
- No live perturbation run yet: the predictions above are pre-registered from code and
  read-only production probes; the measured before/after lands with the harness run.

## Packet status

**Baseline measurement: COMPLETE** (reading set frozen, perturbation identified, movement
pre-registered against state B, state pin declared, re-measure gate set).
**Machinery mapping: COMPLETE** (v1.3 — guards probed live, zero-generation disclosure,
seeding design final, F-W-L0-7-1 / F-W-L0-7-2 handed up).
**Fixture builder: COMPLETE** (v1.5 — 33/33 gates twice; 1123 oracle green both
directions; 11 closure generations synthesized; F-W-L0-7-3 / F-W-L0-7-4 handed up;
rehearsal DB madhav_l0w7_fixture live on localhost:55433).
**Construction: AUTHORIZED** (2026-09-26) — readings runner next, then CI vehicle.
**Gate mapping: HELD** (strategy ruling: `Dom` vs Decision 11).

Open rulings, restated as OPEN — none inferred here:

- **W-L0-9 identity ruling:** [OPEN — not ruled]
- **W-L0-6 Sarvatobhadra school ruling:** [OPEN — not ruled]
- **`Dom` vs Decision 11:** [OPEN — strategy, ruling to follow]

Migration posture unchanged: 1120–1124 committed and HELD; 1123 must precede 1124; 1124
gated on the `bg_transit_rules` 76-vs-75 reconciliation. Merge gate on the sangam-stage3
carriage stands.
