---
artifact: DP_BUILDER_PRIVILEGES_PLAN
version: "1.0-DRAFT"
status: HELD_DRAFT (nothing executed against any real system; waits for Strategic Suvarna's dry-run approval and the owner's authorisation sentence in section 1)
date: 2026-10-03
lane: suvarna/land/TI-dp-builder-privileges-1272-1273-001
migration_numbers: [1272, 1273]   # allocated by the coordinator; the SQL files carry the numbers as history text only and are NEVER run by migrate.ts
decision: coordinator allocation of 1272 (B3) and 1273 (B4) after the production-mirrored real-PG rehearsal found both blockers
execution: NONE against any real system. Production was read only as suvarna_reader (function text, md5, ACL, attestation digests). Every test ran on a disposable PostgreSQL 15 with production's roles, owners and ACLs and a NON-superuser CREATEROLE administrator.
frozen_by: not frozen. The plan hash below is the hash of the plan as of executor sha256 6588ae18...; any change to the executor, the gate files or the bound constants changes it.
changelog:
  - "1.0-DRAFT (2026-10-03): first draft. Two items (B3 shadow read grant inside bind_l2_exact_inputs; B4 EXECUTE on the eight bodha_*_identity functions), one transaction, gated by GATE_V2 revision 3."
---

# Owner-path plan: the pipeline login can read what the L2 wrapper binds, and can compute Bodha identities (migration numbers 1272 and 1273)

## 0. One-page summary for the owner (plain language)

**What and why.** When a Bodha (L2) writer runs, the shared wrapper first asks the database to "bind" the exact inputs the build will read. The database function that does this (`bind_l2_exact_inputs`) creates short-lived private copies of the protected tables for that one transaction. Those copies are owned by the function's owner and carry no permissions, so the pipeline's own login (`data_plane_builder`) is refused when it tries to read them: `permission denied`. Separately, every Bodha asset computes stable row identities through eight small database functions (`bodha_signal_identity`, `bodha_cgm_node_identity`, `bodha_cgm_edge_identity`, `bodha_contradiction_identity` and their four namespace helpers); the pipeline login has no right to run them. Without both fixes, every `bo_*` asset fails at its first read or its first identity computation, on any chart. This plan gives the pipeline login exactly those two rights and nothing else.

**The two items**

1. **B3 (1272): the bind function grants read access on its own short-lived copies to the pipeline login.** *What it changes:* one stored procedure, `bind_l2_exact_inputs(uuid, jsonb)`, is replaced by a copy that differs from the live one by exactly ONE inserted block of twelve lines: before it writes its receipt, it grants SELECT on each temporary copy it created, to `data_plane_builder` only, and never on the bind receipt. The temporary copies exist only inside the building transaction and vanish at its end; no other session can see them. Its seal record (the digest the deploy gate compares) is updated to match. *Serving effect:* none directly (no served surface reads these copies); the L2 builder can read its own bound inputs.
2. **B4 (1273): EXECUTE on the eight identity functions.** *What it changes:* eight `GRANT EXECUTE ... TO data_plane_builder`, issued as `amjis_app` (their owner). *Serving effect:* none. The functions are pure computations of a stable id from values the caller already holds.

**What changes in the production database.** One stored procedure replaced by an edited copy; one seal record updated to match; eight function permissions each gaining exactly `data_plane_builder`. **Transient permissions, part of the plan:** for the duration of the transaction the administrator account is granted membership of `data_plane_l2_owner` and of `amjis_app` (each only if not already a member) and exactly what was granted is revoked in the SAME transaction; net role membership is identical before and after and the plan refuses to commit otherwise.

**What is NOT done.** Nothing is inserted into, changed in or deleted from any chart's data; no build is started; no other function, table, permission, role or setting is touched. The plan refuses, changing nothing, if any build is running on any chart, if the deploy gate is not green, or if any object is not exactly the state the plan was written against.

