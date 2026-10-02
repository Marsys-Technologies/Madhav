---
artifact: ASTRA_REVIEW_A2_KERNEL_GEOMETRY
version: "1.1"
status: COMPLETED_INDEPENDENT_READ_ONLY_REVIEW
reviewer: "Codex gpt-6-astra"
date: "2026-09-30"
verdict: REJECT
reviewed_commit: ff6889ddf
authority: "Review only; authorizes nothing."
---

**Verdict: REJECT**

Several original counterexamples now pass. However, the rework introduces incorrect residence exits and missing/duplicated multi-revolution seam events. Physical boundary storage remains duplicated for interval targets, and the required ‘4.0’ serving exclusion is incomplete.

R1/R7 are judged **only through obligations (i)–(iii)**. Full §6.1 identity and broader consumer-contract changes remain Phase 5 work. Nothing in this review authorizes publishing or flipping ‘4.1’.

Verified full SHA: `ff6889ddfb349f83f2056b727c9175b319be3e7e`. All **15 changed files** matched their commit blobs.

Independent execution:

- Requested kernel/enumeration files: **61 passed, 8 deselected**.
- Serving tests, `test_s1_find_episodes.py`: **13 passed**.
- Additional counterexamples below ran independently, including checksum-verified Swiss computations and baseline comparisons against `95e765c3c`.

Tests used disabled bytecode/cache/logging, isolated conftest loading, and an in-memory guard against writes and connections. No files were written, no git write commands or database connections occurred, and neither prohibited directory was accessed.

**Closure table**

References to kernel filenames below mean `platform/python-sidecar/services/gochara_kernel/`. The enumeration driver is `platform/python-sidecar/scripts/kala_gochara_cutover/step06_enumerate_episodes.py`; test filenames are under `platform/python-sidecar/tests/l3/gochara/`.

| Item | Disposition | File:line evidence and independent result |
|---|---|---|
| **R2 — coherent refined residence geometry** | **PARTLY CLOSED** | `episodes.py:571–599` removes the old refined-root/sub-second join. The ordinary-tolerance `200 + 0.137·day` probe now returns coherent entry/exit at approximately **72.992700730 / 291.970802919 days**. Sun 2025 returns **13 spans, 12 exact ingresses, one correctly clipped initial tail**. Upper-boundary metadata is corrected. However, station-spanning exits and domain-start entries now fail; see regressions 1–2. |
| **R3 — every revolution** | **CLOSED** | `episodes.py:532–558` enumerates every intersected band. Independently reproduced **[30,60], [390,420], [750,780]**, within the declared tolerance. Swiss Sun Taurus, 2025–2035: **10 residences and 10 independently found Taurus ingresses**. |
| **R4 — no-root support; truncation versus unresolved** | **CLOSED** | `episodes.py:279–319`; driver `:568–570`, `:622–625`. The original `196 + 0.01·day`, target 200°, orb 5°, 30-day probe now retains **one null-exact conjunction**, with **`both`**, **`unqualified`**, and `near_station_unresolved=True`. A residence clipped at both edges retains `both` on both serialized rows; its observed clipping remains distinct from unresolved root certification. |
| **R5 — boundary storage once and reuse** | **PARTLY CLOSED** | Driver `:753–766` fixes point-target duplication: the original three-point fixture now has **28 boundary rows / 28 physical events** after dedupe. But `:805` still emits target-specific ingress copies for interval targets; `:830` excludes those copies from the uniqueness assertion. Mixed-target probe: **31 normalized rows, 31 distinct contact IDs, 28 physical events**. Shared-root reuse also remains tolerance-dependent; see residual findings. |
| **R6 — seam endpoints and interior ownership** | **PARTLY CLOSED** | `arcs.py:156–173`; `contacts.py:246–250`, `:286–310`. Actual direct-start, retrograde-end and single interior seam probes now pass. Multi-revolution ownership introduces missing and duplicated crossings; see regression 3. |
| **Kimi #1 — upper-boundary longitude** | **CLOSED** | `episodes.py:555`, `:621–630`; `test_wp3a_kernel.py:1107`. Retrograde ingress carries the upper boundary, including 60° for `[30,60]` and 0° for Pisces re-entry through the seam. |
| **Kimi #2 — preserve `both`** | **CLOSED** | `episodes.py:642–644`; driver `:568–570`, `:622–625`. Independent clipped-residence serialization retains **`both` on both rows**. |
| **Kimi #3 — double-counted truncation** | **CLOSED** | Driver `:805–816`; `test_step06_enumeration.py:1350`. One clipped residence produces two null-exact rows and **one** `episodes_without_exact` increment. |
| **Kimi #4 — replay/reversal stance** | **CLOSED** | Migration 1152 `:49–57` explicitly states tracked single-run execution, non-idempotent SQL replay and reversal limitations. Its separate operational assertions remain defective below. |
| **1152 — header** | **PARTLY CLOSED** | Published ‘4.0’ scope is acknowledged at `:37–46`; §6.1 compliance is expressly disclaimed at `:20–23`. However, `:39–40` still infers validation success from `NOT NULL`, and `:58–61` incorrectly describes transaction locking and an unmeasured volume check. |
| **1152 — `both` CHECK** | **CLOSED** | `platform/migrations/1152_kala_gochara_contacts_t_exact_nullable_truncated.sql:75–83` replaces the original CHECK with one admitting `start`, `end`, `both`, or NULL. The exactness-consistency CHECK remains present at `:68–73`. Source-level verification only. |
| **1152 — fixture** | **CLOSED** | `conftest.py:162` and `test_step06_enumeration.py:642` now apply 1152. `test_wp6_ledger.py:750` adds valid/invalid exactness combinations and persisted `both`. These database tests were inspected, **not executed**. |
| **1152 — preflight** | **CLOSED** | `scripts/kala_gochara_cutover/preflight_1152_existing_rows_satisfy_check.sql:10–12` correctly selects violations of the new Boolean consistency invariant, given non-null `exact_crossing`. It supplies a preflight, not evidence that production passed it. |
| **R1/R7 scope (i) — historical exact-ID golden** | **CLOSED** | `test_wp3a_kernel.py:1194–1210`; fixture `golden_contact_ids_origin_main.json:4`. I independently **executed historical `origin/main` code**, then compared its results with the committed goldens and current implementation: **27/27 matched both**. This was not current-code self-comparison. |
| **R1/R7 scope (ii) — no §6.1 compliance claim** | **CLOSED** | Driver `:81–84` and migration 1152 `:20–23` explicitly defer physical identity/enrichment to A5.3/A5.1. No affirmative §6.1-compliance claim remained in the reviewed implementation surfaces. |
| **R1/R7 scope (iii) — ‘4.0’ exclusion gate** | **PARTLY CLOSED** | Driver `:676–685`, `:734–743`, `:815–816` effectively excludes null-exact/residence producer rows for ‘4.0’; independently rerun. Serving is incomplete: `services/ka_gochara/service.py:310` accepts explicit residence requests, and `:358–360` appends ungated Moon results. Both bypasses were reproduced using an in-memory authority adapter. |

