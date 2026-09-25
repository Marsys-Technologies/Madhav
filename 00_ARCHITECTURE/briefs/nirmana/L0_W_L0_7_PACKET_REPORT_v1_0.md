---
artifact: L0_W_L0_7_PACKET_REPORT
version: 1.1
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
  `fact_subject = 'sunapha'` (categories `yoga_label` / `yoga_fires`) lose the
  classical-source bridge — `classical_sources_jsonb` NULL where it previously carried
  citations plus the **post-1123** rule_ids `{a5d58ce9…, cf36fd63…}` — and those 2 rules
  lose their parent join. Named non-movement control: `_corroboration_count_by_text`
  does NOT move — it reads the fact's own `fvj.classical_citations`, never the catalog
  (bo_laksana.py:1646-1673).

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
