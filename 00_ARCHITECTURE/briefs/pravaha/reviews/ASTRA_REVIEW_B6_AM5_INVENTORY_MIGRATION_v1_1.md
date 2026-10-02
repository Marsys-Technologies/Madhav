---
artifact: ASTRA_REVIEW_B6_AM5_INVENTORY_MIGRATION
version: "1.1"
reviewer: "Codex gpt-6-astra"
date: "2026-10-02"
verdict: REJECT
reviewed_commit: 377c5ce71
authority: "Review only; authorizes nothing."
---

**Verdict: REJECT.** R1–R4 are closed. R5 is partly closed. One new merge-blocking defect remains: **1206 assumes PUBLIC EXECUTE on its functions, but the governed deployment bootstrap revokes that default for their creator, `amjis_app`.** The builder tests miss this because they create the functions as `postgres`.

The review covers detached commit `377c5ce71bd49484581e4275c2274385cbcf018b`, the prior v1.0 review, AM-5 v0.5/v0.6, and the review-driven corrections in locally available `origin/campaign/pravaha` at `e1f07c929`. No repository fetch was performed.

For compact file:line references below:

- **SQL** = [platform/migrations/1206_gochara_search_inventory_completeness.sql](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2867b/platform/migrations/1206_gochara_search_inventory_completeness.sql)
- **DB** = [platform/tests/integration/gochara_b6_am5_search_inventory.db.test.ts](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2867b/platform/tests/integration/gochara_b6_am5_search_inventory.db.test.ts)

**1. Fidelity to AM-5 and closure of R1–R5**

| Finding | Status | Evidence and counterexample result |
|---|---|---|
| **R1: commitment equality lacks path/version scope** | **CLOSED** | Both the predicate and diagnostic now use `(chart, generation, class, path, version, ob_id)` — **SQL:810–838**. My cross-path and cross-version reruns produce `committed_set_mismatch`; another pin’s stored obligations cannot satisfy the commitment. PostgreSQL regressions are at **DB:593,612**, and passed in inspected CI. |
| **R2: snapshot convention unbound** | **CLOSED** | Snapshot insertion resolves the publication bridge; first sealing checks publication and every claimed partition, including missing bridges — **SQL:589–599,755–776**. My extracted-predicate reruns detect incompatible and absent bridges for both publication and partition, without records/windows. **DB:729–759** exercises these cases in PostgreSQL and passed in CI. |
| **R3: excluded pin accepts NULL reason** | **CLOSED** | Explicit non-NULL enforcement and total boolean predicates close both escapes — **SQL:389–399**. My reruns reject `(reason=NULL, ruling=NULL)` and `(reason=NULL, ruling='R-9')`; valid controls pass. **DB:761–776** passed in CI. |
| **R4: timezone-dependent inputs / wrong audit column** | **CLOSED** | Both L1/dasha helpers pin UTC and float rendering, exclude the actual `computed_at`, and scope rows to the chart — **SQL:247–277**. **DB:530–566** tests four timezones, audit/material changes, and construction in Kolkata followed by sealing in New York. These passed in inspected PostgreSQL CI. I could not independently rerun PostgreSQL locally. |
| **R5: database evidence, roles, concurrency, mutations** | **PARTLY** | Database execution, realistic column types, competing sessions, all-table post-seal operations, and reproducible mutations are substantially repaired. However, **DB:399–418** applies migrations through the `postgres` connection, so **DB:570–579** does not reproduce the deployment creator’s ACLs. See questions 4 and 6. |

My R1–R3 predicate reruns used extracted expressions in an in-memory SQLite database, with PostgreSQL-specific casts/record parameters adapted. They are independent predicate checks, **not PostgreSQL trigger executions**. PostgreSQL results cited above come from inspected CI logs.

The central structural contract is now implemented:

- One input snapshot per chart/generation, with inventory and interval bindings.
- One-shot finalization that verifies both digests.
- Exact committed/stored obligation equality within each owning pin.
- Full-horizon coverage **for each obligation**, using only `searched_complete` and `searched_unqualified`.
- Refusal of missing-input intervals, unaccounted registry versions, input drift, and partition overclaims.
- A separate sealed-generation replay branch that avoids requiring later registry versions.

