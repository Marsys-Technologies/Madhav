---
artifact: ASTRA_REVIEW_A5_5_SPEC_AMENDMENTS
version: "1.16"
reviewer: "Codex gpt-6-astra"
date: "2026-10-03"
verdict: REJECT
reviewed_commit: "29104c422 (campaign/pravaha)"
reviewed_heads:
  campaign/pravaha: "29104c4226b104744bbc71617cfa3301997c39dd"
  origin/pravaha/a53-am5-inventory: "699638fbe8538160470dac4c52d5b0d0adce5e96"
  "PR #2961 — origin/pravaha/b6-act7-verifier-secret-isolation": "2ffb954afe11cf0bad02df71b548e35cf2da1863"
  "PR #2975 — origin/pravaha/b6-gochara-seal-workflow": "bd05b59989f76a3f5f003da65387420996bac595"
  "PR #2976 — origin/pravaha/b6-gochara-verification-job-def": "ef31ffe0f807b30cfa85c72418ab72f1c658e575"
  "PR #2949 — origin/pravaha/b6-1241-verifier-sealer-grants": "c26743b5db35ce63c55bd83975ecaf3970023b6a"
  origin/pravaha/b6-composed-rehearsal-integration: "6dcbc450111ce1a94ac0967c9180986f303f9166"
  "PR #2903 — origin/pravaha/b6-am10-repin-tool": "5d1476d61308c9568c44563e9d57377db93cc22f"
  "PR #2952 — origin/pravaha/b6-composed-rehearsal — tree comparison only": "730879ea3900e551ac375dbaee0590cae9e6f5c7"
comparison_refs:
  round_16_writer: "1e6e55534d79c80955ac5a50d253230a9db1f22f"
  round_16_pr_2961: "2b91a1e5f4fe61ed259c4c4ada44cd17c206a9c2"
  round_16_pr_2976: "668718fc31ea5a7d2aceb9ae4c1152bca37f15f6"
authority: "Review only; authorizes nothing."
---

## Verdict

**REJECT the complete executable set.**

**Step (a), the protected window, is now UNBLOCKED at source AND procedure within this review. Only the ordered operational preconditions below remain.** The accepted protected-window SQL and 1241 v7 are byte-identical to the accepted versions; I did not reopen their SQL semantics.

**Step (c) is not waiting only on SETTLED-1, performing the re-pin, capacity evidence and operational receipts.** The re-pin tool needs substantive corrections, and §5.5 retains one impossible comparison.

The original IAM, annotation, phase, shared-contract and window-manifest defects are closed. The new blockers principally concern #2903: its ordinary CLI cannot read the rows, its application leaves the independent verifier pinned to the old build, and its comparison can accept an unexpected shift or omit rows carrying a lord change.

No file was written. No production database was contacted.

## Item status table

“CLOSED” below means closure in the inspected source or procedure. It does not claim that production acts or the authors’ full database suites were independently executed.

