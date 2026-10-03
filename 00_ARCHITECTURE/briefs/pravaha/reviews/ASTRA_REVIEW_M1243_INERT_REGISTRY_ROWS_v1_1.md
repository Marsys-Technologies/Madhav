---
artifact: ASTRA_REVIEW_M1243_INERT_REGISTRY_ROWS
version: "1.1"
reviewer: "Codex gpt-6-astra"
date: "2026-10-03"
verdict: REJECT
reviewed_commit: "324b8c9686185a1be22c7be30998cf5210780bfe"
authority: "Review only; authorizes nothing."
---

**REJECT. R20-1 and R20-2 are corrected, but the migration cannot follow its documented routine deployment path, and its ACL excludes a legitimate caller.**

GitHub confirmed the reviewed head. The detached checkout was `84f7afb`; the additional commit changes only a comment. Probes loaded the reviewed commit directly from Git objects.

| Prior finding | Status | Evidence |
|---|---|---|
| **R20-1** — throughput-only evidence missed | **CLOSED in source and controlled probes** | [Migration:165–167](https://github.com/Marsys-Technologies/Madhav/blob/324b8c9686185a1be22c7be30998cf5210780bfe/platform/migrations/1243_ka_gochara_inert_registry_rows.sql#L165) checks all three tables. [definitions.ts:144–146](https://github.com/Marsys-Technologies/Madhav/blob/324b8c9686185a1be22c7be30998cf5210780bfe/platform/src/lib/nirmana-elevation/definitions.ts#L144) supplies the identical guarded expression to all seven loaders. |
| **R20-2** — supporting-writer dependency hidden | **CLOSED** | [definitions.ts:405–408](https://github.com/Marsys-Technologies/Madhav/blob/324b8c9686185a1be22c7be30998cf5210780bfe/platform/src/lib/nirmana-elevation/definitions.ts#L405) and [monitor.ts:225](https://github.com/Marsys-Technologies/Madhav/blob/324b8c9686185a1be22c7be30998cf5210780bfe/platform/src/lib/nirmana-elevation/monitor.ts#L225) evaluate exclusion before removing supporting writers. |

Both IDs passed refresh-only and watchdog-pruned throughput probes. Both also survived exclusion with **active and inactive `bo_grounding` dependents through baseline construction and both actual comparison callers**. The dependency-free controls still exclude the candidates and preserve retired identities.

**Required changes**

1. **P1 — 1243 now requires a protected schema-capability window.**

   [Migration:153](https://github.com/Marsys-Technologies/Madhav/blob/324b8c9686185a1be22c7be30998cf5210780bfe/platform/migrations/1243_ka_gochara_inert_registry_rows.sql#L153) creates a function in `public`. The repository explicitly gives the ordinary migration role **USAGE without CREATE**: [deploy.yml:953–961](https://github.com/Marsys-Technologies/Madhav/blob/324b8c9686185a1be22c7be30998cf5210780bfe/.github/workflows/deploy.yml#L953). The ownership attestation rejects persistent CREATE for `amjis_app` at `platform/scripts/data-plane-ownership-status.ts:559–570`.

   Consequently, under the enforced privilege model, first application fails at function creation and rolls back the registry INSERT. The regression fixture conceals this by granting CREATE at `platform/python-sidecar/tests/test_migration_1243_inert_registry_rows.py:101`.

   **Change:** provide an explicitly selected, bounded grant/apply/revoke path for 1243, with guaranteed revocation and postflight verification; classify it appropriately in the runner. Preserve application **before the protected train introduces pending predecessors such as 1204**. Test the real no-CREATE baseline and the successful temporary window. Merely adding 1243 to the later Gochara train does not satisfy that ordering.

2. **P2 — the fifth definitions loader also runs as the ungranted ingress role.**

   [definitions.ts:3254–3256](https://github.com/Marsys-Technologies/Madhav/blob/324b8c9686185a1be22c7be30998cf5210780bfe/platform/src/lib/nirmana-elevation/definitions.ts#L3254) selects `nirmana_evidence_ingress_writer` for server-reconstructed receipts. Foundation lane C and transitions `T0_CENSUS` / `DENOMINATOR_FROZEN` call `loadCurrentRegistryRows` at lines **2864 / 3046**, which now invokes the function at line **2797**.

   [Migration:179–185](https://github.com/Marsys-Technologies/Madhav/blob/324b8c9686185a1be22c7be30998cf5210780bfe/platform/migrations/1243_ka_gochara_inert_registry_rows.sql#L179) grants only app/control execution. With the staged rows present, these legitimate ingress reads encounter permission denial.

   I exercised all three paths through the actual `recordNirmanaElevationEvidence` entry point with a controlled `42501`: each selected the ingress pool, reached the function, rolled back and inserted no receipt.

   **Change:** reconcile the approved two-role boundary with this third caller. The minimal ACL repair requires owner approval to grant **only this function’s EXECUTE** to ingress, then update the ACL assertion, readback and actual-role tests. If that boundary remains fixed, redesign these reads through an approved evidence reader while preserving transaction consistency and ingress write identity. Treating permanent denial as acceptable fail-closed behaviour leaves required operations unusable.

3. **P2 — a pre-existing grant option survives the ACL check.**

   [Migration:198–205](https://github.com/Marsys-Technologies/Madhav/blob/324b8c9686185a1be22c7be30998cf5210780bfe/platform/migrations/1243_ka_gochara_inert_registry_rows.sql#L198) checks grantee and privilege but ignores `is_grantable`. A pre-existing control-writer `EXECUTE WITH GRANT OPTION` survives replacement and the plain GRANT; the post-check reports `v_bad=0`. That role can subsequently delegate execution. PostgreSQL preserves existing ownership/permissions on replacement and permits onward grants through grant options. [CREATE FUNCTION](https://www.postgresql.org/docs/15/sql-createfunction.html), [GRANT](https://www.postgresql.org/docs/15/sql-grant.html).

   **Change:** reject non-owner grant options, for example with `OR (a.grantee <> p.proowner AND a.is_grantable)`. Add the pre-existing-grant-option regression and include `is_grantable` in readback.

**Function assessment**

- The fixed `search_path = pg_catalog, pg_temp`, schema-qualified evidence tables and absence of dynamic SQL provide sound name-resolution protection.
- PUBLIC revocation immediately follows creation. The runner wraps the complete file and ledger insertion in one transaction (`platform/scripts/migrate.ts:828–840`), so this path has no committed PUBLIC-execution window. Preserve that transaction boundary.
- Ownership is **checked, not assigned**. With `amjis_app` present, another owner either prevents replacement or triggers rollback. Unexpected direct ACL grantees also trigger rollback. This safely refuses conflicting pre-existing objects; it does not repair them.
- If `amjis_app` is absent, the owner assertion is skipped and the creator remains owner. If control is absent, its grant is skipped. Later role creation does not replay a ledger-applied migration. Governed application must establish the required roles first.
- Basic row shape, incoming dependencies, owner, SECURITY DEFINER, search path and unexpected direct grants are checked. Zero runtime evidence and complete seed equivalence for pre-existing rows are **not** in-migration assertions.
- **STABLE is correct:** this is a read-only lookup using the calling statement’s snapshot, not a permanently cached answer. [PostgreSQL volatility documentation](https://www.postgresql.org/docs/15/xfunc-volatility.html).
- Successful calls return one combined existence boolean per allowed ID; NULL/other IDs raise before evidence lookup. No row-returning or injection channel was found. The implementation does not promise constant-time execution.

**Fail-closed behaviour and build impact**

`has_runtime_evidence === false` is the sole evidence condition permitting exclusion ([definitions.ts:117–123](https://github.com/Marsys-Technologies/Madhav/blob/324b8c9686185a1be22c7be30998cf5210780bfe/platform/src/lib/nirmana-elevation/definitions.ts#L117)). NULL/undefined retain the candidate. Missing-function, denied-execution and timeout probes propagated failure through definitions; monitor reports `source_unavailable`; snapshot throws its source error. I found no error-to-false fallback.

Ordinary builds do **not** depend on these loaders:

- Writer-gap preflight directly selects `asset_id, has_writer` (`runner.py:175–201`).
- Build preparation and recalibration use their own registry queries (`runPreparation.ts:174–184`, `recalibrationEnqueue.ts:138–141`).
- The internal elevation executor submits definition/evidence commands; it is not the ordinary build dispatcher.

Function errors therefore block the affected elevation operations, including the ingress paths above. Separately, failed migration application leaves the original writer-gap problem unresolved.

**Ordering and readback**

The campaign readback at `campaign/pravaha@cde180705` now checks function metadata, direct ACL entries, zero evidence counts and both boolean results (`registry_1243_readback.sql:15–31`). These are **inspection queries with expected-result comments**, not executable assertions. Extend them for grant options, actual caller-role execution and schema-CREATE revocation.

The sitting checklist still pins the old SQL hash `88be3ed5…` at `PROTECTED_WINDOW_SITTING_CHECKLIST_v1_0.md:12`. The reviewed migration’s hash is:

```text
bb6a7a33bf1f1928cdd4bc45e0ea46de9e1e70480af8d2baa2bd0ac952f80556
```

Re-pin the final amended bytes and revise the obsolete “routine migration / automatic green deployment” procedure.

Verification comprised **20 independent TypeScript caller probes**, three ingress-path reproductions, and in-memory SQL-expression/ACL-predicate probes. SQL probes used SQLite; PostgreSQL roles, PL/pgSQL and transaction enforcement were **not executed**. The read-only sandbox prevented a disposable PostgreSQL instance. No files were written and no production database was accessed.