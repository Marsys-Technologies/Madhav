---
artifact: SIDDHANTA_GATE_PACKET_DB6
canonical_id: SIDDHANTA_GATE_PACKET_DB6
version: 1.0
status: PRE-SCORED — awaiting independent Gate-Executor verification
created: 2026-08-08
campaign: SIDDHANTA (arc-finishing run)
governing: PRODUCTION_GATE_EXECUTION_POLICY_v1_0.md (v1.1, in-session fresh-context dispatch)
head: 7594107b7
base: main @ ab4feb310
---

# Gate Packet — DB6 / DB12

**The builder swarm produced this packet and does NOT execute the gated action.**
An independent fresh-context Gate-Executor re-derives every condition below from
observed git/CI/DB state, never from this packet's self-report.

---

## §1 — SCOPE CORRECTION (read this first)

The arc charter assumed this packet would carry "v3 engine + mi_adhilepa fix +
DB6". **That is wrong, and the correction reduces risk.** PR #1099 already
squash-merged Phase 1+2 to main. Verified by content diff, not by commit log
(the commit list is misleading because #1099 was squashed):

| Component | Already on main? | Evidence |
|---|---|---|
| bo_pratijna v3.0 engine | **YES** | shipped in #1099 |
| mi_adhilepa leakage repair | **YES** | shipped in #1099 |
| migration 548 | **YES** | `git ls-tree main` lists it |
| migration 549 | **YES** | `git ls-tree main` lists it |
| **DB6 fix** | **NO** | `git show main:...bo_pratijna.py \| grep -c _load_fact_key_map` → 0 |
| **DB12 test fix** | **NO** | new in 7594107b7 |

**True divergence — 3 files, +279/-9 lines:**

```
00_ARCHITECTURE/briefs/siddhanta/SIDDHANTA_STATE.md      |  38 ++-
platform/.../writers/bo_pratijna.py                      |  60 ++++-
platform/.../writers/tests/test_bo_pratijna.py           | 190 +++++++++-
```

**NO MIGRATION RIDES THIS GATE.** No schema change, no DB-write at deploy.
This is a pure code + test change.

---

## §2 — What DB6 is

`bodha_msr_signals.constituent_facts_array` stores **fact_id digests**
(16-hex, e.g. `012f55cebed7f5a0`), not fact_keys. `_match_signal_to_class`
tested bhava/karaka/divisional patterns (`house_7`, `venus`, `d9`) against
those opaque digests, so it **matched nothing**. Every occurrence and condition
weight came out 0.0 — which is why every v3 skill score was numerically zero
(~1e-16) and `condition_grade` was 0.000 everywhere (DB7).

Fix: dereference each fact_id through `chart_facts` to its `fact_key` before
pattern matching (§N.5 — L1 is the authority; an L2 signal REFERENCES the L1
fact and must follow that reference, never restate or guess it).

---

## §3 — Pre-scored gate conditions

| # | Condition | Score | Evidence |
|---|---|---|---|
| G1 | Failing test written BEFORE fix (TDD) | **PASS** | RED run recorded: property test listed **all 21** non-provisional event classes as unreachable from their own declared primary bhava |
| G2 | Tests green after fix | **PASS** | 42 passed, 0 skipped, with live `DATABASE_URL` |
| G3 | Negative cases present and non-vacuous | **PASS** | `test_unrelated_fact_key_still_does_not_match` and `test_unresolvable_fact_id_does_not_crash` passed BOTH before and after the fix |
| G4 | R13 no-fitting: zero weight/threshold changes | **PASS** | diff shows exactly ONE logic line replaced; zero changes to any `sal *` weight, `_PROMISED_FLOOR`, `_DENIED_CEIL`, `_MIN_SALIENCE`, or grade normalization |
| G5 | Live-data verification (read-only) | **PASS** | chart 482012f1, 4,000-signal sample: 139,471 fact_ids resolved; **21/21** non-provisional classes now match (was 0/21) |
| G6 | DB7 falls with DB6 | **PASS** | condition weights nonzero for **20 of 21** classes (exception: `separation`, see DB11) |
| G7 | No regression from DB6 | **PASS** | full writer+L2 sweep: every failure/error traced to `DATABASE_URL` absence or the pre-existing missing `bodha_graph` table; `bo22.py` has **0** references to `bo_pratijna` |
| G8 | DB12 detector mutation-proven | **PASS** | after comment-stripping, a REAL gate in executable SQL is still detected; a comment-only occurrence no longer fires |
| G9 | No migration in packet | **PASS** | `git diff --name-only main HEAD` → no `.sql` files |
| G10 | CI green on PR | **PENDING** | Gate-Executor must observe every required check `status=COMPLETED` + SUCCESS |

---

## §4 — Rollback

Pure code revert; no schema change to unwind.
`git revert 20121a154 7594107b7` restores prior behavior exactly.
Prior behavior is *known-broken* (all-zero skill scores), so rollback restores a
defective-but-stable state, not a good one.

---

## §5 — Honest residuals NOT fixed here (R13 forbids riding along)

| ID | Finding | Why not fixed here |
|---|---|---|
| **DB10** | Bhava pattern `house_1` substring-matches `house_10`/`11`/`12` | Pre-existing matcher-semantics bug. Fixing it changes results beyond the mechanical repair; R13 forbids it riding along. Recorded with evidence. |
| **DB11** | `separation` `cond_sum = 0.00` in the 4,000-signal sample | **R16 scope-stated:** this is a sample-scoped observation, NOT a defect claim. Must be re-checked against the full post-rebuild data before any conclusion. |
| **DB13** | `relation "bodha_graph" does not exist` → 3 `test_bo22.py` failures | Pre-existing schema/test drift, unrelated to this packet (0 `bo_pratijna` references). |

---

## §6 — What the Gate-Executor must independently re-derive

Do not trust §3. Re-derive each of these yourself:

1. `git diff --stat main HEAD` — confirm 3 files, no `.sql`.
2. `git show main:platform/python-sidecar/pipeline/orchestrator/writers/bo_pratijna.py | grep -c _load_fact_key_map` — must be 0 (proves DB6 is genuinely new).
3. Run the test suite yourself with a live `DATABASE_URL`.
4. Confirm every required CI check on the PR is `COMPLETED` + SUCCESS. A null conclusion is PENDING, never PASSED.
5. Confirm no weight/threshold constant changed, by reading the diff — not by trusting G4.
