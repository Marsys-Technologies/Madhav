---
canonical_id: CLAUDECODE_BRIEF_MCP_REM_SESSION_B
version: 1.0
status: READY
authored: 2026-05-26
session_id: MCP-REM-SESSION-B
parent_plan: MCP_TOOL_AUDIT_REM_V2_PLAN_v1_0.md
description: >
  Data quality and retrieval logic fixes for 3 tools with DB/logic gaps:
  query_chart_facts (planet category 0 rows), query_signal_state (uniform 0.6
  confidence fallback), query_remedial_mantras (over-broad filter). Target: all
  3 tools to ≥88%.
---

# MCP-REM Session B — Data Quality Fixes

## §1 — Role and scope

You are executing three targeted fixes on the `platform` package:

1. **B.1 — `query_chart_facts`**: Seed the `planet` category rows into `chart_facts` DB. Currently 0 rows for planet → all planet-category queries score 0.
2. **B.2 — `query_signal_state`**: Replace the hardcoded `confidence ?? 0.6` fallback with a state-derived formula. All signals currently return uniform 0.6 regardless of activation state.
3. **B.3 — `query_remedial_mantras`**: Tighten the filter SQL to return domain-matched remedies only, not all remedies matching a loose term.

Sessions A and B are parallel-safe. B does not depend on A landing first.

---

## §2 — Mandatory reads before any edits

1. `00_ARCHITECTURE/BRIEFS/MCP_TOOL_AUDIT_REM_v2_PLAN_v1_0.md §4 Session B` — full spec
2. `platform/src/lib/retrieve/query_signal_state.ts` — find the confidence fallback line
3. `platform/src/lib/retrieve/query_remedial_mantras.ts` — read the current SQL/filter
4. `platform/python-sidecar/pipeline/loaders/chart_facts_loader.py` — understand the existing loader
5. `01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md` §planet placements (or equivalent section) — source data for planet rows
6. `platform/scripts/data/` — look for any existing planet seeding script

---

## §3 — Branch and worktree

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav
git worktree add ../MadhavMCPDataB fix/mcp-data-quality 2>/dev/null || \
  git worktree add ../MadhavMCPDataB -b fix/mcp-data-quality
