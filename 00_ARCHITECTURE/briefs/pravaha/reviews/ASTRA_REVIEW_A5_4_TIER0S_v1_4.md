---
artifact: ASTRA_REVIEW_A5_4_TIER0S
version: "1.4"
reviewer: "Codex gpt-6-astra"
date: 2026-10-01
verdict: REJECT
reviewed_commit: cebb08323
authority: "Review only; authorizes nothing."
---

## Verdict

**REJECT — the requested repairs largely work, but the native acceptance procedure retains two substantive defects.**

It rejects valid producer-generated fact IDs, and its retained-value check can accept a mechanism-node weight whose sign has been reversed. These prevent closure of the production-rebuild acceptance claim. The identity/testimony repair, all-lord detector, required-control records, and scoped L3 successor pass this review.

Verified HEAD: `cebb083232be32ce16cc775601fe4a066cf705d3`. Main’s changes were treated as context.

Independent verification: **693 pytest passes, six skipped**—687 passes across 25 sidecar test files and six A5.4 pin tests. Two subprocess tests initially hit the review harness’s prohibition; targeted reruns with guarded child processes passed. Additional counterexamples ran in memory. **No PostgreSQL execution was performed.**

Path abbreviations below:

- `S` = `platform/python-sidecar`
- `C` = `S/scripts/kala_gochara_cutover`

## Closure table

These identifiers refer to the amendments in **v1.3**.

| Round-4 amendment | Status | Evidence and independent rerun |
|---|---|---|
| **1 — Production-faithful oracle and eligible class universe** | **PARTLY CLOSED** | The original defects are repaired: citations use `array_to_string` over migration 388’s `TEXT[]`; expected identities use the writer’s 26 classes. My citation-list replay produced the expected joined string, and the retained `birth_anchor` plus A1 fixture no longer produced `(birth_anchor, fact-a1)`. Schema construction now derives input-table DDL from migrations. However, the reference detector still requires UUID-shaped fact IDs, while actual producers emit 16-hex IDs; the fixture conceals this by generating UUIDs. See amendment 1 below. `C/resonance_rebuild_backup_sql.py:45`, `:274`, `:417`; `C/resonance_rebuild_disposable_rehearsal.py:238`, `:263`, `:653`. |
| **2 — Truthful primary-contact identity and complete testimony** | **CLOSED** | With ingress at **13:47 UTC**, the ledger and midnight hashes differed. The date-grain row persisted `identity_resolution="unresolved"` with null ledger identifiers; a supplied ledger identity survived unchanged. Saturn obstruction **January–June** versus Mars **January 15–March 1** now produced different persisted objects retaining obstructor, interval and root. Both testimony cases remained `clear`, with nullable testimony factor. `S/services/ka_vedha_gochara/gate.py:133`, `:169`, `:174`, `:342`; `S/tests/l3/gochara/test_vedha_interval_gate.py:644`, `:696`. |
| **3 — Native all-lord identity comparison** | **CLOSED** | Both EXCEPT directions are printed in the native runbook and executed by the rehearsal. My `marriage:7L → marriage:2L` replay preserved **51** lord rows but produced **one extra and one missing identity**. Deleting `marriage:7L` produced **zero extra, one missing**. Named wrong-token and missing-token controls exist and are required. `C/resonance_rebuild_backup_sql.py:356`; `C/resonance_rebuild_R1_R6_runbook.md:353`; `C/resonance_rebuild_disposable_rehearsal.py:858`. |
| **P2 — Require every named detector-control record** | **CLOSED** | Removing all mutation entries while retaining `clean` and `restored_after_controls=True` now returns **ten missing-control failures**, rather than `[]`. Unknown names and missing baseline records are also rejected. A separate baseline-content weakness remains a non-blocking follow-up. `C/resonance_rebuild_disposable_rehearsal.py:394`, `:465`; `S/tests/l3/test_resonance_rebuild_rehearsal.py:311`. |

