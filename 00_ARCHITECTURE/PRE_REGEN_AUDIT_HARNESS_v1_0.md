---
artifact: PRE_REGEN_AUDIT_HARNESS_v1_0.md
canonical_id: PRE_REGEN_AUDIT_HARNESS
version: 1.0
status: CURRENT
authored_by: Claude (Cowork) 2026-06-26
purpose: >
  Reusable audit toolbox for the Pre-Regeneration Full Audit Campaign (Waves 1–5).
  Provides parameterisable SQL query templates for Axis B data-correctness checks,
  the 3-axis per-asset rubric, the live grep command for Axis A contamination
  class detection, and the DB connection recipe.
applies_to: PRE_REGEN_FULL_AUDIT_CAMPAIGN_v1_0.md (Wave 1 onward)
changelog:
  - version: 1.0
    date: 2026-06-26
    author: Claude (Cowork)
    note: Initial creation from Wave 0 audit design.
---

# Pre-Regeneration Audit Harness v1.0

## §1 — DB Connection Recipe

All SQL templates below are run against the production DB via:

```bash
psql -h 127.0.0.1 -p 5433 -U amjis_app -d amjis -c "<SQL here>"
```

Replace `<SQL here>` with the parameterised query after substituting all
`{placeholder}` values for the specific asset under audit.

For multi-line queries, use `-f <file.sql>` instead of `-c`.

---

## §2 — SQL Query Templates (Axis B — Data Correctness)

Placeholders used throughout:

| Placeholder | Meaning |
|---|---|
| `{table}` | The DB table for this asset (e.g. `chart_facts`, `bodha_laksana`) |
| `{chart_id}` | The native chart UUID (`482012f1-710e-4a25-994a-93821f5871aa`) or a non-native UUID |
| `{asset_id}` | The asset_id string as registered in `asset_registry` (e.g. `ga_nakshatra`) |
| `{natural_key_cols}` | Comma-separated column(s) forming the natural key (e.g. `chart_id, graha`) |
| `{value_col}` | A column whose distribution is being inspected (e.g. `rashi_id`, `planet_name`) |
| `{required_col1}` | A column that must be non-null for every row |
| `{required_col2}` | A second column that must be non-null for every row |
| `{non_native_chart_id}` | A non-native chart UUID for cross-chart isolation checks |

---

### B1 — Count Query (Cockpit Truth Check)

Verifies the actual row count for a chart and cross-checks the asset's
`count_sql` in `asset_registry`. The registered `count_sql` must agree with
the direct count; if it does not, it is the L1 trap (cockpit reads `count_sql`,
not `asset_throughput`).

**Step 1 — Direct count:**
```sql
SELECT COUNT(*) AS actual_rows, '{chart_id}' AS chart_id
FROM {table}
WHERE chart_id = '{chart_id}';
```

**Step 2 — Retrieve the registered count_sql:**
```sql
SELECT asset_id, count_sql
FROM asset_registry
WHERE asset_id = '{asset_id}';
```

**Step 3 — Execute the retrieved count_sql** (substitute it verbatim) and
compare the result with Step 1. Mismatch = **FAIL**.

---

### B2 — Row-Count vs Target Floor

Checks that every chart meets the known minimum row count for this asset.
The `target_floor` is the minimum acceptable value established after a clean
build (per §N.4 "floors are aspirational, not gates" — set it from the achieved
count, never fabricate rows to hit a number).

```sql
SELECT chart_id, COUNT(*) AS row_count
FROM {table}
GROUP BY chart_id
ORDER BY row_count;
-- Compare min(row_count) with known target_floor for this asset.
-- Any chart below target_floor = FAIL.
```

---

### B3 — Distribution Check (Degenerate Collapse Detector)

A `{value_col}` that should vary across rows but shows only 1 distinct value
is a degenerate collapse — the canonical example is the `kala_convergence` bug
where every row showed `Jupiter` regardless of chart position.

```sql
SELECT {value_col}, COUNT(*) AS occurrences
FROM {table}
WHERE chart_id = '{chart_id}'
GROUP BY {value_col}
ORDER BY occurrences DESC
LIMIT 20;
-- Expected: multiple distinct values.
-- Single value dominating 100% of rows = degenerate collapse = FAIL.
```

