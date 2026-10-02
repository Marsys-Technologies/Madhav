---
artifact: ASTRA_REVIEW_A2_KERNEL_GEOMETRY
version: "1.0"
status: COMPLETED_INDEPENDENT_READ_ONLY_REVIEW
reviewer: "Codex gpt-6-astra"
date: "2026-09-30"
verdict: REJECT
reviewed_commit: 95e765c3c
authority: "Review only; authorizes nothing."
---

**Verdict: REJECT**

The directed-aspect correction is correct. The interior seam crossings and grid sizes also work. However, A2.1 does not completely repair residence geometry, truncated contacts, physical identity, or the global boundary substrate. Independent counterexamples reproduce missing contacts, missing residence intervals, lost ingress instants, and duplicate physical events despite passing new tests.

Confirmed checkout: `pravaha/a2-kernel-geometry`, full SHA `95e765c3c829f382690fe8c951ccb1b05623b33c`. The specified diff contains **9 files, +620/−68**. All nine working files matched their reviewed commit blobs. No files were written, no database connections were made, and neither prohibited directory was accessed.

**Per-step review**

| Step | Commit | Correct and complete? | Evidence |
|---|---|---|---|
| 1. `aspect_direction` | `3d77a1326` | **Yes**, for finding #13 / §6.2 invariant 6 | [contacts.py:211](/Users/Dev/madhav-l3/pravaha-a/platform/python-sidecar/services/gochara_kernel/contacts.py:211) correctly computes `target − angle`. Independent arithmetic and executable probes give Mars 4th → **270°**, Mars 8th → **150°**, Saturn 3rd → **300°**, Saturn 10th → **90° Cancer** for target 0°. Jupiter’s 5th/9th roots are 240°/120°; the universal 7th remains 180°; nodes return no dṛṣṭi roots. |
| 2. `zero_degree_seam` | `faebf5d83` | **Partial; introduces an endpoint regression** | [contacts.py:276](/Users/Dev/madhav-l3/pravaha-a/platform/python-sidecar/services/gochara_kernel/contacts.py:276) correctly supplies 12/27/96 boundaries, including 0°. Interior direct and retrograde crossings pass. But [arcs.py:154](/Users/Dev/madhav-l3/pravaha-a/platform/python-sidecar/services/gochara_kernel/arcs.py:154) universally represents zero as 360°, losing valid roots at certain index endpoints. See R6. |
| 3. `no_fabricated_ingress` | `823a412d9` | **Partial; production-path geometry is incorrect** | [episodes.py:448](/Users/Dev/madhav-l3/pravaha-a/platform/python-sidecar/services/gochara_kernel/episodes.py:448) searches both boundaries, and line 516 removes the fabricated exact timestamp. However, the refined-root/spline-time join at line 495 rejects real ingresses; upper-boundary entries still carry lower-boundary longitude metadata at lines 513–514. See R2. |
| 4. `truncated_contacts_kept` | `b772523d4` | **Partial; violates §6.1 identity and misses another N3 case** | [enumeration:670](/Users/Dev/madhav-l3/pravaha-a/platform/python-sidecar/scripts/kala_gochara_cutover/step06_enumerate_episodes.py:670) retains already-generated no-exact episodes; migration 1152 permits persistence. But [ids.py:61](/Users/Dev/madhav-l3/pravaha-a/platform/python-sidecar/services/gochara_kernel/ids.py:61) implements the forbidden rounded-time, role-qualified identity. Episodes are still absent when no exact root exists anywhere in the fitted knots. See R1/R4. |
| 5. `residence_spans_persisted` | `40e7d1cf4` | **Partial; emitted intervals are incomplete** | [enumeration:594](/Users/Dev/madhav-l3/pravaha-a/platform/python-sidecar/scripts/kala_gochara_cutover/step06_enumerate_episodes.py:594) emits real interval-shaped rows with dwell, and line 730 retains them. But the helper loses repeated revolutions, both-edge truncation is erased, and existing consumers do not correctly retrieve/use the new rows. See R2–R4/R7. |
| 6. `global_boundary_table` | `59a1d625d` | **No, as an implementation of the complete invariant/oracle** | [enumeration:684](/Users/Dev/madhav-l3/pravaha-a/platform/python-sidecar/scripts/kala_gochara_cutover/step06_enumerate_episodes.py:684) caches three solves per body, but line 712 still emits every event per point target. Dedupe preserves distinct role-qualified IDs. Interval targets independently re-solve sign boundaries through [episodes.py:450](/Users/Dev/madhav-l3/pravaha-a/platform/python-sidecar/services/gochara_kernel/episodes.py:450). See R5. |
| 7. `regression_suite` | `95e765c3c` | **Accurate index of tests; incomplete acceptance evidence** | [test index:15](/Users/Dev/madhav-l3/pravaha-a/platform/python-sidecar/tests/l3/gochara/test_wp3a_kernel.py:15) names the tests, but they do not establish physical storage uniqueness, partition-stable identity, normal-tolerance residence correctness, or O-SS-4. Two claimed protections have surviving mutations, detailed below. |