Evidence: **SQL:305–331,455–456,603–641,779–884,890–928**.

It is nevertheless **not an exact, complete implementation of every v0.5/v0.6 statement**:

1. **Verification is stronger:** every verification row must agree, rather than merely requiring one matching row. A stale disagreeing row vetoes sealing. This is disclosed and recoverable before sealing by deleting that candidate verification row — **SQL:875–884; DB:669–683**.
2. **Ledger bytes changed:** the new `input=<digest>` header correctly binds even an empty ledger, but changes the earlier W1 ledger vectors — **SQL:528–539**. The current campaign text records this as a v0.7 correction.
3. **F-3 remains deferred:** whole-second bounds, canonical/storage-domain mapping, declared class census, and historical registry-version selection still constrain the eventual writer. The SQL currently requires accounting for **every sealed registry version per claimed class** — **SQL:342–346,779–787**.
4. **F-6 remains deferred:** the aggregate digest helper exists, but generation-5 manifest construction incorporating `inventories_digest` is not implemented here — **SQL:544–551**. Replay relies on sealed immutability and recomputation; it does not compare against an independently stored aggregate commitment.

These are disclosed follow-up boundaries, not reopened structural bypasses.

**2. Migration safety, trigger ordering, locking, and cost**

The migration is additive against the inspected sources. Migrations 1153–1157 are unchanged against local `origin/main`; the seventeen new function names do not replace their existing functions. The only new trigger on an existing relation is **SQL:941–943**. CI also passed the existing-object fingerprint comparison at **DB:429**.

Idempotence is correctly qualified:

- The migration runner verifies the recorded content and skips an already-applied file.
- Directly executing this SQL twice deliberately fails its gate.
- Replaying an already-sealed generation takes the integrity branch.

See [migrate.ts:797](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2867b/platform/scripts/migrate.ts:797) and **SQL:119–179,890–928**. Calling the file freely repeatable would be inaccurate.

