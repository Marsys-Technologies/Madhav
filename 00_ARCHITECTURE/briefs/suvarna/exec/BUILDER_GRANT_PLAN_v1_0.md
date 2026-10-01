---
artifact: BUILDER_GRANT_PLAN
version: "1.0"
status: DRAFT-FOR-REVIEW
produced_by: exec-suvarna
date: 2026-10-01
base_commit: origin/main 3311b0a06b424bef1e48c026408321fb59a88eed
related: CANONICAL_CHART_REBUILD_PLAN_v1_0.md (P0.2, P0.5 check 2, S5/S6), reader_grants.py (D6 pattern, branch suvarna/exec), migrations 1070 and 1073
execution: NONE. Analysis only. No grant, admin action, DB write, push, PR, migration or workflow change was made. The SQL and the script below are drafts inside this document.
db_access: read-only, as suvarna_reader (SELECT, has_*_privilege, catalog reads). Evidence and queries in /Users/Dev/suvarna-evidence/Grants/ (verify.sql, verify_before.txt, builder_grants_DRAFT.py, progress.md).
changelog:
  - "1.0 (2026-10-01): first draft for SS review. Covers the second grant gap only (phala_* and mimamsa_* target tables for data_plane_builder). The asset_throughput_state_audit grant is Pravaha's and is NOT covered here."
---

# Builder grant plan: phala_* and mimamsa_* (REVIEW document for SS)

Scope asked by SS: the role `data_plane_builder` (the identity of `brahma-build-pipeline-job`) has no privilege on the `phala_*` target tables of the `ph_*` assets, nor on `mimamsa_predictions` and `mimamsa_manifestation_sets`, so stages S5 and S6 of the canonical-chart rebuild cannot write. SS ruled the fix is ours. This document establishes the facts read-only, answers the deploy-gate question, derives the least-privilege grant from the writer code, and proposes who runs it and how it is verified and rolled back.

Evidence labels used throughout: **observed** (read live as `suvarna_reader`, 2026-10-01 about 15:17 to 15:45Z), **repo** (file:line at the base commit), **code-derived** (follows from code or PostgreSQL semantics, never observed in production), **not visible** (the reader cannot see it).

## 0. What SS needs to see first

1. **The gap is wider than the ten tables.** Three things beyond the ten target tables block or silently degrade S5/S6 for the same reason (a role with no inherited rights, and objects created by `amjis_app` whose default function ACL excludes PUBLIC):
   - `phala_anchor_identity(...)` and `phala_anchor_identity_namespace()` have EXECUTE for `amjis_app` only (observed). `ph_nimitta`'s INSERT calls `phala_anchor_identity` inline (`ph_nimitta.py:243`) and the BEFORE INSERT trigger calls it again. Without EXECUTE, `ph_nimitta` fails with `permission denied for function`, even once INSERT on `phala_anchors` is granted (code-derived).
   - `ph_pramana` reads `life_events` (`ph_pramana.py:190`), which the builder cannot read. The handler catches only `UndefinedTable` (`:212`), so `InsufficientPrivilege` propagates and the asset fails loudly (code-derived).
   - `ph_muhurta` reads `brahma_activity_ontology` (`ph_muhurta.py:503`) inside `except Exception` that logs at debug and returns `{}` (`:510-518`). Without SELECT the asset would COMPLETE with silently degraded output (code-derived). This is the dangerous one: it would not show as a failure.
2. **Not covered by the deploy gate. No gate amendment is needed.** None of these objects is in `L1_ACTIVE_TABLES`, `L2_ACTIVE_TABLES`, the history lists or the attested function set that `data-plane-ownership-status.ts` pins (section 2). The plan therefore has no "PR before the grant" part; Part G is deliberately empty.
3. **Ownership is not the protected-owner contract.** All ten tables, the two read tables and the two functions are owned by `amjis_app` (observed), not by `data_plane_*_owner`. They are not protected tables. The standing rule "never touch protected tables" is not engaged. The repo's own precedent for granting the builder on `amjis_app`-owned tables is migrations 1070 and 1073, both applied as routine migrations.
4. **No sequence privilege is needed.** None of the ten tables owns a sequence, identity or `nextval` default (observed).
5. **Two items are deliberately NOT granted:** `phala_rectification` and `phala_rectification_best` (the 1073 HOLD; `ph_rectification` is not in S5), and any `mimamsa_*` table other than the two `mi_bhavisya` writes (Q2, Q3).
6. **Recommended executor:** the holder of the Secret Manager administrator secret, which in D6 was the native, using the D6 in-process pattern (Part B). Not any swarm lane.

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

