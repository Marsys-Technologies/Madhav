---
finding: F-25
stream: S1 DVARA
class: CL-01 reachability
disposition: BRANCH-EXISTS (adopt) — fix already written on ekv/a-25-dasha-sandhi-principal
stage: D COMPLETE (retroactive — code pre-exists; documenting for VERIFIER per plan §0 discipline)
---

## 1. Live reproduction (on main, pre-fix)

```
mcp__marsys-jis-direct__kala_dasha_sandhi_get({chart_id:'482012f1-710e-4a25-994a-93821f5871aa'})
```
Live result this session: `{"boundaries":[], "coverage":[{"concept":"dasha_sandhi_calendar",
"state":"honest_empty","reason":"L1 dasha registry (marsys://tool/L1/get_dashas) could not be
dispatched this call."}], ...}` — STILL REPRODUCES on main (fix not yet merged). Confirms the
finding is live and real, not stale.

## 2. Claim decomposition

Single assertion: "kala_dasha_sandhi_get is non-functional for all charts due to a dropped Principal
at registration, causing every dispatch to fail authorization and get silently reported as
honest-empty." Confirmed by the live repro above (the "could not be dispatched" honest-empty framing
is exactly the auth failure being swallowed, per the finding's own mechanism note).

## 3. Mechanism → file:line, and the fix already on the adopted branch

`platform-mcp/src/tools/kala_views/register_all.ts:64` (pre-fix) called
`registerDashaSandhiCalendar(server)` — omitting `principal`, unlike all 8 sibling
`registerKala*Tool(server, principal)` calls in the same function. `dasha_sandhi.ts:358-362` (pre-fix)
fell back to a hardcoded `{user_uid:'system', key_id:'system', role:'super_admin'}` placeholder that
fails the `/api/retrieval/capability` entitlement gate for real callers; the resulting error is
swallowed into the generic honest-empty coverage row.

**Adopted branch fix** (commit `134cc9de9` on rebased `ekv/a-25-dasha-sandhi-principal`, mirrored to
`par/s1-f25-dasha-sandhi-principal`): `registerDashaSandhiCalendar` now takes `principal: Principal`
as a second parameter and closes over it in the handler instead of constructing the placeholder;
`register_all.ts:64` now passes `registerDashaSandhiCalendar(server, principal)`. Diff matches the
finding's mechanism exactly — see this branch's own commit message for the full rationale.

## 4. Sibling census

All 8 sibling `registerKala*Tool` calls in `register_all.ts` already pass `principal` correctly (this
was the ONE outlier) — confirmed by reading the full function body during rebase; no further sibling
sites in this file. Not investigated: whether any other MCP tool registration elsewhere in the
codebase has the same "principal dropped, placeholder substituted" pattern — out of this lane's scope
(§2's CL-01 grouping is specific to `kala_views/*` registrations); flagging as a possible follow-up
census, not blocking this lane.

## 5. Blast radius / adoption housekeeping

- Rebase performed this session: `ekv/a-25-dasha-sandhi-principal` was 25 commits behind
  `origin/main` and 8 ahead; rebased clean except one unrelated governance bookkeeping commit
  (`47e3a6a54`, "conductor(sampurti): session close — R42 CLOSE", touching only
  `CURRENT_STATE_v1_0.md`/`SESSION_LOG.md`, zero code) — skipped as out-of-scope noise, not part of
  this finding's fix.
- Per repo git-safety discipline, the rebased history was NOT force-pushed over the existing
  `ekv/a-25-dasha-sandhi-principal` ref (that would rewrite a branch other swarm agents may be
  reading). Instead the rebased tip was pushed as a new branch:
  **`par/s1-f25-dasha-sandhi-principal`** (origin, HEAD `134cc9de9`) — this is the branch VERIFIER/
  INTEGRATOR should review and land, not the stale `ekv/a-25-…` ref.
- This branch also carries `ekv/b-08-ranker` and `ekv/b-09-rebuild-runbook`'s commits (shared branch
  history from the night run) plus a `CAMPAIGN_COORDINATION.md` diff — out of S1's scope to adjudicate;
  flagged for the conductor/INTEGRATOR to decide whether those ride along or get cherry-picked out at
  merge time.
- No control in the CL-00 battery currently exercises `kala_dasha_sandhi_get` directly (not
  investigated further this pass).

**Recommendation to VERIFIER: treat this as SPEC-equivalent (the commit message doubles as the spec)
and move straight to Stage R/V — re-run reproduce_cmd against the `par/s1-f25-…` branch in a fresh
worktree to confirm boundaries are non-empty before merge.**
