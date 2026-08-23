---
finding: F-73
stream: S1 DVARA (diagnosis + this spec) — build ownership CORRECTED, see §0 (same pattern as F-38)
class: CL-01 reachability
stage: S COMPLETE — supersedes DIAGNOSIS.md's original "register the missing URI in
  layers/L4_phala/index.ts" fix-location note with a more precise mechanism found while
  writing this spec.
---

## 0. Correction to the original diagnosis (FM-09/PAR-R-8 discipline applied)

DIAGNOSIS.md's §5 assumed the fix was registering `marsys://tool/L4/gochara_forecast_get` in a
`layers/L4_phala/index.ts`-style registry file, pointing at "the same already-working capability"
the standalone `gochara_forecast_get` MCP tool uses. Writing this spec required finding exactly
where that standalone tool's data comes from — and it is **not** a registry capability at all:

- `gochara_forecast_get`/`gochara_activation_get` are registered directly in
  `platform-mcp/src/tools/retrieval/register_gochara_windows.ts` (S3's lease, recently granted —
  see `LEASES.json`'s F-34 note), and their handlers (`computeGocharaForecast`,
  `computeGocharaActivation`) query the DB **directly** — there is no `marsys://tool/L4/gochara_*`
  registry-layer capability backing them at all. Confirmed by exhaustive grep: no
  `layers/*/index.ts` file anywhere registers a "gochara" URI (this session's grep, matching
  DIAGNOSIS.md's own earlier zero-hit result — but that earlier result was read as "the
  registration is just missing," not "there was never a registry capability here to register").
- **`now.ts`'s `fetchGocharaForecastWindows` (line 1359-1373) is calling a registry URI that was
  never meant to exist**, not one that's merely unregistered. The actual fix is not "add the
  missing registration" — it's "stop going through the registry/HTTP round-trip at all and call
  the already-exported, already-correct in-process function directly," since both files live in
  the **same `platform-mcp` package**:
  `platform-mcp/src/tools/retrieval/register_gochara_windows.ts` exports
  `computeGocharaForecast(chartId, dateRange, eventClass, valence, limit, principal, domain?, resolution?): Promise<Record<string, unknown>>`
  (line 1605) — a plain importable async function, no HTTP hop needed.

**Lease implication (same pattern as F-38):** the edit site is `now.ts` itself — S4 VĀCA's lease.
S1 does not import a function INTO S4's file; that's S4's build step. S3's `register_gochara_windows.ts`
needs no changes at all (its exported function is already public and correct) — **this fix touches
zero S1/S3-owned lines**, only S4's. **Posting `PAR-F73-NEEDS-LEASE
platform-mcp/src/tools/kala_views/now.ts`** — recommend the same "S1 specs, S4 builds once
VERIFIED" routing conductor already confirmed for F-38 (both fixes are now inside the same file,
different code regions — see §4).

## 1. Root cause (one sentence, mechanism-level)

`now.ts`'s `fetchGocharaForecastWindows` calls `callRegistryCapability('marsys://tool/L4/gochara_forecast_get', ...)`, a registry URI that was never backed by an actual registered capability (the real gochara-forecast logic lives entirely inside `platform-mcp`'s own `register_gochara_windows.ts`, queried directly, never exposed through the registry/HTTP capability system) — every call 404s, silently converted to an empty `active_windows` array, which forces `field_gochara_alignment: 'insufficient_data'` unconditionally.

## 2. Files to change

- `platform-mcp/src/tools/kala_views/now.ts` — replace `fetchGocharaForecastWindows`'s body (or
  the function entirely) to import and call `computeGocharaForecast` directly:
  ```ts
  import { computeGocharaForecast } from '../retrieval/register_gochara_windows.js'
  // ...
  async function fetchGocharaForecastWindows(chartId: string, asOfDate: string, principal: Principal) {
    const result = await computeGocharaForecast(
      chartId,
      { start: asOfDate, end: asOfDate }, // or an appropriate short forward window — exact
                                            // range semantics to confirm against now.ts's own
                                            // existing intent (this function's current callers
                                            // pass asOfDate as a point, not a range; a short
                                            // window e.g. asOfDate..asOfDate+N days may be more
                                            // correct — Stage B's call, not fixed by this spec)
      undefined, undefined, 25, principal,
    )
    // extract active_windows from result's own served shape (result.windows or equivalent —
    // exact field name to confirm against computeGocharaForecast's return shape at Stage B)
    return result
  }
  ```
  Exact parameter mapping (date range width, which result field feeds `active_windows`) needs
  Stage B to read `computeGocharaForecast`'s full body/return shape closely — this spec establishes
  the mechanism and import path, not a byte-exact diff, consistent with plan §3's Stage S bar
  ("designs the fix, names every file, test, lint" — the exact field extraction is a build-time
  detail here, not a design ambiguity).
- No changes needed to `register_gochara_windows.ts` (S3's file) — its export is already correct
  and public.

## 3. Exit test

```
mcp__marsys-jis-direct__kala_now_get({chart_id:'482012f1-710e-4a25-994a-93821f5871aa'})
```
FAILS today (live-confirmed this session, twice): `gochara_narrative.active_windows: []`,
`field_gochara_alignment: 'insufficient_data'` even on the fully-healthy native chart. PASSES once
built: `active_windows` populated from real `gochara_windows` rows (4627+ marriage-domain rows
alone confirmed to exist per DIAGNOSIS.md's corpus citation, not independently re-counted this
pass), `field_gochara_alignment` computed as `'aligned'`/`'divergent'` rather than the permanent
`'insufficient_data'` default.

## 4. Sibling sites covered

`kala_explain_get` shares the identical narrative-assembly code path per DIAGNOSIS.md §4 (not
independently re-verified live this pass — see that lane's own note about the `domain`/`bhava`
required-arg gate blocking a bare repro). **Same file family as F-38** (both fixes land inside
`now.ts`, different functions — F-38 is the top-of-handler entitlement gate, F-73 is the
`fetchGocharaForecastWindows` helper — no line overlap, independently buildable in either order or
the same commit). If `kala_explain_get` (`explain.ts`, also S4's lease) has its own copy of this
same broken registry-URI call, it needs the identical fix — not confirmed this pass, flagged for
whoever builds this to check with one grep (`grep -n "gochara_forecast_get" explain.ts`).

## 5. Recurrence guard

Recommend (not built here): a registry-catalog lint that flags any `marsys://tool/...` URI string
literal appearing in `platform-mcp/src/**` that has no corresponding entry in
`platform/src/lib/retrieval/registry/layers/*/index.ts` — would have caught this mechanically (the
URI was a phantom reference from day one, not a registration that regressed). Flagged as a
candidate governance addition, not required for this lane's own COMPLETE verdict.

## 6. Dependencies and rollback

No dependency on other lanes; independent of F-38 despite sharing a file (see §4). Rollback: revert
the `fetchGocharaForecastWindows` change; behavior reverts to today's permanent
`insufficient_data` state — zero risk, since the function currently always returns an empty result
(nothing downstream depends on it ever being populated).

## 7. Sub-claim coverage table

| D-2 sub-claim | Spec element that closes it |
|---|---|
| "field_gochara_alignment is insufficient_data unconditionally for every chart/domain" | §2: replaces the always-404ing registry call with the actually-working direct function call |
| "root cause is a registry URI with no matching registration" | §0/§1: corrected — the URI was never backed by a registration at all; the real capability lives in-package, unreached via HTTP |
| "underlying kala_gochara_windows substrate is healthy" | §2: the fix reuses that exact healthy substrate directly, no new computation |
