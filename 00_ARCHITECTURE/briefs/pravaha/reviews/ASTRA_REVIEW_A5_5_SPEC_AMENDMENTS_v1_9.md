---
artifact: ASTRA_REVIEW_A5_5_SPEC_AMENDMENTS
version: "1.9"
reviewer: "Codex gpt-6-astra"
date: "2026-10-02"
verdict: REJECT
reviewed_commit: "c884eacfc (campaign/pravaha)"
reviewed_commit_full: "c884eacfce680b97187c2c5e2e8c718eafe164d3"
reviewed_heads:
  "origin/pravaha/a53-am5-inventory": "dc63af1129c63b4d6bfafbf59fbe9f1c9c3730b6"
  "PR #2867 / origin/pravaha/b6-am5-inventory-migration": "e4d31c9ef82aa2e3874cd2095d295622f6756bf6"
  "origin/pravaha/b6-pc4-1206-builder-verification-grant": "e4d31c9ef82aa2e3874cd2095d295622f6756bf6"
  "PR #2919 / origin/pravaha/b6-am21-p1-anchor-1233": "728b91501ad5c3b653a6130c7cac792b381871da"
  "PR #2920 / origin/pravaha/b6-1234-eval-window-builder-grants": "9e37be5dc70d885020b95f125fd4144efcccb5d5"
  "PR #2922 / origin/pravaha/b6-1236-authority-governed-guard": "8a908f372d665fd6518265729987c2edfb37ef59"
  "PR #2940 / origin/pravaha/b6-1242-builder-record-replace-grants": "e55deef5c9735b148b8e8d7a7da253d7bbc446a5"
  "PR #2949 / origin/pravaha/b6-1241-verifier-sealer-grants": "50b5ab94b8ad46d8c9ef7aa887de1cbceeeb52b4"
  "PR #2952 / origin/pravaha/b6-composed-rehearsal": "09a306e0d84d80276292e387107883fae2de444b"
  "origin/pravaha/b6-composed-rehearsal-integration": "0e88df1a3ba764e57266d6b82bdf53e20a1d03cb"
  "PR #2923 / origin/pravaha/b6-stage1-candidate-measurement": "2e1e5fdd39578009b7972e90ed8338e07c9fdd3b"
comparison_commits:
  initial_origin_main_diff_base: "f8df71b537cf59ee9c81537d9ebc92ebb0afffd3"
  round_9_writer: "4221f3bc54237f2591cd290250eb126441bc610b"
  pc4_predecessor: "fc10a91fe722c316c0d7d0d88b4693a4563a8d7d"
ref_observations:
  origin_main_at_close: "7b7144fc7a7d6c65244776ccc1a53616ba077a37"
  origin_main_at_close_scope: "Ref identity only; not a replacement for the reviewed diff base."
authority: "Review only; authorizes nothing."
---

**Verdict**

**REJECT the complete A5.5 gate. Step (b) remains UNBLOCKED.**

The original numeric **window** leaks are fixed. PC-4 is correctly folded into unapplied 1206, the builder’s verification step is report-only, and a separate verification job now exists.

However, the candidate is **not yet independently verifiable end to end**:

- Expected records can be omitted without the job detecting their absence.
- Relationship-record result fields escape the all-NULL verification and freshness boundary.
- Verification reads occur before protective locks; persistence can attest to newer data than the job checked.
- Input-identity verification is optional, and the actual verification runner’s code identity is not recorded as AM-24 requires.
- The identity check and deployment grant closure remain incomplete.

These are defects in the adopted AM-24 invariant for the current all-NULL milestone. They do not require activating any deferred numerical capability.

The packet correctly discloses that the nine owner acts are unperformed and that production has neither principal. That disclosure is honest. Its blanket source-level “DONE” treatment of several R9 findings is not supported.

**Item status table**

