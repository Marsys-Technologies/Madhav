---
finding: F-38
stream: S1 DVARA
class: CL-19 missing existence check
disposition: OPEN — DIAGNOSIS-INCOMPLETE in corpus, CLOSED here (2x budget spent on real trace)
stage: D COMPLETE
lease_note: fix is route-level middleware in platform/src/app/api/mcp/primitives/** per plan §2.1
  lease-conflict table — MUST NOT be built inside now.ts (S1-owned but explicitly the wrong layer)
  or registry_bridge.ts (S2 HOT lease).
---

## 1. Live reproduction

```
mcp__marsys-jis-direct__kala_now_get({chart_id:'aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee'})
```
Live result this session: `ok`-shaped envelope (no `isError`), most `coverage[].state` = `honest_empty`,
BUT `provenance_envelope.panchanga_native_context_error` = `"HTTP 404: Chart
'aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee' not found"` (raw upstream string, leaked verbatim) and
`gochara_dual_reference` still returns 9 real (chart-unrelated) live planetary transit rows. No clean
`ENTITLEMENT_DENIED`/`AUTHZ_DENIED` signal anywhere in the envelope. CONFIRMED exactly as claimed.

## 2. Claim decomposition

1. "kala_now_get performs no entitlement/existence check before doing substantial work" — CONFIRMED,
   see §3.
2. "unlike every other chart-scoped tool tested (ganita_chart_facts_get, assess_career,
   judgment_query, dossier, catalog_chart_select), which cleanly reject with
   ENTITLEMENT_DENIED/AUTHZ_DENIED before computation" — spot-checked via source grep (§3); not
   independently re-run live against all five siblings this pass (out of 2x diagnosis budget scope;
   corpus's own live tests already cover them and are not in dispute).
3. "the raw upstream HTTP error string leaks through verbatim inside
   provenance_envelope.panchanga_native_context_error" — CONFIRMED verbatim in §1's live output.
4. "the caller receives no clean signal, would have to infer from honest_empty proliferation" —
   CONFIRMED: every `coverage[]` entry that isn't `disha_shula`/`gulika_kalam_now`/`hora_now` (which
   are pure ephemeris-only, chart-independent) reads `honest_empty`, with no summary flag naming the
   chart itself as the problem.

## 3. Mechanism → file:line (the trace the corpus marked incomplete — closed here)

`platform-mcp/src/tools/kala_views/now.ts`:
- Line 1613: `const nativeContextErrorDetail = typeof nativeContextError === 'string' && ...` — this is
  where the raw error string from the panchanga service call is captured into a local var.
- Line 1823: that detail is interpolated into a human-readable narrative string
  (`` ` — overlay reported: ${nativeContextErrorDetail}.` ``).
- Line 2012: `panchanga_native_context_error: nativeContextErrorDetail` — the raw string is placed
  directly onto the served envelope, unmodified, unclassified.
- **No entitlement/existence check precedes any of this.** `now.ts`'s handler proceeds directly into
  its substrate calls (panchanga service, L3 registries, `query_planet_transit`) with the caller-
  supplied `chart_id`, and only discovers the chart doesn't exist when one of those substrate calls
  (the panchanga overlay) 404s — by which point ephemeris-only computation
  (`gochara_dual_reference`, `hora_now`, `disha_shula`) has already run and is served as if normal.

Sibling comparison (source-grep, not live-retested this pass): `AUTHZ_DENIED`/`ENTITLEMENT_DENIED`
short-circuit guards exist near the top of the handler in `dossier.ts:887`, `muhurta_finder.ts:884`,
`phala_outlook.ts:266`, `phala_event_anchors.ts:315`, `mechanism_retrodiction.ts:115`,
`mimamsa_lel_intake.ts:211`, `chart_selection.ts:206`, `bo_2-8.ts:172` — a well-established codebase
pattern `now.ts` simply never adopted. This is the missing piece the corpus flagged
DIAGNOSIS-INCOMPLETE: it is a *pattern absence*, not a broken check — `now.ts` has no entitlement gate
call at all, early or late.

## 4. Sibling census

Not investigated this pass whether `kala_explain_get`, `kala_ahead_get`, `kala_elect_get`,
`kala_story_get` (the other `kala_views/*` tools) share the same absent-gate pattern — flagging as
follow-up census for whoever builds the fix, since the middleware approach (§ lease_note above) would
close all of them at once if applied at the route level rather than per-tool.

## 5. Blast radius

- Fix must land as **route-level middleware under `platform/src/app/api/mcp/primitives/**`** per
  plan §2.1's lease-conflict resolution (S1's lease) — explicitly NOT inside `now.ts` (would only
  fix this one tool, leaving the sibling `kala_views/*` tools exposed) and NOT inside
  `registry_bridge.ts` (S2's HOT single-builder file).
- Interacts with F-73 (also in `now.ts`, same `kala_now_get` handler, different concept —
  `gochara_narrative.field_gochara_alignment`) — same file, but a different code region and a
  different fix (F-73 is a missing registry URI, not an entitlement gate); no direct conflict, but
  both lanes touch `now.ts`'s general vicinity and should be sequenced (F-73's fix does not touch
  entitlement logic and vice versa, so parallel build is safe, just noting for the lead's own
  tracking).
- CL-00: no existing control currently probes a nonexistent chart_id against `kala_now_get`
  specifically (not verified exhaustively) — candidate for a new CL-00 check once middleware lands.
