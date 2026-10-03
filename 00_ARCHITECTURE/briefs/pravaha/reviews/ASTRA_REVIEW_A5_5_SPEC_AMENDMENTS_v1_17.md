---
artifact: ASTRA_REVIEW_A5_5_SPEC_AMENDMENTS
version: "1.17"
reviewer: "Codex gpt-6-astra"
date: "2026-10-03"
verdict: REJECT
reviewed_commit: "c3b7aeec5 (campaign/pravaha)"
reviewed_heads:
  campaign/pravaha_requested: "c3b7aeec5accb3a99f44c8c8413e787b402c98bb"
  campaign/pravaha_supplementary_scheduling_documents: "ad626bd7af1b110d219c42371391a7a250e8e45d"
  origin/pravaha/a53-am5-inventory: "7678f77228b77e77cc0dd2fb04ddf36c01086ee5"
  "PR #2903 — origin/pravaha/b6-am10-repin-tool": "e8f417298f8fbe678b3986a0fd34909d1a941952"
  origin/pravaha/b6-composed-rehearsal-integration: "074923179a5ec685fed5cf72a0e905ba2d861fd8"
  "PR #2961": "2ffb954afe11cf0bad02df71b548e35cf2da1863"
  "PR #2975": "bd05b59989f76a3f5f003da65387420996bac595"
  "PR #2976": "ef31ffe0f807b30cfa85c72418ab72f1c658e575"
  "PR #2949": "c26743b5db35ce63c55bd83975ecaf3970023b6a"
  "PR #2952 — tree comparison only": "84b463b81765e220ad6efef21791a66a6bedc4a7"
comparison_refs:
  round_17_campaign: "29104c4226b104744bbc71617cfa3301997c39dd"
  round_17_writer: "699638fbe8538160470dac4c52d5b0d0adce5e96"
  round_17_integration: "6dcbc450111ce1a94ac0967c9180986f303f9166"
authority: "Review only; authorizes nothing."
---

**Verdict: REJECT the complete executable set.**

The specific R17-1…R17-7 defects are corrected. The §5.5 field mapping, R17-H1 and F-R17-3 are also closed.

**Step (a)’s acceptance stands.** Its accepted migration bytes and expected trigger manifest are unchanged. I did not re-review accepted SQL semantics.

**Step (c) is still not waiting only on settlement, the reviewed re-pin, capacity and operational receipts.** Two capture defects remain: a self-inconsistent capture can receive `CLEAN`, and capture can report success for a malformed tree that its own later loader rejects. The checklist and F-R17-4 documentation also need bounded corrections.

No file was written, and no database connection was made.

**Item status table**

“CLOSED” means closure in the inspected source or procedure, not completion of production operations.

