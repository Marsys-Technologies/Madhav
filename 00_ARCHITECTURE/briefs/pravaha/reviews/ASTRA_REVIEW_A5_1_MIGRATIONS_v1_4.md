---
artifact: ASTRA_REVIEW_A5_1_MIGRATIONS
version: "1.4"
reviewer: "Codex gpt-6-astra"
date: "2026-09-30"
verdict: REJECT
reviewed_commit: 09a840d7c
authority: "Review only; authorizes nothing."
---

**Verdict: REJECT**

The corrected family keys resolve the runner’s main/worker self-block. The enrichment fix also closes N7/N15. Three merge blockers remain: a permitted mixed-write deadlock, candidate updates that invalidate window membership without preventing sealing, and a coverage encoding collision that misclassifies incompatible coverage as identical.

These affect execution and persisted correctness; they are not minor post-merge amendments. This review accepts the corrected steward ruling and does not require restoring legacy-table business triggers, the definition verifier, replay GUC, or family-wide migration atomicity.

HEAD is `09a840d7c620694e855233d5254884a1d96115f4`. “CLOSED” means closed at source-review level. The counterexamples below are derived from source and PostgreSQL semantics, not executed against a database.

**Closure table**

Evidence abbreviations identify files; numbers identify lines:

- **M1153:** [sky-event substrate](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2765e/platform/migrations/1153_gochara_sky_event_substrate.sql); **M1154:** [rule-path registry](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2765e/platform/migrations/1154_gochara_rule_path_registry.sql).
- **M1155:** [relationship records](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2765e/platform/migrations/1155_gochara_relationship_record.sql); **M1156:** [evaluation windows](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2765e/platform/migrations/1156_gochara_eval_window.sql).
- **DBT:** [database tests](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2765e/platform/tests/integration/gochara_a5_1_migrations.db.test.ts); **URL:** [disposable-database resolver](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2765e/platform/tests/integration/gochara_a5_1_disposable_url.ts).
- **MT:** [migration runner](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2765e/platform/scripts/migrate.ts); **DY:** [deployment workflow](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2765e/.github/workflows/deploy.yml).

| Open finding | Judgment | Evidence and disposition |
|---|---|---|
| **N2 — locking and isolation protocol** | **PARTLY CLOSED** | READ COMMITTED enforcement remains at **M1153:360,378,394**. Dedicated keys and statement guards fix the identified ownership and chart-table tuple-order defects. Mixed substrate/chart transactions still admit a cycle, detailed below. |
| **N7 — dependent precision becomes stale** | **CLOSED** | Precision propagation remains at **M1155:825–849**. Precision-only synchronization bypasses coverage revalidation at **M1155:668–701**, while still checking the contact’s precision at **M1155:738–743**. **DBT:1335–1356** now covers actual extend-then-enrich after sealing. |
| **N10 — coverage binding and applicability** | **PARTLY CLOSED** | Stored facts, drift classification and seal refusal are implemented at **M1155:347**, **M1156:431**, **M1153:805**. Contributor applicability is checked at **M1156:389**, but only on membership INSERT (**M1156:517–519**). Candidate parent updates bypass it; see **N16**. Encoding also remains unsound for permitted infinities; see **N17**. |
| **N12 — worker waits on its scheduler** | **CLOSED** | Family keys at **M1153:370,386,398** replace orchestrator keys. **DBT:929–983** uses separate main, worker and competing connections, keeps both main-session locks held, and checks worker completion and family exclusion. This addresses the real connection-ownership topology. |
| **N13 — transaction and tuple-lock inversions** | **PARTLY CLOSED** | Markers reject registry/chart mixing at **M1153:367,382**. Statement guards at **M1153:448–465** fix the former chart-table UPDATE/DELETE inversion, exercised at **DBT:1062–1109**. Tables expressly permitted to share those transactions without a family key still create cycles. |
| **N14 — coverage serialization collisions** | **PARTLY CLOSED** | JSON preserves empty/unbounded distinctions, NULL elements and element boundaries at **M1155:353–370**; the original three cases are covered at **DBT:1359–1384**. Explicit timestamp infinities still collide; see **N17**. |
| **N15 — coverage extension blocks enrichment** | **CLOSED** | **M1155:671–701,714–734** omit coverage revalidation for precision-only synchronization. The sealed validation-time snapshot remains unchanged; **DBT:1335–1356** specifically checks extension, enrichment, retained snapshot and `extended` classification. |
| **P2 — operational overclaims** | **CLOSED** | **M1153:78–103** now distinguishes retained FK effects, routine-runner writes, per-file atomicity, predecessor requirements and partial-window recovery. These match **MT:733,747,777,798,822–832** and the corrected PR description. A separate minor locking-wording issue is noted below. |

The round-4 closures remain intact:

