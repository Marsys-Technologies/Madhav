---
artifact: ASTRA_REVIEW_A5_5_SPEC_AMENDMENTS
version: "1.8"
reviewer: "Codex gpt-6-astra"
date: "2026-10-02"
verdict: REJECT
reviewed_commit: "e75ac9127 (campaign/pravaha)"
reviewed_heads:
  campaign/pravaha: e75ac91278392ec914f5b329dbd130e63cd2a7bd
  origin/main: d35938a1854d5dc79cbb1c20cfa7262f59e236f0
  origin/pravaha/a53-am5-inventory: 4221f3bc54237f2591cd290250eb126441bc610b
  "PR #2919 — origin/pravaha/b6-am21-p1-anchor-1233": 728b91501ad5c3b653a6130c7cac792b381871da
  "PR #2920 — eval-window builder grants": 9e37be5dc70d885020b95f125fd4144efcccb5d5
  "PR #2922 — authority guard": 8a908f3729987c2edfb37efc... 
  "PR #2901 — vedha": ab1afc50ac8ce4fa55700558f81b774eff4fe9b3
  "PR #2914 — strict L1 wrappers": f5f921c03a1ba5202c7b48b5777e896732878477
  "PR #2923 — packet pin": e1f308aac5bd26968c11f8c5c38b2b5370f1c546
  "PR #2923 — local branch head": bbfa022af1eca60cd57db94ed5e84bd5564f37c8
authority: "Review only; authorizes nothing."
---

**Verdict: REJECT for the scoped milestone. Registry binding is unblocked at source level; the protected window and first internally consistent all-NULL candidate remain blocked. Measurement has separate blockers.**

The numerical deferrals are legitimate. I do **not** require the dynamic solver guarantee, qualified vedha integration, or qualified P1 scoring before this milestone.

The remaining defects concern what this milestone *does* promise: no numeric results, complete and consistent materialization, independent verification that remains valid until sealing, and usable restricted-role execution. The current code still produces numeric results and can miss omitted records, missing memberships and interior geometry gaps.

The #2923 local head is ahead of the packet pin. I inspected that delta; its additional ephemeris/read-back checks do not close the measurement findings below.

**R8 status**

“CLOSED” below means the source defect is repaired; it does not assert production application. “PARTLY / ACCEPT” identifies an explicitly accepted deferment.

