---
artifact: ASTRA_REVIEW_A5_5_SPEC_AMENDMENTS
version: "1.6"
reviewer: "Codex gpt-6-astra"
date: "2026-10-02"
verdict: REJECT
reviewed_commit: >-
  campaign/pravaha 9628b77f603bfdc7e547ac2bb593ff282450b20f;
  origin/main c6cc65d50aa74faec90925dfdc7400c660a540e5,
  subsequently 23bf43bcf8187b73a09bda3f971a935e40b20d31;
  PR #2905 c083cbd6dd78e3b641dc64038f5c4d0f64945681;
  PR #2909 358c332113e98cc3585403e014e3e30751394597;
  PR #2897 d70d76cb069741860c17ee8f3192023969e484c8;
  PR #2907 b598ee302a7d272988d8017287da0426b446e41f;
  PR #2901 37de1bb2c89179d57f6a16f6ea60464f346276de;
  PR #2867 fc10a91fe722c316c0d7d0d88b4693a4563a8d7d;
  origin/pravaha/a53-am5-inventory
  4f8895384e19394ce118cae879fc77d6ff040f69,
  subsequently 3677cccaebd5cdf8fdde208cd52455be28ad8d5c;
  unchanged references:
  PR #2817 b9d5d27184427703ea79cda57f633c165b211f04,
  PR #2894 8cf6fba6e1aacb402ea7203b31d3a3cc8e9d8a60,
  PR #2884 dba48ec5cd3eb026450a0cd4568a0c879b2c2830
authority: "Review only; authorizes nothing."
---

**Verdict: REJECT the packet as sufficient to pass A5.5 or satisfy PC-5.**

The amendments substantially improve the contracts. The score reducer, kernel validation, Moon-domain migration and window-component construction contain real fixes. However, qualification can still be lost while choosing a peak; P1 support remains broader than its time-dependent permission; the writer cannot bind the actual successor registry declarations; and its verifier accepts function-valued windows without reproducing their numbers.

The writer advanced during this review. This verdict incorporates **`3677cccae`, including design v1.13**, its adoption of `score.path_channel_scores`, and its new input-vector implementation. Findings below do not treat those additions as absent.

Prior acceptance of **AM-1–AM-12, migrations 1204/1206 and migration 1220 remains intact**, with its existing conditions. **AM-15 remains ACCEPT.** Migration 1232 is **ACCEPT_WITH_AMENDMENTS at source-review level**; its integration and deployment evidence remain incomplete.

References below use:

- **A** — `00_ARCHITECTURE/briefs/pravaha/design/GOCHARA_SPECS_V1_5_AMENDMENTS_DRAFT.md` at `9628b77f6`.
- **W** — `platform/python-sidecar/services/gochara_kernel/` at `3677cccae`.
- **G** — `platform/python-sidecar/services/gochara_rules/` at the named PR head.
- **V5** — `platform/python-sidecar/pipeline/orchestrator/writers/ka_gochara_v5.py` at `3677cccae`.

The latest writer brief is under `00_ARCHITECTURE/briefs/nirmana/l3_autonomous/gochara_wp0_7/A5_3_REGISTERED_WRITER_BRIEF_v1_0.md`; its latest appended design is **v1.13**.

**R1–R9 status**

“CLOSED” concerns the review finding. It does not certify that a later operational gate has been executed.

