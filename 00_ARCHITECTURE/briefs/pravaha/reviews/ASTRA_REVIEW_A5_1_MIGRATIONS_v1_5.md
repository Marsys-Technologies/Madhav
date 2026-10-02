---
artifact: ASTRA_REVIEW_A5_1_MIGRATIONS
version: "1.5"
reviewer: "Codex gpt-6-astra"
date: "2026-09-30"
verdict: REJECT
reviewed_commit: 6d67a29fe
authority: "Review only; authorizes nothing."
---

**Verdict: REJECT**

N16’s seal-boundary enforcement and N17’s rejection of non-finite horizons are implemented. Two merge blockers remain:

1. Finite BC and AD horizons encode identically, allowing incompatible coverage to pass sealing.
2. A transaction can acquire substrate locks under one chart context and subsequently wait for another chart’s family lock, recreating N13’s deadlock.

These affect persisted correctness and transaction execution. They require correction before merge.

HEAD was verified as `6d67a29feddb83ff8341b9f5bdeb0cc29e6127b1`. “CLOSED” below means closed at source-review level. Counterexamples are derived from inspected source and PostgreSQL semantics; they were not executed against a database.

**Closure table**

Evidence abbreviations identify these files; appended numbers identify lines:

- **M1153:** [sky-event substrate](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2765f/platform/migrations/1153_gochara_sky_event_substrate.sql); **M1154:** [rule-path registry](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2765f/platform/migrations/1154_gochara_rule_path_registry.sql).
- **M1155:** [relationship records](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2765f/platform/migrations/1155_gochara_relationship_record.sql); **M1156:** [evaluation windows](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2765f/platform/migrations/1156_gochara_eval_window.sql); **M1157:** [AV declaration](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2765f/platform/migrations/1157_gochara_av_polarity_declaration.sql).
- **DBT:** [database tests](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2765f/platform/tests/integration/gochara_a5_1_migrations.db.test.ts); **URL:** [disposable-database resolver](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2765f/platform/tests/integration/gochara_a5_1_disposable_url.ts); **ST:** [static contract tests](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2765f/platform/tests/unit/migrations/gochara_a5_1_contract_static.test.ts).
- **MT:** [migration runner](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2765f/platform/scripts/migrate.ts); **DY:** [deployment workflow](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2765f/.github/workflows/deploy.yml).

| Finding | Judgment | Evidence and disposition |
|---|---|---|
| **N16 — candidate updates bypass membership applicability** | **CLOSED** | The seal acquires the chart key at **M1153:895**, then refuses any membership violation at **913–920**. **M1156:417–439,476–486** reuse one predicate over every membership, checking convention, searched relation and support containment. **DBT:1554–1617** covers valid membership followed by relation, convention, window-horizon and contributor-support changes, seal refusal, and successful sealing after restoration. This implements the steward’s chosen boundary. N19 below is a separate defect in the horizon representation consumed by that predicate. |
| **N13 — mixed substrate/chart lock order** | **PARTLY CLOSED** | Statement triggers acquire a chart key before substrate writes, and absent context is refused: **M1153:531–545,567–571,610–614,760–763,839–842,993–996**. AV is included at **M1157:146–149**, consistently extending the rule. However, **M1153:413–428** permits changing charts within a transaction; the substrate guard’s boolean marker does not establish an immutable chart binding. N18 below recreates the cycle. |
| **N17 — unsupported horizons** | **CLOSED** | **M1153:400–406** rejects NULL, empty, unbounded and explicit infinite bounds. The encoder raises at **M1155:359–362**; support intervals are constrained at **333–339,561–562**; windows at **M1156:281–283**. Coverage guards reject unsupported completed horizons at **M1155:690–693; M1156:391–394**. Later non-finite coverage becomes `incompatible` at **M1156:521,540–542**. Regression cases appear at **DBT:1506–1551**. |
| **N2 — locking and isolation protocol** | **PARTLY CLOSED** | READ COMMITTED enforcement and dedicated family keys remain at **M1153:416–456**. Scheduler/worker separation remains covered by **DBT:972–1026**. The permitted chart-context switch leaves the N18 transaction cycle open. |
| **N10 — coverage binding and applicability** | **PARTLY CLOSED** | N16’s parent-update bypass and N17’s infinity case are addressed. Stored-fact equality still misclassifies the finite-era collision as `identical` at **M1156:522**, allowing the seal’s checks at **M1153:905–920** to pass. |
| **N14 — coverage serialization collisions** | **PARTLY CLOSED** | JSON retains relation element boundaries, NULLs, duplicates and inclusivity: **M1155:363–374**. Unsupported horizons now raise. However, the accepted finite domain contains BC dates, and **M1155:366–368** omits their era. N19 below demonstrates a remaining collision and failed round trip. |