| Item | Status | Scoped verdict | Reproduction and exact remaining change |
|---|---|---|---|
| **R8-1 — consumed-input identity** | **PARTLY** | **ACCEPT_WITH_AMENDMENTS** | The real 42-row exhibit now loads: all rows are `favourable`; selection uses `vedha_house IS NOT NULL`; the digest is `fc31379d48f3ac473ed44d0cd962c32e5471c9bb3fc80487ba31108cf2bce328`. `/2`, library identity and complete builder-side replay are substantive repairs. The independent verifier’s `not_derived` list is incomplete: it does not independently establish the opened-file census, backend/version/probe or scope/schema semantics. Derive those or disclose them accurately; see **R9-3**. |
| **R8-2 — per-class selection and supersession** | **CLOSED** | **ACCEPT** | The two-P3-version regression now includes at most one version. Supersession requires the approved successor to be selected **and included**; withheld, unknown-H and held-P5 cases are distinct. Independent planner/verifier tests pass. Actual-schema read-back and historical-selection tests exist; I could not rerun their PostgreSQL portions. Explicit binding/selection and its execution receipt remain work for step (b). |
| **R8-3 — P1 anchors and support** | **PARTLY** | **REJECT** | The anchor is now `(lord, level)`. My pure reproduction restricted the Sun’s Saturn reading to Saturn AD, and its Moon reading to Moon AD; Sun-in-Taurus retains the Moon-AD anchor. AM-20’s Lagna descriptor is consistent with the revised contract. However, an entirely omitted contact’s anchored records evade `verify_p1_anchors`, and PD remains minted despite the packet’s disabled-capability statement. Close **R9-2** and **R9-5**. |
| **R8-4 — comprehensive durable verification** | **PARTLY** | **REJECT** | The all-against P2 Saturn-house-8 builder and verifier now agree; the verifier returns `VERIFIED`. Changing its `evidence_for` to `123.0` is rejected. Durable 1240 rows improve enforcement, but their digest does not bind the complete record/membership dependency set. Whole omitted outputs also escape derivation. Close **R9-2**, **R9-3**, **R9-4** and the independent-job work in **R9-6**. |
| **R8-5 — scope versus completeness** | **PARTLY** | **ACCEPT_WITH_AMENDMENTS** | The manifest-only fake no longer produces completeness. The constructor derives coverage/inventory/verification state separately. Its positive result still inherits the verification holes identified here. Serving wiring remains unfinished, but §C2 correctly places that work at the **FLIP**, not steps (a)–(c). |
| **R8-6 — numerical correctness and disabled solver** | **PARTLY** | **REJECT** | The three-record P4 unknown now yields NULL; the boundary-less island is unqualified, not zero. The smooth day-5 maximum was approximately **5.4 ms early**, eliminating the former 27-second shoulder shift. The geometry-gap `[4,6)` reproduction still bridges the gap. Moreover, constant and empty-for-channel cases remain numeric with dynamic solving disabled. Close **R9-1/R9-3**. The global solver guarantee remains an accepted deferment. |
| **R8-7 — vedha integration** | **PARTLY** | **ACCEPT for the disabled milestone** | #2901 fixes duplicate keys across all 42 rows and adds the structured callback contract; its 30 pure tests passed. Those latest changes are not all present in writer head `4221f3bc5`. `VEDHA_SOURCE=None` makes integration a disclosed activation dependency, not a present candidate blocker. Merge and consume the contract before enabling qualified vedha. |
| **R8-8 — unknown competitors and freeze** | **PARTLY** | **REJECT for (d) only** | Original cases pass: `2/1/0/NULL/NULL` gives `[0,40]`; the matched-zero case gives `[60,80]`; the original tie bridge gives fractions `2/8`, `3/8`, `5/8`. New counterexamples disprove the general bounds claim, and an empty substantive Stage-1 freeze passes validation. Close **R9-7/R9-8**. |
| **R8-9 — strict L1 inputs/P1 scoring** | **PARTLY** | **ACCEPT for the disabled milestone** | Nine #2914 pure tests passed. The wrappers explicitly refuse missing/divergent inputs rather than defaulting them. Writer consumption, AM-19 decisions and numeric integration remain activation prerequisites. They do not block an actually all-NULL candidate. |
| **R8-10 — operational evidence** | **PARTLY** | **REJECT** | All ten recorded rehearsal migration hashes match the reviewed writer tree. The reported rehearsal is useful, but does not establish full restricted-builder execution or composed 1153/1206/1240 seal flows. Roles and the separate verifier runner remain unprovisioned/unbuilt in the packet. Close **R9-4/R9-6**. |

**Migrations**

| Migration | Verdict | Additivity, replay, privilege and route assessment |
|---|---|---|
| **1233** | **ACCEPT** | Adds the two anchor columns and CHECKs; no function, trigger or grant replacement. Refusal over existing P1 records prevents silent reinterpretation. Its protected-window placement is consistent with the chosen contract-change procedure. Raw SQL replay deliberately refuses; migration-ledger replay should skip it. |
| **1234** | **ACCEPT** | Routine grants-only migration. Window `SELECT/INSERT/DELETE`, membership `SELECT/INSERT`, and the existing helper grants fit the intended replacement flow; no unnecessary UPDATE or TRUNCATE. **Its grant closure becomes incomplete once 1240 adds another CHECK helper.** |
| **1236** | **ACCEPT** | Routine, validated CHECK using the governed-generation pattern. It blocks literal `5.0` and other governed labels through INSERT/UPDATE, including the five reviewed operator scripts. DELETE rollback cannot point authority at `5.0`. None of those scripts removes the constraint; `session_replication_role` does not bypass a CHECK. Owner DDL could remove it, but that is not a bypass in these scripts. Raw reapplication refuses; ledger replay skips it. |
| **1240** | **REJECT pending amendments** | Structurally additive: new verification storage/helpers, nullable provenance columns and one additional seal trigger. The builder receives no verification-table privilege. However, the new window CHECK helper lacks the builder EXECUTE grant (**R9-4**), and the freshness/expected-set checks omit material dependencies (**R9-2**). Full composed-role execution evidence is also missing (**R9-6**). |

