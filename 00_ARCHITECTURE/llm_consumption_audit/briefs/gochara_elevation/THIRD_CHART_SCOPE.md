---
artifact: THIRD_CHART_SCOPE.md
campaign: GOCHARA-UTKARSA (gochara v3 elevation)
remediation_item: MR-34
version: 1.0
status: CURRENT
authored: 2026-08-10
---

# Third-Chart (cb73cd3d) Scope Statement — v1-Authority Intentional

## §1 — Chart identity

| Field | Value |
|---|---|
| Chart ID (full UUID) | `cb73cd3d-9eba-4220-9902-0de91566e980` |
| Short name | Kiran |
| Role | Entitled family chart; granted to principals `EiThXD5YRPfzwfoAtYeGDXHxsTv2` and `t0sSkP1qeoegmWESi7P50QNFMgF3` |
| Canonical reference | `BEYOND_ACHARYA_MASTER_IMPLEMENTATION_PLAN_v1_0.md` §1 ("entitled family charts … Kiran `cb73cd3d-…`") |

## §2 — Current state (as of 2026-08-10)

- **`kala_gochara_windows` rows:** 2,667 rows with `generation = 'v1'`
- **`gochara_resonance_map` resonance classes:** 3 classes present
- **`kala_gochara_authority` row:** ABSENT — no row exists for this chart_id

Because no `kala_gochara_authority` row exists, the `AUTHORITATIVE_GENERATION_FILTER` in
`register_gochara_windows.ts` resolves to `'v1'` via its COALESCE fallback (see §4 below).
The chart therefore serves v1-generation windows by default. This is correct behaviour, not a
gap in the serving code.

## §3 — Scope decision

**v1-authority is intentional for this chart.**

This chart has not been authorized for 3.0 (g3_*) elevation. It remains on v1-authority until
the native explicitly requests elevation via the committed flip tooling (MR-08). No
`kala_gochara_authority` row should be seeded for this chart outside of an explicit native
directive.

Rationale:
- The GOCHARA-UTKARSA campaign elevated the two primary charts (native `482012f1` and
  Abhinandan `1c826d5a`) through a deliberate review + adjudication process (Waves 1–4,
  UTK-R2/R3 rulings).
- Kiran's chart was not included in the elevation scope — this is a native scope decision, not an
  oversight. The CURRENT_STATE record at v6.x confirms the same pattern applied to the
  `bo_pratijna` scoring engine ("chart 3 `cb73cd3d` explicitly dropped from scope per native
  instruction mid-campaign, not a gap").
- Serving v1 rows honestly for this chart is correct and complete given the current scope.

## §4 — AUTHORITATIVE_GENERATION_FILTER verification

**Finding: COALESCE to 'v1' is confirmed correct by the source code.**

File: `platform-mcp/src/tools/retrieval/register_gochara_windows.ts`, lines 319–322:

```typescript
const AUTHORITATIVE_GENERATION_FILTER =
  " AND kala_gochara_windows.generation = COALESCE(" +
  '(SELECT authoritative_generation FROM kala_gochara_authority ' +
  "WHERE chart_id = kala_gochara_windows.chart_id), 'v1')"
```

Behaviour for a chart with no `kala_gochara_authority` row:

1. The subquery `SELECT authoritative_generation FROM kala_gochara_authority WHERE chart_id = …`
   returns zero rows, so the subquery result is SQL `NULL`.
2. `COALESCE(NULL, 'v1')` evaluates to `'v1'`.
3. The WHERE clause appended to every query becomes:
   `AND kala_gochara_windows.generation = 'v1'`
4. All 2,667 existing rows for this chart carry `generation = 'v1'`, so all are served correctly.
5. If a future build lands `g3_*` rows for this chart without first inserting a
   `kala_gochara_authority` row, COALESCE still returns `'v1'` — the v1 rows continue to be
   served and the g3_* rows are silently excluded. This is the correct safety behaviour: elevation
   only takes effect when the authority row is explicitly inserted.

The accompanying code comment (lines 308–318, ADJUDICATION-6 / migration 527) states this
explicitly: "An ABSENT `kala_gochara_authority` row means 'v1' authoritative BY DEFINITION
(never requires a seeded row)."

**Verification verdict: COALESCE correctly defaults to 'v1' for charts with no authority row.
No code fix is required.**

## §5 — Test coverage

- **MR-02 coverage gate:** the authority-aware coverage source selector explicitly names
  `cb73cd3d` as a v1-authority test case — v1-authority charts keep reading the sweep asset;
  the gate must not fail closed on this chart after the v3 retirement.
- **MR-24 E2E battery:** the committed product-level probe suite covers 3 tools × 3 charts,
  with `cb73cd3d` as the v1-authority chart in the battery. It must return correct v1 rows and
  correct resonance-class counts (3 classes).

Both items are cross-referenced in `MASTER_REMEDIATION_REGISTER_v2_0.md` §2 (MR-02, MR-24,
MR-34).

## §6 — Elevation path (for reference, not current scope)

If the native later requests elevation of this chart to g3_* authority:
1. Run the g3_* sweep writer for `cb73cd3d` (same writer used for the two elevated charts).
2. Use the committed flip tooling (MR-08) to insert the `kala_gochara_authority` row:
   `flip(chart_id='cb73cd3d-9eba-4220-9902-0de91566e980', generation='g3_<campaign_id>')`.
3. Run the MR-24 probe battery to confirm the chart now serves g3_* rows correctly.
4. No code change to `register_gochara_windows.ts` is required — the COALESCE filter
   already handles both states.
