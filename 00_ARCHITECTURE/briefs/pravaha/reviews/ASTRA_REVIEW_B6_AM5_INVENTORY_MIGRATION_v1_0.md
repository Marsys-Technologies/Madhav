---
artifact: ASTRA_REVIEW_B6_AM5_INVENTORY_MIGRATION
version: "1.0"
reviewer: "Codex gpt-6-astra"
date: "2026-10-02"
verdict: REJECT
reviewed_commit: edece78c9
authority: "Review only; authorizes nothing."
---

**Verdict: REJECT.** The migration contains a structural completeness bypass, an unbound convention identity, and two input-validation defects. Its protected-window wiring is sound at source level, but the database tests do not establish the claimed role and concurrency guarantees.

This review covers 1206 and its wiring. Acceptance of 1204 is unchanged. I compared AM-5 v0.5/v0.6 and its executable evidence using the locally available campaign commit `f301e0dd55a67bd7f7d41bed84b981deba07f7fd`. I did not fetch, because that would violate the read-only instruction.

**1. Fidelity to AM-5**

The implementation correctly establishes much of the intended structure: one snapshot per chart/generation, input-bound inventories and intervals, finalized commitments, per-obligation interval-union coverage, refusal of `missing_inputs`, and a separate replay branch that avoids rechecking the advanced registry.

Four defects prevent acceptance:

**R1 — P1: commitment equality is not checked within the owning path/version.**  
The “committed but not stored” branch searches by `(chart, generation, event_class, ob_id)` and omits `path_id` and `rule_version`. Its diagnostic repeats the omission. The reverse branch does scope obligations to their owning path/version. Consequently, another path’s obligations can satisfy an included path’s entire commitment. See [the commitment check](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2867a/platform/migrations/1206_gochara_search_inventory_completeness.sql:714).

This violates AM-5’s explicit structural promise that each pin’s committed set equals that pin’s stored obligations. It is distinct from the acknowledged trust in an independent verifier’s doctrinal derivation.

**R2 — P1: snapshot convention is not bound to the published coverage convention.**  
The snapshot references an existing sky convention. The publication comparison checks the input vector and horizon; the partition comparison checks horizon and relations. Neither resolves the publication/partition’s legacy convention through `ka_gochara_convention_bridge` and compares it with the snapshot’s convention. See [publication selection](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2867a/platform/migrations/1206_gochara_search_inventory_completeness.sql:642) and [partition validation](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2867a/platform/migrations/1206_gochara_search_inventory_completeness.sql:758).

A fully searched inventory under sky convention A can therefore support advertised coverage under legacy convention B, bridged to a different sky convention. With no records/windows, the existing consumer guards have nothing to inspect. This permits a false complete-empty claim even when the verifier correctly derives the inventory under A.

