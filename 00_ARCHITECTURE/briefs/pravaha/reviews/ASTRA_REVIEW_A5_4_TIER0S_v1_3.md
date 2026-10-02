---
artifact: ASTRA_REVIEW_A5_4_TIER0S
version: "1.3"
reviewer: "Codex gpt-6-astra"
date: 2026-10-01
verdict: REJECT
reviewed_commit: 558d2ebea
authority: "Review only; authorizes nothing."
---

## Verdict

**REJECT — round-3 P1-1 is closed; P1-2 and P1-3 remain partly closed.**

The daśā repair passes the former counterexamples. Vedha states now survive serialization, but the new primary-contact identity does not match the ledger identity, and Moon testimony loses its obstruction evidence. The production rebuild checks also disagree with the checked-in schema and event-class universe, while remaining weaker than the disposable rehearsal’s identity checks.

Verified HEAD: `558d2ebeaf4961ea9473819d734e36db18c86002`. I reviewed the requested author rework, treating the main merge as context.

Independent completed pytest runs: **526 passed, 6 skipped**—520 passes across 20 sidecar files, plus six A5.4 pin tests. Additional counterexamples ran in memory. No PostgreSQL execution was performed.

Path abbreviations:

- `S` = `platform/python-sidecar`
- `C` = `platform/python-sidecar/scripts/kala_gochara_cutover`

## Closure table

These identifiers refer to the amendments and follow-ups in **v1.2**.

| Round-3 amendment | Status | Evidence and independent rerun |
|---|---|---|
| **P1-1 — Pin before canonicalization; recursively collapse MD/AD/PD trees** | **CLOSED** | The loader called by `main()` selects the contract from raw rows, then fetches the pinned build before canonicalization. Parents are normalized before deduplicating each subsequent level. My shuffled counterexample contained three copies of the complete tree plus one overlapping foreign-build row: **31 inputs → 10 canonical rows**, all duplicate groups retained three source IDs, no orphan parents, foreign row excluded. Mars remained selected **1 ms before** the AD boundary; Rahu at the boundary. `C/step06a_class_context.py:265`, `:427`; `S/services/gochara_grammar/dasha_data.py:124`. |
| **P1-2 — Preserve vedha state and identity through persisted output** | **PARTLY CLOSED** | The engine-to-materializer JSON rerun now produces three distinct objects: `unavailable/None`, `clear/1.0`, `obstructed/None`, while retaining product `value=1.0`. Coverage and rule version survive; old term breakdowns serialize as `not_recorded`. However, primary-contact identity is reconstructed from a midnight date rather than the ledger ingress, and testimony serialization drops fired obstruction intervals. See amendment 2. `S/services/gochara_v3/engine.py:726`, `:982`; `S/pipeline/orchestrator/writers/ka_gochara_v3_century_materialize.py:1584`; `S/services/ka_vedha_gochara/gate.py:145`, `:319`. |
| **P1-3 — Class-associated identities and retained-value acceptance** | **PARTLY CLOSED** | My former class-swap and **0.5 → 0.125** mutations now fail the pure acceptance function. R-1/R-2/R-3 include event class, canonical ayanāṃśa and both EXCEPT directions. Seven SQL mutation controls are implemented. However, the production value query uses the wrong citation type, expected sets include excluded `birth_anchor`, and native verification omits the rehearsal’s all-lord identity comparison. See amendments 1 and 3. `C/resonance_rebuild_backup_sql.py:254`, `:284`, `:364`; `C/resonance_rebuild_disposable_rehearsal.py:299`, `:623`, `:859`. |
| **(a) — Rewrite 12 stale adjacent tests** | **CLOSED** | The previously failing graded-suppression and latta cases pass within the rerun suites. They now assert interval state and annotation-only behavior. `S/services/gochara_v3/tests/test_graded_suppression.py:236`, `:326`, `:354`; `S/services/gochara_v3/mechanisms/tests/test_w31_latta_quality_gates.py:186`, `:216`, `:252`. |
| **(b) — Replace refusal tautology with recorded certificates** | **CLOSED at source/test level** | Separate full certificates are recorded before and after refusal; foreign-chart preservation also compares full certificates. My changed post-refusal certificate produces an acceptance failure. Database execution remains unverified. `C/resonance_rebuild_disposable_rehearsal.py:779`, `:933`, `:938`, `:949`. |
| **(c) — Bound and strengthen reachability evidence** | **CLOSED** | The AST scan now covers 11 named package roots, checks references and imports, documents dynamic-dispatch limitations, and positively finds the shared evaluator’s callers and aliased imports. Relevant tests pass. This supports the bounded static claim, not universal runtime unreachability. `S/tests/l3/gochara/test_vedha_interval_gate.py:422`, `:443`, `:459`, `:488`. |