| Item | Closure | Verdict | Finding and exact remaining change |
|---|---|---|---|
| **R9-1 — all-NULL policy** | **PARTLY** | **REJECT** | Constant P3/P4 and all-against P2 windows now obey the manifest policy, including `objective_value`, absent peak and unqualified valence. Extend enforcement to relationship-record evidence, severity and valence, and bind these fields into verification freshness: **R10-2**. |
| **R9-2 — completeness, membership and freshness** | **PARTLY** | **REJECT** | The particular omitted-membership attack is addressed. Complete expected record derivation, dependency coverage, verification-time consistency and runner identity are not: **R10-1–R10-4**. |
| **R9-3 — geometry and independent input identity** | **PARTLY** | **REJECT** | Interior-gap detection, independent reconstruction and opened-file census are substantial repairs. The bounded geometry claim is acceptable with its disclosed limits. Require the job to execute input-identity verification before persisting: **R10-4**. |
| **R9-4 — restricted builder CHECK helper** | **CLOSED** | **ACCEPT** | 1240 grants the builder the required helper `EXECUTE`. The composed exhibit exercises the restricted build and removal of this grant. |
| **R9-5 — PD testimony** | **CLOSED** | **ACCEPT** | Sun-in-Libra PD is explicit testimony under `ST-P1-PD-TESTIMONY-20261002`, excluded from scored membership. The implementation now matches the ruling. |
| **R9-6 — separate verification, PC-4 and composed proof** | **PARTLY** | **REJECT** | Separation architecture, report-only builder, persistence order, PC-4 removal and the ordinary composed flow are implemented. Close the job and grant defects in **R10-3–R10-5 and R10-7**. Actual credentials remain owner preconditions. |
| **R9-7 — unknown competitors** | **PARTLY** | **ACCEPT_WITH_AMENDMENTS** | Both mathematical counterexamples are fixed by structural enumeration. Its resource budget does not bound eager enumeration allocation: **R10-8**, affecting unknown-SI runs only. |
| **R9-8 — freeze schema and run binding** | **CLOSED at source** | **ACCEPT** | The hollow freeze is rejected; typed inputs, code hashes, manifest reconciliation and run binding are present. Actual Stage-1/Stage-2 freezes and the disclosed 4.1 ephemeris prerequisite remain outstanding. |
| **R9-9 — derived boundary tolerance** | **PARTLY** | **REJECT** | The new comparison uses derived tolerance, but the real job first invokes the old fixed-three-second comparison: **R10-6**. |
| **R9-10 — manifest-selected stored scope** | **CLOSED** | **ACCEPT** | Reviewed body-enumerating derivations consume the manifest’s stored scope; the non-Moon selection is propagated into expected P1 contacts. |

The AM-16 schema `/3` and explicit `result_policy` are accepted. All 17 frozen literals and their hashes matched the writer fixture; differences in outer JSON indentation are not vector drift. AM-22’s catalogue/selection distinction remains accepted. AM-24’s text is sound; its implementation is incomplete. AM-25 remains a disclosed prerequisite of later numerical activation.

The requested reproductions gave these results:

| Reproduction | Round-10 result |
|---|---|
| Constant P3/P4 and all-against P2 | **Passed the repaired all-NULL behavior** in the executed pure tests: numeric result fields, including objective value, are NULL; peak absent; valence unqualified. |
| Add an admitted record inside an already verified window, omit its membership | The actual Python verifier rejects the omission. 1240 separately compares expected/stored memberships and recomputes dependencies at seal. **I did not execute the PostgreSQL seal attempt.** This particular attack is closed at source. |
| `verify_p1_anchors` with every anchored record omitted for a contact | The direct function now refuses and reports missing expected anchors. **The job can skip this function when the entire anchored record population is empty**—R10-1. |
| Residence `[0,10)` with interior gap `[4,6)` | Independent reconstruction produced approximately `[0,4)` and `[6,10)`; certification rejected the bridged stored residence. |
| Restricted builder INSERT after 1240, with/without helper grant | Source grant verified; the author’s composed positive and revoke-one cases inspected. **Not independently rerun on PostgreSQL.** |
| PD in Sun-in-Libra | Enumeration yields the PD reading as testimony, with the named ruling; MD/AD scored readings remain distinct. |
| Unknown-competitor bridge case | `[0, 2.9e-9, 1, 2, 3, 4]` plus two unknowns includes a maximum plateau of **4/8**. |
| Unknown above the former large sentinel | Known `[1e10, 0]`, matched `1e10`, plus one unknown yields the required percentile range **0–33⅓**. |
| Hollow Stage-1 freeze | Rejected with **60 validation findings**, including the 12 mandatory input identifiers. |