**Reconfirmation of round-5 closures**

The supplied [v1.4 review](/Users/Dev/madhav-l3/pravaha/00_ARCHITECTURE/briefs/pravaha/reviews/ASTRA_REVIEW_A5_1_MIGRATIONS_v1_4.md) explicitly labels **12 items CLOSED**: eleven N-findings plus P2. All twelve remain closed. Its separate, unnumbered wording issue is also corrected this round; it was not previously a closure.

| Previously closed finding | Reconfirmation |
|---|---|
| **N1 — legacy publication trigger** | **CLOSED.** Governed-generation predicate **M1153:393–396**; explicit legacy refusal **944–948**. All declared business triggers target this migration family’s tables. |
| **N3 — protected deployment route** | **CLOSED.** Protected dispatch/environment **DY:949–964**, exact ordered family **1054–1060**, invocation/revocation **1067–1073**; routine refusal **MT:138–152,798**. |
| **N4 — verifier/replay design** | **CLOSED.** Presence checks remain, including **M1153:1210–1219**; tracked files are hash-checked and skipped at **MT:789–795**. All five embedded preflight blocks independently match their standalone copies. |
| **N5 — rule membership/seal race** | **CLOSED.** Membership takes global EXCLUSIVE before reading the seal: **M1154:469–475**. Consumers take SHARED before checking: **484–490**. Rule sealing retains the global guard at **520–523**. |
| **N6 — conflicting solved readings** | **CLOSED.** Canonical-chart restriction **M1153:1034–1035**, chart lock **1094**, cross-generation consistency checks **1129–1143**. The guard is unchanged from round 5. |
| **N7 — stale dependent precision** | **CLOSED.** Propagation remains at **M1155:834–858**, with contact-precision verification at **746–751**. Extend-then-enrich coverage remains at **DBT:1460–1481**. |
| **N8 — prerequisite reparenting** | **CLOSED.** Scope immutability and result-only changes **M1155:434–444**, installed on prerequisites at **892–895**. |
| **N9 — published membership changes** | **CLOSED.** Sealed INSERT/UPDATE refusal and immutable membership mode **M1155:425–450**; window-membership guard **M1156:581–588**. |
| **N11 — disposable URL targeting** | **CLOSED.** Driver parsing, query restrictions and explicit target validation remain at **URL:71–111**, byte-identical to round 5. |
| **N12 — worker waits on scheduler** | **CLOSED.** Dedicated family keys **M1153:426,443,455** remain separate from the orchestrator keys. **DBT:972–1026** retains the separate-main/worker topology and completion/exclusion assertions. |
| **N15 — extension blocks enrichment** | **CLOSED.** Precision-only synchronization bypasses coverage revalidation at **M1155:671–709,722–742**, while checking the restated precision. **DBT:1460–1481** retains the validation-time snapshot and `extended` assertion. |
| **P2 — operational overclaims** | **CLOSED.** FK effects, routine-runner writes, per-file atomicity and recovery remain accurately described at **M1153:114–139**, consistent with **MT:733,747–755,777,789–832**. |

The prior minor refusal wording is corrected at **M1153:66–70; M1154:29**: it now distinguishes family advisory locks from tuple-lock waits.

**New defects**

**N18 — P1: chart context can switch after substrate locks have been acquired. Residual N13/N2.**

`ka_gochara_lock_chart` accepts any non-NULL UUID, acquires its key, and overwrites `gochara5.chart`. It never compares the requested chart with an existing transaction binding (**M1153:413–428**). The substrate guard returns immediately whenever `chart_locked = 'on'` (**535–536**).

Let **C** be the canonical chart and **D** another UUID with a different family key. Let **Y** be a new contact identity under a committed physical object.

| Step | Transaction A | Transaction B |
|---|---|---|
| 1 | Mutates an existing candidate contact; holds C. | |
| 2 | | Declares context D using the documented `set_config` entry point, then inserts Y. Its statement trigger acquires D; the identity insertion succeeds. |
| 3 | Inserts Y with `ON CONFLICT DO NOTHING`; waits for B’s uncommitted identity. | |
| 4 | | Inserts Y’s ledger row for canonical chart C. **M1153:1094** requests C and waits for A. |

