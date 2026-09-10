/**
 * orb_strength_no_invented_default.test.ts — NIRMĀṆA L3-W3 (§N.7 item 6, §N.6).
 *
 * THE DEFECT. `priority_score` was computed as
 *   `m.computed_salience * COALESCE(a.orb_strength, 0.5) * <dignity penalty>`
 * and `kala_activation.orb_strength` is NULL on **669,964 of 672,551 rows (99.6%)**, so the
 * default fired on almost every row of a RANKING score.
 *
 * And 0.5 is not a neutral default. Measured where `orb_strength` IS present: range
 * **0.700–1.000, mean 0.986** — the substituted value sits below the entire observed range. The
 * effect was a systematic penalty for the *absence of data*: the 0.4% of rows carrying an orb
 * outranked the rest largely because they carried one at all.
 *
 * THE FIX. The factor is dropped when unavailable rather than invented — this codebase's
 * established convention for an absent term (`kala_ritual_resonance`: "DROPPED from the product
 * and the product renormalised over the factors actually present — never zero-filled"). A
 * companion `orb_strength_available` boolean is emitted so a caller can distinguish a score
 * computed *with* the orb term from one computed without it. The two are not strictly comparable,
 * and the flag is what makes that visible rather than silent.
 *
 * These are source-shape assertions on the SQL, which is the right form here: the defect is a
 * literal in a query string, and a test that mocked the query's result could not see it.
 */
import { describe, it, expect } from 'vitest'
import { readFileSync } from 'node:fs'
import { join } from 'node:path'

const RAW = readFileSync(join(__dirname, 'call_service_wrappers.ts'), 'utf8')

/**
 * Strip SQL `--` comments before asserting. The fix's own comment quotes the removed expression
 * verbatim, and that documentation is worth keeping — the guard is about executable SQL, so it
 * must not match prose describing the defect. (Same trap as the M11 shape guard.)
 */
const SRC = RAW.split('\n')
  .map((line) => {
    const i = line.indexOf('--')
    return i >= 0 && !line.slice(0, i).includes("'") ? line.slice(0, i) : line
  })
  .join('\n')

describe('priority_score does not invent an orb_strength (§N.7 item 6)', () => {
  it('no longer substitutes the below-range 0.5 default', () => {
    expect(SRC).not.toMatch(/COALESCE\(\s*a\.orb_strength\s*,\s*0\.5\s*\)/)
  })

  it('drops the factor instead, rather than inventing a mid-range value', () => {
    expect(SRC).toMatch(/COALESCE\(\s*a\.orb_strength\s*,\s*1\.0\s*\)/)
  })

  it('emits orb_strength_available so the two score shapes are distinguishable (§N.6)', () => {
    expect(SRC).toMatch(/\(a\.orb_strength IS NOT NULL\) AS orb_strength_available/)
  })

  it('still exposes the raw orb_strength, so nothing has to trust the derived score alone', () => {
    expect(SRC).toMatch(/a\.orb_strength AS activation_strength/)
  })
})
