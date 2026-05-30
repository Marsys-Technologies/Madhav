// ARCHIVED 2026-05-31 — duplicate-chart hazard. Use POST /api/clients/create
// (form-driven) for chart creation. See 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_CHART_DEDUPE_v1_0.md.

/**
 * Seed script: create Abhisek Mohanty's chart and upload existing pyramid documents.
 * Migrated from Supabase to GCP stack (Firebase Auth + Cloud SQL + GCS) on 2026-04-28.
 *
 * Prerequisites:
 *   1. Cloud SQL Auth Proxy running locally: DATABASE_URL set in .env.local
 *   2. GCS bucket created (chart-documents or equivalent)
 *   3. FIREBASE_ADMIN_CREDENTIALS set in .env.local
 *   4. SUPER_ADMIN_EMAIL set in .env.local
 *
 * Run:
 *   cd platform && npx tsx scripts/seed-abhisek.ts
 */

import * as fs from 'node:fs'
import * as path from 'node:path'
import * as dotenv from 'dotenv'
import { Pool } from 'pg'

dotenv.config({ path: path.join(process.cwd(), '.env.local') })

// ── DB connection (Cloud SQL via DATABASE_URL) ────────────────────────────────

const pool = new Pool({ connectionString: process.env.DATABASE_URL! })

async function dbQuery<T extends Record<string, unknown> = Record<string, unknown>>(
  sql: string,
  params?: unknown[]
): Promise<T[]> {
  const { rows } = await pool.query(sql, params)
  return rows as T[]
}

// ── Firebase Admin ────────────────────────────────────────────────────────────

async function initFirebaseAuth() {
  const { initializeApp, getApps, cert } = await import('firebase-admin/app')
  const { getAuth } = await import('firebase-admin/auth')

  let serviceAccount: object = {}
  try {
    serviceAccount = JSON.parse(process.env.FIREBASE_ADMIN_CREDENTIALS ?? '{}')
  } catch {
    throw new Error('FIREBASE_ADMIN_CREDENTIALS is not valid JSON')
  }

  const app =
    getApps().length > 0
      ? getApps()[0]
      : initializeApp({ credential: cert(serviceAccount) })

  return getAuth(app)
}

// ── GCS client ────────────────────────────────────────────────────────────────

async function initGCS() {
  const { Storage } = await import('@google-cloud/storage')
  return new Storage()
}

// ── Chart data ────────────────────────────────────────────────────────────────

const CHART = {
  name: 'Abhisek Mohanty',
  birth_date: '1984-02-05',
  birth_time: '10:43:00',
  birth_place: 'Bhubaneswar',
  birth_lat: 20.2961,
  birth_lng: 85.8245,
  ayanamsa: 'lahiri',
  house_system: 'sripathi',
}

// ── Document inventory ────────────────────────────────────────────────────────
// Map: { local file path (relative to project root) → { layer, name } }

const DOCUMENT_MAP: Array<{ localPath: string; layer: string; name: string }> = [
  // ── L1 — Facts Layer ────────────────────────────────────────────────────────
  {
    localPath: '../01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md',  // v8.0 current (CANONICAL)
    layer: 'L1',
    name: 'forensic_data',
  },
  {
    localPath: '../01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md',
    layer: 'L1',
    name: 'life_event_log',
  },

  // ── L2 — Analytical Layer ───────────────────────────────────────────────────
  {
    localPath: '../02_ANALYTICAL_LAYER/DEEP_ANALYSIS_Abhisek_Mohanty_v1.md',
    layer: 'L2',
    name: 'deep_analysis',
  },
  {
    localPath: '../02_ANALYTICAL_LAYER/MATRIX_HOUSES.md',
    layer: 'L2',
    name: 'matrix_houses',
  },
  {
    localPath: '../02_ANALYTICAL_LAYER/MATRIX_PLANETS.md',
    layer: 'L2',
    name: 'matrix_planets',
  },
  {
    localPath: '../02_ANALYTICAL_LAYER/MATRIX_SIGNS.md',
    layer: 'L2',
    name: 'matrix_signs',
  },
  {
    localPath: '../02_ANALYTICAL_LAYER/MATRIX_DASHA_PERIODS.md',
    layer: 'L2',
    name: 'matrix_dasha_periods',
  },
  {
    localPath: '../02_ANALYTICAL_LAYER/MATRIX_DIVISIONALS.md',
    layer: 'L2',
    name: 'matrix_divisionals',
  },

  // ── L2.5 — Holistic Synthesis Layer ─────────────────────────────────────────
  {
    localPath: '../025_HOLISTIC_SYNTHESIS/CGM_v9_0.md',  // v9.0 current (CANONICAL)
    layer: 'L2.5',
    name: 'cgm',
  },
  {
    localPath: '../025_HOLISTIC_SYNTHESIS/MSR_v3_0.md',  // v3.0 current (CANONICAL)
    layer: 'L2.5',
    name: 'msr',
  },
  {
    localPath: '../025_HOLISTIC_SYNTHESIS/CDLM_v1_1.md',
    layer: 'L2.5',
    name: 'cdlm',
  },
  {
    localPath: '../025_HOLISTIC_SYNTHESIS/RM_v2_0.md',
    layer: 'L2.5',
    name: 'rm',
  },
  {
    localPath: '../025_HOLISTIC_SYNTHESIS/UCN_v4_0.md',  // v4.0 current (CANONICAL)
    layer: 'L2.5',
    name: 'ucn',
  },

  // ── L3 — Domain Reports ──────────────────────────────────────────────────────
  {
    localPath: '../03_DOMAIN_REPORTS/FINANCIAL_REPORT_Abhisek_Mohanty.md',
    layer: 'L3',
    name: 'report_financial',
  },
]

