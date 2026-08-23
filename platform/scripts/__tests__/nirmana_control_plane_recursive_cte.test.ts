import { describe, it, expect } from 'vitest'
import fs from 'fs'
import path from 'path'

// ═══════════════════════════════════════════════════════════════════════════════════════
// REGRESSION COVERAGE FOR THE CONTROL-PLANE RECURSIVE CTEs — Nirmāṇa M0-T43 (SQ-04)
//
// WHAT DEFECT THIS PINS (M0-T33 / F-13). `build_asset_control_workbook.py`'s DAG-depth CTE
// used `UNION ALL` in its recursive term. What the query needs is one integer per asset —
// the longest root-to-asset path, a property of the (asset_id, depth) PAIR. What `UNION ALL`
// computed was every distinct root-to-asset PATH: the same pair re-derived once per route
// reaching it, then re-expanded to all children on the next iteration. On the live graph
// (127 active assets, 283 edges, 0 cycles, max depth 25) that was 3,022,346 rows materialised
// for 127 answers, worst node mi_darshana at 1,139,325 — and because each recursive step
// re-joins the working table against the whole registry with `= ANY(depends_on)`, the cost is
// O(paths x registry). Measured 75.553s -> 0.338s after the one-word fix. The same mistake
// had been copied style-for-style into the within-rung wave CTE below it.
//
// WHY NOTHING WARNED, and why a text assertion is the honest instrument here: the planner's
// ESTIMATE is BYTE-IDENTICAL for both forms (cost=531.46, rows=191) against 3,022,346 actual.
// Postgres does not estimate recursive-CTE cardinality. Nothing in the system could have
// flagged this except running it against real data — which this suite deliberately cannot do
// (no DATABASE_URL in CI; that absence is the root cause of two separate defects fixed in
// this campaign). So:
//
//   WHAT THIS TEST CAN DO: catch the revert. `UNION ALL` coming back — by an edit, a
//   copy-paste of the older form, or a third CTE added in the same style — turns this red.
//   That is precisely the shape the defect arrived in, twice.
//
//   WHAT IT CANNOT DO, stated rather than glossed: it cannot prove the two forms return the
//   same result set, and it does not try to. That identity was established by M0-T33 against
//   the live graph cell-by-cell over all 127 rows, and re-establishing it needs a database.
//   A test that re-derived the equality in TypeScript would be testing its own reimplementation,
//   not this SQL.
// ═══════════════════════════════════════════════════════════════════════════════════════

const REPO_ROOT = path.resolve(__dirname, '../../..')
const WORKBOOK = path.join(REPO_ROOT, '00_ARCHITECTURE/control/build_asset_control_workbook.py')

const SRC = fs.readFileSync(WORKBOOK, 'utf8')

/** Each `WITH RECURSIVE …` SQL body, taken from the triple-quoted execute() literals. */
function recursiveBlocks(src: string): { name: string; sql: string; at: number }[] {
  const out: { name: string; sql: string; at: number }[] = []
  const re = /WITH\s+RECURSIVE\s+([a-z_][a-z0-9_]*)\s+AS\s*\(/gi
  for (const m of src.matchAll(re)) {
    const at = m.index as number
    // The literal ends at the closing `"""` of the execute() call it sits in.
    const end = src.indexOf('"""', at)
    out.push({ name: m[1], sql: src.slice(at, end === -1 ? src.length : end), at })
  }
  return out
}

const BLOCKS = recursiveBlocks(SRC)

describe('build_asset_control_workbook.py recursive CTEs', () => {
  it('the file and its recursive CTEs are still there — the oracle is not vacuous', () => {
    // If the queries move or the file is renamed, every assertion below would pass over
    // nothing. Failing here is the signal to re-point this file, not to delete it.
    expect(fs.existsSync(WORKBOOK)).toBe(true)
    expect(BLOCKS.map((b) => b.name).sort()).toEqual(['dag', 'wave'])
  })

  for (const b of BLOCKS) {
    it(`\`${b.name}\` uses UNION, never UNION ALL, in its recursive term`, () => {
      // THE REGRESSION. `UNION` de-duplicates the recursive term against everything already
      // produced, so the working table can only ever hold DISTINCT (asset_id, depth) pairs —
      // at most nodes x depths — which is exactly the set `max()` aggregates over. One word.
      expect(b.sql).not.toMatch(/\bUNION\s+ALL\b/i)
      expect(b.sql).toMatch(/\bUNION\b/i)
    })

    it(`\`${b.name}\` still carries its depth cap`, () => {
      // Belt-and-braces against a cycle. With `UNION` the dedup bounds the working table on
      // its own, which is exactly why a later reader might judge the cap redundant and drop
      // it — and dropping it is only safe while the UNION is there. The two travel together.
      expect(b.sql).toMatch(/\b(depth|w)\s*<\s*\d+/)
    })
  }

  it('a server-side statement_timeout is SET, and set BEFORE the recursive queries run', () => {
    // The other half of M0-T33 / F-13, and the half that is about blast radius rather than
    // cost: killing the python client does NOT cancel the server-side query. Before this
    // line, every interrupted or retried run left its query burning production CPU with no
    // error and no log — on 2026-08-23 five abandoned copies of the DAG CTE wedged the shared
    // database for ~25 minutes and had to be cleared by hand with pg_cancel_backend.
    const m = SRC.match(/SET\s+statement_timeout\s*=\s*'(\d+)(m?s)'/i)
    expect(m, 'no SET statement_timeout found in the workbook generator').toBeTruthy()
    const at = SRC.indexOf(m![0])
    expect(at).toBeGreaterThan(-1)
    for (const b of BLOCKS) expect(at).toBeLessThan(b.at)
    // A timeout of 0 is "no timeout" in Postgres — the disabled state wearing the setting's
    // clothes, and the one value that would satisfy a naive "is it set?" check while
    // restoring the exact hazard.
    expect(Number(m![1])).toBeGreaterThan(0)
  })
})