The intended order is correct:

`routine prerequisites, including 1234 and 1236 → 1204 → 1206 → 1232 → 1233 → 1240`

The routine route must first satisfy **every** unselected predecessor below the protected-window ceiling, including 1230 where applicable. Reviewed Stream B wiring contains the ordered five-file sequence.

At source level, 1240’s `_zz_window_verified` trigger sorts after 1206’s `_z_search_complete` and 1153’s original guard. Its chart-exclusive-then-global-shared lock order agrees with those guards.

Its existing-seal branch also correctly distinguishes replay from first sealing: a generation sealed before 1240—including one sealed between 1206 and 1240—does not acquire a retroactive requirement for verification rows that never existed. That historical replay must **not** be represented as satisfying the new candidate verification gate. I found no source-level lock-order reversal, but composed execution remains unproved.

**New findings**

**R9-1 — Dynamic-disabled does not mean all-NULL. Blocks (c).**

At writer head, `window_sweep.py:808–903` disables qualified function-valued objectives. It still evaluates constant objectives and empty for-channel sums.

Executed reproductions using the actual registry rows produced:

| Case | Stored result |
|---|---|
| P2 Saturn, house 8, only against-channel member | `score=NULL`, `evidence_for=0.0`, `evidence_against=NULL`, `objective_value=0.0`, peak at window start |
| P3 residence, `1.1.0` | `score=1.0`, `evidence_for=1.0`, `evidence_against=0.0`, `objective_value=1.0` |
| P4 Jupiter/Saturn residences, `1.1.0` | `score=1.0`, `evidence_for=2.0`, `evidence_against=0.0`, `objective_value=1.0` |

The independent P2 verifier reproduces and accepts the first result. Thus builder/verifier agreement does not establish compliance with this milestone. Migration 1240’s conditional unqualified-result CHECK also permits it.

**Closing change:** bind an explicit all-NULL candidate policy across builder, independent verifier and candidate gate. Every numerical **result** field—including `objective_value`—must be NULL for every path and channel composition; peak must be absent and valence unqualified. Geometry, support intervals, identifiers and accounting counts remain populated. Add regressions for constant P3/P4 and all-against P2, not only dynamic cases.

**R9-2 — Verification does not prove the complete output set or remain current after all relevant changes. Blocks (a), (c).**

Three connected holes remain:

- `verify_window_semantics` reads **existing membership links** (`window_verifier.py:175–188`) yet reports `"membership"` among verified fields. It does not independently compare the full expected membership set.
- 1240’s content digest hashes window fields and existing member IDs (`1240…sql:212–238`). Its expected-set digest hashes only the union/intersection of admitted record supports (`:254–278`). It does not bind all relevant record contents or detect every newly omitted membership.
- `verify_p1_anchors` starts from **relationship records**, not the complete expected contact set (`record_verifier.py:133–176`). With no such records, my fake read returned `{"contacts": 0}` successfully. Omitting every anchored record for a contact evades the per-contact anchor comparison.

A concrete **source-level** stale-verification counterexample is:

1. Verify a window legitimately.
2. Before sealing, insert another valid admitted scored record whose support lies wholly inside that window.
3. Omit its membership link.
4. Window content and existing member IDs are unchanged; the expected interval union is unchanged.
5. The examined 1240 checks do not invalidate the old verification. The older membership guard checks existing links, not absent ones.

