---
artifact: ASTRA_REVIEW_A5_5_SPEC_AMENDMENTS
version: "1.5"
reviewer: "Codex gpt-6-astra"
date: "2026-10-02"
verdict: REJECT
reviewed_commit: >-
  305c35dc2 (campaign/pravaha);
  PR #2897 576907611a35e0d13d521f616ab397127a35d9a0;
  PR #2894 8cf6fba6e1aacb402ea7203b31d3a3cc8e9d8a60;
  PR #2867 fc10a91fe722c316c0d7d0d88b4693a4563a8d7d;
  PR #2884 dba48ec5cd3eb026450a0cd4568a0c879b2c2830;
  origin/main e88e63a5a1f4c74b0c1a86981c4d96d0836f9e91;
  integration reference pravaha/a53-am5-inventory 58a26a02008a6c4abd1b6f7bbfc86c05d2484683
authority: "Review only; authorizes nothing."
---

**Verdict: REJECT the current A5.5 gate packet as sufficient for passage.** The blocking contradictions concern qualification propagation, Moon-resolved period obligations, and window construction/peak semantics. The remaining amendments below make the integration and measurement contracts reviewable.

The prior acceptance of **AM-1–AM-12 and migrations 1204/1206 remains intact**, with its existing conditions. Migration **1220 is accepted**. Adding immutable registry versions is also sound; the problem is incomplete binding and consumption of those versions.

Independent in-memory checks passed the **108 graha × offset cases**, 18 current kernel operand checks, and equality comparisons for **13 existing factor rows and six existing path rows**. The same probes reproduced the qualification-loss and factor-version mismatches described below. These were Python checks, not PostgreSQL integration tests.

References below use **A** for `GOCHARA_SPECS_V1_5_AMENDMENTS_DRAFT.md`, **S** for `GOCHARA_DESIGN_SPECS_v1_4.md`, and **P** for `EVALUATION_PROTOCOL_v2_3.md`. Code paths are under `platform/`.

| Item | Verdict | Disposition |
|---|---|---|
| AM-13: geometry and kernels | ACCEPT_WITH_AMENDMENTS | Extent membership and unqualified points are sound. Geometry validation, applicability handling and qualification propagation remain incomplete. R1, R4. |
| AM-13: immutable versions | ACCEPT_WITH_AMENDMENTS | Existing row contents remain unchanged; historical replay need not break. Binding and per-class supersession require correction. R5. |
| AM-14 | REJECT | Literal Moon exclusion does not settle `period_lord:*` intervals resolving to Moon. Mandatory serving scope is not demonstrated. R2. |
| AM-15 | ACCEPT | Correct for the natal relationship predicate, using the class’s already-resolved signature houses. It does not replace relative-frame resolution or each record’s own frame arithmetic. |
| AM-16 | ACCEPT_WITH_AMENDMENTS | Necessary inputs are named, but complete fingerprint contents and verification are not specified. R6. |
| AM-17 | REJECT | Column types are compatible with 1156; component cardinality, prerequisite-restricted support and peak objective are not adequately defined. R3. |
| SI addendum | ACCEPT_WITH_AMENDMENTS | The timing of the choice can constitute disclosed pre-registration. Its NULL handling is not supplied by the cited protocol sections. R7. |
| PR #2897 | ACCEPT_WITH_AMENDMENTS | Catalogue and current fail-closed point behavior are sound. Not ready for candidate consumption. R1, R4, R5. |
| PR #2894 | ACCEPT_WITH_AMENDMENTS | Numeric grid agrees with the frozen oracle. Version binding, canonical input adaptation and citation attribution need amendment. R4, R5. |
| PR #2867, post-review delta | ACCEPT | Test-only delta repairs restricted-sealer replay coverage. The AM-14 test proves coexistence with Moon coverage, not complete AM-14 implementation. |
| Migration 1220 | ACCEPT | Appropriately limited grants; repeatable; no generation-sealing authority granted. |
| PC-1 | ACCEPT_WITH_AMENDMENTS | Correct activation gate; actual-role and full-call-graph evidence remains required. R9. |
| PC-2 | ACCEPT_WITH_AMENDMENTS | Identity, registry and manifest prerequisites must precede the first candidate build. Moon receipt acceptance can remain tied to on-demand use. R9. |
| PC-3 | ACCEPT_WITH_AMENDMENTS | Correct protected-window gate; add exact-head, database-version and complete writer-flow evidence. R9. |
| PC-4 | ACCEPT_WITH_AMENDMENTS | Correct distinction between process and database independence; complete the verifier’s read/helper privileges and effective-role separation tests. R9. |
| ND-ORB decision packet | REJECT | It conflates admission and ranking orbs and misstates options A, D and E. Corpus exhaustion is not established. R8. |