| Item | Status | Verdict | Remaining closure |
|---|---|---|---|
| **R1 — qualification propagation** | **PARTLY** | **REJECT** end-to-end | #2905 repairs `path_channel_scores`; the latest writer also preserves NULL opposing evidence at the selected peak. Peak search still discards unknown portions, `aggregate_paths` still discards unknown paths, and stored record placeholders/reason retention remain wrong. Amendment 1. |
| **R2 — Moon-resolved obligations and serving scope** | **PARTLY** | **REJECT** end-to-end | 1232 correctly checks exclusion equality against its consumed snapshot. Writer/verifier still produce `missing_inputs` for Moon periods; the manifest and mandatory response path do not implement the required scope. Independently validate the snapshot’s §4.0 selection. Amendment 2. |
| **R3 — components, support and peak** | **PARTLY** | **REJECT** | Connected components, P4 intersection and the original max-min counterexample are repaired. P1 prerequisite restriction, global peak qualification, numeric verification, P4 `score` semantics and tie tolerance remain incomplete. Amendments 3, 5 and 7. |
| **R4 — validated geometry and angular configuration** | **PARTLY** | **ACCEPT_WITH_AMENDMENTS** | The helper rejects the original malformed probes and mislabelled point. The sweep bypasses its ratification checks; the helper misclassifies an exact nakṣatra boundary. Amendment 8. |
| **R5 — version-aware persistence and consumption** | **PARTLY** | **REJECT** for activation | Composite membership/read-back support improved, and explicit drishti calls return the requested reference. Actual successor rows fail the writer’s separate codec; enumeration, prerequisite evaluation and drishti consumption still lose versions. Amendment 4. |
| **R6 — complete fingerprint** | **PARTLY** | **ACCEPT_WITH_AMENDMENTS** | The contract is substantially closed and new runtime code exists. Its schema differs from the model, its implementation closure is incomplete, and the promised fixed expected-byte vectors are absent. Amendment 9. |
| **R7 — SI pre-registration** | **PARTLY** | **ACCEPT_WITH_AMENDMENTS** | Admission burden, known zero and unknown merged representatives are addressed. Unknown competing candidates can still disappear from percentile arithmetic and make another candidate appear qualified. Amendment 10. |
| **R8 — native orb decision** | **PARTLY** | **ACCEPT_WITH_AMENDMENTS** | Decision packet v1.1 repairs the substantive errors. The native-facing open list still presents one decision and links v1.0; its corpus statement is stronger than the packet’s evidence. Amendment 11. |
| **R9 — precondition ordering** | **CLOSED** as text | **ACCEPT** | PC-1–5 now precede the actions they protect. Actual-role, deployment and complete-writer receipts remain outstanding. Extend PC-3 explicitly to 1232 and its predecessor/grant requirements before execution. |

**New items**

| Item | Verdict | Assessment |
|---|---|---|
| **N1 — AM-18 amendment** | **ACCEPT_WITH_AMENDMENTS** | Cited binary nullification can reduce a record’s contribution to zero while preserving admission. State explicitly that the factor affects the favourable-residence contribution before class-relative channel assignment. Scope and qualification must survive storage and serving. |
| **N2 — #2901 implementation** | **REJECT** as ready for consumption | Exception pairs, half-open intersections, node-only uncertainty and Mercury’s Moon exemption are sound in the tested complete-input cases. Empty/gapped residence inputs can become known inactivity; pair loading does not enforce the claimed complete cited set; writer integration is absent. Amendment 6. |
| **N3 — Stream A window writer** | **REJECT** | Component/P4 repairs pass, but qualification, P1 support, successor binding and verifier coverage remain blocking. |
| **N4 — native open decisions** | **ACCEPT_WITH_AMENDMENTS** | Preserve ND-VIPAREETA and ND-NODE-VEDHA as open. Repair the orb entry and attribution links. Amendment 11. |
| **N5 — P1/P2/P5 answers** | **ACCEPT_WITH_AMENDMENTS** | Reusing L1 rules and L0 data is the correct authority direction. Missing-input guards and a common authority for dignity classification/breakpoints are still needed. P1 has no qualified window scoring today. P5 remains held. Amendment 12. |
| **N6 — unchanged accepted work** | **ACCEPT**, carried forward | No new defect established in the unchanged 1204/1206/1220 contracts. This is not fresh deployment, runtime or role-provisioning evidence. |
| **N7 — #2903 repin tool** | **Not reviewed** | Excluded from judgment by the packet. No repin or rebuild authorization follows from this review. |

**Re-run results**

I executed the AM-16 model and directly invoked existing pure test cases using pinned Git blobs in memory: **9 qualification, 27 kernel, 17 drishti, 10 vedha and 81 window cases passed**. These were direct Python invocations, not a full pytest, PostgreSQL or CI run.

Prospective cross-PR checks composed the specified modules in memory; they do not establish that a merged integration branch exists.