| Previously closed finding | Reconfirmation |
|---|---|
| **N1 — legacy publication trigger** | **CLOSED.** Governed-generation predicate **M1153:348–350**; explicit seal rejects legacy generations before locking at **M1153:835–839**. No publication business trigger was restored. |
| **N3 — protected deployment route** | **CLOSED.** Protected job **DY:952**, exact file list **DY:1056**, invocation/revocation **DY:1067–1070**, routine refusal **MT:146–152,798**. |
| **N4 — verifier/replay design** | **CLOSED.** Presence checks remain at **M1153:1090,1154,1181**; tracked files are hash-checked/skipped at **MT:789–795**. All five embedded preflights match their standalone copies. |
| **N5 — rule membership/seal race** | **CLOSED.** Membership mutations acquire global EXCLUSIVE before checking the seal at **M1154:466–475**; rule sealing uses that guard at **M1154:520–523**. Consumers acquire global SHARED before checking at **M1154:481–492**. |
| **N6 — conflicting readings for one contact identity** | **CLOSED.** Canonical-chart restriction **M1153:920–921**, chart locking **M1153:980**, cross-generation solved-reading checks **M1153:1015–1028**. |
| **N8 — prerequisite reparenting** | **CLOSED.** Scope immutability and result-only updates at **M1155:430–440**, applied to prerequisites at **M1155:883–886**. |
| **N9 — published membership changes** | **CLOSED.** Sealed-generation INSERT refusal **M1155:421–425**, membership UPDATE refusal **M1155:434–436**, window-membership guard installation **M1156:512–515**. N16 concerns pre-seal parent mutation, not reopening sealed membership. |
| **N11 — disposable URL targeting** | **CLOSED.** Query restrictions, driver parsing and explicit target validation remain at **URL:71–111**, unchanged from round 4. |

**Lock design**

The dedicated transaction keys are appropriate for the frozen runner’s separate connections. The main connection holds orchestrator locks while workers use their own connections: [runner.py:682](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2765e/platform/python-sidecar/pipeline/orchestrator/runner.py:682), [runner.py:753](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2765e/platform/python-sidecar/pipeline/orchestrator/runner.py:753), [runner.py:1092](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2765e/platform/python-sidecar/pipeline/orchestrator/runner.py:1092). The revised database test models that ownership correctly, although it does not invoke the Python runner end to end.

The advisory-only ordering also addresses the former C/G cycle: chart writers take chart EXCLUSIVE before global SHARED; registry mutations take global EXCLUSIVE and cannot mix with chart mutations; sealing takes chart EXCLUSIVE.

**Residual N13 — P1: ordinary substrate writes can invert that order through unique or tuple locks.**

Contact identities deliberately take no family key, and the migration explicitly permits inserting them beside ledger rows (**M1153:701–708**). The fixture helper does exactly that, identity first (**DBT:452–455**).

Let **C** be the canonical chart family key and **Y** a new identity under an already committed physical object:

| Step | Transaction A | Transaction B |
|---|---|---|
| 1 | Mutates an existing candidate contact; holds **C**. | |
| 2 | | Inserts identity **Y**; leaves the transaction open. No family key is acquired. |
| 3 | Inserts the same **Y** with `ON CONFLICT DO NOTHING`; waits for B’s uncommitted unique-key entry. | |
| 4 | | Inserts Y’s valid contact-ledger row; its guard waits for **C**, held by A. |

