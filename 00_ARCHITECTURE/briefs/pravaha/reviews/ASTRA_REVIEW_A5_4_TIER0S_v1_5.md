---
artifact: ASTRA_REVIEW_A5_4_TIER0S
version: "1.5"
reviewer: "Codex gpt-6-astra"
date: 2026-10-01
verdict: ACCEPT_WITH_AMENDMENTS
reviewed_commit: 1683f620a
authority: "Review only; authorizes nothing."
---

## Verdict

**ACCEPT_WITH_AMENDMENTS. All three round-5 amendments are CLOSED. No merge-blocking amendment remains.**

The requested fact-reference, mechanism-weight and forged-baseline counterexamples now fail or pass as intended. The L3 successor’s re-basing is correct. Earlier closures remain supported at source/test level.

One **P2 follow-up** remains: the native runbook overstates its resolution-state coverage. Its SQL accepts certain incorrect, enum-valid mechanism/M-6 states. The current writer handles these cases correctly, and the expanded rehearsal checks their seeded output; this is a bounded verification gap, not a demonstrated new producer defect.

Verified HEAD: `1683f620a87dc75d62cd83eeba48183d3b069778`.

Independent verification: **693 pytest passes, 23 skips**—687 passes across 25 sidecar test files, plus six A5.4 pin tests. Additional counterexamples ran in memory. **No PostgreSQL execution was performed.**

Path abbreviations:

- `S` = `platform/python-sidecar`
- `C` = `S/scripts/kala_gochara_cutover`
- `B` = `C/resonance_rebuild_backup_sql.py`
- `R` = `C/resonance_rebuild_disposable_rehearsal.py`
- `RB` = `C/resonance_rebuild_R1_R6_runbook.md`
- `W` = `S/services/ka_gochara_resonance/writer.py`

## Closure table

| Round-5 amendment | Status | Evidence and independent rerun |
|---|---|---|
| **1 — Resolve production TEXT fact references** | **CLOSED** | The detector now uses chart-scoped `NOT EXISTS`, without a UUID restriction. Executing its generated query verbatim in SQLite memory accepted both requested IDs, **`0ba04cc77e4f2bd9`** and **`795c47dd1b8acc07`**, when present for the chart: **zero violations**. Missing, foreign-chart-only, NULL and blank references each produced **one violation** in separate cases. The fixture now calls category-specific producer ID functions. **B:210; R:77–102, :484, :978; RB:229.** |
| **2 — Eliminate mechanism-weight self-comparison** | **CLOSED** | The mechanism weight is checked against the cited rule’s `rule_type`; every emitted type is enumerated, with unknown types rejected. For the actual writer’s `illness_acute / saturn:unfavourable:h8` row, replaying the generated weight predicate returned **zero violations at −1.0** and **one at +1.0**, with identity and provenance unchanged. Mechanisms and M-6 rows now participate in exact-tuple expectations; the sign-flip control is mandatory. The separate state-coverage qualification appears below. **B:285, :299, :504; R:408, :422, :454, :988.** |
| **P2 — Validate clean-baseline contents and control application** | **CLOSED** | A valid report returned `[]`. Replacing its clean baseline with `r1=[9,9]` and `value_violations=99` produced **two named failures**. Marking all 13 controls unapplied produced **13 failures**; removing all 13 produced **13 missing-control failures**. **R:450, :538, :558.** |
| **L3 pins re-basing** | **CLOSED / VALID** | Exactly one successor is admitted over `729dfe2c4`; archived predecessor data matches that baseline, and the successor’s source and digests have not moved. Independent regeneration and scoped checks pass as detailed below. |

Primary repair locations: [reference detector](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2769f/platform/python-sidecar/scripts/kala_gochara_cutover/resonance_rebuild_backup_sql.py:210), [mechanism-weight detector](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2769f/platform/python-sidecar/scripts/kala_gochara_cutover/resonance_rebuild_backup_sql.py:504), [baseline validation](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2769f/platform/python-sidecar/scripts/kala_gochara_cutover/resonance_rebuild_disposable_rehearsal.py:538).

These SQL counterexamples establish the relevant predicate behavior; they are **not PostgreSQL integration results**.

Earlier closures remain supported:

