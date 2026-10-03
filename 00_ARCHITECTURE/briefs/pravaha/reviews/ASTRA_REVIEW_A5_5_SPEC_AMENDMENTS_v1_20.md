---
artifact: ASTRA_REVIEW_A5_5_SPEC_AMENDMENTS
version: "1.20"
reviewer: "Codex gpt-6-astra"
date: "2026-10-03"
verdict: REJECT
reviewed_commit: "89f4d674f4b674fbf02c7335a8f367b04082d2ff (campaign/pravaha)"
heads_read:
  final_window_composition: "e3349b52e73cdad32cd7b8da80963c7743b0f526"
  main: "7d1130703fd4b8a5f83c6b84349afd174392ba55"
  pr_2961: "6ab0f2f5f77c875603552d8be323a6a99e436fb7"
  pr_2963_metadata_and_ancestry: "9bbad986ab755044412354e437de52b37a219ada"
  pr_2867: "2c4f9759c88c294bf64cbb6a0fd8eb7b348ac8ff"
  pr_2919: "1a4c256f152cf612d390e3a13b838f53b7311f8f"
  pr_2999_writer: "af19df86ae5602a3dec603429628d8dd83adbaf9"
  previous_writer: "7678f77228b77e77cc0dd2fb04ddf36c01086ee5"
  pr_2903_repin_tool: "5a46c9c97e61e86dde56c3608032431b9a9ff0e0"
  pr_2981_gate_proof: "c3e16405f1bff0ed0d7ff3f1684f9f806a42af0d"
additional_commit_metadata_read:
  - "bf74158d82a4e72706d5ba873d690e6e6487eb10"
  - "897039525c85a459b54f74c5f1af9e1450b4300f"
  - "2317b4a159e6fd0242f2d85272a41ad9406ed78e"
  - "b3aa5fe38eeccafedc93419e9321e1cef2855127"
  - "de5c3ca7313f9ff41ea4bca085624f35ca00d861"
  - "3277f2576b36375ce808ba7a5145c52c8b8a072c"
  - "4023b720f5cc491da6a4dd6800805c5199997ee5"
  - "1e662e99b8454dc5ef585404c8ed48aaae29ff59"
  - "26c97be16e72ceb6026f965228c1aad95a51f988"
  - "e126b436e9cbf13368fa5ecf50d0fb2c0fd05108"
authority: "Review only; authorizes nothing."
---

## Verdict

**REJECT the package as the final executable sitting instruction. ACCEPT the inspected window composition and the narrow writer changes.**

**(a) Is the protected window NOW EXECUTABLE AS PACKAGED with only operational acts remaining? No.** The checklist still needs bounded procedural corrections: provide an explicit permitted merge point for the proof workflow required by row 6, replace its obsolete qualification pins, and reconcile contradictory operational wording.

The five-file window is correctly selected. The inspected composition preserves all ten migration hashes, contains rows-only 1243, and excludes production migrations 1235 and 1241. I found no new writer-algorithm defect. The evidence function remains outside this window.

## Item table

