# L0-W7 Data-Plane Fixture — Rehearsal Notes v1.0

**Date**: 2026-09-26
**Branch**: `l0/infra-w7-data-plane-campaign-rehearsal`
**Builder**: `scripts/l0harness/build_fixture.py` (steps a–l per `L0_W7_DATA_PLANE_CAMPAIGN_BRIEF_v1_0.md`)
**Result**: `BUILD GREEN` — 14/14 gates, two consecutive end-to-end runs (fresh DB each run).

Rehearsal cluster: `/tmp/l0w5/pgdata`, port 55433, trust auth, superuser `Dev`.
Fixture database: `madhav_l0w7_fixture`. Production source: `amjis` via
cloud-sql-proxy `127.0.0.1:5433` (read-only probes only).

---

## 1. What the fixture contains

- **27 probe-derived tables** (`fixture_schema.py` from `production_schema/` probes):
  full DDL — columns, defaults, PKs, unique constraints, CHECKs, indexes, and 6 FKs
  (`charts_client_id_fkey` deliberately skipped; `clients` is not in the fixture set).
- **512 bounded reference rows** (`production_seed/`, 7 JSONL + `seed_manifest.json`):
  asset_registry 129, brahma_yoga_catalog 233, brahma_dosha_catalog 79,
  sutravali_rules 2 (`yoga_canonical_id='sunapha'`), classical_texts 1 (`bphs`),
  classical_text_chunks 1 (`bphs_pg0030_c01`, chapter=30, with embedding +
  content_sha256), fact_category_ownership 67.
- **8 roles** mirroring production pg_roles flags (LOGIN/NOINHERIT exactly; none
  super/createrole/createdb/bypassrls — 1035/1036 preflights check this).
- **207 grantor-faithful grants** replayed from `grants.json`
  (39 amjis_app, 12 l2_owner, 156 l1_owner).
- **Migrations applied verbatim**: 171-extract → 596 → 1035 → 1036, 1035/1036 as
  `data_plane_migrator` with `SET ROLE data_plane_l1_owner` / `data_plane_l2_owner`.
- **2 complete generations** (ga_positions, ga_structural) with capture-faithful
  row snapshots (3), fact snapshots (3), partitions (2), heads (2); digest,
  `completed_partitions == receipt count`, `completed_at` set.

## 2. Deviations from the brief (each forced by a rehearsal failure)

1. **Step-(j) data seeds folded into pre-migration step (d).** The brief's
   post-migration seed would require a fake `data_plane_builder` session to pass
   the mutation guard. Instead the 12 data rows (charts 1, chart_facts 7,
   ga_yoga_firings 1, chart_vichara 2, bodha_msr_signals 1) are inserted before
   the guard triggers exist — same final state, no counterfeit builder session.
2. **Grant replay (f/g) runs before migrations (e).** Every `grants.json` table is
   a pre-migration fixture table, and production's grants predated 1035/1036 —
   1036's preflights read `asset_registry` and `asset_output_digest_specs` as
   `data_plane_l2_owner`, which only holds SELECT via those grants. Replaying
   after migrations makes 1036 fail with `permission denied`.
3. **`asset_output_digest_specs` support table** (28th table, not in the fixture
   set). 1036:396-405's bo_samvada preflight reads it unconditionally. DDL and
   grants (SELECT to builder + l2_owner, grantor amjis_app) probed from
   production. Production also grants `retrieval_census_ro` and
   `nirmana_evidence_ingress_writer` — roles outside the fixture set, omitted.
   Table is empty, matching production's retired-spec state for bo_samvada.
4. **28 L2 producer stub tables.** 1036's closing GRANT (1036:2049-2062) names
   all 29 L2 producer tables unconditionally, so verbatim application requires
   their existence; the trigger installer itself tolerates missing tables
   (1036:1729). Stubs are identity-column-only (`<name>(<identity_col> text
   PRIMARY KEY)`), owned by `data_plane_l2_owner` (production owner, probed).
   Only `bodha_msr_signals` is a full fixture table.
5. **Schema/sequence bootstrap grants.** A fresh DB's `public` schema is owned
   by the superuser; production's schema-level grants were reproduced:
   `ALTER SCHEMA public OWNER TO amjis_app`, CREATE to both owner roles, USAGE
   to the data-plane roles. `chart_vichara_id_seq` and `ga_yoga_firings_id_seq`
   owned by `data_plane_l1_owner` so 1035's dynamic `GRANT ... ON SEQUENCE`
   (run as l1_owner) can execute; `yoga_families_id_seq` owned by amjis_app.