The cycle is **A → B’s transaction → C → A**. PostgreSQL unique checking waits for an uncommitted conflicting insertion to resolve. [PostgreSQL unique-index checks](https://www.postgresql.org/docs/17/index-unique-checks.html).

The schedule uses the documented context setter and ordinary table writes, with canonical chart IDs in all ledger rows. No manual alteration of `chart_locked` is required. The canonical-chart CHECK does not prevent it: the ledger row actually names C.

The same context switch recreates the sky-event tuple variant: B updates the event while holding D; A holds C and waits for that event; B subsequently requests C.

**DBT:1197–1227** tests both transactions using the same context. It does not test a mismatched context or refusal to switch charts. The implemented protection therefore depends on a caller convention where the ruling requires structural prohibition.

**N19 — P1: finite BC/AD horizons collide, permitting an incompatible generation to seal. Residual N14/N10.**

The finite predicate accepts both of these nonempty, bounded horizons:

| Horizon | Lower bound | Upper bound |
|---|---|---|
| H_AD | `2025-03-01 00:00:00+00 AD` | `2025-04-01 00:00:00+00 AD` |
| H_BC | `2025-03-01 00:00:00+00 BC` | `2025-04-01 00:00:00+00 BC` |

Use `[)` bounds for both, with identical convention and relations.

The formatter at **M1155:366–368** uses `YYYY` without an era token. PostgreSQL’s `YYYY` implementation converts BC years to their positive era-year number; era output is handled separately. [PostgreSQL formatting implementation](https://raw.githubusercontent.com/postgres/postgres/REL_17_STABLE/src/backend/utils/adt/formatting.c).

Both therefore encode these bounds:

```json
{
  "lower": "2025-03-01T00:00:00.000000Z",
  "lower_inc": true,
  "upper": "2025-04-01T00:00:00.000000Z",
  "upper_inc": false
}
```

The inverse at **M1155:390–399** interprets those strings as AD, so H_BC also fails round-trip preservation.

A complete sealing counterexample is:

1. Create a valid AD record, AD window and membership. The window’s class partition uses H_AD; the record’s separate partition covers its March AD support.
2. Change only the class partition’s `completed_horizon` to H_BC.
3. Publish and seal.

The inherited coverage column permits that update: [1081:225–248](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2765f/platform/migrations/1081_nirmana_l3_gochara_ledger_coverage_publication.sql:225). H_BC passes the new finite predicate. Its facts equal the stored AD facts, so **M1156:522** returns `identical` before testing containment. The record’s partition is unchanged. The membership predicate reads the unchanged AD snapshots and reports no violation. Consequently **M1153:905–920** permits sealing although the window’s current coverage contains none of its AD interval.

This is an accepted-domain correctness defect. **DBT:1484–1551** covers ordinary AD timestamps and unsupported infinities, but no era distinction.

**Ranked amendments**

**Merge-blocking**

1. **P1 — N19/N14/N10: preserve timestamp era in coverage facts and their inverse.** Keep the steward’s finite-horizon restriction, but make serialization lossless throughout that accepted domain. Add BC/AD inequality and round-trip tests, plus valid AD consumer → BC coverage replacement → `incompatible` → seal refusal.

2. **P1 — N18/N13/N2: bind the transaction to one supported chart before substrate acquisition.** Reject a different chart before requesting another family key. Under the existing canonical-only scope, enforcing that scope at the context/lock boundary is sufficient; retain the dedicated keys. Add mismatched-context and chart-switch tests for both unique-entry and sky-event tuple schedules, with the main connection retaining its orchestrator locks.

If any reviewed migration has already been applied, corrections must use forward migrations.

**Post-merge follow-up — non-blocking**

- **P3:** Update the static suite’s stale “round 5” label at **ST:128**. It does not affect execution.

**What I could not verify**

Completed independent checks include byte correspondence of **17 reviewed files** to the requested commit, all **five** embedded/standalone preflight comparisons, and exact preservation of **eight** relevant guard/helper functions from round 5.

- No database was contacted. Migrations, database tests, concurrency schedules and protected deployment were not executed.
- Production privileges, applied migration hashes, deployment approvals and actual lock timing remain unverified.
- I could not establish that migrations 1153–1157 have never been applied anywhere.
- Live PR-body and check-result verification was unavailable: the GitHub connector required approval, which this session’s policy disallowed. The rulings were assessed from the user’s binding instructions and corresponding migration comments.

No files were created or modified, no git write commands were run, and neither prohibited directory was accessed.