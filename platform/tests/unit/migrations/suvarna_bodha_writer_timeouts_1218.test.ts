import { readFileSync } from 'node:fs'
import { join } from 'node:path'
import { describe, expect, it } from 'vitest'

const sql = readFileSync(
  join(process.cwd(), 'migrations/1218_suvarna_bodha_writer_timeouts.sql'),
  'utf8',
)
// Executable SQL only: strip `--` comment lines so prose in the header cannot satisfy or trip a check.
const code = sql
  .split('\n')
  .filter((line) => !line.trimStart().startsWith('--'))
  .join('\n')

const definitions = readFileSync(
  join(process.cwd(), 'src/lib/nirmana-elevation/definitions.ts'),
  'utf8',
)
const seed = readFileSync(join(process.cwd(), 'scripts/seed/asset_registry_seed.ts'), 'utf8')

const WRITE_TARGET = /\b(?:UPDATE|INSERT\s+INTO|DELETE\s+FROM|MERGE\s+INTO|TRUNCATE(?:\s+TABLE)?)\s+(?:ONLY\s+)?(?:"?public"?\.)?"?asset_registry"?(?![\w])/gi
const UPDATE_STATEMENT = /UPDATE\s+(?:ONLY\s+)?(?:"?public"?\.)?"?asset_registry"?\b[\s\S]*?;/i

/** The one UPDATE, whitespace-collapsed with any `public.` qualifier removed, for exact comparison. */
function normalizedUpdate(): string {
  const match = code.match(UPDATE_STATEMENT)
  if (!match) throw new Error('no UPDATE asset_registry statement found')
  return match[0].replace(/\bpublic\./gi, '').replace(/\s+/g, ' ').trim()
}

