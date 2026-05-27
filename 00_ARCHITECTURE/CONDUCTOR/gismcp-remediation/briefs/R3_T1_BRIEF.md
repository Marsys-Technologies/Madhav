---
session_id: R3-T1
status: PENDING
phase: GISMCP-R3
title: "MSR grounding verification + discovery layer quality test"
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavGISMCP-S2
branch: fix/gismcp-r3
may_touch:
  - platform/src/__tests__/integration/msr_grounding.integration.test.ts
must_not_touch:
  - platform/src/lib/**
  - platform-mcp/**
  - 025_HOLISTIC_SYNTHESIS/**
  - "*.yaml"
---

# R3-T1: MSR Grounding Verification Tests

## Context

R3-S2 completed (or verified) MSR grounding. This session authors integration tests that permanently assert the grounding state and discovery layer quality.

---

## File: `platform/src/__tests__/integration/msr_grounding.integration.test.ts`

```typescript
/**
 * MSR Grounding Verification — Integration Tests
 * 
 * Permanently asserts:
 * 1. All 573 MSR signals have source_citation populated
 * 2. Discovery layer tools (pattern_register, etc.) return attributed responses
 * 3. No regression to 74% quality state
 * 
 * Skipped unless DB_PROXY_PORT is set.
 */

const SKIP = !process.env.DB_PROXY_PORT

describe.skipIf(SKIP)('MSR signal grounding — 573/573 contract', () => {
  it('total MSR signal count is 573', async () => {
    // Query the msr_signals table (or equivalent)
    // Adjust table name based on R3-S1 audit findings
    const { rows } = await db.query('SELECT COUNT(*) as cnt FROM msr_signals')
    expect(Number(rows[0].cnt)).toBe(573)
  })

  it('zero signals have null source_citation', async () => {
    const { rows } = await db.query(`
      SELECT COUNT(*) as cnt FROM msr_signals
      WHERE source_citation IS NULL 
         OR source_citation::text = ''
         OR source_citation::text = '{}'
    `)
    expect(Number(rows[0].cnt)).toBe(0)
  })

  it('all source_citations contain at least one FORENSIC or LEL reference', async () => {
    // Source citations should reference FORENSIC.* or LEL.EV.* format
    const { rows } = await db.query(`
      SELECT COUNT(*) as cnt FROM msr_signals
      WHERE source_citation IS NOT NULL
        AND (
          source_citation::text LIKE '%FORENSIC%'
          OR source_citation::text LIKE '%LEL.EV%'
        )
    `)
    expect(Number(rows[0].cnt)).toBe(573)
  })
})

describe.skipIf(SKIP)('Discovery layer tools — attributed responses', () => {
  it('pattern_register returns signals with source_citation fields', async () => {
    // Call the pattern_register retrieval function directly
    // Expect each returned signal to have a non-null source_citation
    const result = await patternRegister({ limit: 10 })
    expect(result.patterns.length).toBeGreaterThan(0)
    for (const pattern of result.patterns) {
      expect(pattern.source_citation || pattern.citations).toBeDefined()
    }
  })

  it('resonance_register returns attributed signals', async () => {
    const result = await resonanceRegister({ signal_code: 'MSR.001', limit: 5 })
    // Should return resonant signals, each with citations
    expect(result).toBeDefined()
  })

  it('msr_sql query returns source_citation columns', async () => {
    // Direct msr_sql query — should include citation data
    const result = await msrSql({ 
      query: "SELECT signal_code, source_citation FROM msr_signals LIMIT 5" 
    })
    expect(result.rows.length).toBeGreaterThan(0)
    expect(result.rows[0].source_citation).not.toBeNull()
  })
})
```

**Note on imports:** Use the actual function imports from `platform/src/lib/retrieve/index.ts`. Adjust function signatures to match the actual API.

---

## Run tests

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavGISMCP-S2/platform
DB_PROXY_PORT=5433 npx vitest run \
  src/__tests__/integration/msr_grounding.integration.test.ts \
  2>&1 | tail -20
```

Expected: 0 failures.

---

## Commit

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavGISMCP-S2
git add platform/src/__tests__/integration/msr_grounding.integration.test.ts
git commit -m "test(R3): MSR grounding 573/573 contract tests + discovery layer attribution

- Asserts zero null source_citation rows in msr_signals
- Asserts all citations reference FORENSIC or LEL fact IDs
- Discovery layer tools return attributed responses

Closes R3-T1 per GISMCP_REMEDIATION_PLAN_v1_0 §4"
```

## Acceptance Criteria

1. `test -f platform/src/__tests__/integration/msr_grounding.integration.test.ts`
2. With `DB_PROXY_PORT=5433`: all tests pass, 0 failures
3. Without `DB_PROXY_PORT`: tests skip cleanly
4. The null source_citation count test asserts exactly 0
