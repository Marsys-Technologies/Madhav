---
artifact: ASTRA_REVIEW_A5_4_TIER0S
version: "1.2"
reviewer: "Codex gpt-6-astra"
date: 2026-09-30
verdict: REJECT
reviewed_commit: 5d1bd3cbf
authority: "Review only; authorizes nothing."
---

## Verdict

**REJECT — three P1 amendments remain partly closed:** the production daśā read contract, preservation of vedha evidence through persistence, and identity/value-level rebuild acceptance.

Verified HEAD: `5d1bd3cbf74aaa4b820f420594eb8ac1c89b1aa0`. I reviewed the requested rework and used protected baseline `297c09c7948cbb2d9480cc0ea72c10876ef9c0fc` to distinguish inherited main changes.

My read-only test runs produced **420 passed and 12 failed**. Six tests requiring prohibited fixtures were deselected; another 78 pin tests were outside the selected A5.4 cases. Additional counterexamples ran in memory, with database connections and filesystem mutations blocked.

Path abbreviations below:

- `S` = `platform/python-sidecar`
- `C` = `platform/python-sidecar/scripts/kala_gochara_cutover`

## Closure table

Numbers in this table refer to the **seven ranked P1 amendments in v1.1**.

| P1 | Status | Independent rerun and evidence |
|---|---|---|
| **1. Negative-only production construction** | **CLOSED** | Signed input `[-0.8]` through the production constructor now gives **PROMISE 0.8**, activity **0.2176**, λ **0.0278528**, and an adverse era window with negative signed intensity. No helper-side conversion to positive weights was needed. `C/step06b_windows_projection.py:939`. |
| **2. Frozen daśā contract and C5 identity** | **PARTLY CLOSED** | Wrong/null explicit pins, conflicting siblings, exact half-open selection and C5 relation IDs improve. At the AD boundary, my probe selected **Mars one millisecond before** and **Rahu at the boundary**. However, actual `step06a.main()` still fetches and canonicalizes **before selecting the build pin**. Adding an overlapping unrelated build raises `DashaReadConflict`; explicitly supplying the pin succeeds. A duplicated MD/AD tree also fails after parent aliases converge. `C/step06a_class_context.py:401`, `:412`; `S/services/gochara_grammar/dasha_data.py:121`, `:135`, `:205`, `:223`. |
| **3. Vedha on affected production paths** | **PARTLY CLOSED** | Actual writer payloads now give **clean 1.0**, **expired obstruction 1.0**, and **0.7 rather than 0.49** for duplicate roots when a cited scale is supplied. Cancellation, coverage gaps and testimony tests pass. Without a cited scale, obstruction correctly carries `factor=None`. But shared materialization discards these distinctions, and the projection fetch discards `formula_version`. Primary-contact identity remains a graha/house/residence description rather than the required contact identity. `S/services/gochara_v3/engine.py:470`, `:964`; `S/pipeline/orchestrator/writers/ka_gochara_v3_century_materialize.py:1570`; `C/step06b_windows_projection.py:1710`; `S/services/ka_vedha_gochara/gate.py:173`. |
| **4. Kakṣyā identity and direction** | **CLOSED** | Re-ran the conflicting-grid case: retained indexes `[0,2,3,4,5,6,7]` keep their identities in both consumers. At **217.5°**, direct entry selects **Mars**, including its zero bindu; retrograde selects **Jupiter**, including its competing positive bindu. Projection now consumes the ledger branch. `S/services/gochara_grammar/primitives.py:879`; `S/services/gochara_v3/engine.py:1559`; `C/step06b_windows_projection.py:760`, `:1017`, `:1669`. |
| **5. C2 evidence reduction** | **CLOSED** | Two independent `0.5` roots produce **1.0**; aliases of one root remain **0.5**. Channel independence and order invariance pass. The three-field evidence uses the new reduction; the old noisy-OR result remains only in the disclosed legacy calculation. `C/step06b_windows_projection.py:1171`, `:1304`, `:1338`. |
| **6. Complete preimage certificate** | **CLOSED at source level** | Full-row serialization includes IDs and timestamps and distinguishes JSON null from strings. The generator rejects zero-count snapshots and rejects `"empty"` as a positive-count certificate. SQL checks precede `DELETE`, restoration is transactional and rechecked, and rehearsal stops before the writer on a mismatched/empty snapshot. PostgreSQL execution remains unverified. A separate rehearsal assertion defect is listed below. `C/resonance_rebuild_backup_sql.py:102`, `:126`, `:139`, `:156`; `C/resonance_rebuild_disposable_rehearsal.py:579`, `:595`. |
| **7. Identity/value acceptance and destination identity** | **PARTLY CLOSED** | Moving `afflicted` from `career_setback:10L` to `marriage:7L` now fails. R-5 tokenization is repaired. Cluster identity is checked before database creation. However, swapping positive fact IDs between event classes, or changing a retained weight from **0.5 to 0.125**, leaves the measured acceptance inputs unchanged and returns **`[]` failures**. Sensitive/arudha/yoga identity sets omit event-class associations, and expected preserved values are not checked. `C/resonance_rebuild_disposable_rehearsal.py:249`, `:298`, `:658`, `:665`, `:682`. |

