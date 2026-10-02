---
artifact: ASTRA_REVIEW_A5_1_MIGRATIONS
version: "1.2"
reviewer: "Codex gpt-6-astra"
date: "2026-09-30"
verdict: REJECT
reviewed_commit: ad4f658ab
authority: "Review only; authorizes nothing."
---

**Verdict: REJECT**

The rewrite closes several exact round-2 defects, but it is not safe to merge. The publication trigger affects live `4.0` operations, publication and rule sealing remain vulnerable to concurrency, and several constraints can still be bypassed through ordinary permitted writes. The deployment workflow also lacks an application route compatible with its protected-schema privilege policy.

All 14 migration, preflight and test files reviewed match HEAD `ad4f658abf42d8c6124753f1698ab536d4887238`. No files were written, no git write commands were run, no database was contacted, and neither prohibited directory was accessed.

“CLOSED” below means closed at source-review level. SQL counterexamples are reasoned from the implementation; they were not executed against PostgreSQL.

Evidence abbreviations:

- **S:** [frozen specification](/Users/Dev/madhav-l3/pravaha/00_ARCHITECTURE/briefs/pravaha/design/GOCHARA_DESIGN_SPECS_v1_4.md). **R2:** [round-2 review](/Users/Dev/madhav-l3/pravaha/00_ARCHITECTURE/briefs/pravaha/reviews/ASTRA_REVIEW_A5_1_MIGRATIONS_v1_1.md).
- **M1153:** [sky-event substrate migration](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2765c/platform/migrations/1153_gochara_sky_event_substrate.sql).
- **M1154:** [rule-path registry migration](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2765c/platform/migrations/1154_gochara_rule_path_registry.sql).
- **M1155:** [relationship-record migration](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2765c/platform/migrations/1155_gochara_relationship_record.sql).
- **M1156:** [evaluation-window migration](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2765c/platform/migrations/1156_gochara_eval_window.sql).
- **M1157:** [AV-polarity migration](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2765c/platform/migrations/1157_gochara_av_polarity_declaration.sql).
- **DBT:** [database tests](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2765c/platform/tests/integration/gochara_a5_1_migrations.db.test.ts). **URL:** [disposable-database guard](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2765c/platform/tests/integration/gochara_a5_1_disposable_url.ts).

**Closure table**

| Finding | Judgment | Constraint evidence and remaining gap |
|---|---|---|
| **F1 — identity versus generation ownership** | **CLOSED** | Global identity uniqueness at **M1153:785–803**, generation-scoped ledger PK/FKs at **1007–1026**, and the six-column record FK at **M1155:406–411** genuinely reject the former ownership contradictions. **DBT:840–866** includes a direct FK rejection with the coverage guard disabled. Different solved readings under the same identity remain a separate F4 defect, N6. |
| **F2 — permanent publication protection, concurrency, TRUNCATE** | **PARTLY CLOSED** | Permanent seals, retirement protection and unconditional TRUNCATE triggers are real: **M1153:861–948, 1066–1118**; **DBT:882–956**. However, the trigger reaches `4.0`, the locking protocol is incomplete, and published window membership remains extensible. See N1, N2 and N9. |
| **F3 — complete rule-version immutability** | **PARTLY CLOSED** | Seals and membership INSERT guards reject sequential additions after sealing: **M1154:499–575**, **DBT:959–979**. Membership insertion and sealing do not synchronize, so concurrent additions can commit after a version becomes sealed and usable. N5. |
| **F4 — correction identity and enrichment** | **PARTLY CLOSED** | `correction_seq` is removed; target/convention-changing supersession is supported; only the clipped placeholder can change method during enrichment: **M1153:785–844, 1077–1105**, **DBT:980–1020**. But another generation can INSERT a changed solved reading under the same contact ID, and legitimate enrichment can invalidate existing record precision. N6–N7. |
| **F5 — NULL validators and qualification consistency** | **PARTLY CLOSED** | The original NULL bypasses are rejected through `IS TRUE`; deferred qualification checks enforce ordinary insert/result-update/delete cases: **M1154:199–210; M1155:277–292, 441, 637–694, 711–728**; **DBT:1044–1090**. Moving a prerequisite to another record checks only the destination, leaving the source invalid. N8. |
| **F6 — C2 factor contract** | **CLOSED** | **M1154:352, 370–388** enforces valid mandatory calibration status, finite ordered bounds within `[0,1]`, and calibrated ⇒ mapping. Uncalibrated authored mappings and continuous factors without category ordering are accepted. **DBT:1093–1102** tests the corrected boundary. |
| **F7 — relation, membership and coverage consistency** | **PARTLY CLOSED** | Relation-exact FKs and window class/path/version FKs are real: **M1153:596, 640, 1011–1013; M1155:406–411; M1156:286–293**. Coverage applicability still has a NULL-array bypass, incomplete target/window checks, and mutable-parent invalidation. N10. |
| **F8 — function signature matching** | **CLOSED** | Gates use argument type identities rather than parameter-name-bearing text: **M1153:286–300; M1155:230–239**. The named-parameter collision case at **DBT:700–709** addresses the original defect. |
| **F9 — effective gates, schema resolution, definition verification** | **PARTLY CLOSED** | All five embedded gates are byte-identical to their standalone preflights. Creation/reference schemas are substantially pinned, and verification now checks actual catalog definitions. But the deployment privilege route is missing, the normalizer admits semantically different CHECKs, and replay mutates before establishing equivalence. N3–N4. |
| **F10 — destructive-test target validation** | **PARTLY CLOSED** | Parsing the pathname rejects the original misleading-token cases. However, the guard and PostgreSQL driver disagree about the effective host and, for doubled slashes, database name. These bypasses were confirmed without connecting. N11. |
| **F11 — selectors, finite values, AV categories, fact-resolution disposition** | **CLOSED** | Token encoding, finite/nonnegative quantities and nonempty AV-category elements are enforced: **M1154:218–268; M1153:383–398, 669–673, 1043–1045; M1155:453–456, 471–478; M1156:235–240; M1157:138–144**. The explicit writer-boundary disposition at **M1155:85–93** is acceptable for this migration scope. Actual fact resolution remains an unverified downstream obligation. |

