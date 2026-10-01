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

describe('migration 1218: bodha writer timeouts (SS ruling R-25)', () => {
  it('raises exactly bo_grounding and bo_laksana_rerank from 600 to 10800, nothing else', () => {
    const updates = code.match(/UPDATE\s+asset_registry\b[\s\S]*?;/g) ?? []
    expect(updates).toHaveLength(1)
    const update = updates[0]
    expect(update).toMatch(/SET\s+writer_timeout_seconds\s*=\s*10800\b/)
    expect(update).toMatch(/asset_id\s+IN\s*\(\s*'bo_grounding'\s*,\s*'bo_laksana_rerank'\s*\)/)
    // sets one column only
    expect(update.match(/\bSET\b/g)).toHaveLength(1)
    expect(update).not.toMatch(/SET[\s\S]*,\s*[a-z_]+\s*=/)
  })

  it('is idempotent and never overwrites a different value (guarded on = 600)', () => {
    const update = (code.match(/UPDATE\s+asset_registry\b[\s\S]*?;/) ?? [''])[0]
    expect(update).toMatch(/AND\s+writer_timeout_seconds\s*=\s*600\b/)
    // (`ON COMMIT DROP` on the temp snapshot is the only DROP in the file and is not a DROP statement)
    expect(code).not.toMatch(
      /\bDELETE\s+FROM\b|\bTRUNCATE\b|\bALTER\s+(TABLE|FUNCTION|TRIGGER)\b|\bDROP\s+(TABLE|COLUMN|FUNCTION|TRIGGER|INDEX|CONSTRAINT)\b|\bINSERT\s+INTO\s+asset_registry\b/i,
    )
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
    expect(code).toMatch(/RAISE EXCEPTION '1218: target row\(s\) not at 10800 after update: %'/)
    expect(code).toMatch(/RAISE EXCEPTION '1218: expected both or neither of bo_grounding\/bo_laksana_rerank/)
  })

  it('verifies after the UPDATE, never before it', () => {
    const updateAt = code.search(/UPDATE\s+asset_registry\b/)
    const stray = code.indexOf("unexpected writer_timeout_seconds change on")
    expect(updateAt).toBeGreaterThan(-1)
    expect(stray).toBeGreaterThan(updateAt)
  })

  it('does not touch a column that the registry-receipt invalidation trigger or a frozen manifest watches', () => {
    const update = (code.match(/UPDATE\s+asset_registry\b[\s\S]*?;/) ?? [''])[0]
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

  it('seed preserves the live value on conflict and carries no per-asset override for the two assets', () => {
    expect(seed).toContain('writer_timeout_seconds = asset_registry.writer_timeout_seconds')
    for (const assetId of ['bo_grounding', 'bo_laksana_rerank']) {
      const start = seed.indexOf(`asset_id: '${assetId}'`)
      expect(start).toBeGreaterThan(-1)
      const block = seed.slice(start, seed.indexOf('\n  },', start))
      expect(block).not.toContain('writer_timeout_seconds')
    }
  })
})