| Round-6 reproduction | Result |
|---|---|
| Applicable unqualified record reduced to numeric zero | **Fixed in `path_channel_scores`.** Affected totals are NULL, with separate partial subtotals and reasons. Further loss during window maximization remains. |
| Drishti `1.1.0` request returning `1.0.0` | **Fixed when `factor_ref` is passed.** The writer still calls the default and discards the returned reference. |
| Orb `0`, `-1`, `NaN`, `Infinity` | All four now raise **`KernelFactorConfigError`** in #2897’s helper. |
| Point labelled `house_span` | Now raises **`TargetKindMismatch`** in the helper; sweep geometry tests also reject it. |
| P4: Jupiter `0.2+0.8t`, Saturn `1−0.8t` | Correct peak **`t=0.5`**, objective **`0.6`**, evidence-for **`1.2`**. |
| P4 supports `[0,2)` and `[1,3)` | Correct joint window **`[1,2)`**. |
| Disconnected supports `[0,1)` and `[2,3)` | Correctly produce **two windows**. |

**Ranked amendments**

1. **P1 — Qualify the maximum over the whole support, and retain qualification through storage. Blocks the first candidate build.**

   At `W/window_sweep.py:632`, a function-valued record is marked unqualified only when it is undeterminable over its **entire** support. `maximise_earliest:402–408` drops unknown samples and maximizes the remaining values.

   Reproduced at the latest writer head with the actual P2 `1.1.0` factor rows and a legal AM-18 value function:

   ```text
   favourable residence:
     first half: vedha value 0
     second half: None, node obstruction undecided

   emitted:
     peak = window start
     score = 0
     evidence_for = 0
     null_states_used = []
     unqualified_reason = None
   ```

   The second half could contain a larger value. Neither the maximum nor its earliest instant has been established.

   The newer `reduce_at` correctly changes the earlier opposing-channel reproduction from zero to **NULL**. However, its per-instant qualification reasons are not incorporated into the persisted window disclosure. Separately, `G/score.py:148–154` still gives:

   ```text
   aggregate_paths([0.2, "unqualified"]) -> 0.2
   ```

   `W/record_store.py:777` also inserts unevaluated record evidence and severity as `0.0`. `W/window_store.py:172–183` stores `null_states_used` but drops the draft’s detailed unresolved reasons.

   **Required closure:**

   > A peak is qualified only when the objective’s maximum and earliest maximizing instant are established over the entire component. Unknown portions cannot be removed from that determination. A bounded reduction may remain qualified only where the result is proved independent of the unknown operands.

   Implement that rule for window and cross-path reductions. Store NULL for unevaluated record evidence/severity; persist, or obligatorily reconstruct from bound inputs, the affected channels and reasons. Add partial-support unknown cases, unknown competing paths and storage/read-back assertions. Preserve genuine computed zero.

2. **P1 — Finish AM-14’s writer, verifier and serving implementation. Blocks affected-class sealing and the first candidate build.**

   **1232’s source-level result is sound within a valid snapshot:**

   - It is a new successor migration; it does not edit the accepted 1206 file.
   - It necessarily alters the state CHECK and replaces the completeness function; “additive” does not mean CREATE-only.
   - Undoing the two state-list extensions and appended scope-check call yields the **byte-identical 1206 completeness function**.
   - `missing_inputs_present` remains unchanged.
   - The excluded union must equal the consumed Moon-domain union, clipped to the horizon, with the correct MD/AD/PD level.
   - Non-period exclusions are refused; 1206’s overlap guard prevents a portion being both searched and excluded.
   - The interval remains digest-bound and protected by finalization/sealing.
   - No seal/replay weakening was found. Historical replay retains the accepted 1206 branch.

   References: migration `1232:81–147,306–353`; 1206’s interval guard and replay branch.

   **Can an adversarial writer exclude a non-Moon interval?** An interval outside the Moon domain of the **supplied, valid snapshot** is refused. This is not yet an unconditional proof against a wrongly selected snapshot. The SQL domain accepts consumed IDs without independently checking their system, build, ayanāṃśa and tier against §4.0. `W/inventory_verifier.py:327–328` likewise reads the supplied IDs’ level/time/lord. A Moon row from an inadmissible build is not made authoritative by hashing it.

   **Required closure:**

   - Change both independent derivations from Moon-period `missing_inputs` to the checked `excluded_moon_tier` disposition.
   - Independently validate the consumed daśā population against the approved §4.0 read contract, including conflicting/extra/omitted rows. Include a wrong-build or wrong-system Moon-row adversary.
   - Put `stored_scope="stored_non_moon"` in the candidate vector. Neither reviewed writer vector implementation currently supplies it.
   - Make the mandatory positive **and no-window** response constructor obtain and return that scope from the bound generation; missing scope must refuse an unqualified completeness claim.
   - Test before/after on-demand queries, plus preserved Moon natal targets, Moon frames and Sun/Jupiter delivery during Moon bhukti.

   Correct the stale batch-checklist AM-14 row that still says “1206 unchanged; no new migration.”

