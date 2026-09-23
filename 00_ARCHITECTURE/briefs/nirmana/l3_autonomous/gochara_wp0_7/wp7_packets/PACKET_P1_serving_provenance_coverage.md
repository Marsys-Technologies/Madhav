---
artifact: WP7_PACKET_P1
packet_id: P-1
version: "1.0"
status: DESIGN_ONLY_NOT_IMPLEMENTED
date: 2026-09-23
owner: "Owner of platform-mcp/src/tools/retrieval/register_gochara_windows.ts (+ the /api/mcp/db/query whitelist owner for §6)"
executes: GOCHARA_FAMILY_ELEVATION_PLAN_v2_1.md §6.2 P-1 (a–d), §4.7; GOCHARA_RULING_SHEET_v1_0.md N-10; WP0_FINDINGS.md consumer re-enumeration item 1 (E-004)
authority_note: "This packet is owed to its owner, not written into their file. Every anchor below was read at this checkout (branch l3/gochara-autonomous-wp0-7 @ fd13ec0a6; pin c58e86662 is an ancestor, source files identical)."
---

# P-1 — Serving provenance & coverage: manifest-driven for `'4.0'` and later

## 1. The failure mode this fixes (exact)

`buildSourceCitation(generation)` today branches on literal generation strings. Read at
`platform-mcp/src/tools/retrieval/register_gochara_windows.ts:573-598`:

```ts
function buildSourceCitation(generation: string | null | undefined): string {
  // ...
  if (generation === '3.0') {           // :579
    return ('kala_gochara_windows (L3 Kāla, W6.4 cutover ka_gochara materializer) — ...')
  }
  if (generation != null && (generation === 'g3_utkarsha' || generation.startsWith('g3_'))) {  // :586
    return ('kala_gochara_windows (L3 Kāla, GOCHARA-UTKARSA W3.4 ka_gochara_v3_century_materialize writer) — ...')
  }
  return (                              // :593 — the v1 fall-through
    'kala_gochara_windows (L3 Kāla, D-5 Lane G-4 ka_gochara_sweep writer) — ... generation=v1'
  )
}
```

Any generation that is not `'3.0'`/`g3_*` — including the family's new publication
generation `'4.0'` **and every later rebuild label `'4.1'`, `'4.2'`, …** — falls to the
v1 else-branch and is served with **false provenance** (it names the retired
`ka_gochara_sweep` writer and `generation=v1`). The plan (§4.7) already records why a
`g4_*` relabel is not an escape: a `g4_` prefix matches neither branch either. And a
hardcoded `=== '4.0'` branch would be the same bug recurring on first use: the first
rebuild republishes as `'4.1'` and falls straight back to the v1 fall-through. **The
branch must be manifest-driven, not string-matched.**

The same defect exists on the coverage axis. `computeGocharaCoverage`
(`:926-1000`) resolves the authority generation at `:963-966`:

```ts
const authGen = typeof authorityResp.rows[0]?.['authoritative_generation'] === 'string'
  ? authorityResp.rows[0]['authoritative_generation'] as string
  : 'v1'
const isV3Authority = authGen === '3.0' || authGen.startsWith('g3_')
```

and selects the substep-history asset at `:977`:

```ts
const substepAssetId = isV3Authority ? 'ka_gochara_v3_century_materialize' : 'ka_gochara_sweep'
```

For `'4.0'`, `isV3Authority` is **false**, so coverage attestation reads the *retired
sweep's* `build_substep_progress` history (`:995-1002`, `split_part(substep_key, ':year:', 1)`)
and misreports a fully-built chart as uncovered. P-1b routes any manifest-carrying
generation to `asset_id='ka_gochara'` and, when present, serves coverage **from the
`kala_gochara_coverage` manifest rows** instead of substep archaeology.

## 2. The contract the new branch serves (pinned shapes — do not paraphrase)

From `WP1_CONTRACTS.md` §5.2, `kala_gochara_publication` (one row per (chart_id,
generation)):

| column | type | notes |
|---|---|---|
| `manifest_id` | uuid PK | what authority's `evidence_ref` will name at WP10 |
| `chart_id` | uuid | |
| `generation` | text | `'4.0'`, `'4.1'`, … — bare string, never `g4_*` |
| `writer_asset_id` | text | `'ka_gochara'` |
| `convention_id` | text FK → `kala_gochara_convention` | the §1.1 `sha256:<hex>` id |
| `input_generation_vector` | jsonb | §5.3 pinned field-for-field |
| `ephemeris_backend` | jsonb | `{backend, retflag, se1_checksums}` from retflag |
| `horizon` | tstzrange | |
| `row_counts` | jsonb | `{contacts, coverage, windows}` |
| `content_digest` | text | sha256 over the canonical row set |
| `status` | text | `candidate`/`published`/`superseded`/`rolled_back` |

