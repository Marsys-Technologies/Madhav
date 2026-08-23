# F-12 — DIAGNOSIS (exemplar for the CL-06 "count dies under composition" class)

Stream: S2 MĀTRĀ (as filed) · Class: CL-06, grouped with F-36/F-37/F-45 ·
File: `platform/src/lib/retrieval/registry/layers/L1_ganita/get_dignity.ts` (+ siblings
`get_avasthas.ts`, `get_karakas.ts`, same directory)
Stage: D (DIAGNOSE) · Chart: `482012f1-710e-4a25-994a-93821f5871aa` (Abhisek Mohanty, canonical)

**This document is the shared exemplar for the whole CL-06 group** (§4 sibling census, §5
BRANCH-EXISTS verdict, §6 shared defect-class taxonomy are written once here; F-36/F-37/F-45's
own DIAGNOSIS.md files are short and reference this one for the parts that are identical).

## 1. Live reproduction — REPRODUCES

`ganita_condition_get(chart_id=482012f1-710e-4a25-994a-93821f5871aa, facet='dignity', limit=3)`:

```json
{"content": {"facet": "dignity", "rows": [ /* 3 rows */ ], "total": 3}}
```

`total: 3` — wrong. It is the count of the page just returned, not the true row count for this
facet.

`ganita_condition_get(chart_id=482012f1-710e-4a25-994a-93821f5871aa, facet='dignity', limit=25000)`:

```json
{"content": {"rows": [ /* … */ ], "total": 563}, "trim_report": [
  {"path": "rows", "original_count": 563, "kept_count": 70, "reason": "rows: trimmed to 70", ...}
]}
```

`total: 563` at this limit — this happens to be the TRUE row count for the `dignity` facet on
this chart, but only because `limit=25000` was set high enough that `SELECT ... LIMIT $3` (with
`$3=25000`) never truncated the underlying query — `result.rows.length` (563) and the real
`COUNT(*) WHERE chart_id=… AND fact_category = ANY(...)` (also 563) coincide by construction, not
by design. Both reproductions confirmed live, exactly as the finding predicted.

