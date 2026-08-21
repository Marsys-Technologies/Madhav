---
canonical_id: PARISESA_V4_GA2_RULING_RATE07
version: 1.0
status: CURRENT
authority: GA-2 (architecture decision), explicitly delegated by the PARIŚEṢA-V4 campaign owner
decided: 2026-08-21
decided_against_base: origin/main @ e53fa58
supersedes: none
inputs:
  - /Users/Dev/shad_overnight/par-night/state/codex-v4/F06_RATE07_ARCHITECTURE_DECISION.md (the AWAITING NARROW AUTHORITY request)
---

# GA-2 ruling — RATE-07: fleet-wide rate limiting for the OAuth mutation endpoints

## 0. The two findings this ruling closes

**F-06 (scope honesty).** `ref_remedies_chart_get` advertised "Chart-specific remedy
suggestions" while neither its MCP parameter schema nor the server-side query scoped by
chart. Reproducer: `ref_remedies_chart_get({affliction:'Saturn', top_k:5})` — the schema
accepted only `{affliction, top_k}`; a caller could not pass `chart_id` even if it wanted to.

**RATE-07 (the architecture decision).** A security review of the F-06 repair candidate
surfaced a deeper, unrelated defect: the five OAuth mutation endpoints have no fleet-wide
rate limiting. That is the decision this document rules on.

---

## 1. RATE-07 — the defect, re-verified against current `main`

The preflight in the decision request was dated 2026-08-18 against `3d15ea03`. Every
finding was re-verified read-only against `e53fa58` on 2026-08-21. All still hold, plus
three that the original preflight did not state:

| Preflight claim | Status on `e53fa58` |
|---|---|
| `redis_client.ts` still references `infra/memorystore/main.tf` | **Holds.** The reference is at `platform/src/lib/cache/redis_client.ts:8`; `infra/` contains `artifact_registry, cloud_scheduler, iam, logging, monitoring, scheduler, secrets, teardown` — no `memorystore`. |
| `deploy.yml` supplies no `REDIS_HOST`/`REDIS_PORT`, no VPC connector, no Cloud Armor | **Holds.** `grep -E "REDIS\|vpc\|VPC\|armor\|Armor" .github/workflows/deploy.yml` returns nothing. |
| The cache helper degrades **open** on Redis failure | **Holds.** `getRedis()` returns `null` and is documented "callers MUST gracefully fall back to compute-on-miss". Correct for a cache; disqualifying for a rate-limit authority. |
| MCP service can scale out | **Holds.** `amjis-mcp` deploys `--allow-unauthenticated --min-instances=1 --concurrency=80`, no max-instance cap. |
| Socket-derived identity is untrustworthy behind Cloud Run | **Holds, and is worse than stated:** `platform-mcp/src/server.ts` never calls `app.set('trust proxy', …)` and reads no forwarding header anywhere. |

**Not in the original preflight, found here:**

1. **The existing limiter is not merely per-instance — it is not on these routes at all.**
   `platform-mcp/src/lib/rate_limiter.ts`'s `checkMcpRateLimit` has exactly one call site,
   `server.ts`'s `POST /mcp`, and it runs *after* principal resolution because it keys on
   `key_id`. OAuth mutations carry no `key_id`. Four of the five are unauthenticated.
   The correct characterisation is "no rate limiting", not "weak rate limiting".

2. **`POST /mcp/oauth/authorize` is an unauthenticated DB-write amplifier.** `handleAuthorize`
   (`platform-mcp/src/oauth/authorize.ts:122`) validates `response_type` and scope shape, then
   calls `createDbAuthCode` — writing an `mcp_oauth_auth_codes` row — **without ever validating
   `client_id` against a registered client**. Any anonymous caller can drive unbounded row
   creation for arbitrary client identifiers. This is the sharpest edge in RATE-07 and it
   determined the tightest per-IP limit in the table.

3. **The sidecar has no database access whatsoever.** `oauth_platform_client.ts`'s header is
   explicit: "the MCP sidecar has no direct DB access"; `pg` is a dependency but is imported
   nowhere in `platform-mcp/src`, and `amjis-mcp` is deployed with no `DATABASE_URL`,
   `INSTANCE_CONNECTION_NAME`, or DB credentials. **This materially reshapes route 3** and is
   addressed in §3.