Earlier closures remain supported:

| Earlier closure | Reconfirmation |
|---|---|
| **Negative-only production construction** | Still closed. Production-constructor tests retain PROMISE **0.8**, activity **0.2176**, positive λ and adverse output for signed weight `-0.8`. `S/tests/l3/gochara/test_step06b_three_field_valence.py:305`. |
| **Angular evaluation** | Still closed. Shortest-arc and angular-decay tests pass, including the 3.64° separation case. `C/step06b_windows_projection.py:296`; `S/tests/l3/gochara/test_step06b_three_field_valence.py:320`. |
| **Kakṣyā identity and direction** | Still closed. Gap-preserving indices and direct/retrograde selection at **217.5°** pass. `S/tests/l3/gochara/test_kakshya_l1_seam.py:244`, `:283`. |
| **C2 reduction** | Still closed. Two independent `0.5` roots yield **1.0**; aliases retain the maximum **0.5**. `S/tests/l3/gochara/test_step06b_three_field_valence.py:560`, `:575`. |
| **Full preimage certificate** | Still closed at source level. Typed full-row hashing, positive-count requirements, pre-delete verification and transactional restore verification remain. `C/resonance_rebuild_backup_sql.py:102`, `:126`, `:139`, `:156`. |
| **Tārā testimony and N5 peak separation** | Still hold. Stars **25/21 → count 24 → class 6**; day-only testimony leaves intensities unchanged. Two admitted peaks 30 days apart remain separate families. `S/tests/l3/gochara/test_step06b_tara_testimony.py:57`, `:73`; `test_step06b_windows_projection.py:283`. |
| **N6 and N7** | The producer still enumerates **26 classes excluding `birth_anchor`**. Mūrti remains `algorithmic_approximation` or `unsourced`, with `corpus_verifiable=False`. The new acceptance SQL contradicts N6; the producer closure itself holds. `S/services/ka_gochara_resonance/writer.py:197`, `:220`; `S/services/ka_moorti_nirnaya/logic.py:94`, `:102`; `writer.py:441`. |

## ‘4.0’ impact

**I found no author-owned automatic rewrite of published `4.0` rows or authority flip.**

- Projection writes still refuse published generations before deletion; the serving reader remains authority-based. `C/step06b_windows_projection.py:1808`, `:2089`; `S/services/ka_gochara/service.py:320`, `:339`.
- The shared materializer’s production writes remain scoped to generation **`3.0`**. Adding its new suppression metadata does not backfill existing `4.0` rows. `S/pipeline/orchestrator/writers/ka_gochara_v3_century_materialize.py:2285`.
- **“Pre-§5 rows become `not_recorded`” applies when an old term breakdown passes through the new serializer.** Already stored rows are not rewritten or normalized by this change. `:1590`.
- The projection retains its existing `suppression_state.quality_gates_detail` shape, now including the fetched `formula_version`. The shared materializer adds `term_breakdown.vedha_gate` and structured suppression fields. These are distinct representations. `C/step06b_windows_projection.py:1619`, `:1718`.
- MCP retrieval passes these JSON fields through; it does not repair their evidence or synthesize missing historical state. `platform-mcp/src/tools/retrieval/register_gochara_windows.ts:2490`, `:2533`.

The new metadata therefore has serving significance when newly computed rows are served. Its incorrect identity and incomplete testimony can reach consumers. The shared evaluator is not generation-gated, and rebuilding the unversioned resonance map or overlays affects subsequent consumers independently of a window-generation label.

## Rebuild