**Tests: can each fail?**

The safe subset of the two requested files produced **49 passed, 8 deselected**. All new tests ran.

The unmodified command would violate the review constraints: the outer autouse fixture creates a directory, and several tests connect to and rebuild a disposable database. I therefore disabled bytecode, cache and logging output, used `--confcutdir=tests/l3/gochara`, deselected database/file-fixture tests, and installed an in-memory audit hook rejecting writes and connections.

Mutations below were applied **only in process memory**.

| New or modified test | Mutation exercised | Result and limitation |
|---|---|---|
| `test_oad_aspect_direction` — all six parameter cases | Replace `target − angle` with `target + angle` | **Fails in all six cases.** Meaningful independent positive and negative roots. |
| `test_oad_levels_computed_as_target_minus_angle` | Mirror the directed levels | **Fails.** Also preserves the 180° invariant. |
| `test_oss2_case1_direct_crossing_aries_ingress` | Remove zero from boundary grids | **Fails.** Does not cover index-endpoint roots. |
| `test_oss2_case2_retrograde_pisces_reentry_upper_boundary` | Remove zero from boundary grids | **Fails.** Tests the interior boundary root. |
| `test_oss1_boundary_counts_one_revolution` | Remove the seam | **Fails.** Tests root counts, not stored-event uniqueness. |
| `test_oss_grids_include_zero_exactly_once` | Remove zero | **Fails.** Meaningful grid membership/count assertion. |
| `test_n2_retrograde_upper_boundary_entry_found` | Remove the upper seam root from the residence search | **Fails.** But replacing returned `level_deg` and `target_deg` with **123° still passes**. |
| `test_n3_clipped_span_never_fabricates_ingress` | Assign the clipped entry to `t_exact` and set `exact_crossing=True` | **Fails.** Does not test normal-tolerance refinement or persisted both-edge clipping. |
| `test_contact_id_no_exact_t_in_fallback` | Remove the distinction between fallback and exact identity payloads | **Fails.** But adding a field that changes **every historical hash still passes**. It does not verify legacy byte equality or the required identity contract. |
| `test_boundary_events_solved_once_per_body` | Repeat boundary solving per point target | **Fails.** It neither runs dedupe nor asserts one stored row per physical event; interval-target re-solving is invisible to it. |
| Modified `test_orb_regime_return_gating_and_boundary_attachment` | Mirror aspect direction | **Fails**, through the missing expected dṛṣṭi row. |
| Modified `test_interval_target_residence_and_agent_restriction` | Drop residence rows | **Fails.** Its single-pass, tight-tolerance fixture misses the real residence failures. |
| Renamed `test_truncated_contacts_kept_and_counted` | Drop no-exact producer rows | **Fails.** Its exact root exists in the larger fitted knot window, so it misses R4. |

The identity test’s “same value as pre-change” assertion compares the **current function with itself**, with and without an optional argument: [test_wp3a_kernel.py:948](/Users/Dev/madhav-l3/pravaha-a/platform/python-sidecar/tests/l3/gochara/test_wp3a_kernel.py:948). This is not a detector for historical compatibility under §N.8.

Separately, I compared the current implementation against the actual `origin/main` implementation in memory: **27 unchanged-input exact-contact cases had identical IDs**. That establishes bounded compatibility independently of the defective assertion.

Oracle disposition:

- **O-AD-1…4:** satisfied.
- **O-SS-1:** Swiss/Lahiri Sun counts for 2025 independently reproduced **12/27/96**; its storage-uniqueness requirement fails.
- **O-SS-2:** the specified interior cases pass; endpoint regression remains.
- **O-SS-3:** incomplete retention, identity and truncation coverage.
- **O-SS-4:** Moon remains excluded from `PERSISTED_BODIES`, but this diff adds no complete on-demand/coverage/non-materialization proof.
- **O-RX-1:** not implemented by the current identity algorithm.