The previously closed findings and steps remain as follows:

| Earlier item | Reconfirmation |
|---|---|
| **Original #1 — angular evaluation** | **Still CLOSED.** The `359° → 1°` shortest-arc probe gives decay **0.6** for a 5° orb. `253.43° − 249.79°` gives **3.64°**, decay **0.272**, and weighted activity **0.2176**. Angular/episode tests pass. `C/step06b_windows_projection.py:296`. |
| **Original #6 — tārā testimony** | **Still CLOSED.** Stars **25 and 21**, inclusive count **24**, class **6**. The annotation appears on day rows only. With versus without testimony, raw intensity is **0.1024** on era/month/day rows, with identical signed intensities. `C/step06b_windows_projection.py:896`; `S/services/gochara_v3/engine.py:975`. |
| **Step 1 — N5 separation** | **Still holds at the producer.** Two peaks 30 days apart remain two admitted/retained peaks, producing two month/day families within one era. `C/step06b_windows_projection.py:1484`; test at `S/tests/l3/gochara/test_step06b_windows_projection.py:283`. |
| **Step 2 — N6 birth_anchor** | **Still holds for rebuilt maps.** Enumeration contains **26 classes**, excluding `birth_anchor`. This does not remove previously published windows. `S/services/ka_gochara_resonance/writer.py:203`, `:220`, `:1322`. |
| **Step 3 — N7 mūrti honesty** | **Still holds.** Computed → `algorithmic_approximation`; uncomputed → `unsourced`; both → `corpus_verifiable=False`. Final writer stamping remains present. `S/services/ka_moorti_nirnaya/logic.py:94`, `:102`; `writer.py:440`. |

**Judgment on the two legacy evaluators:** leaving them unchanged is acceptable for this tree, but the submitted tests are not a sound general proof of unreachability. They search literal call spellings in selected directories; aliases and callback references can evade them (`S/tests/l3/gochara/test_vedha_interval_gate.py:422`).

My broader AST scan of **643 non-test Python modules** found no references outside the defining modules to `compute_quality_gates`, `quality_gates_at`, `OverlayInterval` or `coverage_gaps`, including relevant aliased imports. That supports the current dead-code claim. It does not resolve the production persistence defects above.

## ‘4.0’ impact

**I found no PR-owned automatic rewrite of published `4.0` contacts/windows or authority flip.** Candidate admission and published-generation refusal remain, including inside `write_windows()` (`C/step06b_windows_projection.py:1805`, `:2086`). The authority-based reader remains unchanged (`S/services/ka_gochara/service.py:320`, `:339`).

The activation boundaries are nevertheless different:

- **New projections:** signed PROMISE handling, C2 evidence, directional kakṣyā qualification and repaired interval evaluation change newly computed windows and their explanations.
- **Shared evaluation/materialization:** the changed functions are not generation-gated. They apply whenever invoked after deployment. Legacy-shaped vedha rows now become unavailable rather than receiving PG353 attenuation; the shared persistence path currently loses that unavailable state.
- **Resonance and overlays:** rebuilding the chart-scoped resonance map or unversioned overlays changes subsequent consumers after commit. These are not isolated by a window-generation label.
- **Packaged provenance:** writer digests and the L3 successor change with the packaged code/metadata. They do not establish rebuilt, deployed or accepted output.

Thus, “published rows are not automatically rewritten” is supported. A blanket “no serving impact until the planned rebuild” claim is not.

## Rebuild

The full-preimage repair is substantive. `row_to_json(t)` covers every column, including `id` and `computed_at`; content-only hashing is separately retained for idempotent reruns. Empty, absent, foreign-chart and mismatching snapshots are checked before deletion. The restore and its full-row verification share one transaction.

**False success remains possible.** My in-memory source-row mutations demonstrate that the acceptance projection can bless incorrect class-to-fact associations and changed retained values. Repeating the same incorrect writer output merely reproduces its content digest; that proves repeatability, not correctness.

The production runbook also has two concrete gaps:

1. **R-3 claims both EXCEPT directions but supplies only actual-minus-live.** With eligible live IDs `{yoga1, yoga2}` and output `{yoga1}`, the positive control passes, unbacked count is zero, and the printed EXCEPT is empty. Missing `yoga2` is not detected. See `C/resonance_rebuild_R1_R6_runbook.md:214`–`:228`.
2. **R-1 expected IDs are not ayanāṃśa-pinned.** A positive fact from another ayanāṃśa makes a correct canonical rebuild fail the expected-set comparison. The writer filters by canonical ayanāṃśa and class-relevant subjects; the runbook must construct expected identities using the same eligibility contract. See runbook `:173`–`:184` versus `S/services/ka_gochara_resonance/writer.py:819`, `:967`.