3. **P1 — Restrict P1 support by its running-period domains. Blocks AM-17 implementation acceptance and the first candidate build.**

   `W/record_store.py:1219–1236` stores the full clipped contact support. `:1294–1302` evaluates `period_running_at` at one occurrence instant, which can precede the requested horizon.

   Therefore a positive ingress test can admit support through a period gap; a negative ingress test can discard a valid later portion. NULL scoring does not repair incorrect admission.

   **Required code change:** intersect each P1 contact’s support with the applicable resolved running-period domains before writing admitted support. Retain multiple disjoint pieces. Have the independent verifier derive this restriction from the pinned periods, rather than merely union the builder’s stored supports.

   Required cases: period begins/ends inside a contact; multiple licensed pieces separated by a gap; ingress before the horizon; and retrograde re-crossings.

4. **P1 — Use one codec and carry composite versions through the entire writer. Blocks binding `1.1.0` and the first candidate build.**

   The binder’s composite references, per-member versions and read-back are improvements. They do not yet compose with the actual PR rows.

   Reproduced at `3677cccae`:

   ```text
   actual activity_kernel@1.1.0
     -> RegistryDivergenceError: unknown key ['aspect_geometry']

   actual vedha_attenuation@1.1.0
     -> RegistryDivergenceError: unknown keys
        ['mapping', 'qualification_on_active', 'scope_not_needed_for',
         'scope_on_inactive', 'unqualified_reasons']
   ```

   `W/rule_registry.py:237–304` contains a second codec, incompatible with Stream B’s `flat_selector.py`. It also infers “ratified” from orb presence and drops declaration information.

   Further gaps:

   - `W/evaluator.py:163,214,294,349,433` and other emission sites use global `RULE_VERSION`.
   - `W/inventory.py` iterates sealed versions but calls enumeration without the selected version.
   - `W/record_store.py:1389–1396` reads prerequisite version `_pv`, then supplies the **path version** to `set_prerequisite_result`.
   - `V5:94–99` calls drishti without the membership’s factor reference and returns only its value.

   **Required code change:** adopt the canonical lossless codec; pass selected path references into enumeration/materialization; pass `_pv` into prerequisite updates; pass exact factor references into evaluators and verify returned references. Derive per-class supersession only when the successor is included for that class.

   Exercise the **actual** #2897/#2901 rows through binding, SQL read-back, inventory and record evaluation. Synthetic older-shaped applicability fixtures are insufficient. Keeping current bindings at `1.0.0` pending acceptance is itself appropriate.

5. **P1 — Make verifier limitations enforceable. Blocks claims of independent window verification and the first candidate build.**

   `W/window_verifier.py:178–179` skips numerical reproduction whenever a member is function-valued. `V5:681–696` discards the returned counters and reports semantic re-derivation as passed.

   At the latest head, a fabricated **one-root P2 window with `evidence_for=123.0`** was accepted:

   ```text
   {"windows": 1, "numeric_reproduced": 0, "structural_only": 1}
   ```

   Even the universal one-root product bound excludes that value. The verifier also trusts kind/support declarations without independently validating the physical target and prerequisite-restricted geometry.

   **Required code change:** reproduce dynamic qualification, values and peak objectives from independently obtained operands. Until implemented, retain an explicit unverified result and prevent it satisfying PC-5; do not emit an unconditional semantic-success statement. Verify support against source geometry and permissions.

   The surviving P4 mutant is **legitimately equivalent in the restricted constant-step domain**, where both agent activities are one. That classification is acceptable. It supplies no evidence for dynamic P4 verification. Using it to imply coverage of the full sweep is a hole.

   AM-18’s proposed verifier call to the same `derive_vedha` function also does not independently test that function’s interval logic. Separate the derivation or supply an independent oracle over the source intervals.

