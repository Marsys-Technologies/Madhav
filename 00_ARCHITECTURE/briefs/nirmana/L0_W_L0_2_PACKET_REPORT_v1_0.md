---
artifact: L0_W_L0_2_PACKET_REPORT
version: 1.0
status: CURRENT
packet: W-L0-2 (Declared dependencies and declared use)
session: l0/nirmana-elevation-20260921 execution session (worktree /Users/Dev/madhav-l3/l0-exec)
date: 2026-09-25
plan: MADHAV_DATA_PLANE_L0_BRAHMAGYAN_STRATEGY_v2_1.md
---

# W-L0-2 Packet Report — Declared dependencies and declared use

Per-packet report per the execution kickoff. Convention: change → detector before →
detector after → blocks. All production figures measured live on 2026-09-25 via
read-only queries; this session writes nothing to production.

## Item 1 — Every writer-side code read of a bg_* table is now a registered depends_on edge

**Change (code, uncommitted in worktree):**
- `platform/scripts/seed/asset_registry_seed.ts` — 16 consumer assets gained bg_*
  (and reconciliation) edges, each marked `// W-L0-2 (2026-09-25)`:

  | Consumer | Edges added |
  |---|---|
  | bo_laksana | bg_texts, bg_yogas, bg_doshas, bg_class_priors |
  | bo_pratijna | bg_reference |
  | bo_grounding | bg_rules |
  | bo_upaya | bg_remedies |
  | ga_sensitive_degree | bg_nakshatra |
  | ga_yoga | bg_yogas |
  | ga_structural | bg_yogas, bg_doshas |
  | ga_condition | bg_dignity_reference |
  | ga_medical | bg_medical_mappings, bg_nakshatra_medical |
  | ka_gochara | bg_gochara_arcs (live+seed UNION reconciliation — the other 7 edges were already migration-governed live) |
  | ka_gochara_resonance | bg_ghatana |
  | ka_gochara_v3_century_materialize | bg_ghatana, bg_vedha_malefic_scale, bg_transit_rules |
  | ka_kshetra | ka_vedha_gochara (UNION reconciliation), bg_ghatana, bg_ephemeris, bg_kp_sublord_division, bg_transit_rules |
  | ph_nimitta | bg_ghatana |
  | ph_rectification | bg_formula_constants |
  | mi_darshana | bg_ghatana |

  All intra-L0 writer reads were already declared (verified against the census).

**Census method:** an 11-agent read-only swarm walked every writer/payload file
mapped to its producer asset; output distilled into
`platform/python-sidecar/brahmagyan/l0_declared_use_register_v1.json`
(use_type vocabulary of 8; writer_side_reads with evidence files and
pre_existing/declared_this_packet marking; excluded_reads; serve_time_reads with
access class; tables_without_readers; writer_only_tables; mention_only;
producer_files; write_only_access).

**Detector before:** 21 of 40 L0 assets had no cross-layer consumer declared while
all 40 are read by code (strategy §1.1/§4.2 figure).
**Detector after:** standing detector
`platform/scripts/__tests__/l0_declared_dependencies.test.ts` (8/8 green):
(a) every register writer_side_read's producer asset is in the consumer's seed
depends_on; (b) use_types ⊆ vocabulary, all named files exist, access class valid;
(c) staleness grep — walks platform/python-sidecar, platform/src, platform-mcp/src
(skipping tests/generated/scripts/migrations) for `FROM|JOIN|INTO|UPDATE <table>`
per register table and refuses any (file, table) hit the register does not cover.
Initial fallout of 14 hits was adjudicated: 2 real reads → excluded_reads with
recorded reasons (l0_sutravali_extractor unregistered tooling; l0_reference.py
dead-block legacy plural read), 1 multi-producer case fixed by coverage
(l0_class_lifetime_counts.py co-producer of brahma_class_priors), 11
comment/docstring mentions → mention_only.

**Exclusions (no edge, by design — recorded in the register):**
ga_sensitive/ga_dashas → legacy `reference_nakshatras` (plural, retired;
L1 repoint handover from W-L0-1); ka_gochara_sweep → beo (consumer RETIRED);
mi_jivanaghatana → beo (deliberately inert lookup); l0_sutravali_extractor /
l0_remedy_yaml_scaffolder / l0_text_index.py / brahma_pipeline.py (unregistered
tooling/diagnostic).

## Item 2 — Pin-test fallout from the deliberate seed changes repaired (fix the artifact class)

Two pre-existing pin tests documented the pre-W-L0-2 governed state and failed on
the deliberate changes; both were updated to the new governed state (same
convention as migration 1030's pin updates — no gate weakened):

- `platform/scripts/__tests__/asset_registry_seed_dag_parity.test.ts` —
  MIGRATION_GOVERNED_DEPENDENCIES entries for bo_laksana, bo_pratijna,
  bo_grounding, ph_nimitta updated in place (28-row denominator unchanged);
  ga_structural canonical-order pin and the shared-MSR grounding expectation
  extended with the new edges; header comment records the 1122 rewrite.
- `platform/tests/unit/migrations/nirmana_l0_prashna_integrity_contract.test.ts` —
  bg_prashna_rules pin updated from `target_table: null` to the honest five-table
  comma-set (W-L0-1 fallout, migration 1120; W-L0-1 had run only targeted tests).

**Detector after:** full suite `cd platform && npx vitest run` —
1144 passed files / 12433 passed tests, 0 failures (78 files / 707 tests skipped
as usual).

## Item 3 — Migration 1122 authored, HELD

- `platform/migrations/1122_l0_declared_dependencies.sql` — guarded DO-block
  (1075/1120/1121 pattern): refuses if any of the 16 assets is absent, if any
  canonical edge names an unregistered asset_id (no phantom declarations), or if
  any live row carries an edge outside its canonical array (a post-census
  addition by another session must not be silently dropped). Converges each row
  to the canonical live+seed-union array; postflight verifies exact equality.
  VERIFY falsifier + manual DOWN (per-asset pre-W-L0-2 arrays, with the
  live-verified ka_gochara/ka_kshetra pre-sets) included.
- **HELD** per the kickoff blocker: `_migrations_applied` is unreconciled for
  1080–1095; application belongs to the consolidation session (madhav-65) after
  ledger reconciliation. Number 1122 chosen by scanning every origin/* head
  across BOTH platform/migrations/ (head 1091) and
  platform/supabase/migrations/ (head 1090): no 1092–1199 exists on any ref;
  1120 and 1121 are this session's W-L0-1 and W-L0-9 migrations.

## Item 4 — Serve-time reads documented with declared use types

Every serve-time read of a bg_* table is recorded in the register's
serve_time_reads section with file, table, access class
(direct/indirect/transport), use_types from the 8-type vocabulary, and purpose.
Producer-internal reads, tables_without_readers (classical_attributions,
vidhi_*), and writer_only_tables (bg_gochara_arcs, bg_synthetic_cohort) are
recorded as such — L0 is a reference layer; absence of a reader is not
redundancy and retires nothing.

## Packet status

W-L0-2 closed on the code/detector side: edges registered for all 16 consumers,
zero undeclared writer-side reads under the standing staleness grep, register
JSON emitted, detector added, full suite green. The live-registry effect is held
in migration 1122 for the consolidation session (ledger reconciliation). No gate
was weakened; no production write was made from this session.
