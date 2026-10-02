---
artifact: ASTRA_REVIEW_A5_1_MIGRATIONS
version: "1.3"
reviewer: "Codex gpt-6-astra"
date: "2026-09-30"
verdict: REJECT
reviewed_commit: 9436ad276
authority: "Review only; authorizes nothing."
---

**Verdict: REJECT**

The simplification closes several round-3 defects, including the live publication trigger, rule-membership race, prerequisite reassignment and disposable-database targeting. However, the locking design blocks writers dispatched by the frozen orchestrator itself, and permitted transactions can still create lock inversions. Coverage binding also remains incomplete and introduces an enrichment regression.

This review accepts the steward’s explicit seal, existing advisory keys, presence checks and protected deployment window. It does not require restoring the removed verifier, replay GUC or legacy-table triggers.

HEAD is `9436ad276b351fcaafe3aa9684625f7d1e072e14`; the reviewed files match that commit. No files were written, no git write commands were run, no database was contacted, and neither prohibited directory was accessed.

“CLOSED” below means closed at source-review level. Database counterexamples are reasoned from source and PostgreSQL behavior, not executed.

**Closure table**

Evidence abbreviations:

- **M1153:** [sky-event substrate](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2765d/platform/migrations/1153_gochara_sky_event_substrate.sql); **M1154:** [rule-path registry](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2765d/platform/migrations/1154_gochara_rule_path_registry.sql); **M1155:** [relationship records](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2765d/platform/migrations/1155_gochara_relationship_record.sql); **M1156:** [evaluation windows](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2765d/platform/migrations/1156_gochara_eval_window.sql); **M1157:** [AV polarity](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2765d/platform/migrations/1157_gochara_av_polarity_declaration.sql).
- **MT:** [migration runner](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2765d/platform/scripts/migrate.ts); **DY:** [deployment workflow](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2765d/.github/workflows/deploy.yml).
- **DBT:** [database tests](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2765d/platform/tests/integration/gochara_a5_1_migrations.db.test.ts); **URL:** [disposable-database resolver](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2765d/platform/tests/integration/gochara_a5_1_disposable_url.ts).
- **S:** [frozen specification](/Users/Dev/madhav-l3/pravaha/00_ARCHITECTURE/briefs/pravaha/design/GOCHARA_DESIGN_SPECS_v1_4.md); **R3:** [round-3 review](/Users/Dev/madhav-l3/pravaha/00_ARCHITECTURE/briefs/pravaha/reviews/ASTRA_REVIEW_A5_1_MIGRATIONS_v1_2.md).

| Finding | Judgment | Evidence and disposition |
|---|---|---|
| **N1 — live `4.0` publication trigger** | **CLOSED** | No new trigger or seal FK targets `kala_gochara_publication`. Explicit sealing starts at **M1153:757** and rejects legacy generations before acquiring its lock at **M1153:761**. The governed-generation predicate is at **M1153:318**. This closes the publication-trigger defect; the broader claim that existing tables acquire no effects is false, as explained below. |
| **N2 — incomplete locking and isolation protocol** | **PARTLY CLOSED** | **M1153:332** and **M1153:346** explicitly reject non-READ COMMITTED isolation. State-reading guards acquire the appropriate advisory key first. However, scheduler/worker connection ownership defeats reentrancy, transaction-wide chart/global ordering is unenforced, and row locks can precede row-trigger advisory locks. See N12–N13. |
| **N3 — no deploy route compatible with protected schema** | **CLOSED** | The input at **DY:64**, protected-job condition at **DY:952**, exact file list at **DY:1056**, and runner refusal at **MT:146** implement the ruling. Revocation is scheduled at **DY:1069**. The route is present; “touches nothing” and unrestricted “no half-applied family” claims need correction. |
| **N4 — unsound definition verifier and mutating replay** | **CLOSED** | The removed verifier/GUC are not required under the ruling. Presence checks begin at **M1153:1021**, with validated constraints checked at **M1153:1089** and enabled triggers at **M1153:1116**. Tracked files are hash-checked and skipped at **MT:789**. All five embedded preflight blocks match their standalone counterparts byte-for-byte. |
| **N5 — rule sealing races membership insertion** | **CLOSED** | Membership construction takes the global key before checking the seal at **M1154:462**; seal insertion uses the same global guard at **M1154:514**. Consumers acquire it before checking completion at **M1154:476**. This closes the specific membership/seal race. Broader liveness defects remain under N2. |
| **N6 — changed reading under one contact ID across generations** | **CLOSED** | **M1153:953** checks existing non-NULL solved readings and non-placeholder methods on both INSERT and enrichment UPDATE. **M1153:918** serializes that check. The single canonical-chart constraint at **M1153:854** makes the chart lock sufficient for this currently permitted scope. |
| **N7 — enrichment leaves dependent precision stale** | **PARTLY CLOSED** | **M1155:734** propagates precision, and **M1155:369** permits precision-only synchronization after sealing. However, legitimate coverage extension changes the digest and causes the subsequent propagation to fail at **M1155:602**. See N15. |
| **N8 — prerequisite reparenting bypasses finalization** | **CLOSED** | **M1155:364** permits only `result` changes in prerequisite rows; **M1155:356** prohibits scope changes. The prerequisite trigger selects this mode at **M1155:784**. The former source-record escape is therefore prohibited. |
| **N9 — INSERT changes published window membership** | **CLOSED** | **M1155:347** rejects INSERT into sealed generations. **M1156:354** applies that guard to window membership and prohibits all membership UPDATEs. The prior destination-scope escape is also closed. |
| **N10 — incomplete applicability and mutable coverage parents** | **PARTLY CLOSED** | NULL-array rejection, fail-closed relation membership and full body-target keys are implemented at **M1155:597**, **M1155:623** and **M1155:611**. Windows require class coverage at **M1156:231**. But digest serialization has deterministic collisions, binding is checked only on child writes, and window coverage is not checked against contributing records’ relations/conventions. |
| **N11 — URL guard differs from driver target** | **CLOSED** | **URL:78** validates the driver’s parse; host, port and database are explicit; target-changing query parameters are rejected at **URL:71**. **DBT:684** passes the resolved configuration to `Pool`. All 27 committed URL cases passed in my connection-free assertion harness. |