6. **P1 — Distinguish missing vedha coverage from proven inactivity. Blocks #2901 consumption and qualified P2 windows.**

   `G/vedha_derive.py:139,146` checks dictionary-key presence, not coverage. With every required key present and every span list empty, the function returns:

   ```text
   Sun primary:     inactive, value=1, Moon-exclusion scope
   Mercury primary: inactive, value=1, no scope
   ```

   No obstructor residence was actually known. Partial gaps have the same defect.

   `pairs_from_rows:60–80` also accepts a fabricated `("sun",1,2,"unrelated citation","favourable")` row. It does not validate the complete 36-pair census. A missing pair becomes declared non-applicability at `:131–133`, so an incomplete load can silently remove the factor.

   **Required code change:**

   - Validate the authoritative pair load’s completeness, supported citation provenance, unique keys, favourable rule type and house domains; bind its consumed content identity. Do not duplicate the mapping as a competing authority.
   - Distinguish absent data from a validated non-applicable pair.
   - Establish residence coverage over the primary domain for each necessary obstructor. Where no known cited obstruction settles the value, coverage gaps must yield NULL or refusal.
   - Preserve the valid precedence: known cited obstruction → zero; otherwise undecided node obstruction → NULL; only established inactivity → one with the required Moon scope.
   - Integrate structured factor results into the writer. `VEDHA_SOURCE` remains `None`; a float-only callback cannot carry `not_applicable`, `vedha_active`, reason and scope.
   - Persist and serve `excluding_on_demand_moon_obstruction` on affected records/windows; Mercury-primary inactivity is complete only when the other required inputs are complete.

   **AM-18’s doctrinal amendment is defensible:** zero contribution need not remove an admitted window. Its wording should say:

   > Apply the cited binary factor to the favourable-residence record’s contribution, then assign that contribution to the event class’s channel. Active obstruction never changes admission or admitted support.

   This avoids treating “FOR” as an unconditional channel label.

7. **P1 — Reconcile the peak objective, stored `score`, tie rule and search method. Blocks AM-17 implementation acceptance and qualified dynamic windows.**

   **`act_g=max` is a defensible reading of frozen P4.** It preserves the existential influence union and a bounded activity value: one qualifying influence suffices. Summation would introduce reinforcement by contact count. Freeze this explicit reduction in AM-17; the frozen text alone does not specify its numerical implementation.

   Three contradictions remain:

   - **Stored score:** A:1390 defines maximum record product at the selected peak. The writer uses the P4 max-min objective instead (`W/window_sweep.py:718–719`), and the verifier repeats it. With constant Jupiter activity `1` and Saturn `0.25`, the writer stores `score=0.25`; AM-17’s stated field is `1`. Either implement the stated field or explicitly amend that definition before candidate inspection. Keep objective and stored field distinct.
   - **Tie tolerance:** writer `_TIE=1e-6` and verifier `_TOL=1e-6` select peaks, while the frozen measurement contract specifies `1e-9`. Separate storage-comparison tolerance from peak-tie semantics.
   - **Missed extrema:** the 64-sample maximizer does not receive internal vedha/aspect change boundaries. A legal binary vedha function equal to one only on a short interior interval, and zero elsewhere, returned peak-at-start with value zero in my probe.

   **Required code change:** partition at exact factor-state boundaries, then solve each applicable objective over those pieces using a method that establishes the global maximum. Add a short inactive vedha island and unequal-agent P4 cases. Align the writer, verifier, AM-17 and SI adapter on the same frozen field and tie definitions.

