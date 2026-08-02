#!/usr/bin/env -S npx tsx
/**
 * apply_muhurta_chintamani_translations.ts
 *
 * Applies the Muhūrta-Cintāmaṇi translation pass to `classical_text_chunks`
 * (text_id='muhurta_chintamani'), per MUHURTA_CHINTAMANI_TRANSLATION_BRIEF_v1_0.md
 * v1.1 §4/§5. Reads a JSON data file of {chunk_id, action, ...} records produced
 * by the translation pass and writes them to the DB — idempotent, batched,
 * dry-run capable, checkpointed.
 *
 * Prerequisites (mirrors platform/scripts/backfill_conversation_embeddings.ts):
 *   1. DATABASE_URL env var pointing at a live/proxied Postgres with write access
 *      to classical_text_chunks (e.g. `source platform/.env.local`).
 *   2. ADC auth for Vertex AI embeddings: `gcloud auth application-default login`.
 *   3. GCP_PROJECT / VERTEX_AI_LOCATION env vars (defaults below match the repo's
 *      other embedding scripts).
 *
 * Usage (from platform/):
 *   npx tsx scripts/corpus/apply_muhurta_chintamani_translations.ts --dry-run
 *   npx tsx scripts/corpus/apply_muhurta_chintamani_translations.ts
 *   npx tsx scripts/corpus/apply_muhurta_chintamani_translations.ts --input path/to/other.json
 *
 * Idempotency / resume: before writing each chunk, the script checks whether
 * the row already carries this pass's `ocr_cleanup_pass_version` AND (for
 * translated rows) the expected `content_sha256` — if so, it's already applied
 * and is skipped. A stalled/interrupted run is safe to re-run from scratch; it
 * will only do work on chunks not yet in their target state.
 *
 * Provenance scheme: MUHURTA_CHINTAMANI_TRANSLATION_BRIEF_v1_0.md v1.1 §4,
 * verbatim. `translator`, `content_sa`, `source_citation`, `content_summary`,
 * `topics` are READ-ONLY and never written by this script.
 */

import { Pool, type PoolClient } from 'pg'
import { GoogleAuth } from 'google-auth-library'
import { createHash } from 'crypto'
import { readFileSync } from 'fs'
import { resolve } from 'path'

// ── Config (mirrors backfill_conversation_embeddings.ts) ───────────────────────

const GCP_PROJECT     = process.env.GCP_PROJECT ?? 'madhav-astrology'
const VERTEX_LOCATION = process.env.VERTEX_AI_LOCATION ?? 'asia-south1'
const VERTEX_MODEL    = 'text-multilingual-embedding-002'
const EMBED_DIM       = 768
const BATCH_SIZE      = 10
const EMBED_DELAY_MS  = 200

const DATABASE_URL =
  process.env.DATABASE_URL ?? 'postgresql://amjis_app@127.0.0.1:5432/amjis'

const TEXT_ID = 'muhurta_chintamani'
const OCR_CLEANUP_PASS_VERSION = 'mc_ocr_translation_v1_2026-08'
const TRANSLATION_PROVENANCE =
  'machine_translation_supervised_2026-08; commissioned per ' +
  'SHAD_DARSHANA_ADJUDICATIONS_NIGHT3_v1_0.md §NATIVE CONFIRMATIONS; source ' +
  'edition per translator field'

// ── CLI args ─────────────────────────────────────────────────────────────────

const args = process.argv.slice(2)
const DRY_RUN = args.includes('--dry-run')
const inputIdx = args.indexOf('--input')
const INPUT_PATH = resolve(
  inputIdx !== -1 && args[inputIdx + 1]
    ? args[inputIdx + 1]
    : resolve(__dirname, 'data/muhurta_chintamani_translations.json'),
)

// ── Data shape ───────────────────────────────────────────────────────────────

interface TranslationRecord {
  chunk_id: string
  action: 'translated' | 'deferred'
  priority_topic: 'agnivasa' | 'parihara' | 'combination_yoga' | 'kota_chakra' | null
  cleaned_devanagari_text: string | null
  content_en: string | null
  low_confidence_flag: boolean | null
  ocr_review_note: string | null
  ocr_confidence_score: number | null
  defer_reason: string | null
}

function sha256(text: string): string {
  return createHash('sha256').update(text, 'utf8').digest('hex')
}

// ── Vertex AI embedding (local reimplementation — server-only guarded
//    embedText.ts cannot be imported from a plain tsx script; same pattern as
//    backfill_conversation_embeddings.ts) ───────────────────────────────────

const auth = new GoogleAuth({ scopes: ['https://www.googleapis.com/auth/cloud-platform'] })

