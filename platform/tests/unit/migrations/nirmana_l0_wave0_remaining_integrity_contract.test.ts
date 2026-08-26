import fs from 'node:fs'
import path from 'node:path'
import { Client } from 'pg'
import { describe, expect, it } from 'vitest'

import { ASSETS } from '../../../scripts/seed/asset_registry_seed'

const migrationPath = path.resolve(
  process.cwd(),
  'supabase/migrations/628_nirmana_l0_wave0_remaining_integrity_contracts.sql',
)
const migration = fs.existsSync(migrationPath) ? fs.readFileSync(migrationPath, 'utf8') : ''
const TEST_DATABASE_URL = process.env.NIRMANA_L0_WAVE0_REMAINING_TEST_DATABASE_URL

if (TEST_DATABASE_URL) {
  const parsed = new URL(TEST_DATABASE_URL)
  if (!['localhost', '127.0.0.1'].includes(parsed.hostname)
    || parsed.pathname !== '/nirmana_l0_wave0_remaining_test') {
    throw new Error(
      'NIRMANA_L0_WAVE0_REMAINING_TEST_DATABASE_URL must point to the exact local '
      + 'nirmana_l0_wave0_remaining_test database',
    )
  }
}

const CONTRACTS = [
  {
    assetId: 'bg_sky_calendar', sortOrder: 69, floor: 31_059,
    targetTable: 'bg_sky_calendar', countSql: 'SELECT COUNT(*) FROM bg_sky_calendar',
    partition: 'event_type,primary_body,secondary_body_key,event_jd',
    outputSpec: 'd806c806b7d22231c1266ec8f0f11d84325daaeff03418d418dc460a4074c75c',
    spec: { components: [{ key_columns: ['event_type', 'primary_body', 'secondary_body_key', 'event_jd'], name: 'bg_sky_calendar', relation: 'bg_sky_calendar', value_columns: ['event_type', 'primary_body', 'secondary_body', 'secondary_body_key', 'event_jd', 'event_datetime_utc', 'sign', 'nakshatra', 'longitude_deg', 'speed_dps', 'detail', 'ayanamsha_key', 'sampling_method', 'source_citation'] }], version: 'nirmana-output-digest-spec-v1' },
  },
  {
    assetId: 'bg_vidhi_primitives', sortOrder: 68, floor: 60,
    targetTable: 'vidhi_primitives', countSql: '(SELECT COUNT(*) FROM vidhi_primitives)',
    partition: 'primitive_id',
    outputSpec: '179ab2c22fad87f5f3c21475e3ddc5151eaf5fd88ea1c05cea0a6d73b845804f',
    spec: { components: [{ key_columns: ['primitive_id'], name: 'vidhi_primitives', relation: 'vidhi_primitives', value_columns: ['primitive_id', 'version', 'definition', 'category', 'live_tool', 'tool_args', 'fallback_face', 'known_gap', 'mandatory_tags', 'cr27_prevents'] }], version: 'nirmana-output-digest-spec-v1' },
  },
  {
    assetId: 'bg_muhurta_lattice', sortOrder: 70, floor: 91_477,
    targetTable: 'bg_muhurta_lattice', countSql: 'SELECT COUNT(*) FROM bg_muhurta_lattice',
    partition: 'factor_family,factor_key,start_utc',
    outputSpec: 'dd96913547048da000efbd94cfc106a9f90fe15b14b2def68aba9f45b4e4db98',
    spec: { components: [{ key_columns: ['factor_family', 'factor_key', 'start_utc'], name: 'bg_muhurta_lattice', relation: 'bg_muhurta_lattice', value_columns: ['factor_family', 'factor_key', 'start_utc', 'end_utc', 'detail', 'reference_lat', 'reference_lon', 'reference_tz_offset_minutes', 'reference_location_key', 'ayanamsha_key', 'sampling_method', 'source_citation', 'corpus_status'] }], version: 'nirmana-output-digest-spec-v1' },
  },
] as const