**R3 — P2: an excluded pin can have no exclusion reason.**  
`exclusion_reason` is nullable. For `disposition='excluded'` and a NULL reason, both the reason-domain check and the ruling-reference equivalence can evaluate to NULL, which PostgreSQL accepts as satisfying a CHECK. A valid basis and empty commitment do not repair the missing reason. See [the exclusion constraints](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2867a/platform/migrations/1206_gochara_search_inventory_completeness.sql:337). This follows PostgreSQL’s documented [CHECK semantics](https://www.postgresql.org/docs/17/ddl-constraints.html).

Require an explicit non-NULL reason for excluded pins, then enforce the closed vocabulary and ruling requirement without nullable boolean escape paths.

**R4 — P2: live-input digests are session-dependent and exclude the wrong L1 audit column.**  
The L1 helper hashes `to_jsonb(f) - 'created_at'`, whereas the actual `chart_facts` schema contains `computed_at`. The dasha helper removes `computed_at` but leaves material `timestamptz` columns rendered through `to_jsonb`. Neither helper fixes the session timezone. See [the digest helpers](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2867a/platform/migrations/1206_gochara_search_inventory_completeness.sql:198) and [the actual L1 schema](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2867a/platform/supabase/migrations/204_chart_facts.sql:10).

Thus unchanged rows can hash differently when snapshot construction and sealing use different timezones. PostgreSQL renders timestamp-with-time-zone values using the session timezone; the inventory’s separate UTC formatter does not normalize these row JSON values. See [timestamp behavior](https://www.postgresql.org/docs/17/datatype-datetime.html).

There are also two narrower departures from the text:

- Verification requires **every** verification row to match, whereas AM-5 specifies at least one matching independent verification. This is conservatively stronger; a stale negative row vetoes sealing until removed.
- An empty ledger hashes the empty string, so its digest does not change with the input snapshot. Inventory binding remains, but the universal claim that both completion digests change needs correction or an input-bound empty-ledger preimage.

**2. Migration safety, ordering, locks, and cost**

Source-level additivity is satisfactory. I verified six new tables and seventeen functions, with no function-name replacement against 1153–1157. Those applied migration files are byte-identical to the inspected `origin/main` commit `2992093bc9626e0289ad570c569a17e7883d4953`. The only new trigger on an existing family table is `ka_gochara_generation_seal_z_search_complete`.

The existing `..._write_guard` runs before `..._z_search_complete`, consistent with PostgreSQL’s [alphabetical ordering of otherwise equivalent triggers](https://www.postgresql.org/docs/17/sql-createtrigger.html). Existing manifest, coverage-drift, and membership checks remain in force.

Idempotence needs precise wording:

- **Migration-runner replay:** supported by the applied-migration ledger and hash check.
- **Executing the SQL file twice directly:** deliberately rejected by the preflight/table existence checks; it is not independently idempotent.
- **Sealed-generation replay:** the new branch correctly checks stored integrity and manifest identity without requiring pins for newly sealed registry versions. The existing seal guard still runs first, so replay remains subject to its published-manifest and consumer checks.

The new guards use the existing chart-family EXCLUSIVE lock before acquiring the global-family SHARED lock for registry-dependent operations. UPDATE/DELETE statement guards preserve acquisition before affected tuple locks. I found no new lock-order inversion in these paths.

The orchestrator’s main-connection session lock hashes the raw chart identifier; the Gochara contract uses the `gochara5:chart:` family prefix. The worker therefore does not deliberately reacquire the main connection’s lock key. That source-level distinction avoids the obvious self-deadlock, but is not a concurrency test.

Two obligations remain external to these triggers:

- The writer must acquire the chart-family lock **before** legacy publication/coverage writes, as AM-3 requires.
- The test suite must exercise competing registry/chart transactions and the main-connection/worker pattern. Checking transaction-local marker settings does not establish these properties.

Seal cost is substantial and data-dependent: registry accounting, commitment checks, interval unions, sorted digest construction, live L1/dasha/declaration hashing, and the existing consumer scans all execute while locks are held. Replay also recomputes digests. The dasha join casts the indexed UUID column to text, which warrants a realistic query-plan check. Migration-local `lock_timeout` and `statement_timeout` do not cap future seal calls.

**3. Adversarial row sets and legitimate completion**

I reran all **32 executable model cases** in memory. Their output was byte-identical to the committed expected output.

I also reconstructed **W2 exactly**, without the additional P6 exclusion used by the database fixture:

```text
Sealed registry: P1, P5a
Pins: P1 included; P5a included
Commitments: each path's own intended obligation IDs
Stored obligations: P1 only
Intervals: every stored obligation covers the full horizon
Partition: same horizon; exactly the stored obligations' relations
Digests: correctly recomputed from stored rows
Records/windows: empty
```

The model rejects this as `committed_set_mismatch`; the SQL predicate also rejects it by inspection.

The additional adversaries expose the following:

| Adversary | Result and evidence |
|---|---|
| **Cross-pin W2:** change P5a’s commitment to P1’s obligation IDs; retain no P5a obligations | The normative model rejects it. An executable evaluation of 1206’s predicate shape finds no commitment mismatch. All remaining completeness predicates can be satisfied. **R1** |
| Complete inventory under sky A; publication and partition under incompatible legacy B; no records/windows | No new predicate checks the convention correspondence, and existing consumer checks are vacuous. Source-derived bypass. **R2** |
| Excluded pin with NULL reason, with or without a ruling reference | The relevant boolean expressions yield NULL rather than FALSE. PostgreSQL CHECK semantics admit them. **R3** |
| Same real L1/dasha rows, snapshot and seal sessions using different timezones | Row serialization can change, producing false `input_snapshot_drift`. Source-derived false refusal. **R4** |

These are not claims of successful PostgreSQL executions during this review.

For R1, the minimal structural witness is:

```text
P1@v:  included, committed={a,b}, stored obligations={a@P1,b@P1}
P5a@v: included, committed={a,b}, stored obligations={}
```

Full intervals for `a,b`, exact partition relations, and recomputed inventory/verification digests satisfy the remaining new checks. SQL must reject this even if a purported verifier merely rehashes the adversarial rows—the same adversarial verification posture used to test W2.

I did not establish an unavoidable permanent refusal for an otherwise legitimate inventory. R4 causes false refusals; aligning serialization or rebuilding the candidate can recover. Similarly, the stronger all-verifications-match rule is recoverable because candidate verification rows remain deletable. These recovery possibilities do not make the defects acceptable.

**4. Ownership, builder privileges, and function security**

As wired, the protected migration runs as `amjis_app` with temporary public-schema creation capability. That migration principal should own the new objects and have the required authority over the existing seal table. `data_plane_builder` should remain a grantee, not their owner.

The [new grants](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2867a/platform/migrations/1206_gochara_search_inventory_completeness.sql:848) provide:

- SELECT/INSERT/DELETE on the six candidate-capable tables.
- UPDATE only on the inventory’s digest/finalization columns.
- SELECT on the existing generation-seal and AV-declaration tables.

They grant no schema CREATE, TRIGGER, TRUNCATE, or REFERENCES capability. Candidate DELETE and narrowly scoped finalization UPDATE are justified by this lifecycle; sealed-row guards must remain the enforcement boundary.

All seventeen functions use invoker security; there is no new SECURITY DEFINER escalation. Stateful functions pin `search_path` and qualify relation references. Some pure helpers do not explicitly pin it, so “all functions have pinned search paths” would overstate the source.

Function execution currently relies on PostgreSQL’s default PUBLIC EXECUTE behavior rather than explicit grants for these new functions. That default is documented in [CREATE FUNCTION](https://www.postgresql.org/docs/17/sql-createfunction.html); actual owner-specific default privileges still require verification.

The builder does **not** have a complete publication path:

- Migration 1216 deliberately withholds INSERT on the generation seal and AV declarations, and defers window writes.
- The invoker-security seal function does not bypass those omissions.
- Existing candidate contact/record replacement is also constrained by 1216’s insert-only grants.

Therefore, the builder can construct/finalize the new inventory under the intended existing read grants, but sealing needs a separately authorized principal or an explicitly completed writer authority design. Do not silently widen builder grants to resolve this.

No new SELECT grants are made to `data_plane_verifier`. The independent verifier’s runtime principal must be specified; its independence is not established by the verification table’s name. The new tests never switch to `data_plane_builder`, leaving these conclusions untested against effective ACLs.

**5. Protected-window wiring and rollback**

The source wiring is consistent:

- [The protected deploy job](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2867a/.github/workflows/deploy.yml:964) uses the protected environment, pinned deployment SHA, route validation, serialized execution, temporary capability grant, and unconditional revocation.
- Its migration list includes 1204 followed by 1206.
- [The runner’s protected set](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2867a/platform/scripts/migrate.ts:145) includes 1206. Isolated execution of the actual guard source confirmed refusal outside the protected path and allowance inside it.
- The standalone preflight and embedded preflight are byte-identical.

The shared protected window is **not one atomic transaction**: the runner commits each migration separately. A failed 1206 can leave 1204 committed, while rolling back 1206 itself.

The documented drop sequence is not a complete post-commit rollback procedure. It omits reconciliation of the migration ledger and the additional SELECT grants on existing tables. Once generations have been sealed using this completeness layer, removing it also removes their future enforcement. A pre-window rollback runbook should distinguish an unused installation from one already relied upon; a forward correction is preferable after use.

**6. Do the tests earn their claims?**

The database suite has useful coverage: actual migration application, existing-object fingerprints, digest vectors, omission adversaries, input drift, finalization, replay after registry advance, and selected sealed-mutation refusals.

However, **R5 — P2: the checked-in execution path and fixtures leave material acceptance gaps.**

- Both database describes use `skipIf(!TEST_DB_URL)`. The checked-in CI workflows neither supply `GOCHARA_A51_TEST_DATABASE_URL` nor explicitly exercise this new suite.
- Tests run through the schema-owning connection, not `SET ROLE data_plane_builder`.
- L1 stand-ins use `created_at` instead of the actual `computed_at`, concealing R4.
- The lock test checks markers on one connection, not competing sessions or blocking behavior.
- The post-seal assertions do not exercise every operation on every new table, despite the broader claim.
- No reproducible mutation harness/report supporting **18/18 caught** was present in the reviewed changes. I cannot independently affirm that count.

The separate CI test for 1216’s grants does not remedy these gaps: it does not apply 1206.

**Ranked merge-blocking amendments**

| Rank | Priority | Required amendment |
|---:|---|---|
| 1 | P1 | Make committed/stored equality exact for each full chart/generation/class/path/version key. Add cross-path and cross-version borrowing adversaries. |
| 2 | P1 | Bind snapshot sky convention to both publication and coverage conventions through the immutable bridge. Test incompatible and missing bridges with no records/windows. |
| 3 | P2 | Reject excluded pins with NULL reasons; make reason/ruling checks total booleans. Test both NULL-reason variants. |
| 4 | P2 | Canonicalize real input timestamps independently of session timezone and exclude the actual audit columns. Test real-schema rows across timezones and material versus audit-only changes. |
| 5 | P2 | Wire disposable PostgreSQL execution into CI without silent skipping; exercise the actual builder/sealer roles and concurrent lock protocol. Include R1–R4 regressions and reproducible mutation evidence if retaining the count. |

**Separate follow-ups**

- Preserve the accepted F-3 boundary: actual independent derivation, storage-domain mapping, declared class census, registry-version selection, and candidate invalidation still require writer-gate evidence.
- A class absent from both coverage and inventory is not detected. Serving must report it as `not_searched`; a seal is not proof that every possible class was searched.
- F-6’s generation-5 manifest binding to `inventories_digest`, including Moon-partition treatment, remains unimplemented here.
- Resolve the empty-ledger digest discrepancy and document the stricter verification-row policy.
- Before the protected window, establish realistic seal cost, PostgreSQL version compatibility, quiescence, effective ACLs, and the post-commit recovery procedure.

**What I could not verify**

I did not run the PostgreSQL/Vitest integration suite or the reported eighteen mutations. No disposable test URL was configured, and the read-only environment prevented the writable temporary/database setup required by the suite. Installed PostgreSQL binaries alone do not establish a runnable disposable instance.

I did not connect to production or verify its current catalog, privileges, migration ledger, runtime version, or workload. Campaign/main comparisons used the pinned local refs identified above, without fetching.

No files or git state were changed. The checkout remained clean at `edece78c9`.