For the historical golden, the independently executed local `origin/main` revision was `469009b6a8240dd3b2f59036e4f6356327ec004f`; its `ids.py` blob was `3c787d840ffaa91772fb56d3e06c465a5f081017`.

**Regressions and remaining defects**

**1. High — station-spanning residences refine their exit against the entry segment.**

At [episodes.py:563](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/a22-review-ff6889ddf/platform/python-sidecar/services/gochara_kernel/episodes.py:563), merging replaces the exit crossing but retains the first segment. Line 589 then refines that exit with the retained entry segment.

Consequences reproduced:

| Probe | Correct exit | Rework result |
|---|---|---|
| Swiss Mars 2025, residence `[60°,90°]` | **2 April**, at 90° | **14 March 11:03 UTC**, at **84.724426942°** |
| Swiss Jupiter 2025, residence `[30°,60°]` | **14 May**, at 60° | **25 March**, at **50.813265291°** |
| Analytic `λ(t)=20−(t−10)²`, `[0°,30°]`, shared roots supplied | Exit on the falling segment | **`ValueError: … lost its bracket under direct Swiss`** |

The Mars baseline at `95e765c3c` exits on 2 April near 90°. This is a **new geometry regression**, not merely the old missing-ingress defect.

**2. Medium — observed domain-start residence ingress becomes null.**

The strict comparisons at [episodes.py:544](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/a22-review-ff6889ddf/platform/python-sidecar/services/gochara_kernel/episodes.py:544) leave `entry_crossing=None` when the first knot is exactly on the entry boundary.

For `λ(t)=30+t`, domain/horizon `[0,40]`, residence `[30,60]`:

- Boundary solver: observed 30° root at **day 0**.
- Baseline residence: **`t_exact=day 0`**.
- Rework residence: **`t_exact=None`, truncation NULL, completeness `applied`**.

This recreates false missing-exactness at a valid domain endpoint.

**3. High — full-revolution arcs break seam deduplication.**

[contacts.py:246](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/a22-review-ff6889ddf/platform/python-sidecar/services/gochara_kernel/contacts.py:246) selects the 360° representative first. On an arc whose **both endpoints are seams**, `_anchor` at line 286 nevertheless chooses its start, without using the solved root’s location. Distinct crossings are consequently treated as duplicates.

Independent baseline comparison:

```text
λ(t)=10+t°, days [0,1500]

Expected / 95e765c3c: 350, 710, 1070, 1430
ff6889ddf:           350,      1070, 1430, 1430
```

For `λ(t)=t°`, `[0,1000]`, expected `0,360,720`; returned `360,720,720`.

