---
artifact: ASTRA_REVIEW_A5_4_TIER0S
version: "1.0"
reviewer: "Codex gpt-6-astra"
date: 2026-09-30
verdict: REJECT
reviewed_commit: "6dd8f9149"
authority: "Review only; authorizes nothing."
---

**Verdict: REJECT**

The change set does not complete the ten repairs to the frozen contract. Several helpers are correct in isolation, but the projection still uses the old permission and vedha scoring paths. The angular replacement introduces incorrect aspect scoring and cross-episode double counting. The rebuild procedure also needs correction before production use.

Reviewed `git diff origin/main...HEAD`, with merge base `16e3725cee360ec003f6bf5e85b1f5524fc9b4f8`. No repository files were changed, no git write commands were run, and no database connections were made. The two prohibited directories were not accessed.

Below, `S/` means `platform/python-sidecar/`. Code line numbers refer to the reviewed head.

**Per-step review**

| Step | Assessment | Evidence |
|---|---|---|
| 1. `serve_time_90d` — N5 | **Producer repair correct.** Write-time separation becomes zero; the regression retains both peaks 30 days apart. The existing serving trim remains optional. An actual query applying that trim was not demonstrated. | `S/scripts/kala_gochara_cutover/step06b_windows_projection.py:178,784`; `S/tests/l3/gochara/test_step06b_windows_projection.py:268`; `S/services/gochara_v3/resolution_hierarchy.py:508` |
| 2. `birth_anchor_excluded` — N6 | **Correct for the rebuilt resonance-map path.** Enumeration contains 26 classes, excludes `birth_anchor`, and a successful chart-partition replacement removes its old map rows. This does not remove already published windows. | `S/services/ka_gochara_resonance/writer.py:197,220,1278,1322`; `S/tests/l3/test_ka_gochara_resonance.py`, `test_writer_emits_zero_birth_anchor_rows` |
| 3. `moorti_flag_honest` — N7 | **Writer flag repair correct.** Computation no longer implies corpus verification: computed rows are `algorithmic_approximation`, and `corpus_verifiable` is always false. Existing rows require rebuilding. | `S/services/ka_moorti_nirnaya/logic.py:94,102`; `S/services/ka_moorti_nirnaya/writer.py:379,440` |
| 4. `tara_key` — #5 | **Partial; contract failure remains.** The canonical `MOON` lookup is fixed. The projection still supplies `None, None`, while the shared v3 engine now activates a numerical multiplier forbidden for P6 testimony. | `S/services/gochara_v3/mechanisms/w23_tara_bala.py:217`; `S/scripts/kala_gochara_cutover/step06b_windows_projection.py:534`; `S/services/gochara_v3/engine.py:852,887` |
| 5. `kakshya_key` — #19 | **Incomplete.** The donor-key helper is added, but the original L1 boundary-key mismatch remains in both readers. Correct `KAKSHYA_1…8` input still produces no fetched boundaries. | `S/services/gochara_grammar/primitives.py:659,676`; `S/services/gochara_v3/context.py:704`; actual producer: `S/ga_writers/ga_strength_writer.py:1137` |
| 6. `per_instant_permission` — #2/#3 | **Not repaired on the executable projection path.** `main()` never installs the new permission function. The function also caches by date, and its underlying evaluator does not implement C5’s nested, per-level licences. | `S/scripts/kala_gochara_cutover/step06b_windows_projection.py:374,519,1385`; `S/services/gochara_intensity/permission.py:191`; `S/services/gochara_grammar/dasha_data.py:90,123` |
| 7. `three_field_valence` — #11/#12 | **Partial annotation, incomplete evaluation repair.** Independent evidence fields exist, but negative-only occurrence evidence still produces zero activity and no windows. Missing donor data globally disqualifies unrelated outcomes. Legacy netted fields remain the served compatibility fields. | `S/scripts/kala_gochara_cutover/step06b_windows_projection.py:627,641,855`; `S/services/gochara_kernel/legacy_semantics.py:378`; `S/scripts/kala_gochara_cutover/step06a_class_context.py:109` |
| 8. `angular_m1` — N1 | **Incorrect integration.** Angular distance ignores `aspect_deg` and does not restrict contributions to the contact’s episode. Exact aspects score zero; separate passes contribute simultaneously. | `S/scripts/kala_gochara_cutover/step06b_windows_projection.py:610,617,930`; ledger representation: `S/scripts/kala_gochara_cutover/step06_enumerate_episodes.py:584,589` |
| 9. `vedha_interval_relation` — #16/#17/#25 | **Helpers improved; scoring repair incomplete.** Interval clipping, cancellation carving and exceptions are represented, but the projection still invokes the legacy whole-row multiplier. Coverage, interval states, independence groups and testimony roles are ignored there. | `S/services/ka_vedha_gochara/logic.py:371,408,448`; `S/services/ka_vedha_gochara/writer.py:458`; `S/scripts/kala_gochara_cutover/step06b_windows_projection.py:1006` |
| 10. `resonance_rebuild_R1_R6` — #9 | **Writer tests credible; operational deliverable not ready.** The synthetic rehearsal reports 154 → 0, but its verification block does not enforce its results. Backup reuse, incomplete postconditions and an incorrect required counter make the production runbook unsafe/inconsistent. | `S/scripts/kala_gochara_cutover/resonance_rebuild_disposable_rehearsal.py:318,350`; `S/scripts/kala_gochara_cutover/resonance_rebuild_R1_R6_runbook.md:45,90,136,150` |

