---
artifact: B-008 cockpit authorization sweep outcome (P2-B-008)
version: "1.0"
status: FIXED_AWAITING_INDEPENDENT_VERIFICATION
as_of: "2026-08-28T01:45:00Z"
session: "Claude Code session, P2 blocker B-008 coordinated cockpit authz sweep (test-driven, isolated worktree)"
relates_to:
  - 00_ARCHITECTURE/briefs/pariprashna_assurance/P2_BLOCKER_INTAKE_v1_0.md (P2-B-008 row)
  - 00_ARCHITECTURE/briefs/pariprashna_assurance/B007_COCKPIT_CLEAR_AUTHZ_OUTCOME_v1_0.md (sibling, same root cause)
  - platform/src/app/api/cockpit/runs/route.ts
  - platform/src/app/api/cockpit/atlas/sample/route.ts
  - platform/src/app/api/cockpit/atlas/schema/route.ts
  - platform/src/app/api/cockpit/refresh/route.ts
  - platform/src/app/api/cockpit/plan/route.ts
  - platform/src/app/api/cockpit/stats/route.ts
  - platform/src/app/api/cockpit/registry/route.ts
  - platform/src/app/api/cockpit/watchdog/route.ts (examined; deliberately UNCHANGED)
  - platform/src/lib/auth/requireChartPermission.ts (new)
  - platform/src/lib/auth/authorizeChartAccess.ts (the one authorization brain, unchanged)
  - PR https://github.com/Marsys-Technologies/Madhav/pull/1603