**Conclusion: a GRANT to `data_plane_builder` on these objects will not make any deploy-time ownership or isolation check fail.** To prove it rather than assert it, the post-apply verification runs the real gate under the reader (D6 runbook `§3`, the `data-plane-ownership-status.ts` command at `D6_SUVARNA_READER_RUNBOOK_v1_0.md:314`) and expects `marked`; the same check is the dry-run's last step (V9 below). If a future decision puts these tables under protection, `L1_ACTIVE_TABLES`/`L2_ACTIVE_TABLES` would have to change first; that is out of scope.

Is the grant permitted by the data-plane ownership contract? Yes. `MADHAV_DATA_PLANE_RI02_SECURITY_CUTOVER_v1_0.md:98-99` gives the builder "exact producer DML ... no schema create, owner membership, TRUNCATE, TRIGGER, REFERENCES", and the protected-object map covers L1 and L2 only. Grants to the builder on tables owned by `data_plane_l2_owner`/`data_plane_schema_owner` would be a different question; none of our objects is one.

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

## 4. The plan

### Part A. Proposed GRANT statements (least privilege)

Grantee `data_plane_builder`; every statement is issued by the owner `amjis_app` (Part B), so the ACL entry reads `data_plane_builder=.../amjis_app` like the existing builder grants.

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
-- reads the S5 writers need (without them: ph_pramana fails loudly, ph_muhurta degrades silently)
GRANT SELECT ON TABLE public.brahma_activity_ontology TO data_plane_builder;
GRANT SELECT (id, event_date, category, description, outcome_observed) ON TABLE public.life_events TO data_plane_builder;
-- inline call in ph_nimitta's INSERT (and the BEFORE INSERT trigger)
GRANT EXECUTE ON FUNCTION public.phala_anchor_identity(uuid,text,text,text,text,text,date,date,date,text) TO data_plane_builder;
GRANT EXECUTE ON FUNCTION public.phala_anchor_identity_namespace() TO data_plane_builder;
```

Explicitly NOT granted: any sequence privilege (none exist); TRUNCATE, TRIGGER, REFERENCES; UPDATE on the other eight; `WITH GRANT OPTION`; `phala_rectification`, `phala_rectification_best` (the 1073 HOLD; `data_plane_builder_l3_reference_read_grants.test.ts:28-30`); every other `mimamsa_*` table; EXECUTE on `phala_anchors_set_identity()` (a trigger function is not ACL-checked at fire time, code-derived); table-level SELECT on `life_events`; any role membership; any default privilege.

### Part B. Who executes, and how (the D6 in-process pattern)

- **Executor:** the holder of the Cloud SQL administrator secret `cloudsql-postgres-admin-password` (Secret Manager) through the local proxy on `127.0.0.1:5433`, which in D6 and the cutover was the native. No swarm lane has that secret. This is a physical act under the charter (the native's acts include credential handling); SS decides whom to ask.
- **Tool:** a new script modelled on `reader_grants.py` (the applied D6 tool, same directory family on branch `suvarna/exec`). Draft in Appendix A (also saved as `/Users/Dev/suvarna-evidence/Grants/builder_grants_DRAFT.py`; it is not placed in the repo and not authored for application). Reused unchanged from `reader_grants.py`: secret fetched in-process and never printed; `SET LOCAL search_path = pg_catalog, pg_temp`; `GRANT amjis_app TO postgres` only if `pg_has_role` says it is missing, `SET LOCAL ROLE amjis_app`, grants, `RESET ROLE`, `REVOKE amjis_app FROM postgres`, all in one transaction; before/after ACL snapshot; commit only if the ACL diff is exactly the planned one and role memberships are unchanged; `--dry-run` rolls back; `--apply --expect-plan H` refuses unless H equals the plan hash. Changes versus `reader_grants.py`: the grant list covers table, column and function privileges; the snapshot adds column ACL (`pg_attribute.attacl`), function ACL and sequence ACL (a sequence ACL change would be an unplanned diff and abort); `lock_timeout = 5s`; a `--rollback` mode with its own hash.
- **Draft plan hash** (sha256 of the plan text, the expected-diff JSON and the mode; recomputed with the stubbed-driver import, no DB access): apply `1c5722a2dee4df3803f18bbf896458246f0b936d1da09f606216a030bf0a6640`, rollback `f31a652a75a5b765851bd5c5007d6e4f34405483435b34096d83951ed1447fd0`. They change if any statement changes; the executor must use the hash printed by the dry-run of the approved script, not this number.
- **Approval:** REVIEW document (this) approved by SS, then dry-run output reviewed (the plan hash and `diff exactly as planned: True`), then `--apply --expect-plan <hash from the dry run>`.
- **Alternative (not recommended, for completeness):** an ordinary migration run by the deploy pipeline as `amjis_app`, as 1070 and 1073 were (`GRANT` on tables `amjis_app` owns; no bootstrap). It is the repo's precedent and needs no admin secret, but it ships the grants through every deploy path (not an explicit approval-by-hash step), the reserved number range 1070-1119 belongs to L3 Kāla (DP-SD-021, migration 1073 header), and SS's ruling asks for the D6 pattern. If SS prefers it, the statements in Part A are the migration body and the V1-V8 checks become its `DO $$` self-assertion, as 1073 did.

### Part C. Pre-checks (all read-only, immediately before the dry run and again before apply)

1. **Deploy idle.** No `deploy.yml` run in progress for `main` and no merge queue deploy pending (a GRANT is instantaneous, catalog-only, and the gate is not pinned to it, so this is the D6 runbook's standing "never during a deploy or migration" rule, not a technical need). Check with `gh run list --workflow deploy.yml --limit 5`.
2. **No in-flight build:** `SELECT id, state FROM build_runs WHERE state IN ('planned','running','paused');` returns no row (the same query as rebuild plan P0.3 check 3 but for all charts). A run mid-flight would simply see the privilege appear; the check keeps the evidence clean.
3. **Baseline captured:** `verify_before.txt` (V1-V8 below) re-run, including the V7 md5 of every other ACL entry (it changes with other workstreams' grants, so capture it within minutes of the apply).
4. **Gate baseline:** run `data-plane-ownership-status.ts` under the reader (command in section 2); it must print `marked` before and after.
5. **Owner and shape re-check:** `relowner` is `amjis_app` and `relrowsecurity` false for all ten (V6); if any owner differs, STOP (a protected-owner table would change the answer to Q1).

### Part D. Verification SQL (read-only; the file is `/Users/Dev/suvarna-evidence/Grants/verify.sql`; its pre-state output is `verify_before.txt`)

```sql
-- V1 table matrix: as_planned must be true for all 11 rows after the grant (today all false)
WITH x(t, es, ei, eu, ed) AS (VALUES
 ('phala_anchors',true,true,false,true),('phala_muhurta',true,true,false,true),('phala_mitigation',true,true,false,true),
 ('phala_sankrama',true,true,false,true),('phala_sodhana',true,true,false,true),('phala_suddha_sodhana',true,true,true,true),
 ('phala_pramana',true,true,false,true),('phala_phaladesa',true,true,true,true),
 ('mimamsa_predictions',true,true,false,true),('mimamsa_manifestation_sets',true,true,false,true),
 ('brahma_activity_ontology',true,false,false,false))