describe('migration 1218: bodha writer timeouts (SS ruling R-25, value 1800)', () => {
  it('raises exactly bo_grounding and bo_laksana_rerank from 600 to 1800, nothing else', () => {
    // Exact statement: one column in SET, the two ids, the = 600 guard, and no OR / extra predicate
    // (kills `= 600 OR TRUE`, a widened id list, a dropped guard, a second SET column).
    expect(normalizedUpdate()).toBe(
      "UPDATE asset_registry SET writer_timeout_seconds = 1800 WHERE asset_id IN ('bo_grounding', 'bo_laksana_rerank') AND writer_timeout_seconds = 600;",
    )
  })

  it('tolerates a schema qualifier on the UPDATE target', () => {
    const qualified = 'UPDATE public.asset_registry\n   SET writer_timeout_seconds = 1800\n WHERE asset_id IN (\'a\');'
    expect(qualified.match(UPDATE_STATEMENT)).not.toBeNull()
    expect(('UPDATE "public"."asset_registry" SET x = 1;').match(UPDATE_STATEMENT)).not.toBeNull()
  })

  it('performs exactly one write to asset_registry (no second UPDATE/INSERT/DELETE/MERGE/TRUNCATE)', () => {
    expect(code.match(WRITE_TARGET)).toHaveLength(1)
    // the detector itself recognises each write form, qualified or not
    for (const write of [
      'UPDATE asset_registry SET a = 1',
      'UPDATE public.asset_registry SET a = 1',
      'INSERT INTO asset_registry (a) VALUES (1)',
      'INSERT INTO public.asset_registry (a) VALUES (1)',
      'DELETE FROM asset_registry',
      'MERGE INTO asset_registry',
      'TRUNCATE asset_registry',
    ]) {
      expect(write.match(WRITE_TARGET), write).toHaveLength(1)
    }
    expect('SELECT 1 FROM asset_registry r'.match(WRITE_TARGET)).toBeNull()
  })

  it('is idempotent and never overwrites a different value (guarded on = 600)', () => {
    expect(normalizedUpdate()).toMatch(/AND writer_timeout_seconds = 600;$/)
    expect(normalizedUpdate()).not.toMatch(/\bOR\b/i)
    // (`ON COMMIT DROP` on the temp snapshot is the only DROP in the file and is not a DROP statement)
    expect(code).not.toMatch(
      /\bDELETE\s+FROM\b|\bTRUNCATE\b|\bALTER\s+(TABLE|FUNCTION|TRIGGER)\b|\bDROP\s+(TABLE|COLUMN|FUNCTION|TRIGGER|INDEX|CONSTRAINT)\b/i,
    )
  })

  it('does not carry the superseded 10800 value in executable SQL', () => {
    expect(code).not.toMatch(/\b10800\b/)
    expect(code.match(/\b1800\b/g)?.length).toBeGreaterThanOrEqual(4)
  })

  it('leaves transaction ownership to migrate.ts', () => {
    expect(code).not.toMatch(/^\s*(BEGIN|COMMIT|ROLLBACK)\s*;/im)
  })

  it('snapshots writer_timeout_seconds inside the transaction and verifies against it', () => {
    expect(code).toMatch(/CREATE TEMP TABLE _m1218_before ON COMMIT DROP/)
    expect(code).toContain('FROM asset_registry;')
    expect(code).toMatch(/FULL JOIN asset_registry r ON r\.asset_id = b\.asset_id/)
    expect(code).toContain('r.writer_timeout_seconds IS DISTINCT FROM b.writer_timeout_seconds')
    expect(code).toMatch(/RAISE EXCEPTION '1218: % asset_registry row\(s\) changed writer_timeout_seconds, expected exactly %'/)
    expect(code).toMatch(/RAISE EXCEPTION '1218: unexpected writer_timeout_seconds change on: %'/)
    expect(code).toMatch(/RAISE EXCEPTION '1218: target row\(s\) not at 1800 after update: %'/)
    expect(code).toMatch(/RAISE EXCEPTION '1218: expected both or neither of bo_grounding\/bo_laksana_rerank/)
  })

  it('verifies after the UPDATE, never before it', () => {
    const updateAt = code.search(UPDATE_STATEMENT)
    const stray = code.indexOf('unexpected writer_timeout_seconds change on')
    expect(updateAt).toBeGreaterThan(-1)
    expect(stray).toBeGreaterThan(updateAt)
  })

  it('does not touch a column that the registry-receipt invalidation trigger or a frozen manifest watches', () => {
    const update = normalizedUpdate()
    // nirmana_registry_receipt_invalidation fires AFTER UPDATE OF these columns (live DB, read-only check)
    const triggerColumns = [
      'depends_on', 'natural_key_partition', 'health_probe', 'integrity_check_sql', 'target_floor',
      'asset_kind', 'asset_type', 'scope', 'has_writer', 'is_active', 'target_table',
    ]
    for (const column of triggerColumns) {
      expect(update).not.toMatch(new RegExp(`\\b${column}\\b`))
    }
  })
})

describe('migration 1218: writer_timeout_seconds is outside the frozen-manifest contract', () => {
  it('is not in registryContractFingerprintInput nor in the registry row type', () => {
    const fingerprint = definitions.slice(
      definitions.indexOf('export function registryContractFingerprintInput'),
      definitions.indexOf('export function canonicalRegistryContractDigest'),
    )
    expect(fingerprint).toContain('registry_contract')
    expect(fingerprint).not.toContain('writer_timeout_seconds')
    expect(definitions).not.toContain('writer_timeout_seconds')
  })

  it('seed preserves the live value on conflict; its per-asset value for the two assets is the 1296 value (10800)', () => {
    expect(seed).toContain('writer_timeout_seconds = asset_registry.writer_timeout_seconds')
    for (const assetId of ['bo_grounding', 'bo_laksana_rerank']) {
      const start = seed.indexOf(`asset_id: '${assetId}'`)
      expect(start).toBeGreaterThan(-1)
      const block = seed.slice(start, seed.indexOf('\n  },', start))
      // migration 1296 (raised 1800 -> 10800) added the seed value so a fresh database matches the live one
      expect(block).toMatch(/writer_timeout_seconds: 10800,/)
    }
  })
})