| Item | Status | Verdict | Remaining change or qualification |
|---|---|---|---|
| R17-1 — driver interface and capture arguments | CLOSED | ACCEPT | Psycopg3, named reader refusals, and capture without a replacement build are implemented. |
| R17-2 — both governed pins | CLOSED | ACCEPT | Actual application updates both pins. Regenerate the lock and affected goldens in the eventual re-pin PR. |
| R17-3 — precision and non-finite notice values | CLOSED | ACCEPT | Measurements retain microseconds; expectations and tolerance must be finite; tolerance must be ≥1 s. |
| R17-4 — unreachable rows and count checks | CLOSED | ACCEPT | Comparison rejects malformed trees on either side, differing level totals and differing child sequences. Acquisition-time validation remains R18-2 below. |
| R17-5 — settlement notice build identity | CLOSED | ACCEPT | Explicit notice UUID must agree with CLI and database readback. The separate **old-capture** identity defect is R18-1. |
| R17-6 — application gate cycle | CLOSED | ACCEPT | Local preparation needs settlement receipt; production remains held pending reviewed merge and steward release. |
| R17-7 — dry-run writes | CLOSED | ACCEPT | Mode validation precedes connection and dispatch; tested dry-run paths make no writes. |
| §5.5 / R16-3 residue | CLOSED | ACCEPT | Persisted `produced_by` is checked against `gochara_verifier`; approval identity and shared identifiers have their actual counterparts. |
| R17-H1 — absolute-probe NaN | CLOSED | ACCEPT | Non-finite and nonnumeric results receive the named mismatch. |
| F-R17-1 — real-reader plumbing | CLOSED | ACCEPT | Real reader exercised through a psycopg3-shaped connection; psycopg2 shape refuses explicitly. |
| F-R17-2 — verifier pin and lock instructions | CLOSED | ACCEPT | Both declarations are rewritten and checked; lock regeneration is explicitly required. |
| F-R17-3 — refusal classification | CLOSED | ACCEPT | Mixed and wrong builds reach `REFUSED / stale_inputs`, exit 2, through the job entry point. |
| F-R17-4 — stale descriptions/version | PARTLY | ACCEPT_WITH_AMENDMENTS | Corrective text and version bump exist, but contradictory operative descriptions remain. See R18-4. |
| F-R17-5 — optional hardening | CLOSED | ACCEPT | Minimum tolerance, existing/nonempty forensic report and named `DashaReadConflict` handling are present. Report contents remain owner evidence. |
| F-R17-6 — R0 catalog-type confirmation | CLOSED procedurally | ACCEPT | Four-column catalog check is specified. Its production result was not independently verified. |
| Capture identity/qualification | PARTLY | REJECT | R18-1 and R18-2 must close before relying on the official capture. |
| Sitting checklist | PARTLY | ACCEPT_WITH_AMENDMENTS | Nine-step sequence preserved; explicit check placement and scheduling wording need correction. |
| Capacity | NOT CLOSED | REJECT for first approval/seal | Actual candidate and complete clone-seal measurements remain absent. |
| Protected-window SQL and 1241 v7 | CLOSED / unchanged | ACCEPT | No SQL amendment requested. |

**Probes**

I executed the **79 non-database re-pin test cases: 79 passed, 0 failed**, using an in-memory harness. Filesystem operations were intercepted into RAM; database tests were excluded. This is not a claim to have reproduced the authors’ 81-test PostgreSQL run or 1,080-test composed run.

Additional probes used the frozen tool, the composed reader, real governed reference rows and controlled connection responses.

| Probe | Result |
|---|---|
| Psycopg2-shaped connection | Named STOP, exit 3; no misleading “no rows” result. |
| Capture without `--new-build-id` | Accepted through the real reader; captures daśā and natal data. |
| 6,995.9 s against 6,993 ±2 s | STOP, exit 3; measured value remains **6,995.900 s**. |
| NaN, +∞, −∞ expectations or tolerance | Refused. |
| Non-finite measured shift | Refused. |
| Notice without build ID | STOP, exit 3. |
| Notice build disagrees with CLI/database | STOP, exit 3. |
| Self-parented new row | STOP naming self-parenting/cycle. |
| Unreachable old row; changed lord on unreachable new row | Old capture rejected as malformed; no successful comparison. |
| Every new row ID differs | All ten reference rows pair structurally; clean comparison succeeds. |
| One parent loses a level-3 child | STOP naming the refused subtree and unequal level-3 totals. |
| Level-3 lord sequence reordered, counts unchanged | STOP naming the refused subtree. |
| Correctly labelled capture from another build | Refused. |
| Capture header claims old pin, but every row carries another build | **Incorrectly accepted: `CLEAN`, exit 0.** |
| Dry-run/capture/application mode matrix | Invalid combinations refuse before connection; tested dry-run paths write nothing. |
| Application without settlement receipt | Refused. |
| Application after receipt, before re-pin merge | Succeeds in RAM and explicitly retains the production hold. |
| Writer-only re-pin control | Writer accepts new build; independent verifier refuses it. |
| Actual tool application | Both pins change; both readers accept new build and reject old build. |
| Missing, duplicated or mismatched verifier declaration | Application refuses before source writes. |
| Capture snapshot changes / wrong isolation / missing natal row | Refused; owned connection rolled back and closed. |
| Capture contains a self-parented row | **Capture returns 0 and saves it; later loading refuses it.** |
| Absolute probe: finite reference / NaN / ±∞ / None / boolean / string | Reference accepted; all invalid values refused by name. |
| Mixed/wrong build through verification CLI | Exit **2**, `status: REFUSED`, `code: stale_inputs`; connection closed. External identity/ephemeris checks were stubbed for these classification probes. |