The builder-side `WindowStore.verify_grain` check is useful but does not replace an independently enforced, current seal-time invariant.

**Closing change:** independently derive and compare complete contact, anchored-record and membership sets, including zero-output cases. At the gate, compare expected versus stored memberships in both directions and bind verification to all derivation-relevant records, contacts, prerequisites and input revisions. Relevant changes must invalidate verification.

The anchor-free XX.38 obligation is a **sound search grain**: concrete Sun/Jupiter sign searches can cover the whole horizon, with AD anchoring applied to records afterward. No anchor column is required in the obligation grammar merely for that decomposition. But the claimed boundary is not yet enforced: inventory certification of a search and verification of only surviving records leave wholly omitted output undetected.

On the explicit trust question: the builder cannot directly INSERT a 1240 verification row under the intended grants. A verifier principal **can** construct a `VERIFIED` row using SQL-derived digests and asserted report fields without running the independent Python derivation. Database grants identify the trusted principal; they cannot prove that its computation occurred. Option A therefore needs a pinned, independently executed verifier job, and must not describe table access alone as computational independence.

**R9-3 — Endpoint geometry probes miss interior gaps; independent identity coverage is overstated. Blocks (c).**

I supplied a residence support `[0,10)` with longitude inside the target sign except during `[4,6)`.

- The `1.1.0` builder returned one `[0,10)` window.
- `_probe_contact`, with valid entry/exit behavior and the interior gap, returned **no problems**.

`window_verifier.py:469–529` checks just inside and outside the endpoints. Those probes do not establish that the entire interval is a contact. The separate aspect-to-span check does not establish complete residence/point-contact output for every admitted obligation. NULL numerical results would not repair a falsely continuous support.

The independent input verifier also hashes the **file names supplied in the stored vector**; it does not independently establish the opened-file census. Its `not_derived` list contains only `orb_policy` and `rulings_digest`, while backend, version/probe and scope/schema semantics are not independently reproduced there.

**Closing change:** independently reconstruct or certify complete contact geometry over the bound horizon, including interior exits/reentries and omitted contacts. Incomplete boundary evidence must prevent a complete-search claim. Independently establish the consumed ephemeris identity needed by that derivation; accurately enumerate everything else that remains bound but not independently derived.

This requires a contact-completeness guarantee. It does **not** require activation of the deferred objective maximizer.

**R9-4 — 1240 removes effective window-insert capability from the restricted builder. Blocks (a), (c).**

1240 creates:

`ka_gochara_window_qualification_ok(jsonb)`

and invokes it from the new window CHECK (`1240…sql:100–124`). Production-shaped default privileges revoke PUBLIC EXECUTE. Neither 1234 nor 1240 grants this new helper to `data_plane_builder`.

A table INSERT grant does not supply the missing function permission. The restricted builder therefore lacks the complete privilege set for post-1240 window inserts.

The current role suite misses this: `test_a53_window_verification_roles.py:89–91` constructs the build as superuser. The rehearsal checks that the builder retains the table INSERT privilege, not that its real INSERT succeeds.

**Closing change:** grant only EXECUTE on this CHECK helper to the builder, retaining zero verification-table privileges. Run the complete builder write flow after the whole stack with PUBLIC EXECUTE revoked, and prove that removing this helper grant makes the flow fail.

**R9-5 — PD is disclosed as disabled but remains a scored-path reading. Blocks (c).**

The request packet §C lists **P1 PD level** among disabled capabilities. The writer enumerates it, and `record_verifier.py:142–156` requires it. The Sun-in-Libra test explicitly expects Sun MD, AD **and PD** plus Saturn AD.

Calling PD a “flagged extension” does not implement the packet’s disabled switch.

**Closing change:** make the scoped PD policy executable and consistent across enumeration, inventory, records and verification: exclude PD from scored eligibility under a named limitation, or represent it as explicitly authorized testimony. Update the packet’s stale statements about anchored records not being minted. Keep the deferred inimical-sign/retrograde admission limits explicit; do not describe the implemented subset as exhaustive classical coverage.