**Lock order**

The keys match the orchestrator. The claimed complete ordering argument does not.

**N12 — P1: The orchestrator’s own workers block behind its scheduler.**

The migration’s reentrancy premise at **M1153:325** applies only when the lock holder and writer use the same PostgreSQL session.

The frozen runner does the opposite:

- [runner.py:1092](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2765d/platform/python-sidecar/pipeline/orchestrator/runner.py:1092) acquires the chart lock on the main connection; global acquisition follows at line 1101.
- [runner.py:682](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2765d/platform/python-sidecar/pipeline/orchestrator/runner.py:682) explicitly documents that the scheduler holds that lock while each asset uses its own connection.
- [runner.py:753](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2765d/platform/python-sidecar/pipeline/orchestrator/runner.py:753) opens the worker connection. [asset_runner.py:983](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2765d/platform/python-sidecar/pipeline/orchestrator/asset_runner.py:983) gives that connection to the writer.
- The main connection releases its advisory locks only after scheduling finishes, at [runner.py:1212](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2765d/platform/python-sidecar/pipeline/orchestrator/runner.py:1212).

Consequently, a governed worker waits for its scheduler’s lock while the scheduler waits for the worker. PostgreSQL session-level and transaction-level advisory locks conflict across sessions; reentrancy does not transfer between connections. [PostgreSQL advisory-lock semantics](https://www.postgresql.org/docs/17/explicit-locking.html#ADVISORY-LOCKS).

This is an application-level wait cycle, not necessarily a PostgreSQL-detectable deadlock. The runner’s watchdog can eventually mark the asset failed; that is not successful execution. Setting worker concurrency to one does not change connection ownership.

**DBT:869** proves that another connection blocks until the holder explicitly unlocks. It does not prove that an actual orchestrator worker can complete.

**N13 — P1: Local trigger ordering does not enforce transaction-wide lock ordering.**

Let **C** be the canonical chart key and **G** the global-assets key. With valid pre-existing parents:

1. Transaction A inserts a registry row and acquires **G** through **M1153:369**.
2. Transaction B inserts a relationship record, acquiring **C** through **M1155:344**, then waiting for **G** through **M1154:476**.
3. A inserts a contact-ledger row and waits for **C** through **M1153:918**.

That is **A → C → B → G → A**. No trigger violates its own internal order; the transaction order is nevertheless inverted.

There is also a tuple-lock inversion:

1. A deletes unreferenced candidate contact X and holds **C**.
2. B starts deleting another candidate contact Y. PostgreSQL locks Y before invoking the BEFORE ROW trigger; B then waits for **C**.
3. A deletes Y and waits for B’s tuple lock.

`ExecBRDeleteTriggers`/`ExecBRUpdateTriggers` obtain the tuple through `GetTupleForTrigger` before calling user triggers. Putting the advisory lock first inside PL/pgSQL does not put it before that tuple lock. [PostgreSQL trigger implementation](https://raw.githubusercontent.com/postgres/postgres/REL_17_STABLE/src/backend/commands/trigger.c).

These schedules cause transaction aborts rather than demonstrating committed corruption. They still falsify the claimed deadlock-free protocol.

**Isolation refusal is correct for the intended guard reads.** The helpers reject REPEATABLE READ and SERIALIZABLE before permitting mutations. The volatile PL/pgSQL guards issue their state queries after acquiring the lock, allowing fresh READ COMMITTED snapshots. This closes the identified stale-snapshot schedule, but does not repair either lock-ownership or lock-order defect. [PostgreSQL function snapshot behavior](https://www.postgresql.org/docs/17/xfunc-volatility.html).

**`4.0` isolation**

The original publication-path effect is removed. Legacy publication, republication and rollback no longer invoke an A5.1 trigger, and explicit sealing refuses `4.0` and `4.1`.

However, **“nothing on any existing table” is not accurate**:

- New foreign keys reference existing `charts` rows at **M1153:701**, **M1153:826**, **M1155:387** and **M1156:184**.
- The bridge references the existing, globally shared convention table at **M1153:802**.
- Record/window FKs reference existing coverage at **M1155:461** and **M1156:233**.

These FKs create referential dependencies and internal RI triggers on referenced tables. `charts` and the convention table are not generation-scoped; the PR’s claim that these references can touch only governed-generation rows is therefore incorrect.

FK creation also takes locks on referenced tables that can temporarily block legacy writes. PostgreSQL’s FK implementation uses `SHARE ROW EXCLUSIVE` on the referenced relation. The migration timeouts at **M1153:129** limit waiting/execution; they do not eliminate contention. [PostgreSQL FK implementation](https://raw.githubusercontent.com/postgres/postgres/REL_17_STABLE/src/backend/commands/tablecmds.c).

There is no top-level legacy business-data rewrite here. The retained dependencies do not justify restoring the removed publication trigger, but they must be disclosed accurately.

**Deploy consequence**

**The intended refusal is loud and correctly prevents routine application of this family.**

At **MT:146**, pending protected files produce an actionable instruction to dispatch `gochara_contracts_schema_migration=true`. The check occurs before that file’s `BEGIN` and SQL execution at **MT:798**. The CLI exits unsuccessfully at **MT:879**, and dependent deployment jobs require successful migration completion—for example **DY:1243**.

The protected job selects 1153–1157 at **DY:1056**, invokes `--only` at **DY:1067**, and schedules capability revocation with `always()` at **DY:1069**. `--only` also refuses unapplied predecessors at **MT:747**.

**The atomicity claim needs qualification:**

| Situation | Actual consequence |
|---|---|
| Routine runner encounters pending 1153 | None of 1153–1157 is applied by that invocation. |
| Earlier migrations are also pending | Those can commit before the runner reaches and refuses 1153. |
| Tracker maintenance is required | Tracker DDL/backfill occurs before refusal: **MT:733**, **MT:777**. |
| Protected window fails in 1156 | 1153–1155 remain committed; 1156 rolls back; 1157 is not attempted. |

I confirmed these control-flow distinctions using the actual runner with synthetic in-memory files and a fake client. No SQL reached a database.

Per-file SQL plus ledger atomicity remains correct at **MT:822**. The five-file window is not one transaction. This is the previously accepted runner model, not grounds to demand a family-wide transaction now. Nevertheless, the PR must distinguish “routine refusal applies none of this family” from “the deployment changes nothing” and from “a protected-window failure cannot leave a partial family.”

**New defects**

**N14 — P1: The coverage digest loses distinctions before hashing.**

At **M1155:309**, the digest concatenates coalesced bounds, inclusivity flags and comma-joined relation values.

For otherwise identical inputs:

| Different coverage facts | Identical serialized component |
|---|---|
| Fully unbounded horizon `(,)` versus `empty` | Both bounds become empty strings; both inclusivity flags become `()`. |
| `ARRAY['conjunction']` versus `ARRAY['conjunction', NULL]` | `string_agg` discards the NULL. |
| `ARRAY['aspect','conjunction']` versus `ARRAY['aspect,conjunction']` | Both become `aspect,conjunction`. |

The inherited table permits these range/array shapes: [1081:234](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2765d/platform/migrations/1081_nirmana_l3_gochara_ledger_coverage_publication.sql:234).

PostgreSQL returns NULL bounds for empty and unbounded ranges, and false inclusivity for empty ranges; `string_agg` omits NULL inputs. [Range functions](https://www.postgresql.org/docs/17/functions-range.html), [aggregate functions](https://www.postgresql.org/docs/17/functions-aggregate.html).

Thus a parent can change from covering everything to covering nothing without changing the digest. These are serialization collisions; replacing MD5 with a stronger hash alone would not fix them.

**Residual N10 — write-time comparison is not continuing coverage validation.**

The ruling permits a digest instead of legacy-table triggers. That alternative still needs a sound consumer contract.

Currently, **M1155:601** and **M1156:317** compare the digest only during child INSERT/UPDATE. The FKs bind partition identity alone. Explicit sealing at **M1153:757** does not revalidate coverage, and the original validated facts are not retained as an immutable version.

A transaction can therefore insert a valid child, change the parent’s non-key coverage facts, seal the generation and commit. For noncolliding changes the stored digest can reveal staleness only if a subsequent consumer actually compares it. That continuing comparison remains an unimplemented acceptance obligation in the reviewed code. N14 defeats even such a future comparison for the demonstrated inputs.

Window applicability also remains incomplete. **M1156:303** checks the class partition and horizon, while membership FKs at **M1156:274** bind chart/generation/class/path. Nothing checks that the window partition’s searched relations or convention cover its contributing records. A conjunction record validated against body-target coverage can be attached to a same-class window whose class partition searched only aspects.

**N15 — P1: Coverage extension can prevent required in-place enrichment.**

A concrete permitted sequence is:

1. Create a truncated contact and dependent record; seal the generation.
2. Extend that coverage partition’s `completed_horizon`.
3. Enrich the contact with its newly solved centre and precision.

The contact AFTER trigger updates dependent precision at **M1155:741**. The sealed-row precision exception permits this, but the subsequent coverage guard recomputes the digest from the extended parent and rejects the record’s old digest at **M1155:602**. The contact enrichment consequently rolls back.

Changing the sealed record’s digest is itself prohibited by **M1155:369**, which allows only precision changes. Reversing statement order merely leaves a stale digest after the parent changes.

This conflicts with the required partition-extension enrichment at **S:626** and **S:638**. **DBT:1107** tests enrichment without first extending the coverage parent, so it misses this interaction.

**Ranked merge-blocking amendments**

1. **P1 — Resolve scheduler/worker lock ownership, N12.** Reconcile the binding lock ruling with the frozen runner’s separate connections before making these migrations permanent. Demonstrate that an actual dispatched worker can finish while unrelated writers remain excluded. Same-session reentrancy is not sufficient evidence.

2. **P1 — Establish ordering across complete transactions and PostgreSQL tuple locks, N13/N2.** Cover global-then-chart statements and concurrent UPDATE/DELETE entry. Trigger-local ordering and isolated lock-blocking tests do not establish this.

3. **P1 — Complete the digest-based coverage contract, N10/N14.** Use an unambiguous encoding that distinguishes empty/unbounded ranges and array elements. Define and enforce how consumers handle changed parent facts, and verify coverage applicability to window contributors. Keep this within the steward’s prohibition on legacy-table triggers.

4. **P1 — Preserve enrichment after real partition extension, N7/N15.** Test extend-then-enrich with dependent records in a sealed generation. Precision synchronization and coverage binding must remain compatible without rewriting published evidence indiscriminately.

5. **P2 — Correct operational assertions and matching tests.** Remove claims of zero existing-table effects, zero-write routine refusal and unconditional family atomicity. Document predecessor requirements, retained FK effects and partial-window recovery under immutable migration hashes.

**What I could not verify**

- I did not execute migrations, PostgreSQL concurrency schedules, the integration suite or the protected workflow.
- Production ownership, privileges, ledger contents, lock durations, environment approvals and successful capability revocation remain unverified.
- The PR’s reported PostgreSQL 15/17 and 1,028-test results are author-reported, not independently reproduced here.
- I could not establish that these migration numbers have never been applied anywhere.
- Independently completed checks were file/commit correspondence, five preflight-block comparisons, the 27 connection-free URL cases, and migration-runner control flow through an in-memory fake client. Those checks do not constitute database or deployment acceptance.