---

## 2. THE RULING

> **Route 3 — database-backed (Postgres) — is adopted.** Routes 1 (Memorystore/Redis) and
> 2 (Cloud Armor front door) are **rejected for this control**, with the reasoning and the
> conditions that would reopen them stated in §4.

Implemented as: migration `580_mcp_oauth_rate_buckets.sql` (a bounded, hash-keyed,
fixed-window bucket table) + a single-statement atomic upsert
(`platform/src/lib/mcp/oauth_rate_limit.ts`) + a service-token-guarded platform route
(`POST /api/mcp/rate-limit/check`) + a fail-closed sidecar gate
(`platform-mcp/src/lib/oauth_rate_limit.ts`) wired to all five OAuth mutation routes.

### 2.1 Why — and the part I did NOT take on faith

The campaign's GA-2 doctrine says "choose minimal-reversible option where comparable", and
route 3 is plainly the more reversible option. But "more reversible" only decides the
question **if the options are comparable on the merits**, and the task explicitly required
verifying that for this specific case rather than accepting it. Three checks:

**(a) The decisive one — route 3 introduces no new failure domain; route 1 does.**
This is the argument that actually settles it, and it is specific to these five endpoints.
Every one of them *already* cannot function without a Postgres round-trip through the
platform API:

| Endpoint | Existing hard dependency on Postgres-via-platform |
|---|---|
| `POST /oauth/authorize` | `createDbAuthCode` → `POST /api/mcp/oauth/codes` |
| `GET /oauth/callback` | `verifySessionCookieViaPlat` + `stampDbAuthCodeUid` → `PATCH /api/mcp/oauth/codes` |
| `POST /oauth/token` | `validateOAuthClient` / `consumeDbAuthCode` / `issueTokens` |
| `POST /oauth/refresh` | `refreshAccessToken` → `POST /api/mcp/oauth/tokens/refresh` |
| `POST /oauth/register` | `validateMcpKeyFromHeader` + `registerOAuthClient` |

A fail-closed limiter must, by construction, reject when its store is unreachable. On route
3 that rejection coincides with an outage in which the endpoint was already going to fail —
the limiter is never the *sole* reason a request dies. On route 1, Redis would be a
**second, independent** dependency: a Redis outage would take down OAuth even while Postgres
was perfectly healthy. Route 1 therefore *reduces* the availability of these endpoints in
exchange for latency the endpoints demonstrably do not need. That is a bad trade here.
This inverts the usual "Redis for rate limiting" default, and it inverts it on a fact
specific to this codebase, not on a general preference.

**(b) Query volume and latency genuinely do not need Redis.** OAuth mutations are
per-authorization-session events, not per-request events. The per-tool-call hot path is
`POST /mcp`, which is *not* in scope here and keeps its existing in-process limiter. Each
gated request adds 2 bucket charges (per-IP + route-global), each a single primary-key upsert
on a table whose live row count is bounded by distinct-callers-per-window. Against handlers
that already spend 1–3 platform round-trips with 5–10 s timeout budgets, one more ~2–5 ms
in-region statement is not a meaningful latency change. Choosing Redis for this would be
choosing microsecond latency for a path that already costs milliseconds, at the price of
(a).

**(c) Existing Postgres load is not a constraint at this scale.** `initPool()` caps the web
pool at `max: 10` with a documented note that Cloud SQL `max_connections=50` leaves headroom
for orchestrator workers. The bucket statement is a PK upsert plus a probabilistic, `LIMIT`-ed
prune — orders of magnitude cheaper than the chart-fact reads this pool already serves. If
OAuth mutation volume ever reached a scale where this mattered, that volume would itself be
the abuse the limiter exists to stop.

**Conclusion:** routes 1 and 3 are *not* comparable-with-3-more-reversible. Route 3 is better
on the merits for this specific control, and is also more reversible. The doctrine and the
independent analysis agree; the ruling does not rest on the doctrine alone.

### 2.2 What route 3 had to become, given the no-DB-access finding

The decision request's route 3 said "add a bounded, transactional rate-bucket design". As
written that implies the limiter runs where the endpoints run. It cannot: the sidecar has no
database. So route 3 as adopted is **Postgres-backed, reached over the platform API** —
the identical `X-MCP-Internal-Token` channel these handlers already use for every DB
operation. This is a change to the *mechanism*, not to the ruling, and it strengthens
argument (a): the limiter now travels the exact same wire that is already load-bearing for
these endpoints, so "the store is down" and "the endpoint was already broken" are the same
event, not two events.