predecessors:
  - P2-B-001 — GET /api/charts/[id] cross-user PII read (PR #1597, MERGED)
  - P2-B-007 — cockpit Clear preview+execute cross-user delete (PR #1602, OPEN)
severity: P2 blocker — live production vulnerability (unauthenticated cross-tenant data dump + cross-user irreversible data deletion)
branch: pariprashna/p2-b008-cockpit-authz-sweep
merged: false
---

# B-008 cockpit authorization sweep outcome (P2-B-008) v1.0

## Verdict

**FIXED.** Eight routes across the `/api/cockpit/*` surface now enforce
authentication and, where the data is chart-scoped, per-chart authorization via
the same `authorizeChartAccess` brain used by B-001 and B-007. Landed on branch
`pariprashna/p2-b008-cockpit-authz-sweep` as PR
[#1603](https://github.com/Marsys-Technologies/Madhav/pull/1603), **deliberately
not merged** — left for independent verification per the campaign's fix/verify
separation.

A ninth route (`watchdog`) was examined and found **already authenticated**; the
intake claim against it is disproven below. It was deliberately left unchanged.

This is the third instance of one root cause: **a caller-supplied `chart_id`
trusted after only a "is anyone logged in" check — or, in four routes, after no
check at all.**

The branch is cut from `origin/main` and touches **zero** files that the still-open
PR #1602 touches (`cockpit/clear/*`), so the two merge in either order.

## Severity summary

| Route | Severity | Pre-fix state | Gate applied |
|---|---|---|---|
| `POST /api/cockpit/runs` | **CRITICAL** | auth-only; `clear_before` → real cross-tenant `DELETE`, **no confirmation gate at all** | `'write'` (`permission === 'all'`) |
| `GET /api/cockpit/atlas/sample` | **CRITICAL** | **zero auth**; anonymous `SELECT *` of any chart's rows | auth + `'read'` + `chart_id` required |
| `POST /api/cockpit/refresh` | MEDIUM | auth-only; cross-tenant `asset_throughput` write | `'write'` |
| `GET /api/cockpit/stats` | MEDIUM | **zero auth**; per-chart row counts + build state | auth + `'read'` when `chart_id` given |
| `GET /api/cockpit/runs` | MEDIUM | auth-only; cross-chart build history | `'read'` |
| `POST /api/cockpit/plan` | LOW-MED | auth-only; cross-chart build-state profile | `'read'` |
| `GET /api/cockpit/registry` | LOW | **zero auth**; internal table names + SQL | auth only |
| `GET /api/cockpit/atlas/schema` | LOW | **zero auth**; column metadata | auth only |
| `POST /api/cockpit/watchdog` | — | **claim disproven — already authenticated** | UNCHANGED |

## The two CRITICALs

### 1. `POST /api/cockpit/runs` — worse than B-007's pre-fix state

B-007 at least required a `preview_hash` round-trip between "ask" and "delete".
This route had **no confirmation gate whatsoever**. A single request with
`clear_before: true` from any authenticated user (default role `guest`):

- ran `DELETE FROM <target_table> WHERE chart_id=$1` across every build-derived
  table in scope;
- reset `asset_throughput` to `dormant` for every cleared asset;
- marked the transitive downstream closure `stale`;
- inserted `build_runs` / `build_run_assets` rows; and
- dispatched a Cloud Run build job **billed against the victim's chart**.

The non-clearing path is a cross-tenant write too, and `GET` on the same route
disclosed the last 20 build runs — states, timings, `last_error` strings — for
any chart.

### 2. `GET /api/cockpit/atlas/sample` — graded CRITICAL, above the brief's expectation

The intake grouped this under a MEDIUM "reportedly unauthenticated" bucket. On
inspection it is the **most severe finding of the sweep** and is graded
CRITICAL. It called `getServerUser()` zero times — no authentication at all, let
alone authorization — and issued, for a caller-supplied `asset` + `chart_id`:

```sql
SELECT * FROM <target_table> WHERE chart_id = $1 LIMIT $2
```

`SELECT *`, on any table in the asset registry, for any chart. That is a full
read of another person's `chart_facts` (the derived astrological facts of a named
individual), every `bodha_*` interpretation table, every `kala_*` / `phala_*`
row. Unlike every other route in this sweep it required **no account at all** —
an anonymous HTTP request sufficed.

It carried a **second, independent hole in the same function.** For an asset
with `scope: 'per_chart'` and no `chart_id` supplied, `buildSampleQuery` fell
through to the unscoped branch:

```sql
SELECT * FROM <target_table> LIMIT $1
```

— rows from **all** charts, mixed. Adding authentication alone would **not** have
closed this: any logged-in user with one chart of their own could still read
everyone else's rows by simply omitting the parameter. The fix therefore does
both — require authentication, require ownership when a `chart_id` is given, and
require a `chart_id` for per_chart assets so the unscoped branch is reachable
only by genuinely global-scope assets.

## The disproven claim — `POST /api/cockpit/watchdog`

The intake listed watchdog alongside stats/registry/atlas as "calls
`getServerUser()` zero times — fully unauthenticated". **The first half is
literally true and the conclusion does not follow.**

It is a machine-to-machine endpoint invoked by Cloud Scheduler every 5 minutes;
it has no user session by design. It authenticates with a shared secret, and
**fails closed**:

```ts
if (!process.env.WATCHDOG_SECRET) return 401          // fails CLOSED
if (req.headers.get('x-watchdog-auth') !== process.env.WATCHDOG_SECRET) return 401
```

Adding `getServerUser()` here would harden nothing and would **break the
scheduler, disabling the stuck-build reaper**. The route is therefore
deliberately UNCHANGED.

Per **§N.8 (Earned-Signal Principle)**, "we looked and it seemed fine" is not a
result — the question is *what code path would have to run, and fail, for this
signal to correctly read false*. Four tests were added as that detector, proving
the gate rejects a missing secret and a wrong secret and admits the correct one.
**Those four tests passed against unpatched code**, which is precisely what
disproves the claim. Without them the "already authenticated" disposition would
itself be the unearned green signal §N.8 forbids.

## One brain, not eight hand-written copies

B-001 and B-007 each open-coded the same three-step block (read role → wrap
`query` into a `DbLike` → map `Permission` to HTTP status). B-008 needed it in
six more routes, at which point **eight hand-written copies of a security check
is itself the risk**: one transcription slip — a `!==` for a `===`, a forgotten
`super_admin` mapping, a 200 where a 403 belongs — is a silent cross-tenant hole
that no type error catches.

New helper `platform/src/lib/auth/requireChartPermission.ts` is that block,
written once, over the unchanged `authorizeChartAccess` brain. Two levels:

- **`'write'`** — requires `permission === 'all'` (owner or super_admin). Used
  for anything destructive or state-changing. A `chart_grants` **'view' grantee
  is denied**: a read grant is not a delete grant. Mirrors the Nirmāṇa page
  guard, which already gates the cockpit UI on
  `canBuild === (permission === 'all')`.
- **`'read'`** — requires `permission !== 'deny'`. Used for read-only disclosure
  of chart-scoped data, which is exactly what a 'view' grant is for.

The unknown-role case defaults **down** to `guest`, the only safe direction.
Denials return a bare `{ error: 'Forbidden', code: 'FORBIDDEN_CHART' }` — a
non-existent chart and an existent-but-unreachable one are reported identically,
so the endpoint cannot be used to enumerate which chart_ids exist.

Note the deliberate scope boundary: PR #1602's two inline copies were **not**
refactored onto this helper, to avoid conflicting with an open PR. Folding them
in is a follow-up once #1602 lands.

## Demonstrated-can-fail proof

TDD was followed strictly: for every route, the deny case was written **first**
and confirmed failing against unpatched code before any fix was written.

**Recorded proof, CRITICAL `runs` path.** Attacker uid, role `guest`, not the
owner, holding no `chart_grants` row, against the victim's chart:

```
attacker uid : attacker-uid (role guest, NOT owner, NO grant)
victim chart : 482012f1-710e-4a25-994a-93821f5871aa (owner_id=victim-uid)
HTTP status  : 201
DELETEs fired: 2
   -> DELETE FROM kala_avadhi WHERE chart_id=$1
   -> DELETE FROM kala_kshetra WHERE chart_id=$1
Cloud Run job dispatched: true
```

The fixture deliberately uses two Kāla writers carrying real sidecar digests, so
the request reaches the clear loop for real rather than short-circuiting on an
unrelated validation — a sanity test asserts those digests exist, so the deny
tests can never pass for the wrong reason.

**RED counts before fix, per route:** runs 5 failed · refresh 3 · plan 2 ·
atlas 3 · stats 2 · registry 2 · **watchdog 4 passed** (the disproof).

**ALLOW coverage.** Every route has owner, view-grantee, and super_admin allow
tests, so legitimate functionality is *proven* intact rather than assumed —
including that the owner's `clear_before` rebuild still issues its DELETEs and
still returns `cleared_asset_count: 2`.

## Verification

- Full suite: **925 files / 10,253 tests passed, 0 failures** (55 files skipped)
- Cockpit surface specifically: **134/134**
- `tsc --noEmit`: clean
- `eslint`: clean (one pre-existing warning in an untouched file)
- Isolated worktree `.clone/worktrees/pariprashna-b008-fix`, cut from
  `origin/main`. The shared checkout and all sibling worktrees were left
  untouched.

**No legitimate caller broken.** Every caller of these routes is a same-origin
browser `fetch` from a cockpit UI component (`useAssetStats`,
`useAssetRegistry`, `AtlasView`, `BuildControlsBar`), so session cookies are
already sent. `AtlasView` already passes `chart_id` when it has one and already
surfaces `errors[0]`, so the new per_chart `chart_id` requirement degrades to an
honest message rather than a silent cross-chart dump.

`Cache-Control: public` → `private` on `registry` and `atlas/schema`: a
shared/CDN cache must not store and re-serve a now-authenticated response. The
60s freshness window is preserved. `registry`'s `revalidate = 60` was replaced
with `dynamic = 'force-dynamic'`, since reading the session makes the route
inherently dynamic.

## Findings OUTSIDE this PR's scope — not fixed, not ignored

Same defect class, surfaced while sweeping, deliberately left for their own pass
rather than silently widening this PR:

1. **`POST /api/build/rebuild-all`** and **`POST /api/build/rebuild`** —
   authenticated-only; `INSERT INTO build_events` for an arbitrary
   caller-supplied `chart_id`. A genuine cross-tenant write; lower impact than a
   DELETE (event rows only), but the same root cause.
2. **`GET /api/assets/[chart_id]/[asset_key]`** — authenticated-only; returns
   per-chart asset data keyed by a `chart_id` path parameter with no ownership
   check. Cross-tenant read disclosure.

A broader scan flagged roughly **30 further API routes** accepting a `chart_id`
without any ownership check. Many are likely fine — owner-scoped in their SQL,
or behind admin middleware — but that list has **not** been triaged, and saying
so plainly is the honest disposition. Recommend a dedicated triage pass; the
scan is one grep over `platform/src/app/api/**/route.ts` for `chart_id` absent
`authorizeChartAccess` / `requireChartPermission` / `resolveChartPageAccess`.

## Status

**FIXED, NOT MERGED.** PR #1603 is open for independent verification. Per the
campaign's fix/verify separation, this session did not merge it.