| Item | Closure | Verdict | Basis |
|---|---|---|---|
| R20-1 — differing evidence predicates | **CLOSED** | ACCEPT | Every inspected loader uses receipts OR build-run evidence. This is the subsequently accepted narrow fallback, with throughput deliberately excluded. |
| R20-2 — supporting dependents filtered too early | **CLOSED** | ACCEPT | Baseline and both comparisons evaluate exclusion against the complete registry. |
| R20-3 — wrong integration merge-control claim | **CLOSED** | ACCEPT | v1.27 identifies a valid window-only tree; independent assertion replay passes on `e3349b52e`. Residual checklist references are addressed below. |
| R20-4 — capture shape and absent-v5-row wording | **CLOSED** | ACCEPT | Capture shape includes `chart_id`, `build_id`, `selection`, and `meta.census`; v5 exclusion now rests on inactivity. |
| F-R20-1 — overstated merge-control evidence | **CLOSED** | ACCEPT | Correct replacement composition; `npm ci` included; exact five-entry grep retained. |
| F-R20-2 — one predicate everywhere | **CLOSED** | ACCEPT | One implementation, including ingress, monitor and snapshot. |
| F-R20-3 — exclusion expiry and disposition | **PARTLY** | ACCEPT_WITH_AMENDMENTS | Source states the accepted every-dispatch commitment. Runbook still describes a nonexistent 1243 function and permanent successful-run evidence. |
| F-R20-4 — evidence and monitor readback | **PARTLY** | ACCEPT_WITH_AMENDMENTS | Three evidence counts exist. The executable readback’s monitor expectation contradicts v1.27’s documented baseline. |
| F-R20-5 — original wording corrections | **CLOSED** | ACCEPT | #2996 freeze exception, green-deploy prerequisite, apply-log wording and expected `not_migrated` state are present. |
| Final composition `e3349b52e` | **PASS within inspected scope** | ACCEPT | Hashes, selection, protected-set equality, file presence and absence checks pass. PostgreSQL catalog replay was unavailable. |
| Writer governed-code delta | **PASS within inspected scope** | ACCEPT | Successful digest semantics preserved; by-path import failure deliberately repaired; implementation lock matches. |
| Fixture, census exceptions, E6 changes and deselect | **PASS within inspected scope** | ACCEPT | No production migration path from the fixture; exceptions are bounded; deselected test remains selected in the full-history job. |
| Frozen writer’s row-7 readiness | **PARTLY** | ACCEPT_WITH_AMENDMENTS | `af19df86a` still needs the already-prescribed synchronization with the reviewed controls and a new pin. |
| Checklist v1.8 as one consistent executable page | **NOT CLOSED** | **REJECT** | R21-1 through R21-4 below. |
| Steward dispatch under the owner’s ruling | **Authority arrangement clear** | ACCEPT | Ruling 2 expressly delegates act 9 to the AI steward. Residual “owner personally” wording needs removal. |

## Probes

### Composition and protected selection

All ten hashes independently recomputed from `e3349b52e` match `EXPECTED_WINDOW_SHA256.txt`:

| Migration | SHA-256 |
|---|---|
| 1153 | `5c04af16660cc036c3232a7544196bf5f79e2afb9e36f11ffc2d7743c6aab2f4` |
| 1154 | `d3b2d1f0c98550ff0b055941fa24fecd6ab89658fbe5e5e6229e2e4f7fcf85c2` |
| 1155 | `476aa27fc1dc6aa0d1ad8ed17939f3839f99987de6dc834ee251b6380566ad3a` |
| 1156 | `0b688dfa09f556a986c5675b7ca23cdcbec006883406b2c608c64a5c5cca9dbd` |
| 1157 | `706fac56f6fe575f3be9f0c82005b886d0db9479c4d59ef49a3ee064a08524b5` |
| 1204 | `a0b267f7ef6002a1997c30d34595ec3b86147ca617bf70ef8a05de55b8407ca1` |
| 1206 | `941c79f59f2d3d3125dc5ca680430d4a91a7dcddb53fc6daa9a9da8819e410d7` |
| 1232 | `f2ef6406604b819d5f443e32c1e70914f2337ead8867f12e0aecd96d13f1ec44` |
| 1233 | `958b911703eee3528e1db75624984020964b8d31fe3fe286d64071368bd5a705` |
| 1240 | `05a8f897a0b8ae6b955915eced717ad30c98af485d490185333a88355707bc6b` |

Additional results:

- No `platform/migrations/1241_*`; no `platform/migrations/1235_*`.
- 1243 is present with SHA-256 `88be3ed59aaa0685d65e9b8b6607f3787c3ae65a5e8fb96d51f09ebe63798321`.
- Executed the **actual extracted `deploy.yml` shell block**, with `npx` replaced by an argument-printing shell function.
- All **32 input combinations** behaved as expected: 31 nonempty combinations succeeded; the empty combination refused explicitly; none selected 1241.
- Gochara-contracts-only selection is exactly **1153–1157, 1204, 1206, 1232, 1233, 1240**, ascending.
- Against committed ledger snapshot `prod_ledger_2026-10-02c.txt`, pending selection is exactly **1204 → 1206 → 1232 → 1233 → 1240**.
- Replayed all eight selection-test conditions, including both `WINDOW_MERGE_CONTROL` conditions. Selected files exist; the Gochara protected set equals the selection; all four phase/exception wiring pairs exist.

