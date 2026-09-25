---
artifact: L0_W_L0_7_PACKET_REPORT
version: 1.2
status: BASELINE_COMPLETE_GATE_MAPPING_HELD
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

## Certification-template position (v1.1 §4, read 2026-09-26)

This packet certifies under the 8-gate template. Anticipated conditional disposals, to be
recorded with reasons at certification: **Narr** N/A (the harness emits no prose); **Dens**
judged at certification time. **Dom: HELD** per the flag above — no `Dom` coverage is
claimed by this packet until the strategy ruling resolves `Dom` vs Decision 11.

## What this report does NOT contain

- No gate mapping, no `Dom`-coverage claim, no certification verdict (HELD, strategy
  ruling pending).
- No consumer repairs — consumer findings belong to L1–L5's plans.
- No live perturbation run yet: the predictions above are pre-registered from code and
  read-only production probes; the measured before/after lands with the harness run.

## Packet status

**Baseline measurement: COMPLETE** (reading set frozen, perturbation identified, movement
pre-registered against state B, state pin declared, re-measure gate set).
**Construction: AUTHORIZED** (2026-09-26) — harness, fixture, CI vehicle.
**Gate mapping: HELD** (strategy ruling: `Dom` vs Decision 11).

Open rulings, restated as OPEN — none inferred here:

- **W-L0-9 identity ruling:** [OPEN — not ruled]
- **W-L0-6 Sarvatobhadra school ruling:** [OPEN — not ruled]
- **`Dom` vs Decision 11:** [OPEN — strategy, ruling to follow]

Migration posture unchanged: 1120–1124 committed and HELD; 1123 must precede 1124; 1124
gated on the `bg_transit_rules` 76-vs-75 reconciliation. Merge gate on the sangam-stage3
carriage stands.