---

## 3. What was built

| Artifact | Purpose |
|---|---|
| `platform/supabase/migrations/580_mcp_oauth_rate_buckets.sql` | `mcp_rate_buckets`: PK = SHA-256 of `v1\|route\|kind\|subject` (fixed 64 chars → bounded key width against a hostile subject), fixed-window counter, `expires_at` index. Additive only; DOWN section included. |
| `platform/src/lib/mcp/oauth_rate_limit.ts` | The single-statement atomic charge (`INSERT … ON CONFLICT DO UPDATE … RETURNING`), argument bounds, bounded prune. Throws on store failure — no "assume allowed" branch exists. |
| `platform/src/app/api/mcp/rate-limit/check/route.ts` | Service-token-guarded store endpoint. Returns **200 for both allowed and denied** (it reports a decision; the 429 belongs on the OAuth endpoint); **500 with no decision field** on store failure. |
| `platform-mcp/src/lib/oauth_rate_limit.ts` | Identity derivation, per-route limit profiles, the Express gate, `chargeValidatedSubject`, 429/503 responses. Fail-closed throughout. |
| `platform-mcp/src/server.ts` | `oauthRateLimit(<key>)` attached as the **first** middleware on all five mutation routes; post-validation principal charge on `/register`. |
| `platform-mcp/src/oauth/token.ts` | Post-validation client charge, placed after `validateOAuthClient`'s `invalid_client` rejection. |

### 3.1 Three design points that are load-bearing

**Atomicity is a property of one SQL statement, not of a transaction.** The charge is a
single `INSERT … ON CONFLICT (bucket_key) DO UPDATE … RETURNING`. Postgres takes a row lock
on the conflicting tuple, so concurrent Cloud Run instances serialise and each observes its
own post-increment value. There is deliberately **no SELECT of the table anywhere** — a
read-then-write pair at READ COMMITTED lets two instances read the same count and both
decide "allowed", which is precisely the lost-update bug a fleet-wide limiter must not have.
`window_start` is computed in SQL as `floor(epoch(now())/window)`, so instances with skewed
clocks agree on the boundary and no caller ever supplies a timestamp.

**Two-layer charging, to make quota poisoning impossible rather than unlikely.** Charging a
bucket keyed on an *unvalidated* identifier is itself an attack primitive: anyone could spend
a victim's quota by naming their `client_id`. So layer 1 (pre-handler, always) keys only on
things a caller cannot assert — the transport-derived IP and a route-wide global ceiling —
and layer 2 keys on a principal or client the handler has **already proven**, charged only
after validation succeeds. `chargeValidatedSubject` is a separate function from the
middleware for exactly this reason, and a wiring test asserts it is never called with a value
taken off `req.body`/`req.query`/`req.headers`.

**Fail-closed, with 503 kept distinct from 429.** A limiter that fails open is
indistinguishable from no limiter at the exact moment (a database under load) an attacker
most wants it gone. Store failure returns **503 `temporarily_unavailable`** with
`Retry-After`, never 429 — conflating them would tell an operator "we are being flooded"
during what is actually an outage. `MCP_OAUTH_RATE_LIMIT_ENABLED` is the rollback switch and
**defaults ON**; only the literal string `false` disables it (`'0'`, `'no'`, `'off'` and the
empty string all leave it armed — a security control must not be switchable off by accident).

### 3.2 DISCLOSED AMBIGUITY — client-IP derivation

The acharya-grade bar requires disclosing this rather than picking an assumption silently.

Behind Cloud Run, each hop **appends** to `X-Forwarded-For`, so a client sending
`X-Forwarded-For: 1.2.3.4` produces `1.2.3.4, <real peer>`. The **leftmost** entry is
therefore fully caller-controlled and is never read. The identity is taken from the **right**,
`MCP_TRUSTED_PROXY_HOPS` entries in (default `1` = rightmost). Single-value headers
(`X-Real-IP`, `CF-Connecting-IP`, `True-Client-IP`) are ignored entirely — behind Cloud Run
they are verbatim caller input with no appending hop to make them trustworthy.