async function embedText(text: string): Promise<number[]> {
  const endpoint =
    `https://${VERTEX_LOCATION}-aiplatform.googleapis.com/v1/projects/${GCP_PROJECT}` +
    `/locations/${VERTEX_LOCATION}/publishers/google/models/${VERTEX_MODEL}:predict`

  const client = await auth.getClient()
  const { token } = await client.getAccessToken()

  const res = await fetch(endpoint, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token ?? ''}`,
    },
    body: JSON.stringify({
      instances: [{ task_type: 'RETRIEVAL_DOCUMENT', content: text }],
    }),
  })

  if (!res.ok) throw new Error(`Vertex AI ${res.status}: ${await res.text()}`)

  const data = (await res.json()) as { predictions?: Array<{ embeddings?: { values?: number[] } }> }
  const values = data.predictions?.[0]?.embeddings?.values
  if (!values || values.length !== EMBED_DIM) {
    throw new Error(`Unexpected embedding dim: got ${values?.length ?? 0}, expected ${EMBED_DIM}`)
  }
  return values
}

async function sleep(ms: number) {
  return new Promise(r => setTimeout(r, ms))
}

// ── Per-chunk apply ──────────────────────────────────────────────────────────

interface ApplyOutcome {
  chunk_id: string
  status: 'applied' | 'already_applied' | 'skipped_invalid' | 'error'
  detail?: string
}

async function alreadyApplied(client: PoolClient, chunkId: string, rec: TranslationRecord): Promise<boolean> {
  const { rows } = await client.query<{
    ocr_cleanup_pass_version: string | null
    translation_status: string | null
    content_sha256: string | null
  }>(
    `SELECT ocr_cleanup_pass_version, translation_status, content_sha256
       FROM classical_text_chunks WHERE text_id = $1 AND chunk_id = $2`,
    [TEXT_ID, chunkId],
  )
  if (rows.length === 0) return false
  const row = rows[0]
  if (row.ocr_cleanup_pass_version !== OCR_CLEANUP_PASS_VERSION) return false
  if (rec.action === 'deferred') {
    return row.translation_status === 'deferred'
  }
  const expectedSha = sha256(rec.content_en ?? '')
  return row.translation_status === 'machine_translated_supervised' && row.content_sha256 === expectedSha
}

async function applyOne(client: PoolClient, rec: TranslationRecord): Promise<ApplyOutcome> {
  if (rec.action === 'deferred') {
    if (!rec.ocr_review_note || !rec.ocr_review_note.startsWith('deferred: ')) {
      return { chunk_id: rec.chunk_id, status: 'skipped_invalid', detail: 'deferred row missing deferred: -prefixed ocr_review_note' }
    }
    const result = await client.query(
      `UPDATE classical_text_chunks
          SET translation_status = 'deferred',
              translation_provenance = $1,
              ocr_cleanup_pass_version = $2,
              ocr_review_note = $3,
              low_confidence_flag = false,
              ocr_confidence_score = NULL
        WHERE text_id = $4 AND chunk_id = $5`,
      [TRANSLATION_PROVENANCE, OCR_CLEANUP_PASS_VERSION, rec.ocr_review_note, TEXT_ID, rec.chunk_id],
    )
    if (result.rowCount !== 1) {
      return { chunk_id: rec.chunk_id, status: 'error', detail: `expected 1 row affected, got ${result.rowCount}` }
    }
    return { chunk_id: rec.chunk_id, status: 'applied' }
  }

  // action === 'translated'
  if (!rec.content_en || !rec.cleaned_devanagari_text || rec.ocr_confidence_score == null) {
    return { chunk_id: rec.chunk_id, status: 'skipped_invalid', detail: 'translated row missing content_en/cleaned_devanagari_text/ocr_confidence_score' }
  }

  const newSha = sha256(rec.content_en)
  const vec = await embedText(rec.content_en)
  const vecStr = '[' + vec.join(',') + ']'

  const result = await client.query(
    `UPDATE classical_text_chunks
        SET content_en = $1,
            cleaned_devanagari_text = $2,
            ocr_cleanup_pass_version = $3,
            translation_status = 'machine_translated_supervised',
            translation_provenance = $4,
            low_confidence_flag = $5,
            ocr_review_note = $6,
            ocr_confidence_score = $7,
            content_sha256 = $8,
            embedding = $9::vector
      WHERE text_id = $10 AND chunk_id = $11`,
    [
      rec.content_en,
      rec.cleaned_devanagari_text,
      OCR_CLEANUP_PASS_VERSION,
      TRANSLATION_PROVENANCE,
      rec.low_confidence_flag ?? false,
      rec.ocr_review_note ?? null,
      rec.ocr_confidence_score,
      newSha,
      vecStr,
      TEXT_ID,
      rec.chunk_id,
    ],
  )
  if (result.rowCount !== 1) {
    return { chunk_id: rec.chunk_id, status: 'error', detail: `expected 1 row affected, got ${result.rowCount}` }
  }
  return { chunk_id: rec.chunk_id, status: 'applied' }
}

// ── Main ─────────────────────────────────────────────────────────────────────

async function main(): Promise<void> {
  console.log('='.repeat(70))
  console.log('Muhūrta-Cintāmaṇi translation pass — apply script')
  console.log(`input: ${INPUT_PATH}`)
  console.log(`dry_run: ${DRY_RUN}`)
  console.log('='.repeat(70))

  const raw = readFileSync(INPUT_PATH, 'utf-8')
  const allRecords = JSON.parse(raw) as TranslationRecord[]
  const records = allRecords.filter(r => r.action === 'translated' || r.action === 'deferred')
  console.log(`\nLoaded ${allRecords.length} records; ${records.length} are translated/deferred (rest are non-priority, untouched).`)

  const pool = new Pool({ connectionString: DATABASE_URL })
  const client = await pool.connect()

  const outcomes: ApplyOutcome[] = []
  try {
    const { rows } = await client.query(
      `SELECT count(*) AS n FROM classical_text_chunks WHERE text_id = $1`,
      [TEXT_ID],
    )
    console.log(`Connected. classical_text_chunks WHERE text_id='${TEXT_ID}': ${rows[0].n} rows.`)

    for (let start = 0; start < records.length; start += BATCH_SIZE) {
      const batch = records.slice(start, start + BATCH_SIZE)
      console.log(`\n[batch ${start / BATCH_SIZE + 1}] chunks ${start + 1}-${Math.min(start + BATCH_SIZE, records.length)} of ${records.length}`)

      for (const rec of batch) {
        try {
          if (await alreadyApplied(client, rec.chunk_id, rec)) {
            outcomes.push({ chunk_id: rec.chunk_id, status: 'already_applied' })
            console.log(`  = ${rec.chunk_id} already applied, skipping`)
            continue
          }

          if (DRY_RUN) {
            outcomes.push({ chunk_id: rec.chunk_id, status: 'applied', detail: '[dry-run, not written]' })
            console.log(`  ~ ${rec.chunk_id} would ${rec.action} [dry-run]`)
            continue
          }

          const outcome = await applyOne(client, rec)
          outcomes.push(outcome)
          const marker = outcome.status === 'applied' ? '+' : outcome.status === 'error' ? '!' : '?'
          console.log(`  ${marker} ${rec.chunk_id} ${outcome.status}${outcome.detail ? ' — ' + outcome.detail : ''}`)

          if (rec.action === 'translated' && !DRY_RUN) {
            await sleep(EMBED_DELAY_MS)
          }
        } catch (err) {
          outcomes.push({ chunk_id: rec.chunk_id, status: 'error', detail: (err as Error).message })
          console.error(`  ! ${rec.chunk_id} ERROR: ${(err as Error).message}`)
        }
      }

      // Per-batch row-count verification (skipped in dry-run — nothing was written).
      if (!DRY_RUN) {
        const batchIds = batch.map(r => r.chunk_id)
        const { rows: verifyRows } = await client.query(
          `SELECT count(*) AS n FROM classical_text_chunks
            WHERE text_id = $1 AND chunk_id = ANY($2::text[])
              AND ocr_cleanup_pass_version = $3`,
          [TEXT_ID, batchIds, OCR_CLEANUP_PASS_VERSION],
        )
        const verified = parseInt(verifyRows[0].n, 10)
        const expectedApplied = batch.length
        console.log(`  [verify] ${verified}/${expectedApplied} rows in this batch now carry ${OCR_CLEANUP_PASS_VERSION}`)
      }
    }
  } finally {
    client.release()
    await pool.end()
  }

  const applied = outcomes.filter(o => o.status === 'applied').length
  const alreadyDone = outcomes.filter(o => o.status === 'already_applied').length
  const invalid = outcomes.filter(o => o.status === 'skipped_invalid').length
  const errors = outcomes.filter(o => o.status === 'error').length

  console.log('\n' + '='.repeat(70))
  console.log('Summary')
  console.log(`  Applied:          ${applied}`)
  console.log(`  Already applied:  ${alreadyDone}`)
  console.log(`  Skipped (invalid):${invalid}`)
  console.log(`  Errors:           ${errors}`)
  console.log('='.repeat(70))

  if (errors > 0) {
    console.error('\nSome chunks errored. Re-run this script to retry — already-applied chunks are skipped automatically.')
    process.exit(1)
  }
  if (invalid > 0) {
    console.error('\nSome records were structurally invalid and were not applied. Fix the input data file and re-run.')
    process.exit(2)
  }
}

main().catch(err => {
  console.error('Fatal error:', err)
  process.exit(1)
})
