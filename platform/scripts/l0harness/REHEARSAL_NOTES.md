# L0-W7 Data-Plane Fixture — Rehearsal Notes v1.2

**Date**: 2026-09-26
**Branch**: `l0/brahmagyan-exec`
**Design law**: `00_ARCHITECTURE/briefs/nirmana/L0_W_L0_7_PACKET_REPORT_v1_0.md` v1.4
**Builder**: `scripts/l0harness/build_fixture.py`
**Result**: `BUILD GREEN` — 33/33 gates, two consecutive end-to-end runs (fresh DB each run).

v1.2 adds §8 (readings runner: first decorated-path execution of the frozen
9-step sequence; 2 PASS / 3 UNMEASURED verdicts; F-W-L0-7-5/-7/-8 confirmed
and new F-W-L0-7-9 measured) and corrects §6's stale "integer identity"
claim for chart_facts.chart_id.

v1.1 corrects v1.0: v1.0 cited a nonexistent brief
(`L0_W7_DATA_PLANE_CAMPAIGN_BRIEF_v1_0.md`) and branch
(`l0/infra-w7-data-plane-campaign-rehearsal`), and wrongly claimed "no
1120–1123 migrations exist". Migrations 1120–1124 exist at
`platform/migrations/1120..1124_*.sql` (W-L0-1/9/2/3 + the HELD 1124) and are
now exercised by the patch-apply oracle below.

Rehearsal cluster: `/tmp/l0w5/pgdata`, port 55433, trust auth, superuser `Dev`.
Fixture database: `madhav_l0w7_fixture`. Production source: `amjis` via
cloud-sql-proxy `127.0.0.1:5433` (read-only probes only).

---

## 1. What the fixture contains

- **27 probe-derived tables** (`fixture_schema.py` from `production_schema/` probes):
  full DDL — columns, defaults, PKs, unique constraints, CHECKs, indexes, and 6 FKs
  (`charts_client_id_fkey` deliberately skipped; `clients` is not in the fixture set).
- **Reference data** (`production_seed/`, 11 JSONL + `seed_manifest.json`):
  - *Full raw `to_jsonb(row)::text` exports* (imported via `\copy` + per-line
    `jsonb_populate_record`, no client-side value handling — byte-faithful
    numeric scale and jsonb serialization; migration 1123's digest gates depend
    on this): **sutravali_rules 3,002** (state A: 17 linked, no
    `unlinked_reason` column), **brahma_ontology 741**, **brahma_remedy_corpus
    341** (pre-1123 drift spellings present), **brahma_class_priors 177**,
    **brahma_dasha_systems 20**, **classical_texts 16**.
  - *Bounded Python-JSON exports* (not digest-gated): asset_registry 129,
    brahma_yoga_catalog 233, brahma_dosha_catalog 79, classical_text_chunks 1
    (`bphs_pg0030_c01`, chapter=30, with embedding + content_sha256),
    fact_category_ownership 67.
- **8 roles** mirroring production pg_roles flags (LOGIN/NOINHERIT exactly; none
  super/createrole/createdb/bypassrls — 1035/1036 preflights check this).
- **207 grantor-faithful grants** replayed from `grants.json`
  (39 amjis_app, 12 l2_owner, 156 l1_owner).
- **Migrations applied verbatim**: the W-L0-1/9/2/3 set **1120 (skipped,
  disclosed) → 1121 → 1122 → 1123** from `platform/migrations/` (1124 remains
  HELD and is never applied), then 171-extract → 596 → 1035 → 1036, 1035/1036
  as `data_plane_migrator` with `SET ROLE data_plane_l1_owner` /
  `data_plane_l2_owner`.
- **11 complete L1 generations** — the bo_laksana upstream closure minus
  ga_yoga, derived live from the post-1122 asset_registry — with
  capture-faithful row snapshots (3), fact snapshots (3), partition receipts
  (11), heads (11); digest, `completed_partitions == receipt count ==
  expected_partitions`, `completed_at` set on every generation.

## 2. 1120–1123 patch-apply oracle (packet report v1.2 item 4)