This is **A → B’s transaction → C → A**. PostgreSQL unique checking waits for an uncommitted conflicting insertion to resolve. [PostgreSQL unique-index checks](https://www.postgresql.org/docs/17/index-unique-checks.html).

Relevant implementation: identity uniqueness **M1153:685–698**, no-lock normal identity insertion **M1153:715–716**, and contact-family acquisition **M1153:980**. Neither transaction mixes registry mutations with chart writes or violates the implemented C→G order.

There is also a direct **tuple-lock** variant:

1. A holds C through a contact mutation.
2. B performs an allowed sky-event UPDATE and retains its row lock.
3. A updates that same sky-event row and waits for B.
4. B performs a contact mutation and waits for C.

Even `SET longitude = longitude` passes the sky-event guard. That guard takes no family key (**M1153:630–677**). Conflicting UPDATEs retain row locks until transaction end. [PostgreSQL row-level locking](https://www.postgresql.org/docs/17/explicit-locking.html#LOCKING-ROWS).

The main connection may retain both orchestrator locks throughout either schedule. Those locks do not break these worker-level cycles.

These schedules cause deadlock/timeout aborts, rather than demonstrating committed corruption. They nevertheless defeat the asserted deadlock-free protocol. **DBT:929** starts the worker with a chart-table DELETE and pre-existing identities; **DBT:1062** exercises chart-table mutations. Neither covers these mixed-write entry orders.

**New defects**

**N16 — P1: candidate parent updates invalidate existing window membership, and sealing accepts it.**

Membership applicability checks convention, searched relation and support horizon at **M1156:409–423**. Its trigger runs only on membership INSERT (**M1156:517–519**).

Candidate records/windows remain updateable (**M1155:429–449**). The window UPDATE guard validates only its own coverage facts and interval (**M1156:347–381**). Neither it nor the drift classifier revalidates existing contributors.

A permitted sequence is:

1. Create a conjunction record **R**, validated against `body_target/mars:karaka`.
2. Create same-class window **W**, whose class coverage searched conjunction and aspect, and insert valid R→W membership.
3. Change W’s class coverage to `relations_searched = ARRAY['aspect']`.
4. Update candidate W’s `coverage_facts` to the freshly computed facts of that class partition.
5. Publish and seal.

The window’s own coverage guard passes. R’s body-target coverage is unchanged. Both consumers therefore classify as `identical` at **M1156:455**, while the existing conjunction membership is now inapplicable.

All membership FK scope fields remain unchanged. The classifier enumerates records/windows without checking membership (**M1156:441–475**), and the seal only rejects its `incompatible`/`partition_missing` results (**M1153:805–810**).

**DBT:1439–1453** tests invalid membership insertion, not valid insertion followed by parent mutation. The invariant must also survive updates to existing contributors and windows.

**N17 — P1: explicit timestamp infinities still produce indistinguishable coverage facts.**

At **M1155:357–363**, explicit bounds are formatted with `to_char`. PostgreSQL distinguishes an omitted range bound from a timestamp bound whose value is `infinity`; `lower_inf`/`upper_inf` identify the former. PostgreSQL’s timestamp formatter returns SQL NULL for non-finite timestamps. [Range infinity semantics](https://www.postgresql.org/docs/17/rangetypes.html#RANGETYPES-INFINITE), [timestamp formatting implementation](https://raw.githubusercontent.com/postgres/postgres/REL_17_STABLE/src/backend/utils/adt/formatting.c).

For identical convention and relation arrays, these permitted, nonempty ranges consequently encode identically:

| Horizon | Meaning |
|---|---|
| `tstzrange('-infinity','infinity','[]')` | Includes every finite timestamp. |
| `tstzrange('infinity','infinity','[]')` | Contains only positive infinity. |

Both produce:

```json
{
  "empty": false,
  "lower": null, "lower_inf": false, "lower_inc": true,
  "upper": null, "upper_inf": false, "upper_inc": true
}
```

The inherited coverage table permits these values: [1081:234](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2765e/platform/migrations/1081_nirmana_l3_gochara_ledger_coverage_publication.sql:234). The new guards impose no finite-bound restriction.

After validating a finite consumer under the first horizon, changing coverage to the second leaves its facts equal. **M1156:455** reports `identical`, and **M1153:805** permits sealing although coverage contains no finite instant.

The inverse at **M1155:383–395** also reconstructs NULL formatted bounds as unbounded bounds, so this encoding does not round-trip. **DBT:1359–1384** covers omitted bounds and ordinary finite timestamps, not explicit subtype infinities.

**Minor, non-blocking wording issue:** **M1153:64–65,428–430** says refused statements never wait. Row-level refusals can still wait for PostgreSQL tuple acquisition before their trigger runs. The accurate claim is that those guards refuse before acquiring a *family advisory lock*. This wording correction alone would not justify rejection.

**Ranked merge-blocking amendments**

1. **P1 — Preserve contributor applicability across candidate mutations, N16/N10.** Revalidate existing memberships when relevant record/window facts change, or enforce the complete invariant at a deferred/seal boundary. Add valid-membership → parent-update → seal tests covering relation, convention and support horizon. No legacy-table trigger is required.

2. **P1 — Complete transaction ordering across substrate and chart writes, N13/N2.** Ensure a transaction that will write chart data obtains the necessary family lock before acquiring mixable substrate tuple/unique locks, or structurally prohibit the conflicting mixed order. Retain the corrected keys and registry separation. Test both schedules above with the main connection holding its session locks.

3. **P1 — Make coverage encoding unambiguous over the accepted domain, N17/N14.** Preserve explicit positive/negative infinity separately from omitted bounds, or reject unsupported horizons at the relevant consumer boundaries. Test round-trip behavior and full-horizon → positive-infinity-singleton drift; the latter must not classify as identical or pass sealing.

The refusal wording can be handled as a non-blocking follow-up. Applied migration files must remain immutable: if any reviewed hash has already been applied, corrections require forward migrations.

**What I could not verify**

- No database was contacted. I did not execute migrations, concurrency schedules, integration tests or the protected deployment workflow.
- The PR’s reported PostgreSQL 15/17 and test-suite results were inspected as author-reported evidence, not independently reproduced.
- Production ownership, privileges, ledger state, deployment approvals, capability revocation and actual lock timing remain unverified.
- I could not establish that migrations 1153–1157 have never been applied anywhere.
- Independently completed checks include correspondence of 19 reviewed files to the requested commit, all five embedded/standalone preflight comparisons, and source/control-flow inspection. These do not constitute database acceptance.

No files were created or modified, no git write commands were run, and neither prohibited directory was accessed.