The database fixture still applies only migrations 1081 and 1087, omitting 1152: [test_step06_enumeration.py:599](/Users/Dev/madhav-l3/pravaha-a/platform/python-sidecar/tests/l3/gochara/test_step06_enumeration.py:599). It cannot validate the new nullable persistence contract as written.

**Migration**

[1152_kala_gochara_contacts_t_exact_nullable_truncated.sql:33](/Users/Dev/madhav-l3/pravaha-a/platform/migrations/1152_kala_gochara_contacts_t_exact_nullable_truncated.sql:33) is narrowly scoped DDL: it drops `t_exact`’s `NOT NULL` and adds/validates `exact_crossing = (t_exact IS NOT NULL)`. It contains no row updates, deletions or identity rewrites.

The Boolean consistency check is sound because `exact_crossing` is already non-null. Exact rows must retain a timestamp; no-exact rows must lack one. Existing publication, foreign-key and completeness guards are unchanged. However, this check does **not** establish that missing exactness represents genuine truncation, nor preserve the missing truncation information identified below.

Material qualifications:

- **It affects published '4.0' rows too.** The “candidate '4.x' generations only” comment is not an SQL restriction. The assertion that all existing rows satisfy the new check remains unverified.
- **Numbering:** scanning both migration directories across **1,115 local remote-tracking references / 1,109 distinct heads** found 1152 only on this reviewed branch. No local collision was found. This does not verify newly changed remote state or the reservation authority independently.
- **Validation cost:** `NOT VALID` is immediately followed by validation in the same migration transaction. This is not a separately staged validation operation; production scan and blocking costs are unmeasured.
- **Replay:** the tracked runner skips applied migrations, but the SQL itself is not replay-idempotent: the second `ADD CONSTRAINT` would encounter the existing name.
- **Reversibility:** no rollback is supplied. Restoring `NOT NULL` after legitimate null rows have been written requires an explicit preservation strategy; deleting those rows would recreate N3.
- The comments claiming that fallback-time identity satisfies §6.1 are incorrect and must be corrected with the implementation.

Before application, the release procedure needs a data preflight for the new check, bounded lock handling, post-application constraint verification, and a stated rollback/preservation procedure. This review does not authorize application.

**Regressions and incomplete repairs**

**R1 — High: identity changes when a truncated contact becomes exact.**

The frozen [§6.1 contract](/Users/Dev/madhav-l3/pravaha/00_ARCHITECTURE/briefs/pravaha/design/GOCHARA_DESIGN_SPECS_v1_4.md:615) requires a label-independent physical tuple, a domain-stable occurrence ordinal, and the same contact ID when a later partition reveals its centre.

Instead, [ids.py:61–81](/Users/Dev/madhav-l3/pravaha-a/platform/python-sidecar/services/gochara_kernel/ids.py:61) hashes `target_kind`, fact/ref identity and minute-rounded time. No physical-object identity or occurrence ordinal is supplied.

Reproduced:

- Truncated contact → revealed exact centre: **different ID**.
- Same physical contact through two role aliases: **different IDs**.
- Two distinct exact instants within one minute: **same ID**.
- Two partitions within one continuous clipped residence: **different IDs**.

The existing exact-ID serialization is preserved for unchanged inputs, but that is not compliance with the new identity contract. Convention identity also remains the old vector, without the required occurrence domain; candidate `method_version` remains `1.0.0`. No correction/supersedes mapping is introduced.

**R2 — High: real ingresses become null through an invalid time join; retrograde metadata remains wrong.**

Residence entry `ca` is solved from the spline, then matched against a Swiss-refined root within **`1e-6` day = 0.0864 seconds**: [episodes.py:457–495](/Users/Dev/madhav-l3/pravaha-a/platform/python-sidecar/services/gochara_kernel/episodes.py:457).

That threshold is incompatible with the ordinary angular stopping tolerance.

Reproductions:

- Synthetic `λ(t) = 200° + 0.137°·day`, span `[210°,240°]`, one-arcsecond index tolerance and exact analytic refinement: the entry estimates differ by **53.2155 seconds**. The returned ingress has `t_exact=None`, no truncation flag, and `completeness_state='applied'`.
- With checksum-verified Swiss files and ordinary defaults, **all 12 returned Sun residence spans for 2025 had null ingress timestamps**, although their ingresses were inside the horizon.

