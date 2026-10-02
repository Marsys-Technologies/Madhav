---
artifact: ASTRA_REVIEW_A5_1_MIGRATIONS
version: "1.6"
reviewer: "Codex gpt-6-astra"
date: "2026-09-30"
verdict: ACCEPT_WITH_AMENDMENTS
reviewed_commit: 02f4ad0e3
authority: "Review only; authorizes nothing."
---

**Verdict: ACCEPT_WITH_AMENDMENTS**

**N19, N18 and the prior P3 label issue are CLOSED. No merge-blocking defect remains within this closure review.** One new documentation correction is listed separately as a non-blocking follow-up.

Verified HEAD: `02f4ad0e332d3646265a7b1f030648b24b5ca99f`. Reviewed the complete five-file diff from `6d67a29fe`. “CLOSED” means closed at source-review level; database execution was prohibited.

Evidence abbreviations, with current-checkout line numbers below:

- **M1153:** [substrate migration](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2765g/platform/migrations/1153_gochara_sky_event_substrate.sql); **M1154:** [rule registry](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2765g/platform/migrations/1154_gochara_rule_path_registry.sql).
- **M1155:** [relationship records](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2765g/platform/migrations/1155_gochara_relationship_record.sql); **M1156:** [evaluation windows](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2765g/platform/migrations/1156_gochara_eval_window.sql); **M1157:** [AV declaration](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2765g/platform/migrations/1157_gochara_av_polarity_declaration.sql).
- **DBT:** [database tests](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2765g/platform/tests/integration/gochara_a5_1_migrations.db.test.ts); **ST:** [static tests](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2765g/platform/tests/unit/migrations/gochara_a5_1_contract_static.test.ts); **URL:** [disposable-target resolver](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2765g/platform/tests/integration/gochara_a5_1_disposable_url.ts).
- **MT:** [migration runner](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2765g/platform/scripts/migrate.ts); **DY:** [deployment workflow](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2765g/.github/workflows/deploy.yml).

**Closure table**

| Finding | Judgment | Evidence and disposition |
|---|---|---|
| **N19 / N14 / N10 — timestamp collision and incompatible sealing** | **CLOSED** | **M1153:417–423** requires a nonempty, bounded range with lower bound ≥ `1000-01-01T00:00Z` and upper bound < `3000-01-01T00:00Z`. Range ordering makes these sufficient to constrain both bounds. **M1155:364–374** refuses unsupported input before encoding. **M1156:523,542–545** classifies an out-of-domain partition as `incompatible`, returning NULL current facts before any encoding/equality comparison; **M1153:939–945** refuses sealing. **DBT:1593–1615** covers BC, domain edges and exact round trips; **1649–1674** reproduces the same-digits AD→BC replacement, expects seal refusal, then restores AD and expects successful sealing. This implements the binding domain restriction. |
| **N18 / N13 / N2 — chart switching and substrate deadlock** | **CLOSED** | **M1153:441–449** rejects a different bound chart and every non-canonical chart before the advisory-lock call at **453**. The successful acquisition records the transaction binding at **454–456**. **565–577** rejects conflicting declared substrate context or routes first acquisition through the restricted helper. Statement triggers remain ahead of sky-event and identity writes at **795–797,874–876**. Thus the prior transaction cannot acquire substrate locks under D and subsequently wait for C through these entry points. **DBT:1250–1322** covers direct refusal, switching, conflicting context, and both mixed-context schedules while the main connection retains its orchestrator locks. |
| **P3 — stale static-suite round label** | **CLOSED** | **ST:133** now says “round 7”; the header at **ST:3** agrees. The database-suite label was also updated at **DBT:776**. |