describe('migration 628 — remaining L0 wave-0 integrity contracts', () => {
  it('is runner-owned, fail-closed, and aligned with reviewed registry identities', () => {
    expect(migration).not.toBe('')
    expect(migration).toContain('migration 628 refuses unknown')
    expect(migration).not.toMatch(/^BEGIN;/m)
    expect(migration).not.toMatch(/^COMMIT;/m)

    for (const contract of CONTRACTS) {
      expect(ASSETS.find(asset => asset.asset_id === contract.assetId)).toMatchObject({
        sort_order: contract.sortOrder,
        target_table: contract.targetTable,
        count_sql: contract.countSql,
        target_floor: contract.floor,
        depends_on: [],
      })
      expect(migration).toContain(contract.partition)
      expect(migration).toContain(contract.outputSpec)
    }
  })

  it('pins the exact 60-row Vidhi semantic digest and all rolling-family invariants', () => {
    expect(migration).toContain('41463a2be208bc33c645cc943a242a2cd5b4906e8babd3dc68fe5ef566738cce')
    for (const eventType of [
      'ingress', 'station', 'eclipse_solar', 'eclipse_lunar', 'double_transit',
    ]) expect(migration).toContain(eventType)
    for (const factorFamily of [
      'agnivasa', 'combination_yoga', 'kalam', 'ghati_muhurta',
    ]) expect(migration).toContain(factorFamily)
  })

  it('binds each reviewed SHA to the exact JSONB specification', () => {
    expect(migration.match(/AND spec = (sky|vidhi|muhurta)_spec/g)).toHaveLength(6)
    for (const contract of CONTRACTS) {
      expect(migration).toContain(JSON.stringify(contract.spec))
    }
  })
})

describe.skipIf(!TEST_DATABASE_URL)('migration 628 — real PostgreSQL behavior', () => {
  async function connectPrepared(): Promise<Client> {
    const client = new Client({ connectionString: TEST_DATABASE_URL })
    await client.connect()
    await client.query(`
      DROP TABLE IF EXISTS asset_registry, asset_output_digest_specs CASCADE;
      CREATE TABLE asset_registry (
        asset_id text PRIMARY KEY, layer text, sort_order integer, scope text,
        asset_kind text, catalog_status text, is_active boolean, has_writer boolean,
        target_table text, count_sql text, target_floor bigint, depends_on text[],
        data_disposition text, natural_key_partition text, integrity_check_sql text
      );
      CREATE TABLE asset_output_digest_specs (
        asset_id text NOT NULL, spec_sha256 text NOT NULL, spec jsonb NOT NULL,
        retired_at timestamptz, PRIMARY KEY (asset_id, spec_sha256)
      );
      INSERT INTO asset_registry
        (asset_id,layer,sort_order,scope,asset_kind,catalog_status,is_active,
         has_writer,target_table,count_sql,target_floor,depends_on)
      VALUES
        ('bg_sky_calendar','brahmagyan',69,'global','data','CURRENT',true,true,
         'bg_sky_calendar','SELECT COUNT(*) FROM bg_sky_calendar',31059,ARRAY[]::text[]),
        ('bg_vidhi_primitives','brahmagyan',68,'global','data','DRAFT',true,true,
         'vidhi_primitives','(SELECT COUNT(*) FROM vidhi_primitives)',60,ARRAY[]::text[]),
        ('bg_muhurta_lattice','brahmagyan',70,'global','data','CURRENT',true,true,
         'bg_muhurta_lattice','SELECT COUNT(*) FROM bg_muhurta_lattice',91477,ARRAY[]::text[]);
    `)
    for (const contract of CONTRACTS) {
      await client.query(
        `INSERT INTO asset_output_digest_specs (asset_id,spec_sha256,spec)
         VALUES ($1,$2,$3::jsonb)`,
        [contract.assetId, contract.outputSpec, JSON.stringify(contract.spec)],
      )
    }
    return client
  }

  it('applies and replays exact contracts, then rejects altered JSON carrying the expected SHA', async () => {
    const client = await connectPrepared()
    try {
      await client.query(migration)
      await client.query(migration)
      await client.query(`
        UPDATE asset_output_digest_specs
        SET spec = spec || '{"unreviewed":true}'::jsonb
        WHERE asset_id = 'bg_sky_calendar' AND retired_at IS NULL
      `)
      await expect(client.query(migration)).rejects.toThrow(
        'migration 628 refuses unknown output digest contract',
      )
      const status = await client.query(
        `SELECT catalog_status FROM asset_registry WHERE asset_id='bg_vidhi_primitives'`,
      )
      expect(status.rows).toEqual([{ catalog_status: 'CURRENT' }])
    } finally {
      await client.end()
    }
  })
})