| Item | Status | Verdict | Remaining change or qualification |
|---|---|---|---|
| **R16-1 — composed annotation handling and project canonicalisation** | **CLOSED** | **ACCEPT** | Valid annotations pass the composed sequence; owner, service-agent and exception resources accept project ID/number equivalence. |
| **R16-2 — phase wiring and remedies** | **CLOSED** | **ACCEPT** | Phase transitions, readbacks, compensation and exception exports are present. Actual IAM execution remains operational. |
| **R16-3 — §5.5 comparisons and stale descriptions** | **PARTLY** | **REJECT** for first-seal procedure | SQL casts and auxiliary-versus-pinned comparisons are corrected. Comparison 2(e) still compares `produced_by` with an approval-file field that does not exist. |
| **R16-4 — W5 condition/body detection; W6 preservation** | **CLOSED** | **ACCEPT** | Actual conditions and function-body hashes are represented; W5 checks query failure; W6 compares both directions. Actual production baseline remains required. |
| **R16-5 — malformed v2 retries, annotations, int64** | **CLOSED** | **ACCEPT** | All three callers refuse the tested invalid-present cases. Shared copies are identical. |
| **R16-6 — lifecycle, chronological claim, integration evidence** | **CLOSED** at source/claim level | **ACCEPT** | All 16 pairs are parameterised; chronological claim is narrowed; historical enrichment is exercised separately; v7 static test is included. Full reported suite counts were not independently rerun. |
| **F-R16-1 — phase variable assigned by no act** | **CLOSED** | **ACCEPT** | Acts 3/10 now assign and read it back. |
| **F-R16-2 — exceptions not delivered to workflows** | **CLOSED** | **ACCEPT** | Four routine preflight steps and #2976 export it. |
| **F-R16-3 — landed/pending and G3 wording** | **CLOSED** | **ACCEPT** | First all-NULL approval does not wait for the numerical-activation G3 decision. The separate R16-3 field-mapping residue remains. |
| **F-R16-4 — log freshness and permission sources** | **CLOSED** | **ACCEPT** | Explicit execution-start timestamp bound replaces ineffective freshness usage; get/list permissions are separately accounted for. |
| **F-R16-5 — function hash and actual-1071-table test** | **PARTLY** | **ACCEPT_WITH_AMENDMENTS** | Function hash is present. Actual-table, real-login interaction test remains planned; this optional evidence item does not reopen (a). |
| **F-R16-6 — natal wording and duplicate read** | **CLOSED** | **ACCEPT** | Both disclosure branches say `lahiri_chitrapaksha`; one tier read supplies both fields. |
| **Capacity** | **NOT CLOSED** | **REJECT** for first approval/seal | Actual-volume evidence remains absent. This is not a protected-window source blocker. |
| **Round-16 optional rank 8** | **PARTLY** | **ACCEPT_WITH_AMENDMENTS** | Reading natal tiers once is done. Optional legacy statement locks remain outstanding. |
| **Stream A 699638fbe delta** | **PARTLY** as a composed post-re-pin delivery | **ACCEPT_WITH_AMENDMENTS** | Current-pin G6 behavior, natal changes and implementation lock check out. #2903 must update the independent verifier pin. Absolute-probe non-finite handling merits the bounded hardening below. |
| **#2903 re-pin tool** | **NOT CLOSED** | **REJECT** | R17-1 through R17-7 below. |
| **Protected-window SQL; 1241 v7** | **CLOSED / unchanged** | **ACCEPT** | No SQL amendment requested by this review. |

## Probes

### Frozen bytes and integration

I compared all ten entries in `EXPECTED_WINDOW_SHA256.txt` across the previous accepted writer, `699638fbe`, and `6dcbc4501`. They match. In particular:

| File | SHA-256 |
|---|---|
| 1204 | `a0b267f7ef6002a1997c30d34595ec3b86147ca617bf70ef8a05de55b8407ca1` |
| 1206 | `941c79f59f2d3d3125dc5ca680430d4a91a7dcddb53fc6daa9a9da8819e410d7` |
| 1232 | `f2ef6406604b819d5f443e32c1e70914f2337ead8867f12e0aecd96d13f1ec44` |
| 1233 | `958b911703eee3528e1db75624984020964b8d31fe3fe286d64071368bd5a705` |
| 1240 | `05a8f897a0b8ae6b955915eced717ad30c98af485d490185333a88355707bc6b` |
| 1241 v7, #2949 versus integration | `a3480710c7498065892965f23d9bee43dc700d4d8f16eb46ac8fb0ee601efefa` |

The integration and #2952 exhibit have the same Git tree. The integration carries the v7 registry-SELECT static test.

I independently recomputed the implementation identity from the frozen source of all **60 listed modules**, using the verifier’s digest function with Git blobs supplying the source text. All three stage digests and the combined lock match:

`ff393d982a52be92b64d75035d5d39b5e6017c478ac098fbd2084a0ce935afde`.

### Original exact-function failures

The executable probes ran frozen functions in memory. External calls and file writes were intercepted where necessary; no production operation was performed.

| Probe group | Result |
|---|---|
| **38 TypeScript preflight probes** | Expected outcomes throughout. Tests traversed `assertVerifierInheritedControl` **then** `assertEffectiveIsolation`. |
| Valid comma-form annotation on an ordinary resource | Accepted through both stages. |
| Empty, JSON-map, malformed, trailing-comma or conflicting-alias annotation | Refused. |
| Ordinary-resource annotation redirected to verifier secret | Refused. |
| Declared owner and canonical Cloud Run service agent, project ID versus number | Accepted in both representations. Service-agent probe included `iam.serviceAccounts.actAs`. |
| Declared exceptions, all ID/number combinations | Canonicalised correctly. Malformed triples and conditional exceptions refused. |
| Project/folder/organisation policy-writing capability | Refused without the exact exception. An exception did not exempt a binding from the shared isolation gates. |
| Phase matrix | Staged/empty and deployable/exact-policy passed; staged/deployer, deployable/empty, missing and invalid phase failed. |
| **44 Python cases through each of three callers: 132 outcomes** | Deployment readback, pre-execution job check and executed-resource check behaved consistently. |
| Invalid-present v2 retries | Booleans, malformed strings, negatives, floats, padded values, overflow and malformed document shapes refused. |
| v1/v2 retry combinations | Either valid zero representation could supply the value; absent-both, nonzero, disagreement and invalid-present cases refused. |
| Secrets annotation scan | v1 and v2-only annotation presence refused on all three paths, including empty annotation values. |
| Integer domain | Canonical non-negative integers through `2**63 - 1` accepted by the parser; negatives, overflow, booleans, floats and noncanonical strings refused. |
| Resource spellings | Supported equivalent integer quantities accepted; unsupported fractional/exponent/case variants refused. |

The contract copies in #2975, #2976 and integration have SHA-256:

`caf6fe767682c9699c12bfe9d91753ecc50400500eb267e7999639ac7d51311f`.

The phase procedure also accounts for the short fail-closed transition intervals: no routine deployment may be running or queued during those changes.

### §5.5, W5 and W6