8. **P1 for angular activation; P2 for deferred star consumption — Finish geometry enforcement.**

   The repaired helper rejects the four invalid orbs and the mislabelled point. Two residuals are concrete:

   - A real `activity_kernel@1.1.0` row modified in memory to contain orb `5` while retaining `orb_status="unratified_nd_orb_open"` is rejected by #2897’s helper, but `W/window_sweep.py:181–208` returns a numeric function and value `1.0`.
   - `kernel_factor.activity_kernel("star","star:4", body_longitude_deg=40.0, …)` returns `0.0`. Floating floor division by `360/27` places this exact fourth-nakṣatra boundary in the preceding extent.

   **Required code change:** route sweep evaluation through the validated row/geometry contract, or implement equivalent explicit ratification and decision-reference checks. Do not infer ratification from numeric presence. Make nakṣatra membership correct at all 27 boundaries, the seam and adjacent representable positions.

   Validate support geometry beyond an optional check at the chosen peak. Missing geometry must not become affirmative membership. The star defect may remain behind an explicit non-consumption gate; it does not justify claiming complete extent support.

9. **P1 — Finish and freeze the actual AM-16 preimage. Blocks the first candidate build.**

   Credit the new implementation: `W/input_vector.py` binds registry payloads, memberships, census, ephemeris-file hashes, orb policies, rulings and selected source digests. The SQL registry derivation is meaningfully separate.

   It still does not close R6:

   - The runtime schema/serialization differs from `am16_vectors_model.py`, whose promised output must currently be reproduced byte-for-byte.
   - The model generates its expected table at runtime and asserts changed/unchanged identities. It contains no fixed expected-byte/hash table that catches serializer drift.
   - `IMPLEMENTATION_MODULES:41–50` omits result-bearing modules including `substrate`, `inventory`, `permission`, `frames` and the writer orchestration itself. For example, changing the substrate domain or permission implementation can change results without changing these implementation digests.
   - File/library identity is not the explicitly required consumed arc/node-series content binding. A transitive substitute needs a specified, demonstrated equivalence.
   - Future L0 pair and P1-table consumption needs content binding. The independent runtime check currently reproduces the registry component, not the complete consumed-input contract.
   - `verify_replay:233–242` checks the original registry component; that alone is not proof of complete original-input replay.

   **Required closure:** choose one normative typed schema and canonical encoding; reconcile the model and runtime through an explicit pre-inspection amendment if necessary; freeze literal preimages and expected hashes; complete the result-bearing implementation/input closure; verify those bindings at both derivations’ consumption boundaries. Preserve original-input historical replay.

   The model’s perturbation checks pass. They are useful sensitivity tests, not sufficient acceptance evidence for the current runtime format.

10. **P1 before measurement — Qualify ranks against the full candidate set. Blocks the first candidate measurement.**

   SI addendum v1.1:29 excludes unknown candidates from percentile arithmetic. That can qualify a different candidate whose rank depends on them.

   Counterexample: one fixed candidate set has intensities:

   ```text
   matched candidate = 2; other known candidates = 1, 0;
   two additional admitted candidates = NULL, NULL
   ```

   Removing the unknown competitors gives the matched candidate rank 1. If both unknown values exceed 2, its actual rank is 3 of 5: percentile **40**, not zero. Retaining event denominators does not repair candidate-order uncertainty.

   **Required text:**

   > Score qualification does not remove admitted merged candidates from the frozen candidate set or N. If an unknown competitor can alter a relevant representative, rank, timing choice or plateau-validity conclusion, that result is unqualified and cannot establish a passing endpoint, unless the conclusion is proved for every admissible value of the unknown inputs.

   Implement that rule in the adapter. Preserve the admitted-day union, known zero, event rules and the 17-event validity floor. Freeze actual adapter/scorer commits and extract hashes before inspection; a list of fields to freeze is not the completed freeze.

11. **P1 before the native decision — Synchronize the decision-facing documents.**

   `NATIVE_OPEN_DECISIONS_v1_0.md` v1.1:12–16 still presents one ND-ORB question, links packet v1.0, and makes an unqualified corpus-absence assertion.

   **Required text change:** replace that entry with separate **ND-ORB-ADMISSION** and **ND-ORB-SCALE** entries, link v1.1, and use “not found in the stated searches.” State explicitly whether any eventual ruling governs one policy or both. Preserve the corrected duration caveats and the fact that changing only ranking scale does not change the admitted-day union.

   Also correct the stale orb-packet pointer in AM-13. The amended packet itself is acceptable; the native-facing decision surface is not yet consistent with it.