The existing `..._write_guard` sorts before `..._z_search_complete`. Thus its publication, coverage-drift, and membership checks still execute first, including during replay. This follows PostgreSQL’s [alphabetical ordering of equivalent triggers](https://www.postgresql.org/docs/15/trigger-definition.html).

The new seal guard independently acquires **chart EXCLUSIVE → global SHARED** before its registry checks — **SQL:914–915**. Pin/obligation insertion follows the same order; UPDATE/DELETE statement guards acquire chart context before tuple work — **SQL:568,644–645,683–703**.

The orchestrator’s main-connection lock uses `hashtext(chart_id)`, while the contract uses the prefixed `gochara5:chart:` family. The competing-session test verifies that the main connection does not block the worker — **DB:1010–1017**; [orchestrator/locks.py:13](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2867b/platform/python-sidecar/pipeline/orchestrator/locks.py:13).

I found no new lock-order inversion under the governed protocol. This remains conditional on writers acquiring the family lock **before legacy publication/coverage DML**. Automatic locking on the six new tables cannot repair an older writer that first takes a legacy row lock and subsequently requests the chart lock.

Seal insertion performs substantial synchronous work: live-input hashing, per-class digest recomputation, registry accounting, commitment checks, and per-obligation range aggregation while retaining the family locks. CI recorded **53 ms** for 27 classes × 40 obligations × 2 intervals — **DB:1046–1087**. That is useful small-fixture evidence, not a production workload bound; its input fixture contains only two facts and two dasha rows.

**3. Partial-search acceptance and legitimate-completion refusal**

My exact W2 model rerun used:

- Only P1 and P5a in the registry.
- Both pins `included`, with their own nonempty committed sets.
- All P1 obligations stored and fully covered.
- No P5a obligations stored.
- A verifier that merely rehashes the stored inventory.

It produced **`committed_set_mismatch` for P5a**. The corrected SQL predicate independently detects that omission. This establishes the intended distinction between absent obligations and a genuinely derived empty set.

The database test called “W2 exactly” uses additional excluded P6/P1-version pins through `goodBuild`; it exercises the same omission but is not literally the minimal W2 row set — **DB:79,295,349,582**.

Within the declared-inventory/trusted-verifier boundary, I found no remaining structural route among the reviewed adversaries for borrowing obligations, combining snapshots, or substituting coverage of different obligations for full coverage of each obligation.

Two qualifications matter:

- SQL still cannot detect a false `computed_empty` or incorrectly reduced commitment when supplied with a matching purported verification digest. AM-5 explicitly assigns doctrinal correctness and derivation independence to O-RP-9; inserting a verification row does not establish that independence.
- A legitimately complete build is blocked under the documented deployment ACL baseline by the new finding below. Separately, stale verification disagreements are recoverable before sealing; they do not permanently trap a candidate.

**4. Privileges and function security — new merge blocker**

**R6 — P1: required function EXECUTE privileges are absent under the governed creator defaults.**

The evidence chain is concrete:

1. Deployment validates `PROD_DATABASE_URL` as the **`amjis_app`** route — [validate-migration-database-routes.ts:12](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2867b/platform/scripts/validate-migration-database-routes.ts:12).
2. The ownership bootstrap explicitly executes:
   ```sql
   ALTER DEFAULT PRIVILEGES FOR ROLE amjis_app
     REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC;
   ```
   See [nirmana-evidence-ownership-preflight.ts:256](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2867b/platform/scripts/nirmana-evidence-ownership-preflight.ts:256).
3. The protected migration job requires Nirmana’s marked state. Its temporary capability grants `amjis_app` schema CREATE, without restoring function execution defaults — [deploy.yml:974](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2867b/.github/workflows/deploy.yml:974), [jataka-schema-capability.ts:64](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2867b/platform/scripts/jataka-schema-capability.ts:64).
4. **SQL:92** nevertheless assumes PostgreSQL’s PUBLIC EXECUTE default. **SQL:950–963 contains only table/column grants; there are zero EXECUTE grants.**

PostgreSQL applies the creating role’s configured defaults to new functions; table grants do not confer function execution. See [ALTER DEFAULT PRIVILEGES](https://www.postgresql.org/docs/15/sql-alterdefaultprivileges.html).

Consequently, under that checked-in bootstrap state, `data_plane_builder` cannot call new digest APIs. Even a writer computing digests externally encounters invoker-security calls to new helpers inside insertion/finalization guards — **SQL:576–577,618–619**. This is a source-established deployment incompatibility, not a production permission error I observed.

The ownership design itself is appropriate:

- **`amjis_app`** owns the new objects and applies the migration.
- **`data_plane_builder`** remains a grantee. Its candidate INSERT/DELETE, restricted finalization UPDATE, and necessary SELECT grants do not grant sealing, schema creation, TRUNCATE, or trigger control.
- A separately authorized sealer needs the seal/publication privileges, required reads, and executable function call graph.
- The independent verifier’s production principal remains unspecified; the disposable `gochara_sealer` is not evidence of a provisioned production principal.

All seventeen functions use invoker security and pin `search_path`. That avoids an unnecessary ownership bypass, but makes complete caller grants essential. Fix the ACL contract explicitly; changing these functions to SECURITY DEFINER or reopening PUBLIC defaults would not be an appropriate substitute.

The current “real roles” test switches callers only **after `postgres` created the functions with different defaults** — **DB:399–418,570–579**. It therefore passes while missing R6.

**5. Protected-window wiring and rollback**

The source wiring is sound:

- The protected deployment list includes 1206 after 1204 — [deploy.yml:1085](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2867b/.github/workflows/deploy.yml:1085).
- The runner’s protected set includes 1206 and rejects routine application — [migrate.ts:138](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2867b/platform/scripts/migrate.ts:138).
- My static execution confirmed byte identity between the embedded gate and standalone preflight DO block.
- The workflow pins deployment source and always attempts capability revocation.

The preflight does **not** attest the builder’s effective function permissions, so passing it does not address R6.

The runner commits each migration separately. A failed 1206 rolls back its own work but may leave 1204 committed — [migrate.ts:830](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2867b/platform/scripts/migrate.ts:830).

The rollback prose is appropriately divided between an unused installation and one that has sealed generations: unused objects may be removed in dependency order with ledger reconciliation; used installations require forward correction — **SQL:103–112**. This is an operational outline, not an executed rollback proof.

**6. Do the tests earn their claims?**

**Substantially more than v1.0, but not the deployment-principal claim.**

I inspected [CI run 36933767759, database job 110609086462](https://github.com/Marsys-Technologies/Madhav/actions/runs/36933767759/job/110609086462). Its logs establish:

- PostgreSQL **16.15**.
- **31 passing tests**: 30 database cases plus the required-URL sentinel.
- Passing R1–R4 regressions, competing-session locks, all six tables’ post-seal operation checks, and registry-advance replay.
- **27/27 mutations reported caught**, zero survivors, zero missing targets.

The run executed GitHub merge commit `8769db5a9470eeefdc20091e98c80d5080b72677`. I compared it with the reviewed head: the reviewed migration, tests, harness, and wiring were unchanged. These are inspected CI results, **not my own PostgreSQL rerun**.

My own read-only execution established:

- **14/14 static test bodies passed**, evaluated in memory using the project’s TypeScript compiler and Vitest matchers.
- **35/35 campaign model cases passed**, with output matching the checked-in model evidence.
- Exact minimal W2 and independent borrowing/predicate counterexamples behaved as described above.
- All **27 mutation anchors** occur exactly once in the reviewed SQL.

Remaining limits:

- The supplied PR body’s **20 database / 10 static / 18 mutation / PG17-only** account is stale.
- The mutation harness counts any test failure as a caught mutation, including static assertions; it does not retain a named behavioral killer for each mutation — [mutation_check_1206.py:98](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2867b/platform/scripts/gochara/mutation_check_1206.py:98). The baseline pass makes the report useful, but “27 database guards independently demonstrated” would overstate it.
- `GOCHARA_REQUIRE_DB=1` prevents silent skipping inside this job. The job is documented as deliberately advisory — [ci.yml:257](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2867b/.github/workflows/ci.yml:257). I did not verify current branch-protection settings.
- The fixture never creates functions as `amjis_app` under the revoked PUBLIC default. That is the material remaining R5 gap.

**Ranked merge-blocking amendments**

| Rank | Priority | Required amendment |
|---:|---|---|
| **1** | **P1 — R6 / remaining R5** | Define and grant the necessary function EXECUTE privileges for the builder and authorized runtime callers, including invoker callees; preserve owner/grantee separation and the existing no-seal boundary. Add an end-to-end regression that applies the real migration as `amjis_app` with PUBLIC function execution revoked, then constructs/finalizes as `data_plane_builder`. Prove the failure before the fix and success afterward, while retaining unauthorized-operation refusals. Attest prerequisite helper permissions explicitly. |

**Separate follow-ups**

1. Refresh the PR evidence to the actual CI commit, PostgreSQL version, test counts, and mutation report. Preserve mutation-to-failing-test attribution and describe advisory versus merge-required execution accurately.
2. Carry the disclosed ledger-byte and verification-policy changes into the eventual ratified specification. Preserve F-3’s writer/identity obligations and F-6’s manifest binding; this migration does not close them.
3. Before the protected window, establish representative seal cost, runtime-version compatibility, effective ACLs, writer lock ordering, quiescence, and a reviewed recovery procedure.

**What I could not verify**

I did not independently execute PostgreSQL integration tests, cross-timezone SQL calls, the deployment-ACL counterexample, or mutations locally. No disposable URL was configured, and the read-only sandbox prevented the required writable setup. The mutation harness also rewrites the migration file, so I did not run it.

I did not connect to production or verify its actual catalog, ACLs, migration ledger, runtime version, or workload. “Applied nowhere” remains the supplied premise.

No file or git state was changed. The checkout remained clean at `377c5ce71`.