**Tests and independent arithmetic**

Tests used `python3 -B -m pytest -q -p no:cacheprovider`, with `PYTHONDONTWRITEBYTECODE=1`, plugin autoload disabled, `--noconftest` and `-s`. These additions avoid bytecode, cache/capture files and the root autouse fixture’s temporary-directory creation (`S/conftest.py:37–46`). Database/file-writing integration cases were deselected.

| Execution | Result |
|---|---:|
| Safe selection from 14 touched Python test files | **277 passed, 25 deselected** |
| R-1…R-6 suite cited by the rehearsal, including existing correction/derived-target tests | **203 passed**; overlaps the preceding selection |
| A5.4-specific pins tests | **6 passed, 78 deselected** |
| Pins `--check --delivery-topology` against protected baseline `16e3725…` | **Passed** |

All mutations below were performed **in memory**, without editing files:

| Mutation | Result |
|---|---|
| Make the real per-instant permission factory raise whenever called | **All 12 permission tests still pass.** Production-factory coverage is missing. |
| Replace angular decay with constant `1.0` | **5 failures, 2 passes.** The scalar kernel has useful coverage. |
| Admit `not_gandanta` as positive | **4 failures, 23 passes.** Reproduces the reported R-1 sensitivity. |
| Remove `target_resolution_state` from `_base_row` | **14 failures, 52 passes.** Reproduces the reported R-6 sensitivity. |

Independent calculations and executable probes:

- **Aspects:** `body = (target − angle) mod 360`. Saturn’s third aspect: target 100°, body 40°. Mars’s fourth: target 100°, body 10°. Jupiter’s ninth: target 100.31°, body 220.31°. All three exact-contact probes returned **activity 0**, rather than 1.
- **Separate episodes:** two weight-0.5 conjunction records, 100 days apart, both contribute at the first episode: activity **0.75**, rather than 0.5.
- **Bereavement:** 253.43° − 249.79° = **3.64° = 3°38′24″**; both positions are Sagittarius, ninth from Aries. A negative-only probe produced `evidence_for_occurrence=0.8`, outcome `adverse`, but **activity 0, λ 0, zero windows**.
- **Tārā:** natal Moon 327.06° gives zero-based nakṣatra 24. Transit index 20 gives inclusive count **24**, ninefold position **6, Sādhana**.
- **Kakṣyā:** 30°/8 = **3.75°**. Cell two is **[3.75°, 7.5°), Jupiter**. Supplying all 24 actual L1 boundary facts to the context reader returned **zero boundaries**.
- **Vedha:** from Aquarius, Venus 12→6 corresponds to **Capricorn→Cancer**; 11→3 corresponds to **Sagittarius→Aries**. Sun–Saturn and Moon–Mercury exceptions remain symmetric. With actual new writer payloads, a clean row still yielded **0.85**; an obstruction ending March 1 still yielded **0.70 on April 1**; duplicate identical roots yielded **0.49**.
- **Frozen O-SM arithmetic:** the supplied parabola yields angular activities **[0.8, 0.5, 0.4, 0.5, 0.8]**, not the temporal triangle.

**‘4.0’ serving impact**

I found no new automatic rewrite of published `4.0` contacts/windows. The projection checks the candidate manifest and refuses published generations, including inside `write_windows()` (`step06b_windows_projection.py:1298,1020`). The authority-based contact reader is unchanged (`S/services/ka_gochara/service.py:320,339`).

However, the changes are **not all isolated from shared serving paths**:

| Surface | Serving-visible change |
|---|---|
| Shared v3 evaluation | The tārā key repair activates the existing default-enabled multiplier, potentially changing λ by factors **0.70–1.20** on subsequent evaluations/materializations. This is outside the resonance rebuild itself. |
| Grammar/kakṣyā | The grammar path adds donor details and contributor queries. The v3 qualification changes when `_KAKSHYA_BINDU_INTERIM_ENABLED` is enabled; its default remains false. |
| Shared vedha overlay | On an overlay rebuild, returned JSON changes from singular obstruction/cancellation fields to `vedha_intervals`, plural obstructors, coverage and operator-role data. PG353 grade fields become null, partial cancellation no longer sets whole-row cancellation, and the formula version changes to v1.1. The unversioned retrieval tool returns this `detail` directly (`platform/src/lib/retrieval/registry/layers/L3_kala/query_vedha_gochara.ts:137`). |
| Shared mūrti overlay | On rebuild, provenance stamps change without changing the computed grade. The current retrieval query does **not** select those honesty stamps, so that endpoint does not disclose the repair (`…/query_moorti_nirnaya.ts:99`). |
| Shared resonance map | The intended rebuild removes negative sensitive targets, refreshes R-1…R-6 states and excludes `birth_anchor`. This table is chart-scoped, not isolated by published generation. |
| Future candidate windows | Peak retention, angular curves, contact attribution and nested three-field metadata change. Permission and vedha scoring remain legacy because of the wiring failures. |
| Generated provenance | The active L3 pin and five writer digests change immediately as packaged metadata. This does not establish rebuilt rows or accepted scoring behavior. |

Thus, unchanged published window rows are plausible from source inspection; unchanged behavior across every shared evaluator/overlay is not.

**Rebuild runbook and rehearsal**

The writer’s transaction ownership and complete-candidate-before-delete structure are sound: the caller owns commit, and missing class coverage preserves the previous partition (`S/services/ka_gochara_resonance/writer.py:1276–1325`).

The operational proof has four defects:

1. **The backup can be stale.** `CREATE TABLE IF NOT EXISTS … AS SELECT` silently reuses an existing backup. Rollback then deletes the current partition and inserts whatever that table contains. There is no snapshot freshness, completeness or chart-count assertion before deletion.
2. **The required counter is wrong.** The runbook requires `negative_dropped_zero_rows = 154` at lines 136–138. That counter counts per-class exclusions; the rehearsal itself reports **735**, while its pre-rebuild map contained 154 negative targets (`evidence/resonance_rebuild_R1_R6_evidence.md:85`).
3. **Postqueries can pass incomplete output.** The R-1 inner join omits dangling references; SQL `NOT IN` does not reject null values. Empty output satisfies several zero-count/equality checks. R-4/R-5 merely record states/qualifiers without checking expected resolution or preservation.
4. **The rehearsal does not fail on failed verification.** It prints the `ver` dictionary and returns zero. Its loopback/non-5433 guard also does not establish that the destination is disposable; another local database or forwarded production port passes.

The reported **154 → 0 is a synthetic-fixture result**, supported by meaningful writer tests and matching mutation failures. I could not independently reproduce the database result under this review’s no-DB constraint. The checked-in evidence does not prove production cleanup, idempotent rerun, or rollback restoration.

**Pins**

**Pass for the requested admission invariants.**

I independently compared the committed inventories and rederived all five changed writer source-closure hashes. Every hash matches its committed value. The exact delta equals `changed_assets`:

- `ka_gochara`
- `ka_gochara_resonance`
- `ka_gochara_v3_century_materialize`
- `ka_moorti_nirnaya`
- `ka_vedha_gochara`

The archived protected pin and writer snapshot equal the baseline; previous history, other layers and definition bindings are preserved. Evidence: `platform/src/generated/nirmana-analysis-layer-pins.json:1243,1540`.

The successor is `l3:454dab04134d:be13d85ab725`, superseding `l3:f4c69a6d0cd4:829354703812`. The delivery-mode checker passes. I did not create a simulated squash because that would require prohibited git/filesystem writes.

**Ranked merge-blocking amendments**

1. **P1 — Correct the angular kernel’s integration.**  
   [The evaluation loop](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2769/platform/python-sidecar/scripts/kala_gochara_cutover/step06b_windows_projection.py:610) must preserve aspect angle and episode identity/support. Fetch `aspect_deg`, apply the frozen directional geometry, restrict contributions to their valid intervals, and prevent repeated physical roots/passes from multiplying current activity. Add exact Saturn/Mars aspect and separated retrograde-pass regressions. Current conjunction-only kernel tests cannot establish this.