Disposition of the **nine ranked amendments in R2:169–181**:

| R2 rank | Subject | Judgment |
|---|---|---|
| 1 | F1–F2: scoped identity and permanent publication protection | **PARTLY CLOSED** — F1 closed; N1/N2/N9 remain. |
| 2 | F8–F9: ordered application and definition verification | **PARTLY CLOSED** — F8 closed; N3/N4 remain. |
| 3 | F3: complete rule-version immutability | **PARTLY CLOSED** — N5. |
| 4 | F4: correction and enrichment | **PARTLY CLOSED** — N6/N7. |
| 5 | F5: validators and final qualification | **PARTLY CLOSED** — NULL cases closed; N8 remains. |
| 6 | F6: remove unauthorized factor restrictions | **CLOSED**. |
| 7 | F7: applicable coverage and consistent references | **PARTLY CLOSED** — N10. |
| 8 | F10: destructive-test boundary | **PARTLY CLOSED** — N11. |
| 9 | F11: typed values and fact-resolution disposition | **CLOSED** at migration scope. |

For the separately numbered round-1 amendments, **#2 and #3 remain CLOSED**. The runner still owns each migration’s DDL-and-ledger transaction, and mandatory versioned FKs remain intact. The expanded failure tests now individually target all five migrations and check their tables and standalone functions—**DBT:1230–1267**. Round-1 **#7 and #9 are now CLOSED at schema/disposition scope**; **#1, #4, #5, #6 and #8 remain PARTLY CLOSED**.