Build step (j), `step_l0_patch_oracle()`, runs after the reference-data seed
and before grants/596/1035/1036 (so 1123's asset_registry UPDATE never meets
596's `nirmana_registry_receipt_invalidation` trigger, and the closure walk
sees 1122's canonical depends_on). Gate outputs, final run:

1. **State-A digest gate — MATCH.** The freshly imported 3,002-row
   sutravali_rules digests (vector A, 13 columns) to
   `87b697041c73359e12daf8258cfdd6e85a38eb5c63fa39865e42f5b46e610dbd`, exactly
   1123's `old_digest` — and exactly production's own state-A digest (measured
   via MCP 2026-09-26). This is the export-fidelity proof.
2. **Rolled-back state-B simulation — MATCH.** Inside a transaction: ADD COLUMN
   `unlinked_reason`, replay the migration's own 36-row backfill (VALUES block
   extracted verbatim from the migration file by regex — one source of truth),
   bulk-label `no_concept_reference_in_window`, digest (vector B, 14 columns),
   ROLLBACK. Result
   `f1d56d0cebf7ce2ad270ba1145cda20cae4c10f2ec3fb1ea01bc6b999feee098` == 1123's
   `new_digest`.
3. **Registry contract check — PASS, no patch needed.** The exported bg_rules
   row already carries the 618 `integrity_check_sql` verbatim (the migration's
   `old_contract` text, compared newline-normalized) and `target_floor=3002` —
   consistent with the state-A digest equality. A mismatch would fail the
   build rather than be patched.
4. **Apply in order: 1120 → 1121 → 1122 → 1123 (NEVER 1124).**
   - **1120 SKIPPED (disclosed partial application).** All five declared member
     tables are absent from the 27-table fixture set:
     `bg_prashna_lagna_methods`, `bg_prashna_tajik_yogas`,
     `bg_prashna_significators`, `bg_prashna_fructification_rules`,
     `bg_prashna_special_techniques` (they exist in production). Exact failing
     statement had it been applied: migration 1120 refuses at 1120:55-60,
     `RAISE EXCEPTION 'migration 1120 refuses: declared member table % does
     not exist', member_table` with `member_table='bg_prashna_lagna_methods'`.
     Consequence: `bg_prashna_rules` keeps `target_table NULL` (production
     state A); nothing downstream (1122 closure walk, 1123, generation
     synthesis) reads it.
   - **1121 applied**: 7 `relation_type` ontology rows (741 → 748).
   - **1122 applied**: 16 depends_on arrays converged to canonical.
   - **1123 applied**: 36-row replay backfill + 2,966-row bulk label →
     7 linked of 3,002; `unlinked_reason` column + XOR/vocabulary CHECKs;
     remedy-corpus normalization (BPHS×193, Phaladeepika×11, Tajaka×3,
     bphs_jaimini×1, Muhurta-Chintamani×1 — every measured count asserted by
     the migration and met); 3 ontology alias entries; bg_rules registry
     contract replaced 618 → tightened (the migration's exact-match
     `IN (old_contract, rules_check)` accepted the exported row as-is).
5. **Post-apply verification — PASS.** sunapha link set exactly
   `{a5d58ce9-5331-5db4-a803-41d9530e45fc, cf36fd63-ba97-5ead-ad17-de9054fc051f}`;
   post-1123 digest == `new_digest` (also gated, §4).

**`not_a_yoga_qualifier` finding.** Packet report v1.2 item 4 names a
`not_a_yoga_qualifier` vocabulary value. It appears nowhere in migration 1123,
its unit test, or anywhere else in the repo — the migration's declared
vocabulary is exactly `no_concept_reference_in_window`, `ambiguous_reference`,
`reference_not_in_catalog`. The fixture gates on the migration's real
post-patch numbers (7 linked; 2,986/7/2); the report phrase is a report-side
artifact, recorded here rather than implemented.

## 3. Generation synthesis — bo_laksana upstream closure minus ga_yoga

Derived **live** from the patched asset_registry (recursive `depends_on` walk
from bo_laksana), per packet report v1.3:

- **Full walk: 25 assets** — bo_laksana; bg_class_priors, bg_dasha_systems,
  bg_dignity_reference, bg_doshas, bg_kp_sublord_division, bg_nakshatra,
  bg_ontology, bg_panchanga, bg_reference, bg_rules, bg_texts, bg_yogas;
  ga_condition, ga_dashas, ga_nakshatra, ga_panchanga, ga_positions,
  ga_sade_sati, ga_sensitive, ga_strength, ga_structural, ga_vargas,
  ga_vichara, ga_yoga.
- **ga\_\* closure: 12 assets** — diff vs the directive's expected-12 list:
  **none, either direction**. ga_yoga is reachable via `ga_vichara`'s
  pre-existing live `depends_on` edge.
- **Synthesized generations: 11** (closure minus ga_yoga): ga_condition,
  ga_dashas, ga_nakshatra, ga_panchanga, ga_positions, ga_sade_sati,
  ga_sensitive, ga_strength, ga_structural, ga_vargas, ga_vichara.
- Generations replicate `open_l1_data_plane_generation` (1035:643-685):
  contract/L0-release/L0-config pins, mutually consistent
  `base_context_jsonb`, `expected_partitions=1`, empty building state.
  Run UUIDs are deterministic: ga_positions `f0000000-…-000000000101`,
  ga_structural `…0102` (snapshot attachment depends on these), ga_yoga
  `…0103`, bo_laksana `…0104` (data seeds reference them), remaining closure
  assets `f0000000-0000-4000-8000-000000000111+` in sorted order.