This changes the previous fallback into false missing-exactness.

Additionally, a retrograde path entering `[0°,30°]` through **30°** returns ingress `level_deg=target_deg=0°`: [episodes.py:513](/Users/Dev/madhav-l3/pravaha-a/platform/python-sidecar/services/gochara_kernel/episodes.py:513). That also corrupts the boundary’s independence-group identity.

**R3 — High: residence enumeration loses repeated revolutions.**

[episodes.py:459–482](/Users/Dev/madhav-l3/pravaha-a/platform/python-sidecar/services/gochara_kernel/episodes.py:459) chooses one 360° band from the midpoint of an entire station-bounded segment. A direct segment can span many revolutions.

Independent line fixture, `λ(t)=t°`, horizon days `[0,1000]`, residence `[30°,60°]`:

- Required: **[30,60], [390,420], [750,780]**.
- Returned: **[390,420] only**.

Checksum-verified Swiss Sun, 2025–2035:

- Independently solved Taurus ingresses: **10**.
- Returned Taurus residence spans: **1**.

The helper defect predates this branch, but step 5 now persists its incomplete result as the repaired interval substrate. It therefore blocks the claimed T0-3 completion.

**R4 — High: N3 still becomes absence, and both-edge clipping loses disclosure.**

[episodes.py:263–270](/Users/Dev/madhav-l3/pravaha-a/platform/python-sidecar/services/gochara_kernel/episodes.py:263) constructs the levels to examine exclusively from already-found exact roots. If none exists in the fitted knots, no in-orb interval is considered.

For `λ(t)=196°+0.01°·day`, target 200°, orb 5°, and a 30-day horizon, the body is inside the orb throughout. The driver returns **zero conjunctions**, counts zero no-exact episodes, and reports the relation searched. The real driver’s padding is only one day: [enumeration:1134](/Users/Dev/madhav-l3/pravaha-a/platform/python-sidecar/scripts/kala_gochara_cutover/step06_enumerate_episodes.py:1134).

Separately, a residence clipped at both horizon edges persists as:

```text
relation=residence
t_exact=NULL
truncated_at_horizon=NULL
completeness_state=applied
dwell_days=30
```

The new [residence serializer:603](/Users/Dev/madhav-l3/pravaha-a/platform/python-sidecar/scripts/kala_gochara_cutover/step06_enumerate_episodes.py:603) deliberately erases `"both"`. No replacement `coverage.truncated=true` is stored. Null exactness cannot substitute for truncation coverage.

**R5 — High: the global boundary table remains duplicated physical output.**

The cache improves repeated point-target solving, but it does not implement [O-SS-1’s “each event stored once” requirement](/Users/Dev/madhav-l3/pravaha/00_ARCHITECTURE/briefs/pravaha/design/GOCHARA_TEST_ORACLES_v1_4.json:260).

Using the new test’s three-target fixture, then running the real `dedupe_episodes`:

```text
boundary rows before dedupe: 84
boundary rows after dedupe:  84
distinct physical groups:   28
```

Different target references/types produce different contact IDs, so the deduper at [enumeration:809](/Users/Dev/madhav-l3/pravaha-a/platform/python-sidecar/scripts/kala_gochara_cutover/step06_enumerate_episodes.py:809) does not collapse them.

Three interval targets additionally caused **six boundary-root solves**: the three cached grids plus three independent sign-grid solves. Memory and persisted row volume remain proportional to targets × boundary events, and interval-target refinement remains repeated.

**R6 — Medium: the seam fix removes previously working endpoint point contacts.**

The unconditional zero-to-360 mapping excludes an arc occupying `[0°,1°]`.

Direct comparison with the baseline implementation:

- Direct path beginning exactly at 0°: baseline finds the conjunction at day 0; reviewed code finds none.
- Retrograde path ending exactly at 0°: baseline finds it at day 10; reviewed code finds none.

This affects conjunctions/returns and aspects whose effective level is zero, through [contacts.py:252](/Users/Dev/madhav-l3/pravaha-a/platform/python-sidecar/services/gochara_kernel/contacts.py:252), as well as boundary roots. It contradicts the helper’s closed-endpoint contract. Ownership must prevent duplicate interior roots without discarding valid domain endpoints.