Earlier closures remain supported **at source/test level**:

| Earlier closure | Reconfirmation |
|---|---|
| **Pin before canonicalization; recursively collapse daśā trees** | My shuffled replay again produced **31 inputs → 10 canonical rows**, excluded the foreign build, retained three source IDs per duplicate group, and left no orphan parents. Mars was selected **1 ms before** the boundary; Rahu at it. `C/step06a_class_context.py:427`; `S/services/gochara_grammar/dasha_data.py:124`; `test_step06b_per_instant_permission.py:809`, `:852`. |
| **Negative-only production construction and three-field valence** | Production-constructor tests pass with PROMISE **0.8**, activity **0.2176**, positive λ and adverse output. Per-key P5c operand qualification remains covered. `S/tests/l3/gochara/test_step06b_three_field_valence.py:305`. |
| **Angular evaluation, episode support and shared roots** | Angular/aspect-point, episode-local and alias-reduction tests pass. C2 still yields **1.0** for two independent `0.5` roots and **0.5** for aliases. `test_step06b_angular_m1.py`; `test_step06b_three_field_valence.py:560`, `:575`. |
| **Kakṣyā identity and direction** | Gap-preserving indices and direct/retrograde donor selection at **217.5°** pass. `S/tests/l3/gochara/test_kakshya_l1_seam.py:244`, `:283`. |
| **Persisted vedha states** | `unavailable/None`, `clear/1.0`, and `obstructed/None` remain distinguishable; old term breakdowns become `not_recorded` when serialized. `S/tests/l3/gochara/test_vedha_interval_gate.py:588`; `S/pipeline/orchestrator/writers/ka_gochara_v3_century_materialize.py:1584`. |
| **Adjacent graded-suppression and lattā tests** | Updated interval-state and annotation-only assertions pass. `S/services/gochara_v3/tests/test_graded_suppression.py:236`; `S/services/gochara_v3/mechanisms/tests/test_w31_latta_quality_gates.py:186`. |
| **Full preimage certificate and refusal evidence** | Typed full-row hashing, positive-count requirements, verification before deletion, transactional restoration, and distinct pre/post-refusal certificates remain. Mutation tests reject changed certificates. `C/resonance_rebuild_backup_sql.py:115`, `:129`; `C/resonance_rebuild_disposable_rehearsal.py:1146`. |
| **Bounded reachability evidence** | The 11-root AST scan and its positive controls pass. Its documented limitation concerning dynamic dispatch remains appropriate. `S/tests/l3/gochara/test_vedha_interval_gate.py:422`, `:443`, `:488`. |
| **Tārā, N5, N6 and N7** | Tārā remains testimony with unchanged intensity; nearby admitted peaks remain separate; the producer excludes `birth_anchor`; mūrti retains honest provenance states. Relevant suites pass. `test_step06b_tara_testimony.py:57`, `:73`; `test_step06b_windows_projection.py:283`; `S/services/ka_gochara_resonance/writer.py:197`; `S/services/ka_moorti_nirnaya/logic.py:94`. |

## Runbook

**The rollback safeguards remain substantive.** The procedure requires a unique, nonempty snapshot whose full-row certificate matches the live preimage. The writer constructs the candidate before replacement and leaves transaction ownership with the orchestrator. Restore verifies the snapshot before deletion and verifies the restored partition inside the same transaction. I found no demonstrated empty/stale-snapshot deletion bypass.

Evidence: `C/resonance_rebuild_R1_R6_runbook.md:81`, `:92`, `:144`, `:508`; `C/resonance_rebuild_backup_sql.py:139`, `:152`, `:163`, `:175`; `S/services/ka_gochara_resonance/writer.py:1257`, `:1289`, `:1314`.

**The acceptance procedure still cannot establish the complete claim it makes.**

