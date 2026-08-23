---
finding_id: F-129
tier: TIER2-HONESTY
stream: S4-VACA
lane_status: DIAGNOSED
---

# F-129 Diagnosis — synth_chart_brief_get top_discoveries served as raw signal descriptors

## Live Reproduction

Called `mcp__marsys-jis-direct__synth_chart_brief_get` with
`chart_id=482012f1-710e-4a25-994a-93821f5871aa`, `depth=complete`. `content.top_discoveries`
returned 20 rows. Verbatim `statement` values observed (with `discovery_id` + `salience_score`):

- `89e49bf6-d12e-460c-a3d5-7b297b6a47b3` / `2e8e2c09-…` / `6e044195-…` / `06ceffee-…` /
  `1ff6186c-…` (5 rows, salience_score 1.2 each): `"Appears as one of many composite_state signals"`
- `9a5cf97b-…`, `1d7df67f-…` (salience 1.08046): `"Signal combustion_per_varga:is_combust with low visibility (salience 0.215)"`
- `994ef41a-…` (salience 1.075033): `"Signal combustion_per_varga:is_combust with low visibility (salience 0.215)"`
- `091e6a91-…`, `5c3d0a5d-…` (salience 1.073939): `"Signal dispositor_chain_per_varga:chain with low visibility (salience 0.227)"`
- `24885dce-…`, `81badb49-…` (salience 1.073939): `"Signal dispositor_tree:tree_position with low visibility (salience 0.227)"`
- `2bd5427b-…`, `302554b7-…` (salience 1.072728): `"Signal karaka_web_per_varga:aspect_MER with low visibility (salience 0.229)"`
- 4 more `combustion_per_varga:is_combust` rows (salience 1.071264, salience value 0.232)
- `bbeef3e3-…` (salience 1.071249): `"Signal karaka_web_per_varga:aspect_MER with low visibility (salience 0.227)"`
- `d0a73b2a-…` (salience 1.069048): `"Signal dispositor_tree:tree_position with low visibility (salience 0.228)"`

Every one of the finding's claimed literal strings reproduces verbatim, live, on the canonical
chart at depth=complete. **REPRODUCES.**

## Claim Decomposition

