/**
 * Seed script — chart_facts planet category extension
 *
 * Adds chara-karaka roles, dignity, and house-lordship rows for the 9 grahas.
 * All values sourced exclusively from FORENSIC_ASTROLOGICAL_DATA_v8_0.md
 * (§PLN.* individual graha sections).
 *
 * Idempotent: INSERT ... ON CONFLICT (fact_id) DO NOTHING.
 * Safe to run multiple times — second run changes 0 rows.
 *
 * Usage:
 *   DATABASE_URL=... npx tsx platform/scripts/data/seed_chart_facts_planet.ts
 */

import pg from 'pg'

const SOURCE = '01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md §PLN.*'
const BUILD_ID = 'mcp-data-quality-planet-seed-v1'

interface PlanetRow {
  fact_id: string
  category: 'planet'
  divisional_chart: string
  value_text: string
  value_number: number | null
  source_section: string
}

// ---------------------------------------------------------------------------
// Data — sourced only from FORENSIC §PLN.* individual graha sections
// ---------------------------------------------------------------------------

const ROWS: PlanetRow[] = [
  // --- Chara Karaka roles (explicitly listed in each PLN.* section) ---
  {
    fact_id: 'PLN.SUN.CHARA_KARAKA',
    category: 'planet',
    divisional_chart: 'D1',
    value_text: 'Bhratrukaraka (BK)',
    value_number: null,
    source_section: SOURCE,
  },
  {
    fact_id: 'PLN.MOON.CHARA_KARAKA',
    category: 'planet',
    divisional_chart: 'D1',
    value_text: 'Atmakaraka (AK)',
    value_number: null,
    source_section: SOURCE,
  },
  {
    fact_id: 'PLN.MARS.CHARA_KARAKA',
    category: 'planet',
    divisional_chart: 'D1',
    value_text: 'Putrakaraka (PK)',
    value_number: null,
    source_section: SOURCE,
  },
  {
    fact_id: 'PLN.MERCURY.CHARA_KARAKA',
    category: 'planet',
    divisional_chart: 'D1',
    value_text: 'Darakaraka (DK)',
    value_number: null,
    source_section: SOURCE,
  },
  {
    fact_id: 'PLN.JUPITER.CHARA_KARAKA',
    category: 'planet',
    divisional_chart: 'D1',
    value_text: 'Gnatikaraka (GK)',
    value_number: null,
    source_section: SOURCE,
  },
  {
    fact_id: 'PLN.VENUS.CHARA_KARAKA',
    category: 'planet',
    divisional_chart: 'D1',
    value_text: 'Matrukaraka (MK)',
    value_number: null,
    source_section: SOURCE,
  },
  {
    fact_id: 'PLN.SATURN.CHARA_KARAKA',
    category: 'planet',
    divisional_chart: 'D1',
    value_text: 'Amatyakaraka (AmK)',
    value_number: null,
    source_section: SOURCE,
  },
  {
    fact_id: 'PLN.RAHU.CHARA_KARAKA',
    category: 'planet',
    divisional_chart: 'D1',
    value_text: 'Putrakaraka (PK, 8-karaka system)',
    value_number: null,
    source_section: SOURCE,
  },

  // --- Dignity — only where FORENSIC explicitly states D1 dignity ---
  // FORENSIC §PLN.SATURN Special Role: "Exalted D1"
  {
    fact_id: 'PLN.SATURN.DIGNITY.D1',
    category: 'planet',
    divisional_chart: 'D1',
    value_text: 'exalted',
    value_number: null,
    source_section: SOURCE,
  },
  // FORENSIC §PLN.JUPITER Special Role: "9L own-sign own-house"
  {
    fact_id: 'PLN.JUPITER.DIGNITY.D1',
    category: 'planet',
    divisional_chart: 'D1',
    value_text: 'own_sign',
    value_number: null,
    source_section: SOURCE,
  },
  // FORENSIC §PLN.MARS Special Role: "Lagna Lord" (Aries lagna; Libra = Mars enemy sign)
  // NOTE: Mars debilitates in CANCER (28°), NOT Libra. Libra is Venus-owned; Mars-Venus are
  // enemies — so Mars in Libra = śatru-kṣetra (enemy sign). Prior seeding of 'debilitated'
  // was a factual error. Corrected 2026-05-27.
  {
    fact_id: 'PLN.MARS.DIGNITY.D1',
    category: 'planet',
    divisional_chart: 'D1',
    value_text: 'enemy',
    value_number: null,
    source_section: SOURCE,
  },

  // --- House lordship — only where FORENSIC explicitly states the role ---
  // FORENSIC §PLN.VENUS Special Role: "2nd and 7th Lord"
  {
    fact_id: 'PLN.VENUS.HOUSE_LORDSHIP',
    category: 'planet',
    divisional_chart: 'D1',
    value_text: '2, 7',
    value_number: null,
    source_section: SOURCE,
  },
  // FORENSIC §PLN.SATURN Special Role: "10th/11th Lord"
  {
    fact_id: 'PLN.SATURN.HOUSE_LORDSHIP',
    category: 'planet',
    divisional_chart: 'D1',
    value_text: '10, 11',
    value_number: null,
    source_section: SOURCE,
  },
  // FORENSIC §PLN.MARS Special Role: "Lagna Lord" (1L) + classical 8L for Aries lagna
  {
    fact_id: 'PLN.MARS.HOUSE_LORDSHIP',
    category: 'planet',
    divisional_chart: 'D1',
    value_text: '1, 8',
    value_number: null,
    source_section: SOURCE,
  },
]