Swiss Sun 2025–2035 confirms the defect: **2026’s seam crossing disappears and 2034’s appears twice**. Across the three grids, the driver emits 1,350 rows; dedupe removes three duplicates, leaving **1,347**. `assert_sky_events_unique` passes despite the three missing physical events.

**4. R5 remains incomplete for interval targets and ordinary tolerances.**

The interval loop still writes each residence’s ingress as another boundary-event row at [driver:805](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/a22-review-ff6889ddf/platform/python-sidecar/scripts/kala_gochara_cutover/step06_enumerate_episodes.py:805).

Adding three interval targets to the original three-point fixture produces **31 boundary rows for 28 physical events**, even after real dedupe and `_normalize_episode`. All 31 contact IDs are distinct. The February 10 sign ingress survives as:

```text
sky_event / sky:sign_ingress
bhava     / x
bhava     / y
```

The uniqueness assertion at line 830 checks only `sky_event`, so it ignores the duplicates. Sharing an `independence_group` does not satisfy “stored once.”

Reuse also still depends on the **86.4-second** timestamp threshold at `episodes.py:468`. With ordinary one-arcsecond tolerance and `λ(t)=350+0.137t`, the two spline-solving brackets disagree by **96.317 and 180.762 seconds**. Residence construction re-refines crossings despite receiving their solved boundary events.

**5. Scope obligation (iii) is not enforced across the serving method.**

The new serving test exercises default relations. `EPISODE_RELATIONS` is a default, not an enforced whitelist:

- With its own in-memory ‘4.0’ fixture, `find_episodes(..., relations=['residence'])` **returns the residence row**.
- With ‘4.0’ authority, real Swiss Moon computation for 1–2 January 2025 and a target 0.5° beyond the Moon’s end longitude returns **`t_exact=None`, truncation `end`, completeness `applied`**.

Relevant paths are [service.py:310](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/a22-review-ff6889ddf/platform/python-sidecar/services/ka_gochara/service.py:310), `:358–360`, and `:611–627`.

These are **unclosed gate obligations**; I am not reopening the deferred consumer redesign or claiming production data was modified.

**6. Migration 1152’s new operational assurances are incorrect.**

The header at [1152:58](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/a22-review-ff6889ddf/platform/migrations/1152_kala_gochara_contacts_t_exact_nullable_truncated.sql:58) describes brief locks followed by nonblocking validation. However, [migrate.ts:791](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/a22-review-ff6889ddf/platform/scripts/migrate.ts:791) executes the whole file in one transaction. The earlier `ACCESS EXCLUSIVE` lock remains held through validation and commit; requesting a weaker validation lock does not release it. This follows from PostgreSQL’s documented [ALTER TABLE lock rules](https://www.postgresql.org/docs/current/sql-altertable.html) and [transaction lock lifetime](https://www.postgresql.org/docs/current/explicit-locking.html).

Additionally:

- `t_exact NOT NULL` does **not** prove `exact_crossing=True`; the preflight is necessary.
- The preflight returns violating rows, not table volume. Zero violations cannot establish the header’s “trivially cheap” claim.
- The migration contains no bounded lock/statement handling.

**Ranked merge-blocking amendments**

1. **P1 — Repair residence edge provenance.** Preserve the segment/event belonging to each exit across station merges; reject invalid refinement brackets. Preserve observed ingress roots at domain boundaries. Add the Mars/Jupiter, analytic station and exact-start counterexamples.
2. **P1 — Repair multi-revolution seam ownership.** Anchor deduplication to the actual solved crossing, including arcs with two seam endpoints. Assert expected distinct instants over multiple revolutions and after dedupe; include the missing-2026 Sun case.
3. **P1 — Complete R5 across the whole payload.** Store each physical boundary event once, represent target attachments separately, and assert uniqueness after normalization without filtering away attached copies. Reuse boundary events through explicit crossing association rather than another timestamp-tolerance join.
4. **P2 — Enforce scope obligation (iii) at serving.** Cover explicit relation requests and Moon on-demand output under ‘4.0’ authority. Extend the gate tests to these exercised paths while retaining the working producer and published-generation protections.
5. **P2 — Correct and bound migration operation.** Remove unsupported validation-success/volume claims; accurately document transaction-wide blocking and supply a bounded application/validation procedure. Retain the violation preflight as a required **pre-application** check.

**What I could not verify**

- Database execution of migration 1152, its valid/invalid-row tests, actual persisted uniqueness, production preflight results, table volume, lock duration or rollback behavior.
- Eight file/database-dependent tests deselected from the requested pair.
- The original author’s golden-generation invocation; the golden values were independently regenerated from historical code during this review.
- Remote changes beyond local `origin/main`, production serving/deployment, or any ‘4.1’ publication state.
- Century-scale execution and complete Moon acceptance. The Moon probe above establishes the serving-gate gap only.
- Phase 5 physical identity, enrichment lineage and consumer-contract implementation, which remain outside this closure check.