cd ../MadhavMCPDataB
```

All work in `/Users/Dev/Vibe-Coding/Apps/MadhavMCPDataB`.

---

## §4 — Fix B.1: `query_chart_facts` — seed planet category

### Step 1: Verify the gap

Connect to the DB (via DB proxy on port 5433 or Cloud SQL direct) and run:

```sql
SELECT count(*), category
FROM chart_facts
WHERE category = 'planet'
GROUP BY category;
```

If returns 0 rows (or no rows at all for the `planet` category), proceed.

Also check what categories exist to understand the existing data shape:

```sql
SELECT DISTINCT category, count(*)
FROM chart_facts
GROUP BY category
ORDER BY count(*) DESC;
```

### Step 2: Understand the planet data source

Read `01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md` to find the canonical graha placement table. It should contain for each of the 9 grahas (Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, Rahu, Ketu):
- Sign (rashi)
- House number (bhava)
- Degree (longitude within sign)
- Dignity (exalted / debilitated / own sign / friend / neutral / enemy)
- Nakshatra placement
- Lord of which houses

### Step 3: Check the existing loader

Read `platform/python-sidecar/pipeline/loaders/chart_facts_loader.py` to understand:
- How existing categories were seeded
- What the `chart_facts` table schema expects (columns: `category`, `subcategory`, `key`, `value`, `source_citation`, `chart_id`, etc.)
- Whether there is already a `planet` section that was just not invoked

If the loader already has a `planet` section that wasn't called, find the invocation script and run it. If not, write a new TypeScript seed script at:

```
platform/scripts/data/seed_chart_facts_planet.ts
```

### Step 4: Write seed script (if needed)

The script must be idempotent (`INSERT ... ON CONFLICT DO NOTHING` or equivalent).
It must source data ONLY from `FORENSIC_ASTROLOGICAL_DATA_v8_0.md` — do not
invent values.

Expected rows: 9 planets × ~8 attributes = ~72 rows minimum.

Each row shape (check actual schema from existing rows):
```typescript
{
  category: 'planet',
  subcategory: 'sun',          // graha name lowercase
  key: 'sign',                 // attribute name
  value: 'Capricorn',          // value from FORENSIC
  source_citation: 'FORENSIC_ASTROLOGICAL_DATA_v8_0.md',
  chart_id: 'abhisek_mohanty_primary',   // or the native chart UUID
}
```

### Step 5: Run and verify

```bash
npx tsx platform/scripts/data/seed_chart_facts_planet.ts
```

Then verify:
```sql
SELECT count(*), subcategory
FROM chart_facts
WHERE category = 'planet'
GROUP BY subcategory
ORDER BY subcategory;
```

Must return 9 rows (one per graha) with count ≥ 5 each.

---

## §5 — Fix B.2: `query_signal_state` — state-derived confidence

File: `platform/src/lib/retrieve/query_signal_state.ts`

Find the line that reads (approximately):
```typescript
confidence: r.confidence ?? 0.6,
```

Replace with:
```typescript
confidence: r.confidence ?? (
  r.state === 'lit'      ? 0.85 :
  r.state === 'ripening' ? 0.65 :
  r.state === 'dormant'  ? 0.35 : 0.5
),
```

**Additional investigation (do not skip):** Read the full file and check whether
`r.state` is always available at this point in the code. If `r.state` may be
null/undefined, add a fallback:

```typescript
confidence: r.confidence ?? (
  r.state === 'lit'      ? 0.85 :
  r.state === 'ripening' ? 0.65 :
  r.state === 'dormant'  ? 0.35 : 0.5
),
```

Also open `platform/python-sidecar/pipeline/signal_activator.py` and check
whether there is an existing `strength_score`, `weight`, or similar field being
computed but not written to the `confidence` column. If one exists, add the
write:
```python
confidence=computed_strength_score,  # float 0.0–1.0
```
If no such field exists, leave the Python file alone and rely on the TypeScript
fallback. Document which path was taken in the commit message.

---

## §6 — Fix B.3: `query_remedial_mantras` — tighten filter

File: `platform/src/lib/retrieve/query_remedial_mantras.ts`

Read the file in full. The current issue is the filter is too broad — likely a
`ILIKE '%term%'` matching too many remedies regardless of planetary or domain
relevance to the query.

**Step 1:** Identify the SQL WHERE clause. Look for the condition that filters
remedies by the incoming query. It may look like:
```sql
WHERE r.text ILIKE '%' || $1 || '%'
```
or a vector similarity search with a low threshold.

**Step 2:** Understand the `remedial_mantras` table schema:
```sql
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'remedial_mantras';
```

If there are columns like `planet`, `domain`, `category` — use them as
mandatory equality filters, not just the fuzzy text match. The query should
first check for an exact planet/domain match, then fall back to text similarity.

**Step 3:** If the tool receives a `planet` or `graha` parameter, pass it as
an equality condition. If no structured filter is available, add a minimum
similarity threshold to the vector search (e.g. `similarity > 0.65` rather than
`> 0.40`).

The goal: precision over recall. Return only high-relevance remedies.
If the fix requires understanding the existing DB schema more deeply, do so
before editing.

---

## §7 — Test requirements

### B.1 tests — in `platform/` test suite:

```typescript
it('returns planet category rows for a graha query', async () => {
  // mock DB to return sample planet rows
  const result = await query_chart_facts({ category: 'planet', subcategory: 'sun' });
  expect(result.facts.length).toBeGreaterThan(0);
  expect(result.facts[0].category).toBe('planet');
});
```

### B.2 tests:

```typescript
it('returns state-derived confidence for lit signal', () => {
  const mockRow = { state: 'lit', confidence: null, signal_id: 'SIG.MSR.001', ... };
  // call the mapping function (extract it or test via the retrieval function)
  expect(mappedConfidence).toBeCloseTo(0.85);
});

