---
artifact: ASTRA_REVIEW_A2_KERNEL_GEOMETRY
version: "1.2"
status: COMPLETED_INDEPENDENT_READ_ONLY_REVIEW
reviewer: "Codex gpt-6-astra"
date: "2026-09-30"
verdict: ACCEPT
reviewed_commit: ee0dd335f
authority: "Review only; authorizes nothing."
---

**Verdict: ACCEPT**

All five ranked amendments from v1.1 are **CLOSED** within the steward’s scope ruling. No new merge-blocking regression was found.

Reviewed `ff6889ddf..ee0dd335f`, including `ce39993c6`, `989844066`, and `ee0dd335f`. Verified full HEAD: `ee0dd335fe7d0c350a5edfe690035f466ad53aa9`. All **eight changed files** matched their commit blobs.

R1/R7 remain limited to obligations **(i)–(iii)**. Full §6.1 identity, enrichment lineage, and consumer redesign remain Phase 5 work.

Independent execution:

- Requested kernel, enumeration, and serving tests: **82 passed, 8 deselected**.
- Separately reran the prior counterexamples and additional regression probes.
- Swiss computations used checksum-verified `.se1` files and asserted the returned Swiss backend flags.

Execution disabled bytecode, pytest cache, and file logging; isolated conftest loading; and guarded against filesystem writes and database connections. No files were created or modified, no git write command or database connection occurred, and neither prohibited directory was accessed.

**Closure table**

The numbering below follows the five ranked amendments in v1.1; amendment 1 includes both station-spanning exits and domain-start ingress.

