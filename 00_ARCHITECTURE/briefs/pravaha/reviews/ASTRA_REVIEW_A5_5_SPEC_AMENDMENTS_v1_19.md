---
artifact: ASTRA_REVIEW_A5_5_SPEC_AMENDMENTS
version: "1.19"
reviewer: "Codex gpt-6-astra"
date: "2026-10-03"
verdict: REJECT
reviewed_commit: "5aa4008bc3706690134a1068cf0617ca12a801c5 (campaign/pravaha)"
reviewed_heads:
  pr_2961: "8a204a7b11078e18fa9a6e5920bb6e4d9b0859a8"
  pr_2903: "5a46c9c97e61e86dde56c3608032431b9a9ff0e0"
  pr_2996: "75a36fe625d8aed40abc049a7483ad97f28353da"
  composed_integration: "20ad1bd6edddd10c8fc122db11a2925ad17b1cd3"
  writer_a53: "7678f77228b77e77cc0dd2fb04ddf36c01086ee5"
  inspected_origin_main_with_pr_2997: "b97536e0fb2aed7f2078d123b5082db3cb40bf74"
additional_commit_metadata_read:
  pr_2996_base: "7a6481ad457f17da00d9d0945137756bcda936ae"
authority: "Review only; authorizes nothing."
---

## Verdict

**REJECT overall.**

The protected-migration selection and capture defects are corrected. The checklist closes the requested automatic-run, drain, ledger and 1241 sequencing amendments.

**#2996 remains REJECTED:** its exclusion can conceal throughput-only evidence from the definition loaders, and its callers can discard an incoming dependency before evaluating the exclusion. Both violate the agreed self-cancellation conditions.

The packet also incorrectly reports that the integration tree passes `WINDOW_MERGE_CONTROL=1`: that tree contains 1241, which the test expressly rejects.

No file was written. No production database was accessed.

## Item status table

“CLOSED” means corrected in the inspected source or procedure; it does not mean an operational act occurred. The original round-19 review files were unavailable, so these closure assessments cover the findings described in the commissioning prompt and packet v1.25.

| Item | Status | Verdict | Remaining change or qualification |
|---|---|---|---|
| R19-1 — incomplete protected selection | **CLOSED** | ACCEPT | Both named workflow heads execute the complete ordered selection and exclude 1241. The separate integration qualification claim needs R20-3 below. |
| R19-2 — zero-measurement baseline | **CLOSED** | ACCEPT | Capture, W0 import and subsequent load refuse an all-clipped level. |
| R19-3 — automatic runs, drains, ledger | **CLOSED** | ACCEPT | Checklist specifies the sole expected-red exception, skipped deployment jobs, ledger differences and drain gates. Actual runs remain unobserved. |
| F-R19-1 — attribution and observation | **CLOSED** | ACCEPT | Behaviour is attributed to train source and the executing test; refusal becomes observable after the first protected merge. |
| F-R19-2 — 1241 timing | **CLOSED** | ACCEPT | #2949 stays unmerged until SETTLED-1; the protected-train gate requires no 1241 file. |
| F-R19-3 — documented W0 shape | **CLOSED** | ACCEPT | Documented omissions, database aliases and counted level-4 removal work. |
| F-R19-4 — offset-less ISO strings | **CLOSED** | ACCEPT | Strings without an offset refuse under both tested non-UTC timezones. |
| F-R19-5 — minor wording | **PARTLY** | ACCEPT_WITH_AMENDMENTS | The runbook still lists `census` as a root capture field despite correctly explaining `meta.census` elsewhere. |
| M1243 A1 — teardown preservation | **CLOSED in source** | ACCEPT | Inspected main includes #2997: teardown preserves the registration, restores inactivity and validates before commit. |
| M1243 A2 — monitor reconciliation | **PARTLY** | **REJECT** | R20-1 and R20-2 remain. |
| M1243 A3 — release ordering | **CLOSED procedurally** | ACCEPT | Checklist requires merged/applied 1243, exact ledger hash, row fingerprints and zero-gap preflight before the first protected merge. Receipts remain outstanding. |
| #2996 migration payload and SQL | Reviewed | ACCEPT | Correct for inert staging; application and live catalog assumptions were not verified. |
| #2996 as a complete PR | **PARTLY** | **REJECT** | Correct the two exclusion defects and qualify the amended composition. |
| Claimed integration merge-control pass | **NOT CLOSED** | **REJECT** | Correct the incompatible evidence claim and supply the appropriate tree/result. |