| Earlier closure | Reconfirmation |
|---|---|
| **Production-shaped schema and eligible class universe** | Migration-derived fixture schema, `TEXT[]` citations, canonical ayanāṃśa and the writer’s 26 eligible classes remain enforced. Retained `birth_anchor` does not become eligible. **R:166, :260, :577; B:274, :330.** |
| **Primary-contact identity and complete vedha testimony** | Tests retain the distinction between the **13:47 UTC** ledger identity and midnight projection identity. Unbound rows remain unresolved; bound identifiers survive. Obstructor, interval and root distinguish the Saturn and Mars testimony cases. **`S/services/ka_vedha_gochara/gate.py:133`, `:169`, `:342`; `test_vedha_interval_gate.py:644`, `:696`.** |
| **All-lord identities and afflicted qualifiers** | Both comparison directions and the wrong-token/missing-token controls remain. Counts alone cannot satisfy these checks. **B:239, :412; R:959.** |
| **Pin before canonicalization; recursive daśā collapse** | Canonicalization and boundary-selection tests pass, including duplicate ancestry and Mars/Rahu boundary behavior. **`C/step06a_class_context.py:427`; `S/services/gochara_grammar/dasha_data.py:124`; `test_step06b_per_instant_permission.py:809`, `:852`.** |
| **Negative-only construction, three-field valence and per-key qualification** | Production-constructor tests retain PROMISE **0.8**, activity **0.2176**, positive λ and adverse output. Per-key P5c qualification passes. **`test_step06b_three_field_valence.py:305`; `test_p5c_kakshya_donor_key.py`.** |
| **Angular evaluation, episode support and shared roots** | Aspect-point and episode-local tests pass. Independent `0.5` roots yield **1.0**; aliases yield **0.5**. **`test_step06b_angular_m1.py`; `test_step06b_three_field_valence.py:560`, `:575`.** |
| **Kakṣyā identity and direction** | Gap-preserving indices and direct/retrograde donor selection at **217.5°** pass. **`test_kakshya_l1_seam.py:244`, `:283`.** |
| **Persisted vedha states and bounded reachability** | Unavailable, clear and obstructed states remain distinguishable. Old breakdowns serialize as `not_recorded`. The 11-root AST scan and positive controls pass, with its dynamic-dispatch limitation unchanged. **`test_vedha_interval_gate.py:422`, `:443`, `:488`, `:588`; materializer `:1584`.** |
| **Tārā, N5, N6, N7 and adjacent materializers** | Testimony-only Tārā, separate nearby peaks, `birth_anchor` exclusion and honest mūrti provenance remain covered. Graded-suppression, lattā and all four selected materializer suites pass. **`test_step06b_tara_testimony.py:57`; `test_step06b_windows_projection.py:283`; W:197; `S/services/ka_moorti_nirnaya/logic.py:94`.** |
| **Full preimage, rollback refusal and required controls** | Typed full-row certificates, nonempty snapshots, verification before deletion, transactional restoration and separate pre/post-refusal certificates remain enforced. **B:119, :133; R:589, :1296.** |

Test filenames without prefixes above are under `S/tests/l3/gochara`, unless otherwise identified.

## Runbook

**I found no demonstrated new data-loss path or unconditional SQL/type error in the reviewed procedure. PostgreSQL execution remains unverified.**

The safeguards remain substantive:

- Snapshot creation refuses name reuse. The recorded snapshot must be nonempty and match the live preimage using every column, including IDs and timestamps. **RB:81, :92; B:98, :119.**
- The writer constructs its candidate before replacement and preserves prior rows when the required ontology is absent. Transaction ownership remains with the governed caller. **W:1247, :1287, :1313, :1322.**
- Rollback verifies snapshot existence, chart scope, positive count and full-row digest **before deletion**, then verifies restoration inside the transaction. **B:156, :163, :173, :179.**
- Rollback restores the prior map—including its prior defects—and calls for diagnosis; it is not rebuild acceptance. **RB:645.**

The §3 detector assessment is:

| Postcondition | Assessment |
|---|---|
| **R-1: positive, class-associated sensitive targets** | Positivity, positive-control counts and both identity directions can fail. Valid producer TEXT references now pass. **B:210, :347.** |
| **R-2: eligible arudha sign facts** | Chart-scoped references, both identity directions and sign-derived state checks exist. **B:393, :555.** |
| **R-3: eligible live yoga targets** | Canonical ayanāṃśa, live-firing predicates and both identity directions exist. The rehearsal also asserts the stopped-yoga note against its seeded expectation. **B:370; R:497; RB:575.** |
| **R-4: correct lord identities and resolution** | Both identity directions and the lord-resolution chain can fail. **B:412, :534.** |
| **R-5: afflicted qualifiers** | Both class/token comparison directions and per-row qualifier checks can fail. **B:239, :566.** |
| **R-6: valid stored state, references and nonempty partition** | Vocabulary, reference existence and nonempty checks can fail. Vocabulary validity alone does not establish state correctness. **RB:229, :242.** |
| **Retained weights, provenance and identities** | The mechanism self-comparison is removed; rule-derived mechanism checks, M-6 constants and unknown-type rejection are present. **B:299, :504, :518.** |
| **Every retained resolution state** | **Not fully established.** Mechanism and M-6 states retain the gap described below. |
| **Rerun equality** | Typed content hashing detects non-repeatability. A consistently incorrect value can reproduce the same digest. **RB:567.** |

