#!/usr/bin/env npx tsx
/**
 * R9-S2 Historical embedding backfill.
 *
 * Embeds all conversation_messages that do not yet have a row in
 * conversation_message_embeddings, using Vertex AI
 * text-multilingual-embedding-002 (768 dims) via ADC.
 *
 * Prerequisites:
 *   1. Cloud SQL proxy running locally on 5432 (or direct DB accessible via DATABASE_URL).
 *      gcloud sql connect / cloud-sql-proxy madhav-astrology:asia-south1:amjis-postgres
 *   2. ADC auth: `gcloud auth application-default login`
 *   3. GCP_PROJECT and VERTEX_AI_LOCATION env vars set (or defaults below).
 *
 * Run from platform/ dir:
 *   DATABASE_URL="postgresql://amjis_app:<pw>@127.0.0.1:5432/amjis" \
 *   GCP_PROJECT=madhav-astrology \
 *   VERTEX_AI_LOCATION=asia-south1 \
 *   npx tsx scripts/backfill_conversation_embeddings.ts
 *
 * Safety rules:
 *   - INSERT ... ON CONFLICT DO NOTHING — idempotent; safe to re-run.
 *   - DO NOT run more than once concurrently against the same DB.
 *   - If interrupted, re-run — already-embedded rows are skipped automatically.
 *   - Rate-limit: BATCH_DELAY_MS between Vertex AI calls to avoid quota errors.
 */

import { Pool } from 'pg'
import { GoogleAuth } from 'google-auth-library'

const GCP_PROJECT      = process.env.GCP_PROJECT         ?? 'madhav-astrology'
const VERTEX_LOCATION  = process.env.VERTEX_AI_LOCATION  ?? 'asia-south1'
const VERTEX_MODEL     = 'text-multilingual-embedding-002'
const EMBED_DIM        = 768
const BATCH_SIZE       = 20   // messages per DB fetch batch
const BATCH_DELAY_MS   = 200  // ms between Vertex AI calls

const DATABASE_URL =
  process.env.DATABASE_URL ??
  'postgresql://amjis_app@127.0.0.1:5432/amjis'

const pool = new Pool({ connectionString: DATABASE_URL })
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

  const data = await res.json()
  const values = data.predictions?.[0]?.embeddings?.values as number[] | undefined
  if (!values || values.length !== EMBED_DIM) {
    throw new Error(`Unexpected dim: got ${values?.length ?? 0}, expected ${EMBED_DIM}`)
  }
  return values
}

async function sleep(ms: number) {
  return new Promise(r => setTimeout(r, ms))
}

async function main() {
  const client = await pool.connect()
  try {
    // Count total un-embedded messages
    const { rows: [{ total }] } = await client.query<{ total: string }>(`
      SELECT count(*) AS total
      FROM conversation_messages cm
      WHERE cm.content IS NOT NULL
        AND cm.content <> ''
        AND NOT EXISTS (
          SELECT 1 FROM conversation_message_embeddings e
          WHERE e.message_id = cm.id
        )
    `)
    const totalInt = parseInt(total, 10)
    console.log(`Messages to embed: ${totalInt}`)
    if (totalInt === 0) {
      console.log('Nothing to do — all messages already embedded.')
      return
    }

    let offset = 0
    let embedded = 0
    let errors = 0

    while (offset < totalInt) {
      const { rows } = await client.query<{ id: string; content: string }>(`
        SELECT cm.id, cm.content
        FROM conversation_messages cm
        WHERE cm.content IS NOT NULL
          AND cm.content <> ''
          AND NOT EXISTS (
            SELECT 1 FROM conversation_message_embeddings e
            WHERE e.message_id = cm.id
          )
        ORDER BY cm.created_at ASC
        LIMIT $1
      `, [BATCH_SIZE])

      if (rows.length === 0) break

      for (const row of rows) {
        try {
          const vec = await embedText(row.content)
          const vecStr = '[' + vec.join(',') + ']'
          await client.query(
            `INSERT INTO conversation_message_embeddings (message_id, embedding)
             VALUES ($1, $2::vector)
             ON CONFLICT (message_id) DO NOTHING`,
            [row.id, vecStr],
          )
          embedded++
          if (embedded % 10 === 0 || embedded === totalInt) {
            process.stdout.write(`\r  Embedded ${embedded}/${totalInt} (${errors} errors)`)
          }
          await sleep(BATCH_DELAY_MS)
        } catch (err) {
          errors++
          console.error(`\n  ERROR message ${row.id}: ${(err as Error).message}`)
        }
      }

      offset += rows.length
    }

    console.log(`\nDone. Embedded: ${embedded}, Errors: ${errors}`)
    if (errors > 0) {
      console.warn(`Re-run to retry failed rows — already-embedded rows are skipped automatically.`)
      process.exit(1)
    }
  } finally {
    client.release()
    await pool.end()
  }
}

main().catch(err => {
  console.error('Fatal:', err)
  process.exit(1)
})
