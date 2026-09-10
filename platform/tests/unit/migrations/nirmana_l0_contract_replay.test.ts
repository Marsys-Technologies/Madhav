/**
 * Nirmana T0 L0 contract replay guards.
 *
 * `594_nirmana_t0_sky_calendar_contract.sql` requires the canonical physical
 * relation. Its historical rename is absent from the replayable migration tree,
 * so the dedicated compatibility migration must be scheduled immediately before
 * 594 without changing ordinary migration ordering.
 */
import { describe, expect, it, vi } from 'vitest'
import fs from 'fs'
import os from 'os'
import path from 'path'
import crypto from 'crypto'
import type { PoolClient } from 'pg'

import { ASSETS } from '../../../scripts/seed/asset_registry_seed'
import { collectMigrationFiles, runMigrations } from '../../../scripts/migrate'

function tempDir(): string {
  return fs.mkdtempSync(path.join(os.tmpdir(), 'nirmana-l0-contract-'))
}

describe('Nirmana T0 sky-calendar replay ordering', () => {
  it('uses an idempotent canonical-only no-op and fails closed when both relations exist', () => {
    const migration = fs.readFileSync(
      path.resolve(process.cwd(), 'supabase/migrations/597_nirmana_t0_sky_calendar_replay_compat.sql'),
      'utf8'
    )

    expect(migration).toContain("IF legacy_relation IS NOT NULL AND canonical_relation IS NOT NULL THEN")
    expect(migration).toContain("RAISE EXCEPTION\n      'migration 597 refuses ambiguous sky-calendar relations")
    expect(migration).toContain('ALTER TABLE public.bg_sky_events RENAME TO bg_sky_calendar')
    expect(migration).toContain("ELSIF canonical_relation IS NULL THEN")
  })

  it('runs the exact compatibility migration immediately before the exact 594 contract migration', () => {
    const dir = tempDir()
    try {
      fs.writeFileSync(path.join(dir, '594_nirmana_t0_sky_calendar_contract.sql'), 'SELECT 594;')
      fs.writeFileSync(path.join(dir, '597_nirmana_t0_sky_calendar_replay_compat.sql'), [
        '-- MIGRATION_BEFORE: 594_nirmana_t0_sky_calendar_contract.sql',
        'SELECT 597;',
      ].join('\n'))
      fs.writeFileSync(path.join(dir, '598_unrelated.sql'), 'SELECT 598;')

      expect(collectMigrationFiles([dir]).map(file => file.name)).toEqual([
        '597_nirmana_t0_sky_calendar_replay_compat.sql',
        '594_nirmana_t0_sky_calendar_contract.sql',
        '598_unrelated.sql',
      ])
    } finally {
      fs.rmSync(dir, { recursive: true, force: true })
    }
  })

  it('puts the real compatibility file immediately before the real 594 contract file', () => {
    const migrationNames = collectMigrationFiles([
      path.resolve(process.cwd(), 'migrations'),
      path.resolve(process.cwd(), 'supabase/migrations'),
    ]).map(file => file.name)
    const compatibilityIndex = migrationNames.indexOf('597_nirmana_t0_sky_calendar_replay_compat.sql')
    const contractIndex = migrationNames.indexOf('594_nirmana_t0_sky_calendar_contract.sql')

    expect(compatibilityIndex).toBeGreaterThanOrEqual(0)
    expect(contractIndex).toBe(compatibilityIndex + 1)
  })

  it('reaches 594 on a blank replay after the compatibility prerequisite', async () => {
    const dir = tempDir()
    try {
      fs.writeFileSync(path.join(dir, '594_nirmana_t0_sky_calendar_contract.sql'), 'SELECT 594;')
      fs.writeFileSync(path.join(dir, '597_nirmana_t0_sky_calendar_replay_compat.sql'), 'SELECT 597;')
      const client = {
        query: vi.fn(async () => ({ rows: [] })),
      } as unknown as PoolClient

      await expect(runMigrations(client, [dir], {
        disclosures: new Map(),
        renumberDisclosures: new Map(),
      })).resolves.toEqual([
        '597_nirmana_t0_sky_calendar_replay_compat.sql',
        '594_nirmana_t0_sky_calendar_contract.sql',
      ])
    } finally {
      fs.rmSync(dir, { recursive: true, force: true })
    }
  })

  it('still skips an already-applied compatibility migration during later runs', async () => {
    const dir = tempDir()
    try {
      const compatibilityName = '597_nirmana_t0_sky_calendar_replay_compat.sql'
      const compatibilitySql = 'SELECT 597;'
      fs.writeFileSync(path.join(dir, '594_nirmana_t0_sky_calendar_contract.sql'), 'SELECT 594;')
      fs.writeFileSync(path.join(dir, compatibilityName), compatibilitySql)
      const compatibilityHash = crypto.createHash('sha256').update(compatibilitySql).digest('hex')
      const applied = [{ filename: compatibilityName, sha256: compatibilityHash, sql_identity: null }]
      const client = {
        query: vi.fn(async (sql: string) => {
          if (sql.includes('SELECT filename, sha256, sql_identity FROM _migrations_applied')) {
            return { rows: applied }
          }
          return { rows: [] }
        }),
      } as unknown as PoolClient

      await expect(runMigrations(client, [dir], {
        disclosures: new Map(),
        renumberDisclosures: new Map(),
      })).resolves.toEqual(['594_nirmana_t0_sky_calendar_contract.sql'])
    } finally {
      fs.rmSync(dir, { recursive: true, force: true })
    }
  })

  it('leaves ordinary lexical migration order unchanged when no replay prerequisite is declared', () => {
    const dir = tempDir()
    try {
      fs.writeFileSync(path.join(dir, '002_b.sql'), 'SELECT 2;')
      fs.writeFileSync(path.join(dir, '001_a.sql'), 'SELECT 1;')

      expect(collectMigrationFiles([dir]).map(file => file.name)).toEqual([
        '001_a.sql',
        '002_b.sql',
      ])
    } finally {
      fs.rmSync(dir, { recursive: true, force: true })
    }
  })
})

describe('L0 registry metadata', () => {
  it('matches the tested 41-row Prashna corpus', () => {
    const prashna = ASSETS.find(asset => asset.asset_id === 'bg_prashna_rules')
    expect(prashna).toMatchObject({
      target_floor: 41,
      volume_explanation: '41 rows across 5 prashna sub-tables (5 lagna methods + 16 Tajik yogas + 12 significators + 5 fructification rules + 3 special techniques).',
    })
  })

  it('does not describe the 60-row Vidhi corpus as the obsolete 48-row deterministic count', () => {
    const vidhi = ASSETS.find(asset => asset.asset_id === 'bg_vidhi_primitives')
    expect(vidhi).toMatchObject({
      target_floor: 60,
      volume_explanation: '60 vidhi primitive atoms — deterministic count from the canonical TS/Python parity corpus.',
    })
  })
})