12. **P1 before qualified P1 scoring — Reuse L1 without inheriting silent defaults or split boundary authority.**

   Calling L1’s pure functions with transit operands and reading L0 tables is the correct authority direction. No new transit-specific convention is needed.

   It still needs an explicit strict wrapper. At reviewed `origin/main`:

   - `ga_condition_writer.py:389–394` returns non-combustion for a missing graha row and defaults missing numeric fields to zero.
   - `compute_panchadha_maitri:452` defaults an unrecognized combination to neutral.
   - `_load_combustion_orbs:669–680` falls back to literals after a read failure.
   - Dignity classification uses `_MOOLATRIKONA_RANGE`, while the proposed crossing schedule reads L0 `from/to`.

   **Required code/contract change:** validate complete typed operands before calling the pure functions; missing or invalid source rows yield named qualification failure. Do not use fallback loaders for governed transit scoring. Derive crossing boundaries from the same effective authority used by classification, or enforce equality and refuse divergence until the L0/L1 owner repairs it. Bind both data and implementation identities; replace the duplicate maitrī table through the accepted loader.

   **Is P1 scored today? No qualified P1 window is produced by this writer.** Its categorical value mappings and channel assignment remain unavailable; windows have NULL score/evidence/peak. The numeric record placeholders identified in amendment 1 must not be mistaken for completed P1 scoring. AM-19 and ND-COMBUSTION remain future work. P5’s hold and P5c/P5d input gates remain in force.

**What remains before each next step**

| Step | Required evidence/change |
|---|---|
| **(a) Protected window for 1204 + 1206 + 1232** | It can share one protected capability window, in logical order **1204 → 1206 → 1232**, with separate file transactions. Rehearse exact application/migration heads, ownership/default privileges, grants, realistic volume, contention and partial-failure recovery. Prove the actual deployment invocation against the migration ledger. |
| **Migration-order qualification** | `migrate.ts:756–763` refuses skipped unapplied predecessors. The 1232 live fixture explicitly applies **1216 between 1206 and 1232**. Therefore the deployment’s single `--only` list works only when all unselected predecessors are already applied. Otherwise stage them through their proper route; the fixture does not prove that the single deployment invocation works on that ledger. |
| **Sealer/verifier activation** | Demonstrate initial seal and both replays under the intended restricted sealer, PUBLIC EXECUTE revoked, full helper closure including 1232’s two new functions, and builder refusal. Establish verifier source/helper access and remove builder verification-write capability. These are PC-1/PC-4 receipts, not consequences of merge status. |
| **(b) Bind `1.1.0` registry versions** | Close amendment 4 using actual successor rows and exact membership references; read back under 1154’s existing flat-selector contract; preserve old rows and valid historical replay. No new selector DDL is established as necessary. |
| **(c) First `5.0` candidate build** | Close qualification, support, scope, geometry, verifier and fingerprint findings; demonstrate the complete restricted-writer flow and class census. The inventory verifier still refuses included P2 because it lacks an independent derivation. P5 may remain explicitly held. Deliberately unqualified points/P1 are permissible only under the frozen qualification and measurement contract; they do not excuse incorrect admission or false verification. |
| **(d) First candidate measurement** | Close amendment 10; reconcile stored fields, peak/tie semantics and all scopes; freeze selected versions, orb states, cohort, controls, conversions, precision, adapter/scorer commits, extract hashes and rerun policy. Verify extracts and NULL handling before computing endpoints. |

**What I could not verify**

- I connected to **no production database**, created no disposable database, and ran no database integration or mutation suite. The author’s live-test, mutation and CI counts remain reported evidence.
- I did not verify current remote CI, protected deployment readiness, actual role provisioning, production migration ledger, seal cost or contention.
- The AM-16 SQL/Python agreement tests were read but not executed against PostgreSQL.
- I did not independently repeat served-corpus searches or verify current production L0 contents. Classical attribution findings are limited to the supplied exhibits and code.
- No complete `5.0` writer build, candidate extract, serving-scope round trip or candidate measurement was observed.
- The review is pinned to the listed commits. No file was created, edited, moved or deleted; the pre-existing untracked round-6 review remained unchanged.