| Amendment | Disposition | Source evidence and independent result |
|---|---|---|
| **1 — Residence edge provenance, including domain-start ingress** | **CLOSED** | [Edge handling](./platform/python-sidecar/services/gochara_kernel/episodes.py) at lines **560–633** carries each crossing’s own segment through merges. Mars `[60°,90°]` exits **2025-04-02 19:59:18 UTC**, at **89.99999999995°**. Jupiter `[30°,60°]` exits **2025-05-14 17:06:48 UTC**, at **59.99999999995°**. Both agree with independently bracketed Swiss bisections, with and without shared roots. The analytic `20−(t−10)²` case returns the correct falling-leg exit without raising or performing another refinement. `λ=30+t`, domain/horizon `[0,40]`, returns **observed ingress at day 0**, exit at day 30, and no truncation. |
| **2 — Multi-revolution seam ownership** | **CLOSED** | [Contact solving](./platform/python-sidecar/services/gochara_kernel/contacts.py) at lines **231–337** enumerates both seam representatives and anchors ownership to the solved endpoint. Independently recovered **350/710/1070/1430** for `10+t` and **0/360/720** for `t`, within the declared tolerance, across all three boundary relations. Retrograde counterparts also pass. Daily-knot Swiss Sun computation produces **one seam crossing in every year 2025–2035 inclusive**. |
| **3 — R5 across the whole payload and explicit crossing reuse** | **CLOSED** | The [enumerator](./platform/python-sidecar/scripts/kala_gochara_cutover/step06_enumerate_episodes.py) at lines **810–862** retains residence attachments without emitting target-specific boundary copies. The mixed three-point/three-interval fixture yields **28 normalized boundary rows, 28 distinct contact IDs, and 28 physical events** after real dedupe and normalization. All three residence attachments survive. Injected target-attached and duplicate sky rows both fail the whole-payload assertion. `episodes.py:449–482` associates shared roots by level, direction, and bracket containment. Independent **one-arcsecond** probes, including `350+0.137t` and direct/retrograde multi-revolution cases, reuse the shared instants with **zero additional refinements**. |
| **4 — Serving exclusion under ‘4.0’** | **CLOSED** | [Serving gates](./platform/python-sidecar/services/ka_gochara/service.py) at lines **339–349** and **376–383** cover both bypasses. An explicit `relations=['residence']` request returns no episodes; a mixed residence/conjunction request retains only the permitted conjunction. The real Swiss Moon probe for **1–2 January 2025**, targeting **0.5° beyond the end longitude**, still computes a null-exact, end-truncated episode internally, but **serves none under ‘4.0’**. Exact Moon output remains served. Producer exclusion and the published-generation write refusal also remain effective. |
| **5 — Migration 1152 operation and header** | **CLOSED — source-level** | [Migration 1152](./platform/migrations/1152_kala_gochara_contacts_t_exact_nullable_truncated.sql) at lines **37–74** removes the unsupported validation-success and volume claims, requires the pre-application violation check, accurately describes transaction-wide blocking, and sets **`lock_timeout='5s'`** plus **`statement_timeout='120s'`** before DDL. The runner still wraps execution and tracking in one transaction with rollback on error. The header agrees with PostgreSQL’s documented [lock lifetime](https://www.postgresql.org/docs/current/explicit-locking.html) and [timeout semantics](https://www.postgresql.org/docs/current/runtime-config-client.html). The statement timeout is a per-statement bound, not a 120-second bound on the complete transaction. |

Previously **CLOSED** findings remain closed:

| Finding from v1.1 | Disposition | Reverification |
|---|---|---|
| **R3 — Every revolution** | **CLOSED** | Recovered `[30,60]`, `[390,420]`, `[750,780]`; Swiss Sun Taurus has **10 residences** over `[2025-01-01,2035-01-01)`. |
| **R4 — No-root support; truncation versus unresolved** | **CLOSED** | Original `196+0.01·day`, target 200°, orb 5°, 30-day probe retains one null-exact episode with **`both`**, **`unqualified`**, and `near_station_unresolved=True`. |
| **Kimi #1 — Upper-boundary longitude** | **CLOSED** | Retrograde ingress reports **60°** for `[30,60]` and **0°** for Pisces re-entry through the seam. |
| **Kimi #2 — Preserve `both`** | **CLOSED** | Kernel and serialization retain `both`; the surviving residence row retains it after normalization. |
| **Kimi #3 — Count physical truncation once** | **CLOSED** | One clipped residence now produces one persisted residence row and one truncation increment. |
| **Kimi #4 — Replay/reversal stance** | **CLOSED** | Migration lines **50–69** retain explicit single-run, non-idempotent replay, and reversal limitations. |
| **1152 — `both` and exactness CHECKs** | **CLOSED — source-level** | Lines **79–94** retain both constraints and validation statements; `exact_crossing` remains non-null in the base schema. |
| **1152 — Fixtures** | **CLOSED — source-level** | Both database fixtures still apply 1152; the valid/invalid exactness-combination and persisted-`both` test remains present. Database execution was excluded. |
| **1152 — Preflight** | **CLOSED — source-level** | The preflight still selects violations using `exact_crossing <> (t_exact IS NOT NULL)`. No production result is inferred. |
| **R1/R7 (i) — Historical exact-ID golden** | **CLOSED** | Independently executed historical `ids.py` at **`469009b6a8240dd3b2f59036e4f6356327ec004f`**, blob **`3c787d840ffaa91772fb56d3e06c465a5f081017`**: **27/27** results match both committed goldens and current code. |
| **R1/R7 (ii) — No §6.1 compliance claim** | **CLOSED** | Enumerator lines **79–86** and migration lines **20–23** continue explicitly deferring the full contract to Phase 5. |

**Regressions**

No new merge-blocking regression was reproduced.

Additional checks beyond the supplied counterexamples established:

- The ten-year Sun payload retains **1,350 boundary events after dedupe and normalization**: **120 sign**, **270 nakshatra**, and **960 kakshya** crossings. These counts independently match daily Swiss longitude crossings.
- All-sign residences continuously cover the 2025 horizon for **Sun, Mercury, Venus, Mars, Jupiter, Saturn, Rahu, and Ketu**, with matching adjacent edges and no additional refinement of supplied boundary roots.
- The original ordinary-tolerance residence probe still returns coherent entry/exit at approximately **72.992700730 / 291.970802919 days**.
- Sun 2025 retains **13 residences, 12 observed ingresses, and the clipped initial residence**.

**Ranked merge-blocking amendments**

**None.**

**What I could not verify**

- Database application of migration 1152, database constraint tests, persisted uniqueness, production preflight results, table volume, actual lock duration, or operational rollback behavior.
- The **eight file/database-dependent tests** deselected from the requested suite.
- Remote changes, production serving or deployment, or any ‘4.1’ publication state.
- Century-scale execution or complete Moon acceptance.
- Phase 5 physical identity, enrichment lineage, and consumer redesign, which remain outside this review.