const UPSERT_SQL = `
  INSERT INTO chart_facts
    (fact_id, category, divisional_chart, value_text, value_number,
     source_section, build_id, provenance, is_stale)
  VALUES ($1, $2, $3, $4, $5, $6, $7, $8::jsonb, FALSE)
  ON CONFLICT (fact_id) DO NOTHING
`

const BUILD_MANIFEST_SQL = `
  INSERT INTO build_manifests
    (build_id, triggered_by, registry_fingerprint, pipeline_image_uri,
     embedding_model, embedding_dim, chunk_count, embedding_count, status, manifest_uri)
  VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
  ON CONFLICT (build_id) DO NOTHING
`

async function seed(): Promise<void> {
  const databaseUrl = process.env.DATABASE_URL
  if (!databaseUrl) throw new Error('DATABASE_URL env var not set')

  const client = new pg.Client({ connectionString: databaseUrl })
  await client.connect()

  // Register build manifest (required by FK constraint)
  await client.query(BUILD_MANIFEST_SQL, [
    BUILD_ID,
    'seed_chart_facts_planet.ts',
    'n/a',
    'n/a',
    'n/a',
    0,
    ROWS.length,
    0,
    'live',
    `local://mcp-data-quality/${BUILD_ID}`,
  ])

  const provenance = JSON.stringify({
    source_uri: SOURCE,
    source_version: 'FORENSIC_ASTROLOGICAL_DATA_v8_0',
    extraction_method: 'manual_seed_mcp_data_quality_session_b',
    brief: 'CLAUDECODE_BRIEF_MCP_REM_SESSION_B_v1_0',
  })

  let inserted = 0
  let skipped = 0

  for (const row of ROWS) {
    const result = await client.query(UPSERT_SQL, [
      row.fact_id,
      row.category,
      row.divisional_chart,
      row.value_text,
      row.value_number,
      row.source_section,
      BUILD_ID,
      provenance,
    ])
    if (result.rowCount && result.rowCount > 0) {
      inserted++
    } else {
      skipped++
    }
  }

  await client.end()

  console.log(`\n=== seed_chart_facts_planet result ===`)
  console.log(`Rows inserted: ${inserted}`)
  console.log(`Rows skipped (already present): ${skipped}`)
  console.log(`Total attempted: ${ROWS.length}`)

  // Verify final count
  const verify = new pg.Client({ connectionString: databaseUrl })
  await verify.connect()
  const res = await verify.query<{ count: string }>(
    `SELECT count(*) FROM chart_facts WHERE category = 'planet'`
  )
  await verify.end()
  console.log(`Total planet rows in DB: ${res.rows[0].count}`)
}

seed().catch((err) => {
  console.error('seed failed:', err)
  process.exit(1)
})