- Snapshots attach only to ga_positions (1 row) and ga_structural (2 rows),
  as before; the other 9 generations complete with 0 snapshots — each gets its
  partition receipt (`rows_inserted=0`) and a **synthetic disclosed**
  `semantic_output_digest` =
  `encode(digest('l0w7-synthetic-empty-generation:' || asset_id, 'sha256'),'hex')`
  (64-hex, marked synthetic here; production has 0 generations, so no real
  digest exists to reproduce).

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
PASS complete generations + heads (closure minus ga_yoga)   (11/11)
PASS generation heads cover exactly the derived closure     (11-asset set, exact)
PASS row snapshots / fact snapshots                         (3/3)
PASS manifest rows: asset_registry                          (129)
PASS manifest rows: brahma_yoga_catalog                     (233)
PASS manifest rows: brahma_dosha_catalog                    (79)
PASS manifest rows: sutravali_rules                         (3002)
PASS manifest rows: classical_texts                         (16)
PASS manifest rows: classical_text_chunks                   (1)
PASS manifest rows: fact_category_ownership                 (67)
PASS manifest rows: brahma_ontology (+7 relation_type)      (748)
PASS manifest rows: brahma_remedy_corpus                    (341)
PASS manifest rows: brahma_class_priors                     (177)
PASS manifest rows: brahma_dasha_systems                    (20)
PASS sutravali post-1123 rows/linked                        (3002/7)
PASS sutravali post-1123 digest == 1123 new_digest          (f1d56d0c…)
PASS sutravali unlinked_reason distribution                 (2986/7/2)
PASS sunapha link set                                       (a5d58ce9…, cf36fd63…)
PASS remedy source drift eliminated                         (0)
PASS Muhurta Chintamani row reattributed                    (0)
PASS ontology relation_type rows                            (7 via 1121)
PASS ontology text aliases present                          (3 via 1123)
PASS seeded data rows                                       (1/7/1/2/1)
PASS mutation guard rejects non-builder chart_facts write
all 33 gates green → BUILD GREEN
```

Negative gate verified: `INSERT INTO chart_facts …` as superuser returns
`ERROR: protected L1 INSERT requires direct data_plane_builder
authentication` (`l1_data_plane_guard_active_mutation()` line 15).

## 5. Deviations from the packet report (each forced by a rehearsal failure or probe)

1. **Data seeds run pre-migration (step d).** A post-migration seed would
   require a fake `data_plane_builder` session to pass the mutation guard.
   Instead the 12 data rows (charts 1, chart_facts 7, ga_yoga_firings 1,
   chart_vichara 2, bodha_msr_signals 1) are inserted before the guard
   triggers exist — same final state, no counterfeit builder session.
2. **Grant replay runs before 1035/1036.** Every `grants.json` table is a
   pre-migration fixture table, and production's grants predated 1035/1036 —
   1036's preflights read `asset_registry` and `asset_output_digest_specs` as
   `data_plane_l2_owner`, which only holds SELECT via those grants. Replaying
   after migrations makes 1036 fail with `permission denied`.
3. **`asset_output_digest_specs` support table** (28th table, not in the
   fixture set). 1036:396-405's bo_samvada preflight reads it unconditionally.
   DDL and grants (SELECT to builder + l2_owner, grantor amjis_app) probed
   from production. Production also grants `retrieval_census_ro` and
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
   table outside the fixture set). The 1120–1123 migrations live in
   `platform/migrations/` (not `platform/supabase/migrations/`) and are applied
   by the oracle (§2); 1124 stays HELD.
7. **Role creation is idempotent** (`DROP ROLE IF EXISTS` first): roles are
   cluster-level and survive the fixture DB drop between runs.
8. **`useEvidenceExplorer.ts` / `catalogService.ts`** named in the packet
   report were not found in this repo — treated as absent, no consumer-shape
   extraction needed.
9. **Dual seed format.** The six digest-sensitive tables are raw
   `to_jsonb(row)::text` line exports (imported byte-faithfully); the other
   five remain the original Python-JSON exports. `seed_manifest.json`'s
   `format_note` records which is which. `yoga_families` /
   `yoga_family_members` stay DDL-only (0 rows in production, verified).
10. **1120 not applied** — disclosed partial application with the exact
    failing statement recorded (§2 item 4). The fixture set does not include
    the five `bg_prashna_*` member tables; adding them would grow the fixture
    set beyond the 27-table probe contract for zero downstream effect.
11. **Synthetic empty-generation digests** for the 9 snapshot-less closure
    generations (§3) — production has never run the data plane, so there is no
    real completion digest to reproduce; the synthetic values are 64-hex and
    disclosed here.
12. **`not_a_yoga_qualifier` not implemented** — the phrase exists only in the
    packet report, not in migration 1123, its test, or the repo (§2). Gates
    use the migration's real vocabulary and numbers.

## 6. Production probe surprises (affect future exports/captures)

- **Production has 0 generations, 0 snapshots, 0 heads** — the data plane has
  never been run. All generation/snapshot rows in the fixture are synthesized.
- **Production sutravali_rules state-A digest is exactly 1123's `old_digest`**
  (`87b69704…`), measured 2026-09-26 — production is in the exact pre-1123
  state the migration expects (3,002 rows, 17 linked, no `unlinked_reason`
  column).
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
- **`chart_facts.chart_id` joins `charts.id` by UUID directly** — `charts.id`
  is `uuid` (`f0000000-…-000000000001` for the fixture chart) and
  `chart_facts.chart_id` carries the same value; there is no integer-identity
  indirection (corrected 2026-09-26, readings-runner verification:
  `information_schema.columns` shows `charts.id uuid`; v1.1's "integer
  identity" note was wrong).
- **ga_positions owns 0 fact categories**; production ownership is 64
  ga_structural, 2 ga_condition, 1 ga_ayurdaya (67 total exported).
- **The five `bg_prashna_*` tables exist in production** but are outside the
  27-table fixture set — the sole reason 1120 cannot apply here (§2 item 4).

## 7. Rehearsal failures encountered and fixed

| # | Failure | Fix |
|---|---------|-----|
| 1 | `permission denied for schema public` (1035 CREATE TABLE as l1_owner) | schema owner + CREATE/USAGE bootstrap (deviation 5) |
| 2 | `role "amjis_app" already exists` on rerun | `DROP ROLE IF EXISTS` (deviation 7) |
| 3 | `permission denied for table asset_registry` (1036 preflight as l2_owner) | grant replay moved before migrations (deviation 2) |
| 4 | `permission denied for table asset_output_digest_specs` (1036 preflight) | support-table grants probed + replayed (deviation 3) |
| 5 | `relation "public.bodha_cgm_nodes" does not exist` (1036 closing GRANT) | 28 L2 stub tables (deviation 4) |
| 6 | negative gate FAIL — syntax error in gate's own INSERT (unquoted UUID literal), guard never reached | quoted the literal; gate now exercises the guard |
| 7 | raw import corrupted escaped quotes: `\copy` text format interprets backslash escapes (`\"Poison` → `"Poison`), breaking JSON on `brahma_ontology` | `\copy … WITH (FORMAT csv, DELIMITER E'\x07', QUOTE E'\x06')` — bytes JSON can never carry raw; Python asserts 0x06/0x07 absent first |
| 8 | j3 contract check false-failed: `query_scalar` is line-splitting, so the multi-line contract compared as `"SELECT"`; the trailing-newline diff was psql's row terminator, not data | full-text fetch preserving newlines, newline-normalized comparison |

---

## 8. Readings runner (W-L0-7 9-step decorated-path rehearsal, 2026-09-26)

Runner: `scripts/l0harness/run_readings.py` (+ `read_serve.ts` tsx bridge).
Full output: `run_readings_20260926.log`; machine state:
`reading_verdicts.json`. Command:

```
cd platform && /Users/Dev/Vibe-Coding/Apps/Madhav/.venv/bin/python3 scripts/l0harness/run_readings.py
```

The runner rebuilds the fixture (step 0), then executes the frozen 9-step
sequence from the packet report v1.5 "Predicted movement" against the real
decorated path (`dry_run=False`) on a direct `data_plane_builder` psycopg
connection — `session_user`, never `SET ROLE` (1035:578-580, 1036:805-807,
1036:941-943 check `session_user`; SET ROLE would not satisfy it).

### Measured verdicts vs the frozen matrix

| Verdict | Predicted | Measured | Result |
|---|---|---|---|
| V-C0-S3 | sunapha absent from `query_yoga_catalog` | `total_matching=0`, sunapha rows=0 | **PASS** |
| V-R2-S4 | firing row PRESENT, `catalog_classical_citations` → NULL | row id=1 present, citations NULL | **PASS** |
| V-R1-S5 | firings lose exactly the sunapha/surya_siddhanta row | R1 cannot complete (F-W-L0-7-9; workaround probe hits F-W-L0-7-5) | **UNMEASURED** |
| V-R2-S6 | sunapha firing row absent | premise broken; actual served state: row PRESENT | **UNMEASURED** |
| V-R3-S7 | catalog_ids/rule_ids → [], citations unchanged | R3 fails at upstream resolution (F-W-L0-7-8) | **UNMEASURED** |

Step 9 (RESEED + REPLAY) green: catalog row re-inserted via
`jsonb_populate_record`, link set exact, replay C0 `total_matching=1`, R2
citations restored.

### Findings measured by the run (verbatim errors in the log/JSON)

- **F-W-L0-7-9 (NEW, masks everything downstream).**
  `InsufficientPrivilege: permission denied for table build_runs` raised
  inside `open_l1_data_plane_generation` (PL/pgSQL line 18 at IF — the
  build_runs/build_run_assets existence check, 1035:599-611). The function is
  SECURITY DEFINER owned by `data_plane_l1_owner`, which holds **no SELECT
  grant on build_runs/build_run_assets** (grant probe: only amjis_app holds
  any privilege on them). The decorated R1 dies before the writer body.
  `open_l2_data_plane_generation` carries the same check (1036:951-963) under
  `data_plane_l2_owner` with the same missing grant — not measurable here
  because R3 fails earlier (F-W-L0-7-8). Whether production grants this is
  unverifiable from the rehearsal cluster (production proxy password
  unavailable); the fixture's grant set is the production-probed one, so the
  defect reproduces with production-faithful grants.
- **F-W-L0-7-5 (confirmed).** Measured via the disclosed grant workaround
  (below): `RaiseException: L1 partition ayanamsha_lahiri_chitrapaksha has
  undeclared empty output` (`complete_l1_data_plane_partition` line 75 at
  RAISE). The ga_yoga writer plans 5 ayanamsha substeps; the fixture seeds
  chart_facts for surya_siddhanta_classical only, so the first substep finds
  0 facts → 0 rows → complete_l1 rejects the undeclared empty partition
  (asset_registry.target_floor=63 ≠ 0). Identical error pre- and
  post-perturbation — the catalog perturbation never reaches the R1 path.
- **F-W-L0-7-8 (confirmed).** R3 pre-flight:
  `ContractError: missing completed selected L1 dependencies: ['ga_yoga']`
  (`bodha_writers/data_plane_contracts.py:262-266`). ga_yoga is in
  bo_laksana's transitive L1 closure but has no generation head (R1 failed),
  so `_resolve_upstream_context` raises before bind/open. Fires identically
  at baseline and post-perturb.
- **F-W-L0-7-7 (re-measured through the real bind path).**
  `InsufficientPrivilege: permission denied for table chart_facts`:
  `bind_l2_exact_inputs` (SECURITY DEFINER, owner data_plane_l2_owner) builds
  pg_temp shadows with relacl NULL; pg_temp precedes public in name
  resolution, so the writer role's unqualified `chart_facts` reads land on a
  shadow it cannot SELECT. Probe used the 11-head vector (bind only validates
  each element vs heads, 1036:813-828 — no closure-completeness check, so the
  bind succeeds even with ga_yoga headless).

### Runner deviations (disclosed)

1. **Serve role = data_plane_builder, not amjis_app.** amjis_app holds no
   SELECT on ga_yoga_firings in the production-probed grant set
   (`grants.json`); data_plane_builder does. `read_serve.ts` honors
   `DATABASE_URL`, so the reads run as data_plane_builder. C0/R2 handlers are
   role-agnostic apart from table grants.
2. **build_runs lifecycle rows inserted as superuser.** data_plane_builder
   holds no INSERT on build_runs/build_run_assets (owner amjis_app; only
   amjis_app grants exist) — the harness mirrors
   `run_heavy_writer_standalone.py:121-141`, which does the same on its own
   connection. State transitions use the fixture-valid CHECK values
   (`failed`/`error`; there is no `last_error` column — error text goes to
   `build_run_assets.error`).
3. **Grant-workaround probe (temporary GRANT + REVOKE, superuser).** To
   measure F-W-L0-7-5 past the F-W-L0-7-9 mask, the runner temporarily runs
   `GRANT SELECT ON build_runs, build_run_assets TO data_plane_l1_owner`,
   reruns R1, then REVOKES — mirroring this fixture's own doctrine (solve
   surprises in the builder/roles, never edit migrations or consumer/writer
   SQL). Both the masked error (F-W-L0-7-9) and the unmasked error
   (F-W-L0-7-5) are recorded as findings; the main-path verdicts use the
   no-workaround result.
4. **R3 bind prime.** F-W-L0-7-1 (decorator opens before binding, but
   1036:984-996 requires a pre-existing pg_temp receipt): each R3 run primes
   exactly one `bind_l2_exact_inputs(chart_id, vector)` in the same
   transaction first. Receipt/shadows are ON COMMIT DROP, so the whole R3 run
   stays in ONE transaction. (Moot in this run — R3 never reaches bind —
   but the prime path is what the probe in finding F-W-L0-7-7 exercises.)

### Fixture-coverage gaps surfaced (for a future fixture revision)

- ga_yoga needs seeded chart_facts for all 5 planned ayanamshas (or a
  declared-empty carve-out) for R1 to complete; today only
  surya_siddhanta_classical is seeded → F-W-L0-7-5.
- The seeded `yoga_label` fact f…005 is not in the snapshot v_map, so the L2
  chart_facts shadow would lack the R3 target fact even if R3 ran.
- The sunapha formation rule (planet_not_sun_in_2nd_from_moon) is unevaluable
  from seeded facts (no MOON position row): any successful R1 rerun would
  DELETE the seeded firing and not recreate it, destroying the step-4
  pre-registered state. This compounds V-R1-S5's premise: the frozen matrix's
  "lose exactly the sunapha row" can only hold if the writer re-derives
  sunapha, which this fixture's fact coverage does not support.