Ranked amendments follow. Each identifies the step it blocks.

1. **P1 — Preserve `unqualified` through evidence reduction. Blocks the first candidate build.**

   In `python-sidecar/services/gochara_rules/score.py:53–83`, `record_channel_value()` marks an unresolved factor result as unqualified, but `path_channel_scores()` skips that record and returns ordinary numeric totals.

   With the new point kernel, I reproduced:

   ```text
   activity_kernel("degree_point", delta_lambda_deg=0)
       → value=None, reason=orb_not_ratified

   record_channel_value(...)
       → evidence_for=0, evidence_against=0, unqualified=True

   path_channel_scores(...)
       → evidence_for=0, evidence_against=0
   ```

   The final result has lost the qualification flag. This directly contradicts S:209–213 and would let the SI adapter interpret unavailable point evidence as known zero.

   **Required code change:** make qualification part of the reduction result and preserve it through window storage, valence and measurement. An applicable factor with `null_state="unqualified"` must not disappear from a numerical reduction.

   **Closing text:**

   > An unresolved applicable factor propagates score qualification. An affected evidence channel is NULL unless its value is established independently under an explicitly specified reduction rule. Known partial subtotals may be reported separately, but never as complete evidence. Admission and admitted support remain unchanged.

   Required cases: all records unqualified; mixed qualified/unqualified records; shared-root aliases; genuine numeric zero; testimony; and explicitly non-applicable factors. The latter may be omitted by declared applicability, without pretending their operands were evaluated.

2. **P1 — Resolve Moon exclusion after period-role resolution. Blocks affected-class sealing and AM-14 acceptance.**

   A:1286–1291 excludes Moon-agent obligations, while accepted AM-11 retains stable `period_lord:md|ad|pd` obligations covering the whole horizon.

   The integration reference makes the conflict concrete:

   - `gochara_kernel/inventory.py:268–275` assigns `missing_inputs` when a period role resolves to Moon.
   - `inventory_verifier.py:357–359` independently reproduces that assignment.
   - Migration 1206:880–898 rejects uncovered intervals and every `missing_inputs` interval.

   Removing obligations whose literal `agent` equals `moon` cannot fix this. Removing Moon-resolved intervals leaves coverage gaps. Relabelling an unperformed search as complete would defeat the accepted contract.

   The new test at `gochara_b6_am5_search_inventory.db.test.ts:858–877` uses an already non-Moon fixture, adds a `moon_on_demand` partition, and checks literal Moon-agent count zero. It does not exercise this conflict.

   **A concrete closing contract is:**

   > Moon exclusion applies to the resolved concrete transiting agent, including period-role agents. Each period-role obligation has a snapshot-bound applicable time domain. Moon-resolved portions are explicitly accounted for as excluded from the stored tier; they are neither missing search intervals nor completed geometry searches. Completeness requires coverage of the applicable domain and verified accounting of its excluded complement.

   Implement that domain—or an explicit, equivalently checked interval disposition—in both derivations and the seal contract. If this needs storage/check changes, use a new additive migration. Do not weaken `missing_inputs_present` or `obligation_uncovered`.

   Thus, **“1206 needs no change” is established only for ordinary concrete-agent exclusion, not for the complete AM-14 proposal**. The existing 1206 implementation remains correct for its accepted contract.

   Also require a machine-readable scope, for example `stored_non_moon`, bound to the manifest and returned by the mandatory coverage response constructor. Missing scope must prevent an unqualified “complete” answer. Test positive and no-window responses, before and after an on-demand query.

   Exclusion must follow the **transiting agent**: it must not remove Moon as a natal target, Moon-frame evaluation by other agents, or Sun/Jupiter delivery during a Moon bhukti.