SELECT t,
  has_table_privilege('data_plane_builder','public.'||t,'SELECT') s, has_table_privilege('data_plane_builder','public.'||t,'INSERT') i,
  has_table_privilege('data_plane_builder','public.'||t,'UPDATE') u, has_table_privilege('data_plane_builder','public.'||t,'DELETE') d,
  (has_table_privilege('data_plane_builder','public.'||t,'SELECT')=es AND has_table_privilege('data_plane_builder','public.'||t,'INSERT')=ei
   AND has_table_privilege('data_plane_builder','public.'||t,'UPDATE')=eu AND has_table_privilege('data_plane_builder','public.'||t,'DELETE')=ed
   AND NOT has_table_privilege('data_plane_builder','public.'||t,'TRUNCATE,REFERENCES,TRIGGER')) AS as_planned
FROM x ORDER BY 1;
-- V2 life_events: exactly five columns readable, no table-level SELECT
SELECT a.attname, has_column_privilege('data_plane_builder','public.life_events',a.attname,'SELECT') col_select,
       a.attname = ANY(ARRAY['id','event_date','category','description','outcome_observed']) AS planned
FROM pg_attribute a WHERE a.attrelid='public.life_events'::regclass AND a.attnum>0 AND NOT a.attisdropped ORDER BY a.attnum;
SELECT has_table_privilege('data_plane_builder','public.life_events','SELECT') AS must_be_false;
-- V3 functions: the two inline-called ones true; the trigger function and phala_anchor_signal_provenance stay false
SELECT p.oid::regprocedure::text fn, has_function_privilege('data_plane_builder',p.oid,'EXECUTE') exec
FROM pg_proc p WHERE p.pronamespace='public'::regnamespace AND p.proname LIKE 'phala\_%' ORDER BY 1;
-- V4 holds stay false
SELECT t, has_table_privilege('data_plane_builder','public.'||t,'SELECT,INSERT,UPDATE,DELETE') AS must_be_false
FROM unnest(ARRAY['phala_rectification','phala_rectification_best','mimamsa_journal','mimamsa_calibration','mimamsa_load_bearing']) t;
-- V5 owned sequences of the ten tables: 0 (nothing to grant)      V6 relrowsecurity true rows: 0
-- V7 md5 of every ACL entry NOT held by data_plane_builder: equal before and after
-- V8 data_plane_builder role memberships: 0
-- (V5-V8 are in verify.sql)
```

Expected V3 after the grant: `phala_anchor_identity(...)` and `phala_anchor_identity_namespace()` true; `phala_anchors_set_identity()` and `phala_anchor_signal_provenance(uuid)` false; the three PUBLIC functions unchanged (true). Baseline V7 md5 at 15:45Z: `a15ebe2724202646dc9570e21c374bca`.

- **V9 (gate, the proof of section 2):** `data-plane-ownership-status.ts` under the reader prints `marked` after the apply. If it prints an error instead, ROLL BACK (Part E) and re-read section 2: the pin analysis was wrong.
- **V10 (what the grant cannot prove):** that the job connects as `data_plane_builder`, that EXECUTE on the two functions is sufficient, and that the writers then complete. The rebuild plan's smoke build (P0.4) covers the audit path on `ka_tithi_pravesha`; for these objects the first S5 asset (`ph_nimitta`, which uses the function path and writes `phala_anchors`) is the real test, and `ph_muhurta`'s output digest must be compared against the pre-rebuild digest to surface any silent `brahma_activity_ontology` degradation (it should not occur after the grant; the check is the detector). A privilege error in `build_run_assets.error` is a clean failure with no data change.

### Part E. Rollback

Script `--rollback --expect-plan <rollback hash>` (same transaction discipline, the diff must remove exactly the added entries). The statements:

```sql
-- issued as amjis_app (SET LOCAL ROLE), the grantor of record; a REVOKE by postgres without the membership has no effect
REVOKE SELECT, INSERT, DELETE         ON TABLE public.phala_anchors, public.phala_muhurta, public.phala_mitigation,
       public.phala_sankrama, public.phala_sodhana, public.phala_pramana, public.mimamsa_predictions,
       public.mimamsa_manifestation_sets FROM data_plane_builder;
