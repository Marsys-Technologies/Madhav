VERDICT: REJECT

Reviewed `5d9e712799336958e5a82bce74b57859a2944f44...2240aa4c0becc104bec1c2df16129e402e40ad38`. The foreign-reference checks have a concurrency gap, and a confirmed commit can still be reported as a confirmed rollback. Both matter even for one owner-role execution after a successful dry run.

References: **TD** = [teardown script](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-td4/platform/scripts/teardown_v5_small_test_job.py); **S** = [shared module](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-td4/platform/scripts/v5_small_test_shared.py); **UT** = [unit tests](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-td4/platform/scripts/__tests__/test_teardown_v5_small_test.py); **DBT** = [database tests](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-td4/platform/python-sidecar/tests/l3/gochara/test_c38_teardown_real_db.py); **RB** = [runbook](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-td4/00_ARCHITECTURE/briefs/pravaha/V5_SMALLTEST_TEARDOWN_RUNBOOK_v1_0.md).

1. **P2 — References can appear after validation and be changed by the delete.**  
   **TD:233–246,338–342,425–429.** The catalog-derived counts acquire no parent-row locks that prevent new references.

   **Failure scenario:** teardown finds no conversation referencing an owned run; another transaction sets `conversations.archived_by_run_id` to that run and commits; teardown then deletes the run. The existing `ON DELETE SET NULL` FK clears the conversation’s audit link. Neither N-137 check examines conversations.

   The FK exists in [migration 1120:76–79](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-td4/platform/supabase/migrations/1120_jataka_conversation_archive_context.sql:76). Neither advisory lock prevents this reference write.

   Lock selected parent rows with `FOR UPDATE` before validating ownership/references, and retain those locks through deletion. Protect the corresponding manifest-reference check too.

   **Blocks single production use: yes under the stated procedure.** An earlier dry run does not close this execution-time race.

2. **P2 — Catalog discovery deliberately omits composite FKs and assumes the referenced column.**  
   **TD:234–243.** `cardinality(c.conkey) = 1` silently excludes every composite FK. The query never reads `confkey`; every discovered child column is compared directly with the supplied run/manifest UUIDs.

   **Failure scenario:** an audit table references `build_runs(id, chart_id)` through a composite FK with `ON DELETE SET NULL` or `CASCADE`. Discovery ignores it; deleting the owned run changes or deletes the audit row. A single-column FK targeting a different unique UUID column can likewise be miscounted.

   Derive and pair the complete child/parent column lists, joining against the selected parent rows. Alternatively, explicitly refuse unsupported FK shapes.

   **Blocks single production use: unless a separate live-catalog audit establishes that every incoming FK fits the supported shape.** I found the six known run references correctly covered in source; I did not establish the live catalog. A successful dry run cannot expose an unintended cascade because it rolls that cascade back.

3. **P2 — Post-commit report preparation still loses COMMIT CONFIRMED.**  
   **TD:491–503.** After `phase = "committed"`, constructing `report` remains inside the transaction exception handler. That handler treats every phase except `"committing"` as eligible for a rollback-labelled failure.

   **Failure scenario:** an allocation failure while constructing the report at line 494 occurs after the database acknowledges COMMIT. A subsequent `rollback()` succeeds as a no-op, and the exception receives `"rolled_back"`.

   Offline fault injection at that exact boundary produced:

   ```text
   commits: 1; exit: 1
   ROLLBACK CONFIRMED: this run changed nothing in the database.
   ```

   Handle `"committed"` explicitly before the rollback branch, and preferably prepare report data before COMMIT. The success-print failure itself is now handled correctly at **TD:513–528**.

   **Blocks single production use: yes.** Dry-run validation never exercises this boundary.

4. **P2 — Reconstruction can bypass a failed preimage proof while a run survives.**  
   **S:138–168.** A surviving run with an invalid manifest digest, missing marker, or mismatched marker merely contributes a diagnostic note. Reconstruction then runs whenever no candidate matched—not only when no owned run row survives.

   **Failure scenario:** a canonical stamp exists, but its surviving owned run’s `plan_manifest_digest` is wrong. I reproduced acceptance by reconstruction, with the digest mismatch explicitly present in the printed explanation.

   This preserves round 3’s reconstruction strength, but does **not** implement the steward’s stronger surviving-run requirement. Tests at **UT:1032–1053** use a noncanonical stamp, whose reconstruction fails anyway; they miss the canonical case.

   **Blocks single production use: if acceptance depends on this fallback despite surviving runs.** A dry run positively reporting a matching **ORIGINAL** preimage avoids this particular defect; execution rechecks it. The general tool should refuse failed surviving-run proof.

5. **P3 — Recovery’s “full identity” still omits a persisted digest.**  
   **RB:34,40–41** records and compares five digests but omits `output_digest_spec_sha256`, which the receipt writer replaces at [provenance.py:264](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-td4/platform/python-sidecar/pipeline/orchestrator/provenance.py:264).

   **Failure scenario:** that specification identity changes while the recorded fields remain equal; recovery still matches and changes the receipt despite not matching its complete recorded provenance identity. Include it in evidence collection and comparison, using NULL-safe comparisons where appropriate.

   **Blocks single production use: no.** Timely teardown does not need recovery, and the section correctly remains **NOT FOR USE**. This review does not approve recovery.

The requested dispositions are:

| Round-3 finding | Round-4 disposition |
|---|---|
| Other incoming run FKs | **Partly resolved.** Six known FKs are discovered and have tests; findings 1–2 remain. TD:227–247; DBT:728–754. |
| Valid normalized writer stamps rejected | **Partly resolved.** Original-preimage compatibility is fixed; fallback eligibility remains finding 4. S:138–172; DBT:761–778. |
| Incorrect transaction-outcome reporting | **Partly resolved.** Success-print failures retain COMMIT; report preparation remains finding 3. TD:494–503,513–528. |
| Recovery mutation not bound to proved receipt | **Partly resolved.** Transaction, locks, identity predicates and rollback-on-mismatch added; finding 5 remains. RB:29–42. |
| Missing trigger-side privileges | **Resolved in the recipe.** Conditional freshness SELECT/UPDATE and required function EXECUTE are listed. TD:137–143; RB:49–55. |

| Second-reviewer item | Disposition |
|---|---|
| **B1 — Owner-role choice** | **Resolved in documentation.** RB:44–63 records `amjis_app` and owner choice. Its production ACL assertions were not independently verified here. |
| **B2 — Update registry only when active** | **Resolved.** TD:374–388,481–482. |
| **B3 — Exact-privilege database test** | **Partly resolved.** Restricted-role and missing-grant tests exist, but their bookkeeping fixture omits migration 596’s invalidation trigger; the exact-role case also lacks external referencing tables. DBT:46–62,611–699. |
| **B4 — Six additional run references** | **Partly resolved.** Named discovery and six tests exist; findings 1–2 qualify the safety claim. |
| **B5 — Legacy manifest NO ACTION reference** | **Resolved for the existing reference.** TD:365–370; DBT:711–716. |
| **B6 — Direct connection and backend checks** | **Resolved at source level.** TD:175–210; RB:18–19. |
| **B7 — Watchdog limitation** | **Resolved.** TD:29–32; RB:26–27 explicitly exclude watchdog serialization. |
| **B8 — Snapshot/inventory ownership** | **Resolved, retained from round 3.** S:218–245. |
| **B9 — NULL-link recovery conditions** | **Partly resolved.** Required conditions are recorded, but recovery remains gated and has finding 5. Also, a NULL-link refusal occurs before the ownership proof, so RB:37 cannot rely on that failed dry run having already proved the manifest/snapshot. TD:323–329,359. |

**Shared module and original-preimage proof — B/D.** The manifest/snapshot/inventory proof retains round 3’s strength for the supported writer sequence. `remedy` and `unproven` change messages only; `notes` collects reporting text.

However, `generation_ownership` trusts the caller’s `owned` IDs: **S:205–207** does not independently check their chart, trigger or exclusive membership. Teardown supplies a checked list through **TD:272–316**. Therefore:

- A NON-test manifest with a valid marker can satisfy the standalone marker validator, but a surviving NON-test member run is refused by teardown before reaching it.
- A staging caller must establish that same ownership, take the locks, call `refuse_if_frozen`, and validate the complete registry shape. The shared functions alone are not a complete staging admission check.
- `end_state_problems` supplies the evidence/dependent/catalog portion of N-137; teardown’s separate registry validation supplies inertness, writer status and dependencies. **S:249–283; TD:149–172,483–486.**

With **both test runs terminal**, run 2’s consistent manifest and snapshot are accepted, and both exclusively owned run IDs can be removed. If run 2 committed a different manifest but failed before replacing run 1’s snapshot, the helper refuses. I reproduced both outcomes offline. Identical vectors remain acceptable because the older output is still test-owned.

The dispatch script and migration 1304 are absent from this tree. Both dispatch integration tests skip. I therefore cannot confirm staging integration, canonical dispatch output, or whether the advised “re-dispatch” recovery can pass the same ownership guard.

**Catalog and privileges — C.** Existing readable single-column references to `id`/`manifest_id` are handled, including NO ACTION and RESTRICT. Self-references are counted too; references entirely within the selected deletion set would conservatively refuse.

Partitioned relations can yield both parent and partition entries, causing duplicate counting and additional SELECT requirements. Other-schema relations can be queried through the catalog’s quoted `regclass` rendering. However, exclusions use textual names rather than relation OIDs, and ordinary queries are unqualified: correctness still assumes the intended search path.

Every counted relation needs SELECT and applicable schema USAGE. An unreadable relation raises an error and rolls back; an offline cursor-error probe confirmed zero deletes before that failure. **RLS-hidden rows are different:** SELECT can succeed while hiding references. The proposed owner execution normally bypasses RLS, but this was not live-verified; the narrow-role tests do not prove that case.

**Backend checks — E.** I found no source-level reason for these checks to reject a healthy direct connection merely because its hash is negative: the shifted high word reconstructs the signed advisory key. Three rollbacks preserve the backend of a direct psycopg connection, and acquisition plus held-lock check occur in the same transaction. These checks cannot identify a quiet transaction pooler reliably; the runbook correctly retains a direct-endpoint requirement. I did not execute the PostgreSQL checks.

**Remaining scope and one-off use — F/G.** Direct generation deletes remain pinned to chart `482012f1-710e-4a25-994a-93821f5871aa` and generation `5.0`; bookkeeping deletes use the pinned asset/chart or selected owned run IDs. Bookkeeping has no generation predicate. The global registry mutation is limited to this asset’s `is_active`. **TD:425–432,481–482.**

I found no new supported-writer path that deletes an older NON-test output chain. Findings 1–2 still permit effects outside that chain. The active-registry branch also relies on other-chart freshness remaining absent between its check and migration 596’s global invalidation.

**Before the proposed one-off use, fix findings 1 and 3.** Findings 2 and 4 require either their code corrections or the explicit, independently established one-off conditions stated above. Owner privileges and execution within days address neither the reference race nor the reporting defect.

Verification performed: **108 offline tests passed, 2 skipped**, targeted in-memory probes, and `git diff --check` passed. No files were modified.

**Not verified:** database execution, real concurrency, production schema/data/ACLs/RLS/search path, CI results, dispatch integration, migration-1304 parity, recovery execution, or census reproducibility. No database or network was accessed.