**R9-6 — Option A is sound architecture, but its runner, grant order and composition proof are unfinished. Blocks (c); rehearsal portion blocks (a).**

The packet correctly proposes:

- a separate verifier job, service account, secret and login;
- no builder role switching or extra verifier credential in the writer;
- an approval-gated sealer;
- a closed candidate gate while verification is absent.

That respects the frozen one-builder-connection writer contract. The packet does **not** establish that these capabilities exist. Its proposed “built / not verified” distinction is appropriate.

Required corrections:

1. Move inventory-verification persistence out of the builder. The writer still calls `write_verification` using its builder connection.
2. Remove the builder’s 1206 verification-write privilege.
3. Replace the packet’s closing instruction that the “writer must connect as the verifier” with the separate-runner contract.
4. Give any grants migration that references 1240’s new table an executable order. The example number **1235** cannot simply be applied after the window: it lies below 1240 and becomes an unapplied routine predecessor. Use an appropriate later migration or another explicitly valid staged sequence.
5. Rehearse real builder → verifier → sealer flows with **all** guards enabled.

For **PC-4**, editing 1206 before its first application is the cleaner solution, provided its unapplied status is confirmed. An additive revoke is also sound after application, but only with an enforced closed execution interval until revocation. “Immediately afterward” alone does not eliminate the privilege gap. Do not rewrite an already applied migration.

The reported 39-assert rehearsal checks order, recovery, object presence and privileges. The dedicated 1240 suite explicitly disables 1206’s seal trigger. Neither is evidence for the required composed seal/replay behavior. Add first sealing, pre-1240 replay, sealing between 1206 and 1240, and restricted-role contention cases to the integrated rehearsal.

**R9-7 — Unknown-competitor enumeration is not a sufficient set of assignments. Blocks (d) only.**

The fixed `0.75 × tolerance` placement grid still misses valid unknown–unknown bridges.

Executed counterexample:

```text
known:   [0, 2.9e-9, 1, 2, 3, 4]
unknown: 2

reported attainable largest-tie fractions:
[0.125, 0.25, 0.375]

valid assignment:
[2.9e-9 / 3, 2 × 2.9e-9 / 3]

actual largest-tie fraction:
0.5
```

Every adjacent gap in the four-value chain is below `1e-9`. The implementation can therefore report invariant “diverse” when a plateau/void assignment exists.

A second counterexample disproves the fixed `BIG=1000` sentinel:

```text
known: [1e10, 0], matched index 0, one unknown
reported percentile range: [0, 16.666666667]
unknown = 1e10 + 1 gives percentile: 33.3333333333
```

Both assignments satisfy the module’s declared finite, nonnegative domain.

**Closing change:** replace the unproved placement grid with a proven enumeration of attainable ordering/tie partitions, or conservative bounds that cannot omit valid assignments. Preserve unqualified results whenever verdict invariance cannot be established. Update both production code and the reference model, with these regressions. Budget fallback does not fix a mathematically incomplete enumeration below the budget.

**R9-8 — Freeze validation accepts missing substantive inputs and does not bind actual execution adequately. Blocks (d) only.**

Against `bbfa022af`, I constructed an in-memory Stage-1 document with:

- every required key present;
- `status="FROZEN"`;
- correct running-code file hashes and a self-consistent canonical command;
- `inputs={}`;
- substantive fields left null;
- `ephemeris_requirement=None`.

`stage1_problems(...)` returned **`[]`**.

Replacing the ephemeris field with only:

```json
{"manifest_readback": {"ephemeris_problems": []}}
```

also passed.

Additionally:

- `candidate_score.py` reads CLI-selected registry/controls without binding those actual inputs to the frozen entries.
- It labels the result with Stage-1’s generation without establishing the extract’s matching generation.
- `dump_extract.py` validates the declared command but does not compare the actual invocation against its frozen arguments.
- Checking a supplied empty `ephemeris_problems` list is not verification of an ephemeris identity.