## Probes

### Protected selection: both named heads

I extracted and executed the actual `deploy.yml` shell block at **8a204a7b1** and **20ad1bd6e**, under `bash -e`, replacing only `npx` with an argument-recording function. No migration command ran.

At both heads, the Gochara contracts input selected:

```text
1153 → 1154 → 1155 → 1156 → 1157
     → 1204 → 1206 → 1232 → 1233 → 1240
```

Across all 32 combinations of the five migration inputs:

- All 31 authorised combinations completed selection successfully.
- No combination selected 1241.
- No-input execution refused with exit 1.
- Both workflows retained four occurrences each of the phase and exception environment wiring.

On the integration tree, the Gochara protected set equals these ten files, and all ten SQL hashes match the campaign’s expected-window manifest.

**The separate merge-control assertion fails.** Replaying its directory predicate against the integration tree produced:

```text
actual:
  1241_gochara_verifier_sealer_inventory_grants.sql
expected:
  []
```

The integration tree also lacks migration 1243.

### Capture and W0 import: 5a46c9c97

The probes used the actual tool and reader code, a psycopg3-shaped controlled connection, and in-memory file handling.

| Probe | Result |
|---|---|
| Normal `--capture-old` entry point with every MD boundary clipped | Exit **3**, named missing-unclipped-boundary refusal, **zero artifacts**, rollback once, close once, no commit |
| Same baseline through `--import-w0` | Exit **3**, zero artifacts |
| Correctly checksummed handcrafted capture containing that baseline | Loader refused with the same coverage failure |
| Documented W0 shape, including omitted per-row contract fields, database aliases, natal `value`, and a level-4 row | Accepted; fills reported; level-4 removal counted; resulting capture identified as W0 |
| Offset-less string under `TZ=Asia/Kolkata` | Refused: `instant without an offset` |
| Offset-less string under `TZ=America/Los_Angeles` | Same refusal |
| Offset-less W0 input | Exit **3**, zero artifacts |
| Explicit `+05:30` input | Correctly normalised to UTC |

Naive Python `datetime` objects retain the documented UTC convention. The offending machine-local interpretation of **strings** is closed.

These probes establish application behaviour with controlled responses; they do not establish PostgreSQL transaction enforcement.

### #2996 payload and exclusion

- Independently evaluated seed-derived values: **28/28 columns match** for each inserted row. The v5 comparison used the writer head.
- Executed the actual TypeScript predicate/filter logic in memory for both candidate IDs.
- Activation, lost writer status, outgoing dependencies, retirement, positive evidence, and absent/null evidence prevent exclusion.
- An ordinary incoming dependent prevents exclusion.
- A `bo_grounding` incoming dependent is missed by the production caller’s filtering order.
- Executed the generated evidence expressions against an in-memory SQLite fixture containing throughput but no receipt/build-run asset: the definition expression reported false; the monitor/snapshot expression reported true. This was **not a PostgreSQL or role-permission test**.

## New findings

### R20-1 — P2: throughput absence is not proved by the definition loaders

**Locations at 75a36fe62:** `platform/src/lib/nirmana-elevation/definitions.ts:132–141`, with `false` calls at lines 671, 816, 970, 1143 and 2790.

The control-writer loaders omit `asset_throughput` and substitute the absence of `build_run_assets`. The comment asserts that every throughput row comes from a build run that also leaves a build-run asset row.

That implication does not hold:

- `platform/src/app/api/cockpit/refresh/route.ts:57–69` accepts an authorised asset-scoped refresh and directly inserts a dormant throughput row. This path creates neither a build-run asset nor a provenance receipt.
- `platform/src/app/api/cockpit/watchdog/route.ts:462–475` prunes old build-run assets and runs. Their existence is not a permanent proxy for throughput.

Consequently, an inactive candidate with **throughput-only evidence** remains excluded from definition comparisons, while monitor/snapshot readers retain it. A definition check can accept a registry view that the monitor rejects.

**The role restriction is real; the substitution is unsound.** Missing permission cannot establish that evidence is absent.

**Closing change:** provide an approved, narrowly scoped means for the control-writer role to determine throughput existence, and use equivalent evidence semantics across every loader. A restricted boolean lookup is one possible implementation. Unknown or failed evidence reads must fail closed. Add a test using the actual role with throughput-only evidence and no receipt/build-run asset, plus unavailable/denied-source coverage. Preserve the role’s intended privilege boundary and update its attestation when necessary.