**Migrations table**

| Migration | Verdict | Assessment |
|---|---|---|
| **1206, PC-4 folded** | **ACCEPT at source** | Removing the builder’s verification-table grant before first application is correct. The parent inventory FK cascade invalidates its verification when that inventory is replaced, without giving the builder permission to create attestations. Sealed-generation guards remain applicable. Confirm unapplied status through the authorized operational path before relying on the source edit. |
| **1232 + 1233** | **ACCEPT** | Moon-scope accounting and P1 anchors fit the protected sequence. Their refusal/preflight behavior avoids silently rewriting historical rows. No new objection to these changes. |
| **1234** | **ACCEPT** | Required builder window/membership privileges and helpers are narrowly supplied; membership removal relies on the intended cascade. |
| **1236** | **ACCEPT** | The governed-generation authority guard does not authorize a 5.x authority flip. It belongs on the routine route before the protected stack is introduced as pending. |
| **1240, final submitted version** | **REJECT** | Helper grant, window policy CHECK, two-direction membership checks and verification-table structure are improvements. Record-result enforcement and dependency coverage remain incomplete; AM-24 freshness/runner requirements remain unmet. Amend before first application: **R10-2**, with the other AM-24 closures below. |
| **1241** | **REJECT pending amendment** | Correctly numbered above 1240 and grants-only. Its grants assume 1240 already granted to existing roles; late-created roles miss those grants. The rehearsal also omits a legacy relation that changes the sealer’s read requirements. **R10-7**. Grant closure must be rederived after correcting the job’s combined-gate call. |
| **1242** | **ACCEPT** | DELETE on records/contacts and column UPDATE on admission/prerequisite result are justified for unsealed replacement/finalisation. They do not grant unrestricted UPDATE or TRUNCATE. Existing guards protect sealed generations. |

“Replay-safe” needs precision: the migration ledger can skip an already applied matching file. That is not permission to execute protected SQL again; the raw protected migrations deliberately refuse reapplication. PC-4 does not create a permanent writerless design: the independent verifier becomes the authorized writer after provisioning and grants. Until then, absence of verification is the intended closed state.

The required order remains:

`routine 1234/1236 → protected 1204 → 1206 → 1232 → 1233 → 1240 → routine 1241`

1242 must be available before the restricted replacement/build flow. Its numerical position above 1240 does not allow the routine runner to jump an unapplied protected predecessor. Stage routine prerequisites before introducing pending protected files, or follow the protected sequence first. `migrate.ts` correctly refuses at the first pending protected file; `--only` does not waive its unapplied-predecessor checks.

The composed exhibit is useful evidence. Its **reported 56 passing PostgreSQL tests, zero xfails**, plus the mechanical exhibit, cover the ordinary restricted builder → real verifier login/job → sealer flow, all seal triggers, revoked PUBLIC EXECUTE, first seal, replay, replacement invalidation and builder/sealer contention. Reviewed integration sources match the relevant submitted migration sources; the 1242 head differs in routing commentary rather than executable SQL.

It does **not** establish:

- Complete record derivation under total omission.
- Verifier/builder concurrency safety.
- Correct grant closure when roles are created after 1240.
- The publication branch taken when the legacy windows relation exists.
- Production IAM, secret isolation, approval enforcement, L1 ACLs or deployed identities.
- Full production horizon/class performance.

The generation sealed between 1206 and 1240 is a useful historical-replay fixture. Its owner-created inventory attestation does not prove that the new option-A verification deployment existed at that intermediate point.

**New findings**

**R10-1 — Expected records are still inferred from surviving output. REJECT.**