**The inspected rollback safeguards remain substantive.** A nonempty snapshot must match the live full-row certificate before rebuilding. Restore checks precede deletion, and restoration plus verification share one transaction. I did not demonstrate an empty/stale-snapshot route that erases the partition.

**The native acceptance procedure is not ready.** As written, its retained-value query cannot execute against the declared citation column type. Its identity queries can reject a correct N6-compliant rebuild. Independently, the intended checks cannot distinguish certain incorrect retained identities.

Under `CLAUDE.md:346` and `:369`, the §3 claims have these detector limits:

| §3 claim | Detector assessment |
|---|---|
| R-1 positive-only sensitive facts | Positivity checks and class-associated comparisons exist and can fail. Expected identities use an overbroad event-class universe. |
| R-2 eligible arudha identities | Both comparisons exist, but include `birth_anchor` expectations that the writer must never emit. |
| R-3 eligible live yogas | The missing reverse comparison is repaired and ayanāṃśa is pinned. The same event-class-universe defect remains. |
| R-4 correct lord output | Aggregate resolution and per-present-row state checks exist. They do **not** establish that the correct non-afflicted lord tokens survived for each class. |
| R-5 afflicted qualifiers | Bidirectional `(event_class, token)` comparisons now detect missing, extra and transferred afflicted qualifiers. |
| R-6 valid states/references/nonempty partition | These checks can fail their stated narrow predicates. They do not prove full identity completeness. |
| Retained values | The new query contains meaningful checks, but its citation expression is incompatible with the checked-in schema. |
| Rerun equality | Measures repeatability only. Identical incorrect output can reproduce its digest. |

The disposable rehearsal is stronger than the native runbook: it compares all lord identities and exact tuples at `C/resonance_rebuild_disposable_rehearsal.py:859` and `:869`. Those protections are not all present in the printed native procedure.

The seven rolled-back SQL controls are implemented, but their reported database execution is **author evidence**, not independently reproduced evidence from this review.

## Pins

**The requested L3 successor passes the scoped review.**

- Successor: `l3:de07494333a7:395a24c4ec7c`.
- Source: `de07494333a770192dd8d8a47cc2aae91f31be79`.
- Predecessor: `l3:f4c69a6d0cd4:829354703812`.
- Exactly one history entry is appended; the archived pin and writer slice equal protected main `d4feada9ba01a1d871aa876657ab1cb05ce1e792`.
- Membership and definition bindings are unchanged.
- All **123** writer digests match the derived inventory.
- All **six A5.4 pin tests pass**.

The exact changed L3 set remains `ka_gochara`, `ka_gochara_resonance`, `ka_gochara_v3_century_materialize`, `ka_moorti_nirnaya`, and `ka_vedha_gochara`.

Strict and delivery-topology checks report inherited L1/L2 errors and **no L3 error**. Other layers’ pins/history and the L1/L2 writer slices are unchanged against protected main. These inherited errors are out of scope and are not rejection grounds.

## Regressions

The selected suites expose no remaining obsolete-contract failures or new numerical regression. The outstanding repair defects concern:

- Production-schema and class-universe mismatch in the new acceptance SQL.
- Fabricated primary-contact identity and lossy testimony serialization.
- Unequal acceptance strength between the rehearsal and native runbook.

The producer’s `birth_anchor` exclusion remains correct; the new detector must conform to it.

## Ranked amendments

### Merge-blocking

1. **P1 — Make the rebuild oracle faithful to the production schema and eligible class universe.**

   The value query calls `jsonb_array_elements_text(o.citations)`, but migration 388 declares **`citations TEXT[]`**. The rehearsal masks this by declaring **`citations JSONB`** and inserting JSONB values.

   Evidence: [resonance_rebuild_backup_sql.py:364](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2769d/platform/python-sidecar/scripts/kala_gochara_cutover/resonance_rebuild_backup_sql.py:364); `platform/supabase/migrations/388_brahma_ghatana_ontology.sql:23`; `C/resonance_rebuild_disposable_rehearsal.py:131`, `:476`.

   Separately, `_class_houses_cte()` reads every ontology class. Migration 456 retains `birth_anchor` with house `1` and kāraka `Sun`, while the writer excludes it. My in-memory replay with that actual signature and an A1 fact produces the spurious missing pair **`(birth_anchor, fact-a1)`**.

   Evidence: `C/resonance_rebuild_backup_sql.py:254`, `:293`; `platform/supabase/migrations/456_brahma_event_ontology_dr13_shapes.sql:249`; `S/services/ka_gochara_resonance/writer.py:197`.

   Use the declared citation type and the writer’s exact eligible class set. Rehearse against faithful schema and ontology fixtures, including the retained `birth_anchor` record.