With `hops=1` and **direct Cloud Run ingress**, the rightmost entry is the true peer. That
path is real and reachable: `amjis-mcp` is `--allow-unauthenticated` and its `*.run.app` URL
is live and smoke-tested by `deploy.yml`.

**What I could not determine from the repository:** production also advertises
`MCP_BASE_URL=https://madhav.marsys.in/mcp`, and the config routing that hostname to this
service **is not in the repo** — `firebase.json` rewrites `**` to `amjis-web` (not
`amjis-mcp`), `platform/next.config.ts` has no `/mcp` rewrite, and `infra/` contains no load
balancer or Cloud Armor module. If that path traverses additional proxies, the rightmost XFF
entry is a proxy's address rather than the client's, and all traffic arriving that way shares
one bucket.

That failure mode is **conservative** (over-restrictive, never permissive) and is **never
attacker-steerable onto an innocent third party**, because it collapses identities rather
than letting one be chosen. It is nonetheless real, and it is why:
(i) the hop count is an explicit operator setting rather than a hardcoded guess;
(ii) the per-route **global ceiling** exists, so the endpoint stays protected regardless of
how well IP attribution works; and
(iii) the limits are sized as **abuse ceilings, not fairness quotas**, so a collapsed bucket
does not bite legitimate traffic.

**Owed to whoever operates the front door:** if a GCLB / Cloud Armor / additional proxy is in
front of `amjis-mcp`, `MCP_TRUSTED_PROXY_HOPS` must be raised to match. This is documented in
the module header and in the PR body; it is a configuration obligation this ruling creates and
does not discharge.

### 3.3 Where layer 2 applies, and where it deliberately does not

Layer 2 (post-validation charging) is wired on exactly the two paths that surface a validated
identity through the **existing** contracts:

| Path | Layer 2 subject | Why |
|---|---|---|
| `POST /oauth/register` | `principal.user_uid` | `validateMcpKeyFromHeader` proves the Bearer key first. |
| `POST /oauth/token` (`client_credentials`) | `params.client_id` | `validateOAuthClient` has verified the secret, and the `invalid_client` rejection precedes the charge. |

**Not wired, deliberately:**

- **`grant_type=refresh_token`** (both via `/oauth/token` and `/oauth/refresh`). `token_store.refreshAccessToken` returns `IssuedTokens { access_token, refresh_token, expires_in, scope }` — **no uid**. There is no validated identity to charge without changing the platform refresh route's response shape, and changing an OAuth response contract inside a rate-limiting PR is the wrong blast radius. This path is covered by layer 1 (per-IP + route-global) only. Owed as a follow-up if per-uid refresh accounting is wanted.
- **`grant_type=authorization_code`.** `consumeAuthCode` does surface a validated `authCode.uid`, but the auth code is single-use and consumed by that very call, so a per-uid bucket adds little over layer 1 against replay. Not added, rather than added for the appearance of coverage.
- **`GET /oauth/callback`.** The Firebase session verification yields a uid, but charging it would let an attacker who can trigger callbacks burn a legitimate user's quota mid-login. Layer 1 only, on purpose.

### 3.4 Two things found, disclosed, and deliberately NOT fixed here

Both are pre-existing, both are out of RATE-07's declared scope, and neither is made worse by
this change. Fixing them inside a rate-limiting PR would be scope creep on a security surface.

1. **`handleAuthorize` never validates `client_id` against a registered client** before
   writing an auth-code row (§1, finding 2). Rate limiting *bounds* the resulting write
   amplification; it does not fix the missing validation. A separate finding is owed.
2. **`NODE_ENV` is not set for `amjis-mcp`**, so `authorize.ts:173`'s
   `secure: process.env['NODE_ENV'] === 'production'` sets the CSRF state cookie **without
   the Secure flag in production**. Unrelated to rate limiting; disclosed for triage.

---

## 4. REJECTED ALTERNATIVES (stated explicitly, per GA-2 doctrine)

### Route 1 — Memorystore / Redis-backed. **REJECTED.**

*What it would have been:* provision a Memorystore instance + a Serverless VPC Access
connector, wire `REDIS_HOST`/`REDIS_PORT` into `amjis-mcp` (and `amjis-web`), and use
`INCR` + `EXPIRE` as the atomic counter.