it('returns state-derived confidence for dormant signal', () => {
  const mockRow = { state: 'dormant', confidence: null, ... };
  expect(mappedConfidence).toBeCloseTo(0.35);
});

it('returns actual confidence when present (not null)', () => {
  const mockRow = { state: 'lit', confidence: 0.92, ... };
  expect(mappedConfidence).toBeCloseTo(0.92);
});
```

### B.3 tests:

```typescript
it('returns only planet-matched remedies for a graha query', async () => {
  const result = await query_remedial_mantras({ planet: 'saturn', query: 'Saturn remedy' });
  result.mantras.forEach(m => {
    expect(m.planet ?? m.domain ?? '').toMatch(/saturn/i);
  });
});
```

---

## §8 — Build and test verification

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavMCPDataB/platform
npm run build
npm test
```

Both must pass. Check specifically:
- `query_signal_state` test suite
- `query_remedial_mantras` test suite
- Any tests that reference `chart_facts`

---

## §9 — Acceptance criteria

- [ ] AC-B.1: `SELECT count(*) FROM chart_facts WHERE category = 'planet'` returns > 0
- [ ] AC-B.2: `SELECT count(*) FROM chart_facts WHERE category = 'planet'` returns ≥ 45 (9 planets × 5 attributes minimum)
- [ ] AC-B.3: `query_signal_state` test with `state = 'lit'`, `confidence = null` returns confidence > 0.80 (not 0.6)
- [ ] AC-B.4: `query_signal_state` test with `state = 'dormant'`, `confidence = null` returns confidence < 0.45
- [ ] AC-B.5: `query_signal_state` test with non-null `confidence` returns that exact value
- [ ] AC-B.6: `query_remedial_mantras` integration test returns only domain-matched remedies
- [ ] AC-B.7: `npm run build` exits 0 in `platform/`
- [ ] AC-B.8: `npm test` passes all tests in `platform/`
- [ ] AC-B.9: Seed script is idempotent (run twice → same row count, no duplicates)

---

## §10 — Commit

```bash
git add platform/src/lib/retrieve/query_signal_state.ts
git add platform/src/lib/retrieve/query_remedial_mantras.ts
git add platform/scripts/data/seed_chart_facts_planet.ts  # if new
git add platform/python-sidecar/pipeline/signal_activator.py  # only if confidence write added
git commit -m "fix(mcp-data-quality): planet seed + signal confidence + remedial mantras filter

Session B of MCP Tool Audit Remediation v2.
B.1: seed_chart_facts_planet.ts — N rows inserted for 9 grahas × attributes
B.2: query_signal_state confidence fallback: 0.6 → state-derived (lit=0.85,
     ripening=0.65, dormant=0.35); signal_activator.py [patched|unchanged]
B.3: query_remedial_mantras filter tightened: [describe the specific change]

MCP-REM-V2 §4 Session B all AC pass."
```

Push:
```bash
git push origin fix/mcp-data-quality
```

---

## §11 — Session close signal

Paste back to Cowork chat:

```
SESSION-B COMPLETE
Branch: fix/mcp-data-quality
Commit: <SHA>
Build: PASS
Tests: PASS (N total)
AC-B.1 planet row count: <N>
AC-B.3 lit confidence: <value>
AC-B.4 dormant confidence: <value>
signal_activator.py: [patched with confidence write | left unchanged — no strength field]
remedial_mantras filter change: <brief description>
All AC-B.* checks: PASS
```

---

## §12 — Must NOT touch

- `platform-mcp/` (any file — Session A's territory)
- `platform/src/app/api/` routes
- Any migration file (no new tables; only seeding existing ones)
- `CLAUDE.md`, `CURRENT_STATE_v1_0.md`, `SESSION_LOG.md`
- Any CGM-related files (Session C scope)
- Any L5 timeline files (Session D scope)

---

*End of CLAUDECODE_BRIEF_MCP_REM_SESSION_B_v1_0.md*