The rollback rehearsal introduces an additional evidence defect at `C/resonance_rebuild_disposable_rehearsal.py:713`: it compares two **post-refusal** full digests to each other. I evaluated that exact expression with changed IDs/timestamps and unchanged content; it returned **True**. The foreign-chart check at `:720` likewise remains content-only.

I did not demonstrate an empty/stale-snapshot route that deletes the partition under the inspected rollback SQL. However, the current acceptance checks can report success for missing or incorrect rebuilt data. The verified backup is a recovery mechanism, not proof that the rebuild is correct.

## Pins

**L3 admission passes the reviewed checks.**

- Successor: `l3:aa6a67fb7152:889e2c1fdcfe`.
- Source: `aa6a67fb715248fa2b2eccffaf5327692319194a`.
- Predecessor: `l3:f4c69a6d0cd4:829354703812`.
- Exactly one L3 history entry is appended; its archived pin and writer slice equal the protected main baseline.
- Membership is unchanged. The exact changed set is `ka_gochara`, `ka_gochara_resonance`, `ka_gochara_v3_century_materialize`, `ka_moorti_nirnaya`, and `ka_vedha_gochara`.
- All **123** regenerated writer digests match the checked-in inventory.
- All **six A5.4 pin tests pass**, including authority/source binding and delta classifications.

The delivery-topology check reports inherited L1/L2 errors and no L3 error. L1/L2 pins, histories and corresponding writer inventory slices are unchanged against the protected main baseline. They are **out of scope and not rejection grounds**, as instructed.

## Regressions

The significant rework defects are the nested duplicate-tree failure, loss of the new vedha states during shared persistence, and incomplete/newly overbroad runbook acceptance.

The adjacent suite also has **12 failing tests**:

- **9** in `services/gochara_v3/tests/test_graded_suppression.py`.
- **3** in `services/gochara_v3/mechanisms/tests/test_w31_latta_quality_gates.py`.

These expect retired PG353/latta attenuation or legacy payload behavior. They need reconciliation with the new contract; restoring the prohibited multipliers would be the wrong repair. The adjacent suite is currently not green.

## Ranked amendments

### Merge-blocking

1. **P1 — Apply the daśā pin before canonicalization, and canonicalize duplicate trees recursively.**  
   Actual `main()` omits the new `build_id` argument and filters only after the fetch has already canonicalized all builds. My mixed-build reproduction aborts before that filter. Separately, duplicate MDs collapse, but their identical AD children are not recollapsed after parent normalization and are rejected as overlapping siblings.

   Select the qualified source before conflict handling; normalize and collapse descendants after their parents. Add actual-main mixed-build and complete duplicated MD/AD/PD-tree counterexamples. Evidence: [step06a_class_context.py:401](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2769c/platform/python-sidecar/scripts/kala_gochara_cutover/step06a_class_context.py:401), [dasha_data.py:121](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2769c/platform/python-sidecar/services/gochara_grammar/dasha_data.py:121).

2. **P1 — Preserve vedha state and identity through the real persisted output.**  
   My engine-to-writer probe produced three different evaluator states—`unavailable`, `clear`, `obstructed`—but identical persisted suppression objects with `value: 1.0`. Carry the detailed state, nullable factor, coverage, testimony and identities into the materialized row. Fetch `formula_version` on the projection path and finish the required primary-contact/rule identity contract.

   Test writer-shaped payloads through serialization, not just the gate helper. Evidence: [engine.py:964](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2769c/platform/python-sidecar/services/gochara_v3/engine.py:964), [ka_gochara_v3_century_materialize.py:1570](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2769c/platform/python-sidecar/pipeline/orchestrator/writers/ka_gochara_v3_century_materialize.py:1570), `C/step06b_windows_projection.py:1710`.

3. **P1 — Make rebuild acceptance compare eligible row identities and expected preserved values.**  
   Compare class-associated identities, not global DISTINCT references, and independently check retained weights, qualifiers, resolution states and provenance fields required by the contract. Add source-row mutations that preserve counts and global ID sets. Repair the production runbook’s missing reverse yoga comparison and scope expected facts to canonical, class-eligible inputs.

   Evidence: [resonance_rebuild_disposable_rehearsal.py:665](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2769c/platform/python-sidecar/scripts/kala_gochara_cutover/resonance_rebuild_disposable_rehearsal.py:665), `C/resonance_rebuild_R1_R6_runbook.md:173`, `:214`.

### Separate follow-ups

- **P2:** Replace the refusal-check tautology with a recorded pre-refusal versus post-refusal full certificate; use full certificates for foreign-partition preservation too.
- **P2:** Reconcile the 12 obsolete-contract test failures and strengthen or accurately qualify the literal source-scan reachability assertions.

## What I could not verify

- PostgreSQL execution of snapshot, rebuild, rollback or disposable-cluster rehearsal.
- Production contents, deployed code, live authority, stored `4.0` rows or actual serving behavior.
- The claimed production/synthetic rebuild counts through an independent database run.
- Database/file-writing integration cases, the full repository/TypeScript CI suite, or a newly constructed squash-delivery tree.

No files were created, edited, moved or deleted; no git write command or database connection was run. Neither prohibited directory was accessed.