---

### B4 — Null / Completeness Check

Verifies that required columns are populated for every row in the chart.

```sql
SELECT
  COUNT(*)               AS total_rows,
  COUNT({required_col1}) AS col1_present,
  COUNT({required_col2}) AS col2_present
  -- Extend with additional required columns per asset spec.
FROM {table}
WHERE chart_id = '{chart_id}';
-- total_rows = col1_present = col2_present = PASS.
-- Any column count < total_rows = FAIL (nulls present).
```

---

### B5 — Duplicate Check (Natural-Key Integrity)

Finds duplicate rows on the natural key. Zero rows returned = PASS.

```sql
SELECT {natural_key_cols}, COUNT(*) AS dup_count
FROM {table}
WHERE chart_id = '{chart_id}'
GROUP BY {natural_key_cols}
HAVING COUNT(*) > 1;
-- Zero rows = PASS.
-- Any rows returned = duplicate natural-key violation = FAIL.
```

---

### B6 — Referential Integrity (fact_id / citation_ref Resolution)

For assets that store `fact_id` references (e.g. in a `constituent_facts_array`
column or a `fact_id_ref` column), verifies every reference resolves back to
`chart_facts`. Any dangling reference = FAIL.

```sql
-- Adjust column name {fact_id_ref_col} to match the asset's actual column.
SELECT t.{fact_id_ref_col} AS fact_id_ref,
       (cf.fact_id IS NOT NULL) AS resolves
FROM {table} t
LEFT JOIN chart_facts cf
       ON cf.fact_id  = t.{fact_id_ref_col}
      AND cf.chart_id = '{chart_id}'
WHERE t.chart_id = '{chart_id}'
  AND t.{fact_id_ref_col} IS NOT NULL;
-- All rows: resolves = true = PASS.
-- Any resolves = false = dangling fact_id = FAIL.
```

---

### B7 — Per-Chart Isolation (Contamination Data Check)

For a known non-native chart, verifies that a key differentiator field does NOT
hold the native chart's value. If it does on every non-native chart, the builder
silently injected native data into a foreign chart's rows.

```sql
-- Discover a non-native chart_id:
SELECT chart_id FROM charts
WHERE chart_id != '482012f1-710e-4a25-994a-93821f5871aa'
LIMIT 1;

-- Then check a differentiator column (example: Sun sign must differ from
-- native Capricorn for most non-native charts):
SELECT chart_id, graha, rashi_id
FROM chart_facts
WHERE chart_id = '{non_native_chart_id}'
  AND graha = 'Su';
-- If rashi_id = 'Capricorn' for every non-native chart when random diversity
-- is expected → native data contamination = FAIL.
-- Native reference: chart_id = '482012f1-710e-4a25-994a-93821f5871aa'
```

---

## §3 — Axis A: Contamination Class Detection (Live Grep)

Run this grep from the project root to surface all Python files that reference
native-specific birth data, native identifiers, or hardcoded birth parameters
that could produce silent contamination when processing a non-native chart:

```bash
grep -rlE \
  "NATIVE_BIRTH|birth_params or |CANONICAL_CHART_ID|NATIVE_CHART_ID|1984-02-05" \
  platform/python-sidecar \
  --include="*.py" \
| grep -vE "venv|__pycache__|/tests?/|/test_|_test"
```

Each file returned by the grep is classified into one of four contamination
classes (see §4). Classification drives the Axis A verdict for that file.

---

## §4 — Contamination Classification Taxonomy

| Class | Definition | Axis A Verdict |
|---|---|---|
| **CHART-INDEPENDENT** | File contains no native-specific hardcoding. All birth parameters are received as arguments or fetched from the DB by chart_id. Safe for multi-chart operation. | PASS |
| **NATIVE-ONLY-BY-DESIGN** | File is legitimately scoped to the native chart (e.g., an ephemeris build script, a native-only analysis). Hardcoding is intentional and documented. Not a bug — but must be verified that the scope is truly intentional. | PASS (with note) |
| **CORRECTLY-GUARDED** | File references native data but has an explicit guard that raises or rejects non-native input before the native-specific path executes. Guard must be verified to be on every entry point. | PASS (guard verified) |
| **VULNERABLE** | File references native-specific data and has no effective guard. A non-native chart_id passed to this file may silently receive native data in its output. | FAIL — fix required |