| §3 postcondition | Detector assessment |
|---|---|
| **R-1: positive-only, class-associated sensitive facts** | Positivity and bidirectional identity checks can fail. The separate reference check incorrectly rejects valid 16-hex IDs. |
| **R-2: eligible sign-fact arudha identities** | Bidirectional identity and sign-resolution checks exist. The same reference-format defect rejects valid arudha facts. |
| **R-3: eligible live yoga identities** | Both identity directions, canonical ayanāṃśa and firing predicates are present. The writer computes dropped IDs from prior versus current sets; the rehearsal tests a known stopped yoga. |
| **R-4: correct lord identities and resolution** | Both all-lord identity directions and resolution-state checks exist. The former wrong-token bypass is closed. |
| **R-5: afflicted qualifiers** | Bidirectional class/token comparisons detect missing, extra and transferred qualifiers. |
| **R-6: valid states, references and nonempty output** | State vocabulary and nonempty checks can fail. Reference validity is measured against an incorrect UUID restriction. |
| **Retained values** | **Incomplete.** For `mechanism_node`, weight falls through to comparison against itself. The rehearsal’s exact-tuple comparison excludes this type. |
| **Rerun equality** | Detects non-repeatability; a consistently wrong weight can reproduce the same digest. |

Thus, the answer to “is every §3 claim backed by an adequate detector?” is **no**. Existing detectors cover many meaningful predicates, but do not support the blanket retained-value assurance.

The two new findings below concern acceptance correctness. They do not demonstrate a destructive rollback failure.

## Pins

**The scoped L3 successor passes.**

- Successor: `l3:a7fa8c25e1db:5d43541d2fa6`.
- Source: `a7fa8c25e1db78f01c2d33036b1a020501555704`.
- Predecessor: `l3:f4c69a6d0cd4:829354703812`.
- Exactly **one** history entry was appended over protected baseline `678ca1776a62d0e4c58e623931bd279ebed10ff4`; prior history, archived pin and archived writer slice match that baseline.
- Definition bindings and other layers’ pins/history are unchanged.
- All **123 writer digests**, including the probe digest, match independent regeneration.
- All **six A5.4 pin tests pass**. Strict and delivery-topology checks on this checkout report **no L3 error**.

The exact changed L3 set remains:

`ka_gochara`, `ka_gochara_resonance`, `ka_gochara_v3_century_materialize`, `ka_moorti_nirnaya`, `ka_vedha_gochara`.

Evidence: `platform/src/generated/nirmana-analysis-layer-pins.json:1243`, `:1568`; `platform/scripts/__tests__/test_nirmana_analysis_layer_pins.py:1805`.

The reported L1/L2 errors remain out of scope: their pin/history records and writer slices are unchanged against the protected baseline. I did not construct a new squash-delivery commit.

## Regressions

The selected suites exposed **no new numerical regression**. The outstanding findings are newly identified weaknesses in the PR’s acceptance surfaces, not evidence that the round-5 identity repair changed scoring incorrectly.

The prior serving-boundary conclusions also hold:

- Projection writes still refuse published generations before deletion: `C/step06b_windows_projection.py:1808`, `:2089`.
- The shared materializer’s production writes remain scoped to `3.0`: `S/pipeline/orchestrator/writers/ka_gochara_v3_century_materialize.py:2285`.
- Serving remains authority-based: `S/services/ka_gochara/service.py:320`.
- Existing stored rows are not automatically rewritten. `not_recorded` applies when an old breakdown passes through the new serializer: materializer `:1590`.

## Ranked amendments

### Merge-blocking

**1. P1 — Validate fact references as production `TEXT` identities, not UUIDs.**

The native query counts every non-UUID `sensitive_degree` or `arudha` reference as dangling, even when the referenced fact exists for the same chart:

[resonance_rebuild_backup_sql.py:210](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2769e/platform/python-sidecar/scripts/kala_gochara_cutover/resonance_rebuild_backup_sql.py:210).

Both actual producers generate **16-character hexadecimal fact IDs**:

- [ga_sensitive_writer.py:230](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2769e/platform/python-sidecar/ga_writers/ga_sensitive_writer.py:230)
- [ga_structural_writer.py:759](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2769e/platform/python-sidecar/ga_writers/ga_structural_writer.py:759)

My replay used those producer functions and the actual resonance row builders:

| Valid fixture row | Producer-generated ID | Resolution | Runbook classification |
|---|---|---|---|
| Positive Venus pushkara fact | `0ba04cc77e4f2bd9` | `resolved` | Dangling |
| A7 sign fact | `795c47dd1b8acc07` | `resolved` | Dangling |

Both facts were present for the chart, yet the printed predicate counted **2 violations**.

The migration-derived schema does not expose this because the fixture still assigns `uuid.uuid4()` to every fact: [resonance_rebuild_disposable_rehearsal.py:653](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2769e/platform/python-sidecar/scripts/kala_gochara_cutover/resonance_rebuild_disposable_rehearsal.py:653).

**Required repair:** resolve fact-backed target types using chart-scoped `NOT EXISTS` against the actual text identity. Seed producer-shaped IDs and demonstrate that existing IDs pass while missing and foreign-chart IDs fail. Regenerate the native block. No L1 identity change is needed.

**2. P1 — Remove the retained-weight detector’s self-comparison.**

For types absent from `EXPECTED_WEIGHTS`, the predicate becomes `m.weight <> m.weight`. `mechanism_node` is absent:

[resonance_rebuild_backup_sql.py:269](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2769e/platform/python-sidecar/scripts/kala_gochara_cutover/resonance_rebuild_backup_sql.py:269), [resonance_rebuild_backup_sql.py:427](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2769e/platform/python-sidecar/scripts/kala_gochara_cutover/resonance_rebuild_backup_sql.py:427).

I constructed the actual writer’s `illness_acute / mechanism_node / saturn:unfavourable:h8` row, then changed only its weight:

**`−1.0 → +1.0`**

The source-rule ID, citation, resolution, qualifier, identity and counts remained unchanged. Replay of the applicable printed predicates produced **zero value violations**. R-1 through R-5 do not select this type, and the rehearsal’s exact-tuple check excludes it:

`C/resonance_rebuild_disposable_rehearsal.py:372`.

The writer explicitly defines this adverse weight as `−1.0`: `S/services/ka_gochara_resonance/writer.py:317`, `:462`. Repeatability cannot detect a writer that consistently emits the incorrect sign.

**Required repair:** check mechanism weights against the referenced rule’s type and declared weight contract; require a sign-flip control in the rehearsal. Account explicitly for other emitted types that currently fall through before claiming that every retained value is checked. This requires validating existing behavior, not implementing deferred mechanisms.

### Separate follow-up

**P2 — Validate the recorded clean baseline’s contents.**

`verify_acceptance()` requires the `clean` key but skips its contents. Replacing it with a baseline reporting `r1=[9,9]` and `value_violations=99` still returned **`[]`**.

Evidence: `C/resonance_rebuild_disposable_rehearsal.py:471`.

Require a complete zero-violation baseline and explicit mutation application for every control. This is non-blocking because the current execution path separately measures the clean map; the report-validation weakness alone does not demonstrate a current-run bypass.

## What I could not verify

- PostgreSQL execution of the migration-derived rehearsal, native queries, mutation controls, rebuild or rollback. SQL findings above are source-backed, in-memory predicate replays.
- Production schema/data, deployment, current authority, stored `4.0` rows or live serving output.
- Full repository/TypeScript CI or a newly constructed squash-delivery tree.
- Six integration tests requiring database or filesystem writes: the two `step06a` integration cases and four `step06b` integration cases identified in round 4.

Tests ran with bytecode/cache writes disabled, write-producing fixtures suppressed, and filesystem/database guards. No file was created, edited, moved or deleted; no git write command or database connection was executed. Neither prohibited directory was accessed.

