---
finding: F-25
stream: S1 DVARA
class: CL-01 reachability
stage: S COMPLETE — code already written and pushed (adopted branch); this spec documents the
  already-built fix retroactively so VERIFIER has a COMPLETE REVIEW.md to gate on, per plan §9
  ("every LIVE lane must have REVIEW.md with verdict COMPLETE"). Thin by design — the branch
  IS the fix, this spec states root cause/files/exit test/coverage against it.
branch: par/s1-f25-dasha-sandhi-principal (origin, HEAD 134cc9de9) — worktree: reuse
  .claude/worktrees/ekv-a-25 (adopted, do not re-fork)
---

## 1. Root cause (one sentence, mechanism-level)

`register_all.ts`'s `registerAllKalaViews` called `registerDashaSandhiCalendar(server)` without
passing `principal` — the one outlier among 9 sibling `registerKala*Tool` calls in the same
function — so `dasha_sandhi.ts`'s handler fell back to a hardcoded
`{user_uid:'system', key_id:'system', role:'super_admin'}` placeholder that fails the
`/api/retrieval/capability` entitlement gate for every real caller, and the resulting auth failure
was swallowed into a generic `honest_empty` coverage row that reads as a data gap rather than an
auth bug.

## 2. Files changed (already committed, `134cc9de9`)

- `platform-mcp/src/tools/kala_views/dasha_sandhi.ts` — `registerDashaSandhiCalendar` signature
  gains `principal: Principal` as a second parameter; the handler closes over it instead of
  constructing the placeholder (diff: -1/+2 at the function signature and handler body, per the
  commit's own diff already inspected this session).
- `platform-mcp/src/tools/kala_views/register_all.ts` — the one call site updated:
  `registerDashaSandhiCalendar(server, principal)`.

No other files required — the fix is a two-line parameter-threading change matching the
already-correct pattern every sibling registration in the same file already used.

## 3. Exit test

No new automated test was added on the branch (confirmed: `git show 134cc9de9 --stat` lists only
the two `.ts` files above, no `__tests__` path). **Recommend VERIFIER add, or accept the live
reproduce_cmd as the exit test given TIER-1/cheap-to-verify status:**
```
mcp__marsys-jis-direct__kala_dasha_sandhi_get({chart_id:'482012f1-710e-4a25-994a-93821f5871aa'})
```
FAILS today (pre-merge, live-confirmed this session): `boundaries:[]`,
`coverage:[{state:'honest_empty', reason:'L1 dasha registry ... could not be dispatched'}]`.
PASSES once merged/deployed: `boundaries` non-empty, matching the sibling `kala_now_get`'s own
`dasha_sandhi` sub-field data for the same chart (cross-check already available in this session's
live `kala_now_get` call — its `dasha_sandhi.bands` array is populated for the same chart/date,
proving the underlying `chart_dashas` data is present and the defect is purely the entitlement
failure, not a data gap).

## 4. Sibling sites covered

All 9 `registerKala*Tool` calls in `register_all.ts` were read during this session's rebase; the
other 8 already pass `principal` correctly — `registerDashaSandhiCalendar` was the sole outlier.
No further sibling sites in this file. Not audited: whether any MCP tool registration elsewhere in
the codebase (outside `kala_views/*`) has the same "principal dropped, placeholder substituted"
pattern — out of this finding's CL-01 scope, flagged as an open census item, not blocking.

## 5. Recurrence guard

None added on the branch. **Recommended, not yet built:** a lint/contract test asserting every
`register*Tool(server, ...)` call inside `registerAllKalaViews` passes `principal` as its second
argument — would have caught this mechanically. Flagged for VERIFIER's judgment on whether to
require it before COMPLETE, given the finding is TIER-1/already-fixed and the guard would be new
scope beyond the adopted branch's own diff.

## 6. Dependencies and rollback

No dependency on other lanes. This branch also carries `ekv/b-08-ranker` and
`ekv/b-09-rebuild-runbook`'s commits (shared history from the original `ekv/a-25-…` branch, per
this session's earlier rebase note in `DIAGNOSIS.md` §5) plus an unrelated
`CAMPAIGN_COORDINATION.md` diff — INTEGRATOR should decide at merge time whether to cherry-pick
just the F-25 commit (`134cc9de9`) or land the whole branch; this spec covers only the F-25 commit
itself. Rollback: revert `134cc9de9`; behavior reverts to today's silent-auth-failure state — no
risk to any other currently-working tool (the two changed files are `dasha_sandhi.ts`/
`register_all.ts`, touched by no other in-flight S1/S2 lane this session).

## 7. Sub-claim coverage table

| D-2 sub-claim (from DIAGNOSIS.md §2) | Spec element that closes it |
|---|---|
| "dropped Principal at tool registration causes every dispatch to fail authorization" | §2: `register_all.ts` now passes the real `principal` |
| "failure is silently reported as honest-empty, masking an auth bug as a data gap" | §2: `dasha_sandhi.ts`'s handler no longer manufactures a failing placeholder identity, so the entitlement check now runs against the real caller and either succeeds or produces a real, attributable error — not addressed by a NEW honesty layer, but by removing the cause of the false honest-empty in the first place |
| "proven by sibling kala_now_get serving the identical data" | §3: exit test's cross-check against `kala_now_get`'s own `dasha_sandhi` field for the same chart |