### R20-2 — P2: supporting-writer filtering hides an incoming dependency

**Locations at 75a36fe62:**

- `platform/src/lib/nirmana-elevation/definitions.ts:400–401`
- `platform/src/lib/nirmana-elevation/monitor.ts:223`

Both callers remove `NIRMANA_SUPPORTING_WRITERS` **before** calling the candidate exclusion helper. The supporting set includes `bo_grounding`.

For this input:

```text
candidate: inactive, writer, no outgoing dependencies, no runtime evidence
bo_grounding: depends_on = [candidate]
```

The helper receives only the candidate, concludes that nothing depends on it, and removes it. The actual helper retains the candidate when given the complete registry.

This violates the agreed **no dependents** condition. The existing incoming-dependent test exercises the helper directly with an ordinary asset, so it misses the production-call ordering defect.

**Closing change:** evaluate candidate exclusion against the complete registry first, then remove supporting writers from the elevation denominator. Apply this ordering to baseline construction and both registry comparisons. Test both candidate IDs with active and inactive `bo_grounding` dependents through the actual callers. Keep `bo_grounding` itself excluded from the denominator and retired identities retained.

### R20-3 — P2: the reported integration merge-control pass contradicts its tree

Packet v1.25’s R19-1 evidence says the integration tree passed `WINDOW_MERGE_CONTROL=1`.

At **20ad1bd6e**, `platform/scripts/__tests__/gochara_window_dispatch_selection.test.ts:142` requires no `1241_*` file, but the tree contains `1241_gochara_verifier_sealer_inventory_grants.sql`. The assertion replay fails.

This does **not** reopen the corrected selection defect. It invalidates that specific qualification claim. It also does not establish whether the separately reported 1,104-test suite ran successfully.

**Closing change:** distinguish the full-chain rehearsal containing 1241 from the window-only merge-control composition. Record the latter’s exact SHA and passing result with all ten window files and no 1241. Correct the packet; retain the no-1241 assertion. Qualify the final #2996 amendments separately—the named integration tree does not contain 1243.

### R20-4 — P3: remaining documentation inconsistencies

At campaign head:

- Runbook line 286 says the capture writes `{rows, natal, census, meta, sha256}`. The actual root shape is `{chart_id, build_id, selection, rows, natal, meta, sha256}`; census is under `meta.census`.
- Runbook line 299 still relies on “`ka_gochara_v5` has no registry row” as an execution exclusion. After 1243, the relevant property is its explicit inactivity. Align the corresponding sequencing text.

These are bounded documentation amendments.

### #2996 migration safety and other consumers

The SQL is acceptable for its stated inert-staging purpose:

- One two-row `INSERT`; `ON CONFLICT DO NOTHING`.
- No direct chart-data changes, UPDATE/DELETE, grants or DDL.
- Both fresh rows are inactive writers with empty dependencies.
- Post-checks reject missing/non-inert rows and incoming dependencies from any registry row.
- Existing rows are preserved. The migration does **not** enforce all 28 seed values on pre-existing rows; the release readback must establish those fingerprints.
- The `xmin` comment now correctly describes a supplementary visible-tuple check.
- The repository-defined receipt-invalidation trigger is UPDATE-only, so this INSERT does not fire it.
- The runner commits each file and its ledger entry together. A ledger-skipped redeploy will not repair a later deletion.

The SQL SHA-256 is:

```text
88be3ed59aaa0685d65e9b8b6607f3787c3ae65a5e8fb96d51f09ebe63798321
```

**Ordering is mandatory:** 1243 must be successfully applied and read back **before 1204 lands on main**, as required by this commission and checklist. Once pending 1204 is present, the ordinary runner refuses before reaching 1243. `migrate.ts:753–760` also prevents `--only 1243` from skipping unapplied predecessors. Merging 1243 alone is insufficient evidence.

The inspected main head contains #2997’s preservation fix: teardown no longer deletes the registry row; it restores `is_active=false`, validates the row and commits together.

Consumer review found the expected inactivity filters in planning, recalibration, cockpit plan/stats, readiness and cascade paths. Co-writer detection excludes inactive peers. The writer-gap preflight tolerates v5’s row before its writer registration arrives. Unfiltered registry/catalog inventories will expose the extra rows and counts. The refresh route supplies the concrete throughput-only counterexample above.

