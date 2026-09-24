---
artifact: WP7_REVIEW_REQUEST_P1
packet_id: P-1
status: IMPLEMENTED_AWAITING_REVIEW
date: 2026-09-24
branch: l3/gochara-autonomous-wp0-7
---

# REVIEW REQUEST — P-1 (serving provenance + coverage)

## What landed

`platform-mcp/src/tools/retrieval/register_gochara_windows.ts`:

- **P-1a/c citation** — new `GocharaPublicationManifest` interface +
  `fetchPublicationManifest(chartId, generation, principal)` (null on absent
  generation / query error; never a generation literal). `buildSourceCitation`
  gained the manifest-first branch naming `writer_asset_id`, `convention_id`,
  `manifest_id`, `content_digest`, `generation`; the three legacy branches are
  verbatim. `SOURCE_CITATION_V1` is now `buildSourceCitation('', null, null)` —
  byte-identical output proven by test.
- **P-1d (N-10)** — `AUTHORITATIVE_GENERATION_FILTER` COALESCE removed:
  `generation = (SELECT authoritative_generation FROM kala_gochara_authority
  WHERE chart_id = …)`; NULL matches nothing. Absent authority row ⇒
  `computeGocharaCoverage` early-returns `coverage.status='unpublished'` (empty
  class sets, `materialized_through: null`, explanatory note; knownDomains /
  eventClassDomains still resolved). Activation/forecast/election handlers then
  serve `empty_reason='unpublished'` and a citation naming the absent authority
  row — never a silent `'v1'`.
- **P-1b** — three coverage regimes (manifest `writer_asset_id` substep asset /
  v3 / v1). Manifest regime with ≥1 `kala_gochara_coverage` row serves
  `coverage.coverage_manifest` (partitions verbatim + per-event-class map) and
  demotes substep evidence to `coverage.sweep_execution` (labelled execution
  evidence, never presented as searched-horizon coverage). Manifest regime with
  zero coverage rows keeps substep-derived classes and says so in
  `sweep_completeness.note` (F-11/§N.8).
- **P-1e (H-5)** — forecast + election envelopes carry `trimmed` and
  `pre_trim_count` (COUNT over the un-ORDER-BY query); trim remains display-only,
  no re-rank.
- Whitelist (`platform/src/app/api/mcp/db/query/route.ts`): `ALLOWED_TABLES` +=
  `kala_gochara_publication`, `kala_gochara_coverage` (dated comment).
  `kala_gochara_contacts` deliberately **not** added — P-4 owns that decision.

## Test evidence

- New `register_gochara_windows_p1.test.ts` — 6 tests (4.0/4.1 citation branch;
  coverage-from-manifest + sweep_execution; unpublished honesty incl. asserting
  no `generation=v1` appears anywhere in the served JSON; byte-identical v1 and
  3.0 legacy citations).
- Authority-honesty suites updated for the intended P-1d break (absent row no
  longer means v1): `register_gochara_windows.test.ts` (C3 tier mocks),
  `_cl13.test.ts`, `_f53_successor.test.ts`, `s4_05_health_coverage.test.ts`
  now seed explicit `{authoritative_generation:'v1'}` rows; `_mr01.test.ts`
  updated earlier likewise.
- All gochara retrieval files green (85 passed, 3 skipped across the 5 files).
- Full platform-mcp suite: **79 failed / 2161 passed vs pre-P-1 baseline of
  82 failed / 2158 passed** — the 13-test delta the packet's P-1d break
  introduced is fully repaired; the remaining 79 are pre-existing baseline
  failures unrelated to this packet (verified by stashing the P-1 diff and
  re-running).
- `npx tsc --noEmit` in platform-mcp: 0 errors.

## Items flagged for independent review

1. **Live-DB acceptance rows 1–3** of the packet (real disposable-DB fixture)
   are owned by the WP6 harness per the packet's own §4 — the tests here are
   mocked-fetch; no live DB exists in this environment.
2. **Whitelist PR ordering** per packet §4: the `route.ts` whitelist change
   ships in this commit; if the reviewer wants it split, it is one hunk.
3. **reading_checklist.ts COALESCE**: the same authority COALESCE predicate
   exists in `fetchGocharaSweep` (P-2's file). PACKET_P2 §5 explicitly declines
   to change it and assigns removal to the P-1d owner "in the same release";
   PACKET_P1 §3.4 names reading_checklist as P-2's owner's file. To avoid
   crossing ownership lines without a ruling, P-2 (next commit) leaves the
   predicate in place — meaning the reading layer still serves v1-fallback
   windows where the main tool now says `unpublished`. **This inconsistency
   needs an explicit ruling; recommend removing the COALESCE there too** (one
   ADJUDICATION-6 test would need the same seed-row update pattern used here).
4. `fetchPublicationManifest` treats any query error as manifest-null (legacy
   citation branch) rather than an error surface — matching the packet's
   "never generation-literal" honesty rule, but a reviewer may want a
   distinguishable "manifest lookup failed" state.