The pin-composition probe produced:

```text
Before application:
  old build: writer ACCEPT / verifier ACCEPT
  new build: writer REFUSE / verifier REFUSE

After permission-only change:
  new build: writer ACCEPT / verifier REFUSE

After actual apply_repin:
  new build: writer ACCEPT / verifier ACCEPT
  old build: writer REFUSE / verifier REFUSE
```

I independently verified:

- All **ten** migration hashes match the round-17 writer, current writer, round-17 integration and current integration.
- `EXPECTED_WINDOW_SHA256.txt`, `EXPECTED_WINDOW_TRIGGER_MANIFEST.tsv` and `window_trigger_manifest.sql` are unchanged from the round-17 campaign.
- 1240 remains `05a8f897a0b8ae6b955915eced717ad30c98af485d490185333a88355707bc6b`.
- 1241 v7 remains `a3480710c7498065892965f23d9bee43dc700d4d8f16eb46ac8fb0ee601efefa`.
- The current integration and #2952 have identical Git trees.
- The writer’s kernel, rules and orchestrator trees match the integration.
- Recomputing all **60 implementation-module** source hashes reproduces all stage digests and the lock:

```text
893c475a68e0703be4331a59ede8b020564f7c45a0b9aa863271ea6b3ed04daa
```

The integration delta contains no changes to the accepted deployment/sealing controls or migrations.

**New findings**

**R18-1 — P2: old-capture identity is checked only in the envelope, allowing a false `CLEAN`.**

