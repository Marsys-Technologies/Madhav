---
artifact: ASTRA_REVIEW_A5_5_SPEC_AMENDMENTS
version: "1.18"
reviewer: "Codex gpt-6-astra"
date: "2026-10-03"
verdict: REJECT
reviewed_commit: "cfada045e (campaign/pravaha)"
reviewed_heads:
  campaign: "cfada045e4525ae4f6ac430d960dfa16624b2df8"
  campaign_documents: "cab6dd3e98c0996e4351782376e6cc437ede8c14"
  repin_PR_2903: "4df9db1160b2e1aa757aceefb6fe5434c384b744"
  frozen_writer: "7678f77228b77e77cc0dd2fb04ddf36c01086ee5"
  composed_integration: "d680a1f206323fd35b6232e2a3c9bca4b7247f44"
  exhibit_PR_2952_tree_and_blob_comparison: "f28716b5cfb64740f713206908e5837bb2e86896"
  train_PR_2867: "e4d31c9ef82aa2e3874cd2095d295622f6756bf6"
  train_PR_2919: "ada3a8fbe509d1cf0b00ebf037edb90b3d31c43a"
  deployment_controls_PR_2961: "2ffb954afe11cf0bad02df71b548e35cf2da1863"
comparison_heads:
  round_18_repin_tool: "e8f417298f8fbe678b3986a0fd34909d1a941952"
  round_18_integration: "074923179a5ec685fed5cf72a0e905ba2d861fd8"
authority: "Review only; authorizes nothing."
---

**Verdict: REJECT the complete executable set.**

The original false-`CLEAN` identity defect is closed, and the comparison now handles the writer’s clipped edges correctly. Three bounded corrections remain:

1. **The composed deployment workflow omits the five pending protected migrations from its manual dispatch list.**
2. **Capture still reports success for a baseline with zero measurable boundaries at a level**, although comparison must later reject it.
3. **The checklist still contradicts its expected automatic-run behaviour and omits explicit drain/readback gates.**

Acceptance of the protected SQL and frozen writer’s window implementation stands. It does **not** qualify the defective composed workflow.

No file was written, no Git write command was run, and no database connection was made.

**Item status table**

“CLOSED” means closed in the inspected source or procedure, not performed in production.

| Item | Status | Verdict | Exact remaining change or qualification |
|---|---|---|---|
| R18-1 — envelope versus captured-row identity | CLOSED | ACCEPT | Every row’s build, system, tier and level are checked; chart/build/selection identity is bound to the validated capture. The false-`CLEAN` probe now exits 3. |
| R18-2 — unusable capture accepted at acquisition | PARTLY | REJECT | Self-parenting, missing references and foreign builds now refuse before output. Add acquisition-time **unclipped measurement coverage checks**, per R19-2 below. |
| R18-3 — checklist | PARTLY | ACCEPT_WITH_AMENDMENTS | W4, post-window W2, comparison directions and controlling schedule are corrected. Resolve automatic-run contradictions and add explicit drain/ledger readbacks, per R19-3. |
| R18-4 — stale operative text; missing Addendum 9 | CLOSED | ACCEPT | Runbook status/G6 statements and decision text are corrected; Addendum 9 is committed in the named source. |
| F-R18-1 — clipped window edges | CLOSED | ACCEPT | Comparison excludes both-build clips, requires unchanged instants, detects unflagged PD clips, refuses one-sided clips and zero measurements, and preserves lord/count checks. Acquisition coverage remains the separate R19-2 issue. |
| F-R18-2 — capture validation | PARTLY | REJECT | Same remaining change as R18-2/R19-2. |
| F-R18-3 — executable checklist and automatic deploys | PARTLY | ACCEPT_WITH_AMENDMENTS | Correct refusal path identified, but procedural exceptions/readbacks remain incomplete. Its row-8 success claim also requires the composed-workflow correction. |
| F-R18-4 — notice binding and W0 ingestion | CLOSED | ACCEPT | System, ayanāṃśa, source-message and build fields are checked; extra levels are identified as ignored; W0 checksum validation works. Notice semantics still depend on truthful source evidence. |
| F-R18-5 — application hardening | CLOSED | ACCEPT | Conflicting literal mappings refuse before writes; UUID canonicalization works; noncanonical-chart application refuses; lock and goldens are named. |
| Composed dispatch qualification | NOT CLOSED | REJECT | Restore the five omitted filenames while retaining the deployment-control changes; test the actual composed workflow selection. |
| Capacity checkpoint | NOT CLOSED | REJECT for first approval/seal | Actual candidate/verification/brief measurements and complete disposable-clone seal evidence remain operational prerequisites. |