(a) **Confirmed.** `statement` renders raw `signal_type_id` tokens (`combustion_per_varga:is_combust`,
`dispositor_chain_per_varga:chain`, `dispositor_tree:tree_position`, `karaka_web_per_varga:aspect_MER`)
and a raw `signal_type_class` token (`composite_state`) inside a fixed template, not a synthesized
sentence.
(b) **Confirmed.** 20 rows collapse into effectively 5 distinct template shapes (`"Signal {token}
with low visibility (salience {n})"` × 4 tokens, and `"Appears as one of many composite_state
signals"` × 1), differentiated only by `discovery_id` and `salience_score` — no chart-specific
narrative content (which planet, which house, which varga, why it matters) appears anywhere in
the string.
(c) **Confirmed.** `synth_chart_brief_get` is the Mahā-Brief — the flagship whole-chart synthesis
tool (per its own tool description: "Assemble the Mahā-Brief — a comprehensive chart synthesis
across 38 canonical topic slots"). `top_discoveries` is its cross-domain-discoveries section,
present at `depth=complete`.

## Mechanism (file:line, quoted code)

**Serving-layer defect — the raw diagnostic label is aliased directly to the served field name
`statement`, discarding the two more-narrative fields the same row already carries.**

`/Users/Dev/Vibe-Coding/Apps/Madhav/.claude/worktrees/par-S4-coord/platform-mcp/src/tools/register_p1_synthesis.ts:814-822`
(inside the `synth_chart_brief_get` handler):

```ts
const discLimit = depth === 'complete' ? 20 : 5
const discResult = await platformQuery(`
  SELECT discovery_id, affected_domains_array AS domains, surface_reading AS statement,
         composite_discovery_rank AS salience_score
  FROM bodha_discoveries
  WHERE chart_id = $1
  ORDER BY composite_discovery_rank DESC NULLS LAST
  LIMIT $2
`, [chart_id, discLimit], principal)
```

...and at `register_p1_synthesis.ts:868`: `top_discoveries: discResult.rows` — passed straight
into the response envelope with no post-processing.

**Origin of the `surface_reading` string itself** — the L2 Bodha discovery-mining writer,
`/Users/Dev/Vibe-Coding/Apps/Madhav/.claude/worktrees/par-S4-coord/platform/python-sidecar/pipeline/orchestrator/writers/bo_anveshana.py`:

- Line 499: `surface=f"Signal {cand['signal_type_id']} with low visibility (salience {cand['surface_salience']:.3f})",`
- Line 575: `surface=f"Signal {sig_info['signal_type_id']} appears unremarkable to pattern inspection",`
- Line 638: `surface=f"Appears as one of many {anom['signal_type_class']} signals",`

`_make_discovery` (`bo_anveshana.py:377-433`) stores this `surface` argument to the
`bodha_discoveries.surface_reading` column (line 415: `"surface_reading": surface,`). Its
docstring intent (confirmed by the paired fields on the same row) is a **surface/depth epistemic
pair for internal reasoning display** — "what an acharya would superficially notice" vs.
`depth_reading` ("what the structural computation actually found") — not a public-facing
narrative sentence. It was never meant to be the thing served as "the discovery's statement."

**Does the code path have chart-specific narrative content available?** Yes — and it is dropped,
not merely unbuilt. The same `bodha_discoveries` row `_make_discovery` writes
(`bo_anveshana.py:394-433`) also carries:

- `hypothesis_text` (line 418, e.g. `hypothesis=f"Pattern {cand['signal_type_id']} in {', '.join(cand['domains'][:2])} has outsized structural consequence despite low surface visibility"` at line 502, or `hypothesis=f"Pattern {anom['signal_type_id']} is a {anom['source_l1_asset']} outlier; predicts distinctly unusual outcomes in {', '.join(anom['domains'][:2] or ['unknown'])}"` at line 641) — domain-qualified, more content-bearing than `surface_reading`.
- `depth_reading` (line 416) — the structural-consequence explanation.
- `why_an_acharya_misses_it` (line 406) — the interpretive "why this matters" sentence.

None of these three richer fields are selected by the `synth_chart_brief_get` query at line 816.
The data is threaded through the pipeline and sitting in the same row; the SQL simply selects the
wrong column and mislabels it `statement`. This is a query-authoring defect, not a missing-data
problem — see Sibling Census below for a call site on the same table that already does this
correctly.

## Sibling Census

Searched for other narrative `statement`/`summary` fields fed by the same discovery/signal
pipeline (`bo_anveshana.py` → `bodha_discoveries` / `bodha_mechanisms`):

1. **`bodha_discoveries_get`** (`register_p1_synthesis.ts:590-659`) — proxies to registry
   capability `marsys://tool/L2/query_discoveries`
   (`/Users/Dev/Vibe-Coding/Apps/Madhav/.claude/worktrees/par-S4-coord/platform/src/lib/retrieval/registry/layers/L2_bodha/query_discoveries.ts:110-114, 141-142, 174, 189-190`).
   This capability's SQL selects `surface_reading`, `depth_reading`, `surface_depth_delta`,
   `hypothesis_text`, and `why_an_acharya_misses_it` **all separately, each under its own honest
   field name** — no field is renamed to `statement` or `narrative`, no collapsing. This is the
   **correct pattern** and the direct counter-example to F-129's defect: the same underlying data
   is available and is exposed correctly one call site over. **Not itself an instance of the
   defect.**
2. **`bodha_mechanisms_get`** (`register_p1_synthesis.ts` service registration → registry
   capability `query_mechanisms.ts`,
   `/Users/Dev/Vibe-Coding/Apps/Madhav/.claude/worktrees/par-S4-coord/platform/src/lib/retrieval/registry/layers/L2_bodha/query_mechanisms.ts:144-150`).
   Different source table (`bodha_mechanisms`, not `bodha_discoveries`) with a structurally
   different row shape (`mechanism_name`, `mechanism_class`, `valence`, `citation_human`, …) —
   no `surface_reading`/`statement`-style templated-sentence field exists on this table at all.
   **Not an instance of the defect** (different data shape, nothing to collapse).

**Sibling count: 0 additional defect instances.** The defect is isolated to the single query at
`register_p1_synthesis.ts:816` inside `synth_chart_brief_get`. One directly relevant sibling
(`bodha_discoveries_get`) demonstrates the correct handling of the exact same table/columns,
which sharpens the fix: mirror what `query_discoveries.ts` already does (select
`hypothesis_text`/`depth_reading` alongside or instead of `surface_reading`, and do not alias the
raw column to `statement`) rather than inventing a new narrative-synthesis mechanism.

## Blast Radius

Checked for collision with **F-135** (also `synth_chart_brief_get`, `ranked_themes.weaknesses`
field). Both findings share the same file, `register_p1_synthesis.ts`, but touch **disjoint code**:

- F-129's field (`top_discoveries`) is built by the `discResult` query at lines 814-822 and
  assigned directly at line 868, sourced from `bodha_discoveries` (L2 discovery-mining output).
- F-135's field (`ranked_themes.weaknesses`) is built by `buildRankedThemes()`
  (`register_p1_synthesis.ts:381-470`), which operates on `verdicts` (rows filtered from
  `mimamsa_insight_units`, the L5 insight query at lines 793-812) — a completely different query,
  different source table, different function, invoked separately at line 845.

No shared field, no shared function, no shared query. A fix to one cannot accidentally touch the
other; they can be fixed independently in the same file without conflict.

## Verdict

**REPRODUCES LIVE — confirmed defect, isolated mechanism.**

- Live reproduction: exact match to the finding's claimed literal strings, on the canonical chart,
  at `depth=complete`.
- Root cause: `register_p1_synthesis.ts:816` selects `bodha_discoveries.surface_reading` and
  aliases it directly to the served `statement` field. `surface_reading` is an internal
  surface/depth epistemic-pair diagnostic label (paired with `depth_reading` on the same row,
  written by `bo_anveshana.py`), not a narrative sentence — it was never designed to be
  user-facing prose.
- The fix is narrow and precedented: `bodha_discoveries` rows already carry `hypothesis_text` /
  `depth_reading` / `why_an_acharya_misses_it`, and the sibling call path
  (`bodha_discoveries_get` → `query_discoveries.ts`) already selects and exposes these correctly,
  honestly labeled. No new synthesis mechanism needs to be invented; `synth_chart_brief_get`'s
  query needs to select better columns (or route through the same registry capability its sibling
  already uses) instead of re-deriving a narrower, mislabeled ad-hoc query.
- No PAR-R-7 escalation needed — this determination is not ambiguous; live evidence, code
  location, and blast radius are all unambiguous.
