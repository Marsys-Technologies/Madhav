import fs from 'node:fs'
import path from 'node:path'
import { execFileSync } from 'node:child_process'
import { Client } from 'pg'
import { describe, expect, it } from 'vitest'

import { ASSETS } from '../../../scripts/seed/asset_registry_seed'

const migrationPath = path.resolve(
  process.cwd(),
  'supabase/migrations/628_nirmana_l0_wave0_remaining_integrity_contracts.sql',
)
const migration = fs.existsSync(migrationPath) ? fs.readFileSync(migrationPath, 'utf8') : ''
// Migration 706 re-pins bg_vidhi_primitives' integrity_check_sql content hash after issue
// #2122's from_moon_view correction (migration 705, which fixes the LIVE production row --
// not needed here, since this fixture's vidhi_primitives is populated by dumping the CURRENT
// (already-corrected) writer, so only the re-pinned CHECK needs replaying to match it).
const migration706Path = path.resolve(
  process.cwd(),
  'migrations/706_bg_vidhi_primitives_from_moon_view_content_repin.sql',
)
const migration706 = fs.existsSync(migration706Path) ? fs.readFileSync(migration706Path, 'utf8') : ''
const migration530Path = path.resolve(
  process.cwd(),
  'supabase/migrations/530_bg_muhurta_lattice_panchangika_families.sql',
)
const migration530 = fs.existsSync(migration530Path) ? fs.readFileSync(migration530Path, 'utf8') : ''
const TEST_DATABASE_URL = process.env.NIRMANA_L0_WAVE0_REMAINING_TEST_DATABASE_URL
const MUHURTA_V1 = 'muhurta_lattice_agnivasa_yoga_kalam_ghati_v1'
const MUHURTA_V2 = 'muhurta_lattice_agnivasa_yoga_kalam_ghati_hora_vara_nakshatra_tithi_lagna_v2'
const MUHURTA_V2_FAMILIES = [
  'agnivasa', 'combination_yoga', 'ghati_muhurta', 'hora', 'kalam',
  'lagna', 'nakshatra', 'tithi', 'vara',
] as const
const MUHURTA_V2_OBSERVED_COUNTS = [
  ['agnivasa', 1826], ['combination_yoga', 1480], ['ghati_muhurta', 54780],
  ['hora', 43824], ['kalam', 33389], ['lagna', 23798], ['nakshatra', 1826],
  ['tithi', 1826], ['vara', 1826],
] as const
const MUHURTA_V1_OBSERVED_COUNTS = [
  ['agnivasa', 148], ['combination_yoga', 13], ['ghati_muhurta', 118], ['kalam', 32],
] as const
type VidhiPrimitive = {
  primitive_id: string
  version: number
  definition: string
  category: string
  live_tool: string
  tool_args: unknown
  fallback_face: string | null
  known_gap: string | null
  mandatory_tags: string[]
  cr27_prevents: string[]
}

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
    for (const factorFamily of MUHURTA_V2_FAMILIES) expect(migration).toContain(factorFamily)
    for (const factorFamily of MUHURTA_V2_FAMILIES) expect(migration530).toContain(`'${factorFamily}'`)
    expect(migration).toContain(MUHURTA_V2)
    expect(migration).toContain('registry_row.sort_order IN (21, 69)')
    expect(migration).toContain('registry_row.target_floor IN (48, 60)')
    expect(migration).toContain("secondary_body_key <> COALESCE(secondary_body, '')")
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
      CREATE EXTENSION IF NOT EXISTS pgcrypto;
      DROP TABLE IF EXISTS bg_sky_calendar, vidhi_primitives, bg_muhurta_lattice,
        asset_registry, asset_output_digest_specs CASCADE;
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
      CREATE TABLE bg_sky_calendar (
        event_type text NOT NULL, primary_body text NOT NULL, secondary_body text,
        secondary_body_key text GENERATED ALWAYS AS (COALESCE(secondary_body, '')) STORED,
        event_jd double precision NOT NULL,
        event_datetime_utc timestamp NOT NULL, ayanamsha_key text NOT NULL,
        sampling_method text NOT NULL, source_citation text NOT NULL
      );
      CREATE TABLE vidhi_primitives (
        primitive_id text PRIMARY KEY, version integer NOT NULL, definition text NOT NULL,
        category text NOT NULL, live_tool text NOT NULL, tool_args jsonb NOT NULL,
        fallback_face text, known_gap text, mandatory_tags text[] NOT NULL,
        cr27_prevents text[] NOT NULL
      );
      CREATE TABLE bg_muhurta_lattice (
        factor_family text NOT NULL, factor_key text NOT NULL, start_utc timestamp NOT NULL,
        end_utc timestamp NOT NULL, detail jsonb NOT NULL DEFAULT '{}'::jsonb,
        reference_lat numeric NOT NULL, reference_lon numeric NOT NULL,
        reference_tz_offset_minutes integer NOT NULL, reference_location_key text NOT NULL,
        ayanamsha_key text NOT NULL, sampling_method text NOT NULL,
        source_citation text NOT NULL, corpus_status text NOT NULL,
        build_id uuid, computed_at timestamptz NOT NULL DEFAULT NOW(),
        UNIQUE (factor_family, factor_key, start_utc)
      );
      INSERT INTO asset_registry
        (asset_id,layer,sort_order,scope,asset_kind,catalog_status,is_active,
         has_writer,target_table,count_sql,target_floor,depends_on)
      VALUES
        ('bg_sky_calendar','brahmagyan',21,'global','data','CURRENT',true,true,
         'bg_sky_calendar','SELECT COUNT(*) FROM bg_sky_calendar',31059,ARRAY[]::text[]),
        ('bg_vidhi_primitives','brahmagyan',68,'global','data','DRAFT',true,true,
         'vidhi_primitives','(SELECT COUNT(*) FROM vidhi_primitives)',48,ARRAY[]::text[]),
        ('bg_muhurta_lattice','brahmagyan',70,'global','data','CURRENT',true,true,
         'bg_muhurta_lattice','SELECT COUNT(*) FROM bg_muhurta_lattice',91477,ARRAY[]::text[]);

      INSERT INTO bg_sky_calendar
        (event_type, primary_body, secondary_body, event_jd,
         event_datetime_utc, ayanamsha_key, sampling_method, source_citation)
      SELECT event_type, 'Sun', NULL, sequence::double precision,
        TIMESTAMP '1900-01-01' + sequence * INTERVAL '1 minute', 'lahiri',
        'sky_calendar_ingress_station_eclipse_doubletransit_v1',
        'pyswisseph DE441 (Swiss Ephemeris) via pipeline.transit_search + sol_eclipse_when_glob/lun_eclipse_when; Lahiri ayanamsha'
      FROM (VALUES
        ('ingress', 28755), ('station', 1674), ('eclipse_solar', 308),
        ('eclipse_lunar', 312), ('double_transit', 10)
      ) AS corpus(event_type, row_count)
      CROSS JOIN LATERAL generate_series(1, row_count) AS sequence;

      INSERT INTO bg_muhurta_lattice
        (factor_family, factor_key, start_utc, end_utc, reference_lat, reference_lon,
         reference_tz_offset_minutes, reference_location_key, ayanamsha_key,
         sampling_method, source_citation, corpus_status)
      SELECT factor_family, factor_family || '_' || sequence,
        TIMESTAMP '2026-01-01' + sequence * INTERVAL '1 minute',
        TIMESTAMP '2026-01-01' + (sequence + 1) * INTERVAL '1 minute',
        20.27, 85.84, 330, 'bhubaneswar', 'lahiri', '${MUHURTA_V2}', 'citation', 'computed_cited'
      FROM (VALUES
        ('agnivasa', 1826), ('combination_yoga', 1480), ('ghati_muhurta', 54780),
        ('hora', 43824), ('kalam', 33389), ('lagna', 23798), ('nakshatra', 1826),
        ('tithi', 1826), ('vara', 1826)
      ) AS corpus(factor_family, row_count)
      CROSS JOIN LATERAL generate_series(1, row_count) AS sequence;

      INSERT INTO bg_muhurta_lattice
        (factor_family, factor_key, start_utc, end_utc, reference_lat, reference_lon,
         reference_tz_offset_minutes, reference_location_key, ayanamsha_key,
         sampling_method, source_citation, corpus_status)
      SELECT factor_family, 'legacy_' || factor_family || '_' || sequence,
        TIMESTAMP '2025-01-01' + sequence * INTERVAL '1 minute',
        TIMESTAMP '2025-01-01' + (sequence + 1) * INTERVAL '1 minute',
        20.27, 85.84, 330, 'bhubaneswar', 'lahiri', '${MUHURTA_V1}', 'citation', 'computed_cited'
      FROM (VALUES
        ('agnivasa', 148), ('combination_yoga', 13), ('ghati_muhurta', 118), ('kalam', 32)
      ) AS corpus(factor_family, row_count)
      CROSS JOIN LATERAL generate_series(1, row_count) AS sequence;

      -- The rolling corpora retain their historical lower edge while covering
      -- the required forward window; their timestamps are independent of this
      -- shape fixture's generated natural keys.
      UPDATE bg_sky_calendar SET event_datetime_utc = CURRENT_DATE + INTERVAL '10 years'
        WHERE event_type = 'double_transit' AND event_jd = 10;
      UPDATE bg_muhurta_lattice SET end_utc = CURRENT_DATE + INTERVAL '5 years'
        WHERE factor_family = 'lagna' AND factor_key = 'lagna_1';
    `)
    const dumped = JSON.parse(execFileSync(
      'python3',
      [path.resolve(process.cwd(), 'python-sidecar/pipeline/orchestrator/writers/bg_vidhi_primitives.py'), '--dump-json'],
      { encoding: 'utf8' },
    )) as { primitives: VidhiPrimitive[] }
    expect(dumped.primitives).toHaveLength(60)
    for (const primitive of dumped.primitives) {
      await client.query(
        `INSERT INTO vidhi_primitives
          (primitive_id,version,definition,category,live_tool,tool_args,fallback_face,
           known_gap,mandatory_tags,cr27_prevents)
         VALUES ($1,$2,$3,$4,$5,$6::jsonb,$7,$8,$9::text[],$10::text[])`,
        [
          primitive.primitive_id, primitive.version, primitive.definition, primitive.category,
          primitive.live_tool, JSON.stringify(primitive.tool_args), primitive.fallback_face,
          primitive.known_gap, primitive.mandatory_tags, primitive.cr27_prevents,
        ],
      )
    }
    for (const contract of CONTRACTS) {
      await client.query(
        `INSERT INTO asset_output_digest_specs (asset_id,spec_sha256,spec)
         VALUES ($1,$2,$3::jsonb)`,
        [contract.assetId, contract.outputSpec, JSON.stringify(contract.spec)],
      )
    }
    return client
  }

  async function executeStoredIntegritySql(client: Client, assetId: string): Promise<boolean> {
    const { rows } = await client.query<{ integrity_check_sql: string }>(
      'SELECT integrity_check_sql FROM asset_registry WHERE asset_id = $1', [assetId],
    )
    const result = await client.query(rows[0].integrity_check_sql)
    return Object.values(result.rows[0])[0] === true
  }

  it('transitions exact predecessors, preserves v2 corpus rows, replays, and executes every stored integrity SQL', async () => {
    const client = await connectPrepared()
    try {
      await client.query(migration)
      await expect(client.query(
        `SELECT is_generated FROM information_schema.columns
         WHERE table_schema = 'public' AND table_name = 'bg_sky_calendar'
           AND column_name = 'secondary_body_key'`,
      )).resolves.toMatchObject({ rows: [{ is_generated: 'ALWAYS' }] })
      await expect(client.query(
        `SELECT secondary_body, secondary_body_key FROM bg_sky_calendar
         WHERE event_type = 'ingress' ORDER BY event_jd LIMIT 1`,
      )).resolves.toMatchObject({ rows: [{ secondary_body: null, secondary_body_key: '' }] })
      await expect(client.query(
        `SELECT asset_id, sort_order, target_floor FROM asset_registry
         WHERE asset_id IN ('bg_sky_calendar', 'bg_vidhi_primitives') ORDER BY asset_id`,
      )).resolves.toMatchObject({ rows: [
        { asset_id: 'bg_sky_calendar', sort_order: 69, target_floor: '31059' },
        { asset_id: 'bg_vidhi_primitives', sort_order: 68, target_floor: '60' },
      ] })
      const v2Count = await client.query(
        'SELECT count(*)::integer AS count FROM bg_muhurta_lattice WHERE sampling_method = $1', [MUHURTA_V2],
      )
      expect(v2Count.rows).toEqual([{ count: 164575 }])
      await expect(client.query(
        `SELECT sampling_method, factor_family, count(*)::integer AS count
         FROM bg_muhurta_lattice
         GROUP BY sampling_method, factor_family
         ORDER BY sampling_method, factor_family`,
      )).resolves.toMatchObject({ rows: [
        ...MUHURTA_V2_OBSERVED_COUNTS.map(([factor_family, count]) => ({
          sampling_method: MUHURTA_V2, factor_family, count,
        })),
        ...MUHURTA_V1_OBSERVED_COUNTS.map(([factor_family, count]) => ({
          sampling_method: MUHURTA_V1, factor_family, count,
        })),
      ] })
      // Migration 628's own replay-idempotency + digest-contract-mutation-rejection invariants are
      // exercised here, BEFORE migration 706 (below) re-pins bg_vidhi_primitives.integrity_check_sql.
      // Migration 628's guard for that asset hardcodes the OLD (pre-#2122) from_moon_view content
      // hash; replaying 628 a second time after 706 has already moved that column away from the OLD
      // hash would spuriously trip 628's own guard -- an artifact of same-test-function ordering, not
      // a real production sequence (migrations never replay in production; each of 628/705/706 runs
      // exactly once, in that order). This block only exercises migration 628's own idempotency and
      // digest-guard behavior, both unrelated to the vidhi content correction, so it is unaffected by
      // running before it.
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

      // Migration 706 re-pins bg_vidhi_primitives.integrity_check_sql to the corrected from_moon_view
      // content hash (#2122/F-D21/F-D23) -- needed because this fixture's vidhi_primitives is
      // populated by dumping the CURRENT (already-corrected) writer, not migration 628's original
      // stale content. None of the three stored integrity_check_sql values (sky/vidhi/muhurta)
      // reference asset_output_digest_specs, so the mutation above does not affect this loop.
      await client.query(migration706)
      for (const assetId of CONTRACTS.map(contract => contract.assetId)) {
        await expect(executeStoredIntegritySql(client, assetId)).resolves.toBe(true)
      }
    } finally {
      await client.end()
    }
  })

  it('rejects all nearby registry states and makes an invalid legacy family read false', async () => {
    const client = await connectPrepared()
    try {
      for (const sortOrder of [20, 22]) {
        await client.query(
          `UPDATE asset_registry SET sort_order = $1 WHERE asset_id = 'bg_sky_calendar'`, [sortOrder],
        )
        await expect(client.query(migration)).rejects.toThrow(
          'migration 628 refuses unknown bg_sky_calendar registry contract',
        )
      }
      await client.query(`UPDATE asset_registry SET sort_order = 21 WHERE asset_id = 'bg_sky_calendar'`)
      for (const targetFloor of [47, 49, 59]) {
        await client.query(
          `UPDATE asset_registry SET target_floor = $1 WHERE asset_id = 'bg_vidhi_primitives'`, [targetFloor],
        )
        await expect(client.query(migration)).rejects.toThrow(
          'migration 628 refuses unknown bg_vidhi_primitives registry contract',
        )
      }
      await client.query(`UPDATE asset_registry SET target_floor = 48 WHERE asset_id = 'bg_vidhi_primitives'`)
      await client.query(migration)

      // Keep every accepted v2 row in place: this independently exercises the
      // v1 family predicate rather than merely tripping the v2 population floor.
      await client.query(`
        INSERT INTO bg_muhurta_lattice
          (factor_family, factor_key, start_utc, end_utc, reference_lat, reference_lon,
           reference_tz_offset_minutes, reference_location_key, ayanamsha_key,
           sampling_method, source_citation, corpus_status)
        VALUES ('hora', 'invalid_legacy_hora', TIMESTAMP '2026-01-01',
          TIMESTAMP '2026-01-01 00:01', 20.27, 85.84, 330, 'bhubaneswar', 'lahiri',
          $1, 'citation', 'computed_cited')
      `, [MUHURTA_V1])
      const retainedV2 = await client.query(
        'SELECT count(*)::integer AS count FROM bg_muhurta_lattice WHERE sampling_method = $1', [MUHURTA_V2],
      )
      expect(retainedV2.rows).toEqual([{ count: 164575 }])
      await expect(executeStoredIntegritySql(client, 'bg_muhurta_lattice')).resolves.toBe(false)
    } finally {
      await client.end()
    }
  })

  it('rejects a v2 family deficit even when the overall v2 population remains at its floor', async () => {
    const client = await connectPrepared()
    try {
      await client.query(migration)
      await client.query(
        `UPDATE bg_muhurta_lattice SET factor_family = 'vara'
         WHERE sampling_method = $1 AND factor_family = 'combination_yoga'
           AND factor_key = 'combination_yoga_1'`,
        [MUHURTA_V2],
      )
      const v2Population = await client.query(
        'SELECT count(*)::integer AS count FROM bg_muhurta_lattice WHERE sampling_method = $1', [MUHURTA_V2],
      )
      expect(v2Population.rows).toEqual([{ count: 164575 }])
      const deficientFamily = await client.query(
        `SELECT count(*)::integer AS count FROM bg_muhurta_lattice
         WHERE sampling_method = $1 AND factor_family = 'combination_yoga'`,
        [MUHURTA_V2],
      )
      expect(deficientFamily.rows).toEqual([{ count: 1479 }])
      await expect(executeStoredIntegritySql(client, 'bg_muhurta_lattice')).resolves.toBe(false)
    } finally {
      await client.end()
    }
  })
})
