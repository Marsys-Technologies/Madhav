---
artifact: ASTRA_REVIEW_M1243_INERT_REGISTRY_ROWS
version: "1.0"
reviewer: "Codex gpt-6-astra"
date: "2026-10-03"
verdict: ACCEPT_WITH_AMENDMENTS
reviewed_commit: ea3531af175a3d7dd6883de0e9348d4e44be794d
authority: "Review only; authorizes nothing."
---

The insert payload is correct. **Release requires amendments:** the new rows break Nirmāṇa’s registry reconciliation, and the existing v4.1 teardown can permanently undo this repair.

1. **Seed parity: PASS for all 28 columns of both rows.**

   I independently evaluated the actual seed literals, governance helper, and `main()` parameter derivation against:

   - `origin/main`: `7a6481ad457f17da00d9d0945137756bcda936ae`
   - `origin/pravaha/a53-am5-inventory`: `7678f77228b77e77cc0dd2fb04ddf36c01086ee5`

   Both comparisons produced zero differing columns, including strings, NULLs, arrays, and column order. Both derive `layer_name='Kāla'`, `layer_index='L3'`, `asset_type=asset_kind='data'`, and explicit `catalog_status='CURRENT'`. v4.1 has `has_substeps=true`, timeout 7200; v5 has `false`, timeout 600. Omitted columns receive the same defaults as a fresh seed insertion.

   This establishes parity with v5’s seed, not its readiness for activation.

