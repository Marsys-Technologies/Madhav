# F-37 — DIAGNOSIS

Stream: S2 MĀTRĀ (as filed) · Class: CL-06, grouped with F-12/F-36/F-45 — **see
`F-12/DIAGNOSIS.md` for the shared Flavor-A defect-class taxonomy, the full sibling census, and
the BRANCH-EXISTS methodology; this doc covers what's specific to F-37.**
File: `platform/src/lib/retrieval/registry/layers/L0_brahmagyan/query_yoga_catalog.ts`
Stage: D (DIAGNOSE) · Chart-agnostic tool (global scope, no `chart_id`)

## 1. Live reproduction — REPRODUCES

`ref_yogas_get()` (no args, default `limit=100, offset=0`): payload too large for this session's
tool-result budget (85,164 chars) — the catalog genuinely has well over 100 rows; not needed for
the reproduction below, superseded by the two smaller calls that directly prove the claim.

`ref_yogas_get(offset=50, limit=10)`:
```json
{"content": {"rows": [ /* 10 rows, alphabetically "Danda"…"Dhana (Gṛhādhipati) Yoga" */ ], "total": 10}}
```

`ref_yogas_get(offset=999999)` (default limit=100):
```json
{"content": {"rows": [], "total": 0}}
```

`total` reads 10 at one page and 0 at another — for the SAME global catalog, which cannot itself
have changed between calls. This is definitive proof `total` is not counting the catalog; it is
counting whatever `rows` this particular page happened to return. Confirmed exactly as claimed.

## 2. Claim decomposition

- **F-37a:** `total` is `rows.length` (the served page's size), not a `COUNT(*)` over the whole
  `brahma_yoga_catalog` table (or the filtered subset matching `yoga_name`/`tradition`/`domain`).
- **F-37b (implicit, confirmed by the two-call proof above):** because of (a), `total` VARIES with
  `offset`/`limit` for an unchanging underlying dataset — the field is actively misleading, not
  merely incomplete, since a caller paging through results would see a different "total" on every
  page.

## 3. Mechanism → file:line — confirmed, exact line match, no drift

**`query_yoga_catalog.ts:61`** (matches the finding's citation exactly):
```ts
const result = await query<Record<string, unknown>>(sql, params)
const rows = result.rows ?? []
const filtered = Boolean(args.yoga_name || args.tradition || args.domain)
return {
  content: {
    rows,
    total: rows.length,
    ...(rows.length === 0 && filtered ? { empty_reason: `...` } : {}),
  },
  is_error: false,
}
```
The query itself (`:50-54`):
```ts
let sql = `SELECT * FROM brahma_yoga_catalog WHERE 1=1`
if (args.yoga_name) { sql += ` AND name_en ILIKE $${...}`; ... }
if (args.tradition)  { sql += ` AND LOWER(school) = LOWER($${...})`; ... }
if (args.domain)     { sql += ` AND LOWER(category) = LOWER($${...})`; ... }
sql += ` ORDER BY school, name_en LIMIT $1 OFFSET $2`
```
One query, `LIMIT`/`OFFSET` bound, no second `COUNT(*)`. Identical shape to F-12's three
`L1_ganita` sites — same fix pattern applies verbatim: a parallel
`SELECT COUNT(*) FROM brahma_yoga_catalog WHERE <same filters, minus LIMIT/OFFSET>`, run
alongside the page fetch (see `F-12/DIAGNOSIS.md` §3's `get_condition_composite.ts` contrast for
the established in-codebase correct pattern).

## 4. Sibling census

Covered by the shared Flavor-A census in `F-12/DIAGNOSIS.md` §4a — `query_yoga_catalog.ts:61` is
listed there alongside ~19 other sites of the identical pattern across `L0_brahmagyan/*` and
`L1_ganita/*`. Not re-duplicated here.

## 5. BRANCH-EXISTS verdict — WRONG, same reasoning as F-12

Per `F-12/DIAGNOSIS.md` §5: `ekv/a-09-sara-kernel`'s entire diff is `response_budget.ts` +
`registry_bridge.ts`, scoped to `assess_*` response composition (F-56/F-111). `ref_yogas_get` is
not an `assess_*` tool; `query_yoga_catalog.ts` is untouched by the branch. There is no
"extension" of `SaraKernel`/`assembleSaraContent` that could fix a missing `COUNT(*)` query
inside an L0 reference-catalog handler — this is a fresh, small, unrelated fix (one additional
SQL query + one renamed/added field), not a composition-layer problem at all. Same verdict as
F-12: **BRANCH-EXISTS is wrong; this is OPEN, full pipeline** (though a cheap one — the fix shape
is already proven correct elsewhere in the codebase).

## 6. Blast radius

- **File ownership vs S2's lease:** `query_yoga_catalog.ts` is under
  `platform/src/lib/retrieval/registry/layers/L0_brahmagyan/**`. Per
  `git show origin/par/coordination:00_ARCHITECTURE/briefs/parisesa/LEASES.json`, S5 MŪLA's OWNS
  list explicitly includes "capability SQL under layers/L0_*" — this file is squarely S5's, not
  S2's. **This finding is OUT OF S2's file lease**, same situation as F-12. No separate
  `NEEDS_LEASE.md` filed for F-37 individually since it is the identical lease gap as F-12 against
  the identical target stream (S5) — the conductor can route both findings together; see
  `F-12`'s `NEEDS_LEASE.md` for the one filed note covering this file family.
- **§N controls touched:** same as F-12 — §N.6 item 4 (density signaling is data, not narration).
- **Other lanes sharing this file:** none of S2's OWNS files intersect `L0_brahmagyan/**`. No
  collision with S2's other lanes.
- **A-09 sāra-kernel:** confirmed not touching this file.

## Evidence

Live JSON captured this session for `ref_yogas_get(offset=50, limit=10)` and
`ref_yogas_get(offset=999999)` (both quoted verbatim above). The unfiltered default call's raw
output was saved by the tool harness to
`/Users/Dev/.claude/projects/-Users-Dev-Vibe-Coding-Apps-Madhav/a025ddc3-60fc-4e4f-914a-5f61252972b9/tool-results/mcp-marsys-jis-direct-ref_yogas_get-1786866785834.txt`
(too large to inline; not needed since the two smaller calls above already prove the claim
definitively).