REVOKE SELECT, INSERT, UPDATE, DELETE ON TABLE public.phala_suddha_sodhana, public.phala_phaladesa FROM data_plane_builder;
REVOKE SELECT ON TABLE public.brahma_activity_ontology FROM data_plane_builder;
REVOKE SELECT (id, event_date, category, description, outcome_observed) ON TABLE public.life_events FROM data_plane_builder;
REVOKE EXECUTE ON FUNCTION public.phala_anchor_identity(uuid,text,text,text,text,text,date,date,date,text) FROM data_plane_builder;
REVOKE EXECUTE ON FUNCTION public.phala_anchor_identity_namespace() FROM data_plane_builder;
```

Rollback restores the exact pre-state (`verify_before.txt` V1 all false). It is safe only with no in-flight build run (otherwise that run fails loudly at its next statement). No data is touched by the grant or the rollback.

### Part F. Interaction with Pravāha's audit-table grant

Independent objects: Pravāha's change concerns `asset_throughput_state_audit` INSERT and its sequence (and, if they choose, the trigger function's SECURITY DEFINER form). This plan touches none of those and Pravāha's touches none of ours; neither duplicates the other, and applying them in either order is harmless because both only add privileges to the builder. The dependency is on the **wave**, not between the two changes: the smoke build and stages S0-S4 need only Pravāha's grant; S5 and S6 need both (rebuild plan P0.5 check 1 and check 2). Recommended order for the wave: Pravāha's grant, our grant (any time before S5), smoke build, S0-S4, then S5-S6. One coordination point: if Pravāha ships the audit fix as a migration and our change is a D6 run, the D6 run must not overlap that migration's deploy (Part C item 1).

### Part G. Deploy-gate amendment

None required (section 2). Nothing to land before the grant.

## 5. Risks

1. **Blast radius on `mimamsa_predictions`.** DELETE is table-level; the "only `pending`/`due`" restriction lives in `mi_bhavisya.py:230`, not in the database (RLS is off, no trigger). Today there are 195 rows, all pending, none outcome-bearing, so nothing irreplaceable exists to lose now. Once outcome rows exist (written by `mi_abhilekha`), a builder-credential compromise or a writer bug could delete them. Mitigation inside this plan: no UPDATE, the credential is bound to one named job only (`data-plane-secret-isolation-preflight.ts:477,481`, tests `:236-241,301-305`), and the credential-isolation check is unchanged by this grant. A database-level guard (BEFORE DELETE trigger refusing non-pending rows) would be a separate owner-side change (Q5).
2. **Builder credential isolation.** The builder identity mounted outside the one named build job is what failed a deploy earlier (`:477`). This grant changes no IAM binding, secret, service account or Cloud Run surface, so it cannot cause or cure that failure; it only enlarges what that credential can do inside the DB (ten tables, one reference table, five `life_events` columns, two functions).
3. **Personal data.** `life_events` holds the native's life-event log (63 rows; narrative `description`, `outcome_observed`). Column-level SELECT limits it to the five columns `ph_pramana` reads and withholds `chart_state`, `provenance`, `significance`, `source_citation` and the consent and pool columns (V2).
4. **Silent degradation and its detector.** `ph_muhurta` swallows an ontology read failure at debug level (`ph_muhurta.py:510-518`). The grant removes the cause; the V10 digest comparison is the detector. Without it a green S5 could hide an empty significator map.
5. **Latent RLS.** `mimamsa_predictions` has two policies that exclude the builder. They are inert while `relrowsecurity` is false (V6). If RLS were enabled later, `mi_bhavisya` would fail on INSERT (loud) and DELETE/SELECT would silently see no rows. The plan adds no policy.
6. **The trigger-function assumption** (section 1.2) fails closed: a missing EXECUTE shows as `permission denied for function phala_anchors_set_identity` on the first `ph_nimitta` run, no data change, and the fix is one more owner GRANT through the same tool.
7. **Other workstreams.** No other role's ACL changes, no data changes, no deploy-gate input changes (section 2), no migration is authored or applied. The `phala_anchors` FKs cascade deletes to five dependent tables when `ph_nimitta` runs and `kala_convergence` deletes cascade into `phala_anchors`; that is existing behaviour governed by the rebuild plan's stage order, not by these grants.
8. **`amjis_app` credential rotation (WP2).** The apply uses the administrator login and transient membership, not the `amjis_app` password, so a rotation of that password neither blocks nor is affected by the grant.

## 6. Questions for SS

- **Q1.** Confirm the protected-contract reading: these objects are `amjis_app`-owned and outside the L1/L2 protected set, so D6-style owner-scoped grants are in scope and no gate amendment is needed.
- **Q2.** `phala_rectification` and `phala_rectification_best` stay ungranted (1073 HOLD, Strategy section 6.2; `ph_rectification` is not in S5). Confirm, or tell me to plan a separate decision (a grant would also let `ka_kshetra` read L4, which the hold forbids).
- **Q3.** Keep `mi_abhilekha` and the other 26 `mimamsa_*` tables out of this plan (S6 is only `mi_bhavisya`)? If the wave is extended to `mi_abhilekha`, I need to add `mimamsa_journal` (read), UPDATE of `mimamsa_predictions.lifecycle_status` (column-level) and likely `mimamsa_calibration`; that raises the blast radius in risk 1.
- **Q4.** Table-level UPDATE on `phala_suddha_sodhana` and `phala_phaladesa` (recommended) versus column-level UPDATE with the exact SET lists.
- **Q5.** Do you want a follow-up owner-side guard so a builder compromise cannot delete outcome-bearing `mimamsa_predictions` rows? It is a separate change and not required for this wave.
- **Q6.** Who runs the apply (holder of the administrator secret), and may the plan hash be taken from the executor's dry run of the approved script rather than from this draft?
- **Q7.** Include the `life_events` and `brahma_activity_ontology` reads in this grant (recommended; without them S5 fails or degrades), or have the owners of those tables decide separately?

## Notes for SS to relay

To Pravāha, one line: "Exec Suvarṇa is handling the phala_*/mimamsa_* grants; your audit-table grant stays yours."

Additional note for the rebuild plan (not for Pravāha): P0.2 and P0.5 check 2 should list `life_events`, `brahma_activity_ontology` and EXECUTE on `phala_anchor_identity*` alongside the ten tables, and the plan's `ph_nimitta` stage (S5) should keep the digest comparison for `ph_muhurta`.

## Appendix A. Draft script (not applied; not in the repo)

Saved as `/Users/Dev/suvarna-evidence/Grants/builder_grants_DRAFT.py`. Structure reused from `reader_grants.py`; the plan, the expected diff and the plan hash are computed by pure functions (`plan_text`, `expected_diff`, `plan_hash`) that need no database. Key excerpts:

```python
GRANTEE = "data_plane_builder"
OWNER = "amjis_app"
TABLES = [("phala_anchors", ["SELECT","INSERT","DELETE"]), ... ("phala_suddha_sodhana", ["SELECT","INSERT","UPDATE","DELETE"]),
          ("phala_phaladesa", ["SELECT","INSERT","UPDATE","DELETE"]), ("mimamsa_predictions", ["SELECT","INSERT","DELETE"]),
          ("mimamsa_manifestation_sets", ["SELECT","INSERT","DELETE"]), ("brahma_activity_ontology", ["SELECT"])]