**A second, compounding observation not in the original finding text:** at `limit=25000` a
SEPARATE, generic, downstream response-budget trimmer (S2's own `response_budget.ts` machinery,
invoked somewhere between this handler's return and the MCP envelope being serialized) trims the
served `rows` array further, from 563 down to 70 (`trim_report` above), but does **not** touch
`content.total` — which still reads 563. So in this one call, `content.total` (563) is
accidentally the true full-catalog count, while the actually-served `rows` array has only 70
entries. Two independent bugs are stacked here: (a) `total` was never an independent COUNT in
the first place (F-12's own claim), and (b) a downstream trim can silently diverge the served
array from whatever number happened to be in `total` at handler-return time, regardless of
whether that number was itself honest. See §6 for why this second observation is diagnostic of a
DIFFERENT (but related) failure mode than (a), and why it matters for the BRANCH-EXISTS verdict.

## 2. Claim decomposition

- **F-12a:** `content.total` on `ganita_condition_get`'s `dignity`/`avasthas`/`karakas` facets is
  computed as `result.rows?.length ?? 0` — the length of the page just fetched (bounded by
  `LIMIT $3 OFFSET $4`), not an independent `COUNT(*)` over the full matching set.
- **F-12b (implicit, confirmed by contrast):** the SAME tool's sibling file in the same
  directory, `get_condition_composite.ts`, does this correctly (two parallel queries — the page
  fetch AND a `SELECT COUNT(*) ...` — `Promise.all`'d together, `total_matching` field). This
  proves the correct pattern already exists in the codebase; F-12 is not "nobody knew how," it's
  "three call sites didn't do what a fourth, adjacent call site already does."
- **F-12c (implicit):** no disclosure anywhere in the response that `total` is page-scoped rather
  than corpus-scoped — a caller reading `total: 3` at `limit=3` has no way to know 563 rows
  actually exist for this facet.

## 3. Mechanism → file:line — confirmed, line numbers verified against `origin/main` tip

**`get_dignity.ts:85`** (worktree read at
`.claude/worktrees/par-s2-main-ro/platform/src/lib/retrieval/registry/layers/L1_ganita/get_dignity.ts`,
line numbers exact, no drift from the finding's citation):
```ts
const result = await query<Record<string, unknown>>(sql, params)
return {
  content: { chart_id: chartId, categories, rows: result.rows ?? [], total: result.rows?.length ?? 0 },
  is_error: false,
}
```

**`get_avasthas.ts:72`** — identical pattern, same line number as cited:
```ts
return {
  content: { chart_id: chartId, categories, rows: result.rows ?? [], total: result.rows?.length ?? 0 },
  is_error: false,
}
```

**`get_karakas.ts:118`** — identical pattern (one extra field, `opt_in_categories_available`,
does not change the defect), same line number as cited:
```ts
return {
  content: {
    chart_id: chartId, categories, rows: result.rows ?? [], total: result.rows?.length ?? 0,
    opt_in_categories_available: KARAKA_OPT_IN_CATEGORIES,
  },
  is_error: false,
}
```

All three: the SQL itself is `SELECT ... FROM chart_facts WHERE chart_id=$1 AND fact_category =
ANY($2::text[]) [... optional filters ...] ORDER BY ... LIMIT $3 OFFSET $4` — one query, no
second `COUNT(*)`. `result.rows.length` can never exceed `limit`, so `total` is mathematically
capped at whatever the caller passed as `limit` (default 500/300/500 respectively), regardless of
how many rows actually match.

**Contrast, confirmed correct — `get_condition_composite.ts:87-99`:**
```ts
const [rowsRes, countRes] = await Promise.all([
  query(sql, [...params, limit]),
  query<{ total: string }>(`SELECT COUNT(*)::text AS total FROM ga_condition_composite WHERE ${where}`, params),
])
const total_matching = Number(countRes.rows[0]?.total ?? 0)
return {
  content: {
    chart_id, rows: rowsRes.rows, count: rowsRes.rows.length, total_matching,
    more_available: total_matching > rowsRes.rows.length, ...
  },
  is_error: false,
}
```
This is the same directory, same tool family, same fix shape F-12/F-37 need: a second,
independent `COUNT(*)` query over the same `WHERE` clause (minus `LIMIT`/`OFFSET`), run in
parallel, disclosed as a distinctly-named field (`total_matching`, not overloaded onto the
served-page length) plus a derived `more_available` boolean.

## 4. Sibling census — TWO layers of the same defect class, genuinely widespread

### 4a. Flavor A — `total`/`total_count` fields that are `rows.length` of a LIMIT-bounded query,
never a real `COUNT(*)` (F-12's and F-37's exact defect; F-36 is NOT this flavor, see F-36's own
doc)

`grep -rnE "(total|[a-zA-Z_]*_count)\s*:\s*[a-zA-Z_.]*\.(rows\.length|length)\b"` over
`platform/src/lib/retrieval/registry` and `platform-mcp/src/{tools,lib}`, excluding tests, then
filtered to sites where the surrounding query has its own `LIMIT`/`OFFSET`/`fetchLimit` (i.e. the
field genuinely COULD diverge from the true count, as opposed to a handler that already fetches
the full unbounded set on purpose):

| File:line | Field | Query bounded by |
|---|---|---|
| `L1_ganita/get_dignity.ts:85` | `total` | `LIMIT $3 OFFSET $4` (F-12, this finding) |
| `L1_ganita/get_avasthas.ts:72` | `total` | `LIMIT $3 OFFSET $4` (F-12, this finding) |
| `L1_ganita/get_karakas.ts:118` | `total` | `LIMIT $3 OFFSET $4` (F-12, this finding) |
| `L0_brahmagyan/query_yoga_catalog.ts:61` | `total` | `LIMIT $1 OFFSET $2` (F-37, sibling finding) |
| `L1_ganita/get_av_transit_gating.ts:348` | `total` | bounded fetch, same pattern |
| `L1_ganita/get_av_transit_gating.ts:439` | `total` | bounded fetch, same pattern |
| `L1_ganita/get_dasha_lord_capability.ts:271` | `total` | bounded fetch, same pattern |
| `L1_ganita/get_dashas.ts:575` | `total` | bounded fetch, same pattern |
| `L1_ganita/get_divisionals.ts:121` | `total` | bounded fetch, same pattern |
| `L1_ganita/get_graha_yuddha.ts:269` | `total` | bounded fetch, same pattern |
| `L1_ganita/get_positions.ts:265` | `total` | bounded fetch, same pattern |
| `L1_ganita/get_sade_sati.ts:104` | `total` (`all:true` branch) | `fetchLimit = requestedLimit` when `all:true` — caller's own limit, not a real total |
| `L1_ganita/get_sade_sati.ts:116` | `total` (default branch) | `pageRows.slice(offset, offset+requestedLimit).length` — page size, not total |
| `L1_ganita/get_sensitive_points.ts:153` | `total` | bounded fetch, same pattern |
| `L1_ganita/get_strength.ts:214` | `total` | bounded fetch, same pattern |
| `L0_brahmagyan/query_classical_texts.ts:242` | `total` | `citations.length`, bounded fetch |
| `L0_brahmagyan/query_classical_texts.ts:309` | `total` | bounded fetch |
| `platform-mcp/src/tools/register_p1_reference.ts:346` | `total` | bounded fetch |
| `platform-mcp/src/tools/register_p1_reference.ts:489` | `total` | bounded fetch |
| `platform-mcp/src/tools/register_p1_synthesis.ts:751` | `total` | `synth_tail_divergence_get` — bounded fetch |
| `platform-mcp/src/tools/registry_bridge.ts:2339` | `total_count` | `ranked.length` assigned onto `boundedArj` (needs a closer read — plausibly an intentional "true total before this call's own slice," see caveat below, but the naming/placement is the same risk shape) |
| `register_d8_assess_domain.ts:1816` | `total_count` | `result.rows.length` — bounded fetch |
| `register_d8_assess_domain.ts:635` | `total_count` | `ranked.length` — needs closer read, same caveat as `registry_bridge.ts:2339` |

**~20 sites found, well beyond the 2 named in the findings (F-12's 3 facets + F-37's 1 tool).**
This confirms the plan's suspicion in the assignment brief: Flavor A is a widespread,
copy-pasted pattern across `L1_ganita/*` and `L0_brahmagyan/*` retrieval handlers, not a one-off.
Two entries (`registry_bridge.ts:2339`, `register_d8_assess_domain.ts:635`) are flagged with a
caveat because `X.length` assigned as a "total" BEFORE that same array is sliced/bounded for
serving is actually the CORRECT disclosed-pagination shape (the same shape
`get_condition_composite.ts` uses) — a closer per-site read is needed at SPEC time to sort real
defects from correct-but-superficially-similar code. This list is Stage-D census output, not a
pre-verified defect list for every row.

### 4b. Flavor B — a real, accurate-at-construction `*_count`/narrative-count field that goes
stale because a GENERIC downstream budget trimmer shrinks its sibling array LATER, without
re-deriving or invalidating the count (F-45's defect class; not F-12's own bug, but the same
family — see §6)

This is the F-45 finding's own class (full detail in `F-45/DIAGNOSIS.md`); confirmed live for all
5 of F-45's named tools. Listed here because it is the single most consequential sibling
discovery of this Stage-D pass: **every handler that (1) computes a narrative summary field from
an array's `.length` and (2) returns through `dualOutput`/`finalizeMcpBudget`/
`autoDetectTrimmableSections` (S2's generic trim machinery in `response_budget.ts`) is
structurally exposed**, whether or not a given call happens to trigger a trim. The `trim_report`
mechanism DOES disclose the true original count in a separate part of the envelope in most of
these cases (see `F-45/DIAGNOSIS.md` §3) — but the narrative field itself never points at
`trim_report`, so a caller reading only the narrative field is misled. F-12/F-37's own `total`
field has NO such partial safety net: at low `limit`, no trim ever fires (the payload is tiny),
so there is no `trim_report` at all to cross-reference — F-12/F-37 are the WORSE case of the two
flavors, not a lesser one.

## 5. BRANCH-EXISTS verdict — WRONG for F-12 (and, per the companion docs, wrong for F-36/F-37,
partially-adjacent-but-not-a-fix for F-45)

The campaign board classifies F-12/F-36/F-37/F-45 as `BRANCH-EXISTS(adopt ekv/a-09-sara-kernel,
needs extension)`. Checked directly against the branch:

```
$ cd .claude/worktrees/ekv-a-09 && git log --oneline -2 && git diff origin/main...HEAD --stat
ceadae8cb ekv(a-09): F-56/F-111 — sāra composition for assess_* (buildAssessResponse)
dcc2fb5ad ekv(a-09): F-56/111 — sāra kernel API freeze (SaraKernel + assembleSaraContent)
 platform-mcp/src/lib/response_budget.ts   | 175 ++++++++++++++++++++++++++++++
 platform-mcp/src/tools/registry_bridge.ts |  83 +++++++++++++-
 2 files changed, 253 insertions(+), 5 deletions(-)
```

`ekv/a-09-sara-kernel`'s **entire** committed diff is two files, and its own commit messages say
exactly what it is: `SaraKernel`/`assembleSaraContent`/`buildAssessResponse`, built for **F-56 and
F-111** (CL-05 — the `assess_*` tools' structural blindness to large OBJECT-shaped sections,
which is a real, different, already-diagnosed defect). None of `ganita_condition_get`,
`ganita_chart_facts_get`, `ref_yogas_get`, `bodha_signals_get`, `synth_chart_brief_get`,
`kala_priority_ranking_get`, `kala_windows_get`, or `bodha_remedies_get` — the eight tools these
four findings actually touch — are `assess_*` tools, and none of their handler files
(`get_dignity.ts`, `get_avasthas.ts`, `get_karakas.ts`, `query_yoga_catalog.ts`,
`register_d7_channel.ts`, `register_p1_aliases.ts`, `register_p1_synthesis.ts`,
`call_service_wrappers.ts`, `query_temporal_activation.ts`, `query_remedies.ts`) are touched by
this branch at all.

**Verdict for F-12 specifically: BRANCH-EXISTS is wrong.** F-12's bug is wrong SQL/count
arithmetic inside three L1 retrieval handlers — a missing `SELECT COUNT(*)` sibling query,
exactly the pattern `get_condition_composite.ts` already demonstrates in the same directory.
There is nothing in `SaraKernel`/`assembleSaraContent`/`buildAssessResponse` to "extend" toward
this — those functions compose and budget an `assess_*` response's OBJECT-shaped sections; they
do not touch, and were never designed to touch, a `total` field inside an L1 fact-retrieval
handler three layers below where `assess_*` composition happens. Adopting the branch and trying
to "extend" it would mean writing genuinely new code in genuinely different files — which is just
"OPEN, full pipeline," dressed up as an adoption. F-37 is the same verdict for the same reason
(same Flavor A defect, same wrong file family). See `F-36/DIAGNOSIS.md` and `F-45/DIAGNOSIS.md`
for their own (also negative, with one narrow caveat for F-45) verdicts.

## 6. Blast radius

- **File ownership vs S2's lease:** `get_dignity.ts`/`get_avasthas.ts`/`get_karakas.ts` live
  under `platform/src/lib/retrieval/registry/layers/L1_ganita/**`. Per
  `git show origin/par/coordination:00_ARCHITECTURE/briefs/parisesa/LEASES.json`, this path is
  explicitly owned by **S5 MŪLA** ("platform (L1_ganita/** query files)"), not S2. S2's own OWNS
  list is `response_budget.ts`, `registry_bridge.ts`, and 5 named `kala_views/*.ts` files — none
  of which contain F-12's mechanism. **This finding is OUT OF S2's file lease.** A
  `PAR-F12-NEEDS-LEASE` note is filed alongside this doc (see `NEEDS_LEASE.md` in this lane).
- **§N controls touched:** §N.6 (Serving Density) item 4 ("density signaling is data, not
  narration") — a `total` field IS exactly this kind of density-signaling data, and F-12 is a
  case of it being fabricated rather than computed. §N.7 is adjacent (narration fidelity) but not
  precisely on point — this is a raw retrieval field, not a graded/narrated sentence.
- **CL-00 controls:** not assessed in this DIAGNOSE pass (out of the 27-control cheap-subset
  scope); note for SPEC stage.
- **Other lanes sharing these files:** none of S2's other findings (F-13, F-28, F-56, F-111,
  F-112, F-122, F-14, F-15, F-46, F-124, F-125, F-44) touch `L1_ganita/get_dignity.ts` /
  `get_avasthas.ts` / `get_karakas.ts`. F-37 (sibling, same defect class) touches a DIFFERENT file
  (`L0_brahmagyan/query_yoga_catalog.ts`) — no direct file collision, but the fix pattern should
  be specced once and applied to both (and to the Flavor-A census in §4a) rather than four times
  independently.
- **A-09 sāra-kernel:** confirmed NOT touching any of F-12's three files (see §5). No blast
  radius overlap.

## Evidence

Live JSON captured this session for `ganita_condition_get(facet='dignity', limit=3)` and
`ganita_condition_get(facet='dignity', limit=25000)` (both above, full envelopes in the session's
tool-call transcript — not re-saved to a separate file per the campaign's context-hygiene note,
the exact `total` values and `trim_report` are quoted verbatim above).