2. **SQL safety: acceptable for the repository-defined schema; the `xmin` guarantee is overstated.**

   The migration contains one two-row INSERT, no UPDATE/DELETE, chart-data mutation, grant, or DDL. `ON CONFLICT (asset_id) DO NOTHING` preserves existing rows.

   The repository-defined application trigger, `nirmana_registry_receipt_invalidation`, is **AFTER UPDATE OF** specified columns; this INSERT does not fire it. Its `asset_freshness` invalidation therefore does not occur. Incoming foreign-key DELETE/UPDATE triggers likewise do not fire on this insertion.

   Existing rows with `is_active=true`, NULL activity, `has_writer=false`, or nonempty dependencies cause rollback. An existing inactive writer with different descriptions, timeout, scope, or other metadata **passes unchanged**. NULL dependencies also pass because of `COALESCE`. Thus byte parity applies to inserted rows, not arbitrary pre-existing rows.

   The no-dependents check correctly rejects references from **any** registry row, including inactive rows. These are application-time assertions, not permanent constraints against later edits.

   The [post-check at line 109](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-m1243/platform/migrations/1243_ka_gochara_inert_registry_rows.sql:109) has these limits:

   - `pg_current_xact_id()::xid` requires PostgreSQL **13+**. The repository’s stated production contract, PostgreSQL 15.18, supports it. [PostgreSQL transaction-ID documentation](https://www.postgresql.org/docs/13/functions-info.html).
   - Ordinary and HOT updates in this top-level transaction produce a new tuple version and are detected. HOT does not preserve the old version’s `xmin`. [System columns](https://www.postgresql.org/docs/current/ddl-system-columns.html), [HOT](https://www.postgresql.org/docs/current/storage-hot.html).
   - **False negatives:** deleted rows disappear from the scan; writes inside successful subtransactions can carry a different subxid; deferred triggers can execute after the check. Other-table writes are outside its scope. [Subtransactions](https://www.postgresql.org/docs/current/subxacts.html), [trigger timing](https://www.postgresql.org/docs/current/trigger-definition.html).
   - **False positives:** earlier unrelated registry writes in the same transaction would count, although the normal runner isolates each file. After XID wraparound, preserved frozen `xmin` values can also collide with the current 32-bit ID. [Freezing behavior](https://www.postgresql.org/docs/current/routine-vacuuming.html#VACUUM-FOR-WRAPAROUND).

   **Required wording amendment:** describe this as a supplementary check of visible tuple versions, not proof that nothing else was touched. The reviewed INSERT and trigger definitions establish the narrow write scope.

   The runner commits SQL and its ledger entry together. Failure rolls both back. Subsequent matching-hash deployments skip the file entirely; they neither repeat its assertions nor repair subsequently deleted rows.

3. **Consumer compatibility: ordinary planning passes, but two integration defects require fixes.**

   `runPreparation`, `recalibrationEnqueue`, cockpit plan/stats, and co-writer detection exclude these inactive rows. Their `count_sql` strings are not executed by active cockpit stats. The writer-gap check scans registered IDs, so an extra v5 registry row before registration is harmless to that check.

   `capability_estate_census` consumes the seed, writer inventory, and selected digest migrations; 1243 changes none of those inputs. `asset_census` excludes inactive rows while reporting them in its excluded population. E6 level/family generation remains unchanged. Unfiltered registry/catalog and TCI inventories can gain entries and counts; “inert” does not mean invisible everywhere.

   **A1 — Preserve the registration during teardown.** [Dispatch teardown line 192](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-m1243/platform/scripts/dispatch_a25_v41_candidate_job.py:192) deletes `ka_gochara_v4_41_candidate`. After 1243 is ledgered, this restores the global writer gap permanently until another repair. An in-memory execution of the actual teardown and gap-check functions reproduced `[] → ['ka_gochara_v4_41_candidate']`.

   Remove that registry DELETE, its help text, and the existing tests requiring it. Preserve the inactive writer row. Add a regression covering migration → dispatch/teardown → ledger-skipped redeploy → no writer gap. The ordinary dispatch’s TRUE → FALSE flips already occur within one transaction and are compatible with 1243.

   **A2 — Reconcile Nirmāṇa’s frozen population explicitly.** [Baseline construction](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-m1243/platform/src/lib/nirmana-elevation/monitor.ts:212) reads inactive rows and excludes only designated supporting writers. Both new rows receive `execution_obligation='unresolved'`; `assertFreezableManifest` rejects them. The monitor consequently reports `source_unavailable`, and snapshot reconstruction fails. [Registry comparisons](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-m1243/platform/src/lib/nirmana-elevation/definitions.ts:350) also reject the additional identities.

   Add one shared, explicit exclusion for these two staged candidates across baseline construction and both frozen-registry comparisons, conditioned on their inert shape. Test the existing frozen population with both rows added. **Do not broadly exclude all inactive assets:** existing retired identities belong to the frozen population. Both rejection paths were reproduced using the actual functions in memory.

4. **Protected-window ordering: 1243 is routine, but application order is not guaranteed.**

   The five protected files are absent from inspected main and present on the inventory branch. In the combined tree, numeric ordering reaches pending 1204 before 1243 and the routine runner refuses it. `--only 1243` also refuses to jump unapplied predecessors. See [runner predecessor enforcement](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-m1243/platform/scripts/migrate.ts:750).

   **1243 need not chronologically precede their merge:** a deployment pinned to the earlier source can still apply it, or the authorized protected window can complete first, followed by routine migrations. But merging 1243 first does not prove either happened.

   **A3 — Add an explicit release gate:** require the 1243 filename/hash ledger receipt, both inert rows, and a zero-gap check before releasing the writer train. Keep 1243 outside the protected set. This three-file PR contains no such ordering guarantee.

5. **Other writer gaps and verification limits.**

   Production discovery found **124 registered IDs**, comprising **122 plan-level writers and two explicitly exempt sub-assets**. Every plan-level ID exists in main’s seed; none is missing from the known-good set. No additional source-level seed omission was found.

   This cannot establish that production has all those rows or flags. The new DB fixture manufactures every other writer row, so it proves the modeled repair—not that production’s only gap is v4.1.

   Four existing offline completeness checks and 16 pure E6 checks passed. However, the completeness migration scanner reads only `platform/supabase/migrations`, so it does not validate 1243; the new v5 seed-parity test also skips on main.

   Review was file/in-memory only. No database was connected, no file was written, and the DB suite/full CI were not run. `git fetch origin` was blocked by the read-only sandbox; comparisons use the exact local remote-reference SHAs above.