*Why rejected — in order of weight:*

1. **It adds a new failure domain to endpoints that do not currently have one** (§2.1a).
   This is the decisive reason and it is specific to this codebase: a fail-closed limiter on
   Redis means a Redis outage takes down OAuth while Postgres is healthy. Route 3's store
   outage is an outage the endpoint was already going to have.
2. **It buys latency these endpoints do not need** (§2.1b). Sub-millisecond counting on a
   path that already spends milliseconds on mandatory platform round-trips.
3. **It requires infrastructure authority this ruling does not hold** and cannot self-verify:
   a new Memorystore instance, a VPC connector, IAM, and `deploy.yml` env changes across two
   services. `infra/memorystore/main.tf` — which `redis_client.ts` cites — **does not exist**;
   the module would have to be written, applied, and verified live.
4. **Least reversible of the three.** A migration is revertible by a `DROP TABLE` in the DOWN
   section. A provisioned Memorystore instance and VPC connector are live billed
   infrastructure with their own teardown risk.
5. **The existing Redis helper is not adaptable.** `getRedis()` returns `null` on failure and
   is explicitly documented as degrading open. Reusing it would silently produce a fail-open
   limiter; a distinct fail-closed client would have to be written anyway, so "we already have
   a Redis client" is not a real head start.

*What would reopen it:* if OAuth mutation volume grew to where per-request Postgres upserts
became a measurable share of pool utilisation, **or** if a Memorystore instance were
provisioned for an unrelated reason (making the second failure domain a sunk cost rather than
a new one), route 1 becomes the better answer. Neither condition holds today. The interface
is deliberately narrow — `consumeRateBucket()` behind one HTTP endpoint — so swapping the
storage engine is a single-file change, not a re-architecture.

### Route 2 — Cloud Armor / managed front-door edge policy. **REJECTED for this control.**

*What it would have been:* an edge rate policy owning client identity and enforcement,
applied to a load balancer in front of `amjis-mcp`.

*Why rejected:*

1. **It cannot express the control that actually matters.** An edge policy limits by IP and
   path. It cannot charge a *post-validation* per-client or per-principal bucket, because it
   has no idea whether the `client_secret` in the body was correct. Layer 2 (§3.1) — the part
   that makes quota poisoning structurally impossible — is not expressible at the edge.
2. **Path coverage is not currently verifiable.** There is no load-balancer or Cloud Armor
   module in `infra/`, and the repo does not even show how `madhav.marsys.in/mcp` reaches this
   service (§3.2). A policy whose coverage cannot be verified against the actual ingress path
   is a control that might be enforcing nothing — the §N.8 defect class exactly.
3. **The `*.run.app` URL is directly reachable and `--allow-unauthenticated`.** An edge policy
   on a load balancer does not protect a Cloud Run service whose own URL still answers. Route 2
   would require *also* closing that door — more infrastructure change, more unverifiable
   surface.
4. **Infrastructure authority + least verifiable from code.** No test in this repository could
   ever prove a Cloud Armor policy is attached and effective; route 3's equivalent claims are
   proved by CI (§5).

*What would reopen it — and it should:* route 2 is genuinely the right answer for **volumetric
L3/L4 DDoS absorption**, which route 3 does not and cannot address (a flood large enough to
saturate the service never reaches application code). **These are complementary controls, not
alternatives.** This ruling rejects route 2 *as the mechanism for RATE-07* — the per-identity,
post-validation application limit — and explicitly recommends an edge policy as separate,
additional work under infrastructure authority. Adopting route 3 does not foreclose it.

### Rejected sub-option — extend the existing in-process limiter to the OAuth routes.

Not one of the three offered routes, but the cheapest thing available and therefore worth
rejecting on the record. It would produce a limit of `limit × instance_count` on an
autoscaling service, keyed on an identity that is either absent (no `key_id`) or spoofable
(leftmost XFF), backed by a Map with no eviction that an anonymous caller could grow without
bound. It would look like a control in the diff and be one in no meaningful sense — which is
the defect §N.8 names. Rejected.

---

## 5. Test evidence (see the PR body for command output)