- **SQL type resolution:** both UNION branches now explicitly emit `build_id::text`, and count columns are also text. That resolves the original UUID/TEXT conflict under PostgreSQL’s documented UNION rules. This is source/type analysis, **not a new PostgreSQL execution**. [PostgreSQL type resolution](https://www.postgresql.org/docs/current/typeconv-union-case.html)
- **Comparison 1:** whole-chart inventories and whole-table md5/count readbacks are compared only between R0/R1/R2.
- **Comparison 2:** consumed-row digests use their original derivations; registry checking is assigned to the seal job; image comparison extracts the digest component. The remaining `produced_by` mistake is detailed below.
- **W5:** the committed manifest contains **32 relations, 106 triggers and 14 fields per trigger**, including the actual WHEN expression and function-definition md5. Mutating either field caused the expected line to be missing from comparison. I inspected the transactional WHEN-change negative control and rollback check; I did not execute its PostgreSQL portion.
- **W6:** I ran the exact `comm -23` and `comm -13` operations using anonymous pipes. Preserved baseline plus a boundary addition passed preservation; disappearance and changed enablement appeared in `-23`; unexpected additions appeared in `-13`.
- **Log timestamp:** the exact embedded workflow Python produced the same UTC lower bound from UTC and `+05:30` timestamps, and refused missing `startTime`.

Google’s current documentation confirms that `roles/run.jobsExecutorWithOverrides` supplies run, override and cancel, while get/list permissions need separate coverage. This verifies the runbook’s role description, not the workflow identity’s actual grants. [Cloud Run IAM roles](https://docs.cloud.google.com/run/docs/reference/iam/roles)

### Stream A: G6 semantics and independence

A “second build” means a second **distinct `coalesce(build_id::text, 'NULL')`** among the chart’s:

- `system_id = 'vimshottari'`;
- `ayanamsha_id = 'lahiri_chitrapaksha'`;
- **all tiers, all levels and all dates**, without restricting to the consumed horizon.

Multiple rows or levels carrying the same build do not constitute another build. Another system or ayanāṃśa is outside this particular guard. A NULL alongside a real build counts as another identity.

The writer and verifier independently query `chart_dashas`. The verifier does not call the writer’s guard or accept its supplied build list.

| Guard input | Writer / verifier result |
|---|---|
| Sole current canonical pin | Accept / accept |
| Second build only at another tier or level 4 | `dasha_builds_mixed` / same |
| Current pin plus NULL | `dasha_builds_mixed` / same |
| Sole wrong canonical build | `dasha_build_not_pinned` / same |
| Sole NULL on canonical chart | `dasha_build_not_pinned` / same |
| Another build only in another system or ayanāṃśa | Ignored by both G6 queries |
| Empty set | Neither G6 guard itself refuses; this is not a completeness proof |
| Sole build on a noncanonical chart | Accepted by this guard |

The guard deliberately rejects coexistence even when the old rows are outside the horizon or below the read tier. That is consistent with the stated completed-SETTLED-1 invariant. It would reject a policy that permitted historical builds to coexist, but that is not the policy supplied for this candidate.

**The concrete legitimate-state refusal occurs after #2903 applies:** the writer accepts the replacement build while the verifier still refuses it against its copied old pin. R17-2 closes that composition failure.

The narrower G6 query does not replace the operational whole-chart single-build, 45+1-partition and asset-state checks.

### Stream A: absolute probe and natal disclosure

I checksum-verified the local `/tmp/se1` corpus against all three frozen file pins, then executed the **actual frozen absolute-probe function** with the real Swiss library:

- Prior Fagan/Bradley mode: **256.5156961838706°**.
- Prior Raman mode: **256.5156961838706°**.
- Prior Lahiri mode: **256.5156961838706°**.
- Fresh worker thread: **256.5156961838706°**.
- Nonexistent ephemeris path: refused because the result was not served by Swiss files.

Path setting, Lahiri mode selection and calculation occur together, synchronously, under the shared lock in the calling thread. The tolerance is absolute **`1e-9` degrees**. The check executes even without `jd_range`.

Exact `verify_inputs` probes accepted the reference and a `0.5e-9` offset, and refused `2e-9`, a 24-degree offset and infinity. **NaN passed**, as discussed under optional hardening. I found no production caller supplying the `absolute_probe` test hook, and no normal-call bypass demonstrated by the real-library probes.

Natal disclosure changes are correct: both branches name `lahiri_chitrapaksha`; observed tiers are read once and used for both the text and structured field. The standard sentence remains conditional on exactly the ten named subjects all carrying `single`.

### #2903 adversarial probes

| Case | Observed result |
|---|---|
| Psycopg 2 connection interface passed to exact multilevel reader | Returned `[]`; installed Psycopg 2 connection class has no `execute` method |
| Documented `--capture-old old.json` command | Argument-parser exit 2: missing `--new-build-id` |
| Ordinary matched-row lord change | Detected |
| Ordinary finite wrong shift | Refused |
| Synthetic notice: expected 6,993 ± 2 seconds; actual shift 6,995.9 seconds | **Accepted after truncation to 6,995 seconds** |
| NaN/infinite tolerance, or NaN expected shifts | **Accepted unexpected measurements** |
| Settlement notice without `new_build_id` | **Accepted** |
| Extra self-parented row, with distinct level/start key | **Ignored by path index; no decision stop** |
| Lord change in a self-parented row | **Ignored; no lord-flip stop** |
| Application with unclassified boundary literals | `NeedsRuling`, zero intercepted writes |
| Application with an explicit keep ruling | Event literal retained; writer pin changed |
| Independent verifier after that application | Old pin retained; new build refused |
| `--dry-run --capture-old` | **Actual capture function invoked `write_text`** |
| `--dry-run --capture-old --apply` | Same write path; mutual-exclusion check bypassed |
| `--apply` before the announcement that re-pin is already merged | Refused, creating the sequencing cycle below |

All application/capture writes in these probes were intercepted into RAM.

## New findings

### R17-1 — P2: the ordinary re-pin CLI cannot perform its required reads

At #2903, `_capture_old` and `main` create a **Psycopg 2** connection. `DD.fetch_dasha_periods_multilevel` calls **`conn.execute(...)`**, catches the resulting exception and returns an empty list.

Consequently, ordinary capture reports that the pinned build has no rows, and ordinary comparison cannot obtain the new rows. This is a driver-interface failure, not evidence of absent database rows. Psycopg 2 executes through cursors. [Re-pin connection setup](https://github.com/Marsys-Technologies/Madhav/blob/5d1476d61308c9568c44563e9d57377db93cc22f/platform/python-sidecar/scripts/gochara/repin_dasha_contract.py#L448), [row reader](https://github.com/Marsys-Technologies/Madhav/blob/5d1476d61308c9568c44563e9d57377db93cc22f/platform/python-sidecar/services/gochara_grammar/dasha_data.py#L218), [Psycopg 2 connection API](https://www.psycopg.org/docs/connection.html)

There is also a capture-mode argument error: `--new-build-id` is globally required, although pre-S-L1 capture does not use it and the documented capture command omits it.

**Close:** use a consistent supported connection/reader interface while retaining database read-only mode; require the replacement build only for comparison/application; test the ordinary CLI connection path without replacing the row reader with a lambda.

### R17-2 — P2: applying the re-pin leaves the independent verifier on the old build

`apply_repin` updates `permission.py` and test files. It does not update:

`services/gochara_kernel/inventory_verifier.py::_C_BUILD`.

That constant governs both the new G6 check and the verifier’s consumed-population checks. My composed probe after application produced:

```text
writer after repin: ACCEPT
verifier after repin: dasha_build_not_pinned
```

[Application targets](https://github.com/Marsys-Technologies/Madhav/blob/5d1476d61308c9568c44563e9d57377db93cc22f/platform/python-sidecar/scripts/gochara/repin_dasha_contract.py#L369), [independent verifier pin and query](https://github.com/Marsys-Technologies/Madhav/blob/699638fbe8538160470dac4c52d5b0d0adce5e96/platform/python-sidecar/services/gochara_kernel/inventory_verifier.py#L661).

**Close:** deliberately update both governed pin declarations in the same reviewed re-pin. Preserve the verifier’s independent query. Add a composed test proving both reject the old build and accept the new one, then regenerate the implementation lock and affected goldens.

### R17-3 — P2: shift validation loses precision and permits non-finite values

`norm_rows` converts timestamps to whole-second strings **before** `shift_stats` measures their differences. This can move an out-of-tolerance observation inside the accepted interval.

Separately, notice validation does not require finite expected shifts or tolerance. Comparisons against NaN never produce the intended greater-than result; infinite tolerance accepts arbitrary finite deviations.

[Normalisation](https://github.com/Marsys-Technologies/Madhav/blob/5d1476d61308c9568c44563e9d57377db93cc22f/platform/python-sidecar/scripts/gochara/repin_dasha_contract.py#L77), [notice and tolerance checks](https://github.com/Marsys-Technologies/Madhav/blob/5d1476d61308c9568c44563e9d57377db93cc22f/platform/python-sidecar/scripts/gochara/repin_dasha_contract.py#L235).

**Close:** preserve full timestamp precision in captures and comparisons; separate permission-literal formatting from measurement. Require finite numeric expectations and finite, non-negative tolerance, with explicit coverage of levels 1–3 and both boundaries. Test just-inside/just-outside fractional cases and non-finite inputs.

### R17-4 — P2: unreachable rows evade row-count and lord-change checks

`index_paths` walks only from `parent_row_id = None`. `integrity` detects missing parents but does not detect self-parenting, cycles or rows unreachable from a root. `decide` checks differences between the resulting indexes, not complete input-row coverage.

I reproduced both:

- Three old rows versus four new rows: the extra self-parented row disappeared from comparison.
- Four old versus four new rows: a lord changed on the unreachable row, but no flip was reported.

The counterexamples used distinct level/start keys. No malformed-tree database execution is claimed.

[Path index, integrity and matching](https://github.com/Marsys-Technologies/Madhav/blob/5d1476d61308c9568c44563e9d57377db93cc22f/platform/python-sidecar/scripts/gochara/repin_dasha_contract.py#L89).

**Close:** validate root/parent-level structure and reject cycles; require every in-scope canonical row to be indexed exactly once on both sides; explicitly compare per-level row totals. A malformed old capture must also stop the comparison.

### R17-5 — P2: “build equals SETTLED-1” is not enforced when the notice omits its build

`load_notice` accepts a notice without `new_build_id`. Later:

```python
notice.get("new_build_id") not in (None, a.new_build_id)
```

expressly permits its absence. The mechanical checks then prove agreement with the **CLI argument**, not with a build identified by SETTLED-1.

[Notice/build comparison](https://github.com/Marsys-Technologies/Madhav/blob/5d1476d61308c9568c44563e9d57377db93cc22f/platform/python-sidecar/scripts/gochara/repin_dasha_contract.py#L519).

**Close:** require a valid, explicit settlement build identifier and exact agreement among notice, requested build and database readback. Bind the retained notice to the reviewed upstream evidence.

The forensic-report argument is currently only checked for truthiness. It does not establish that the report exists or that seven anchors passed. That remains an owner-evidence dependency; the tool’s `CLEAN` label must not be presented as independent validation of those anchors.

### R17-6 — P2: the application gate requires the result it is supposed to prepare

`--apply` requires the steward announcement:

> “SETTLED-1 received AND daśā re-pin merged”

But application is what prepares the re-pin changes for review and merge. Once the checkout already contains that re-pin, passing the same replacement build instead reaches “new build equals the current pin.”

[Application gate](https://github.com/Marsys-Technologies/Madhav/blob/5d1476d61308c9568c44563e9d57377db93cc22f/platform/python-sidecar/scripts/gochara/repin_dasha_contract.py#L470).

**Close:** distinguish post-SETTLED-1 preparation of the reviewed re-pin from resumption of production Gochara work. Permit the authorised read-only comparison/local patch preparation after settlement; keep production build/verification/brief/measurement held until the reviewed re-pin is merged and the steward lifts that hold.

### R17-7 — P2: dry-run can write or overwrite a capture file

Capture dispatch occurs before the dry-run/application compatibility checks. Therefore both of these reach `write_capture`:

```text
--dry-run --capture-old …
--dry-run --capture-old … --apply
```

The probe executed the actual capture function and intercepted its `Path.write_text` call.

**Close:** validate mode combinations before capture dispatch or database connection. Either refuse capture with dry-run or implement capture preview without writing. Test dry-run across every dispatch path.

### R16-3 residue — §5.5 compares against a nonexistent approval field

Comparison 2(e) says the persisted brief’s `produced_by` equals the approval file’s counterpart. The actual `seal_approval/2` output contains:

```text
schema, brief_digest, brief_id, producer_execution_id,
run_id, run_attempt, approver_login, approved_by_note
```

There is no `produced_by`. The persisted producer is the database login `gochara_verifier`; `approver_login` identifies a different role in the process.

**Close:** state explicitly:

- persisted brief `produced_by == 'gochara_verifier'`;
- persisted brief/receipt/approval `brief_id` and producer execution identifiers agree;
- approval identity is checked separately;
- commit and image comparisons retain their already specified counterparts.

No SQL or approval-schema expansion is needed.

### R17-H1 — P3, nonblocking hardening: NaN passes the absolute comparison

In `verify_inputs`, this test accepts NaN:

```python
abs(sun_now - reference) > tolerance
```

Require `math.isfinite(sun_now)` before the comparison and refuse a non-finite result with the named mismatch.

**Scope:** demonstrated through the function’s injectable probe seam. Real Swiss calls on the checksum-matched corpus returned the exact finite reference; no ordinary production-input bypass was demonstrated. This is not a reason to reopen the protected window.

## Ranked amendments

| Rank | Exact closing change | Blocks |
|---|---|---|
| **1 — R17-1** | Repair driver/reader compatibility and capture-mode arguments; exercise the normal CLI path | Old-row capture and usable re-pin |
| **2 — R17-2** | Re-pin writer and independent verifier together; composed old/new acceptance test; new lock/goldens | Post-settlement verification and **(c)** |
| **3 — R17-3** | Compare full-precision timestamps; strictly validate finite expectations/tolerance | Trustworthy shift acceptance |
| **4 — R17-4** | Require complete, acyclic row coverage and equal per-level totals | Trustworthy lord/count acceptance |
| **5 — R17-5** | Require and bind the SETTLED-1 build ID | Settlement identity |
| **6 — R17-6** | Remove the prepare-versus-already-merged sequencing cycle while preserving the production hold | Executable re-pin procedure |
| **7 — R17-7** | Enforce no-write dry-run before every mode dispatch | Safe tool use |
| **8 — R16-3 residue** | Correct §5.5’s producer/approval field mapping | First approval/reconciliation |
| **9 — operational capacity** | Measure actual counts, widths, bytes, runtime, memory and clone-seal cost; demonstrate acceptable bounds | First approval/seal |
| **Optional** | Finite absolute-probe guard; actual-1071-table interaction test; remaining legacy statement locks | Additional hardening/evidence |

After governed Python changes, refresh the final composed evidence and implementation identities. **No protected-window SQL change is requested.**

## Step lines

### (a) Protected window — ACCEPT; UNBLOCKED at source AND procedure

**Yes: only operational acts and their evidence remain for (a).** In order:

1. **Open the governed sitting:** owner fixes dispatch timing and SQL administration route; respect the S-L1 merge freeze; ensure no routine deployment is running or queued during phase transitions.
2. **Freeze and qualify the actual candidate:** identify the final combined commit, retain composed/window evidence for its bytes, refresh PostgreSQL version and migration ledger, establish routine predecessors, and confirm 1206 remains unapplied with its expected objects absent.
3. **Perform pre-window catalog checks:** W3 first, then W1/W2; establish required relations, prohibited-chart absence, existing governed rows/seals, effective writers, helper EXECUTE and actual caller isolation. Capture and review the real W6 legacy baseline.
4. **Land the prerequisite controls and provision in the stated order:** acts **3 → 10 → 4 → 11**, with staged/deployable assignments and readbacks, actual IAM/secret/account checks and every exception evaluated through the composed gates.
5. **Perform combined 1 + 2a:** verify roles, memberships, ownership, verifier secret version and password-null sealer state. Remove temporary act-11 capability after every terminal outcome; inventory ambiguous outcomes.
6. **Establish act 5 and prove the no-secret approval gate:** protected-branch waiting, prohibited-branch refusal, steward approval, continuation and captured approval-history shape.
7. **Merge the protected train without 1241 and without an intervening routine deployment.** Recheck all ten migration hashes and the committed expected manifest on the actual merged commit.
8. **Owner personally dispatches act 9:** `1204 → 1206 → 1232 → 1233 → 1240`. Record per-file results and recovery if needed.
9. **Qualify the result:** ownership, capability revocation, PUBLIC EXECUTE and required checks; W5 manifest comparison and both W6 directions. Resolve every unexplained difference before accepting the window.

1241 follows through the ordinary post-window route, with exact effective ACL verification. **SETTLED-1 and re-pin completion are not prerequisites for accepting the protected-window source/procedure.**

### (b) Registry binding — ACCEPT; UNBLOCKED

The prior acceptance stands. Binding/readback on the actual selected registry versions and retaining the final identities remain operational. No round-17 closure regression was found.

### (c) First all-NULL candidate and seal — REJECT; still blocked by source/procedure work

**Beyond receiving SETTLED-1, performing a re-pin, collecting capacity evidence and executing operational acts, the remaining work is R17-1…7 and the R16-3 field-mapping correction.** Refresh the composed evidence after those changes.

Then the operational order is:

1. **Before S-L1**, retain trustworthy old daśā rows and the ten natal longitudes, with their hashes, using the corrected capture path.
2. Receive the actual SETTLED-1 evidence. Verify the whole-chart single build, **45 non-scope + 1 scope-cap partitions**, `ga_dashas` and `ga_positions` both `lit`, notice/build agreement, upstream forensic evidence and the natal-cell comparison.
3. Prepare, review and merge the corrected re-pin, including **both** pins and regenerated implementation identity. Obtain the steward’s production-hold release.
4. Complete post-window 1241/ACL/read-access checks, act 2b, verifier deployment by digest from the final sealing commit, bootstrap, actual API/log-shape qualification and permission proofs.
5. Build the fresh all-NULL candidate and independently verify every required grain **after the last build**. Discard pre-settlement candidate evidence.
6. Measure actual capacity and disposable-clone seal costs before approval.
7. Enforce the input/registry/corpus/image freeze; execute corrected R0/R1/R2 comparisons.
8. Approve the exact brief digest/run/attempt/brief ID; execute seal, reconcile publication/seal/receipt state and verify cleanup.

SETTLED-2 is not added as a gate for this inspected candidate. The G3 owner decision remains a gate for numerical activation, not this disclosed all-NULL proof.

### (d) Measurement — remains BLOCKED

Carry forward the accepted measurement-only scope of #2923; its source was not reopened here.

Outstanding: **S1-REQ-EPHEMERIS**, settlement/re-pin and applicable hold release, completed Stage-1/Stage-2 freezes and readbacks, and actual measurement evidence. The new `5.0` absolute probe does not itself implement the missing governed `4.1` measurement prerequisite.

## What I could not verify

- I did **not** independently reproduce the authors’ **993-pass**, **47/47**, **42/42** or **112-pass** suites. The read-only sandbox did not permit creating the disposable PostgreSQL environment. No database instance was started.
- Consequently, §5.5 SQL execution in both catalog-type variants, PostgreSQL WHEN-expression rendering, lifecycle database behavior and actual legacy-1071 trigger interaction were not freshly executed here.
- No production ledger, catalog, roles/RLS, IAM policy, Cloud Run resource, Cloud Logging entry, GitHub approval response, SETTLED-1 outcome or capacity measurement was verified.
- At `29104c422`, the requested `SUVARNA_UPSTREAM_SETTLEMENT_ANSWER_20261003.md` ends at **Addendum 3**, not Addendum 8. The v1.7 sequencing document records later corrections, but I could not inspect addenda 4–8 in the named source. Restore those source records or correct the pointer before claiming that full upstream packet was reviewed.
- The numeric and malformed-tree re-pin counterexamples are exact-function probes, not observations of corruption in production.
- Working-tree status remained clean. No files, credentials, permissions, deployments or database state were changed.