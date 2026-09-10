---
finding: F-73
stream: S1 DVARA
class: CL-01 reachability (registry URI never registered)
stage: D COMPLETE
---

## 1. Live reproduction

```
mcp__marsys-jis-direct__kala_now_get({chart_id:'482012f1-710e-4a25-994a-93821f5871aa'})
```
Live result this session (on the correct, real, native chart — not a degraded/nonexistent one):
`gochara_narrative: {"moon_primary":{...real data...}, "active_windows":[],
"field_gochara_alignment":"insufficient_data", "narrative_tier":"thin"}`. CONFIRMED — even on the
best-case, fully-populated native chart, `field_gochara_alignment` is `insufficient_data` and
`active_windows` is empty. This matches the finding's claim of UNCONDITIONAL failure exactly (not
domain-specific, not chart-specific).

## 2. Claim decomposition

1. "field_gochara_alignment is 'insufficient_data' unconditionally for every chart/domain" —
   CONFIRMED live for this chart with no domain filter (§1); corpus's own broader domain sweep not
   re-run this pass (would require iterating all domains, out of budget — the mechanism identified in
   §3 is domain-independent by construction, so a domain sweep would not add new information).
2. "root cause is a registry URI (marsys://tool/L4/gochara_forecast_get) with no matching
   registration anywhere in the retrieval registry" — CONFIRMED, see §3.
3. "the underlying kala_gochara_windows substrate is healthy (confirmed via standalone
   gochara_activation_get/gochara_forecast_get MCP tools)" — not independently re-verified this pass
   (would require calling those standalone tools directly); accepted from corpus, and consistent with
   this session's own `kala_now_get` response showing `gochara_dual_reference` (a DIFFERENT,
   correctly-wired gochara concept) fully populated with 9 real planet rows — proving the substrate
   layer generally is reachable, just not via this specific URI.
4. "this is a different root cause from F-53 (domain='marriage' vs 'relationship' naming trap)" — not
   in dispute, no domain parameter was involved in this reproduction at all (§1 called with no
   domain), so the naming-trap explanation is structurally ruled out here, corroborating the finding.

## 3. Mechanism → file:line

`platform-mcp/src/tools/kala_views/now.ts:1373`:
```ts
    'marsys://tool/L4/gochara_forecast_get',
```
— the literal URI `fetchGocharaForecastWindows` (defined at `now.ts:1359`, called at `now.ts:1423`)
passes to `callRegistryCapability`.

`grep -rn "uri: '[^']*gochara[^']*'" platform/src/lib/retrieval/registry/layers/*/index.ts` → **zero
matches**. No `layers/*/index.ts` file registers any URI containing "gochara" at all — confirmed this
session, matching the corpus's own zero-hit grep exactly. Every call to this URI necessarily 404s
against `/api/retrieval/capability`, which `fetchGocharaForecastWindows` converts to an empty
`active_windows` array (silent, no error surfaced upward), which forces
`field_gochara_alignment: 'insufficient_data'` downstream in the narrative composer.

## 4. Sibling census

`kala_explain_get` shares the identical narrative-assembly code path per the corpus's own claim (same
composer, same URI) — not independently re-tested this pass since `kala_explain_get` requires a
`domain`/`bhava` argument to run at all (see F-123's own finding — calling it bare 400s before
reaching the gochara narrative code). Flagging: F-123's fix (adding required-args to the pointer) and
this finding are unrelated mechanisms but the same target tool; no file conflict since F-73's fix is
in the registry layer (`layers/*/index.ts`, a new file/entry) while F-123's fix is in the pointer-
generation code — both can proceed independently.

## 5. Blast radius

- Fix: register the missing URI `marsys://tool/L4/gochara_forecast_get` in the appropriate
  `layers/L4_phala/index.ts` (or wherever the standalone `gochara_forecast_get` MCP tool's own
  capability is ALREADY correctly registered under a different URI/name — the fix is most likely to
  point this URI at that SAME already-working capability rather than build a new one from scratch,
  since §2 item 3 established the substrate is healthy and already reachable via the standalone
  tool). This file is under S1's lease (`platform/src/app/api/mcp/primitives/**` and adjacent
  registry wiring) — confirm exact ownership of `layers/L4_phala/index.ts` at Stage S (per plan §2,
  S3 SATYA owns `layers/L4_phala/**` broadly for disclosure findings; this is a REGISTRATION/
  reachability fix, S1's CL-01 charter — post `PAR-F73-NEEDS-LEASE` if S1's builder finds S3 already
  has an open lane touching the same index.ts file, per plan's file-conflict-resolution rule).
- No CL-00 control currently probes this path.
- Once fixed, `kala_now_get` AND `kala_explain_get`'s gochara narrative both go from
  perpetually-insufficient to actually computed — a real behavior change worth flagging to S4 (VĀCA,
  which owns `now.ts`/`explain.ts` narration quality) since the prose composer downstream of this
  fix may need its own narration-fidelity check (§N.7) once real data starts flowing through a path
  that has never served real data before.