2. **P1 — Implement and wire frozen C5 permission.**  
   [The constructor call in `main()`](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2769/platform/python-sidecar/scripts/kala_gochara_cutover/step06b_windows_projection.py:1385) never receives `permission_fn`. Fixing that alone is insufficient: remove date-only memoization; enforce the pinned build, parent linkage and `(level,parent,index)` conflict rule; return per-level lord/row/licence/relation/applicability; exclude inapplicable systems and Sade-Sati scoring. Probes currently accept an orphan PD and retain conflicting starts for the same period identity. For O-PP-2, Mars AD is scored, Rahu AD testimony, Saturn PD scored at both instants; **class-level licence remains the same**. The exact boundary belongs to Rahu.

3. **P1 — Make vedha intervals control the actual scoring path.**  
   [The projection gate](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2769/platform/python-sidecar/scripts/kala_gochara_cutover/step06b_windows_projection.py:1000) still calls `legacy_semantics.compute_quality_gates`; the shared v3 gate has the same legacy behavior. Consume scoped interval states, cancellation segments, coverage and independence groups. Remove generalized PG353 numerical attenuation from evaluators, not just writer metadata. Supply primary-contact/rule provenance, and restrict Moon vedha to covered P6 day windows with testimony-only behavior. Test actual writer payloads through the evaluator.

4. **P1 — Complete three-field evaluation and operand scoping.**  
   [Activity still clamps negative weights to zero](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2769/platform/python-sidecar/services/gochara_kernel/legacy_semantics.py:378), preventing adverse occurrence evidence from producing a window. The new test explicitly adds a positive contact to bypass this (`test_step06b_three_field_valence.py:233`). Add a negative-only end-to-end regression and ensure consumers use the three independent fields. Scope missing contributor data to **P5c**, as D-SPECS C4 requires; the chart-wide `LIMIT 1` probe must neither disqualify unrelated paths nor resolve every operand from one unrelated row.

5. **P1 — Repair the actual L1 kakṣyā boundary seam.**  
   [The context parser](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2769/platform/python-sidecar/services/gochara_v3/context.py:704) expects `planet.index`; L1 writes `KAKSHYA_n`. Fix both readers and test actual producer-shaped rows in a non-Aries sign. Preserve sign-relative offsets and correct cell selection for retrograde crossings. Contributor reads also need an explicit ayanāṃśa/build selection or conflict policy: currently duplicate identities from different input sets can be selected by row order.

6. **P1 — Restore tārā as P6 testimony, without promoting it into scoring.**  
   [The corrected key](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2769/platform/python-sidecar/services/gochara_v3/mechanisms/w23_tara_bala.py:217) activates a multiplier through `engine.py:887`, contradicting frozen §0/S-04 and O-P6-TARA. Meanwhile the projection still omits the tārā input. Produce the correct annotation on the intended path and require identical scores with/without that testimony. The updated engine-parity tests presently assert the prohibited weighting.

7. **P1 — Make production backup and rollback verifiable.**  
   [The backup/restore procedure](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2769/platform/python-sidecar/scripts/kala_gochara_cutover/resonance_rebuild_R1_R6_runbook.md:45) needs a uniquely identified snapshot, recorded chart/count/content verification, and refusal to delete when that snapshot is absent, stale or incomplete. Rehearse restoring the exact preimage and preserving another chart’s partition.

8. **P1 — Turn rehearsal and postconditions into failing acceptance checks.**  
   [The verification block](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2769/platform/python-sidecar/scripts/kala_gochara_cutover/resonance_rebuild_disposable_rehearsal.py:318) must return failure for violated R-1…R-6 invariants. Correct the 154-versus-counter confusion; detect null/dangling/wrong-input references; assert nonempty positive controls, expected states and qualifier preservation; verify rerun and rollback. Establish disposable database identity before any DDL/DML, rather than relying on a port exclusion.

**What I could not verify**

- Live `4.0` authority, stored rows, deployed binaries, overlay contents or production count 154.
- The disposable database’s reported results, migration application and transaction/restore behavior.
- Database/file-writing integration tests, the full reported 421/84 suite, and TypeScript receipt tests.
- A fresh simulated-squash delivery check.
- A real serving query applying the optional 90-day trim.

These limits do not affect the reproduced scoring failures or the source-level merge blockers above.