And `kala_gochara_coverage` (WP1_CONTRACTS §4.1, one row per (chart, generation,
partition)): `partition_kind ∈ {body_target, event_class, moon_on_demand}`,
`partition_key`, `requested_horizon`, `completed_horizon`, `resolution`,
`relations_searched`, `targets_requested/resolved/unresolved`,
`target_resolution_state_counts`, `unavailable_inputs`, `unsearched_reason`, `build_id`.

Provenance for a manifest-carrying generation is exactly:
`writer_asset_id` + `convention_id` + `manifest_id`. Coverage is exactly the set of
`kala_gochara_coverage` rows for `(chart_id, generation)`.

## 3. The design

### 3.1 Manifest lookup (one new query, shared by both call sites)

Add one fetch near the top of each tool handler that already resolves rows (the three
call sites today are `:1504`, `:1808`, `:2083`, plus the per-row election-avoidance
citation at `:2183`; the static defaults at `:1440`/`:1733`/`:2019` stay as-is):

```ts
// ── P-1: manifest-driven provenance/coverage (N-10) ─────────────────────
// One row per (chart_id, generation). NULL result = legacy generation
// ('v1' / '3.0' / g3_*), which keeps its existing string branches.
// The status filter admits candidate + published + superseded + rolled_back
// deliberately: provenance must remain honest for a rolled-back or superseded
// generation (the rows still exist; the citation must still name ka_gochara).
interface GocharaPublicationManifest {
  manifest_id: string
  chart_id: string
  generation: string
  writer_asset_id: string
  convention_id: string
  input_generation_vector: Record<string, unknown>
  ephemeris_backend: Record<string, unknown>
  horizon: string
  row_counts: { contacts?: number; coverage?: number; windows?: number }
  content_digest: string
  status: 'candidate' | 'published' | 'superseded' | 'rolled_back'
}

async function fetchPublicationManifest(
  chartId: string,
  generation: string | null | undefined,
  principal: Principal
): Promise<GocharaPublicationManifest | null> {
  if (generation == null) return null
  // Deliberately NOT generation-literal: any label with a manifest row resolves
  // here — '4.0' today, '4.1' after the first rebuild, '5.0' after the next
  // elevation. This is the entire fix for the hardcoded-'4.0' recurrence.
  const { rows } = await platformQuery(
    `SELECT manifest_id, chart_id, generation, writer_asset_id, convention_id,
            input_generation_vector, ephemeris_backend, horizon::text AS horizon,
            row_counts, content_digest, status
       FROM kala_gochara_publication
      WHERE chart_id = $1 AND generation = $2
      LIMIT 1`,
    [chartId, generation],
    principal
  ).catch(() => ({ rows: [] as Record<string, unknown>[] }))
  const r = rows[0]
  if (!r) return null
  return { ...(r as unknown as GocharaPublicationManifest) }
}
```

Failure mode of the lookup itself: degrade to `null` (legacy string branches) — never
throw, never fabricate a manifest. A missing manifest for a `'4.x'` generation is
surfaced through the coverage object (§3.4), not by inventing provenance.

### 3.2 `buildSourceCitation` — new signature, manifest-first dispatch

```ts
function buildSourceCitation(
  chartId: string,
  generation: string | null | undefined,
  manifest: GocharaPublicationManifest | null
): string {
  // P-1a (N-10): manifest-driven. Any generation carrying a
  // kala_gochara_publication row resolves provenance FROM THE MANIFEST —
  // never from a generation-literal match. '4.1' after a rebuild names
  // ka_gochara exactly as '4.0' did, because both have manifest rows.
  if (manifest != null) {
    return (
      `kala_gochara_windows (L3 Kāla, ${manifest.writer_asset_id} writer — ` +
      'contact ledger + search-coverage manifest per GOCHARA_FAMILY_ELEVATION_PLAN v2.1 §4.3–4.7; ' +
      `convention_id=${manifest.convention_id}; manifest_id=${manifest.manifest_id}; ` +
      `content_digest=${manifest.content_digest}; generation=${manifest.generation})`
    )
  }
  // Legacy fallbacks — string branches survive ONLY for generations with no
  // manifest row: 'v1', '3.0', g3_*. These three branches are unchanged.
  if (generation === '3.0') { /* existing branch, verbatim */ }
  if (generation != null && (generation === 'g3_utkarsha' || generation.startsWith('g3_'))) { /* existing */ }
  return /* existing v1 fall-through — now unreachable for any manifest-carrying generation */
}
```

