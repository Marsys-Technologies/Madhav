---
artifact: L0_W_L0_7_PACKET_REPORT
version: 1.0
status: BASELINE_COMPLETE_GATE_MAPPING_HELD
packet: W-L0-7 (consumer-perturbation harness)
session: NIRMANA_L0_BRAHMAGYAN_EXECUTION_20260921
branch: l0/brahmagyan-exec
date: 2026-09-26
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

Per that instruction: the **baseline measurement** (reading set, perturbation, predicted
movement) is ruling-independent and is delivered here. The harness's **gate mapping** and
any **`Dom`-coverage claim are HELD** until the ruling lands. Template v1.1 §4 was read
before this design, as instructed.

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
| L3 | — | **none — verified empty leg** | register records no `ka_*` read of `brahma_yoga_catalog`; grep of `L3_kala/` serve surfaces and of all `ga_yoga_firings` TS readers confirms no L3 consumer. An honest empty leg, not a gap — L0 is a reference layer and lack of a reader is not redundancy | — |

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

Why this row — four grounded criteria (read-only production probes, 2026-09-26):

1. **Catalog-loop evaluated.** `sunapha` appears nowhere in `ga_yoga_writer.py` as code —
   its firing path is the plain `formation_rule_jsonb` catalog loop, the simplest
   predictable mechanism. `DETECTOR_INSERT_IDS` (ga_yoga_writer.py:2411) is exactly
   {`dhana_yoga_house_lords`, `raja_yoga_kendra_trikona`, `sarasvati_yoga`,
   `lakshmi_yoga`, `vipareeta_raja_yoga`} — sunapha is not a detector id.
2. **Carries classical citations** (`has_citations = true`) — R2's join has something to
   lose. School: parashari; category: other; `formation_rule_jsonb` present.
3. **Referenced by `sutravali_rules.yoga_canonical_id`** on exactly 2 rules —
   `7ede2ed9-ceec-5fe5-910f-242b2face906`, `a5d58ce9-5331-5db4-a803-41d9530e45fc` — so
   R3's rule-join leg has something to lose. (Column census while probing: 17 non-null
   rows over 8 distinct yoga ids — consistent with W-L0-3's measured 17-of-3,002.)
4. **Fires on the native chart** `482012f1-710e-4a25-994a-93821f5871aa` under exactly one
   ayanamsha — `surya_siddhanta_classical`, one row,
   `strength_label = computed_extension` — giving R1 a narrow, exact prediction on the
   established fixture chart (the WP-1.3(f) integration tests use the same chart).

## Predicted movement — pre-registered; the harness PASS is exactly these movements

- **R1 (L1 writer):** after a `ga_yoga_writer` rerun on the perturbed snapshot,
  `ga_yoga_firings` loses exactly the `(482012f1…, surya_siddhanta_classical, sunapha)`
  row and nothing else; every other firing row is byte-identical (the writer is
  deterministic; the catalog loop simply never evaluates sunapha). A firing that survives
  the withdrawal has not consumed the catalog — or consumed a cache; either is a finding.
- **R2 (L1 serve):** `get_yoga_firings` for the native chart still returns the sunapha
  firing row (the firing is L1's own data), but its `catalog_classical_citations` moves
  from the seeded citations to **NULL** (LEFT JOIN miss). Movement is in the citation
  field exactly; row presence must NOT move — a named non-movement control.
- **R3 (L2 writer):** a `bo_laksana` rebuild on the perturbed snapshot: L1 facts with
  `fact_subject = 'sunapha'` (categories `yoga_label` / `yoga_fires`) lose the
  classical-source bridge — `classical_sources_jsonb` NULL where it previously carried
  citations plus the 2 rule_ids — and the 2 sutravali rules lose their parent join.
  Named non-movement control: `_corroboration_count_by_text` does NOT move — it reads the
  fact's own `fvj.classical_citations`, never the catalog (bo_laksana.py:1646-1673).
- **C0 (control):** `query_yoga_catalog` no longer returns `sunapha` — confirms the
  perturbation landed before any consumer is judged.
- **L3:** no reading exists to move; verified empty.

A consumer that does not move has not consumed → finding for L1–L5's plans, recorded, not
repaired here.

## CI vehicle — named, not built

The established disposable-snapshot pattern: `pgvector/pgvector:pg15` service → extensions
+ supabase-convention roles → schema restore → `npx tsx scripts/migrate.ts` → live scans
(`.github/workflows/fresh_chart_smoke.yml:72-81, 191-221`). The harness reuses this
vehicle: same service, plus a fixture slice (native-chart `chart_facts`, the
`brahma_yoga_catalog` / `brahma_dosha_catalog` / `sutravali_rules` reference rows, and the
baseline `ga_yoga_firings` rows), then baseline readings → perturb → re-read → diff
against the pre-registered predictions above. Harness construction is the next step; its
gate mapping remains HELD.

## Certification-template position (v1.1 §4, read 2026-09-26)

This packet certifies under the 8-gate template. Anticipated conditional disposals, to be
recorded with reasons at certification: **Narr** N/A (the harness emits no prose); **Dens**
judged at certification time. **Dom: HELD** per the flag above — no `Dom` coverage is
claimed by this packet until the strategy ruling resolves `Dom` vs Decision 11.

## What this report does NOT contain

- No gate mapping, no `Dom`-coverage claim (HELD, strategy ruling pending).
- No harness code and no CI wiring (next step).
- No consumer repairs — consumer findings belong to L1–L5's plans.
- No live perturbation run yet: the predictions above are pre-registered from code and
  read-only production probes; the measured before/after lands with the harness run.

## Packet status

**Baseline measurement: COMPLETE** (reading set frozen, perturbation identified, movement
pre-registered). **Gate mapping: HELD** (strategy ruling: `Dom` vs Decision 11).

Open rulings, restated as OPEN — none inferred here:

- **W-L0-9 identity ruling:** [OPEN — not ruled]
- **W-L0-6 Sarvatobhadra school ruling:** [OPEN — not ruled]
- **`Dom` vs Decision 11:** [OPEN — strategy, ruling to follow]

Migration posture unchanged: 1120–1124 committed and HELD; 1124 gated on the
`bg_transit_rules` 76-vs-75 reconciliation. Merge gate on the sangam-stage3 carriage
stands. W-L0-3's packet report remains owed and is next in this lane after this baseline.