**Probes**

I executed the tool file’s **98 non-database cases: 98 passed, zero failed**, both with the tool-head dependencies and with the composed dependencies. The two PostgreSQL cases were excluded.

Execution used Git-loaded modules, a RAM-only filesystem and controlled connection responses. The independent clipped-tree probes used the **real reader and all ten real reference rows**, without replacing `remeasure_reference_rows`. This does not reproduce the reported 100-case PostgreSQL run or 1,099-case composed run.

| Probe | Observed result |
|---|---|
| Envelope claims old pin; every row carries another build; checksum recomputed | **STOP, exit 3**, naming foreign/mixed builds. |
| Honestly labelled capture from another build | **STOP, exit 3**, naming envelope and row mismatches. |
| Self-parented capture through normal acquisition dispatch | **STOP, exit 3; no output artifact**; rollback once, close once, no commit. |
| First/last edges clipped on both builds at MD/AD/PD; remaining edges +6,993 s | **CLEAN, exit 0**; one start and one end excluded per level. |
| Level-3 clips with both flags false | Classified by the window instants and excluded correctly. |
| Clip present only on old build | **STOP**, including `window-edge status changed`. |
| Flagged clipped edge moves | **STOP**, including clipped instant `MOVED` and flag/bound inconsistency. |
| Clipped PD row changes lord | **STOP**, naming the refused subtree. Clipping does not exempt lord identity. |
| Every MD boundary clipped on both builds | Comparison **STOPs**: `ZERO unclipped measurements` for start and end. |
| Acquire that same all-clipped MD baseline | **Incorrect acquisition success: exit 0**; artifact accepted by the loader. See R19-2. |
| Across-ayanāṃśa range encoded as `[6990,6994]` | Invalid notice; **STOP**. |
| Range incorrectly transcribed as `{start:6990,end:6994}`, measured +6,993 s | ±2 s: **STOP**. ±5 s: **CLEAN**. See notice qualification below. |
| Notice explicitly names Raman | **STOP** on ayanāṃśa identity. |
| `--import-w0` with wrong checksum | **STOP, exit 3; no imported artifact**, no database access. |
| Valid W0 import | Accepted and rewritten with `meta.source="w0"` and the source file checksum. |
| Letter-bearing uppercase UUID in CLI and notice | Canonicalized; **CLEAN** against the corresponding lowercase database identity. |
| One old literal maps to two new literals | Refused before application writes. |
| Noncanonical chart with `--apply` | Usage refusal before connection. |

The ±5 s range result is a **limit of source verification**, not evidence of a genuine Lahiri measurement. A falsely relabelled pair of numbers within the declared tolerance is indistinguishable from legitimate start/end expectations. Retain and inspect the authentic SETTLED-1 message; do not widen tolerance to accommodate the across-ayanāṃśa range.

Additional source verification:

- All **ten migration hashes** match `EXPECTED_WINDOW_SHA256.txt` at the writer and integration heads.
- 1240 remains `05a8f897a0b8ae6b955915eced717ad30c98af485d490185333a88355707bc6b`.
- Integrated 1241 v7 remains `a3480710c7498065892965f23d9bee43dc700d4d8f16eb46ac8fb0ee601efefa`.
- Integration and exhibit have identical trees.
- The tool hash matches the packet: `3d2ed50e30fe0487957ffd14d79017aeaef3c55f91059ab94030ec7beb41edea`.