The existing single-argument call sites change from
`buildSourceCitation(rawRows[0]?.generation ?? null)` to
`buildSourceCitation(chartId, rawRows[0]?.generation ?? null, manifest)` at `:1504`,
`:1808`, `:2083`; the per-row site at `:2183` becomes
`buildSourceCitation(chartId, row.generation ?? null, manifest)` (one manifest per
response — the `AUTHORITATIVE_GENERATION_FILTER` at `:640-643` already guarantees one
generation per response; keep that invariant and fetch the manifest once per tool call,
not per row). `SOURCE_CITATION_V1 = buildSourceCitation(null)` at `:602` becomes
`buildSourceCitation('', null, null)` (or keep a two-line wrapper) — its meaning
("citation for legacy v1 rows") is unchanged.

### 3.3 `computeGocharaCoverage` — manifest-driven asset_id and coverage source

At `:963-980`, replace the `isV3Authority` boolean with a three-way resolution:

```ts
const manifest = await fetchPublicationManifest(chartId, authGen, principal)
// P-1b: three regimes.
//   manifest != null  → '4.x' publication: substep asset is 'ka_gochara'
//                       (writer-owned, key format declared by the writer:
//                        '{event_class}::{partition_key}' — split on '::'),
//                       AND the coverage block prefers the kala_gochara_coverage
//                       manifest rows when any exist for (chart, generation).
//   authGen === '3.0' || startsWith('g3_') → existing v3 behaviour, verbatim.
//   otherwise → existing v1 behaviour, verbatim.
const isManifestGeneration = manifest != null
const isV3Authority = !isManifestGeneration && (authGen === '3.0' || authGen.startsWith('g3_'))
const substepAssetId = isManifestGeneration
  ? manifest.writer_asset_id           // 'ka_gochara'
  : isV3Authority ? 'ka_gochara_v3_century_materialize' : 'ka_gochara_sweep'
```

Substep key format for the manifest regime: `split_part(substep_key, '::', 1)` — the
same branch as v3 (`:986-994`), because the writer-owned substeps will reuse the
`{event_class}::{...}` shape; the plan's §6.3 row for `ka_gochara.has_substeps` declares
the format. **When ≥1 `kala_gochara_coverage` row exists for (chart, generation), the
served coverage object is derived from those rows** (`event_class` partitions map
classes to requested/completed horizon and targets_resolved/unresolved), and the
substep-based `swept_event_classes` axis is demoted to a `sweep_execution` sub-block
(preserved, not dropped — execution evidence stays visible). When zero coverage rows
exist (writer has not yet landed them), fall back to the substep-only object and say so
in the coverage object's `source` label. Never present substep history as coverage of
the searched horizon — that is the F-11/§N.8 class of error this packet exists to end.

### 3.4 P-1d — remove the `'v1'` COALESCE default (absent authority = `unpublished`)

Two sites carry the `COALESCE(..., 'v1')` fall-through; both change (N-10):

1. `AUTHORITATIVE_GENERATION_FILTER` at `:640-643`:

```ts
// Today:
" AND kala_gochara_windows.generation = COALESCE(" +
  '(SELECT authoritative_generation FROM kala_gochara_authority ' +
  "WHERE chart_id = kala_gochara_windows.chart_id), 'v1')"
// After: no COALESCE. The correlated subquery returns NULL for a chart with no
// authority row, and the comparison `generation = NULL` matches nothing — which
// is correct: an unflipped chart has no authoritative generation until WP10's
// flip. The handlers' existing empty-rows path (provenance_envelope.empty_reason,
// :1564) must gain one explicit reason string: 'unpublished'.
```