These were read-only assertion replays, **not a claim that I ran Vitest’s temporary-directory harness**.

The inspected ancestry matches the stated composition order. I did not recreate the merges or independently establish the authors’ zero-conflict claim.

### Trigger and privilege artifacts

The expected trigger manifest has:

- SHA-256 `2a00af09f3db783f4975c03ea925baff7cf60be5630d235bffdfd77eac4bd73e`.
- **32 relation records and 106 trigger records**.
- Complete relation-set agreement with the manifest query; no missing-relation marker; enabled-mode `O` throughout; unique trigger identities and valid function-definition hashes.

The query captures event, timing, level, UPDATE columns, arguments, deferrability, actual WHEN expression and `md5(pg_get_functiondef(...))`. This validates the artifact’s structure and coverage; **catalog equality requires PostgreSQL execution**.

The privilege generator independently reproduces the committed readback SQL from final 1206/1240 bytes: **92 expanded privilege expectations**—47 table, 3 column and 42 function checks; 38 builder, 31 verifier and 23 sealer expectations.

Checklist controls for both roles existing before row 7, positive privilege readback and `CREATE=false` in row 9, automatic-run drain before row 8, and **both directions of W5/W6** are present and correctly expressed.

### Writer behavior and implementation lock

Across the governed implementation list, the executable changes are confined to `ledger.py` and `inventory_verifier.py`.

**“Behavior-preserving” needs one qualification:** the ledger change intentionally turns the former by-path `ImportError` into successful execution. It preserves the successful package-import calculation.

Eight controlled generation/order cases produced identical query behavior and digests across old package loading, new package loading and new by-path loading. The former by-path failure was reproduced. The fallback reuses its cached sibling module.

`_C_TIER` resolves to the same string, `two_pass_verified`; no predicate change was found.

The recomputed implementation lock matches both writer and final composition:

`73f67d223640b1d6a10710d12b17e122a682a0a04a9950486b1ae6f307c81f9d`

### Fixture, guard, CI and supporting changes

The 1241 fixture hashes to:

`a3480710c7498065892965f23d9bee43dc700d4d8f16eb46ac8fb0ee601efefa`

Its loader’s fallback, real-file preference and tamper refusals passed controlled in-memory checks. References are confined to test infrastructure. The production runner scans only the two migration directories, nonrecursively; it does not scan the fixture directory. The pipeline image does not copy tests. **No inspected path lets the runner or protected selection apply this fixture.**

The disposable guard passed 60 controlled address/environment cases. RFC1918 acceptance is restricted to the exact three IPv4 ranges and `GITHUB_ACTIONS == "true"`; other nonloopback classes remain refused. No connection was opened.

The DB-step deselect is justified by source:

- The omitted test reads historical commit `2b3e096739b3501395a74c079846433c1bee3992`.
- That DB job has a shallow checkout.
- Governance Gates uses `fetch-depth: 0` and still selects this unmarked test without that deselect.

Five graha-map parity checks passed. Both verifier dṛṣṭi tables agree with the pinned kernel convention, including empty nodal aspects. The E6 delta adds inactive v5 to the refusal family; it does not add v5 to the 127-active-asset level map or alter the active DAG hash.

### Registry exclusion

Twenty-four targeted checks using the actual TypeScript functions passed, covering both staged IDs, complete-registry dependency checks, active and inactive supporting dependents, malformed shape/evidence cases, both comparisons and baseline behavior.

The source now documents pruning and registry-cascade limitations and requires disposition plus exclusion-list removal for **every real dispatch, successful or not**.

The supplied production ledger/fingerprint/preflight results remain **steward evidence**, not independently observed production results in this review.

## Findings

### R21-1 — P2: row 6 requires a workflow the permitted merge sequence does not install

