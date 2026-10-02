---
artifact: ASTRA_REVIEW_A5_4_TIER0S
version: "1.1"
reviewer: "Codex gpt-6-astra"
date: 2026-09-30
verdict: REJECT
reviewed_commit: 39d591d76
authority: "Review only; authorizes nothing."
---

## Verdict

**REJECT. Two prior P1s are CLOSED; six are PARTLY CLOSED.**

The rework fixes substantial portions of the original defects, but the production-shaped negative-only counterexample still produces **zero windows**. Daśā selection remains outside the frozen read contract, the shared v3 evaluator retains legacy vedha suppression, kakṣyā qualification can select the wrong donor, and rebuild verification can accept incorrect results.

Steps 1–3 remain correct within their original scope. The protected-baseline pin and delivery-topology checks pass.

I read the round-1 review first, then the rework, updated PR body, sealed contract, frozen v1.4 specs/oracles, and D-SPECS C2/C5. I distinguished inherited main changes from the PR contribution using protected baseline `1010659db391a9770b2af3f16adac0dfa71b02f5`.

For references below:

- `S` = `platform/python-sidecar`
- `C` = `S/scripts/kala_gochara_cutover`

## Closure table

| Prior P1 | Closure | Independent rerun and file:line evidence |
|---|---|---|
| **1. Angular integration, episode support and aliases** | **CLOSED** | Saturn `40° + 60° → 100°`, Mars `10° + 90° → 100°`, and Jupiter `220.31° + 240° → 100.31°` each return activity **1.0**. Two weight-0.5 episodes separated by 100 days now yield **0.5** at the first episode; aliases contribute once; evaluation outside support yields zero. The station oracle returns **[0.8, 0.5, 0.4, 0.5, 0.8]**. Evidence: `C/step06b_windows_projection.py:1001`, `:1013`, `:1044`, `:1124`, `:1517`. Distinct-root evidence accumulation remains defective under P1-4/C2 below. |
| **2. Frozen C5 per-instant permission** | **PARTLY CLOSED** | The factory is installed, memoization uses the evaluation instant, and O-PP-2’s per-level licences are correct: Mercury testimony; Mars AD scored versus Rahu AD testimony; Saturn PD scored at both interior instants; class licence scored at both. However, my probes accepted a **wrong sole build**, accepted **NULL build/tier** under explicit pins, retained two conflicting rows with the same `(level,parent,index)`, and orphaned valid children after collapsing duplicate parents. Evidence: `C/step06b_windows_projection.py:430`, `:449`, `:583`, `:2153`; `C/step06a_class_context.py:225`; `S/services/gochara_grammar/dasha_data.py:82`, `:90`, `:123`, `:143`. |
| **3. Vedha intervals on actual scoring paths** | **PARTLY CLOSED** | The projection now returns clean **1.0**, respects the March 1 obstruction endpoint, and applies one supplied factor to duplicate roots. The shared v3 evaluator still returns **0.85 for a clean row**, **0.70 on April 1 for an obstruction ending March 1**, and **0.49 for duplicate roots**, using the empty-scale fallback. It still disregards interval cancellation, testimony and root deduplication. Projection scoping remains by body, without the required primary-contact/rule identity. Evidence: `S/services/gochara_v3/engine.py:470`, `:555`, `:583`, `:876`; `C/step06b_windows_projection.py:1132`, `:1631`, `:1737`. |
| **4. Three-field evaluation and operand scoping** | **PARTLY CLOSED** | Independent evidence fields, compatibility valence and per-key P5c checks improve. But passing the actual production input `weights=[-0.8]` through `build_projection_class_context` gives **PROMISE=0**, activity **0.2176**, **λ=0**, and **zero windows**. The new “end-to-end” test hides this by supplying absolute promise weights. Separately, two distinct roots contributing 0.5 each yield evidence **0.75**, whereas C2 requires **1.0**. Evidence: `C/step06b_windows_projection.py:659`, `:870`, `:1158`, `:1160`, `:2109`; `S/services/gochara_kernel/legacy_semantics.py:291`, `:481`; `S/tests/l3/gochara/test_step06b_three_field_valence.py:58`. |
| **5. Actual L1 kakṣyā seam** | **PARTLY CLOSED** | The 24 producer-shaped facts now resolve to eight boundaries; sign-relative offsets and complete-grid retrograde selection work. But dropping conflicting `KAKSHYA_2` leaves indexes `[0,2,3,4,5,6,7]`; both consumers renumber that list. A direct crossing at **217.5°** is consequently labelled **Jupiter**, and can consume Jupiter’s bindu 1 instead of Mars’s bindu 0. The projection independently ignores direction: a retrograde crossing there requests **Mars**, although the entered cell belongs to **Jupiter**. Evidence: `S/services/gochara_v3/context.py:709`; `S/services/gochara_v3/engine.py:1652`, `:1666`; `S/services/gochara_grammar/primitives.py:883`, `:899`; `C/step06b_windows_projection.py:698`, `:932`, `:1517`. |
| **6. Tārā as P6 testimony** | **CLOSED** | I recomputed zero-based stars **24** and **20**, inclusive distance **24**, ninefold class **6**. The projection emits the day annotation and withholds it from era/month rows. With versus without natal-Moon testimony, my nonzero projection produced identical raw and signed intensities—**0.1024** on each tier. Shared-engine parity tests also pass with a nonzero λ fixture. Evidence: `C/step06b_windows_projection.py:824`, `:1412`; `S/services/gochara_v3/engine.py:857`, `:868`. |
| **7. Verifiable production backup/rollback** | **PARTLY CLOSED** | Unique names, plain `CREATE TABLE`, recorded count/digest and transactional pre/post checks repair stale-name reuse and unguarded deletion. Exact-preimage verification remains insufficient: the digest omits IDs/timestamps and has an ambiguous NULL encoding. The generator also accepts `(recorded_count=0, recorded_digest='empty')`, producing a block that permits deletion and an empty restore. Evidence: `C/resonance_rebuild_backup_sql.py:30`, `:36`, `:65`, `:85`, `:112`, `:115`. SQL was inspected/generated, not executed against PostgreSQL. |
| **8. Failing rehearsal and postconditions** | **PARTLY CLOSED** | Failed recorded checks now cause exit 1; positive controls, NULL/dangling-reference checks, counter semantics and rerun/rollback checks are improved. However, moving `afflicted` from **career_setback/10L** to **marriage/7L** preserves the count six and my in-memory mutation still returns **no acceptance failures**. The production R-5 query compares clean/split references against raw qualified/compound labels, so correct output cannot match. Evidence: `C/resonance_rebuild_disposable_rehearsal.py:184`, `:218`, `:534`, `:583`; `C/resonance_rebuild_R1_R6_runbook.md:202`. |