Within the restricted domain, four-digit AD year, UTC time, six fractional digits and separate inclusivity flags preserve the timestamp bounds consumed by the unchanged inverse at **M1155:396–405**. This source-level conclusion is consistent with PostgreSQL’s documented microsecond timestamp resolution and formatting tokens. [Timestamp types](https://www.postgresql.org/docs/17/datatype-datetime.html), [formatting functions](https://www.postgresql.org/docs/17/functions-formatting.html).

**Reconfirmation of earlier closures**

All earlier closures remain intact.

| Earlier finding | Judgment and current evidence |
|---|---|
| **N1 — legacy publication isolation** | **CLOSED.** Governed-generation predicate **M1153:408–410**; explicit legacy refusal **978–982**. No business trigger on the legacy publication table was introduced. |
| **N3 — protected deployment route** | **CLOSED.** Protected dispatch/environment **DY:949–964**; ordered family and invocation/revocation **1054–1073**; routine refusal **MT:138–152,798**. These files are unchanged. |
| **N4 — verifier/replay design** | **CLOSED.** Presence checks remain; applied files are hash-checked and skipped at **MT:789–795**. All five embedded preflight blocks independently match their standalone copies. No custom definition verifier or replay mode was restored. |
| **N5 — rule membership/seal race** | **CLOSED.** Global EXCLUSIVE precedes membership seal inspection at **M1154:469–475**; consumers acquire SHARED before checking at **484–490**; rule sealing retains the global guard at **520–523**. |
| **N6 — conflicting solved readings** | **CLOSED.** Canonical-chart CHECK **M1153:1068–1069**, chart locking **1128**, cross-generation consistency check **1163–1176**. The guard is unchanged. |
| **N7 / N15 — precision propagation after coverage extension** | **CLOSED.** Propagation **M1155:840–864**; precision-only exemption from coverage revalidation **677–715,728–748**; restated precision still verified **752–757**. Regression retained at **DBT:1545–1567**. |
| **N8 — prerequisite reparenting** | **CLOSED.** Ownership immutability and result-only updates **M1155:440–450**; prerequisite trigger selects that mode at **898–901**. |
| **N9 — published membership changes** | **CLOSED.** Sealed INSERT refusal and immutable membership mode **M1155:431–445**; membership guard installation **M1156:583–590**. |
| **N11 — disposable target validation** | **CLOSED.** Driver parsing, query restrictions and explicit target validation **URL:71–111** are byte-identical to round 6. |
| **N12 — worker blocked by scheduler locks** | **CLOSED.** Dedicated family keys remain at **M1153:453,471,483**. Separate scheduler/worker regression remains at **DBT:983–1038**; orchestrator sources are unchanged. |
| **N16 — candidate updates bypass membership applicability** | **CLOSED.** Seal acquires the chart key at **M1153:929** and checks every membership at **947–955**. Shared predicate and complete membership scan remain at **M1156:419–441,478–488**. Regression retained at **DBT:1677–1741**. |
| **N17 — non-finite horizons** | **CLOSED.** The stricter predicate still excludes empty/unbounded ranges and explicit infinities; both consumer guards and interval CHECKs continue using it: **M1155:336–342,567–568,696–700; M1156:284–285,393–397**. |
| **P2 — operational overclaims** | **CLOSED.** Existing FK effects, routine-runner writes, per-file atomicity and recovery remain accurately disclosed at **M1153:129–154**, consistent with **MT:733–755,777–832**. |
| **Earlier refusal wording** | **CLOSED.** **M1153:66–70** still distinguishes refusal before family advisory locking from possible preceding tuple waits. |

Earlier **F1, F6, F8 and F11** closures and round-1 amendments **#2, #3, #7 and #9** also remain intact: identity/ownership constraints, C2 factor rules, argument-type preflight matching, typed-value constraints, transaction ownership and versioned references were preserved. Representative anchors: **M1153:813–826,1061–1078; M1154:310–350; M1155:540–547,583–599,647–651; M1157:129–135; MT:822–832**. Fact-ID resolution remains the previously accepted downstream writer obligation, not verified implementation.

Independent comparison confirmed preservation of all **18 table definitions**, **59 trigger declarations** and **35 complete helper/guard definitions** between the reviewed commits.

**New defects**

**No new merge-blocking defect found.**

**FU-1 — P3, documentation only:** New wording at **M1153:93–95** and **447** says every chart-scoped table directly CHECKs the canonical chart. That is inaccurate:

- The generation-seal table at **892–902** has no canonical-chart CHECK; its guard invokes the restricted helper at **929**.
- Prerequisites inherit scope through **M1155:647–649**.
- Window memberships inherit scope through **M1156:346–353**.

The enforcement is sufficient for N18. The description should distinguish direct CHECKs, scope FKs and lock-boundary enforcement.

**Merge-blocking versus follow-up amendments**

- **Merge-blocking:** None.
- **Post-merge, non-blocking:** Correct **FU-1**’s explanatory wording. No additional schema constraint or design change is requested.
- **Before application:** Retain the existing exact-commit disposable-database and protected-window verification obligations. If these migrations have already been applied, preserve their applied bytes and use forward migrations for executable corrections.

**What I could not verify**

Completed checks: **18 reviewed files matched the requested commit byte-for-byte**, all five preflight comparisons passed, the preservation checks above passed, and the round-7 diff passed `git diff --check`.

- No database was contacted; migrations, SQL self-tests, integration tests and concurrency schedules were not executed.
- Test assertions were inspected, not reported as passing runtime evidence.
- Live PR checks, production privileges, applied migration hashes, deployment approvals and actual lock timing remain unverified.
- The comments’ assertion that 1153–1157 have never been applied anywhere was not independently established.

No files were created or modified, no git write command was run, and neither prohibited directory was accessed.