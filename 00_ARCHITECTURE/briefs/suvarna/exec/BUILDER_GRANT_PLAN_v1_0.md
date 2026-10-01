---
artifact: BUILDER_GRANT_PLAN
version: "1.1"
status: DRAFT-FOR-REVIEW
produced_by: exec-suvarna
date: 2026-10-01
base_commit: origin/main 3311b0a06b424bef1e48c026408321fb59a88eed for the v1.0 analysis; re-checked against 79dc7e07b (writers, services, gate scripts and deploy.yml unchanged between the two)
related: CANONICAL_CHART_REBUILD_PLAN_v1_0.md (P0.2, P0.5 check 2, S3-S6), F3_MSR_FK_DROP_v1_0.md section 5 (branch F3-msr-fk-drop-001, read-only), reader_grants.py (D6 pattern, branch suvarna/exec), migrations 1070, 1073, 404
execution: NONE. Analysis only. No grant, FK drop, admin action, DB write, push, PR, migration or workflow change was made. The SQL and the script below are drafts inside this document.
db_access: read-only, as suvarna_reader (SELECT, has_*_privilege, catalog reads). Evidence and queries in /Users/Dev/suvarna-evidence/Grants/ (verify.sql, verify_before.txt, verify_v11_extra.sql, verify_v11_before.txt, verify_v11_recheck.txt, builder_grants_v1_1_DRAFT.py, progress.md).
changelog:
  - "1.1 (2026-10-01, SS ruling): ONE REVIEW now covers (A) the three data_plane_l2_owner-owned foreign keys into bodha_msr_signals (owner-path drop), (B) the phala_*/mimamsa_* builder grants of v1.0 plus three additions found in this pass (asset_registry.selftest_detail column UPDATE, bg_combustion_orbs SELECT; the L3 audit of every kala_* privilege), and (C) the pre-check/audit of the Kala wave. One consolidated plan hash (19 statements), one executor, one verification and rollback. The deploy-gate pin check was extended to constraints and asset_registry column ACLs: neither is pinned, so the gate amendment part stays empty. v1.0 phala/mimamsa facts re-verified live (unchanged)."
  - "1.0 (2026-10-01): first draft for SS review. Covers the second grant gap only (phala_* and mimamsa_* target tables for data_plane_builder). The asset_throughput_state_audit grant is Pravaha's and is NOT covered here."
---

# Builder grant plan v1.1: L2 foreign-key drops + builder grants (REVIEW document for SS)

One consolidated change set, run by the D6 in-process executor after SS's `APPROVED <plan hash>`:

- **Part A**: drop three foreign keys into `bodha_msr_signals` that `data_plane_l2_owner` owns (owner-path; F-3 section 5).
- **Part B**: grant `data_plane_builder` what the S3-S6 writers need: the `phala_*`/`mimamsa_*` tables (v1.0), `asset_registry.selftest_detail`, two reference reads, and EXECUTE on two functions.
- **Audit (C)**: the builder's privileges on every `kala_*` table and on the tables the Kala writers read were re-measured; the additional grants it found are in Part B, and what was found but deliberately not granted is listed in section 3.2.

The `asset_throughput_state_audit` grant is Pravāha's and is not covered.

Evidence labels used throughout: **observed** (read live as `suvarna_reader`, 2026-10-01 about 15:17 to 16:30Z), **repo** (file:line at the base commit), **code-derived** (follows from code or PostgreSQL semantics, never observed in production), **not visible** (the reader cannot see it).

## 0. What SS needs to see first

1. **No deploy-gate amendment is needed for any part.** `data-plane-ownership-status.ts` pins neither constraints nor the `phala_*`/`mimamsa_*` objects nor `asset_registry` column ACLs (section 2, 2.1, 2.2). The ordering "gate amendment, then owner-path FK drops, then grants" therefore collapses to "FK drops, then grants", in one transaction.
2. **Consolidated plan: 19 statements** (3 `ALTER TABLE ... DROP CONSTRAINT` as `data_plane_l2_owner`; 16 `GRANT` as `amjis_app`), **one hash for apply and one for rollback** (section 4, Part C). Current draft hashes: apply `2b4793057bbe5978b7ba5b5a46b05d6dd8f5190609166306e045b7a043c1856a`, rollback `beb76d4ed09a8566b2be676a1dd1e8d98308544821d6403b00a8714d5360475b`.
3. **Extra grants found beyond what SS named, all additions to Part B:**
   - `GRANT UPDATE (selftest_detail) ON public.asset_registry`: four services write it, not two: `ka_dasha_kala` (`services/ka_dasha_kala/writer.py:94-100`), `ka_muhurta_seva` (`services/ka_muhurta_seva/writer.py:295-301`), plus `ka_tulana` (`services/ka_tulana/writer.py:71-77`) and `ka_graha_sancara` (`pipeline/orchestrator/writers/ka_graha_sancara.py:259-265`).
   - `SELECT` on `bg_combustion_orbs` (`ka_vighnakara.py:302`): read inside a SAVEPOINT whose `except Exception` falls back to constants (`:307-311`); today the constants equal the table (observed), so the result would be identical, but it is a silent fallback, not a failure.
   - From v1.0 (still needed): `SELECT` on `life_events` (5 columns), `SELECT` on `brahma_activity_ontology`, EXECUTE on `phala_anchor_identity` and `phala_anchor_identity_namespace`.
4. **`kala_obstruction` is fine**: the builder holds SELECT, INSERT, UPDATE, DELETE on it (observed), and on the target table of every one of the 19 `ka_*` assets that have one (18 distinct tables) and every sequence owned by a `kala_*`/`gochara_*` table. The only `kala_*`/`gochara_*` tables the builder cannot touch are the gochara-kernel family (`kala_gochara_contacts`, `_coverage`, `_publication`, `_convention`, `_cutover_step05_snapshot`) and a SELECT-only archive; no registered writer of an S0-S4 asset writes them (section 3.2), so they are reported, not granted.
5. **Ordering correction for the rebuild plan:** `ka_bhavishya_lekha` (stage S4) reads `phala_anchors` whenever `kala_bhavishya` already holds rows for the chart (`ka_bhavishya_lekha.py:249-280`), so the Part B grant must be in place before S4 on any re-run, not only before S5. On the canonical chart `kala_bhavishya` holds 0 rows today, so the read is skipped there (observed in the rebuild plan), but other charts and any second run need it.
6. **Consequence of Part A, stated plainly:** after the three keys are dropped, deleting MSR signals no longer cascades to `bodha_signal_embeddings` and `bodha_contradictions`. The L2 writers already delete those rows explicitly before the MSR delete (`bodha_writers/_idempotency.py:120,123,196,201`), so nothing is lost today, but SS's invariant (MSR writers strictly before Kala/Phala assets, none rebuilt later in the window) stays in force until both migration 1214 and this Part A are deployed (F-3 SS decision 4).
7. **1214 status (observed):** not applied (`_migrations_applied` max id 904, last file `1210_asset_registry_direct_edges.sql`; `1214` exists only on the F-3 branch). The three owner-path keys are independent of 1214: either order works, and the post-state of V10 below says which.
8. **Recommended executor:** the holder of the Secret Manager administrator secret, using the D6 in-process pattern (Part C). No swarm lane.

## 1. Facts, read-only

### 1.1 Per-table ownership and ACL (observed; `pg_class`, `relacl`)

All ten: owner `amjis_app`, `relkind r`, `relrowsecurity = false`, `relforcerowsecurity = false`, no column-level ACL (`pg_attribute.attacl` null for all), no owned sequence, no identity or serial default. `has_table_privilege('data_plane_builder', t, ...)` is **false for SELECT, INSERT, UPDATE, DELETE, TRUNCATE** on every one (evidence `verify_before.txt`). Rows today (all charts): phala_anchors 60, phala_muhurta 183, phala_mitigation 1277, phala_sankrama 630, phala_sodhana 41, phala_suddha_sodhana 60, phala_pramana 60, phala_phaladesa 26, mimamsa_predictions 195 (all `pending`, 0 outcome-bearing), mimamsa_manifestation_sets 195.