COLUMNS = [("life_events", ["id","event_date","category","description","outcome_observed"], "SELECT")]
FUNCTIONS = ["phala_anchor_identity(uuid,text,text,text,text,text,date,date,date,text)", "phala_anchor_identity_namespace()"]
# transaction: SET LOCAL search_path = pg_catalog, pg_temp; SET LOCAL lock_timeout = '5s'; snapshot (relation, column,
# function, sequence ACL + memberships); GRANT amjis_app TO postgres only if missing; SET LOCAL ROLE amjis_app; statements;
# RESET ROLE; REVOKE amjis_app FROM postgres; snapshot; commit only if added == expected_diff(), nothing removed,
# memberships unchanged, and (apply) --expect-plan == plan_hash("apply").
```

The full file (about 150 lines, one transaction per run, never prints a traceback or the secret) is in the evidence directory for review.

## Appendix B. Evidence index

| Item | Where |
|---|---|
| Table owners, ACLs, RLS, policies, triggers, FKs, functions, default ACLs, sequences | read-only catalog queries 2026-10-01 15:17-15:45Z, summarised in section 1 |
| Builder privilege matrix and V1-V8 baseline | `/Users/Dev/suvarna-evidence/Grants/verify_before.txt`; queries in `verify.sql` |
| Upstream read audit | section 3 last bullet (`has_table_privilege` per table) |
| Gate pins | `platform/scripts/data-plane-ownership-status.ts` (577 lines), `data-plane-ownership-preflight.ts:9-68,278,321-358`, `.github/workflows/deploy.yml:509-574,686-708`, `data-plane-secret-isolation-preflight.ts:477,481` |
| Precedents | migrations `1070_data_plane_builder_orchestrator_grants.sql`, `1073_data_plane_builder_l3_reference_read_grants.sql` (applied 2026-09-20, 2026-09-29), `reader_grants.py`, `D6_SUVARNA_READER_RUNBOOK_v1_0.md` |
| Progress log | `/Users/Dev/suvarna-evidence/Grants/progress.md` |
