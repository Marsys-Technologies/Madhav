---
artifact: VERIFY_RC-12.md
residual: RC-12 (R-7) — authorizeChartAccess Rule-1 hardening
branch: res/rc12-authz-hardening
commit_verified: e7934363
verifier: independent VERIFIER agent (did NOT implement)
verdict: ACCEPT
date: 2026-07-22
---

# RC-12 Independent Verification — VERDICT: ACCEPT

## Residual DONE bar (brief §E RC-12, verbatim)

> **RC-12 (R-7) — `authorizeChartAccess` Rule-1 hardening.** super_admin is
> granted any `chart_id` without an existence check first. Add the existence
> check so a non-existent chart_id is rejected even for super_admin (defense
> in depth; pre-existing, carried since W0). **DONE:** super_admin request
> for a non-existent chart_id returns a clean not-found, not a silent grant;
> regression test; existing super_admin flows unaffected.

## (a) Test suite — rerun by verifier (not trusted from report)

Ran in worktree `.claude/worktrees/wf_2c9867fc-2f8-4` (branch checked out at `e7934363`), node_modules symlinked to main platform install.

- `npx vitest run src/lib/auth/__tests__/authorize_chart_access.test.ts` → **7 passed (7)**, 1 file passed.
- Downstream consumers `src/lib/pipelines/shared/__tests__/auth_and_chart.test.ts` + `src/lib/gateway/__tests__/gateway.test.ts` → **6 passed (6)**, no regressions.
- `npx tsc --noEmit` → no `error TS` lines anywhere; zero errors touching the changed files.

**Adversarial: does the new regression test actually guard the bug?** Swapped in `main`'s (unfixed) `authorizeChartAccess.ts` and reran the branch's test file:
```
× super_admin returns 'deny' (not a silent grant) for a non-existent chart_id
AssertionError: expected 'all' to be 'deny'
Tests  1 failed | 6 passed (7)
```
The new test fails against the pre-fix source with exactly the silent-grant symptom (`'all'` where `'deny'` is required), and passes against the fix. The test is a genuine guard, not a tautology. Branch source restored after the check; worktree tracked files clean.

## (b) DONE bar checked verbatim vs implementation

- **"super_admin request for a non-existent chart_id returns a clean not-found, not a silent grant"** — MET. The Rule-1 branch now runs `SELECT owner_id FROM charts WHERE id=$1` and returns `existsRes.rows[0] ? 'all' : 'deny'` (`authorizeChartAccess.ts:53-60`). `'deny'` is the function's established not-found shape — the brief itself frames Rule-4 `'deny'` as "the clean not-found every other role already gets." Both live consumers map `'deny'` to a refusal: consult route → `res.forbidden()` (`consult/route.ts:367-369`); MCP primitives → entitlement-denial envelope, HTTP 401 (`primitives/[tool]/route.ts:195-203`). No silent grant reaches downstream.
- **"regression test"** — MET. New test `"super_admin returns 'deny' (not a silent grant) for a non-existent chart_id"` added; proven above to fail on unfixed source. The prior test (which asserted `'all'` against an empty DB — i.e. encoded the bug) was correctly renamed/repointed to `"super_admin returns 'all' for an existing chart"` with an owner row present.
- **"existing super_admin flows unaffected"** — MET. Only behavior delta is super_admin + non-existent chart (`'all'`→`'deny'`). super_admin against an existing chart still returns `'all'` (verified by test; logic: `rows[0]` truthy including `{owner_id: null}` → `'all'`). Rules 2–4 (owner match, chart_grants, default deny) are byte-for-byte unchanged; non-admin behavior is identical.

## (c) Likely failure mode — hunted

- **Incomplete sweep / bypass path:** grepped every consumer of `authorizeChartAccess` (16 non-test sites across consult, MCP primitives/writes/bundles/authz/prashna_ask, retrieval capability, gateway invoke_tool, chart-page-guard, pipelines auth_and_chart). All treat `'deny'` as refusal; none has a super_admin-specific branch that depended on `'all'` being returned for a non-existent chart. Chart-creation/build-start path does NOT call this gate (only its tests reference it), so no "read gate blocks creation of a not-yet-existent chart" regression.
- **Rule that bans the substitution:** N/A — this is an added existence check, not a tool substitution.
- **Null-owner edge:** an existing chart with `owner_id = null` → `rows[0]` truthy → `'all'` (chart exists), consistent with intent. Not a bypass.
- **Security direction:** the change only *tightens* (removes a grant); it opens no new access. No weakened control.

## (d) Scope / must_not_touch

`git diff --name-only main..HEAD` → exactly two files:
- `platform/src/lib/auth/authorizeChartAccess.ts`
- `platform/src/lib/auth/__tests__/authorize_chart_access.test.ts`

No FROZEN orchestrator / WriterBase, no `ga_*/bo_*/ka_*/ph_*/mi_*` writer logic, no `chart_facts` semantics, no D-4b branches / `kala_*` / gochara serving semantics. Within brief §E may_touch (`platform/**` + `retrieval_residual/**` for this report). Clean.

## Verdict

**ACCEPT.** All three DONE-bar clauses met; regression test is a proven guard; scope is minimal and touches no forbidden path; no bypass or downstream regression found.