Which roles hold what (the `relacl` grantee sets are the same shape on all ten; `mimamsa_predictions` differs as noted):

| Grantee | Privileges | Notes |
|---|---|---|
| `amjis_app` (owner) | arwdDxt | `mimamsa_predictions` owner entry is `arwdxt` (no TRUNCATE) |
| `role_orchestrator` | arwd | NOLOGIN group role; has the write rights the builder lacks, but `data_plane_builder` holds zero memberships and is NOINHERIT, so it inherits nothing (same fact recorded by 1070 and 1073) |
| `role_jobs`, `role_sidecar`, `role_web_serve`, `retrieval_census_ro`, `nirmana_evidence_ingress_writer`, `suvarna_reader` | r | `role_jobs` and `role_sidecar` are absent on a few tables, see the evidence |
| `role_ledger_write` | arw | only on `mimamsa_predictions` (not on the phala_* tables) |
| `data_plane_builder` | none | the gap |

Other facts that bear on least privilege:

- **Triggers:** only `phala_anchors_identity_biu` (BEFORE INSERT, `phala_anchors_set_identity()`, owner `amjis_app`, **not SECURITY DEFINER**). It assigns `NEW.anchor_id := phala_anchor_identity(...)`.
- **Functions:** `phala_anchor_identity(uuid,text,text,text,text,text,date,date,date,text)` and `phala_anchor_identity_namespace()` have `proacl = {amjis_app=X/amjis_app}`, so no PUBLIC EXECUTE; `has_function_privilege('data_plane_builder', ..., 'EXECUTE')` is false for both and for the trigger function. Cause: `pg_default_acl` for role `amjis_app` has `{amjis_app=X/amjis_app}` for functions (observed). `uuid_generate_v5` and `jsonb_build_array` are PUBLIC-executable, so they are not a gap.
- **RLS:** disabled on all ten. `mimamsa_predictions` carries two policies (`mimamsa_predictions_g1c_unscoped` for `role_jobs, role_ledger_write, role_orchestrator`; `mimamsa_predictions_g1c_chart_context` for `role_sidecar, role_web_serve`) that are inert while RLS is off. The builder is in neither list. If RLS were ever enabled, the builder would need a policy (latent risk, section 5).
- **Foreign keys** touching the ten (observed): `phala_anchors` is referenced by `phala_muhurta` (SET NULL), `phala_mitigation` (SET NULL), `phala_sankrama`, `phala_suddha_sodhana`, `phala_sodhana`, `phala_pramana` (all CASCADE); `phala_anchors` references `kala_bhavishya` (SET NULL) and `kala_convergence` (CASCADE); `mimamsa_predictions` references `build_runs` (SET NULL). Referential-integrity actions and checks run as the owner of the table they operate on (`amjis_app` for all), so the FKs need **no extra grant** (code-derived from PostgreSQL's RI trigger execution).
- **Protected-table status:** none of the ten is a `data_plane_*_owner` table (owner is `amjis_app` for all); `phala_*`/`mimamsa_*` are absent from the protected lists in `data-plane-ownership-preflight.ts:9-22`.
- **Scale of the gap (observed):** the builder lacks SELECT on all 10 of the live `phala_*` tables and all 28 of the live `mimamsa_*` tables (shadow `__ssv_` tables excluded). This plan grants 10 of 38. Migration 1070's header recorded "0/37 and 0/20 accessible" and nothing has since granted it.

### 1.2 What the reader could not see

- The job's live runtime DB identity (Secret Manager / Cloud Run), and whether it connects as `data_plane_builder` today. The smoke build (rebuild plan P0.4) proves that.
- Whether `postgres` can run `GRANT amjis_app TO postgres` right now. Precedent says yes: `data-plane-ownership-preflight.ts:278` did exactly that on 2026-09-18 and `:358` reverses it; PostgreSQL 15.18 lets a CREATEROLE role (observed: `postgres` has `rolcreaterole`) grant a non-superuser role. The `--dry-run` proves it before anything commits.
- Other sessions' open transactions and locks.
- The PostgreSQL behaviour that a trigger function is ACL-checked at CREATE TRIGGER, not at fire time (hence no grant on `phala_anchors_set_identity()`). This is code-derived and is exactly what the first `ph_nimitta` S5 run would confirm or refute (loud failure, no data change).

### 1.3 The three L2 foreign keys (observed; `pg_constraint`, 2026-10-01)

All eight foreign keys that reference `bodha_msr_signals(signal_id)` are `ON DELETE CASCADE` (`confdeltype c`), `ON UPDATE NO ACTION`, `MATCH SIMPLE`, not deferrable, validated. Three are owned by `data_plane_l2_owner` (the referencing tables and `bodha_msr_signals` are all owned by it; `postgres` is not a member, `pg_has_role('postgres','data_plane_l2_owner','MEMBER')` is false):

| Constraint | Table | Exact current `pg_get_constraintdef` (the rollback text) |
|---|---|---|
| `bodha_contradictions_signal_a_id_fkey` | `bodha_contradictions` | `FOREIGN KEY (signal_a_id) REFERENCES bodha_msr_signals(signal_id) ON DELETE CASCADE` |
| `bodha_contradictions_signal_b_id_fkey` | `bodha_contradictions` | `FOREIGN KEY (signal_b_id) REFERENCES bodha_msr_signals(signal_id) ON DELETE CASCADE` |
| `bodha_signal_embeddings_signal_id_fkey` | `bodha_signal_embeddings` | `FOREIGN KEY (signal_id) REFERENCES bodha_msr_signals(signal_id) ON DELETE CASCADE` |

The other five are the `kala_*` keys that migration 1214 (branch F-3, not applied) handles; they are owned by `amjis_app`. Facts that bear on the drop:

- Each of the three has four internal RI triggers (two on the referencing table, two on `bodha_msr_signals`): `bodha_msr_signals` carries 16 internal RI triggers today (8 keys x 2), `bodha_contradictions` 4, `bodha_signal_embeddings` 2. They disappear with the keys; no dependent object (view, function, index) depends on the constraints (`pg_depend`, non-internal, observed 0). The unique index behind them (`conindid` 157449) is the `bodha_msr_signals` key and is not touched.
- The only non-internal triggers on the three tables are `l2_data_plane_capture` and `l2_data_plane_mutation_guard`, which fire on row DML, not DDL. No event trigger exists (`pg_event_trigger` empty).
- Size, for lock-time expectations: `bodha_msr_signals` and `bodha_signal_embeddings` 150,724 rows each (observed); `bodha_contradictions` is estimated at 45 rows (the reader has no SELECT on it, so a count is not visible). Zero embeddings are orphaned today (observed), so a rollback re-add would validate cleanly now.
- `assert_l2_msr_delete_safe` (SECURITY DEFINER, owner `data_plane_l2_owner`, attested) reads `pg_constraint` live and skips exactly these two tables (`1036_data_plane_l2_producer_generations.sql:732-744`, with `CONTINUE` at `:744`); the live function body contains that branch (observed). Dropping the three keys makes the loop find fewer rows and changes nothing else. SS has already declined to alter it (F-3 SS decision 2).

### 1.4 asset_registry column ACL (observed)

`asset_registry` is owned by `amjis_app`, RLS off, table-level `data_plane_builder=r`. Column-level UPDATE for the builder exists on exactly three columns (`service_health`, `last_invoked_at`, `last_selftest_at`, `{data_plane_builder=w/amjis_app}`), granted by migration 1070. Its only non-internal trigger, `nirmana_registry_receipt_invalidation`, is `AFTER UPDATE OF depends_on, natural_key_partition, health_probe, integrity_check_sql, target_floor, asset_kind, asset_type, scope, has_writer, is_active, target_table`, so an update of `selftest_detail` alone does not fire it.

## 2. Does the deploy gate pin these tables? **No.**

The deploy workflow runs, on every deploy and before any service deploys, `Inspect protected data-plane ownership state` (`.github/workflows/deploy.yml:509-523`, `npx tsx scripts/data-plane-ownership-status.ts`; a throw makes the step `exit 1`), `Inspect protected data-plane runtime isolation` (`:529-542`, `data-plane-secret-isolation-preflight.ts`, mode `strict`; a failure sets `repair_required` rather than failing the job, but `:588` then routes the privileged-bootstrap path), the Nirmāṇa marker (`:544-558`) and the Pūrṇa state (`:560-574`). The ownership state is re-read under the exclusive lock at `:686-700`. Reviewed lines, in order of relevance to table grants:

| Gate check | file:line | Scope of what it compares | Covers our objects? |
|---|---|---|---|
| Role attributes (6 roles, exact) | `data-plane-ownership-status.ts:78-87` | role flags only | No (no table or ACL involved) |
| Unknown `data_plane_%` principal | `:88-95` | role names | No |
| Memberships, exact and recursive | `:97-143` | edges whose parent or member is one of the six `data_plane_*` roles; expected set is exactly the three migrator-to-owner edges | No. `amjis_app -> postgres` (the transient edge) is never committed and involves none of the six roles |
| Protected table and sequence ownership | `:145-162` | `L1_ACTIVE_TABLES`, `L2_ACTIVE_TABLES` | No |
| Exact relation set and owners | `:164-196` | the lists above plus relations named `l1_data_plane_*`, `l2_data_plane_*` | No |
| Sequence ACL allowlist | `:229-254` (arg at `:253`) | sequences owned by the protected tables | No |
| Lifecycle function hardening | `:256-263` | 14 named functions | No |
| Trigger inventory, shape, surface | `:265-318` | protected tables | No |
| Function digests | `:320-351` | attested functions; the second branch scans functions **owned by `data_plane_l1_owner`/`data_plane_l2_owner`** | No: ours are owned by `amjis_app` |
| Policies, views, default privileges | `:353-417` | protected tables; default ACLs only for the two protected owners | No (`amjis_app`'s own default ACL is not read) |
| **Table ACL allowlist** (builder allowed S/I/U/D) | `:419-447`, argument `[...L1_ACTIVE_TABLES]`, `[...L1_ACTIVE_TABLES, ...L2_ACTIVE_TABLES]` at `:446` | exactly the 12 + 29 protected tables | **No** |
| History/view ACL allowlist | `:449-483`, arguments at `:482` | `L1_HISTORY`, `L2_HISTORY` | No |
| `public` schema ACL (exact) | `:485-511` | schema ACL, not table ACL | No (nothing we change) |
| Function EXECUTE allowlist | `:513-557` | `protected` = functions in the attestation tables only (`:517-522`) | **No**: `phala_anchor_identity*` are not attested |
| Write/DDL privilege drift | `:559-570`, argument `:569` | `has_table_privilege` for builder `TRUNCATE,TRIGGER,REFERENCES`, `amjis_app` and `role_orchestrator` DML, on the protected tables only | No; and this plan grants none of TRUNCATE, TRIGGER, REFERENCES |

The only table lists the gate and the cutover preflight know are `L1_ACTIVE_TABLES`, `L2_ACTIVE_TABLES` (`data-plane-ownership-preflight.ts:9-22`) and the explicit builder-DML list `CONTROL_AND_L0_L3_TABLES` (`:32-68`, consumed at `:325-345`). `grep -E 'phala_|mimamsa_|life_events|brahma_activity_ontology'` over that file returns nothing: the cutover scoped the builder to control tables, L0 to L3 and the protected producers, which is the origin of this gap. Because the grant loop at `:326-345` is a `REVOKE ALL ... FROM data_plane_builder; GRANT S/I/U/D` per listed table only, a re-run of the cutover would neither revoke nor re-grant our objects.

Other pins checked:

- `nirmana-evidence-ownership-status.ts` (38 lines) reads one `_migrations_applied` marker; no table ACL.
- `data-plane-secret-isolation-preflight.ts` (IAM and Cloud Run only, no SQL). The relevant message is `:477` ("Builder credential is mounted outside the one named build job") and `:481` ("Builder identity is used outside the one named build job"); unit tests `data_plane_security_contract.test.ts:236-241,301-305`. A table grant does not touch any of those inputs.
- Tests: `tests/integration/data_plane_protected_roles.db.test.ts:450-465` ("builder DML denied on every protected table") queries `L1_ACTIVE_TABLES + L2_ACTIVE_TABLES` only, on a disposable DB. `tests/unit/data_plane_builder_l3_reference_read_grants.test.ts:28-30` pins that migration 1073 does not grant `phala_rectification` (relevant to Q2).
- `src/generated/capability_estate_census.json` mentions `data_plane_builder` twice but is a repo-source census, not a DB ACL.

**Conclusion: a GRANT to `data_plane_builder` on these objects will not make any deploy-time ownership or isolation check fail.** To prove it rather than assert it, the post-apply verification runs the real gate under the reader (D6 runbook `§3`, the `data-plane-ownership-status.ts` command at `D6_SUVARNA_READER_RUNBOOK_v1_0.md:314`) and expects `marked` (V18) (V18 below). If a future decision puts these tables under protection, `L1_ACTIVE_TABLES`/`L2_ACTIVE_TABLES` would have to change first; that is out of scope.

Is the grant permitted by the data-plane ownership contract? Yes. `MADHAV_DATA_PLANE_RI02_SECURITY_CUTOVER_v1_0.md:98-99` gives the builder "exact producer DML ... no schema create, owner membership, TRUNCATE, TRIGGER, REFERENCES", and the protected-object map covers L1 and L2 only. Grants to the builder on tables owned by `data_plane_l2_owner`/`data_plane_schema_owner` would be a different question; none of our objects is one.

### 2.1 Does the gate or any preflight pin the three L2 constraints? **No.**

The question asked: constraint lists, FK counts, `pg_constraint` comparisons, the L2 attested functions and digests. Read at the base commit:

- **No constraint query exists in the gate.** A search of `data-plane-ownership-status.ts` (577 lines), `data-plane-ownership-preflight.ts`, `nirmana-evidence-ownership-status.ts` (38 lines), `purna-inquiry-ownership-status.ts`, `data-plane-secret-isolation-preflight.ts`, `data-plane-cutover-preflight.ts`, `data-plane-migration-attestation.ts` and `.github/workflows/deploy.yml` for `pg_constraint`, `contype`, `conname`, `confrelid`, `FOREIGN KEY` and `constraint` returns nothing. The only `pg_depend` joins are for sequence ownership (`data-plane-ownership-status.ts:154,207,233`; `data-plane-ownership-preflight.ts:224,338`), not constraints.
- **Relations:** the exact-relation check (`data-plane-ownership-status.ts:164-196`) compares name, kind and owner of the protected relations; it does not read their constraints.
- **Triggers:** the trigger inventory, shape and surface checks (`:265-318`) filter `NOT t.tgisinternal`, so the RI triggers that disappear with the keys are outside them; the L2 trigger attestation table holds 58 rows, none named `RI_*`, and for the three tables exactly the six non-internal ones (observed).
- **Functions and digests:** `assert_l2_msr_delete_safe` is in the lifecycle list (`:37`) and the digest check (`:320-351`); we do not touch the function, so its attested digest, owner, SECURITY DEFINER flag and config are unchanged. Function EXECUTE allowlist (`:513-557`) is unchanged.
- **Manifest and outputs:** `l2_data_plane_manifest_attestations` (`:219-227`) digests `asset_id`/`source_table` pairs of `l2_data_plane_asset_outputs`, not constraints.
- **Migration 1036 itself** defines the L2 generation foreign keys (`:60-239`, `:325-382`) and a CHECK `bodha_msr_signals_producer_asset_check` (`:325-327`); none of them is into `bodha_msr_signals` or one of the three.
- **Tests and CI:** no test, workflow or script in `platform/` or `.github/` names any of the three constraints; the only repository mention outside migrations is migration 404's own text (`404_bodha_signal_fk_cascade.sql:12-23`). The unit and DB tests of the L2 contract (`bodha_writers/__tests__/test_l2_data_plane_contracts.py:215,265,286,493,540`) exercise the function, not the keys.
- **Memberships:** the transient `GRANT data_plane_l2_owner TO postgres` is the one thing that touches a pinned role. It is never committed (added and removed in the same transaction; a membership grant is transactional), and the gate's membership checks (`:97-143`) read committed state. The same pattern was used for `reader_grants.py` (D6) with this very role.

**Conclusion: dropping the three constraints will not make any deploy-time ownership or isolation check fail, so there is no gate amendment and nothing to order first.** The post-apply proof is the same as for the grants: run the gate under the reader and expect `marked` (V18).

### 2.2 Does the gate pin `asset_registry` column ACLs? **No.**

`asset_registry` appears in `data-plane-ownership-status.ts` zero times and in `data-plane-ownership-preflight.ts` only at `:31` (a comment), `:283` (`UPDATE ... bo_samvada`) and `:285` (a SELECT grant to the migrator-era roles). The gate contains no column-ACL query (`attacl`, `has_column_privilege`, `column_privileges` do not occur in `data-plane-ownership-status.ts` or the preflight). The orchestrator's own registry guard `_verify_registry_still_matches_manifest` (`runner.py:343-372`) compares `scope`, `depends_on`, `natural_key_partition` and co-writers, not `selftest_detail`. So `GRANT UPDATE (selftest_detail)` is outside every pin.

## 3. What the builder actually does to each object (writer code)

Statement inventory from the writers at the base commit (paths under `platform/python-sidecar/pipeline/orchestrator/writers/`). Every `ph_*` writer is chart-scoped delete-then-insert; the table is written only by its own asset.

| Asset | Object | Statements (file:line) | Needed |
|---|---|---|---|
| ph_nimitta | phala_anchors | `DELETE ... WHERE chart_id` (`ph_nimitta.py:129`); `INSERT ... ON CONFLICT (anchor_id) DO NOTHING` (`:224`, `:260`), calling `phala_anchor_identity()` inline (`:243`) | SELECT (conflict inference, integrity and digest reads), INSERT, DELETE; EXECUTE on the two functions |
| ph_muhurta | phala_muhurta | DELETE (`ph_muhurta.py:63`); INSERT ... ON CONFLICT DO NOTHING (`:183`, `:204`); reads phala_anchors (`:262`) | S, I, D |
| ph_muhurta | brahma_activity_ontology | SELECT (`:503`), errors swallowed (`:510`) | S (global reference table) |
| ph_pratikara | phala_mitigation | DELETE (`ph_pratikara.py:100`); INSERT (`:161`, ON CONFLICT DO NOTHING `:182`) | S, I, D |
| ph_sankrama | phala_sankrama | DELETE (`ph_sankrama.py:78`); INSERT (`:151`, ON CONFLICT ON CONSTRAINT natural_key DO NOTHING `:172`) | S, I, D |
| ph_sodhana | phala_sodhana | DELETE (`ph_sodhana.py:53`); INSERT (`:70`, ON CONFLICT DO NOTHING `:85`) | S, I, D |
| ph_suddha_sodhana | phala_suddha_sodhana | DELETE (`:46`); INSERT ... **ON CONFLICT (chart_id, anchor_id) DO UPDATE SET ...** (`:70`, `:89`) | S, I, **U**, D |
| ph_pramana | phala_pramana | DELETE (`ph_pramana.py:56`); INSERT (`:79`, ON CONFLICT DO NOTHING `:96`) | S, I, D |
| ph_pramana | life_events | `SELECT id, event_date, category, description AS event_summary, outcome_observed FROM life_events ORDER BY event_date` (`:190`) | column SELECT on those 5 columns |
| ph_phaladesa | phala_phaladesa | DELETE (`ph_phaladesa.py:170`); INSERT ... **ON CONFLICT (chart_id, domain) DO UPDATE SET ...** (`:208`, `:237`); joins phala_anchors, suddha_sodhana, pramana, sankrama, muhurta, mitigation (`:344-446`) | S, I, **U**, D |
| mi_bhavisya | mimamsa_predictions | `SELECT * FROM phala_anchors` (`mi_bhavisya.py:80`); `DELETE ... WHERE chart_id AND lifecycle_status IN ('pending','due')` (`:230`); INSERT (`:243`) | S, I, D |
| mi_bhavisya | mimamsa_manifestation_sets | DELETE (`:228`); INSERT (`:256`) | S, I, D |

Consequences for least privilege:

- **No TRUNCATE, TRIGGER, REFERENCES anywhere** (matches the contract row). **No UPDATE** except the two `ON CONFLICT DO UPDATE` tables. `ON CONFLICT DO UPDATE` requires UPDATE on the columns it sets; the SET lists in both writers are essentially the full column set (`ph_phaladesa.py:237-261`, `ph_suddha_sodhana.py:89-101`), so column-level UPDATE would add brittleness (a writer edit adding a column would fail loudly until the grant is re-issued) for almost no protection. Proposal: table-level UPDATE on those two tables only (Q4 asks SS to confirm).
- **SELECT is needed on every one of the ten**, not only to read upstream: `DELETE ... WHERE chart_id` needs SELECT, `ON CONFLICT (cols)` inference needs SELECT on those columns, the asset's `integrity_check_sql` and output-digest SELECTs run against the target table (observed in `asset_registry.integrity_check_sql`: they read phala_anchors and the target and, for `ph_sankrama`/`ph_pratikara`, `bodha_cdlm_cells`/`kala_obstruction`, which the builder can already read, observed).
- **`mi_bhavisya` uses `SELECT *`** on `phala_anchors`, so column-level SELECT would not work there; table-level SELECT it is.
- **`mi_abhilekha` is out of scope for this wave.** Its code (`mi_abhilekha.py:70`, `UPDATE mimamsa_predictions SET lifecycle_status`) is the update-only case SS mentioned, but its registry target is `mimamsa_journal` and it also reads `mimamsa_journal`/`mimamsa_calibration`, none of which the builder can access. It is not in S5 or S6. Granting UPDATE on `mimamsa_predictions` now would give the builder the ability to alter outcome status for a path nothing in this wave runs (Q3).
- **Upstream reads outside the ten** were checked one by one against `has_table_privilege` (observed): `chart_facts`, `kala_convergence`, `kala_bhavishya`, `kala_obstruction`, `kala_activation_predicates`, `bodha_msr_signals`, `bodha_pratijna`, `bodha_discoveries`, `bodha_contradictions`, `bodha_cgm_paths`, `bodha_cdlm_cells`, `bodha_signal_embeddings`, `bodha_rm_remedy_prescriptions`, `ga_condition_composite`, `chart_dashas`, `charts`, `brahma_event_ontology`, `brahma_formula_constants` all SELECT = true. The three that are not: `life_events`, `brahma_activity_ontology`, and `phala_rectification(_best)` (not read by any S5/S6 writer; grep of the S5/S6 writers and `services/ph_*` shows no reference outside comments).


### 3.1 `asset_registry.selftest_detail` (the four service writers)

| Service asset | Statement | Behaviour without the grant |
|---|---|---|
| `ka_dasha_kala` | `UPDATE asset_registry SET service_health, last_selftest_at, selftest_detail WHERE asset_id='ka_dasha_kala'` (`services/ka_dasha_kala/writer.py:94-100`) | `permission denied for table asset_registry` (the column list includes an ungranted column), code-derived |
| `ka_tulana` | same shape (`services/ka_tulana/writer.py:71-77`) | same |
| `ka_muhurta_seva` | `_write_service_health` (`services/ka_muhurta_seva/writer.py:287-301`), called at `:121` outside any try | the exception propagates, the asset fails |
| `ka_graha_sancara` | `ka_graha_sancara.py:259-265` inside `except Exception` that logs `failed to write service_health` | logged and swallowed, but on the build connection the failed statement leaves the transaction aborted unless a savepoint isolates it (not verified), so a later statement can fail with an unrelated-looking error |

The three columns migration 1070 granted cover `asset_runner.py:651-656,691-696` (the generic probe updates). `selftest_detail` is a JSON blob the cockpit renders (`src/app/api/cockpit/registry/route.ts:69`); it is not part of any digest or manifest. Of the four services, `ka_muhurta_seva` is in the 26-asset plan (stage S1); the others are registered assets outside it.

### 3.2 Kāla wave privilege audit (C), observed 2026-10-01

Method: `has_table_privilege`/`has_sequence_privilege` for `data_plane_builder`, for (a) every target table of the 23 registered `ka_*` assets (19 have a target table, 18 distinct; 4 are services), (b) all 47 live `kala_*`/`gochara_*` tables (shadow `__ssv_` copies excluded) and their identity sequences, (c) every table named in the SQL of the writers of `ka_vighnakara`, `ka_sangam`, `ka_dasha_kala`, `ka_muhurta_seva`, `ka_avadhi`, `ka_kshetra`, `ka_yojaka`, `ka_tulana`, `ka_graha_sancara`, `ka_bhavishya_lekha`, `ka_kalasutra`, `ka_kala_darshana`, `ka_gochara`, `ka_vedha_gochara`, `ka_gochara_resonance`, `ka_moorti_nirnaya`, `ka_tithi_pravesha` and the services they import, extracted statically (FROM/JOIN/INTO/UPDATE/DELETE) and then checked against the verbs the code uses. This is a static scan: SQL assembled from variables could be missed, which is what the smoke builds and the first stage runs would show.

Result:

- **Targets:** all 18 distinct `ka_*` target tables, including `kala_obstruction` (`ka_vighnakara`, `ka_kala_darshana`), have SELECT, INSERT, UPDATE and DELETE for the builder (service assets have no target table). All identity sequences of `kala_*`, `gochara_*` tables have USAGE. 41 of the 47 `kala_*`/`gochara_*` tables are fully writable by the builder.
- **Missing and on a registered build path (added to Part B or already in it):** `asset_registry.selftest_detail` (section 3.1); `bg_combustion_orbs` SELECT (`ka_vighnakara.py:302`, silent fallback; the 8 table values equal the 8 fallback constants today, observed); `phala_anchors` SELECT (`ka_bhavishya_lekha.py:271`; already in Part B; needed from S4 on re-runs).
- **Missing, held, not granted:** `phala_rectification` SELECT (`ka_kshetra`, `uncertainty.py:185-196` via `stage3_clocks.py:1012`). `ka_kshetra` is not in the 26-asset plan, and migration 1073 holds this grant on a design ruling (Strategy section 6.2); unchanged.
- **Missing, outside this wave, not granted (gochara kernel, Pravāha's territory):** `kala_gochara_contacts`, `kala_gochara_coverage`, `kala_gochara_publication`, `kala_gochara_convention` (written by `services/gochara_kernel/ledger.py`, read by `ka_gochara/service.py:477,549`), `bg_transit_av_gates` (`gochara_v3/context.py:448`, loud failure by design, used by the inactive `ka_gochara_v3_century_materialize`), `kala_gochara_cutover_step05_snapshot`, and SELECT-only `kala_gochara_windows_archive_20260805` (the 1073 note on the R6 drill). No `@register`ed writer of an S0-S4 asset names the first four: the `ka_sangam` static hit comes from `KaGocharaService.find_episodes`, which the `ka_sangam` writer never calls (no caller outside the service). They are reported here so SS can hand them to Pravāha; they are not in this plan.
- **Already fine:** every `bodha_*`, `brahma_*`, `bg_*`, `chart_*`, `ga_*`, `charts`, `ephemeris_daily`, `kala_field_*`, `build_substep_progress` and other read or write named by those writers.

### 3.3 Re-verification of the v1.0 phala/mimamsa part

Re-run at about 16:20Z: the ten tables' owner (`amjis_app`), `relacl` md5 (identical to v1.0, including the `mimamsa_predictions` entry), `relrowsecurity` (false), builder matrix V1-V8 (identical output, `verify_v11_recheck.txt`), the V7 md5 of all other ACL entries (`a15ebe2724202646dc9570e21c374bca`, unchanged), row counts (`phala_anchors` 60, `mimamsa_predictions` 195, all pending), active runs 0, last applied migration unchanged. Writer, service and gate files are byte-identical between `3311b0a06` and `79dc7e07b` (`git diff --stat` empty for them). Nothing in v1.0 needed to change.

## 4. The consolidated plan

### Part A. Owner-path foreign-key drop (executed as `data_plane_l2_owner`)

```sql
SET LOCAL lock_timeout = '5s';
-- via SET LOCAL ROLE data_plane_l2_owner (postgres is added to the role transiently, removed before commit)
ALTER TABLE public.bodha_contradictions    DROP CONSTRAINT bodha_contradictions_signal_a_id_fkey;
ALTER TABLE public.bodha_contradictions    DROP CONSTRAINT bodha_contradictions_signal_b_id_fkey;
ALTER TABLE public.bodha_signal_embeddings DROP CONSTRAINT bodha_signal_embeddings_signal_id_fkey;
```

No `IF EXISTS`: the pre-state is known (V9, 3 rows), so a missing constraint should fail the plan, not pass it. Each DROP takes ACCESS EXCLUSIVE on its table and a lock on `bodha_msr_signals`; F-3's proof showed a reader holding a lock on `bodha_msr_signals` makes the drop fail after exactly 5 s with `LockNotAvailable`, which rolls everything back (so it fails loudly instead of queueing). Run it when no MSR writer or long reader is active (Part D).

### Part B. Grants (executed as `amjis_app`, the owner of every object below)

```sql
-- 10 target tables (S5: 8 ph_* assets; S6: mi_bhavisya)
GRANT SELECT, INSERT, DELETE         ON TABLE public.phala_anchors               TO data_plane_builder;
GRANT SELECT, INSERT, DELETE         ON TABLE public.phala_muhurta               TO data_plane_builder;
GRANT SELECT, INSERT, DELETE         ON TABLE public.phala_mitigation            TO data_plane_builder;
GRANT SELECT, INSERT, DELETE         ON TABLE public.phala_sankrama              TO data_plane_builder;
GRANT SELECT, INSERT, DELETE         ON TABLE public.phala_sodhana               TO data_plane_builder;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.phala_suddha_sodhana        TO data_plane_builder;  -- ON CONFLICT DO UPDATE
GRANT SELECT, INSERT, DELETE         ON TABLE public.phala_pramana               TO data_plane_builder;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.phala_phaladesa             TO data_plane_builder;  -- ON CONFLICT DO UPDATE
GRANT SELECT, INSERT, DELETE         ON TABLE public.mimamsa_predictions         TO data_plane_builder;
GRANT SELECT, INSERT, DELETE         ON TABLE public.mimamsa_manifestation_sets  TO data_plane_builder;
-- reference reads (without them: ph_muhurta and ka_vighnakara degrade silently)
GRANT SELECT ON TABLE public.brahma_activity_ontology TO data_plane_builder;
GRANT SELECT ON TABLE public.bg_combustion_orbs       TO data_plane_builder;
-- column-level
GRANT SELECT (id, event_date, category, description, outcome_observed) ON TABLE public.life_events TO data_plane_builder;  -- ph_pramana
GRANT UPDATE (selftest_detail) ON TABLE public.asset_registry TO data_plane_builder;   -- ka_dasha_kala, ka_tulana, ka_graha_sancara, ka_muhurta_seva
-- inline call in ph_nimitta's INSERT and in the BEFORE INSERT trigger
GRANT EXECUTE ON FUNCTION public.phala_anchor_identity(uuid,text,text,text,text,text,date,date,date,text) TO data_plane_builder;
GRANT EXECUTE ON FUNCTION public.phala_anchor_identity_namespace() TO data_plane_builder;
```

Explicitly NOT granted: any sequence privilege (none exist on the ten); TRUNCATE, TRIGGER, REFERENCES; UPDATE on the other eight phala/mimamsa tables; `WITH GRANT OPTION`; `phala_rectification`, `phala_rectification_best` (1073 HOLD); every other `mimamsa_*` table; the gochara-kernel family and `bg_transit_av_gates` (section 3.2); EXECUTE on `phala_anchors_set_identity()` (a trigger function is not ACL-checked at fire time, code-derived); table-level SELECT on `life_events`; any other `asset_registry` column; any role membership; any default privilege.

### Part C. Executor, hash, approval (D6 in-process pattern), ordering

- **Executor:** the holder of the Cloud SQL administrator secret `cloudsql-postgres-admin-password` through the local proxy on `127.0.0.1:5433` (in D6 and the cutover: the native). No swarm lane has that secret.
- **One transaction, one script** (draft `/Users/Dev/suvarna-evidence/Grants/builder_grants_v1_1_DRAFT.py`, Appendix A; not in the repo): password fetched in-process, never printed; `SET LOCAL search_path = pg_catalog, pg_temp`; `SET LOCAL lock_timeout = '5s'`; in-transaction run guard (refuse unless `build_runs` has no `planned/running/paused` row); before snapshot of relation, column, function and sequence ACLs, **all `public` constraints**, non-internal triggers and role memberships; `GRANT data_plane_l2_owner TO postgres` and `GRANT amjis_app TO postgres` each only if `pg_has_role` says missing (precedent: `data-plane-ownership-preflight.ts:278`, reversed at `:358`); Part A as `data_plane_l2_owner`, Part B as `amjis_app`, `RESET ROLE` between; remove the transient memberships; after snapshot. **Commit only if** the ACL diff is exactly the 42 planned entries (nothing removed), the constraint diff is exactly the three planned rows (nothing added), non-internal triggers and memberships are unchanged, and `--expect-plan` equals the hash. `--dry-run` rolls back. `--rollback` has its own hash.
- **Consolidated plan hash (sha256 of plan text + expected ACL diff + expected constraint diff + mode, recomputed with a stubbed-driver import, no DB access):** apply `2b4793057bbe5978b7ba5b5a46b05d6dd8f5190609166306e045b7a043c1856a`, rollback `beb76d4ed09a8566b2be676a1dd1e8d98308544821d6403b00a8714d5360475b`. They change if any statement changes. The executor uses the hash printed by the dry run of the approved script; SS's `APPROVED <plan hash>` must quote that value.
- **Ordering:** (1) gate amendment: none needed (sections 2, 2.1, 2.2); (2) Part A; (3) Part B; both in the one transaction, so there is no half-applied state. Relative to other work: Pravāha's audit grant any order (Part G); migration 1214 any order but the MSR-first invariant holds until both are deployed; Part B before S4 on any re-run (section 0 item 5) and before S5/S6.
- **Alternative (not recommended):** an ordinary migration as `amjis_app` handles Part B only (1070/1073 precedent); Part A cannot be a migration because the runner (`amjis_app`) cannot drop the L2-owned keys (F-3 section 2: `InsufficientPrivilege`), which is why SS ruled the owner-path.

### Part D. Pre-checks (read-only; immediately before the dry run and again before apply)

1. **Deploy idle.** No `deploy.yml` run in progress for `main` and none queued (`gh run list --workflow deploy.yml --limit 5`); D6's standing rule "never during a deploy or migration". (A catalog change is instantaneous and not gate-pinned, so this is a rule, not a technical need.)
2. **No in-flight build:** `SELECT id, state FROM build_runs WHERE state IN ('planned','running','paused')` returns 0 rows (observed 0 at 16:20Z). The script enforces this itself.
3. **No MSR writer or long reader active** on `bodha_msr_signals`, `bodha_contradictions`, `bodha_signal_embeddings` (Part A's 5 s lock fails loudly otherwise; run again later).
4. **Migration 1214 status recorded:** `SELECT filename FROM _migrations_applied WHERE filename LIKE '1214%'` (observed: no row; max id 904). Record the answer in the run record; it fixes the expected post-state of V10 (5 kala keys remain if 1214 is not applied; 0 if it is).
5. **Baselines captured:** V1-V18 (files `verify.sql`, `verify_v11_extra.sql`; pre-state in `verify_before.txt`, `verify_v11_before.txt`); the V7 md5 and V11 md5 change with other workstreams, so re-capture within minutes of the apply. Baselines at 16:20Z: V7 `a15ebe2724202646dc9570e21c374bca`; V11 `e0b1296a26f56d24178cf626faffb696` over 1,553 constraints.
6. **Owner and shape re-check:** the ten tables, `life_events`, `bg_combustion_orbs`, `brahma_activity_ontology`, `asset_registry` owned by `amjis_app`; the three keys by tables owned by `data_plane_l2_owner`; if any owner differs, STOP.
7. **Gate baseline:** `data-plane-ownership-status.ts` under the reader prints `marked` (command in the D6 runbook, `D6_SUVARNA_READER_RUNBOOK_v1_0.md:314`).
8. **Orphan check for the rollback path** (V17; the executor also runs the `bodha_contradictions` form): 0 orphans.

### Part E. Verification SQL (read-only; run before and after)

V1-V8 are as in v1.0 (`verify.sql`): V1 the 11-row table matrix (`as_planned` all true after; today all false), V2 `life_events` five columns and no table-level SELECT, V3 the two functions true and the trigger function false, V4 holds false, V5 no owned sequences, V6 no RLS, V7 md5 of every ACL entry not held by the builder (equal before and after), V8 builder memberships 0. Added in v1.1 (`verify_v11_extra.sql`, run read-only now; pre-state in `verify_v11_before.txt`):

```sql
-- V9 the three keys: today 3 rows; after Part A: 0 rows
SELECT conrelid::regclass::text tbl, conname, convalidated, pg_get_constraintdef(oid) def FROM pg_constraint
 WHERE conname IN ('bodha_contradictions_signal_a_id_fkey','bodha_contradictions_signal_b_id_fkey','bodha_signal_embeddings_signal_id_fkey');
-- V10 FKs into bodha_msr_signals: today 8 (5 kala); after Part A: 5 (all kala) if 1214 not applied, 0 if applied
SELECT count(*) AS fks_into_msr, count(*) FILTER (WHERE conrelid::regclass::text LIKE 'kala\_%') AS kala_fks FROM pg_constraint
 WHERE contype='f' AND confrelid='public.bodha_msr_signals'::regclass;
-- V11 every other constraint untouched: md5 over all public constraints except the three (equal before and after)
SELECT md5(string_agg(k.conrelid::regclass::text||'|'||k.conname||'|'||pg_get_constraintdef(k.oid), E'\n' ORDER BY k.conrelid::regclass::text, k.conname)), count(*)
FROM pg_constraint k JOIN pg_class c ON c.oid=k.conrelid
WHERE c.relnamespace='public'::regnamespace AND k.conname NOT IN ('bodha_contradictions_signal_a_id_fkey','bodha_contradictions_signal_b_id_fkey','bodha_signal_embeddings_signal_id_fkey');
-- V12 internal RI triggers: today bodha_contradictions 4, bodha_signal_embeddings 2, bodha_msr_signals 16; after Part A: 0, 0, 10 (after 1214 too: 0)
SELECT c.relname, count(*) FROM pg_trigger t JOIN pg_class c ON c.oid=t.tgrelid WHERE t.tgisinternal AND c.relname IN ('bodha_contradictions','bodha_signal_embeddings','bodha_msr_signals') GROUP BY 1;
-- V13 non-internal triggers on the three tables: the same 6 rows before and after
-- V14 asset_registry builder UPDATE columns: today 3 (service_health, last_invoked_at, last_selftest_at); after: those 3 + selftest_detail; table-level UPDATE false
-- V15 bg_combustion_orbs: SELECT true, INSERT/UPDATE/DELETE false
-- V16 holds false: phala_rectification, kala_gochara_{contacts,coverage,publication,convention}, bg_transit_av_gates
-- V17 orphan_embeddings = 0 (rollback precondition)
```

(The full text of V13-V17 is in `verify_v11_extra.sql`.) Post-apply expectations also include: **V18 (gate)**: `data-plane-ownership-status.ts` under the reader prints `marked` (if it prints a drift error instead: roll back and re-read section 2.1/2.2). The total public constraint count goes from 1,556 to 1,553; V11's md5 over the other 1,553 constraints is identical.

What the grant and the drop cannot prove: that the job connects as `data_plane_builder` (the smoke build, rebuild plan P0.4, covers it), that EXECUTE on the two functions suffices (the first `ph_nimitta` run), and that the writers then complete. A privilege error in `build_run_assets.error` is a clean failure with no data change. The `ph_muhurta` and `ka_vighnakara` outputs must be compared against their pre-rebuild digests to surface any silent fallback.

### Part F. Rollback (script `--rollback --expect-plan <rollback hash>`; same discipline, inverse order)

```sql
-- as amjis_app (the grantor of record; a REVOKE by postgres without the membership has no effect)
REVOKE SELECT, INSERT, DELETE         ON TABLE public.phala_anchors, public.phala_muhurta, public.phala_mitigation,
       public.phala_sankrama, public.phala_sodhana, public.phala_pramana, public.mimamsa_predictions,
       public.mimamsa_manifestation_sets FROM data_plane_builder;
REVOKE SELECT, INSERT, UPDATE, DELETE ON TABLE public.phala_suddha_sodhana, public.phala_phaladesa FROM data_plane_builder;
REVOKE SELECT ON TABLE public.brahma_activity_ontology, public.bg_combustion_orbs FROM data_plane_builder;
REVOKE SELECT (id, event_date, category, description, outcome_observed) ON TABLE public.life_events FROM data_plane_builder;
REVOKE UPDATE (selftest_detail) ON TABLE public.asset_registry FROM data_plane_builder;
REVOKE EXECUTE ON FUNCTION public.phala_anchor_identity(uuid,text,text,text,text,text,date,date,date,text) FROM data_plane_builder;
REVOKE EXECUTE ON FUNCTION public.phala_anchor_identity_namespace() FROM data_plane_builder;
-- as data_plane_l2_owner: re-add the exact keys (text read from pg_get_constraintdef 2026-10-01; section 1.3)
ALTER TABLE public.bodha_contradictions    ADD CONSTRAINT bodha_contradictions_signal_a_id_fkey
  FOREIGN KEY (signal_a_id) REFERENCES public.bodha_msr_signals(signal_id) ON DELETE CASCADE;
ALTER TABLE public.bodha_contradictions    ADD CONSTRAINT bodha_contradictions_signal_b_id_fkey
  FOREIGN KEY (signal_b_id) REFERENCES public.bodha_msr_signals(signal_id) ON DELETE CASCADE;
ALTER TABLE public.bodha_signal_embeddings ADD CONSTRAINT bodha_signal_embeddings_signal_id_fkey
  FOREIGN KEY (signal_id) REFERENCES public.bodha_msr_signals(signal_id) ON DELETE CASCADE;
```

The re-added keys are validated, `ON UPDATE NO ACTION`, `MATCH SIMPLE`, not deferrable, which is the exact current definition; they get new internal RI triggers and a new constraint OID, so V12/V9 match by name and definition, not OID. A re-add scans every row (about 150,724 for embeddings) under a lock for the scan time; it is bounded by `lock_timeout` for acquisition, not for the scan. **The FK half of the rollback is valid only while no orphan exists**: if an MSR delete has run after the drop without the writers' explicit child deletes, `ADD CONSTRAINT` fails on validation (the script refuses first). In that case the child rows must be cleaned by the L2 owners before re-adding. The grant half is always safe with no in-flight run (otherwise that run fails loudly at its next statement). No data is touched by either part.

### Part G. Interaction with other work

- **Pravāha's `asset_throughput_state_audit` grant:** independent objects; no duplication; either order. The wave needs it for the smoke and every stage; S5/S6 and the Kāla stages that use Part B need both.
- **Migration 1214 (F-3 branch, five `amjis_app` kala keys):** independent of Part A; either order. Part A is the half of F-3 that only an owner-path can do (F-3 sections 1 and 5); the MSR-first rebuild-order invariant lasts until both are deployed.
- **`assert_l2_msr_delete_safe`:** untouched (SS declined to remove the re-arm). After 1214 and Part A it has no cross-layer key to refuse on; it re-arms if one is ever re-added.
- **Rebuild plan:** P0.5 check 2 should list the additions of v1.1 (`selftest_detail`, `bg_combustion_orbs`, `life_events`, `brahma_activity_ontology`, EXECUTE on `phala_anchor_identity*`) and S4's dependency on `phala_anchors` SELECT.

### Part H. Deploy-gate amendment

None required (sections 2, 2.1, 2.2). Nothing to land first.

## 5. Risks

1. **Part A removes a database-enforced referential guarantee between three L2 tables and the MSR.** Today a stale embedding or contradiction cannot outlive its signal; afterwards only the writers' explicit deletes (`_idempotency.py:120,123,196,201`) and the F-3 detector (`msr_dangling_signal_refs.py`, tier `l2_internal`, post-wave) provide that. A writer bug, or a manual MSR delete outside the writers, would leave orphan embeddings/contradictions silently. SS accepted this in the F-3 decisions; the plan keeps the detector as the post-wave check.
2. **Part A locks.** ACCESS EXCLUSIVE on `bodha_contradictions` and `bodha_signal_embeddings` and a lock on `bodha_msr_signals` for the DDL; `lock_timeout 5s`; sub-second once acquired. A concurrent MSR writer makes the run fail loudly and roll back everything (including Part B); retry when quiet.
3. **One transaction, two owners.** A failure in Part B rolls back Part A. That is the intended atomicity; the cost is that a Part B problem delays the FK drop.
4. **Blast radius on `mimamsa_predictions`.** DELETE is table-level; the "only `pending`/`due`" restriction lives in `mi_bhavisya.py:230`, not in the database (RLS off, no trigger). Today 195 rows, all pending, no outcome-bearing row, so nothing irreplaceable exists to lose now.
5. **Builder credential isolation.** The grants widen what the builder credential can do inside the DB but change no IAM binding, secret, service account or Cloud Run surface, so they can neither cause nor cure the "Builder credential is mounted outside the one named build job" failure (`data-plane-secret-isolation-preflight.ts:477,481`).
6. **Personal data.** `life_events` (the native's life-event log, 63 rows): column-level SELECT on five columns; `chart_state`, `provenance`, `significance`, `source_citation` and the consent/pool columns withheld (V2).
7. **Silent degradation and its detectors.** `ph_muhurta` (`brahma_activity_ontology`) and `ka_vighnakara` (`bg_combustion_orbs`) swallow a read failure; the grants remove the cause, and the pre/post output-digest comparison is the detector.
8. **`selftest_detail` is a cockpit-visible JSON field**; granting UPDATE lets the builder identity write arbitrary text into four services' self-test blobs. Column-level, no other `asset_registry` column; the same writers wrote it as the app login before the 2026-09-18 cutover (inferred from the cutover history, not re-verified).
9. **Latent RLS** on `mimamsa_predictions` (two inert policies that exclude the builder): if RLS were enabled, `mi_bhavisya` would fail on INSERT. No policy is added.
10. **The trigger-function assumption** (not ACL-checked at fire time) fails closed: a missing EXECUTE shows as `permission denied for function phala_anchors_set_identity` on the first `ph_nimitta` run, no data change.
11. **Transient membership.** `postgres` is briefly a member of `data_plane_l2_owner` (a protected owner role) and `amjis_app` inside the transaction; uncommitted, never visible to the gate, same as D6.
12. **Static-scan limits of the Kāla audit** (section 3.2): SQL built from variables could hide another read; the staged runs would reveal it as a clean permission error.

## 6. Questions for SS

- **Q1 (carried).** Confirm the contract reading: all grant objects are `amjis_app`-owned and outside the protected set; the three keys' tables are `data_plane_l2_owner`-owned, but no pin covers them (2.1).
- **Q2 (carried).** `phala_rectification(_best)` stay ungranted (1073 HOLD; `ka_kshetra` is outside the 26-asset plan).
- **Q3 (carried).** Keep `mi_abhilekha` and the other 26 `mimamsa_*` tables out?
- **Q4 (carried).** Table-level UPDATE on `phala_suddha_sodhana` and `phala_phaladesa` (recommended) versus column-level.
- **Q5 (carried).** Follow-up owner-side guard so a builder compromise cannot delete outcome-bearing `mimamsa_predictions` rows?
- **Q6.** Who runs the apply, and may `APPROVED <hash>` quote the hash printed by the executor's dry run of the approved script (the number here is a draft)?
- **Q7 (carried).** Include the `life_events` and `brahma_activity_ontology` reads here (recommended)?
- **Q8.** Add `bg_combustion_orbs` SELECT (recommended: it removes a silent fallback) or leave `ka_vighnakara` on its constants, which equal the table today?
- **Q9.** The gochara-kernel tables (`kala_gochara_contacts`, `_coverage`, `_publication`, `_convention`, `bg_transit_av_gates`) have no builder privilege: hand to Pravāha as their gochara-cutover grants, or fold into this review?
- **Q10.** Are `ka_tulana`, `ka_graha_sancara`, `ka_dasha_kala` ever dispatched through the builder in this campaign? If not, `selftest_detail` still has to be granted for `ka_muhurta_seva`, but the rest need no further action.

## Notes for SS to relay

- To Pravāha: the line "Exec Suvarṇa is handling the phala_*/mimamsa_* grants; your audit-table grant stays yours" was already relayed. Add: "the gochara-kernel tables `kala_gochara_contacts/_coverage/_publication/_convention`, `kala_gochara_cutover_step05_snapshot` and `bg_transit_av_gates` have no `data_plane_builder` privilege; they are yours (not in the Exec Suvarṇa grant plan) unless SS folds them in (Q9)."
- To the rebuild plan owner: P0.2 and P0.5 check 2 should list `asset_registry.selftest_detail`, `life_events`, `brahma_activity_ontology`, `bg_combustion_orbs` and EXECUTE on `phala_anchor_identity*` alongside the ten tables; stage S4 needs `phala_anchors` SELECT on any re-run; keep the output-digest comparison for `ph_muhurta` and `ka_vighnakara`.
- To F-3: the owner-path half is now in `BUILDER_GRANT_PLAN` v1.1 Part A, with the exact rollback text; no gate amendment.

## Appendix A. Draft script (not applied; not in the repo)

Saved as `/Users/Dev/suvarna-evidence/Grants/builder_grants_v1_1_DRAFT.py` (about 240 lines; one transaction per run; never prints a traceback or the secret). The plan, expected diffs and hashes are pure functions (`plan_text`, `expected_acl_diff`, `expected_con_diff`, `plan_hash`) that need no database. Key excerpts:

```python
GRANTEE, L2_OWNER, APP_OWNER = "data_plane_builder", "data_plane_l2_owner", "amjis_app"
FKS = [("bodha_contradictions", "bodha_contradictions_signal_a_id_fkey",
        "FOREIGN KEY (signal_a_id) REFERENCES public.bodha_msr_signals(signal_id) ON DELETE CASCADE"), ... b ..., 
       ("bodha_signal_embeddings", "bodha_signal_embeddings_signal_id_fkey",
        "FOREIGN KEY (signal_id) REFERENCES public.bodha_msr_signals(signal_id) ON DELETE CASCADE")]
TABLES = [...10 phala/mimamsa tables..., ("brahma_activity_ontology", ["SELECT"]), ("bg_combustion_orbs", ["SELECT"])]
COLUMNS = [("life_events", ["id","event_date","category","description","outcome_observed"], "SELECT"),
           ("asset_registry", ["selftest_detail"], "UPDATE")]
FUNCTIONS = ["phala_anchor_identity(uuid,text,text,text,text,text,date,date,date,text)", "phala_anchor_identity_namespace()"]
# apply: SET LOCAL search_path/lock_timeout; refuse if active build runs; snapshot (ACLs + public constraints + non-internal
# triggers + memberships); add transient memberships if missing; Part A as data_plane_l2_owner; Part B as amjis_app;
# remove memberships; snapshot; commit only if acl_added == expected_acl_diff() and nothing removed, con_removed ==
# expected_con_diff() and nothing added, triggers and memberships unchanged, and --expect-plan == plan_hash("apply").
# rollback: REVOKEs as amjis_app, orphan guard, then re-add the three keys as data_plane_l2_owner; inverse diff check.
```

## Appendix B. Evidence index

| Item | Where |
|---|---|
| Table owners, ACLs, RLS, policies, triggers, FKs, functions, default ACLs, sequences | read-only catalog queries, summarised in section 1 |
| Builder privilege matrix and V1-V8 baseline and re-check | `/Users/Dev/suvarna-evidence/Grants/verify_before.txt`, `verify_v11_recheck.txt`; queries in `verify.sql` |
| V9-V17 baseline (FKs, constraints md5, RI triggers, asset_registry columns, holds) | `verify_v11_before.txt`; queries in `verify_v11_extra.sql` |
| Kāla audit scan and matrix | `/private/tmp/claude-504/g/kala_scan.txt`, `kala_scan2.txt`, `kala_priv.sql` (session scratch; the result is summarised in section 3.2) |
| Gate pins | `platform/scripts/data-plane-ownership-status.ts` (577 lines), `data-plane-ownership-preflight.ts:9-68,278,321-358`, `.github/workflows/deploy.yml:509-574,686-708`, `data-plane-secret-isolation-preflight.ts:477,481` |
| F-3 owner-path source | `/Users/Dev/suvarna-lane-f3/00_ARCHITECTURE/briefs/suvarna/exec/F3_MSR_FK_DROP_v1_0.md` sections 1, 2, 5 and the SS decisions |
| Precedents | migrations `1070`, `1073`, `404_bodha_signal_fk_cascade.sql`, `reader_grants.py`, `D6_SUVARNA_READER_RUNBOOK_v1_0.md` |
| Progress log | `/Users/Dev/suvarna-evidence/Grants/progress.md` |
