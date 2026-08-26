import fs from 'node:fs'
import path from 'node:path'
import { Client } from 'pg'
import { describe, expect, it } from 'vitest'
import { ASSETS } from '../../../scripts/seed/asset_registry_seed'

const migration = fs.readFileSync(
  path.resolve(process.cwd(), 'supabase/migrations/624_nirmana_l0_ephemeris_probe_contract.sql'),
  'utf8',
)
const url = process.env.NIRMANA_L0_EPHEMERIS_TEST_DATABASE_URL
const description = 'Swiss Ephemeris (pyswisseph) with the pinned SHA-256-verified sepl_18/semo_18/seas_18 corpus for file-backed sidereal planetary positions. Foundation for all computational Jyotish in MARSYS-JIS. Lahiri ayanamsha canonical. MEAN_NODE convention: Rahu (ascending node).'
const healthProbe = {
  probe_type: 'ephemeris_engine',
  forensic_jd: 2445735.717361111,
  expected_sun_sign: 10,
  expected_mean_node_rahu_sign: 2,
  ayanamsha: 'lahiri',
  node_mode: 'mean',
  allowed_ephemeris_backends: ['swiss_ephemeris_file'],
  ephemeris_file_sha256: {
    'sepl_18.se1': 'ca1393ceab3a44fbc895887cf789c68819ae6a1cbc9b22225872dbe4ccd99a66',
    'semo_18.se1': '1ca07bd67c24374d77226180c20a4f9996cba013697894810518e7eb582ca4f7',
    'seas_18.se1': 'a2cd8fc33807c78ca9a700c91c2e042258b12fc4796519e00781440b5ad8b2e2',
  },
  note: 'JD = 1984-02-05 10:43 IST = 05:13 UTC. Sun in Makara; mean-node Rahu in Vrishabha under sidereal Lahiri.',
}

describe('migration 624 — ephemeris probe contract', () => {
  it('is fail-closed and seed-aligned', () => {
    expect(migration).toContain('migration 624 refuses unknown bg_ephemeris_engine registry contract')
    expect(migration).toContain('2445735.717361111')
    for (const digest of Object.values(healthProbe.ephemeris_file_sha256)) {
      expect(migration).toContain(digest)
    }
    expect(migration).not.toMatch(/^BEGIN;/m)
    expect(ASSETS.find(asset => asset.asset_id === 'bg_ephemeris_engine')).toMatchObject({
      english_description: description,
      health_probe: healthProbe,
    })
  })
})

if (url) {
  const parsed = new URL(url)
  if (!['localhost', '127.0.0.1'].includes(parsed.hostname)
    || parsed.pathname !== '/nirmana_l0_ephemeris_integrity_test') {
    throw new Error('unsafe ephemeris test database')
  }
}

describe.skipIf(!url)('migration 624 — real PostgreSQL', () => {
  const legacyDescription = 'Swiss Ephemeris (pyswisseph) with DE441 JPL file providing sidereal planetary positions from 9999 BCE to 9999 CE. Foundation for all computational Jyotish in MARSYS-JIS. Lahiri ayanamsha canonical. MEAN_NODE convention: Rahu (ascending node).'
  const legacyProbe = {
    probe_type: 'ephemeris_engine',
    forensic_jd: 2445701.948264,
    expected_sun_approximate_sign: 10,
    note: 'JD = 1984-02-05 10:43 IST → UTC. Sun in Makara (sign 10) sidereal Lahiri.',
  }

  async function prepare() {
    const client = new Client({ connectionString: url })
    await client.connect()
    await client.query(`
      DROP TABLE IF EXISTS asset_registry CASCADE;
      CREATE TABLE asset_registry(
        asset_id text primary key, layer text, sort_order int, scope text,
        asset_kind text, asset_type text, catalog_status text, is_active bool,
        has_writer bool, target_table text, count_sql text, target_floor bigint,
        depends_on text[], natural_key_partition text, data_disposition text,
        integrity_check_sql text, rebuild_on_probe_fail bool,
        english_description text, health_probe jsonb, provides_apis jsonb
      );
    `)
    await client.query(
      `INSERT INTO asset_registry VALUES(
        'bg_ephemeris_engine','brahmagyan',14,'global','service','service','CURRENT',
        true,false,NULL,NULL,NULL,'{}',NULL,NULL,NULL,false,$1,$2::jsonb,$3::jsonb
      )`,
      [legacyDescription, JSON.stringify(legacyProbe), JSON.stringify([
        { api: 'swisseph.calc_ut', description: 'Planetary longitude at Julian Day (UT) — wraps pyswisseph swe.calc_ut' },
        { api: 'swisseph.houses_ex', description: 'House cusps + Lagna at JD with geographic coordinates' },
      ])],
    )
    return client
  }

  it('accepts legacy and canonical replay but rejects unknown drift', async () => {
    const client = await prepare()
    try {
      await client.query(migration)
      await client.query(migration)
      const current = await client.query(
        "SELECT english_description,health_probe FROM asset_registry WHERE asset_id='bg_ephemeris_engine'",
      )
      expect(current.rows[0]).toEqual({ english_description: description, health_probe: healthProbe })
      await client.query("UPDATE asset_registry SET health_probe='{}'::jsonb")
      await expect(client.query(migration)).rejects.toThrow('migration 624 refuses unknown')
    } finally {
      await client.end()
    }
  })
})
