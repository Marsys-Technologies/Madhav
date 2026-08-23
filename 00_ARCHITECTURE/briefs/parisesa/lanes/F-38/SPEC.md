---
finding: F-38
stream: S1 DVARA (diagnosis + this spec) — build ownership CORRECTED, see §0
class: CL-19 missing existence check
stage: S COMPLETE — but see §0: this spec supersedes DIAGNOSIS.md's original "route-level
  middleware under platform/src/app/api/mcp/primitives/**" fix-location note with a more
  precise, independently re-verified mechanism found while writing this spec.
---

## 0. Correction to the original diagnosis (FM-09/PAR-R-8 discipline applied)

DIAGNOSIS.md (written earlier this session) followed the plan's own §2.1 guidance that F-38's fix
belongs in "route-level middleware under `platform/src/app/api/mcp/primitives/**`." Writing this
SPEC required tracing exactly how `kala_now_get` reaches the substrate, and that trace found the
plan's location doesn't match the actual call path — **recorded here rather than silently
building in the wrong place**, per the standing discipline of verifying a relayed claim against
source before building on it:

- `now.ts`'s `callRegistryCapability` (line 120) calls `fetch(`${PLATFORM_URL}/api/retrieval/capability`, ...)` — **not** `/api/mcp/primitives/[tool]`. The `primitives/[tool]/route.ts` dispatcher (which DOES already have an entitlement gate at its lines 199-218) is not in `kala_now_get`'s call path at all.
- `/api/retrieval/capability/route.ts` (the route `now.ts` actually calls) ALSO already has an entitlement gate (R5.2 A1, lines 32-236) via `authorizeChartAccess` — and `authorizeChartAccess` (`platform/src/lib/auth/authorizeChartAccess.ts:83-84`, Rule 4) **already correctly returns `'deny'` for a chart_id that does not exist** (confirmed by reading the function directly, plus an existing RC-12 defense-in-depth commit specifically hardening the super-admin path for this exact case).
- **So the entitlement machinery this codebase already has is not broken.** The actual gap is that `kala_now_get`'s own handler (`now.ts`) never calls it — unlike `dossier.ts` (`platform-mcp/src/tools/dossier.ts:48,887`), `muhurta_finder.ts`, `phala_outlook.ts`, and 5 other files, which all `import { remoteAuthorize } from '../lib/authz.js'` (`platform-mcp/src/lib/authz.ts` — a thin wrapper that POSTs to `/api/mcp/authz`, which itself calls `authorizeChartAccess`) and gate on it BEFORE doing any substrate work, returning `AUTHZ_DENIED` cleanly.
- **`remoteAuthorize` already exists, is already used by 7+ sibling tools, and already fail-closes on error** (`authz.ts:44`: `catch { return false }`). No new shared helper needs to be built — the fix is adopting an existing, already-correct pattern that simply was never applied to `kala_now_get`.

**Lease implication:** the actual edit site is `platform-mcp/src/tools/kala_views/now.ts` — S4 VĀCA's lease per the §2.1 kala_views split (S1 owns `now.ts`'s narration-neighbor files but not `now.ts` itself for THIS class of change; F-73, also in `now.ts`, was already flagged the same way). **Posting `PAR-F38-NEEDS-LEASE platform-mcp/src/tools/kala_views/now.ts` — same "S1 specs, S4 builds once VERIFIED" pattern as F-09/F-123, not self-built here.**

## 1. Root cause (one sentence, mechanism-level)

`kala_now_get`'s handler (`now.ts`) dispatches to ~15 substrate calls in parallel without first
calling the already-existing, already-correct `remoteAuthorize(principal, chartId, 'view')` gate
that 7+ sibling MCP tools use, so a nonexistent `chart_id` is never rejected up front — instead
each individual substrate call independently 404s or empties out, and the handler stitches those
partial failures into a structurally-successful-looking envelope with the raw upstream error
string (`panchanga_native_context_error`) leaking through verbatim.

## 2. Files to change

- `platform-mcp/src/tools/kala_views/now.ts` — add `import { remoteAuthorize } from '../../lib/authz.js'` (relative path from this file's location, matching `dossier.ts`'s own import pattern) and, at the top of the handler (before the `Promise.all` substrate dispatch currently starting around the natal-ref-signs fetch), add:
  ```ts
  const authorized = await remoteAuthorize(principal, chartId, 'view')
  if (!authorized) {
    return errOut('kala_now_get', 'AUTHZ_DENIED: not authorized to access this chart', { chart_id: chartId })
  }
  ```
  (exact helper name for the error envelope — `errOut` vs this file's own error-building convention —
  to be confirmed against `now.ts`'s existing error-path code at Stage B; the shape must match the
  `AUTHZ_DENIED`/`ENTITLEMENT_DENIED` sibling convention already used by `dossier.ts:887`,
  `phala_outlook.ts:266`, etc., not a bespoke string.)
- No changes needed to `authz.ts`, `/api/mcp/authz/route.ts`, or `authorizeChartAccess.ts` — all
  three are already correct and unmodified by this fix.

## 3. Exit test

```
mcp__marsys-jis-direct__kala_now_get({chart_id:'aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee'})
```
FAILS today (live-confirmed this session): returns an `ok`-shaped envelope with
`provenance_envelope.panchanga_native_context_error` leaking the raw `"HTTP 404: Chart '...' not
found"` string, most `coverage[]` entries `honest_empty`, no clean denial signal anywhere.
PASSES once built: returns a clean `AUTHZ_DENIED`/`ENTITLEMENT_DENIED`-classed error (matching the
sibling convention), no substrate calls attempted, no raw upstream string in the response.
Regression check: the SAME call against the real native chart_id
(`482012f1-710e-4a25-994a-93821f5871aa`) must continue to return the full, populated envelope
unchanged — `remoteAuthorize` must not introduce a false-deny for the legitimate case.

## 4. Sibling sites covered

DIAGNOSIS.md §4 flagged, unaudited: whether `kala_explain_get`, `kala_ahead_get`, `kala_elect_get`,
`kala_story_get` (the other `kala_views/*` composer tools) share the same missing-gate pattern.
**Not resolved by this spec** — each of those files is a separate handler and would need its own
independent trace to confirm whether it already gates (some might, via a path this session didn't
check) or shares the gap. Recommend: whichever stream builds this fix for `now.ts` runs the same
`grep -L "remoteAuthorize" kala_views/{explain,ahead,elect,story}.ts` census before closing this
finding's family, and opens sibling findings if any of the four lack the import.

## 5. Recurrence guard

Recommend (not built here — Stage S is a document): a lint rule requiring every
`kala_views/*.ts` file whose handler is `scope: per_chart` (i.e. takes `chart_id`) to import
`remoteAuthorize` from `../../lib/authz.js` — mechanical, catches the exact defect class file-wide.
Flagged as a candidate CL-00 addition, VERIFIER's/conductor's call on whether to require it before
COMPLETE given this finding's own fix is a two-line addition.

## 6. Dependencies and rollback

No dependency on other lanes. Independent of F-73 (same file, different code region — the
`gochara_narrative` fetch vs. the top-of-handler gate — no line overlap). Rollback: revert the
`import` + 4-line early-return; behavior reverts to today's leaky-but-non-crashing state — zero
risk to the legitimate-chart path since `remoteAuthorize` fails closed only on network/parse error
(rare, and matches the existing fail-closed convention already accepted by 7+ sibling tools).

## 7. Sub-claim coverage table

| D-2 sub-claim | Spec element that closes it |
|---|---|
| "kala_now_get performs no entitlement/existence check before doing substantial work" | §2: adds the `remoteAuthorize` gate before the substrate `Promise.all` |
| "raw upstream HTTP error string leaks through verbatim" | §2: the gate short-circuits before `call_panchanga_service` (the leak's own source) is ever invoked for an unauthorized/nonexistent chart |
| "caller receives no clean signal, must infer from honest_empty proliferation" | §2/§3: a denied call now returns one clean `AUTHZ_DENIED` envelope instead of a 15-way partial-failure stitch |
