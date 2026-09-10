/**
 * f_vighna_8_darsh_8_stale_header.test.ts — F-VIGHNA-8 / F-DARSH-8
 * (L3_W1_ANALYSIS_BATCH_E.md).
 *
 * THE DEFECT: `L3_kala/index.ts`'s roster comment and `register_d5_fanout.ts`'s roster
 * comment both still called `query_obstruction_periods` (ka_vighnakara) and
 * `query_temporal_view` (ka_kala_darshana) "STUBBED-PENDING-DATA, 0 rows" in the present
 * tense, even though both capabilities' own served `description` field was already fixed
 * (per the sibling `d5_roster_smoke.test.ts` / `d5_l3_capabilities.test.ts` assertions,
 * which already pass) and both writers serve real, measured rows (536-741 for
 * ka_vighnakara, 750 for ka_kala_darshana, per canonical chart).
 *
 * Reads the raw file content (not an import) — these are doc-comment-only files, and this
 * test intentionally avoids pulling in DB-client-dependent modules, matching the sibling
 * `d5_roster_smoke.test.ts`'s own stated reason for not importing `register_d5_fanout.ts`
 * directly.
 *
 * Does NOT touch `query_temporal_view.ts`/`query_obstruction_periods.ts`'s own
 * "previously STUBBED-PENDING-DATA" comments — those are legitimate PAST-TENSE historical
 * notes about a defect already fixed, not a currently-false claim.
 */

import { describe, it, expect } from 'vitest'
import { readFileSync } from 'node:fs'
import { join } from 'node:path'

const INDEX_TS_PATH = join(__dirname, '..', 'L3_kala', 'index.ts')
const FANOUT_TS_PATH = join(__dirname, '..', 'register_d5_fanout.ts')

describe('F-VIGHNA-8 / F-DARSH-8 — no stale STUBBED-PENDING-DATA claim in roster headers', () => {
  it('L3_kala/index.ts no longer claims ka_vighnakara/ka_kala_darshana are stubbed', () => {
    const content = readFileSync(INDEX_TS_PATH, 'utf-8')
    expect(content).not.toContain('STUBBED-PENDING-DATA')
  })

  it('register_d5_fanout.ts no longer claims ka_vighnakara/ka_kala_darshana are stubbed', () => {
    const content = readFileSync(FANOUT_TS_PATH, 'utf-8')
    expect(content).not.toContain('STUBBED-PENDING-DATA')
  })
})