**This does NOT, by itself, let a `bo_*` asset build in production.** Applying 1272 and 1273 (and merging the wrapper fixes in #3008 and #3029) removes two of several blockers. The others are listed in section 8; the S-L2 runbook (`s_l2/S_L2_WINDOW_RUNBOOK_v1_0.md`, blocker table B1 to B14) is the authority on the order. In particular `chart_fact_identity` is not readable by the builder until migration 1262 is live.

**What can go wrong.**
- *It stops by itself.* All checks run in one all-or-nothing transaction; any failure rolls everything back. Cost: a retry.
- *A brief wait on one function.* `CREATE OR REPLACE FUNCTION` takes a lock on that function only; a concurrent caller of `bind_l2_exact_inputs` waits. The plan refuses if a `data_plane_builder` session is active, and gives up rather than wait more than five seconds for a lock.
- *The grant is exercised for the first time by the next real build.* The dry run cannot run the L2 writers end to end; the rehearsal on the mirror database did (section 6, the end-to-end test), and nothing in production is claimed beyond that.
- *Rolling back after an L2 build.* The rollback restores the live function body and removes the eight EXECUTE grants; it does not delete any `bodha_*` data. It is safe at any time none of the builder's sessions is running.

**How it is undone.** One command (`--rollback`): CREATE OR REPLACE from the shipped live definition, re-attest, REVOKE the eight grants, in one transaction, with the same asserting checks and the same net-membership guarantee. If the connection drops at the very moment of the commit, the run records `commit_state_unknown`; nothing else runs until the state is read and decided (the same procedure as D6 section 8a).

**What you are asked to approve**, after Strategic Suvarna approves the dry run: the sentence in section 1. It authorises these two items and the transient grants only; not a rebuild, not migration 1262, not any other blocker.

## 1. The owner's authorisation (one line, exact)

> Authorization: run the dp_builder_privileges owner-path plan with hash `<PLAN_HASH>` on production (B3: `bind_l2_exact_inputs` grants SELECT on its transaction-local shadow tables to data_plane_builder; B4: EXECUTE on the eight bodha_*_identity functions to data_plane_builder; including the transient role grants `GRANT data_plane_l2_owner, amjis_app TO CURRENT_USER`, revoked in the same transaction, net membership unchanged), exactly as described in `<PLAN FILE PATH>` sha256 `<PLAN_FILE_SHA>`, after Strategic Suvarna has approved the dry run. No other change.

`<PLAN_HASH>` is the BOUND hash in section 2. The plan file's own sha256 is quoted next to it and outside the file (a file cannot contain its own hash).

## 2. Hashes (as of this draft)

| what | value |
|---|---|
| plan hash, unbound (plan text + expected diff) | `046af7d337cc9a57cfcd3d407bcbb9da14b584125ee92a49a2fe00e4181edd9b` |
| plan hash, BOUND to the gate pins (the one the owner authorises) | `50f45db82264e69ed5c5a4b0810e89c92df89cb7619ebc7a42debd2e0f3e5766` |
| executor `dp_builder_privileges_exec.py` sha256 | `6588ae1814609b0672e453ae68d28cec99dbf8f195ba2af7cef4bcc16f8c6869` |
| gate `prerun_gate.py` sha256 (pin) | `01ab1d70d0cffea015a64af5430f355dd8d419307aceeaeacf3a0cc4d715773e` |
| gate `run_gated.sh` sha256 (pin) | `305b4406bba57f85944bbb57cb269368287aaa6d6f782e986afa7f857606f076` |
| gate `executor_standards.py` sha256 (pin) | `bbea69552a6a92e7aed3a75758b533868e3e3d2c5b47385ccc1bf6c0660dc135` |
| live `bind_l2_exact_inputs` (shipped pre-state) | md5 `7bf8987517a7b76bd7ffae1c2bcf32ee`, 5678 chars, sha256 `af58dae4df9054784e078dfdfbf8a556a129efa01432b27d85d2ee7c3b5ca992` (equals the live attestation digest, read 2026-10-03) |
| patched `bind_l2_exact_inputs` | md5 `fe428d35f24ba8e54602b89ad76f3472`, sha256 `2d161048f05cebeef89548084db00306e517cd309a219a342de284de690a797a` |
| zero-context diff live to patched | 1 hunk, sha256 `fd150202203caf92c2ec890a7a709fdc7b89b83dd8171a0480396fd477bbcb98` |
| `1272_...sql` sha256 | `fc66015bfade235b89796ee8ca69d78cd64d58598d49a978020ac2a6b3f0c7f0` |
| `1273_...sql` sha256 | `7d040ca0f1b1026968cd4450f9e8eefb9cc222f1718ee671bb5432859ad80851` |

The plan hash is `bind_gate_into_plan_hash(sha256(plan text + "\n" + json(EXPECTED_DIFF)), prerun_gate.py pin, run_gated.sh pin)`. Re-print the plan text with the executor's `render_plan()` (the dry-run record carries it) and compare.

## 3. The hunk (B3), exactly

Inserted into `bind_l2_exact_inputs(uuid, jsonb)` immediately before `v_vector_digest := encode(digest(p_dependency_vector::text, 'sha256'), 'hex');` and the receipt `DROP TABLE IF EXISTS pg_temp.l2_data_plane_bind_receipt;`:

```sql
  -- 1272: the pipeline login must be able to READ the shadows this function creates (they are owned by the function owner and carry no ACL).
  -- The grant goes to the one login this function already requires (session_user = data_plane_builder); other sessions cannot see these temp
  -- tables and they drop at commit. The bind receipt is NOT granted.
  FOR v_table IN
    SELECT c.relname FROM pg_class c
    WHERE c.relnamespace = pg_my_temp_schema() AND c.relkind = 'r'
      AND pg_get_userbyid(c.relowner) = current_user
      AND c.relname <> 'l2_data_plane_bind_receipt'
    ORDER BY c.relname
  LOOP
    EXECUTE format('GRANT SELECT ON pg_temp.%I TO data_plane_builder', v_table);
  END LOOP;
```

Properties the tests pin: the patched body equals the live body with those twelve lines removed (nothing else changed); the grant names the builder and nothing else (no PUBLIC); it is limited to temporary tables in the caller's own temp schema owned by the function owner; the receipt is excluded; the function's owner, SECURITY DEFINER flag, `search_path` setting and ACL are unchanged.

## 4. B4, exactly

Issued as `amjis_app` (owner of all eight): `GRANT EXECUTE ON FUNCTION public.<name>(<args>) TO data_plane_builder` for

`bodha_cgm_edge_identity(uuid,text,text,text,uuid,uuid)`, `bodha_cgm_edge_identity_namespace()`, `bodha_cgm_node_identity(uuid,text,text,text)`, `bodha_cgm_node_identity_namespace()`, `bodha_contradiction_identity(uuid,text,uuid,uuid)`, `bodha_contradiction_identity_namespace()`, `bodha_signal_identity(uuid,text,text,text,jsonb)`, `bodha_signal_identity_namespace()`.

Pre-state checked per function: exists, owner `amjis_app`, not SECURITY DEFINER, no `proconfig`, the bound ACL, no builder EXECUTE. Post-state: across ALL roles the set of (role, identity function) EXECUTE pairs gains exactly the eight builder pairs and loses none.

## 5. Order of operations (one transaction, as the non-superuser administrator)

1. Transient membership: `GRANT data_plane_l2_owner TO CURRENT_USER` and `GRANT amjis_app TO CURRENT_USER`, each only if not already a member.
2. Read-only preconditions (any failure = refuse and ROLLBACK): no `build_runs` planned/running/paused on any chart; no L1 generation `building`; no `data_plane_builder` session; `digest(text,text)` resolves; the deploy gate's three queries green BEFORE the plan; the bind function and the eight identity functions in exactly the bound pre-state; the attestation row exists once with the live digest.
3. `SET LOCAL ROLE data_plane_l2_owner`: `CREATE OR REPLACE FUNCTION public.bind_l2_exact_inputs(...)` with the patched body; re-attest (immutability trigger off, UPDATE, trigger on; rowcount must be 1).
4. `SET LOCAL ROLE amjis_app`: the eight GRANTs.
5. ASSERTING post-checks (DO blocks that RAISE): `has_function_privilege` true for each of the eight; a grant-mechanics probe (a temporary table created as the function owner and granted with the patched body's statement): `has_table_privilege` true for the builder and false for every other role.
6. Before/after snapshot compare against EXPECTED_DIFF (exactly one data-plane function entry changed, exactly one function attestation row changed, exactly eight identity ACLs changed each gaining exactly the builder, no table/sequence/schema/database ACL change, role membership identical, no append-only trigger state change, `pg_get_functiondef` after equals the patched body, the gate's three queries false AFTER the plan under search_path `public`).
7. Revoke exactly the transient memberships; check net membership equals the pre-state; COMMIT only if every check holds.

Launch discipline (GATE_V2): only through `exec/gate_v2/run_gated.sh <python3> dp_builder_privileges_exec.py <args>`; the SAME explicit interpreter for the dry run and the apply (exit 92 otherwise, bound by the evidence digest, which covers the interpreter path, the full `sys.version`, the psycopg and libpq versions); the executor refuses (exit 93) unless the launch marker verifies against the pinned gate files, refuses an under-test marker outside pytest (93) and any `DPBP_TEST_*` variable outside pytest (95); every mode needs `--expect-plan`, and the administrator credential is fetched only after the plan hash matched; `outcome.json` is written in every mode.

## 6. Evidence from the production-mirrored rehearsal (disposable PostgreSQL 15)

The mirror database is built from a read-only `pg_dump -s` of production's `public` schema with production's roles (owner roles, `data_plane_builder` NOINHERIT non-super, `amjis_app`, schema owner) and ACLs replayed from `relacl`; the administrator is `adm_mirror`, CREATEROLE and NOT a superuser (mirrors `postgres`). Recipe: `platform/python-sidecar/tests/l2/realpg/README.md` (added by PR #3008).

| run | exit | status | checks | failed |
|---|---|---|---|---|
| `--dry-run` | 0 | `DRY_RUN_ROLLED_BACK_ALL_CHECKS_HOLD` | 58 | none |
| `--apply` (evidence digest of the dry run) | 0 | `COMMITTED` | 59 | none |
| `--rollback-dry-run` | 0 | `DRY_RUN_ROLLED_BACK_ALL_CHECKS_HOLD` | 56 | none |
| `--rollback` | 0 | `COMMITTED` | 57 | none |

Dry-run evidence digest `e3f2d406dfada9fb0122abf7ddd25e77192f95ffb6eb407590be54957f363ebe`; rollback evidence digest `d2a6bda93a7875483b5de1ad49e4b91cf156e133686b7ea0927c8fb77d98a4f1`. The rollback test compares the restored state with the starting state on: the bind function md5, its attestation digest, every data-plane function fingerprint, both function-attestation tables, the identity function ACLs, every other function ACL, the table ACLs, role membership and the EXECUTE pair set: all identical; the builder can execute none of the eight functions afterwards.

End-to-end proof (test `test_end_to_end_bo_sudarshana_runs_as_the_builder_after_apply_and_no_other_role_reads_the_shadows`): before the plan, the real `asset_runner._run_data_writer` run of `bo_sudarshana` as `data_plane_builder` (no superuser; the wrapper from #3008 and #3029) fails with `permission denied`; after the plan the adapter runs end to end, the integrity check reads the real table, and the shadows are readable by the owner and the builder only. Note that this run uses a fixture chart on the mirror; the production rebuild needs the other blockers of section 8.

Tests: 19 pure tests (bound constants, hunk anchors, gate pins, plan-hash sensitivity, interpreter exit 92, launch refusals, py3.11 compatibility) and 13 mirror tests; 32 passed; the 19 pure tests also pass under Python 3.11.16 in the repository's Linux CI image (`se-ci311v`, repo mounted read-only; the 13 mirror tests skip there without a database). Mutation proof (`tests/mutation_proof.py`): baseline passes, all 15 mutations killed (grant to PUBLIC; shadows granted to PUBLIC; receipt granted; re-attestation skipped; membership never revoked; build-in-flight precondition bypassed; evidence digest not enforced; interpreter precheck disabled; gate pin check skipped; asserting post-check made a no-op; grants issued by the wrong role; live-body precondition dropped; deploy gate result ignored; rollback does not revoke; no-other-role check compares nothing).

`vitest tests/unit/migrations/dp_builder_privileges_not_discovered.test.ts` proves migrate.ts cannot discover the two SQL files (they live outside `platform/migrations` and `platform/supabase/migrations`, and `collectMigrationFiles` over the real directories lists no 1272/1273-numbered file; a mutation that copies one of them into `platform/migrations` fails the test). No `deploy.yml` or `migrate.ts` change.

## 7. Disclosure and the between-state

Applying this plan changes no row and no served surface. It is not a "between-state" in the N-91 sense; it only widens what the build login may do. The runbook's between-state disclosure for the S-L2 window is separate. One correction carried into the runbook: the N-91 statement "1,340 signal_ids move" is a LOWER BOUND (1,340 MSR signals embed the random `chart_divisionals.id` in their identity configuration; any other embedded value that moves in the L1 rebuild moves its signal id as well).

## 8. What this plan does NOT unblock (so nobody reads green here as "bo_* can build")

| blocker | state | owner of the fix |
|---|---|---|
| B1 UUID vs str `chart_id` in every `@l2_producer` adapter | fixed in #3008 (armed by the coordinator) | wrapper |
| B2 open-before-bind order | fixed in #3008 | wrapper |
| B3 shadows unreadable by the builder | THIS plan (1272) | owner path |
| B4 EXECUTE on the identity functions | THIS plan (1273) | owner path |
| B5 `chart_fact_identity` not readable by the builder | migration 1262 | SS |
| B6 integrity check reads the shadows | fixed in #3029 (MED review finding: reset `search_path` at wrapper entry as well; separate commit) | wrapper |
| B7 `bo_laksana` strict `inserted == len(...)` check | to confirm in the production-mirrored rehearsal | S-L2 rehearsal |
| B8..B14 | see `S_L2_WINDOW_RUNBOOK_v1_0.md` (writer-gap preflight, reader cannot read L1/L2 heads, no light-writer heartbeat so the N-93 watchdog pause stands, `bo_samvada` spec, rehearsal items) | SS / runbook |

Merging #3008 does not unblock `bo_*` in production; neither does applying this plan. B3, B4 and B5 (and B6) must all be live, and the production-mirrored rehearsal of the runbook must pass, before an S-L2 window.