// ── GCS bucket name ───────────────────────────────────────────────────────────

const GCS_BUCKET = process.env.GCS_CHART_DOCUMENTS_BUCKET ?? 'chart-documents'

// ── Main ──────────────────────────────────────────────────────────────────────

async function getOrCreateAstrologerUid(): Promise<string> {
  const superAdminEmail = process.env.SUPER_ADMIN_EMAIL
  if (!superAdminEmail) throw new Error('SUPER_ADMIN_EMAIL not set')

  const auth = await initFirebaseAuth()

  let uid: string
  try {
    const user = await auth.getUserByEmail(superAdminEmail)
    uid = user.uid
    console.log(`✓ Firebase Auth user found: ${uid}`)
  } catch {
    console.log(`  Creating Firebase Auth user for ${superAdminEmail}…`)
    const created = await auth.createUser({
      email: superAdminEmail,
      emailVerified: true,
      displayName: 'Abhisek Mohanty',
    })
    uid = created.uid
    console.log(`  ✓ Firebase Auth user created: ${uid}`)
  }

  // Upsert profile with role='super_admin'
  await dbQuery(
    `INSERT INTO profiles (id, role, name)
     VALUES ($1, 'super_admin', 'Abhisek Mohanty')
     ON CONFLICT (id) DO UPDATE SET role='super_admin', name='Abhisek Mohanty'`,
    [uid]
  )
  console.log(`✓ Astrologer profile ready: ${uid}`)
  return uid
}

async function createOrGetChart(clientId: string): Promise<string> {
  const existing = await dbQuery<{ id: string }>(
    `SELECT id FROM charts WHERE client_id=$1 AND name=$2 LIMIT 1`,
    [clientId, CHART.name]
  )

  if (existing.length > 0) {
    console.log(`✓ Chart already exists: ${existing[0].id}`)
    return existing[0].id
  }

  const created = await dbQuery<{ id: string }>(
    `INSERT INTO charts (client_id, name, birth_date, birth_time, birth_place, birth_lat, birth_lng, ayanamsa, house_system)
     VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9) RETURNING id`,
    [
      clientId,
      CHART.name,
      CHART.birth_date,
      CHART.birth_time,
      CHART.birth_place,
      CHART.birth_lat,
      CHART.birth_lng,
      CHART.ayanamsa,
      CHART.house_system,
    ]
  )
  const chartId = created[0].id
  console.log(`✓ Created chart: ${chartId}`)

  // Create pyramid_layers stubs
  const layers = [
    { layer: 'L1', sublayer: 'facts' },
    { layer: 'L2', sublayer: 'analysis_mode_a' },
    { layer: 'L2', sublayer: 'analysis_mode_b' },
    { layer: 'L2.5', sublayer: 'synthesis' },
    { layer: 'L3', sublayer: 'domain_reports' },
    { layer: 'L4', sublayer: 'query_interface' },
  ]
  for (const l of layers) {
    await dbQuery(
      `INSERT INTO pyramid_layers (chart_id, layer, sublayer, status)
       VALUES ($1,$2,$3,'not_started') ON CONFLICT DO NOTHING`,
      [chartId, l.layer, l.sublayer]
    )
  }
  console.log('✓ Pyramid layers created')
  return chartId
}

async function uploadDocument(
  chartId: string,
  localPath: string,
  layer: string,
  name: string
): Promise<void> {
  const resolved = path.resolve(process.cwd(), localPath)
  if (!fs.existsSync(resolved)) {
    console.warn(`  ⚠ File not found, skipping: ${resolved}`)
    return
  }

  // Check if document already exists in DB
  const existing = await dbQuery<{ id: string }>(
    `SELECT id FROM documents WHERE chart_id=$1 AND name=$2 LIMIT 1`,
    [chartId, name]
  )
  if (existing.length > 0) {
    console.log(`  ↩ Document already exists: ${name}`)
    return
  }

  const content = fs.readFileSync(resolved, 'utf-8')
  const storagePath = `charts/${chartId}/${layer}/${name}_v1.0.md`

  // Upload to GCS
  const gcs = await initGCS()
  try {
    await gcs.bucket(GCS_BUCKET).file(storagePath).save(content, {
      contentType: 'text/markdown',
      metadata: { cacheControl: 'no-cache' },
    })
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err)
    console.warn(`  ⚠ GCS upload failed for ${name}: ${message}`)
    return
  }

  // Insert document record
  try {
    await dbQuery(
      `INSERT INTO documents (chart_id, layer, name, storage_path, version)
       VALUES ($1,$2,$3,$4,'1.0')`,
      [chartId, layer, name, storagePath]
    )
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err)
    console.warn(`  ⚠ DB insert failed for ${name}: ${message}`)
    return
  }

  console.log(`  ✓ Uploaded: ${layer}/${name}`)
}

async function main() {
  console.log('── MARSYS-JIS Seed: Abhisek Mohanty ──')

  if (!process.env.DATABASE_URL) {
    console.error('DATABASE_URL not set — start Cloud SQL Auth Proxy and set in .env.local')
    process.exit(1)
  }

  const clientId = await getOrCreateAstrologerUid()
  const chartId = await createOrGetChart(clientId)

  console.log('\nUploading documents…')
  for (const doc of DOCUMENT_MAP) {
    await uploadDocument(chartId, doc.localPath, doc.layer, doc.name)
  }

  await pool.end()
  console.log('\n── Done ──')
  console.log(`Chart ID: ${chartId}`)
  console.log(`Visit: /clients/${chartId}/build`)
}

main().catch(err => {
  console.error(err)
  process.exit(1)
})