Therefore, **not every blanket §3 assurance has a complete detector**. The native SQL can accept the incorrect states below; a repeatable defect producing them would also evade digest equality. This is not evidence that the current writer produces them.

## Pins

**The L3 successor and its re-basing pass this review.**

| Item | Verified value |
|---|---|
| Protected baseline | `729dfe2c4907610754be0a3c1cc244d6f54c9ba4` |
| Successor | `l3:a7fa8c25e1db:5d43541d2fa6` |
| Source | `a7fa8c25e1db78f01c2d33036b1a020501555704` |
| Predecessor | `l3:f4c69a6d0cd4:829354703812` |
| Inventory digest | `5d43541d2fa6aec2b29ca3d99cd0bdad1cefef73c0c9032b685ec2e1617bfca1` |

Independent comparisons confirmed:

- Exactly **one** L3 history append; prior history, archived pin and archived writer slice match the new baseline.
- Other layers’ pins, histories and writer slices, plus definition bindings, match that baseline.
- All **123 writer digests** and the probe digest regenerate exactly; rendered inventory bytes match.
- The changed L3 set remains exactly `ka_gochara`, `ka_gochara_resonance`, `ka_gochara_v3_century_materialize`, `ka_moorti_nirnaya`, and `ka_vedha_gochara`.
- Six A5.4 pin tests pass. Strict and delivery-topology checks on this checkout report **no L3 error**.

Evidence: [archived baseline](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2769f/platform/src/generated/nirmana-analysis-layer-pins.json:1243), [active successor](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2769f/platform/src/generated/nirmana-analysis-layer-pins.json:1568).

The overall pin checks still report three inherited L1/L2 errors. Running the comparison against the baseline produced the same errors; this PR does not worsen them. They remain outside this review’s scope.

## Regressions

The selected suites exposed **no new numerical or producer regression**. The reviewed production service/writer and step06a/step06b source has no delta from round 5; this round changes acceptance machinery, evidence and pin admission.

Earlier serving boundaries remain:

- Published-generation projection writes refuse before deletion: **`C/step06b_windows_projection.py:1808`, `:2089`.**
- Shared materializer production writes remain scoped to `3.0`: **`S/pipeline/orchestrator/writers/ka_gochara_v3_century_materialize.py:2285`.**
- Serving remains authority-based: **`S/services/ka_gochara/service.py:320`.**
- Existing stored rows are not automatically rewritten by serializer changes.

The following finding is a remaining acceptance-coverage weakness.

## Ranked amendments

**Merge-blocking: none.**

### 1. P2 follow-up — Qualify and complete native resolution-state verification

The runbook claims every retained state is independently checked:

[runbook:18](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2769f/platform/python-sidecar/scripts/kala_gochara_cutover/resonance_rebuild_R1_R6_runbook.md:18), [runbook:404](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2769f/platform/python-sidecar/scripts/kala_gochara_cutover/resonance_rebuild_R1_R6_runbook.md:404).

However:

- `mechanism_node` has weight, identity, eligibility and citation checks, but no expected-state check.
- M-6 state checking is explicitly limited to enum membership in the helper’s docstring; the native runbook does not carry that qualification.

Evidence: **B:456, :504, :534–576**.

My in-memory replay of the applicable generated predicates found:

| Mutation | Value violation | R-6 enum violation |
|---|---:|---:|
| Otherwise-valid mechanism: `resolved → unavailable` | None | 0 |
| M-6 row with missing Māndi: actual builder returns `unavailable`; forged stored state `resolved` | None | 0 |

These replays adapted PostgreSQL array/cast syntax for SQLite; they did not execute the full PostgreSQL query.

**Follow-up:** state the precise coverage limit in the native runbook, enforce the existing mechanism `resolved` contract, and add M-6 operand-presence/state controls. This does not require implementing the deferred M-4 audit or new doctrine.

This remains non-blocking because the current writer explicitly preserves mechanism resolution and derives M-6 missing-operand states correctly (**W:646, :1150**), while the rehearsal now includes their exact seeded tuples (**R:408–418**). The native SQL’s universal certification claim should nevertheless be corrected before relying on it.

## What I could not verify

- PostgreSQL execution of the migration-derived rehearsal, generated queries, mutation controls, rebuild or rollback. The author’s recorded disposable results were not independently reproduced.
- Production schema, deployment, authority, stored rows, concurrent operation or live served output.
- Full repository/TypeScript CI or a newly constructed squash-delivery tree.
- **23 skipped integration cases:** six step06a/step06b database/filesystem cases and 17 WP9 database cases.

Two subprocess tests initially encountered the review harness’s prohibition; both passed on targeted reruns with guarded child processes. Tests used disabled bytecode/cache writes and suppressed write-producing fixtures.

No file was created, edited, moved or deleted. No git write command or production-database connection was made. Neither prohibited directory was accessed.