**R7 — High integration risk: consumers still treat the new objects as old exact-centred contacts.**

The concrete receiving paths require compatibility work or an enforced gate:

- [ka_gochara/service.py:60](/Users/Dev/madhav-l3/pravaha-a/platform/python-sidecar/services/ka_gochara/service.py:60) omits `residence` from default episode relations.
- Its [ledger query:456](/Users/Dev/madhav-l3/pravaha-a/platform/python-sidecar/services/ka_gochara/service.py:456) selects by `t_exact`, excluding all new null-exact rows and residences overlapping a query after their ingress.
- The existing [projection:216](/Users/Dev/madhav-l3/pravaha-a/platform/python-sidecar/scripts/kala_gochara_cutover/step06b_windows_projection.py:216) gives null-exact contacts zero contribution. Exact residence rows enter the generic time-decay calculation instead of retaining residence-state semantics.
- The MCP [row mapper:220](/Users/Dev/madhav-l3/pravaha-a/platform-mcp/src/tools/retrieval/register_gochara_contact_ledger.ts:220) converts null to the string `"null"`; its [pagination:348](/Users/Dev/madhav-l3/pravaha-a/platform-mcp/src/tools/retrieval/register_gochara_contact_ledger.ts:348) assumes a non-null exact timestamp.

For the siblings, current Kṣetra code pins window generation/calibration and a resonance-map digest at [writer.py:2319](/Users/Dev/madhav-l3/pravaha-a/platform/python-sidecar/services/ka_kshetra/writer.py:2319); this diff supplies no contact-correction invalidation proof. Saṅgam still has the independently documented symmetric `find_aspects` path at [engine.py:464](/Users/Dev/madhav-l3/pravaha-a/platform/python-sidecar/services/ka_sangam/engine.py:464). These are existing receiving limitations, not newly introduced implementations. The [family coordination contract](/Users/Dev/madhav-l3/pravaha/00_ARCHITECTURE/briefs/pravaha/design/L3_FAMILY_COORDINATION_v1_0.md:68) explicitly requires lineage propagation. This patch does not justify lifting the S-2 gate.

On the positive side, no frozen orchestrator file changes. The existing [published-generation refusal and scoped delete/insert](/Users/Dev/madhav-l3/pravaha-a/platform/python-sidecar/services/gochara_kernel/ledger.py:384) remain intact. Migration 1152 does not itself rewrite already-published '4.0' IDs.

**Ranked amendments required before merge**

1. **Implement §6.1 identity with an explicit compatibility boundary.** Preserve published '4.0' records/IDs; introduce physical identities, domain-stable occurrence ordinals, truncated-to-exact enrichment and correction lineage without repurposing historical IDs.
2. **Repair residence construction.** Enumerate every intersected revolution; use coherent refined boundary events for entry/exit; retain the actual upper-boundary longitude. Remove the sub-second join between differently refined timestamps.
3. **Complete truncated-contact retention and coverage.** Search in-orb support even without an exact root in the fitted knots. Preserve both-edge clipping and distinguish unresolved computation from observed truncation.
4. **Implement physical boundary storage once per body/convention/grid.** Attach target roles separately and reuse the same boundary events for residence construction. Assert uniqueness after dedupe/persistence, not only solver-call counts.
5. **Repair seam endpoint ownership.** Preserve valid direct-start and retrograde-end zero roots while maintaining one interior seam event.
6. **Make the receiving contract compatible, or mechanically gate the new output.** Cover interval-overlap reads, default residence inclusion, null-safe serialization/pagination, residence semantics and downstream invalidation.
7. **Replace incomplete acceptance claims with discriminating tests.** Add the reproduced counterexamples, historical ID goldens, partition-extension/alias tests, stored-boundary uniqueness and O-SS coverage. Update database fixtures to apply 1152 and test valid/invalid null combinations. Add migration replay and rollback/preservation instructions; correct its misleading scope and identity comments.

**What I could not verify**

- Production '4.0' contents, constraint compatibility, migration application history, actual locks or rollback behavior: **no database was contacted**.
- Eight file/database-fixture tests and persistence end-to-end behavior.
- Published-contact lineage, Kṣetra/Saṅgam rebuild acceptance, live serving or deployment.
- O-SS-4’s complete Moon on-demand and no-materialized-rows proof.
- Remote changes newer than the local remote-tracking references.

The independent review is complete. The implementation is not acceptable for merge against the supplied frozen contract.

