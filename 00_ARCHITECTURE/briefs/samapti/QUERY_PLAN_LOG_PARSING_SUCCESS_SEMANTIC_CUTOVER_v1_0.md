---
artifact: QUERY_PLAN_LOG_PARSING_SUCCESS_SEMANTIC_CUTOVER
canonical_id: QUERY_PLAN_LOG_PARSING_SUCCESS_SEMANTIC_CUTOVER
version: 1.0
status: LIVING — PENDING (semantic cutover not yet merged to origin/main; fields below are placeholders until it lands)
date: 2026-07-30
authored_by: SAMĀPTI / B-DOCS-GOVERNANCE (Scribe), per DVA Ruling 27
governing: 00_ARCHITECTURE/briefs/samapti/SAMAPTI_DVARAPALA_LEDGER.md — Ruling 27 (B-N8-TS-SERVE)
---

# `query_plan_log.parsing_success` — semantic cutover marker

## §0 — Why this file exists

`query_plan_log.parsing_success` is a **persisted** column (`platform/migrations/001_baseline.sql`,
`BOOLEAN NOT NULL DEFAULT TRUE`), not a computed/derived value. DVA Ruling 27 found that
`platform/src/app/api/chat/consult/route.ts` writes the literal `parsing_success: true`
unconditionally on every write — the original false-green in its purest form: the column has never,
to date, recorded whether parsing actually succeeded, only that a plan write happened at all.

Lane `B-N8-TS-SERVE` (branch `samapti/n8-ts-serve`, PR #909) fixes this to the correct product
semantic — `parsing_success` becomes true only when the plan **parsed cleanly on the first attempt**,
not merely "a plan exists." That fix was independently re-derived and marked **CONFIRMED** by the
persistent SAMĀPTI Verifier (see `SAMAPTI_VERIFICATION_LEDGER.md` — `## B-N8-TS-SERVE — CONFIRMED`),
but **as of this note's authoring, PR #909 had not yet merged to `origin/main`** — confirmed directly:
`origin/main`'s `consult/route.ts:711` still reads the hardcoded literal `parsing_success: true`, and
`platform/migrations/001_baseline.sql`/the `_pre_squash_schema_snapshot.psql` carry no comment marking
a semantic change. Per Ruling 27 and CLAUDE.md's no-fabrication discipline (§I B.10), this note
**cannot** state a merge date or commit SHA that does not yet exist — the fields below are explicit
placeholders, not filled in from evidence.

## §1 — The semantic change (mechanical description)

| | Before the cutover (current `origin/main` state) | After the cutover (once PR #909 merges) |
|---|---|---|
| What `parsing_success = true` means | "A `query_plan_log` row was written." (Tautological — always true, hardcoded.) | "The planner parsed this query's plan cleanly, on its first attempt." |
| What `parsing_success = false` means | Never occurs (no code path can produce it). | The planner's first-attempt parse failed (a real, meaningful signal). |
| Historical rows (written before the cutover) | All read `true`, unconditionally. | **Still all read `true`** — the column is not backfilled or reinterpreted retroactively; old rows continue to assert the tautology they were written under. |

**The hazard this note exists to mark (Ruling 27's "finding nobody asked about"):** because the column's
*meaning* changes at the cutover point while its *stored values* do not change retroactively, any
query spanning the cutover boundary silently mixes a tautology (pre-cutover rows, where `true` proves
nothing) with a real measurement (post-cutover rows, where `true` is earned). A future calibration or
L5 pass computing e.g. "planner first-parse success rate" without excluding pre-cutover rows will get
a number contaminated by rows that could never have read `false`.

## §2 — Cutover marker (PENDING — fill in at merge time)

- **Cutover date:** *PENDING — not yet merged as of 2026-07-30.*
- **Merge commit SHA (on `origin/main`):** *PENDING.*
- **Evidence as of this note:** branch `samapti/n8-ts-serve`, PR #909 ("fix(samapti/n8-ts-serve): earn
  four TS serving-layer signals (F-20, F-22, F-23, F-24)"), HEAD `b480d87b` (per `git worktree list`),
  VER verdict `CONFIRMED` (`SAMAPTI_VERIFICATION_LEDGER.md`).

**Action required at merge time** (for whoever holds MERGE-LOCK when this PR integrates, or for
`E1-SAMGATI` if this note is still unfilled at terminal close):
1. Fill in the cutover date + merge commit SHA above.
2. Add a one-line SQL comment at the column's definition site
   (`platform/migrations/001_baseline.sql`, the `parsing_success` line inside `CREATE TABLE
   query_plan_log`) pointing back to this file and the cutover SHA — e.g.
   `-- parsing_success semantic cutover <SHA> <date>: see QUERY_PLAN_LOG_PARSING_SUCCESS_SEMANTIC_CUTOVER_v1_0.md;
   rows before this commit are tautological (always true), not a real parse-success measurement.`
   Do **not** edit the column's own `NOT NULL DEFAULT TRUE` — Ruling 27 explicitly declined a rename
   or default change as disproportionate to fix in this pass (see §3).
3. Update this file's `status` frontmatter from `LIVING — PENDING` to `LIVING — RESOLVED`.

## §3 — Residual, recorded not chased (per Ruling 27)

`parsing_success BOOLEAN NOT NULL DEFAULT TRUE` is itself a false-green generator independent of the
cutover: any future INSERT that omits the field silently yields `true`. `DEFAULT NULL` would be the
§N.8-correct shape, but Ruling 27 ruled this disproportionate to fix in the same pass given it is a
migration on a live table — recorded here as an open residual, not actioned by this note or by
B-N8-TS-SERVE.

## §4 — UI legibility note (per Ruling 27 item 2)

Ruling 27 also asks that any surface displaying this field say "clean first parse" rather than a bare
"parsed," so a reader does not read the pre-cutover tautological `true` values as meaning what the
post-cutover ones mean. This is a serving/UI-layer change belonging to whichever lane owns that
surface (not enumerated as touching this migration or this note); flagged here for cross-reference
only.

*End of QUERY_PLAN_LOG_PARSING_SUCCESS_SEMANTIC_CUTOVER v1.0.*