- `platform-mcp/src/__tests__/rate07_oauth_rate_limit.test.ts` — 31 tests: XFF spoofing
  (leftmost never used; forged 50-entry chains ineffective; single-value headers ignored),
  hop-count handling, IP normalisation, no-charging-of-unvalidated-identifiers, 429 +
  integer `Retry-After`, global-ceiling enforcement, both-buckets-charged, fail-closed on
  every store-failure mode, kill-switch semantics.
- `platform-mcp/src/__tests__/rate07_oauth_route_wiring.test.ts` — 11 tests: the gate is
  attached, and is **first**, on all five mutation routes; an exhaustive scan proves no
  `/mcp/oauth/*` route is ungated; post-validation charges provably follow their validation.
- `platform/src/lib/__tests__/mcp/oauth_rate_limit.test.ts` — 31 tests: the SQL is a single
  statement with no read-then-write shape; server-side window; saturation; bounded prune;
  argument bounds; allowed/denied boundary; throws rather than assuming allowed.
- `platform/src/lib/__tests__/mcp/oauth_rate_limit.db.test.ts` — 5 tests against **real
  Postgres**, wired into CI's existing `db-integration-tests` job: 50 concurrent charges yield
  hits 1..50 with **no duplicates** and exactly `limit` allowed (the lost-update detector);
  window rollover reuses one row; TTL prune removes expired and spares live; window boundary
  is server-derived; the raw subject never lands in the table.
- `platform/src/app/api/mcp/__tests__/rate_limit_check_route.test.ts` — 9 tests: fail-closed
  service token; 200-for-both-decisions; 500-with-no-decision-field.
- Migration 580 applied against a throwaway Postgres 16, twice (idempotency), and the
  cross-directory migration number guard passes.

**Honest gap:** the atomicity claim is proved against Postgres 16 in CI, not against the
production Cloud SQL instance. That is the strongest evidence obtainable without a production
write, and the property proved (row-level `ON CONFLICT` serialisation) is engine behaviour,
not instance configuration.

---

## 6. A deployment race this ruling created, and closed

Adopting a fail-closed limiter backed by a **new table** creates an ordering obligation that
did not previously exist. `deploy-web` is the only job that runs migrations; `deploy-mcp`
needed only `changes` and therefore ran **concurrently** with it. An `amjis-mcp` revision
serving before migration 580 applied would 503 every OAuth mutation until deploy-web caught up.

The migration step does run early in `deploy-web` (before its image build), so in practice it
would usually win the race — but "usually wins" is not a detector, and §N.8 forbids resting a
safety property on one. `deploy-mcp` therefore now declares `needs: [changes, deploy-web]`,
guarded with `always()` so that:

- `platform/**` unchanged → `deploy-web` SKIPPED → no new migration exists → MCP deploys exactly as before;
- `deploy-web` SUCCESS → migrations applied → MCP deploys;
- `deploy-web` FAILED → migration state unknown → MCP is **held**, rather than shipping dependent code against unknown schema.

This is a change to shared deployment topology, made under this ruling's authority because the
race is one this ruling's own design introduced. It is flagged in the PR body as the item most
deserving of independent scrutiny.

## 7. F-06 disposition

The registry descriptor for `marsys://tool/L0/query_remedies_for_chart` already said the
honest thing ("No chart-scoped SQL — this is a global corpus lookup"; `scope: 'global'`, the
`CHART_REQUIRED` gate removed in Wave D). The MCP alias was the surface still claiming
otherwise. `brahma_remedy_corpus` is an L0 global reference table with **no chart_id column**,
so per-chart filtering is not merely unimplemented — it is not expressible against this data
source. Adding real scoping would mean building a different capability; one already exists
(`bodha_remedies_get` → `marsys://tool/L2/query_remedies`).

**Ruling: scope honesty, not new scoping.** The description now states what the tool does and
points at `bodha_remedies_get`; `chart_id` is exposed as an explicitly provenance-only,
UUID-validated optional parameter so the schema mirrors the capability's real contract instead
of hiding it; the legacy `remedy_tools.ts` description (which claimed "chart_id + affliction")
is corrected the same way. The original reproducer's arguments still validate — no breaking
change. The old repair candidate (`0ae44858…`) was not reachable locally and the repair was
re-authored against current `main`; the codegen/projection churn that blocked it does not
recur, because `web_tool_bridge.generated.json` carries names and URIs, not descriptions, and
neither is changed.
