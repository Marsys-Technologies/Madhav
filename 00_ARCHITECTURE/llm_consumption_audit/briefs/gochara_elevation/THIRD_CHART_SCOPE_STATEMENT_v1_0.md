---
artifact: THIRD_CHART_SCOPE_STATEMENT
campaign: PARISHKARA (MR-34)
remediation_item: MR-34
version: 1.0
status: CURRENT
authored: 2026-08-10
---

# Third-Chart Scope Statement — v1-Authority Intentional

## §1 — Chart identity

| Field | Value |
|---|---|
| Chart ID (full UUID) | `cb73cd3d-9eba-4220-9902-0de91566e980` |
| Short name | Kiran |
| Role | Entitled family chart; granted to principals `EiThXD5YRPfzwfoAtYeGDXHxsTv2` and `t0sSkP1qeoegmWESi7P50QNFMgF3` |
| Canonical reference | `BEYOND_ACHARYA_MASTER_IMPLEMENTATION_PLAN_v1_0.md` §1 ("entitled family charts … Kiran `cb73cd3d-…`") |

## §2 — Current state (as of 2026-08-10)

DB verification note: the PARISHKARA proxy at port 5434 was not accessible during authoring.
Row counts are taken from the prior conductor audit (MR-34 source record).

- **`kala_gochara_windows` rows:** 2,667 rows with `generation = 'v1'`
- **`gochara_resonance_map` resonance classes:** 3 classes present
- **`kala_gochara_authority` row:** ABSENT — no row exists for this chart_id

Because no `kala_gochara_authority` row exists, the `AUTHORITATIVE_GENERATION_FILTER` in
`register_gochara_windows.ts` resolves to `'v1'` via its COALESCE fallback (see §4 below).
The chart therefore serves v1-generation windows by default. This is correct behaviour,
not a serving gap.

Native's canonical chart (`482012f1-710e-4a25-994a-93821f5871aa`) was elevated to g3_* authority
during GOCHARA-UTKARSA via an explicit `kala_gochara_authority` row. The third chart (cb73cd3d)
was not included in that elevation scope — it remains on v1-authority until the native explicitly
commissions otherwise.

## §3 — Scope decision

**v1-authority is intentional for chart cb73cd3d-9eba-4220-9902-0de91566e980.**

This chart has not been authorized for g3_* (v3) elevation. It remains on v1-authority until
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
- No chart should be on an undocumented engine stance. This statement closes that gap for cb73cd3d.

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
3. The WHERE clause becomes: `AND kala_gochara_windows.generation = 'v1'`
4. All 2,667 existing rows for this chart carry `generation = 'v1'`, so all are served correctly.
5. If a future build lands g3_* rows for this chart without first inserting a
   `kala_gochara_authority` row, COALESCE still returns `'v1'` — the v1 rows continue to be
   served and the g3_* rows are silently excluded. This is the correct safety behaviour:
   elevation only takes effect when the authority row is explicitly inserted.

The accompanying code comment (lines 308–318, ADJUDICATION-6 / migration 527) states:
"An ABSENT `kala_gochara_authority` row means 'v1' authoritative BY DEFINITION (never requires
a seeded row)."

**Verification verdict: COALESCE correctly defaults to 'v1' for charts with no authority row.
No code fix is required.**

## §5 — Constraints on MR-02 and MR-24

### MR-02 constraint

`computeGocharaCoverage` (and any authority-aware coverage source selector) must handle a
chart_id with no `kala_gochara_authority` row honestly: it must return coverage=0 or an empty
result, never a 500 error or a fabricated "elevated" answer. The v1-authority charts keep
reading the sweep asset; the gate must not fail closed on `cb73cd3d` after v3 becomes the
default for elevated charts.

Specifically: `cb73cd3d` is the named v1-authority test case for MR-02's honest-empty coverage
path. Any refactor of the coverage selector must preserve this behaviour.

### MR-24 constraint

The product E2E battery (MR-24) must include `cb73cd3d-9eba-4220-9902-0de91566e980` as the
v1-authority chart in the probe suite. The committed battery covers 3 tools x 3 charts;
this chart occupies the "v1-authority" slot and must:
- Return correct v1 rows from `kala_gochara_windows_get`
- Return the correct resonance-class count (3 classes) from the resonance surface
- Not error on absence of a `kala_gochara_authority` row

Both MR-02 and MR-24 are cross-referenced in `MASTER_REMEDIATION_REGISTER_v2_0.md` §2.

## §6 — AT-PAR check

MR-34 AT-PAR gate: "no chart is on an undocumented engine."

As of this statement:
- Native chart `482012f1`: v1-authority elevated to g3_* — documented (GOCHARA-UTKARSA
  campaign, UTK-R2/R3 rulings, `kala_gochara_authority` row present).
- Abhinandan chart `1c826d5a`: same elevation — documented.
- Kiran chart `cb73cd3d`: v1-authority, no elevation — documented by this statement.

All three charts now have a recorded, intentional engine stance. AT-PAR gate satisfied.

## §7 — Elevation path (for reference, not current scope)

If the native later requests elevation of this chart to g3_* authority:
1. Run the g3_* sweep writer for `cb73cd3d` (same writer used for the two elevated charts).
2. Use the committed flip tooling (MR-08) to insert the `kala_gochara_authority` row:
   `flip(chart_id='cb73cd3d-9eba-4220-9902-0de91566e980', generation='g3_<campaign_id>')`.
3. Run the MR-24 probe battery to confirm the chart now serves g3_* rows correctly.
4. No code change to `register_gochara_windows.ts` is required — the COALESCE filter
   already handles both states.

## §8 — Recorded by

PARISHKARA campaign MR-34, 2026-08-10.
Authored by: Claude Sonnet 4.6 (PARISHKARA builder agent).