3. **P1 — Define window components, prerequisite-restricted support and the optimized quantity. Blocks AM-17 and window-writer acceptance.**

   A:1303 says “one window per (class × path-version)” while its next sentence requires a connected union. A path can have several disconnected components. A single row cannot represent them without either discarding components or filling gaps.

   Moreover, “admitted records’ supports” must mean support **after all necessary predicates are applied**. For P4, Jupiter support `[0,2]` and Saturn support `[1,3]` yield joint support `[1,2]`, not their raw union `[0,3]`.

   “Earliest instant of the max” does not name the maximized function. Frozen S:321–323 and O-RP-3 explicitly require P4’s maximum of `min(activity_Jupiter, activity_Saturn)`. The new P4 registry row retains that rule.

   Counterexample: on `[0,1]`, let Jupiter activity be `0.2+0.8t` and Saturn activity `1−0.8t`. P4’s prescribed peak is `t=0.5`. Maximizing the best record selects an endpoint; maximizing their summed evidence produces a plateau. Earliest-tie handling cannot reconcile these objectives.

   **One concrete replacement that closes the ambiguity is:**

   > Emit one window per maximal connected component of the prerequisite-satisfied support, within a class and path-version. Never bridge a gap. P4 support is the intersection of the two agents’ influence unions. Its peak retains the frozen max-min objective; each agent’s activity reduction is explicitly defined over its applicable records. For other paths, the peak objective is the per-root-reduced evidence_for function. Choose the earliest attained maximum of the specified objective. If that objective is unqualified, peak_instant and dependent peak values are NULL with the reason retained.

   This proposed non-P4 objective must be explicitly adopted before implementation or candidate inspection; an alternative is acceptable only if equally precise and frozen.

   At the selected peak, the proposed bounded `score`, nonnegative unbounded evidence fields and NULL severity fit [1156:247–309](https://github.com/Marsys-Technologies/Madhav/blob/8c7e32fefd6b660670fab1b76a8983e641c1f486/platform/migrations/1156_gochara_eval_window.sql#L247). The CHECKs validate values; they do not clip them or establish the reduction semantics.

   **Required code change:** `valence.py:26` still declares `severity: float = 0.0`. Change the undefined-severity representation to `float | None = None`, and ensure nullable evidence follows the unresolved branch. PR #2894 does not contain this repair.

   Retaining the full admitted union is consistent with P’s merge and T-FP rules. A resulting budget failure is a failure to report, not grounds for a hidden score threshold.

4. **P1 — Make “by geometry” a validated contract, and validate the future angular branch. Blocks candidate consumption; angular validation also blocks any orb-enabled successor.**

   The seven classified `object_kind` values are consistent with the intended grammar; `star:<n>` denotes an extent. Leaving `varga_position` explicitly unqualified is safe, though it is not complete scoring support for all eight kinds.

   However, `kernel_factor.py:38–54` dispatches solely on the supplied name and Boolean. Migration 1155:534–544 checks the kind vocabulary and contact FK, but does **not** establish agreement between `object_kind` and the physical object’s `canonical_target`.

   A point mislabelled `house_span`, with `inside=True`, therefore takes the step branch and bypasses the unratified-orb branch. The kind-enumeration test does not detect this mismatch.

   **Closing text:**

   > Before factor evaluation, resolve the record’s physical object and validate its canonical target against its object kind. `span:1`–`span:12` and `star:1`–`star:27` are extents; the declared point kinds require `point:<longitude>`. Mismatches fail validation. `varga_position` remains explicitly unqualified. Membership comes from the validated contact geometry, not an unchecked caller flag.

   For aspects, membership/distance must use the directed aspect ray, with seam-safe angular distance. Preserve the inclusive offset convention and N-14’s prohibition on node-cast aspect records. The 108-case helper grid passes, but does not prove these record-level conversions. Persisted lowercase graha tokens also need a closed, tested adapter to the helper’s title-case vocabulary.

   The current `orb_deg=None` branch correctly returns unqualified. **Latent configuration probes**, conducted only in memory, found:

   | Row orb | Result at distance 0.5 |
   |---|---|
   | `0` | `ZeroDivisionError` |
   | `-1` | `1.5` |
   | `NaN` | `0.0` |
   | `Infinity` | `1.0` |

   Require a finite, strictly positive numeric orb, a ratified decision binding and matching immutable factor version before evaluating the angular formula. Invalid configuration must fail closed, not score.

   A declared membership step is consistent with NK-4: inside support it supplies a known unitless factor of one. Its zero outside support must not become a second admission filter.

5. **P1 — Complete version-aware persistence and consumption. Blocks registry activation and the first candidate build.**

   The immutable-version approach itself passes. Old row values are unchanged, composite memberships can reference the new versions, and 1206’s historical replay branch deliberately does not demand adoption of later registry rows.

   Three integration gaps remain:

   - The integration binder’s `factor_rows()`, `path_rows()` and membership checks still select global `RULE_VERSION="1.0.0"` (`rule_registry.py:216–312`). Adding rows to the Python catalogue does not bind them.
   - PR #2894’s `drishti.py:43` returns `("graduated_drishti","1.0.0")`, while new P3 requests `1.1.0`. I reproduced this with the two PR modules loaded together. `factor_product()` does not check that mismatch.
   - The nested Python `applicability` object is not directly admissible as `operand_selector`: 1154:221–240 permits a **flat** object of tokens, numbers and token arrays, not nested objects or JSON null. A flattening contract can avoid DDL, but it has not been supplied.

   **Required changes:** select explicit composite path/factor references; preserve each prerequisite’s own version; encode applicability losslessly into the existing typed fields; read it back and compare it; and dispatch evaluators using the exact membership reference. Do not solve this by globally bumping `RULE_VERSION`, which would also disturb unchanged paths and predicates.

   The persisted declaration must include the branch selection, relation applicability, step values, angular form and explicit unratified state. Omit an unavailable numeric orb from the flat encoding rather than inserting JSON null. The top-level numeric-form description must accurately identify the piecewise function.

   Replace A:1267’s blanket supersession sentence with:

   > An older version is `superseded_by_version` only when another version of that path is `included` for the same class. Where no successor is included, retain the independently derived computed-empty or exclusion disposition and basis.

   Otherwise unknown-H or empty classes can hit 1206’s intentional `superseded_without_included_version` refusal.

   For citation accuracy, the quoted Brihat Jātaka passage supports ordinary fractions but does not itself numerically establish Jupiter’s and Saturn’s specials as exactly `1.0`; the other quoted chunks are incomplete. The values nevertheless agree with frozen O-CF-DRISHTI. Attribute that authority explicitly instead of implying the quoted served passage proves every numeric entry. My local BPHS reread found supporting special-aspect calculations, but it was not a fresh served-corpus retrieval.

6. **P1 — Specify and verify AM-16’s complete fingerprint. Blocks the first candidate build.**

   The named components are necessary, but two builds are distinguishable only if the relevant content actually enters a canonical, verified preimage.

   In particular:

   - A `ka_gochara_rule_path_seal` row contains only path, version and timestamp. There is no built-in “seal digest” committing the complete rule graph.
   - Path/predicate/factor rows alone do not commit prerequisite ordering or soft-factor membership edges.
   - `node_convention="mean"` distinguishes a convention label, not two different mean-node series or source revisions.
   - 1206:767–768 compares manifest and snapshot vectors. Two identical stale or incomplete vectors pass that comparison. It does not independently recompute AM-16’s registry or L0 fingerprints.

   **Closing text:**

   > The input vector has a versioned key schema and canonical serialization. Its registry digest covers selected path, predicate and factor payloads, ordered prerequisite memberships, soft-factor memberships, applicability declarations and the accounted sealed-version census, excluding only enumerated audit fields. It binds consumed L0/arc/node-series identities and content digests, both admission and activity-orb policies, applicable rulings, and the implementation identities governing geometry, evaluation and window construction. Inputs already transitively bound by the snapshot need not be duplicated.

   The writer and independent derivation must verify these bindings against the inputs they actually consume. Changing any result-bearing component must change the input identity or cause a mismatch refusal. Freeze test vectors, including membership-only, node-series-only and window-algorithm changes.

   Historical replay must continue checking its original bound inputs rather than recomputing a fingerprint of today’s catalogue.

7. **P1 before measurement — Finish the SI pre-registration. Blocks the first candidate measurement.**

   Choosing `si := evidence_for` after seeing the disclosed 3.0 baseline can be legitimate pre-registration for a later candidate. It is not blind validation, and the protocol already discloses that authors have seen the LEL.

   The substantive gap is addendum:20. P §6.5 defines **class computation coverage**, not how a merged candidate with a NULL intensity is ranked. P §9 prohibits zero filling but does not complete that missing rule.

   **Required amendment:** distinguish admission, computation coverage and score qualification. Define NULL behavior before merging, representative selection, candidate counting, ranking, timing and plateau detection.

   A conservative concrete policy is:

   > Admitted supports remain in the admission union and T-FP burden regardless of score qualification. If a merged candidate’s highest-si representative cannot be determined because a contributing intensity is unknown, do not invent a numeric si or peak. Mark the affected ranking/timing result unqualified and ineligible to establish a passing endpoint; retain the events and report the affected candidates. Known zero remains a numeric value. Unknown necessary-predicate admission is not treated as admitted.

   Freeze before the first candidate output is inspected: the window/peak rules in R3, qualification policy, selected registries and orb state, UTC-to-IST conversion, merge implementation, stored-value precision, `1e-9` tie handling, candidate-set construction, scorer/adapter commits, extract hashes, cohort, thresholds, controls and rerun policy.

   Preserve the existing validity floor and all event-denominator rules. Correct “clipped by the schema CHECK” to “constrained by the schema CHECK.”

8. **P1 before the native decision — Correct the ND-ORB options and corpus claim.**

   The packet’s central error is treating the **contact/admission orb** and **activity-kernel scale** as one decision, despite AM-13 distinguishing them. With fixed admitted supports and no score threshold, changing only the latter does not change T-FP’s admitted-day union.

   **Replace the decision framing with:**

   > Decide separately the angular criterion that admits/enumerates contact support and the angular scale that ranks an already admitted contact. State explicitly if one ruling binds them to the same value. A support change requires the corresponding convention and geometry invalidation; a ranking-only change cannot silently alter support.

   Required option corrections:

   - **A:** Exact contact does not inherently make records disappear. A closed singleton timestamp range can be nonempty, 1156 does not categorically forbid it, and the measurement protocol converts endpoints to inclusive dates. Specify the representation and consequences; do not implement it as division by zero. [PostgreSQL range semantics](https://www.postgresql.org/docs/16/rangetypes.html)
   - **B/E:** The quoted durations are constant-speed illustrations, not geocentric transit or class-union predictions. Retrograde motion, stations, overlapping contacts and span-based paths matter. E is not demonstrably the lowest-exposure option retaining point records; B permits smaller values.
   - **D:** Sphuṭa-dṛṣṭi is a different angular strength model, not merely the existing kernel with its orb removed. Specify the complete piecewise rule, direction, normalization, specials, node treatment, admission domain and interaction with graduated strength. Avoid counting the same strength twice.
   - **“Plainly monotone”:** Withdraw this generalization. The local BPHS text at lines 16605–16630 explicitly alternates increasing and decreasing segments.
   - **Versioning:** Replace “under a new version if needed” with “under a new factor version and new consuming path versions once the existing rows have been bound.” An unratified immutable row cannot later acquire an orb in place.

   **Missed corpus leads:** `design/CORPUS_READS_v1_0.md:99–106` records a served `tajaka_neelakanthi` corpus that is Devanagari-only, where English predicates return zero. Search terms including `दीप्तांश` and OCR variants are an unresolved retrieval route. Separately, `platform/scripts/bootstrap/lib/tajaka_corpus.ts:27` contains a per-graha orb table, but its source inventory explicitly labels it a **derived internal summary**, not a primary translation.

   These leads do not ratify a Parāśari transit orb. They do mean the packet should report “not found in the stated searches,” rather than imply exhaustion of the served corpus.

9. **P2 — Put the preconditions before the actions they protect.**

   **Before sealer activation:** retain PC-1; require the initial seal and both replays under the intended restricted role, with PUBLIC EXECUTE revoked and the complete helper closure available. Verify effective privileges and inability of the builder to seal. The source repair in #2867 addresses the earlier test defect; actual activation evidence remains outstanding.

   **Before the protected 1204+1206 window:** retain PC-3 and require exact migration/application heads, a supported PostgreSQL version, faithful object ownership/default privileges, complete role grants, realistic 26-class volume, contention/seal timing, and per-file failure recovery. The advisory database job needs explicit evidence at the reviewed head; its existence is not sufficient.

   **Before the first 5.0 candidate build:** add a named gate:

   > Accepted successor contracts and oracles, version-aware registry binding/read-back, geometry and qualification handling, the resolved Moon-scope contract, deterministic window construction, complete input/manifest binding, class census and candidate invalidation must be implemented and demonstrated through the intended restricted writer’s complete output flow.

   Split PC-2 accordingly. Moon receipts and deferred P6 containment remain prerequisites of their actual on-demand use. ND-ORB may remain open for a deliberately unqualified-point candidate, provided that state and its measurement consequences are frozen.

   **Before claiming database-enforced verifier independence:** retain PC-4, but grant the verifier the source/registry reads and invoker-helper EXECUTE needed for independent derivation—not merely SELECT on inventory tables. Remove the builder’s verification-write capability and test effective inheritance/role-switching boundaries. Until then, describe independence as a property of the separate derivation code.

   **1220 needs no corrective grant change:** it grants 18 specifically named function signatures and seal-table SELECT, without seal-table writes, `ka_gochara_seal_generation`, grant option or SECURITY DEFINER changes. Repeated GRANT is idempotent. It does not remove unrelated inherited privileges, and its suite does not establish capability for the future window-writing flow. [PostgreSQL GRANT semantics](https://www.postgresql.org/docs/16/sql-grant.html)

What I could not verify:

- I did not run PostgreSQL integration or mutation suites, connect to production, inspect actual deployed privileges, or measure realistic seal latency. Author-reported test counts are not independent execution evidence from this review.
- No candidate measurement was run. Absence of candidate result files supports only a repository observation; it cannot prove that no off-repository run or candidate-output inspection occurred.
- The requested prior-review paths were absent from this checkout. I read the matching v1.4 and v1.2 files in the parent scratchpad.
- I did not fetch because fetch writes Git state and the task prohibits Git writes. Read-only GitHub metadata confirmed the reviewed PR heads. Local tracking refs advanced during the review; the cited main files were unchanged between `8c7e32fefd` and `e88e63a5a`, and the cited integration files were unchanged across the observed advance.
- No files were created or edited.

Fresh served-corpus verification was blocked because the corpus tool required approval while this session’s approval policy was `never`. The local BPHS evidence and documented Tājaka retrieval leads therefore do not constitute a confirmed current served-corpus lookup.