`load_capture_full()` checks the top-level chart/build, data checksum and tree. It never requires each captured daśā row’s `build_id` to equal the expected old pin. Moreover, the embedded checksum excludes the envelope’s chart/build identity. [Capture digest and loading](https://github.com/Marsys-Technologies/Madhav/blob/e8f417298f8fbe678b3986a0fd34909d1a941952/platform/python-sidecar/scripts/gochara/repin_dasha_contract.py#L296-L323)

Reproduction:

1. Retain structurally valid old reference rows, but give every row build `22222222-2222-4222-8222-222222222222`.
2. Supply the expected old build in the capture envelope.
3. Supply a valid new population, matching settlement notice and successful preflight responses.
4. The real comparison reports **`CLEAN`, exit 0**.

Changing only an honestly foreign capture’s envelope to the expected pin also preserves its embedded checksum.

This is a malformed-evidence acceptance defect, not evidence that the normal SQL capture selects the wrong build. Checking an independently retained **whole-file** checksum would detect subsequent header alteration, but the tool does not perform that check.

**Close:** validate every captured daśā row against the old build and read contract; reject foreign/mixed builds, wrong systems and wrong tiers. Bind chart/build/selection identity into the canonical capture checksum. Add the self-inconsistent-envelope case as an exit-3, no-application test.

**R18-2 — P2: capture can declare success for evidence that cannot later be used.**

`_capture_old()` reads rows and natal facts, checks transaction properties, closes the connection and writes the capture. It does not run `tree_problems()` before reporting success. [Capture path](https://github.com/Marsys-Technologies/Madhav/blob/e8f417298f8fbe678b3986a0fd34909d1a941952/platform/python-sidecar/scripts/gochara/repin_dasha_contract.py#L701-L738)

With a self-parented PD row, the actual capture path returned **0**, retained the capture and correctly closed its transaction. Its own subsequent `load_capture()` rejected that capture.

The later refusal is safe for the re-pin, but discovering an unusable baseline **after S-L1 has replaced the old rows** is too late.

**Close:** validate the captured tree and capture contract before writing or announcing successful capture. Reuse the loader’s validation at acquisition, return a named STOP with no successful artifact, and preserve rollback/close on failure. Test this through the normal capture dispatch.

**Capture assessment — ACCEPT_WITH_AMENDMENTS.**

The **transaction design is sound** for a coherent pre-rebuild record: psycopg3 sets REPEATABLE READ and READ ONLY before the first query; both populations are read on that connection; no intermediate commit occurs; the transaction is rolled back and closed before file output. PostgreSQL’s repeatable-read snapshot supplies the cross-query consistency guarantee. [PostgreSQL transaction isolation](https://www.postgresql.org/docs/current/transaction-iso.html#XACT-REPEATABLE-READ)

Snapshot equality is a useful check, but **does not alone prove one transaction**—separate transactions can observe identical snapshots. The inspected lifecycle supplies that evidence. Nor does a consistent snapshot prove that an upstream batch has completed; the capture must still occur before the announced S-L1 window.

The captured full-precision boundaries, parent links, lords, row/build identities and ten natal values/tier/build/fact IDs contain the substantive data needed for the re-pin and later natal-cell comparison. That cell comparison remains a separate operation.

Alongside the mandatory fixes above, retain:

- Capture tool commit, explicit selection contract, per-level counts and independently recorded whole-file checksum.
- Separate daśā and natal build identities; these are different assets and need not share a build ID.
- Capture timing and upstream-window reference; preferably the relevant asset-state/build census from the same snapshot.
- Suvarṇa’s separately owned old-ID→natural-key map for the later resonance comparison. This ten-row natal capture does not replace that map.

Do not add level-4 or Kālacakra equality gates. Addendum 7 expressly permits those changes. The notice must supply the actual **Lahiri L1–3** shifts, rather than treating the across-ayanāṃśa range as one measurement.

**R18-3 — P3: the checklist preserves the sequence but is not yet an unambiguous executable page.**

All nine accepted steps are represented, in order, with the correct owner-only dispatch and principal stop conditions. Three corrections remain:

1. **Move W4 to row 5**, after role creation, with its explicit CONNECT readback and STOP condition. Row 3 currently says to perform it “after the roles exist” without assigning its later execution.
2. **Add the post-window W2 recheck to row 9.** The governing runbook requires it again after the window. Also make the W5 expected-minus-production and production-minus-expected outputs explicit, alongside both W6 directions.
3. **Resolve the scheduling contradiction.** The supplementary text permits setup rows 1–6 “any time,” while the preamble/no-overlap paragraph forbids opening the sitting during S-L1 and excludes S-L1 while rows 4–9 run. Separate setup from the protected train and state one controlling schedule. Preserve the agreed requirement that rows 7–9 finish before W1 or start after SETTLED-1, and that **1241 waits for SETTLED-1**.

These are checklist corrections. The previously accepted master procedure remains available; they do not reopen protected-window SQL. [Checklist](https://github.com/Marsys-Technologies/Madhav/blob/ad626bd7af1b110d219c42371391a7a250e8e45d/00_ARCHITECTURE/briefs/pravaha/runbooks/PROTECTED_WINDOW_SITTING_CHECKLIST_v1_0.md)

**R18-4 — P3: F-R17-4 is only partly closed; Addendum 9’s source is missing.**

The runbook now has `version: "1.16"` and corrective text, but:

- Its `status` still begins **“v1.14 — Codex round 15.”**
- §5.4 still contains the old explanation that coexistence would silently read the pinned old build, beside the correction saying the writer and verifier refuse mixed builds.
- The tool’s introductory G6 description still calls the writer refusal a separate future change. [Tool description](https://github.com/Marsys-Technologies/Madhav/blob/e8f417298f8fbe678b3986a0fd34909d1a941952/platform/python-sidecar/scripts/gochara/repin_dasha_contract.py#L37-L39)

Replace those operative statements rather than appending further corrections.

Also, the named `SUVARNA_UPSTREAM_SETTLEMENT_ANSWER_20261003.md` ends at **Addendum 8 at both `c3b7aeec5` and `ad626bd7a`**. The latter commit records Addendum-9 scheduling terms in the checklist, runbook and sequencing document, but does not append the source addendum. Restore that source record or correct its attribution. I assessed the scheduling terms supplied in this request and those supplementary documents; I cannot claim to have read Addendum 9 in the named source.

**Ranked amendments**

| Rank | Exact closing action | Gate affected |
|---|---|---|
| 1 | **R18-1:** validate captured-row build/read-contract identity and bind envelope identity into its checksum; add false-`CLEAN` regression test. | Trustworthy re-pin; (c) |
| 2 | **R18-2:** validate the baseline before capture success; malformed capture must STOP without a successful artifact. | Official pre-S-L1 capture |
| 3 | **Capacity:** record actual counts, widths, bytes, runtime, memory and lock duration; measure a complete seal on a disposable clone of the actual candidate. | First approval/seal |
| 4 | **R18-3:** place W4 and post-window W2 explicitly; enumerate comparisons; reconcile setup/train scheduling. | Checklist acceptance |
| 5 | **R18-4:** remove stale G6/version descriptions and repair the Addendum-9 source pointer. | F-R17-4/document consistency |

Refresh the composed evidence after the tool fixes. The existing 1,080-pass report cannot qualify amended bytes.

**Step lines**

**(a) Protected window — ACCEPT; source AND master procedure remain unblocked.**

The accepted bytes are unchanged. Execute the nine governed steps with their operational readbacks, using the corrected checklist or the full accepted runbook. The protected train must finish before Suvarṇa’s W1 merge or run after SETTLED-1. **1241 is excluded from that train and waits for SETTLED-1.**

**(b) Registry binding — ACCEPT; prior acceptance stands.**

No closure regression was found. Actual binding/readback and retention of the selected identities remain operational.

**(c) First all-NULL candidate and seal — REJECT; a bounded source correction still remains.**

**No: what remains is not yet only SETTLED-1 and operational work.** Close R18-1/R18-2 first, plus the document corrections above. Thereafter:

1. **Before S-L1:** take and validate the official one-transaction capture, retain both checksums and provenance, and close the connection before the window starts.
2. Receive actual SETTLED-1 evidence. Check the whole-chart single daśā build, **45+1 partitions**, both assets `lit`, notice/build agreement, forensic evidence and old/new natal-cell comparison.
3. Run the corrected comparison and local application. Review and merge one re-pin containing **both pins**, reference-row changes, required literal rulings, regenerated implementation lock and affected goldens. Obtain the steward’s production-hold release.
4. Complete protected-window qualification if outstanding; apply **1241 after SETTLED-1** and verify exact ACL/read-access closure. Complete act 2b, final-commit/image deployment, bootstrap and actual API/log/permission proofs.
5. Build a fresh all-NULL candidate and independently verify every required grain **after the last build**. Discard pre-settlement candidate evidence. Begin the prescribed input/registry/corpus/image freeze.
6. Capture **R0 before the brief**. Obtain real verification/brief measurements and complete disposable-clone seal measurements; pass the capacity checkpoint before approval.
7. At **R1**, enforce the freeze and corrected §5.5 comparisons; approve the exact digest/run/attempt/brief identity.
8. Seal, perform **R2**, reconcile publication/seal/receipt state and verify cleanup.

SETTLED-2 is not added as a gate for this candidate. The G3 decision remains a numerical-activation gate.

**(d) Measurement — prior scope acceptance stands; execution remains BLOCKED.**

Carry forward **S1-REQ-EPHEMERIS**, settlement/re-pin and hold release, Stage-1/Stage-2 freezes/readbacks, and actual measurement evidence. This review does not reopen #2923 or treat the `5.0` absolute probe as closure of the governed `4.1` prerequisite.

**What I could not verify**

- The authors’ **1,080-pass composed**, **81-pass database**, or prior window suites. The read-only sandbox prevented a disposable PostgreSQL environment; no instance was started.
- Real PostgreSQL transaction enforcement, SQL execution, IAM, Cloud Run, GitHub approvals, logging shapes, production catalogs, ACLs or migration receipts.
- The reported production trial capture, Suvarṇa’s measured rebuild results, the actual SETTLED-1 notice, seven-anchor evidence or natal-cell comparison.
- Actual-volume capacity or a complete clone-seal cost.
- Addendum 9 in its named source file.

The counterexamples are controlled source-level probes, not observations of corrupt production data. The working tree remained clean.