Note the adjacent comment block at `:629-639` (ADJUDICATION-6, "An ABSENT
kala_gochara_authority row means 'v1' authoritative BY DEFINITION") **must be rewritten**
when the code changes — it documents the old convention; leaving it would be a live lie.

2. `computeGocharaCoverage`'s authority read at `:963-965` and
   `reading_checklist.ts:1048-1050`/`:1069-1071` (owned by P-2's owner but the same
   predicate): absent row ⇒ `authGen = null` ⇒ the coverage object is served as
   **`unpublished`** — a first-class coverage object (`{status: 'unpublished',
   materialized_through: null, event_classes_covered: [], ...}` with a `note`), never a
   silent `'v1'`. `'v1'` remains authoritative **only** where an authority row literally
   says `authoritative_generation='v1'`.

### 3.5 P-1c — `peak_basis` vocabulary mirror (conditional)

`GENUINE_PEAK_BASES` at `:372` and `deriveResolutionDisclosure` at `:419` need **no
change for `'4.0'`**: the projection keeps emitting `peak_basis='gochara_lambda_v3_argmax'`
(`peak_basis_vocab.py` is shared). This packet's only ask: if the kernel projection ever
introduces a new basis value, the TS mirror at `:369-375` and the Python vocabulary must
change in the same PR — the existing comment already says "Mirrors
services/gochara_v3/peak_basis_vocab.py exactly". Recorded so the owner does not
discover it late; nothing to do now.

## 4. §6 — WP0 E-004 item 1: the `/api/mcp/db/query` whitelist (separate owner)

The three gochara serving tools were re-pointed off a private pool onto this proxy
(comment at `platform/src/app/api/mcp/db/query/route.ts:53-64`), so every query
`register_gochara_windows.ts` issues — including the new ones in §3.1/§3.3 — transits
the route's `ALLOWED_TABLES` set. Read at `route.ts:41`:

```ts
const ALLOWED_TABLES = new Set([
  // ...
  'kala_gochara_windows',   // :64
  // ...
  'kala_gochara_authority', // :71
  // ...
  'gochara_resonance_map',  // :84
  // ...
])
```

**What the whitelist owner must change:** add `'kala_gochara_coverage'` and
`'kala_gochara_publication'` to `ALLOWED_TABLES` (with the same style of dated comment:
read-only, chart-scoped, written only by the ka_gochara writer; the publication row is
written by the release authority's flip at WP10 and by the candidate pipeline,
never by any MCP-served query). `kala_gochara_contacts` is **not** required by P-1 —
this packet reads coverage and publication only; add it only when a future tool reads
contacts (P-4's capability will — leave that decision to P-4's owner). Until the
whitelist lands, the §3.1/§3.3 queries will 400 `"Table ... is not in the read-only
whitelist"` (the exact failure class the `bg_dignity_reference` comment at `:87-95`
documents) and the code degrades to legacy branches — honest, but P-1 is inert. **Order
the two PRs together or whitelist first.**

## 5. Acceptance tests (the two plan §6.2 tests, verbatim intent)

**Test 1 — manifest-driven provenance + republish stability.** On a disposable DB:
insert windows, an authority row `authoritative_generation='4.0'`, and a
`kala_gochara_publication` row (status `published`, `writer_asset_id='ka_gochara'`).
Assert `gochara_forecast_get`'s provenance names `ka_gochara` **and** names the
manifest id + convention id (i.e. it did not fall to the v1 branch). Then simulate the
rebuild: insert `'4.1'` windows + a `'4.1'` manifest row, re-point authority to
`'4.1'`. **The same test, unchanged, passes** — provenance still names `ka_gochara`.
A hardcoded `=== '4.0'` branch fails exactly here.

**Test 2 — coverage equals the manifest.** Same fixture: insert two
`kala_gochara_coverage` rows (e.g. `partition_kind='event_class'`,
`partition_key='marriage'` with `targets_resolved`/`targets_unresolved`, and one
`body_target` partition). Assert the served coverage object's class set, per-class
horizon, and resolution counts equal the manifest rows. Assert the substep axis is
present but labelled `sweep_execution`, not the coverage source.

**Test 3 — unpublished honesty (P-1d).** Chart with windows but **no** authority row:
assert `empty_reason='unpublished'` (or the coverage `status='unpublished'`), and that
no response anywhere names `generation=v1` provenance for it.

**Test 4 — regression guard for legacy.** Charts under `'v1'`, `'3.0'`, `g3_*`
authority with no manifest rows: provenance strings byte-identical to today's output
(snapshot the three existing strings before the change).

## 6. What this packet does NOT do

- It does **not** change `ROW_COLUMNS` (`:604-618`), the authority table's schema
  (527's table is unchanged per N-10), or anything in `kala_views/`.
- It does **not** flip any authority row or touch `generation='v1'`/`'3.0'`/rows —
  the WP10 release authority owns the flip; this packet only makes serving ready for it.
- It does **not** implement P-4's contact-ledger read capability, and it does not add
  `kala_gochara_contacts` to the whitelist (§4).
- It does not change the v1/`3.0`/`g3_*` string branches' text — they survive verbatim
  as legacy fallbacks.
- It does not touch `reading_checklist.ts` (P-2's file) beyond flagging that the same
  COALESCE predicate appears there.
