/**
 * domain_reading_varga_parity.test.ts — F-164 (PARIŚEṢA-V4, GA-5 follow-up on #1419).
 * ========================================================================================
 * `DOMAIN_READING_VARGAS` (registry_bridge.ts) is a SECOND hand-copy of the same
 * classical-varga registry `register_d8_assess_domain.ts`'s `DOMAIN_DIRECT_VARGAS` /
 * `reading_checklist.ts`'s live-read maintain on the `platform` side — the two had already
 * drifted from each other (career) and both had drifted from the live source
 * (`brahma_vichara_constants.operative_vargas`, `platform/migrations/435_ga_vichara.sql`)
 * before this fix.
 *
 * WHY THIS TEST READS THE MIGRATION FILE DIRECTLY, NOT A LIVE DB ROW: platform-mcp is a
 * separate Node package from `platform` — it has no direct DB connection (see
 * `platformQuery()` in registry_bridge.ts, which proxies through `platform`'s HTTP API) and
 * cannot import `platform/src/...` TypeScript modules. `DOMAIN_READING_VARGAS` is therefore
 * kept as a maintained (not live-read) literal on this side — see its own header comment for
 * the full reasoning — and this test is its drift gate: the migration file IS the single
 * literal source of truth for the seed row, so reading it directly is the deterministic,
 * network-free way to catch drift (mirrors `signal_glossary.parity.test.ts`'s
 * read-the-source-file-directly convention, one directory over).
 */
import { describe, expect, it } from 'vitest'
import * as fs from 'node:fs'
import * as path from 'node:path'
import { DOMAIN_READING_VARGAS, type AssessedDomain } from '../registry_bridge.js'

// platform-mcp/src/tools/__tests__ → repo root
const REPO_ROOT = path.resolve(__dirname, '..', '..', '..', '..')
const MIGRATION_PATH = path.join(REPO_ROOT, 'platform', 'migrations', '435_ga_vichara.sql')

// signal_domain (DOMAIN_READING_VARGAS' own key vocabulary) -> brahma_vichara_constants'
// domain-key vocabulary. The one place the two disagree (relationship vs marriage) — mirrors
// reading_checklist.ts's SIGNAL_DOMAIN_TO_VICHARA_DOMAIN on the platform side exactly.
const SIGNAL_DOMAIN_TO_VICHARA_DOMAIN: Record<AssessedDomain, string> = {
  wealth: 'wealth', career: 'career', relationship: 'marriage', health: 'health',
}

interface OperativeVargaEntry { vargas: string[] }

/** Extracts and parses the `operative_vargas` JSONB literal straight out of the migration
 *  SQL text — no DB connection, no Python subprocess, just the file the seed row is defined
 *  in. Throws loudly (failing the test, not silently passing) if the shape ever changes
 *  enough that this regex can no longer find it — that is itself a signal this test needs a
 *  human to look at the new migration shape, not a green light to skip verifying. */
function readOperativeVargasFromMigration(): Record<string, OperativeVargaEntry> {
  const sql = fs.readFileSync(MIGRATION_PATH, 'utf8')
  const match = sql.match(/'operative_vargas',\s*\n\s*'([\s\S]*?)'::jsonb/)
  if (!match) {
    throw new Error(
      `Could not locate the 'operative_vargas' JSONB literal in ${MIGRATION_PATH} — ` +
      'the migration shape changed; update this test\'s extraction regex.',
    )
  }
  return JSON.parse(match[1]!) as Record<string, OperativeVargaEntry>
}

describe('F-164 — DOMAIN_READING_VARGAS agrees with the live source (brahma_vichara_constants.operative_vargas)', () => {
  const constants = readOperativeVargasFromMigration()

  it('the migration file exists and parses to the expected 5-domain shape', () => {
    expect(fs.existsSync(MIGRATION_PATH)).toBe(true)
    expect(Object.keys(constants).sort()).toEqual(['career', 'general', 'health', 'marriage', 'wealth'])
  })

  it.each(Object.keys(SIGNAL_DOMAIN_TO_VICHARA_DOMAIN) as AssessedDomain[])(
    'DOMAIN_READING_VARGAS[%s] == operative_vargas set minus D1 (D1 is the reference, never a voter)',
    (domain) => {
      const vicharaDomain = SIGNAL_DOMAIN_TO_VICHARA_DOMAIN[domain]
      const expected = constants[vicharaDomain]!.vargas.filter((v) => v !== 'D1')
      expect(DOMAIN_READING_VARGAS[domain]).toEqual(expected)
    },
  )

  it('wealth is the one design-ratified (non-provisional) domain — sanity check on the fixture itself', () => {
    const raw = fs.readFileSync(MIGRATION_PATH, 'utf8')
    expect(raw).toMatch(/"wealth":\s*\{"vargas":\s*\["D1","D2","D9","D11"\],\s*"provisional":\s*false/)
  })
})