2. **P1 — Preserve truthful primary-contact identity and complete testimony evidence.**

   The new identity hashes the overlay’s date at midnight. The ledger hashes the actual ingress instant. In my non-midnight ingress probe, the ledger produced **`sha256:04886a…`**, while the persisted identity produced **`sha256:92cbf5…`**.

   Evidence: [gate.py:145](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2769d/platform/python-sidecar/services/ka_vedha_gochara/gate.py:145); `C/step06_enumerate_episodes.py:633`; `S/services/gochara_kernel/ids.py:99`.

   Carry a source-bound contact identity where available; otherwise disclose that it is unresolved. A reconstructed date-grain identifier must not be presented as the ledger contact identity. This does not require inventing occurrence ordinals or expanding Tier 0-S into the deferred identity implementation.

   The serializer also drops testimony’s `fired` intervals. I supplied the same Moon residence with **Saturn obstruction January–June** versus **Mars obstruction January 15–March 1**. The evaluator annotations differed, but the persisted suppression objects were **identical**. Preserve the obstructor, interval and root evidence through serialization. `S/services/ka_vedha_gochara/gate.py:233`, `:319`.

3. **P1 — Put the all-lord identity detector into the native runbook.**

   My source-predicate replay replaced **`marriage:7L` with `marriage:2L`**, preserving weight, resolution, citation and qualifier. Results remained:

   - **51** resolved lord rows.
   - The same **six** afflicted identities.
   - Identical counts and global reference sets.
   - **Zero** retained-value violations.

   Yet the required `marriage:7L` was missing. R-1/R-2/R-3 do not examine lord rows, and R-5 only compares afflicted ones. This is an in-memory evaluation of the printed predicates, not a PostgreSQL run.

   Evidence: [resonance_rebuild_R1_R6_runbook.md:319](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2769d/platform/python-sidecar/scripts/kala_gochara_cutover/resonance_rebuild_R1_R6_runbook.md:319), `:324`, `:381`; compare `C/resonance_rebuild_disposable_rehearsal.py:859`.

   Add both directions of the eligible `(event_class, lord token)` comparison to native verification, with missing-token and valid-but-wrong-token controls.

### Separate follow-up

- **P2 — Require all seven named detector-control records.** Removing all seven mutation entries while retaining `clean` and `restored_after_controls=True` makes `verify_acceptance()` return **`[]`**. The current execution path supplies the seven entries, so this is a guard weakness rather than an independently demonstrated current-run bypass. Require their exact presence before accepting the report. `C/resonance_rebuild_disposable_rehearsal.py:321`.

## What I could not verify

- PostgreSQL execution of the snapshot, acceptance queries, seven mutation controls, rebuild or rollback.
- Live schema/data, deployed code, current authority, stored `4.0` rows or actual serving output.
- The full repository/TypeScript CI suite or a newly constructed squash-delivery tree.

Six database/file-writing integration tests were skipped:

| File under `S/tests/l3/gochara/` | Skipped tests |
|---|---|
| `test_step06a_class_context.py` | `test_producer_wires_from_real_permission_and_feeds_writer`; `test_no_candidate_contacts_exit_3` |
| `test_step06b_windows_projection.py` | `test_windows_gate_red_then_green_and_hierarchy`; `test_stale_overlay_refused_exit_7`; `test_published_generation_refused_exit_6`; `test_no_candidate_manifest_exit_3` |

Tests ran with bytecode/cache writes disabled, write-producing autouse fixtures suppressed, and database/filesystem guards. The two CLI production-refusal cases passed in separate guarded subprocess reruns.

No files were created, edited, moved or deleted; no git write command or database connection was run. Neither prohibited directory was accessed.