[Checklist row 6](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-a55v/00_ARCHITECTURE/briefs/pravaha/runbooks/PROTECTED_WINDOW_SITTING_CHECKLIST_v1_0.md:23) requires the #2981 proof from a protected branch.

`gochara-seal-gate-proof.yml` exists at `c3e16405f`, but is absent from main, the final composition and every listed control/train head. Row 4 merges only #2961/#2963. The freeze permits rows 4/7 and #2996, without an explicit #2981 exception.

Runbook line 315 says “#2981 earlier, for the proof,” but does not resolve that checklist ordering/freeze conflict.

**Closing change:** explicitly place the proof-workflow merge before row 6—naturally in row 4—include it in the freeze exception and automatic-run drain/recording sequence, and qualify the resulting commit. Alternatively, name and qualify an existing permitted protected ref carrying the workflow. The current packet supplies neither executable route.

### R21-2 — P2: the checklist freezes superseded evidence

[Checklist lines 12–24](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-a55v/00_ARCHITECTURE/briefs/pravaha/runbooks/PROTECTED_WINDOW_SITTING_CHECKLIST_v1_0.md:12) still identify:

- Writer `7678f7722` and packet v1.23 in the preamble/row 2.
- `7678f7722` as the frozen writer in row 7.
- Already-resolved conflict descriptions as current instructions.
- Intermediate `50f87cb6f`, with `-X ours`, in the closing qualification note.

The latest packet correctly names `e3349b52e` and `af19df86a`. The executable page must agree.

There is also a real, bounded **operational synchronization requirement**: writer `af19df86a` lacks the four phase/exception wiring pairs present in #2961/final composition and lacks the selection-test file. Consequently, that pinned writer does **not yet satisfy row 7’s byte-identical-workflow/test precondition**.

The checklist already prescribes updating branches with main. I therefore classify the synchronization as an existing operational requirement, not a newly discovered writer-algorithm defect or a failure of `e3349b52e`.

**Closing change:** replace active pins with v1.27/final-composition evidence; label intermediate results historical; perform the prescribed writer synchronization, record its new SHA, and recheck every train PR before the first merge and after each squash.

### R21-3 — P2 before first candidate dispatch; P3 readback correction: registry operational text contradicts the accepted implementation

[Runbook line 299](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-a55v/00_ARCHITECTURE/briefs/pravaha/runbooks/ROLES_AND_SEAL_PROVISIONING_RUNBOOK_v1_0.md:299) still describes:

- Receipt/build-run/**throughput** evidence.
- A “SECURITY DEFINER function of 1243.”
- Permanent exclusion expiry after the first successful run.

All three conflict with the accepted split. The source’s stronger every-dispatch disposition/list-removal commitment is missing from this operational paragraph.

Separately, [registry readback line 20](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-a55v/00_ARCHITECTURE/briefs/pravaha/runbooks/rehearsal/registry_1243_readback.sql:20) expects the newest monitor status **not** to be `source_unavailable`. Packet v1.27 expressly documents the pre-existing third-row failure and rejects that expectation as a 1243 acceptance criterion.

**Closing change:** document the actual two-table predicate and its retention limits; require disposition and list removal in the same governed change for every real candidate dispatch, including failure. Replace the monitor’s blanket healthy-status expectation with timestamped before/after continuity evidence and the named pre-existing failure. Preserve STOP/reporting for unexplained new regressions.

This does not require adding 1235 to this window or fixing the older third-row problem inside it.

### R21-4 — P3: dispatch identity and post-window grants are described inconsistently

The owner’s ruling, checklist introduction/row 8 and runbook act-9 heading honestly describe the **AI steward dispatching under the owner’s account**, with immediate reporting and no separate human approval at that instant.

However, runbook lines 20, 24 and 275 still reserve act 9 to the owner personally.

[Checklist line 28](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-a55v/00_ARCHITECTURE/briefs/pravaha/runbooks/PROTECTED_WINDOW_SITTING_CHECKLIST_v1_0.md:28) also says the verifier/sealer hold “no grants” until SETTLED-1. Row 9 correctly demands positive verifier/sealer grants from 1206/1240, so that statement is false after the window.

**Closing change:** replace residual personal-dispatch wording with ruling 2. Describe the actual post-window state: 1206/1240 grants exist; 1241’s remaining ACL closure and subsequent provisioning remain held until their prescribed gates. No fresh owner decision is required to resolve this wording.

## Ranked amendments

1. **Before declaring the sitting executable:** close R21-1 by installing the proof workflow through an explicit permitted pre-row-6 merge and drain sequence.
2. **Before freezing the sitting packet:** close R21-2 and R21-4; publish one consistent checklist with current evidence, delegated dispatch identity and accurate grant state.
3. **Before the release-gate readback:** correct the monitor expectation in R21-3 and retain the documented pre-existing failure as an explicit baseline.
4. **Before either candidate’s first real dispatch:** replace the stale exclusion-expiry paragraph with the accepted every-dispatch disposition/removal commitment.
5. **During the already-prescribed preparation:** synchronize/re-pin #2999; verify `MERGEABLE`, workflow equality and selection tests before the first train merge and after every squash. Requalify the actual merged tree.

No additional protected migration or writer-algorithm change is requested.

## Step lines

**(a) Protected window — REJECT as packaged. NOW EXECUTABLE WITH ONLY OPERATIONAL ACTS REMAINING: NO.**

The inspected migration payloads, selection and composition controls are accepted. Close the pre-sitting procedure/document amendments above. Then execute the prescribed role, ledger, gap, drain, train, dispatch and post-window checks on the actual heads. Act 9 belongs to the steward under the recorded ruling. Keep the sitting outside S-L1; keep 1235 and 1241 outside this dispatch.

**(b) Registry binding — ACCEPT; prior acceptance stands within this review boundary.**

The inert registrations and accepted exclusion implementation do not reopen the binding acceptance. Current production identities, fingerprints and gap readbacks remain operational evidence to refresh.

**(c) First all-NULL candidate and seal — REJECT as an executable end-to-end package; reviewed source acceptance retained.**

Close the package amendments, including the every-dispatch disposition requirement. The remaining governed sequence still includes:

1. Official pre-S-L1 capture in its prescribed hour, both hashes retained, connection closed before S-L1.
2. Authentic SETTLED-1 evidence: whole-chart single build, 45+1 partitions, required assets `lit`, build agreement and natal-cell checks.
3. Comparison and the planned reviewed re-pin, including both constants, affected references, implementation lock and goldens; steward hold release.
4. Qualified window, post-SETTLED-1 1241/ACL provisioning, deployment, bootstrap and actual permission/API/log proofs.
5. Fresh all-NULL build and independent verification; required freezes/R0; actual-volume capacity and complete disposable-clone seal timing before approval.
6. R1, exact-identity approval, seal, R2, reconciliation, persisted receipts and cleanup.

SETTLED-2 is not added. G3 remains a numerical-activation gate.

**(d) Measurement — ACCEPT_WITH_AMENDMENTS; execution remains blocked by its existing prerequisites.**

Retain S1-REQ-EPHEMERIS, settlement/re-pin and hold release, Stage-1/Stage-2 freezes/readbacks and actual measurement evidence. The `5.0` absolute probe does not close the governed `4.1` prerequisite.

## What I could not verify

- Live GitHub PR mergeability, draft/HOLD transitions, remote freshness, squash results or actual CI runs. No fetch was performed.
- The authors’ 47/42 PostgreSQL rehearsal results, live trigger-catalog equality, actual privileges or transaction behavior. No disposable PostgreSQL was started.
- Production ledger id 925, registry fingerprints, zero evidence/dependents, enforced `gaps=[]`, monitor history, roles, IAM, approvals or deployment drains. These remain supplied steward evidence.
- Official capture, SETTLED-1, future re-pin output, candidate capacity, completed seal or production receipts.
- Broad upstream changes imported from main beyond this narrow review boundary.

No files were created or changed, no database was accessed, and the checkout remained clean.