The daśā arithmetic independently supports the corrected O-PP-2 interpretation. Subdividing the pinned 17-year Mercury MD by Vimśottarī proportions reproduces the Mars→Rahu AD boundary at **2020-02-14T11:47:23Z** and both Saturn PD intervals, including the printed nearest-second boundary. Mars and Saturn occupy Libra, seventh from Aries; Rahu occupies Taurus, second from Aries and eighth from Mars.

## Steps 1–3

| Step | Result |
|---|---|
| **1. N5: separation at serving time** | **Still correct at the producer.** Write-time minimum separation remains zero. My rerun retained both peaks 30 days apart, producing two month/day families within one era. Evidence: `C/step06b_windows_projection.py:212`, `:1341`. The optional serving trim remains in `S/services/gochara_v3/resolution_hierarchy.py:508`; no live serving query was performed. |
| **2. N6: exclude birth_anchor** | **Still correct for rebuilt resonance maps.** Enumeration contains 26 classes and excludes `birth_anchor`; successful chart-partition replacement removes old map rows. It does not remove previously published windows. Evidence: `S/services/ka_gochara_resonance/writer.py:203`, `:220`, `:1278`, `:1322`. |
| **3. N7: honest mūrti flags** | **Still correct at the writer.** Computed rows yield `algorithmic_approximation`; uncomputed rows yield `unsourced`; both yield `corpus_verifiable=False`. Final-state stamping remains present. Evidence: `S/services/ka_moorti_nirnaya/logic.py:94`, `:102`; `S/services/ka_moorti_nirnaya/writer.py:440`. Existing rows require rebuilding. |

The resonance and mūrti implementations above are unchanged between the two review commits.

## ‘4.0’ impact

**I found no PR-owned automatic rewrite of published `4.0` contacts/windows or authority flip.** The projection retains its candidate-manifest check and published-generation refusal, including inside `write_windows()` (`C/step06b_windows_projection.py:1781`, `:2059`). The authority-based contact reader remains unchanged (`S/services/ka_gochara/service.py:320`, `:339`, `:478`).

The serving-visible changes are:

| Surface | Change and activation point |
|---|---|
| **Projected window geometry** | Angular aspect-point evaluation, episode support, alias reduction and cap-free peak retention change curves, active-contact attribution, peaks and resulting window families **when projection runs**. |
| **Projected permission** | Fresh context documents install nested MD/AD/PD evaluation, per-level licences and applicability; Sade-Sati and absent systems leave the scoring fraction. Effective **on projection using those documents**. Old documents without `_dasha_periods` still take the disclosed static fallback (`step06b:639`). |
| **Projected occurrence/valence** | Activity receives absolute weights; signed channels remain separate; served `valence`, `is_adverse` and signed intensity derive from the three-field outcome. Operand/root explanations enter `suppression_state`. Effective **on projection**, with the remaining PROMISE and C2 defects described above (`step06b:1158`, `:1427`, `:1495`). |
| **Projected vedha/P6 annotations** | Interval states replace the projection’s PG353 multiplier; absent/legacy coverage is disclosed; supplied attenuation is scoped by body; Moon-vedha and tārā annotations appear on day rows. Effective **on projection**. |
| **Shared v3/grammar evaluation** | Tārā becomes a non-scoring annotation; actual L1 kakṣyā boundaries, donor reads and directional qualification change subsequent evaluations and materializations. These functions are **not generation-gated** and take effect whenever the changed code is invoked. The shared vedha defect remains. |
| **Resonance map** | The intended rebuild applies R-1…R-6 refreshes and excludes `birth_anchor`. The map is **chart-scoped, not generation-scoped**; consumers can observe the replacement immediately after its transaction commits. |
| **Vedha overlay** | Rebuilding changes returned detail to interval relations, plural obstructors, cancellation segments, coverage/operator-role data and null PG353 grade fields. The retrieval tool returns this unversioned detail directly (`platform/src/lib/retrieval/registry/layers/L3_kala/query_vedha_gochara.ts:137`). |
| **Mūrti overlay** | Rebuilding changes provenance stamps without changing the computed grade. The current retrieval query still does not select those honesty stamps (`…/query_moorti_nirnaya.ts:99`). |
| **Admission/provenance metadata** | W44 tārā wiring status, five writer digests, the live L3 pin and census change **with deployment of the packaged metadata**, without waiting for a data rebuild. They do not establish rebuilt or accepted outputs. |

Therefore, the narrower claim that existing published rows are not automatically rewritten is supported by source inspection. **The blanket claim that no serving-visible change takes effect before the intended rebuild/projection is not supported:** packaged provenance changes immediately, and shared evaluators have no such activation boundary.

## Rebuild

The writer still constructs and validates its candidate before replacement, preserves the previous partition on missing class coverage, and leaves transaction ownership to the caller (`S/services/ka_gochara_resonance/writer.py:1276–1325`).

**The revised procedure can nevertheless report success falsely, and does not yet prove lossless rollback.**

1. **The rollback digest is not an exact-preimage certificate.**  
   It excludes `id` and `computed_at`. It also maps SQL NULL and literal `"<null>"` to identical bytes. I reproduced identical digest input for two different, schema-valid citation values. This is an encoding collision, independent of MD5’s cryptographic properties. Separate the intentionally ID-independent rerun digest from a typed, unambiguous full-row snapshot/restore check.

2. **Empty restore is accepted.**  
   `rollback_sql(..., 0, "empty")` generates equality checks that pass for an empty snapshot, followed by chart deletion, zero inserts and successful post-verification. There is no explicit nonempty refusal.

3. **Snapshot mismatch does not stop the rehearsal before its destructive phase.**  
   `matches_live_preimage` is recorded at `resonance_rebuild_disposable_rehearsal.py:483`, but execution proceeds to `_run_writer` at line 488 without asserting it.

4. **R-5 can falsely pass in rehearsal and falsely fail in production.**  
   The acceptance function checks only the qualifier count. My qualifier-transfer mutation passes. Conversely, the runbook compares four raw labels—including `2L/11L afflicted`—against six normalized rows such as `2L` and `11L`. Those sets cannot be equal on its own fixture.

5. **Disposable database identity is improved, but cluster isolation is not established.**  
   Creating a fresh, uniquely named database protects an existing database from the rehearsal’s table writes. However, the loopback check still allows a forwarded production endpoint to execute `CREATE DATABASE` if its credentials permit it (`resonance_rebuild_disposable_rehearsal.py:246`). The statement that a forwarded production port cannot satisfy the procedure is too strong.

The checked-in evidence reports synthetic-fixture **154→0**, rerun equality, rollback refusal, restore equality and foreign-partition preservation. I did **not** reproduce those PostgreSQL executions. Moreover, “restore equality” currently means equality under the incomplete digest above.

## Pins

**PASS for the requested pin invariants.**

My independent comparisons established:

- Exactly **one** new L3 history entry over protected baseline `1010659db391a9770b2af3f16adac0dfa71b02f5`.
- The archived protected pin equals the baseline pin.
- Its archived writer snapshot equals the baseline L3 inventory.
- Previous history, other layers and definition bindings remain unchanged.
- The changed writer set exactly matches the authorized five assets, and all five independently recomputed source-closure hashes match:

  `ka_gochara`, `ka_gochara_resonance`, `ka_gochara_v3_century_materialize`, `ka_moorti_nirnaya`, `ka_vedha_gochara`.

The live successor is **`l3:92c07a9051ab:5a9de6f7002d`**, superseding **`l3:f4c69a6d0cd4:829354703812`**, with source commit `92c07a9051abad73815933e3a5b98ffde37fa848`.