The [PR body’s §3](https://github.com/Marsys-Technologies/Madhav/pull/2765) receives these judgments:

- **F4:** Restoring the frozen hash and representing a same-target/ordinal correction through a new convention is compatible with **S:615–649, 702–703**. The statement that every corrected reading *is* a method change is an implementation interpretation, rather than text supplied by §7.2. No extra hash component is required. Nevertheless, the claimed impossibility of a same-ID changed reading is false in this schema—N6.
- **F6:** Justified. The implementation now follows C2 and the binding narrowing.
- **F7:** Justified for the four-kind domain. Migration **1087:81–104** explicitly establishes `bodies_on_demand`; S does not supply a competing closed enum for these inherited partition keys. This does not establish applicability of an individual partition.
- **F11:** Justified as a disposition. **S:107** permits heterogeneous fact/extract identifiers and fixture rows. The comment establishes a future writer obligation; it does not prove that obligation has been implemented or passed.

**Publication-trigger assessment**

**N1 — P1: The trigger is not isolated from live `4.0`. Merge-blocking.**

**M1153:928–931** fires after every qualifying INSERT or status UPDATE where `NEW.status = 'published'`. It has no generation guard and no requirement that the old status differ.

Consequently, a `4.0` publication or direct `published → published` status assignment enters:

1. The seal INSERT at **915–921**.
2. The advisory lock and manifest lookup at **880–894**.
3. New table permissions, constraint enforcement and persistent seal storage.

The trigger function is ordinary invoker-security PL/pgSQL. A caller that can update the legacy manifest but cannot perform the new seal operations can now fail its original publication statement. Contention can delay it; errors in the new path abort it. The migration’s `SET LOCAL` timeouts do **not** bound later application transactions.

Applying the migration does not backfill the already-published `4.0` row. The existing publisher also returns early when it finds an already-published manifest. Those narrower cases do not establish isolation for subsequent status writes.

Rollback requires a precise distinction:

- The existing rollback’s `status = 'rolled_back'` UPDATE does **not** satisfy the trigger’s WHEN condition.
- The normal rollback retains the manifest, so the new seal-to-manifest FK does not, by itself, block that operation.
- Once a seal exists, deleting its manifest is newly prohibited. New record/window coverage FKs can also block legacy coverage deletion if new-contract rows are allowed to reference a `4.0` scope.

The existing rollback deletes coverage and contacts before changing status—[ledger.py:595–625](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2765c/platform/python-sidecar/services/gochara_kernel/ledger.py:595).

**Required:** identify generations governed by the new contract and bypass `4.0` before any seal write or advisory lock. Define candidate-only `4.1` treatment explicitly. A lexical comparison such as `generation >= '5.0'` is insufficient for version ordering. Verify actual legacy publication and rollback paths using their runtime role.

**N2 — P1: The advisory lock does not establish a complete publication/rebuild protocol.**

There are three distinct gaps:

- **Repeatable Read bypass.** Transaction A establishes a Repeatable Read snapshot while the generation is candidate. B publishes and commits. A subsequently deletes an otherwise unreferenced contact. Its guard acquires the advisory lock, but its queries can still see the old candidate manifest and no seal. B did not modify that contact row, so there is no necessary row-update serialization failure. **M1153:935–946, 1070–1075** therefore permits the deletion under this schedule. Advisory locking does not refresh a Repeatable Read snapshot. [PostgreSQL isolation documentation](https://www.postgresql.org/docs/16/transaction-iso.html).
- **Lock-order inversion.** A candidate transaction deletes a contact and holds the advisory lock. B updates the manifest, holds its row lock, then waits for A’s advisory lock inside the AFTER trigger. A subsequently updates candidate manifest metadata and waits for B’s row lock. This creates a deadlock. The current tests commit A immediately after deletion and never exercise this ordering.
- **Publication content is read before the lock.** An AFTER status trigger cannot protect digest/count reads already performed by its caller. The existing publisher calculates those before its status UPDATE—**ledger.py:541–575**. The tests demonstrate waiting around a deletion and a status assignment, not an atomic content snapshot, rebuild and publication.

Row-trigger locking also does not cover a delete that affects zero rows; permitted INSERTs and contact enrichment do not take the same generation lock.

**DBT:921–956** exercises two useful default-isolation schedules, but does not close these gaps. Establish one lock order at the publication/rebuild entry boundary, protect the content being certified, and either support or explicitly reject unsupported transaction isolation levels.

**Production application**

**N3 — P1: The committed deployment workflow cannot apply these under its normal protected-schema state.**

The gate correctly requires schema CREATE—**M1153:210–211**, with equivalent checks in the remaining migrations. However:

- [deploy.yml:933–938](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2765c/.github/workflows/deploy.yml:933) states that the ordinary role has USAGE without CREATE.
- Its protected capability job applies only the exact migrations listed at **1033–1044**. **1153–1157 are absent.**
- That capability is revoked at **1053–1057**, before the routine runner invoked at **1186–1195**.
- The ownership attestation explicitly rejects durable CREATE for `amjis_app`—[data-plane-ownership-status.ts:559–570](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2765c/platform/scripts/data-plane-ownership-status.ts:559).

Thus the intended strict deployment state leads to `no_create_privilege_on_public` when the routine runner reaches 1153. Embedding the preflight fixes bypass, but does not supply the required protected application route. The remedy must use the established temporary capability mechanism or another explicitly governed route; permanently widening the ordinary role would contradict the existing attestation.

**Lock footprint is broader than “one touch to an existing table.”**

The new foreign keys reference existing `charts`, `kala_gochara_convention`, `kala_gochara_publication` and `kala_gochara_coverage`. Creating these FKs acquires `SHARE ROW EXCLUSIVE` locks on referenced tables; these conflict with ordinary writes. Creating the publication trigger also takes that lock class. Locks remain until the migration transaction ends. [PostgreSQL FK implementation](https://raw.githubusercontent.com/postgres/postgres/REL_16_STABLE/src/backend/commands/tablecmds.c), [locking documentation](https://www.postgresql.org/docs/16/explicit-locking.html).

On deliberate replay, dropping the **existing** publication trigger at **M1153:927** takes `ACCESS EXCLUSIVE`, blocking reads as well as writes. This stronger-lock statement concerns an existing trigger; it should not be attributed to the absent-trigger fresh-application case. [PostgreSQL trigger-deletion implementation](https://raw.githubusercontent.com/postgres/postgres/REL_16_STABLE/src/backend/commands/trigger.c).

The five-second lock timeout and 120-second statement timeout are useful limits—**M1153:192–194**, repeated in each file—but do not make application lock-free or cap the entire transaction at five seconds.

The migrations contain no top-level business-data rewrite. Each file and its ledger insertion remain atomic through [migrate.ts:791–803](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2765c/platform/scripts/migrate.ts:791). The five-file family is **not** one transaction: failure in a later file leaves earlier migrations, including 1153’s publication trigger, committed.

**N4 — P1: The verifier can accept different semantics; deliberate replay is mutating reconciliation.**

The verifier is substantially stronger than round 2, but **M1153:407–415** strips every parenthesis and whitespace character, lowercases literals, and removes casts. This destroys information required to distinguish expressions.

These two CHECKs produce the same stored fingerprint:

```sql
CHECK (t_exact IS NULL OR
       (t_in <= t_exact AND (t_out IS NULL OR t_exact <= t_out)))

CHECK (((t_exact IS NULL OR t_in <= t_exact) AND t_out IS NULL)
       OR t_exact <= t_out)
```

The first is the required **`kgc_time_order_ck` at M1153:1046–1048**. The second accepts a non-NULL exact time before `t_in`, provided it is before `t_out`.

An in-memory check confirmed that both flatten to the actual embedded expected fingerprint. `IF NOT EXISTS` preserves the wrong CHECK during replay, so this is an actual verifier escape, not merely a theoretical weakness in text comparison.

Other omitted properties include:

- Column defaults, generated/identity properties: **435–439**.
- Index validity/readiness: **453–457**.
- Function bodies and function `search_path` configuration: **468–472**.

The GUC at **M1153:199** recognizes an effective setting of `on`; it does not distinguish a deliberate transaction-local request from an inherited session setting. It skips collision/already-applied checks, then executes `OR REPLACE` and trigger DROP/CREATE before verification. Drifted functions/triggers can therefore be replaced before their previous state is assessed.

The GUC does not grant DDL privileges. Its hazard is weakening collision protection and presenting mutation as equivalent replay. Equivalence must be established with semantics-preserving comparison before mutation, or replay must be explicitly classified and controlled as repair.

**New defects**

**N5 — P1: Rule sealing races with membership insertion.**

**M1154:517–527** performs a plain seal-existence query. The seal table at **499–507** has no corresponding serialization protocol.

A valid concurrent schedule is:

1. A inserts a prerequisite or factor membership while no committed seal exists.
2. B inserts the seal, produces records against the membership visible to B, and commits.
3. A commits its membership addition.

The sealed, potentially used rule version has changed. The shared parent FKs do not prevent this schedule. The inverse ordering, with an uncommitted seal invisible to A, has the same issue.

**DBT:959–979** checks only already-committed seals. Both membership construction and seal creation must participate in a concurrency-safe completion boundary.

**N6 — P1: A published contact can acquire a changed solved reading under the same ID in another generation.**

Solved values reside in the generation-scoped ledger—**M1153:994–1007**. Its identity FK binds only ID/object/ordinal, and its object FK binds the physical tuple—**1008–1013**. Neither binds solved values across generations.

After publishing contact C with exact time T in generation G1, insert C into candidate G2 with exact time T′, retaining the same object, convention and ordinal and supplying valid local intervals/precision. All declared FKs and CHECKs can pass. The lifecycle trigger covers only UPDATE/DELETE—**1111–1114**.

This contradicts **S:641–646** and the migration’s own claim at **75–84** that a same-tuple changed reading is unrepresentable. **DBT:980–1020** tests UPDATE rejection and new correction identities, but not this INSERT path.

Enforce consistency of already-published non-NULL physical readings across every ownership row sharing the identity, while retaining legitimate generation coexistence and NULL enrichment.

**N7 — P1: Permitted contact enrichment invalidates dependent record precision.**

A record’s precision is checked against its contact only when the record is inserted or updated—**M1155:589–617, 702–705**.

A contact can subsequently change from clipped/null precision to solved precision through the permitted enrichment path—**M1153:1077–1105**. Existing records retain their old clipped payload. No contact-side trigger revalidates or updates them. If the generation is sealed, the record guard then refuses the UPDATE needed to reconcile them—**M1155:307–317**.

The result is a permitted, committed state that violates the claimed restatement invariant. The enrichment test at **DBT:980–999** does not include a dependent record.

Preserve the frozen requirement for in-place enrichment, while defining and enforcing how dependent precision remains consistent.

**N8 — P1: Prerequisite reassignment bypasses qualification finalization.**

The finalizer selects **OLD.record_id only for DELETE; otherwise NEW.record_id**—**M1155:647**. Membership ownership is mutable in a candidate generation—**511–534, 720–728**.

Starting with valid candidate record R1:

1. Insert R2 with the same path/version and a different valid natural key.
2. Move R1’s prerequisite rows to R2 using UPDATE of `record_id`.
3. Commit.

R2’s deferred checks pass. R1 receives no record UPDATE and no prerequisite DELETE event; its now-missing prerequisites are never checked. R1 can remain `admitted` without its declared necessary predicates.

Revalidate both old and new owners on reassignment, or prohibit membership identity reassignment. **DBT:1060–1088** does not test this case.

**N9 — P1: INSERT can alter an already-published window’s record list.**

**M1156:354–357** guards membership UPDATE/DELETE only. A new `(window_id, record_id)` membership linking an existing published window to another matching record passes the six-column FKs.

This changes the existing window’s logical `record_ids` and contributing evidence set while its stored score and other values remain frozen. Adding a new window during an authorized partition extension does not require permitting additions to an already-published window’s membership.

There is also no destination-scope check in the generic UPDATE guard: **M1155:310** checks only OLD ownership. Any permitted reassignment must validate both sides.

**N10 — P1: Coverage checks are incomplete and can be invalidated after they pass.**

Three concrete gaps remain:

- **NULL-array escape:** **M1155:585** uses `IF NOT (relation = ANY(...))`. With `relations_searched = ARRAY['aspect', NULL]`, a conjunction comparison yields SQL NULL, so the exception is skipped. The inherited parent permits NULL array elements—**1081:237**. Require the membership predicate to be `IS TRUE`.
- **Incomplete applicability:** body-target coverage checks only the key’s leading body—**M1155:573–576**—and never validates its target suffix. Windows using non-event-class coverage receive only a horizon check—**M1156:314–329**—without establishing applicability to their contributing records.
- **Mutable parents:** coverage convention, searched relations and completed horizon can be changed after a child passes its guard. Even one transaction can insert a valid record/window, change those non-key coverage fields, and commit. The FKs bind only partition identity; no reviewed mechanism rechecks affected children. Contact enrichment creates the analogous precision problem in N7.

The seal has a related correspondence weakness: its FK binds only `manifest_id`—**M1153:864**—while chart/generation agreement is checked only on INSERT. Later reassignment of those manifest fields can invalidate that claimed correspondence.

The claimed relation-negative test is also insufficient: **DBT:1112** supplies a Mars record with a Saturn partition and accepts either a body or relation error. It can pass without exercising the relation guard.

Protect the relevant parent facts or bind consumers to immutable versions, with explicit isolation from legacy `4.0` behavior.

**N11 — P1: The destructive-test guard validates a different target from the driver.**

**URL:42–54** checks WHATWG URL hostname and a pathname with **all** leading slashes removed. The database suite then gives the original connection string to node-postgres before executing the destructive reset—**DBT:285–310, 659–663**.

Using the real helper and the locked `pg-connection-string` version **2.12.0**, an in-memory, connection-free check produced:

| Input | Guard | Driver interpretation |
|---|---|---|
| `postgresql://127.0.0.1/gochara_a51_test?host=db.example.com` | Accepted | Remote host `db.example.com` |
| `postgresql://127.0.0.1//gochara_a51_test` | Accepted | Database `/gochara_a51_test` |

The driver honors the query-string host override; its database-path handling also differs from the guard. [node-postgres parser source](https://raw.githubusercontent.com/brianc/node-postgres/master/packages/pg-connection-string/index.js).

Empty-host URLs are additionally accepted without pinning the effective host configuration. The suite drops `charts`, publication, coverage and the migration ledger with CASCADE. Validate and then use the same fully resolved connection configuration; reject target-changing options and ambiguous/default-dependent targets.

**Ranked merge-blocking amendments**

| Rank | Priority | Required amendment and negative proof |
|---|---|---|
| **1** | **P1** | **N1: Isolate live `4.0`.** Guard new publication behavior by the governed generation contract. Exercise real legacy publish, repeated status assignment and rollback with the runtime role; prove no new seal write, advisory-lock dependency or unintended deletion restriction. |
| **2** | **P1** | **N3: Supply a valid deployment route.** Integrate 1153–1157 with the protected capability mechanism and preserve its revocation/attestation rules. Rehearse with the actual normalized role model, not only an owner-capable fixture. Document existing-table locks and partial-family failure behavior. |
| **3** | **P1** | **N2/N9: Complete publication immutability.** Establish consistent lock ordering before publication content reads and rebuild operations; handle isolation levels explicitly; freeze existing window membership. Reject stale-snapshot deletion, manifest/advisory-lock inversion and post-publication membership additions. |
| **4** | **P1** | **N5: Serialize rule completion.** Make seal creation and membership construction mutually safe. Test overlapping transactions in both orders, including record production before the membership transaction commits. |
| **5** | **P1** | **N6/N7: Enforce correction identity and coherent enrichment.** Reject changed published readings inserted under the same ID in another generation. Preserve allowed enrichment with consistent dependent records, including sealed-generation cases. |
| **6** | **P1** | **N8: Close qualification reassignment.** Revalidate both owners or prohibit membership reparenting. Test moving a complete prerequisite set from an existing valid record to a newly inserted record. |
| **7** | **P1** | **N10: Complete coverage lineage.** Reject NULL-array membership uncertainty; establish target/window applicability; prevent parent changes from invalidating children. Add isolated negative cases that cannot fail earlier for another reason. |
| **8** | **P1** | **N4: Repair definition verification and replay semantics.** Preserve expression grouping, literals and casts; verify required defaults/function properties. Reject the demonstrated same-fingerprint CHECK mutation. Establish equivalence before replacement and control ambient replay settings. |
| **9** | **P1** | **N11: Repair the destructive-test target boundary before rerunning it.** Validate the driver’s effective configuration and reject host overrides, doubled-path ambiguity and uncontrolled defaults. Keep these tests connection-free. |

**What I could not verify**

- No PostgreSQL execution occurred. Fresh application, rollback, replay, runtime privileges, lock durations and the SQL concurrency counterexamples remain unverified experimentally.
- Neither Vitest suite was run. The [PR-reported results](https://github.com/Marsys-Technologies/Madhav/pull/2765)—42 database tests on PostgreSQL 17.10/15.17 and 840 unit tests—are author-reported results, not independent execution evidence from this review.
- The reviewed database fixture now uses real migrations 1081/1087/1152, which improves round-2 coverage, but `charts` remains a key-shape stub. It does not reproduce the full production privilege and deployment state.
- **DBT:909–912 does not test a pre-migration published generation without a seal:** its publication UPDATE creates a seal, and its subsequent `DELETE ... WHERE false` removes nothing. There is no demonstrated live-`4.0` compatibility test.
- Production catalog definitions, ACLs, applied migration hashes, runtime isolation settings and migration-number reservations were not inspected. The statement that 1153–1157 have never been applied remains a supplied assumption.
- The 57 frozen oracles, deterministic identity hashing, writer-side fact resolution and later evaluator obligations were not executed. Declaring these obligations does not satisfy A5.5 acceptance.

Read-only checks confirmed the 14 reviewed files match HEAD, all five embedded preflight blocks match their standalone counterparts, and the two connection-target bypasses and CHECK-fingerprint collision exist in pure in-memory checks.

Frozen input hashes remain:

```text
S  d5097ca18a721d8005cab593f3c3865227d22ff1435b8adc9973275d3f786a47
O  19951b06ce672ac4cff82d74fb6c7bb7babe4315582ec1c142a0a7871752c277
```