**Classification rule:** When in doubt, classify as VULNERABLE and investigate.
A file that looks CORRECTLY-GUARDED must have its guard verified in code, not assumed.

---

## §5 — Per-Asset Audit Checklist (3-Axis Rubric)

Each audited file is assessed on three axes. Run the applicable checks for the
file's layer and asset type. Mark each axis cell as PASS, FAIL, WARN, or N/A
with a brief note.

### Axis A — Contamination Guard

| Check | What it tests |
|---|---|
| A1 | Grep classification (§3 + §4): CHART-INDEPENDENT / NATIVE-ONLY-BY-DESIGN / CORRECTLY-GUARDED / VULNERABLE |
| A2 | Idempotency pattern (§N.3): delete-then-insert for L1+; upsert only for L0 reference tables |
| A6 | No hardcoded native birth date / coordinates / chart_id in the execution path |
| A7 | No "no row → return None" silent failure for non-native chart lookup (must raise) |

### Axis B — Data Correctness (SQL templates §2)

| Check | Template |
|---|---|
| B1 | Count query vs asset_registry.count_sql agreement |
| B2 | Row count ≥ target_floor for every chart |
| B3 | Distribution check — no degenerate collapse on key value columns |
| B4 | Null / completeness check on required columns |
| B5 | No duplicate natural-key rows |
| B6 | All fact_id / citation_ref references resolve in chart_facts |
| B7 | Per-chart isolation — non-native chart does not carry native values |

### Axis C — Structural Conformance

| Check | What it tests |
|---|---|
| C1 | WriterBase conformance: `@register`, `run(ctx)` / `plan_substeps + run_substep`, `ctx.db_conn` never committed by writer, no `_telemetry`, returns `WriterResult` |

*Note: Axis B checks require a live DB connection. Axis A and C checks are
static (grep + code read). Run A and C first; B when DB access is available.*

---

## §6 — Per-Asset Findings Row Format

Each audited file produces one row in `PRE_REGEN_AUDIT_FINDINGS_REGISTER_v1_0.md`.
Column definitions:

```
asset_id / file           | layer       | A1 class          | A2   | A6   | A7   | B1   | C1   | VERDICT       | severity | fix summary
--------------------------|-------------|-------------------|------|------|------|------|------|---------------|----------|------------
<relative path from root> | <layer tag> | <taxonomy class>  | P/F/W/N | P/F/W/N | P/F/W/N | P/F/W/N | P/F/W/N | PASS / FIX-REQUIRED / REVIEW-NEEDED | none/minor/major/blocker | <one-line fix or "None">
```

**Severity levels:**

| Level | Meaning |
|---|---|
| `none` | No action required |
| `minor` | Should fix before regeneration but will not corrupt multi-chart output |
| `major` | Will produce wrong output for at least one chart if not fixed |
| `blocker` | Silently contaminates non-native charts with native data; must fix before any regeneration |

**VERDICT rules:**
- `PASS` — all applicable axes pass; no fix required
- `FIX-REQUIRED` — one or more axes fail; fix must be applied before regeneration
- `REVIEW-NEEDED` — finding is ambiguous or scope is uncertain; native must decide

---

## §7 — Reference: Native Chart Identifiers

These values are fixed constants for all audit queries.

| Item | Value |
|---|---|
| Native chart_id | `482012f1-710e-4a25-994a-93821f5871aa` |
| Native birth date | `1984-02-05` |
| Dead phantom chart_id (never write) | `362f9f17-…` |
| Non-native benchmark chart (Abhinandan) | `1c826d5a-…` (full UUID from `charts` table) |

---

*End of PRE_REGEN_AUDIT_HARNESS_v1_0.md*