In [`verification_job.py:250`](/Users/Dev/madhav-l3/pravaha-a53am5/platform/python-sidecar/services/gochara_kernel/verification_job.py:250), P1 anchor verification runs only when anchor columns are absent **or** `_p1_minting_open` finds an existing anchored record. With 1233 installed and all anchored records omitted, both conditions are false. The repaired independent anchor checker is skipped.

I exercised the real `verify_class` control flow with in-memory database adapters, leaving inventory/geometry stages as fixed successful stubs. With empty P1/P3 record/window output, it returned `VERIFIED`, never called the anchor checker, and emitted the window and inventory verification INSERTs. This is a control-flow reproduction, not a PostgreSQL end-to-end run.

The broader defect affects record completeness beyond P1: inventory reconstruction derives search obligations and ledger coverage, while [`window_gate.py:82`](/Users/Dev/madhav-l3/pravaha-a53am5/platform/python-sidecar/services/gochara_kernel/window_gate.py:82) derives expected windows from **stored admitted records**. Removing required records and their windows can therefore make expected and stored emptiness agree. Hashing stored prerequisites also does not independently establish their truth.

**Closing change:** Always certify included P1 anchors when the required schema exists. Independently derive expected records, prerequisite results and admissions for every included materialised path from bound inputs and certified contacts. Compare both directions, including an entirely empty stored path. Add whole-contact, whole-P1, whole-P3 and prerequisite/admission mutation cases through the real job.

**R10-2 — Record results escape both all-NULL enforcement and freshness. REJECT.**

The honest writer writes NULL record evidence/severity and unqualified valence. The independent verifier and database gate do not enforce that result policy on relationship records.

1155 permits finite values in `evidence_for_occurrence`, `evidence_against_occurrence` and `severity`, and permits qualified valence tokens. 1240’s policy CHECK/gate concerns evaluation windows.

The Python preimage at [`window_gate.py:135`](/Users/Dev/madhav-l3/pravaha-a53am5/platform/python-sidecar/services/gochara_kernel/window_gate.py:135), mirrored by 1240’s `ka_gochara_eval_window_inputs_digest`, omits those record result fields. It also omits record provenance/ruling and other semantic fields. Its contact list covers only contacts referenced by surviving records and only their identifiers/endpoints, rather than the complete contact dependencies consumed by certification.

A source-derived attack remains: after verification, use the authorized unsealed replacement capability to delete/reinsert the same record ID with `evidence_for_occurrence = 1`, restore its prerequisites/memberships, and retain every hashed field. Windows remain NULL; the attestation’s dependency digest remains unchanged. The submitted checks do not detect the numeric record result.

**Closing change:** Enforce the manifest policy on all record result fields and valence in independent verification and the seal gate. Define and hash the complete canonical semantic dependency set, including expected contacts without surviving records and certification-relevant contact fields. Keep Python/SQL equivalence tests and add post-verification record-result/provenance/contact mutation seal-refusal tests.

**R10-3 — The job locks after verification and can attest to unchecked replacement data. REJECT.**

[`verification_job.py:215`](/Users/Dev/madhav-l3/pravaha-a53am5/platform/python-sidecar/services/gochara_kernel/verification_job.py:215) starts derivation; chart/global locks are acquired only at lines 281–282. `record_verification` then computes current content/input digests rather than proving that they identify the earlier report’s read state.

Under the allowed READ COMMITTED execution, a builder can replace a checked P1 record between derivation and lock acquisition—for example, changing its house descriptor while preserving record ID, support and window structure. Persistence can then hash the replacement while retaining the report produced from the original. A seal-time digest comparison against that replacement does not repair the mismatch.

This is a source-derived concurrency schedule. Existing builder/sealer contention tests do not exercise it.

**Closing change:** Acquire chart then global protection before the reads feeding an attestation, and retain it through persistence. Bind each report to the exact input/output fingerprint it checked. Include shared preconditions in the consistency strategy. Add barrier-controlled verifier/builder races that demonstrate refusal or serialization.

**R10-4 — Required derivations and the claimed job receipt are incomplete. REJECT.**