The checker passed with:

```text
--check --protected-baseline-commit 1010659db391a9770b2af3f16adac0dfa71b02f5 --delivery-topology
```

Evidence: `platform/src/generated/nirmana-analysis-layer-pins.json:1243`, `:1540`; `platform/src/generated/nirmana-writer-digests.json`.

This verifies provenance consistency, not closure of the scoring defects. I did not create a simulated squash.

## Regressions

The rework introduces or exposes these additional failures:

- **Kakṣyā conflict compaction changes cell identity.** Removing one conflicting boundary shifts subsequent enumeration indexes and can turn a zero-donor result into an applied bindu-1 result.
- **Permission boundaries move early.** `utc_iso_of_jd()` rounds to 10 ms (`step06b:406`). My probe at **2020-02-14T11:47:22.999Z**, one millisecond before the transition, selected **Rahu**, not Mars.
- **Disjoint coverage becomes false certainty.** The new vedha gate treats the minimum start and maximum end as coverage. Rows covering `[Jan 1, Feb 1)` and `[Apr 1, May 1)` returned **clear, factor 1.0** on March 1. The gap should remain unavailable (`step06b:1631`, `:1761`).
- **The negative-only regression test still bypasses the production defect.** Its helper converts signed promise weights to magnitudes, while the production caller does not.

The additional W44 test failure is **pre-existing**, as disclosed in the PR body: its assertion expects precisely ten unwired mechanisms, while the protected baseline already contains the additional entries and wired W30. I do not classify that failure as introduced here.

## Ranked merge-blocking amendments

1. **P1 — Make negative-only occurrence evidence survive the production construction path.**  
   Correct the PROMISE/activity integration at `step06b:870` and `:2109`. Test signed input through `main`’s constructor path without preprocessing it in a helper. Require nonzero λ and emitted adverse windows for the `−0.8` Saturn/Jupiter example:  
   `253.43° − 249.79° = 3.64° = 3°38′24″`; activity `0.8 × (1 − 3.64/5) = 0.2176`.

2. **P1 — Finish the frozen daśā read contract and C5 identity handling.**  
   Pin build/ayanāṃśa/tier before duplicate handling; retain `index`; reject conflicting `(level,parent,index)` rows; reject missing pin fields; canonicalize parent aliases after identical-duplicate collapse. Preserve the required C5 relation identity and exact half-open selection rather than advancing instants through rounding.

3. **P1 — Replace legacy vedha handling in every affected evaluator.**  
   Wire the interval evaluator into the shared v3 path as well as the projection. Preserve primary-contact and rule-version identity, cancellation, testimony, coverage and independence groups. Test actual writer payloads through both paths; the clean/expired/duplicate probes must cease returning `0.85/0.70/0.49`.

4. **P1 — Preserve kakṣyā identity and direction end to end.**  
   Carry actual boundary indexes through filtering; do not derive them from list positions. Carry the ledger’s direction into projection donor selection. Test incomplete/conflicting grids and retrograde crossings with competing donor values.

5. **P1 — Implement C2’s evidence reduction.**  
   Use per-path, per-channel **max across aliases of a root, then sum across distinct roots**. `legacy_semantics.compute_signed_channels_v3` still implements noisy-OR. Two distinct 0.5 contributions must yield evidence **1.0**; aliases must remain **0.5**.

6. **P1 — Make rollback verification certify the complete preimage.**  
   Use unambiguous typed serialization and a full-row restore comparison, separately from rerun-content comparison. Enforce the intended nonempty snapshot requirement and stop before destructive work when snapshot/live verification fails.

7. **P1 — Make acceptance verify identities and preserved values, not just totals.**  
   Compare exact normalized qualifier sets, verify expected source identities, and repair the runbook’s R-5 comparison. Add source-row mutations that move a qualifier or substitute a wrong input while preserving counts. Correct the disposable-endpoint claim and establish the intended rehearsal destination before cluster DDL.

## What I could not verify

The focused read-only Python runs produced **527 passed, 1 pre-existing failure, 3 skipped and 26 deselected**. The runs included touched tests, pin tests and adjacent W44/N16 checks. Python execution disabled bytecode/cache/log writes and used an audit guard against filesystem mutations and socket connections.

I could not verify:

- PostgreSQL execution of the rebuild, rollback, migration or disposable rehearsal.
- Live authority, deployed code, stored `4.0` rows, overlay contents or production counts.
- Database/file-writing integration cases.
- The TypeScript receipt test: this checkout has no `platform/node_modules`; dependencies were not installed.
- A newly constructed squash-delivery tree or a real serving query applying the optional 90-day trim.

No files were created or edited, no git write command or database connection was run, and neither prohibited directory was accessed.