---
artifact: J4B_PREBUILD
version: "1.2"
status: BUILT_WAITING_ON_GATE — source preparation only; operational acceptance not earned
date: 2026-10-16
authority: "A6 D-40 / SR-A4-01; J-4b and its eight named children"
changelog:
  - "1.2: merge main P07; retain its protected 1235 window and align the rehearsal, ledger readbacks and digest fixture. Migration bytes unchanged."
  - "1.1: J4B-R01 schema-USAGE detector, maintained offline rehearsal (F3–F8), and conditional separate-operation 1235 readback. Applied migrations unchanged."
  - "1.0: retain P05's inherited ports, repair PUBLIC ACL inspection, prepare independent provisioning readback and local mutation proofs."
---

# J4B preparation

P05 (`d9ba4934f4bfe7c159ecc42e7fcb7190f4b982c1`, PR #3508) is already contained in this branch's base. Its seven inherited ports are retained. This preparation adds a catalog audit and repairs the window runner's documented PUBLIC-role defect. It creates no migration, changes no applied migration, provisions no principal, defines no remote job, enables no operation, and writes no executor or independent-review receipt.

The governing provisioning design is `ROLES_AND_SEAL_PROVISIONING_RUNBOOK_v1_0.md`, especially acts 1, 2a, 2b, 6, 8 and the L1 ACL prerequisite. The source close record `PROTECTED_WINDOW_CLOSE_20261004.md` §2.9 records the PUBLIC defect; §7.1–7.6 records the remaining provisioning/job work. These source briefs are in the prompt's read-only `/Users/Dev/madhav-l3/pravaha/00_ARCHITECTURE/briefs/pravaha/` checkout; they are absent at those relative paths on the accepted main used here. Historical production observations in them are provenance, not new readbacks.

## Child coverage

| Item | Retained/prepared source | Code oracle |
|---|---|---|
| J-4b | Protected migration refusal and ordered deploy selection; PUBLIC ACL fix; new independent provisioning SQL | Window runner suite, schema-capability suite, mutation harness |
| J-4b-pr2817 | Applied 1204 AM-7 CHECK/selector widening, v1.0 reader compatibility, unchanged preflight and protected route | AM-7 live suite plus the existing A5.1/v1.5 static suites |
| J-4b-pr2949 | Existing 1378 v7 grant port, unchanged; column-narrow publication/legacy reads | 1378 static suite; catalog audit detects individually missing grants and wider grants |
| J-4b-pr3083 | Active registry target guard after chart authorization | Existing route authorization/target suite |
| J-4b-pr3089 | Four read-only runner phases, SQL pins, identity and refusal evidence | Existing shell harness plus real PostgreSQL cases |
| J-4b-pr3108 | C-sorted comparisons, evidence bytes and runner digest | Existing C44 sort/digest regressions |
| J-4b-pr3114 | Pinned 1235 post-apply function/signature/owner/ACL/ledger readback | Existing stub and real PostgreSQL cases |
| J-4b-pr3119 | Exact project Firebase service-agent pair, verifier-control gate only | Existing verifier isolation and C53 cross-gate regressions |
| J-4b-a55j | Readback procedure prepared; **operation left out** | Requires actual provisioning and independently accepted operation evidence after the gate |

The archived origin refs are locally present at the exact seven inventory heads. **(I) INTERPRETATION:** use these immutable local objects and the already-landed P05 port instead of fetching/re-porting them: this job forbids Git writes. Alternative: fetch each archived branch again in an authorized cockpit session. The local source provenance and measured mutation logs are in the job folder; they do not replace exact-head CI or independent review.

## Independent SQL audit

`platform/scripts/readbacks/gochara_provisioning_readback.sql` is one SELECT/WITH statement accepted by the real fleet `readback_sql.sh` protocol (`fleet/readback_sql.sh:31`–`42`). It starts with WITH, contains no backslash, runs through the prepared-query protocol, and executes none of the audited functions. It reads only catalogs and the migration ledger. Local tests exercise that actual executor script against an isolated loopback database, including its CSV/TSV output.

The result has one row per `(kind, principal, object, privilege)` with `expected`, `observed`, `ok` and database/session identity. A missing role/object yields failed observations or a SQL error; either refuses acceptance. Each row must have `ok = true`, the identity must match the request, and the independent reviewer must bind the exact SQL digest to the executor evidence.

The independent expectation covers the complete 1378 v7 relation/column/function grant set for verifier and sealer, their separately owned L1 reads, unexpected Gochara relations/functions, and grant options. It also checks login/no-inherit/elevated attributes, the runbook's verifier/sealer connection limits (4/2), no role memberships, database CONNECT, effective public-schema USAGE for all four required principals, and absence of schema CREATE. PostgreSQL privilege functions include PUBLIC pseudo-role grants; regressions remove direct/PUBLIC USAGE and exercise PUBLIC table privileges. Table privileges alone cannot make the audit green when namespace access is absent. Builder table **and column** writes on both verification tables must be false, builder membership in verifier/sealer must be false, sealing EXECUTE must be false and its qualification helper must remain available. No verification-row write is attempted.

**(I) INTERPRETATION:** retain the source runbook's explicit starting connection limits 4/2 for the prepared principal audit (`ROLES_AND_SEAL_PROVISIONING_RUNBOOK_v1_0.md:167,192`). Alternative: a future reviewed resource/concurrency change must update the expected limits with its provisioning specification. The query does not inspect passwords or attest credential activation, authentication, capacity, RLS row visibility, or cloud IAM.

After phase eligibility, an authorized controller stages these exact reviewed SQL bytes under its own `run/ops/sql/` directory and requests executor `readback_sql`. The builder must not stage there or query production directly. The response's zero failures is an observation; the controller/reviewer still owes the hash-bound, same-request/same-operation acceptance required by the plan. Neither this file nor a local green test may produce the operational receipt.

The obsolete pre-window merge-control assertion that 1378 must be absent is replaced with today's source boundary: the landed 1378 file exists, is permitted by the routine runner and is never selected by the protected-window invocation. Both previously optional source checks now run in ordinary discovery; this does not claim a historical merge-control receipt.

The source migrations remain byte-for-byte unchanged. No new migration number is required. L1 SELECT grants are audited, not issued here: migration 1378 explicitly leaves them to the data-plane ACL owner (`platform/migrations/1378_gochara_verifier_sealer_inventory_grants.sql:53`).

## Configured but disabled: precise remaining evidence

The existing definition-only workflow is `.github/workflows/gochara-verification-job-deploy.yml:62`. Its whole-definition validator is `platform/scripts/gochara_verification_job_readback.py:73`; the existing workflow-static and readback suites cover its immutable image, verifier identity/secret, command/args, Cloud SQL attachment, resources, tasks and zero retries. No workflow is dispatched by this preparation.

The accepted operation table still has `verification_job.enabled=false`, a disabled prepared dry-run, and a `TO_BE_SET_BY_J-4b` script at `fleet/executor_ops.json:15`. Builders cannot edit that table (its `_doc` and KARAKA KA-02). Thus this preparation **does not claim a configured executor operation**. Controller-owned reviewed binding, actual job definition deployment and independently collected definition/disabled-state evidence remain due.

**(I) INTERPRETATION:** “disabled” is scoped to the fleet operation's admission state; it does not assert that a Cloud Run Job has a native suspension switch or that all other principals are unable to execute it. Alternative: a broader inability-to-execute claim requires a separately specified and observed IAM/scheduler policy. A disabled source-table flag alone is insufficient operational acceptance.

After eligibility, the authorized executor/controller must collect the complete v1/v2 job definitions at the actual deployed source/image and run the existing whole-definition validator; independently read back the disabled operation binding and any scheduler/execution policy claimed by its request. Record the same request/operation identities and evidence digests in the controller's accepted receipts. Until then `configured_disabled_readback` and A5.5j's `principals_grants_disabled_config` remain unearned.

## Repeatable local verification

Use the authorized cluster only. The Python readback suites now accept `KALA_ADMIN_DSN=postgresql://postgres@127.0.0.1:55433/postgres`, validate it with the existing disposable-DB guard and own/drop a UUID-named database. They never start/stop a server or alter an existing principal. Their new catalog fixture creates uniquely named test roles and removes them. Without that local override, CI retains its existing disposable-server helper. CI installs psycopg for these catalog tests; all new regressions are inside the already-required readback suite, so no new test-path selection is added.

The AM-7 suite has the analogous guarded local lifecycle for `gochara_a51_test`; CREATE refuses an existing database, and teardown drops only one this invocation created. CI's supplied fixture remains supported. Set `TMPDIR` and pytest `--basetemp` inside JOB_SCRATCH, `PYTHONDONTWRITEBYTECODE=1`, `SE_EPHE_PATH=/Users/Dev/kalayantra/ephe`, pytest `-p no:cacheprovider` and vitest `--no-cache`.

`python3 platform/scripts/gochara/mutation_check_j4b.py --scratch "$JOB_SCRATCH/j4b-mutations"` produces separate fixed/reverted logs, copies and `evidence.json`. It requires a fresh scratch subdirectory and JOB_SCRATCH, uses no Git writes, and modifies only copied source. The PUBLIC-original and audit-original cases are complete production reversions of this job's fixes; the other cases remove or broaden inherited semantics. Every selected oracle must pass fixed and fail mutated; a surviving mutation fails the harness. This is builder evidence, not independent acceptance.

A5.5j needs actual protected-window/grant/L1/principal/credential/job evidence and original prerequisite A5.5e/J-4a before it can close. None is inferred from a code merge. Exact-head independent child review, CI, containing deployment and operation receipts remain separate gates.


## Round-1 rehearsal repairs (J4B-R01, F3–F8)

The maintained fixture is now `platform/scripts/gochara/rehearsal/`; its README records the read-only historical source and hash provenance. **(I) INTERPRETATION:** port and maintain the missing harness in this branch, since the archived checkout is read-only. Alternative: an authorized cockpit job later updates the archived runbook. No production route, grant operation, cloud job, credential activation or applied migration is changed.

Run from the repository root with `REPO="$PWD" PGHOST=127.0.0.1 PGPORT=55433 PGUSER=postgres STRICT=1 REHEARSAL_OUT="$JOB_SCRATCH/rehearsal" bash platform/scripts/gochara/rehearsal/run_window_rehearsal.sh`; repeat with `TODAY=1` and a fresh output directory. The latter is a legacy mode name, **not today's observed production ledger**. **(I) INTERPRETATION:** represent current-source predecessors in an explicitly synthetic ledger, applying the relevant Gochara routines for real. Alternative: refresh independently authorized production-ledger evidence before the real sitting. This fixture never executes unrelated layer migrations.

Both modes exercise the real eleven-file window, deliberate 1233 failure/retry, complete pre-window runner and unchanged 1378 SQL. The release fixture applies real 1243/1302 and materializes registry, runtime-evidence and monitor tables. Its 129 placeholder rows plus two real 1243 inserts reproduce historical 131/124 expectations; monitor rows are labeled synthetic, not a live census or continuity receipt. **(I) INTERPRETATION:** use this bounded synthetic schema/data fixture; alternative: a separately reviewed full registry census. The independent real sitting still owes its current counts, continuity review and pinned source/ledger evidence.

S4 no longer grants the two functions that 1378 prohibits. **(I) INTERPRETATION:** after the real window runner, apply unchanged 1378 in a fixture-local transaction to measure its ACL closure without representing every later platform migration. Alternative: a full platform schema/prerequisite fixture through 1378. This is no operational migration-runner acceptance. The Node tsx loader avoids CLI IPC sockets under long scratch paths and leaves original migration errors visible. Lifecycle creates a unique database, preserves pre-existing role attributes, and drops only successful CREATEs owned by this invocation, including on failure. A recording SQL guard makes the unsafe historical reversion testable without sending its DROP ROLE commands to PostgreSQL.

For C49, `fn-1235-readbacks.sh` remains strict by default. **(I) INTERPRETATION:** optional `--if-applied` returns **3 / NOT_APPLICABLE** only when both its ledger row and function are absent, records read-only applicability evidence, and issues no PASS/applied receipt. Alternative: run the strict detector only after an accepted protected-window apply. Any partial state still fails strict checks; an applied state runs every original pinned signature/owner/ACL/hash check. Main P07 is authoritative: the protected invocation now includes 1235 (`.github/workflows/deploy.yml:1112`; `platform/scripts/migrate.ts:152`). Its unchanged migration runs after the sitting fixture supplies the runtime-evidence tables and only while the real runner holds the bounded CREATE capability. The pre/post-window readbacks exclude it from routine predecessors and require its digest in the six-file pending ledger. The rehearsal verifies that an earlier 1233 failure leaves the function absent and that recovery creates a callable function. The optional applicability probe remains honest before this window; it cannot replace post-window acceptance.

The complete provisioning, C49 and rehearsal suites are wired into the required readback CI job, retaining skip rejection. Fail-on-revert copies/logs and exact commands are job-folder evidence for independent review; local success does not replace exact-head CI or operation receipts. Migration-runner atomicity and P9 PUBLIC readback remain with `kalayantra/w4-window-fixes`.