**New findings**

**R19-1 — P1: the composed workflow cannot perform checklist row 8.**

At `d680a1f20`, the `APPLY_GOCHARA_CONTRACTS_SCHEMA_MIGRATION` block selects only:

```text
1153, 1154, 1155, 1156, 1157
```

It omits:

```text
1204, 1206, 1232, 1233, 1240
```

The frozen writer’s workflow contains all ten. The composed workflow instead matches the older selection carried by the deployment-controls branch. [Composed dispatch block](https://github.com/Marsys-Technologies/Madhav/blob/d680a1f206323fd35b6232e2a3c9bca4b7247f44/.github/workflows/deploy.yml#L1078-L1094), [writer dispatch block](https://github.com/Marsys-Technologies/Madhav/blob/7678f77228b77e77cc0dd2fb04ddf36c01086ee5/.github/workflows/deploy.yml#L1073-L1113).

I replayed the actual shell selection with `npx` replaced by an argument-printing function:

| Head | Selected migration numbers |
|---|---|
| #2867 | 1153–1157, 1204, 1206 |
| #2919 and frozen writer | 1153–1157, **1204, 1206, 1232, 1233, 1240** |
| #2961, round-18 integration and current integration | **1153–1157 only** |

Consequently, assuming 1153–1157 are already applied, the composed manual job does not apply the pending five. Its following routine job encounters 1204 and refuses again. The assertion that the owner’s dispatch “applies exactly the five files” is false for the supplied integration/exhibit.

This defect **already existed in the round-18 integration**. I missed it then; round 19 did not introduce it. The migration-hash checks cannot detect it because the SQL files themselves are correct.

**Close:** correctly compose the writer’s complete dispatch selection with #2961’s phase/exception wiring. Add a source test that executes or extracts this workflow block and verifies the selected set, ordered pending five, and exclusion of 1241. Refresh the integration/exhibit evidence and check the workflow selection again on merged `main`.

**R19-2 — P2: acquisition still accepts a baseline that can never support a clean comparison.**

`validate_capture()` checks identity, checksum, tree, reference IDs/lords, flag consistency, natal presence and recorded counts. It does **not** check whether each level has measurable start/end boundaries. That check exists only in the later `shift_problems()`. [Capture validation](https://github.com/Marsys-Technologies/Madhav/blob/4df9db1160b2e1aa757aceefb6fe5434c384b744/platform/python-sidecar/scripts/gochara/repin_dasha_contract.py#L386-L409), [later measurement refusal](https://github.com/Marsys-Technologies/Madhav/blob/4df9db1160b2e1aa757aceefb6fe5434c384b744/platform/python-sidecar/scripts/gochara/repin_dasha_contract.py#L636-L657).

Reproduction through normal acquisition:

- Retain all ten real reference IDs, lords and valid parent links.
- Give the sole reference MD the two window bounds, with consistent clipping flags.
- Capture returns **0**, produces its artifact and both checksums, rolls back and closes.
- `load_capture_full()` accepts it; `validate_capture()` returns `[]`.
- Subsequent comparison refuses both MD sides for zero unclipped measurements.

This is a deliberately pathological synthetic baseline, **not a claim about the real captured population**. It nevertheless proves the remaining acquisition defect: the tool already has everything needed to discover this failure before S-L1.

If the new edges remain clipped, there is no measurement; if they cease being clipped, the one-sided-clip rule refuses. Waiting for replacement rows cannot repair this baseline.

**Close:** in the shared acquisition/load validator, require **at least one unclipped start and one unclipped end at every in-scope level**, using `edge_clipped()` so unflagged PD edges count correctly. Failure must return named exit 3 before successful capture/import output. Add normal-dispatch capture and W0 regressions preserving rollback/close and no-artifact behaviour.

**R19-3 — P2: the checklist anticipates the red run but does not yet govern it unambiguously.**

The source supports the automatic refusal path:

1. Automatic runs have no affirmative protected-window input; the protected job is manual-only.
2. Routine migration execution passes no `--only`.
3. The runner refuses a pending protected filename before executing that file.
4. All four service deployment jobs explicitly require `needs.migrate.result == 'success'`.

Therefore, **a red automatic run at the named protected-file refusal between rows 7 and 8 is fail-closed for that file and service deployment**. This is conditional on reaching that stage with the expected prerequisites. [Workflow gates](https://github.com/Marsys-Technologies/Madhav/blob/d680a1f206323fd35b6232e2a3c9bca4b7247f44/.github/workflows/deploy.yml#L968-L981), [routine command and deployment dependency](https://github.com/Marsys-Technologies/Madhav/blob/d680a1f206323fd35b6232e2a3c9bca4b7247f44/.github/workflows/deploy.yml#L1231-L1273), [protected-file guard](https://github.com/Marsys-Technologies/Madhav/blob/d680a1f206323fd35b6232e2a3c9bca4b7247f44/platform/scripts/migrate.ts#L153-L164).

But checklist v1.1 still has these defects:

- Its preamble permits automatic runs from the sitting’s merges, while row 7 still says **“a routine deploy ran in between”** is a STOP.
- Row 8 does not explicitly require the preceding automatic runs to finish, their results to be recorded, and no deploy run to remain running/queued before dispatch.
- It omits Fable’s requested **post-refusal migration-ledger readback**.
- The exception for “our own merges” does not restore the master runbook’s stricter **no-running/no-queued** precondition during acts 3 and 10.

Also, **“applied NOTHING” is not a general property of the guard**. The runner checks files sequentially and can commit earlier ordinary migrations before encountering a protected file; tracker setup/backfill also precedes that refusal. A red result alone is insufficient evidence of zero changes. [Runner ordering](https://github.com/Marsys-Technologies/Madhav/blob/d680a1f206323fd35b6232e2a3c9bca4b7247f44/platform/scripts/migrate.ts#L744-L840).

**Close:** explicitly exempt only the recorded, named protected-file refusal from row 7’s STOP condition; require ledger comparison and skipped-deployment-job evidence; drain automatic runs before row 8, accounting for outstanding CI-triggered runs; restore the stricter drain conditions around acts 3/10. Say **“no protected migration or service deployment”**, with any stronger no-change claim established by readback.

W4 placement, post-window W2, both W5/W6 directions, the manifest comparator, named W3 relations, and the single controlling S-L1 schedule are otherwise corrected. [Checklist v1.1](https://github.com/Marsys-Technologies/Madhav/blob/cab6dd3e98c0996e4351782376e6cc437ede8c14/00_ARCHITECTURE/briefs/pravaha/runbooks/PROTECTED_WINDOW_SITTING_CHECKLIST_v1_0.md).

**Capture-at-acquisition assessment**

The ordinary capture path now performs the loader’s validation **before writing or announcing success**. Its owned connection uses REPEATABLE READ and READ ONLY; rows, flags, natal values and census are acquired together; rollback and close happen before file output. The self-parented and foreign-build acquisition failures preserve that lifecycle. R19-2 is the remaining demonstrated late-discovery defect. [Acquisition path](https://github.com/Marsys-Technologies/Madhav/blob/4df9db1160b2e1aa757aceefb6fe5434c384b744/platform/python-sidecar/scripts/gochara/repin_dasha_contract.py#L922-L972).

The capture retains:

- Full-precision selected boundaries, row/build identities, parent links, lords and clipping flags; canonical-reader provenance such as merged IDs/indexes where supplied.
- The ten natal values, subjects, fact IDs, tiers and separate natal build identities.
- Chart/build/selection identity, per-level counts, tool commit/hash, timestamp, elapsed time and transaction/snapshot evidence.
- The same-snapshot whole-daśā build/partition census and the two asset states.

The **data checksum** covers chart/build/selection plus rows and natal data. Metadata is outside that checksum; the separately retained **whole-file checksum** covers it. Chart and ayanāṃśa selection are established by the SQL predicates and envelope; those fields are not independently retained on every reader row.

Future counterpart changes, actual notice agreement and old/new natal-cell changes necessarily await settlement. Suvarṇa’s whole-chart old-ID→natural-key map remains a **separate pre-window artifact for later resonance work**; this capture does not replace it.

Two minor documentation corrections remain: the actual census is under `meta.census`, and measurement retains microseconds—only application literals are formatted to whole seconds.

**Ranked amendments**

| Rank | Closing change | Gate |
|---|---|---|
| 1 — P1 | **R19-1:** restore and test the composed workflow’s complete protected migration selection; refresh integration/exhibit and final-main qualification. | Executable protected window |
| 2 — P2 | **R19-2:** reject zero-measurement baselines at capture/import acquisition, per level and boundary side. | Official pre-S-L1 capture; re-pin |
| 3 — P2 | **R19-3:** reconcile expected-red wording, add run-drain and ledger/job readbacks, preserve acts 3/10 drain conditions. | Sitting checklist |
| 4 — operational | Obtain actual candidate/verification/brief capacity evidence and complete clone-seal measurements. | First approval/seal |
| 5 — minor | Correct capture-envelope and precision descriptions. | Documentation accuracy |

The reported composed pass count does not close R19-1; a test of the **actual dispatch selection** is required.

**Step lines**

**(a) Protected window — ACCEPT of the SQL and frozen writer implementation stands; REJECT the supplied composed dispatch qualification.**

Correct R19-1 and the checklist before relying on this executable packet. No protected SQL amendment is requested. Preserve the train’s before-W1-or-after-SETTLED-1 schedule, exact merged-main checks, owner-only dispatch and operational readbacks. Keep 1241 outside the train.

**(b) Registry binding — ACCEPT; prior source acceptance stands.**

1241 v7 is unchanged. Application after SETTLED-1 and exact ACL/read-access readbacks remain operational prerequisites.

**(c) First all-NULL candidate and seal — REJECT; the remainder is not yet only operational.**

**No.** R19-1/R19-2 and the checklist correction remain now. After they close:

1. Take the qualified official pre-S-L1 capture and retain both checksums/provenance.
2. Receive actual SETTLED-1 evidence; verify build/notice agreement, 45+1 partitions, both assets `lit`, forensic evidence and natal-cell comparison.
3. Run the tool; review and merge both pins, reference changes and literal rulings, regenerated lock and affected goldens. Obtain the steward’s hold release.
4. Complete window/1241 qualification, provisioning, exact-image deployment, bootstrap and actual permission/API/log evidence.
5. Build a fresh all-NULL candidate; independently verify every required grain after the last build.
6. Complete capacity evidence and the prescribed freeze, R0/R1/R2 readbacks, exact approval, seal, reconciliation and cleanup.

SETTLED-2 is not added as a gate for this candidate. G3 remains a numerical-activation decision.

**(d) Measurement — ACCEPT of prior scope stands; execution remains BLOCKED.**

Carry forward S1-REQ-EPHEMERIS, D6, settlement/re-pin and hold release, Stage-1/Stage-2 freezes/readbacks and actual measurement evidence. No fresh measurement-source acceptance is claimed here.

**What I could not verify**

- The official capture, trial-capture checksum, real clipped-row population or real SETTLED-1 output.
- The 100-test PostgreSQL result or 1,099-test composed result.
- Any actual automatic deploy, owner dispatch, production ledger, IAM/ACL state, Cloud Run execution or log/approval representation.
- Real capacity, clone-seal duration or first-seal receipts.
- Fresh source qualification of the measurement branch or unrelated accepted components.

No disposable PostgreSQL was started. The final checkout remained clean at `cfada045e`.