I found no additional scheduling regression in those inspected consumers. Seed parity does not establish v5’s readiness for activation.

The exclusion otherwise has useful fail-closed behaviour: unknown evidence does not satisfy `=== false`; query failures do not produce a healthy monitor result; retirement and observed runtime evidence retain identities. R20-1 and R20-2 are the exceptions that must close.

## Ranked amendments

| Rank | Required closing change | Gate |
|---|---|---|
| **1 — P2** | **R20-1:** establish throughput existence correctly for the control-writer loaders; test actual-role throughput-only and failed-read cases. | #2996 acceptance; trustworthy definition checks |
| **2 — P2** | **R20-2:** evaluate incoming dependencies before supporting-writer removal; test both IDs through baseline and comparison callers. | #2996 acceptance; self-cancellation |
| **3 — P2** | **R20-3:** correct the integration claim and provide exact window-only merge-control evidence; qualify amended #2996 bytes. | Packaged release qualification |
| **4 — P3** | **R20-4 / F-R19-5:** correct capture shape and post-1243 inactivity wording. | Documentation consistency |

Actual-volume capacity and the complete disposable-clone seal measurement remain prerequisites for first approval/seal. They are outstanding operational evidence, not newly discovered source defects.

## Step lines

**(a) Protected window — REJECT as packaged; corrected selection and procedure ACCEPT.**

**No: the package is not yet executable with only operational acts remaining.** The new release prerequisite includes #2996, whose two source defects remain, and the integration qualification claim needs correction.

After those bounded amendments, the reviewed window mechanism has no remaining R19 selection or checklist defect. Execute the prescribed release readbacks and nine-step sitting; complete the train before W1 or after SETTLED-1; keep 1241 out of the train.

The known writer test-only merge-main resolution remains outside this review. Run the mandatory merged-tree control on its eventual final SHA.

**(b) Registry binding — ACCEPT; prior acceptance stands.**

No regression was found within this review boundary. Actual bindings, readbacks and retention of the selected identities remain operational.

**(c) First all-NULL candidate and seal — REJECT as packaged.**

**No: the complete package’s remainder is not yet only operational.** The capture/re-pin corrections are accepted, but R20-1 through R20-3 still require closure.

After closure, the remaining path within this review boundary is:

1. Take the official pre-S-L1 capture in the prescribed hour, retain both hashes and provenance, and close its connection before the window.
2. Receive authentic SETTLED-1 evidence; verify the whole-chart single build, 45+1 partitions, both required assets `lit`, build agreement, forensic evidence and natal-cell comparison.
3. Run comparison/local application. Review and merge the re-pin with both constants, reference/literal changes, implementation lock and affected goldens; obtain the steward’s hold release.
4. Complete window qualification and post-SETTLED-1 1241/ACL provisioning, deployment, bootstrap and actual permission/API/log proofs.
5. Build and independently verify the fresh all-NULL candidate after the last build; perform the required freezes and R0.
6. Measure actual candidate capacity and a complete disposable-clone seal before approval.
7. Complete R1, approval of the exact identities, seal, R2, reconciliation, persisted receipts and cleanup.

SETTLED-2 is not added as a gate. G3 remains a numerical-activation gate.

**(d) Measurement — ACCEPT_WITH_AMENDMENTS; prior conditional scope stands, execution remains blocked.**

Carry forward S1-REQ-EPHEMERIS, settlement/re-pin and hold release, Stage-1/Stage-2 freezes/readbacks, and actual measurement evidence. The `5.0` absolute probe does not close the governed `4.1` prerequisite.

## What I could not verify

- The original round-19 Astra and Fable review files: neither was present in the inspected packet/tree.
- The authors’ complete 1,104-test run, full Vitest suites, PostgreSQL migration tests, or the re-pin database pair on this head.
- PostgreSQL execution, transaction enforcement, actual control-writer privileges, or production trigger/catalog state. No disposable PostgreSQL was started.
- Live GitHub merge/run state, automatic expected-red runs, deployment drains, IAM, approvals, ledger receipts, registry fingerprints or zero-gap production results.
- Official capture, SETTLED-1 evidence, real re-pin output, capacity measurements or completed seal receipts.
- Remote freshness beyond the named local commit objects; no fetch was performed.

The reproduced failures are controlled source-level counterexamples. The working tree remained clean.