Three related gaps remain:

1. [`check_preconditions:149`](/Users/Dev/madhav-l3/pravaha-a53am5/platform/python-sidecar/services/gochara_kernel/verification_job.py:149) skips independent input-vector verification when either ephemeris path or module mapping is absent. It records “NOT re-derived” and continues. The CLI permits an absent ephemeris path. My probe confirmed zero input-verifier calls without refusal.
2. Verification rows carry static verifier ID/version and policy, not the actual runner commit/digest required by AM-24. Neither verification-job module appears in `IMPLEMENTATION_MODULES`.
3. [`candidate_gate:234`](/Users/Dev/madhav-l3/pravaha-a53am5/platform/python-sidecar/services/gochara_kernel/window_gate.py:234) calls only `ka_gochara_window_verification_violations`. The job’s claim to finish with the **same combined candidate gate as sealing** is false.

**Closing change:** Refuse persistence unless input identity has been independently rederived using the actual runtime context. Bind the real runner code identity to results and include both job modules in the governed implementation identity. Require an actual candidate manifest, call the combined candidate gate, and make status/exit reporting faithfully reflect that gate. Recalculate required verifier privileges for the corrected call.

**R10-5 — The identity self-check does not prove its stated separation. REJECT.**

[`check_identity:61`](/Users/Dev/madhav-l3/pravaha-a53am5/platform/python-sidecar/services/gochara_kernel/verification_job.py:61) checks table-level writes using `has_table_privilege`. It misses column-level INSERT/UPDATE grants—particularly relevant because 1242 deliberately uses column grants. PostgreSQL provides separate column privilege checks; a table-level check alone is insufficient. [PostgreSQL 15 access-privilege functions](https://www.postgresql.org/docs/15/functions-info.html#FUNCTIONS-INFO-ACCESS-TABLE).

The function also reports `session_user` without checking its separation. A superuser login operating under a restricted current role can pass the current-role test, contrary to the promised separate-login contract.

**Closing change:** Check effective table **and column** write privileges over the full builder write surface. Validate login/current-role identity and relevant ownership/role escalation paths against option A. Add column-grant and elevated-session negative cases using actual restricted logins. Extend grant postchecks consistently. This is a defect in the detector, not evidence that an uncreated production principal already holds such privileges.

**R10-6 — The real job retains the obsolete fixed tolerance. REJECT.**

Before calling the new certifier, the job invokes `inventory_verifier.verify_aspect_span_contacts`, whose defaults remain **three seconds** and a six-hour sampling step.

I reproduced a smooth one-degree/day boundary with a ten-second stored offset: the new accuracy/speed-derived comparison accepts it, while the old comparison rejects it. The submitted job can therefore reject data valid under its declared certification contract.

**Closing change:** Remove the obsolete contradictory precheck or bring its boundary and union comparison under the accepted derived-tolerance contract while preserving independent reconstruction. Test the complete job on valid slow-motion/station cases and on offsets outside the derived bound.

**R10-7 — Grant closure is incomplete for the stated deployment and publication flows. REJECT.**

Two independent cases are missing.

**Late-created roles.** 1240 conditionally grants to roles that exist at application time. Those grants are skipped permanently when roles are absent. 1241 explicitly does not repeat them, yet its late-role guidance proposes a follow-up carrying only its own statements. Creating roles after 1240, then applying/repeating only 1241, leaves essential window verification privileges absent.

**Legacy relation present.** The composed fixture omits `kala_gochara_windows`. [`ledger.publish:612`](/Users/Dev/madhav-l3/pravaha-a53am5/platform/python-sidecar/services/gochara_kernel/ledger.py:612) reads that relation when it exists. The declared sealer grants do not provide that SELECT. A source-level adapter probe follows the read when the relation exists and skips it when absent. Thus the rehearsal’s publication success does not establish grant closure for the production-shaped schema.

Removing each of 35 grants proves their necessity for exercised flows. It does not prove that every necessary grant was discovered, or that table-wide UPDATE is the minimum scope.

**Closing change:** Either provision principals before 1240 through the owner-authorized path, or provide a reviewed additive grant backfill covering **both 1240 and 1241**. Test absent-role → create-role → grant → verify/seal. Include the legacy relation in the composed fixture and resolve its publication read through the correct governed flow or a justified narrow grant. Expand postchecks to the entire required/prohibited ACL set. Assess narrowing publication UPDATE to the columns actually updated.

**R10-8 — Unknown-enumeration budget is checked after exponential allocation. ACCEPT_WITH_AMENDMENTS, (d) only.**

[`unknowns.py:135`](/Users/Dev/madhav-l3/pravaha-b-measure/platform/python-sidecar/services/gochara_eval/unknowns.py:135) materialises each `_slot_options` iterator before counting structures against the budget.

My bounded probe with ten unknowns and `budget=1` constructed **512 options** before raising `BudgetExceeded`. With forty all-unknown competitors, the analogous allocation contains `2^39` cut patterns before the budget check can help.

**Closing change:** Bound generation/allocation itself through lazy enumeration or a sound precheck. Raise budget exhaustion before exponential work, and return the declared conservative unqualified range rather than partial bounds. Add a fast large-unknown regression.

This does **not** block the proposed known-only 4.1 diagnostic: `raw_intensity` is non-NULL there.

The verification trust boundary should be stated precisely. The database enforces privileges, structural constraints, stored-data consistency checks, attestation freshness for the fields actually covered, and seal immutability. It cannot prove that the authorized verifier executed independent computation. A verifier principal can submit a fabricated attestation satisfying those database checks. AM-24 correctly treats the independently executed, pinned job as part of the trusted system; the submitted code does not yet fulfil that contract.

Persistence order is correct: window rows first, inventory row last. With the job’s per-class transaction, an exception rolls back that class’s writes. Earlier completed classes remain committed; the whole generation is not one atomic transaction. Existing attestations are not automatically invalidated merely because a later run fails. Reporting must use the combined gate and distinguish current prior attestations from newly completed verification.

The certification’s disclosed limits are acceptable **as limits**:

- Sub-60-second excursions are not excluded and could change contact/support membership.
- The guarantee assumes the stated smooth-motion model.
- Derived tolerance accepts bounded boundary differences, including around half-open endpoints.
- Union equality establishes occupied-time coverage, not exact retrograde episode multiplicity or exact-hit identity.

Consequently, an unqualified claim of exact contact-multiset completeness would be false. Carry the bounded guarantee with completeness claims. These limits do not themselves block the all-NULL milestone; AM-25 must be settled before numerical accumulation makes overlapping roots consequential.

The objective maximiser, qualified vedha and qualified P1 numerical paths must remain disabled under their named switches/reasons. The delegated numerical rulings remain ruled but implementation-deferred. PD testimony, P5 hold and unknown-H exclusions remain explicit.

**Ranked amendments**

| Priority | Amendment | Closing evidence | Steps blocked |
|---|---|---|---|
| **1** | **R10-1: independent complete record derivation** | Real job refuses total record/path omission and independently wrong prerequisites/admissions. | **(c)**; also **(a)** through its adopted R9-2 closure prerequisite. |
| **2** | **R10-2: complete all-NULL and dependency enforcement** | PostgreSQL refuses record-result leaks and post-verification semantic tampering; Python/SQL dependency agreement. | **(a), (c)**. |
| **3** | **R10-3: verification consistency and locking** | Barrier-controlled builder/verifier races serialize or refuse; persisted fingerprint identifies checked data. | **(c)**; also **(a)** through AM-24/R9-2. |
| **4** | **R10-4: mandatory identity derivation, runner binding and combined gate** | Missing runtime identity refuses; actual runner identity recorded; job/seal gate agreement. | **(c)**; also **(a)** through AM-24/R9-2. |
| **5** | **R10-7: complete provisioning/publication grants** | Late-role and legacy-relation composed flows pass with all guards and restricted identities. | **(c)** verification/sealing; **(a)** requires a reviewed viable 1241 sequence. |
| **6** | **R10-5: sound separation check** | Column-write and elevated-session negative tests refuse. | **(c)** verification. |
| **7** | **R10-6: one consistent boundary contract** | Complete job accepts valid derived-tolerance cases and refuses invalid ones. | **(c)** verification. |
| **8** | **R10-8: bounded enumeration work** | Large unknown population reaches conservative fallback within its declared budget. | **(d), unknown-SI runs only**. |

After source changes, rerun the composed rehearsal with the new attacks and final migration bytes. The current exhibit cannot stand as proof for changed verification or grant code.

**Step lines**

**(a) BLOCKED BY R10-1, R10-2, R10-3, R10-4 and R10-7** — the adopted AM-24/R9-2 closure and reviewed grant-sequence prerequisites remain unsatisfied. The owner’s protected-window dispatch remains a separate required act.

**(b) UNBLOCKED** — binding and selecting the reviewed 1.1.0 registry versions may proceed under the existing governance, with historical versions preserved and numerical activation disabled.

**(c) BLOCKED BY R10-1–R10-7** — the current source does not establish the claimed complete, current, independently verifiable all-NULL candidate.

**(d) BLOCKED BY S1-REQ-EPHEMERIS and the uncompleted actual Stage-1/Stage-2 freeze and extract receipts; additionally R10-8 for unknown-SI runs.**

Before verifier/sealer principals exist:

- **(a):** Source amendments, routine-prerequisite preparation and disposable rehearsals may proceed. Once source gates are closed and the owner dispatches it, the role-guarded schema window can technically apply without those principals. That choice requires the complete later grant-backfill route; skipped grants are not queued.
- **(b):** Registry binding/selection does not require verifier or sealer credentials. It must not be represented as verification, publication or numerical activation.
- **(c):** A build may be produced and held behind closed verification/seal gates. Its truthful status is **BUILT · NOT VERIFIED · NOT SEALED**. Such a held build does not establish this review’s end-to-end candidate claim. Verification must wait for the separate login, complete ACLs, runtime identity and operator-dispatched job; sealing must wait for the separate sealer and owner-approved workflow.

No new principal, secret, service account, approval environment or production grant is authorized by this review.

For **(d)**, the corrected SI semantics and typed freeze tooling are acceptable at source. The remaining work includes the disclosed 4.1 writer/input-identity change: capture its actual ephemeris identity, including consumed Moon inputs, and refuse the disallowed fallback. Do not substitute 3.0’s identity.

Then complete and commit Stage-1 before extraction; produce the exact authorized extract with live-manifest reconciliation; seal the extract bytes and Stage-1 identity in Stage-2 before inspection/scoring; validate the scoring run against both. The 4.1 result remains **diagnostic, T-honesty UNVERIFIABLE, `pass:false`, never flip-eligible under v2.3**.

**What I could not verify**

I did not execute PostgreSQL, contact production, create credentials, dispatch a migration/build/verification job, or generate candidate output. Database seal/refusal and concurrency conclusions above are explicitly source-derived unless attributed to the author’s exhibit.

My read-only execution covered:

- **64 passed, 1 skipped**: policy, contact completeness/certification, boundary tolerance, anchors and input-vector tests.
- **66 passed, 1 skipped**: registry/version selection, scope and static 1240 tests.
- **93 passed**: measurement, unknown competitors and freeze/run-binding tests.
- Additional in-memory reproductions described above.

Tests requiring excluded database or filesystem-writing fixtures were deselected; these counts are not a substitute for the composed PostgreSQL suite. The packet’s 56-test and mechanical-exhibit results are author evidence, not my own SQL runs.

The requested round-9 artifact is absent from the tracked `c884eacfc` tree. I read the supplied sibling scratchpad copy of `ASTRA_REVIEW_A5_5_SPEC_AMENDMENTS_v1_8.md` before substantive review. The final findings are anchored to the pinned branch heads above. Local `origin/main` changed during the review; its closing identity is recorded separately and was not substituted into the reviewed comparisons.

No files were written, no Git write command was run, and the reviewed worktrees remained clean.