**Closing change:** validate a substantive typed freeze schema with mandatory input identities; bind actual registry, controls, generation, command arguments and measurement options to it; validate and reconcile real manifest ephemeris components. Then complete Stage 1 before extraction and Stage 2 before inspection/scoring, with the required commit/hash receipts.

The following measurement decisions are acceptable:

- **`4.1` uses `si := raw_intensity`**, preregistered before candidate inspection, with the stated sign reconciliation.
- **T-honesty is UNVERIFIABLE for `4.1`**; a body/target representation must not be invented into class/year testimony.
- Consequently **`4.1` is diagnostic and not flip-eligible**.
- The `4.1` ephemeris identity must cover the actual consumed bodies, files and runtime, including the Moon where the windows projection consumes it. A `3.0` identity or missing component is not a substitute.

The draft honestly states that no completed freeze or candidate extract exists. Those remain required execution artifacts, not completed measurements.

**Ranked amendments**

| Priority | Item | Exact closure | Blocks |
|---|---|---|---|
| 1 | **R9-2** | Complete expected output/membership derivation; bind verification to all relevant dependencies; reject stale attestations at sealing. | **(a), (c)** |
| 2 | **R9-4** | Add the narrow builder CHECK-helper EXECUTE grant; prove the complete restricted write flow. | **(a), (c)** |
| 3 | **R9-1** | Implement one bound all-NULL policy across builder, verifier and gate, including constant and all-against cases. | **(c)** |
| 4 | **R9-3** | Certify complete contact geometry and consumed ephemeris identity; refuse incomplete support/completeness claims. | **(c)** |
| 5 | **R9-6** | Resolve PC-4, provision the independent jobs/grants in executable order, and supply composed-role rehearsal evidence. | **(a): rehearsal; (c): operational capability** |
| 6 | **R9-5** | Enforce the disclosed PD policy consistently and reconcile packet statements with the implemented search scope. | **(c)** |
| 7 | **R9-7** | Replace unsound unknown-assignment bounds with proven or conservative bounds. | **(d) only** |
| 8 | **R9-8** | Enforce substantive freeze/input/runtime identity, then complete the two-stage process. | **(d) only** |

**Step lines**

- **(a) Protected migration window: BLOCKED BY R9-2, R9-4 and R9-6’s integrated rehearsal requirement.**
- **(b) Binding 1.1.0 registry versions: UNBLOCKED at source level.** Perform explicit composite-version binding/selection and retain SQL read-back and historical-version receipts. Current configured defaults remain `1.0.0`; this is not a claim that binding has occurred.
- **(c) First internally consistent, all-NULL `5.0` candidate: BLOCKED BY R9-1 through R9-6.**
- **(d) Measurement: BLOCKED BY R9-7, R9-8, the required candidate ephemeris identity, and completed Stage-1/Stage-2 receipts.** `4.1` remains diagnostic even after those requirements are met.

The absent global objective solver, qualified vedha, qualified P1 scoring, unresolved numerical rulings and unbuilt serving reader are **named limits**, not additional blockers to the correctly implemented all-NULL milestone. Serving completeness and consumer routing remain explicit FLIP prerequisites.

**What I could not verify**

- No PostgreSQL migration, restricted-role flow, seal/replay or concurrency test was executed in this review. SQL conclusions and the omitted-membership attack are source-level findings.
- I did not connect to production or independently refresh the packet’s role, privilege, ledger, volume or deployment observations.
- I did not run a `4.1`/`5.0` build, generate/read a candidate extract, execute candidate measurement, or verify remote CI/PR state.
- Read-only execution did pass **121 writer/input-vector regressions**, **30 vedha tests**, **9 strict-input tests** and **39 measurement tests**. Database/file-writing cases were excluded; two writer-suite cases skipped. The adversarial reproductions above are additional to those suite results.
- I checked the reviewed migration bytes against all ten rehearsal hashes. The checkout remained clean. No file was written and no git write command was run.