6. **171 applied as programmatic verbatim extract** of just `build_runs` +
   `build_run_assets` from migration 171 (the asset_throughput ALTERs target a
   table outside the fixture set). No 1120-1123 migrations exist; the old plan
   note referencing them was wrong.
7. **Role creation is idempotent** (`DROP ROLE IF EXISTS` first): roles are
   cluster-level and survive the fixture DB drop between runs.
8. **`useEvidenceExplorer.ts` / `catalogService.ts`** named in the brief were not
   found in this repo — treated as absent, no consumer-shape extraction needed.

## 3. Production probe surprises (affect future exports/captures)

- **Production has 0 generations, 0 snapshots, 0 heads** — the data plane has
  never been run. All generation/snapshot rows in the fixture are synthesized.
- **175,949 of 421,096 production `chart_facts` rows are multi-valued** (more
  than one typed value column set). They would fail the capture-time CHECK
  (exactly one typed value). The fixture's dignity seed row
  (`f100000000000004`) is deliberately multi-valued and therefore excluded from
  fact snapshots — snapshot map covers f…001 (ga_positions), f…002, f…003
  (ga_structural).
- **`classical_text_chunks.chapter` is a page number, not a chapter** (max 1034
  for bphs). The sunapha-relevant chunk is `bphs_pg0030_c01` (chapter=30).
- **Sunapha catalog citations carry no chunk_id** — citation linkage is by text
  only; `bphs_pg0001_c01` appearing in citation refs is a chunk-id *format
  string*, not a `text_id`.
- **`yoga_families` / `yoga_family_members` are empty in production** — not
  exported; tables exist in the fixture for DDL/FK completeness only.
- **`yoga_label` and `graha_shadbala_total` fact categories are unowned** in
  `fact_category_ownership` — seed rows in those categories are only possible
  pre-trigger (guard checks ownership for chart_facts writes).
- **`chart_facts.chart_id` joins `charts.id`** (integer identity), not a UUID —
  the fixture chart uses `f0000000-…-000000000001` as the charts row's UUID
  column and joins by the integer id.
- **ga_positions owns 0 fact categories**; production ownership is 64
  ga_structural, 2 ga_condition, 1 ga_ayurdaya (67 total exported).

## 4. Gate evidence (final run)

```
PASS mutation guard on 12 guarded L1 tables                 (12/12)
PASS capture trigger on 11 L1 tables (chart_dashas none)    (11/11)
PASS L2 guard+capture on bodha_msr_signals                  (2/2)
PASS L1 admin immutability triggers                         (7/7)
PASS L1 data-plane admin tables                             (13/13)
PASS L2 data-plane admin tables                             (15/15)
PASS support/receipt/build tables                           (5/5)
PASS roles                                                  (8/8)
PASS fixture FK count (charts_client_id_fkey skipped)       (6/6)
PASS complete generations + heads                           (2/2)
PASS row snapshots / fact snapshots                         (3/3)
PASS reference data rows                                    (512/512)
PASS seeded data rows                                       (1/7/1/2/1)
PASS mutation guard rejects non-builder chart_facts write
all 14 gates green → BUILD GREEN
```

Negative gate verified manually: `INSERT INTO chart_facts …` as superuser
returns `ERROR: protected L1 INSERT requires direct data_plane_builder
authentication` (`l1_data_plane_guard_active_mutation()` line 15).

## 5. Rehearsal failures encountered and fixed

| # | Failure | Fix |
|---|---------|-----|
| 1 | `permission denied for schema public` (1035 CREATE TABLE as l1_owner) | schema owner + CREATE/USAGE bootstrap (deviation 5) |
| 2 | `role "amjis_app" already exists` on rerun | `DROP ROLE IF EXISTS` (deviation 7) |
| 3 | `permission denied for table asset_registry` (1036 preflight as l2_owner) | grant replay moved before migrations (deviation 2) |
| 4 | `permission denied for table asset_output_digest_specs` (1036 preflight) | support-table grants probed + replayed (deviation 3) |
| 5 | `relation "public.bodha_cgm_nodes" does not exist` (1036 closing GRANT) | 28 L2 stub tables (deviation 4) |
| 6 | negative gate FAIL — syntax error in gate's own INSERT (unquoted UUID literal), guard never reached | quoted the literal; gate now exercises the guard |
