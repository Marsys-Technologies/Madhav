#!/usr/bin/env -S npx tsx --conditions=react-server
/**
 * R9-S2 Historical embedding backfill.
 *
 * Embeds all conversation_messages that do not yet have a row in
 * conversation_message_embeddings, using Vertex AI
 * text-multilingual-embedding-002 (768 dims) via ADC.
 *
 * Prerequisites:
 *   1. Cloud SQL proxy running locally on 5433 (or direct DB accessible via DATABASE_URL).
 *      cloud-sql-proxy madhav-astrology:asia-south1:amjis-postgres --port=5433
 *   2. ADC auth: `gcloud auth application-default login`
 *   3. GCP_PROJECT and VERTEX_AI_LOCATION env vars set (or defaults below).
 *
 * Run from platform/ dir:
 *   DATABASE_URL="postgresql://amjis_app:<pw>@127.0.0.1:5433/amjis" \
 *   GCP_PROJECT=madhav-astrology \
 *   VERTEX_AI_LOCATION=asia-south1 \
 *   npx tsx --conditions=react-server scripts/backfill_conversation_embeddings.ts
 *
 * NOTE (PB-2/M-4, 2026-07-28): `--conditions=react-server` is now REQUIRED (not
 * optional) because this script imports the M-1 canonical-store DAL's
 * `readTurnParts`, which is guarded by `import 'server-only'` (as every
 * `@/lib/**` server module in this codebase is). The `server-only` package
 * throws unconditionally under the plain Node `default` export condition and
 * only resolves to a no-op under `react-server` — the same flag several other
 * scripts in this repo already require (see `pipeline:test`, `eval:planner`,
 * `codegen:projections` in package.json). Without the flag this script now
 * fails fast on the `readTurnParts` import rather than silently skipping
 * canonical rows.
 *
 * Safety rules:
 *   - INSERT ... ON CONFLICT DO NOTHING — idempotent; safe to re-run.
 *   - DO NOT run more than once concurrently against the same DB.
 *   - If interrupted, re-run — already-embedded rows are skipped automatically.
 *   - Rate-limit: BATCH_DELAY_MS between Vertex AI calls to avoid quota errors.
 *
 * ── PB-2 (SMṚTI) lane M-4 EXTENSION (2026-07-28) ─────────────────────────────
 * ADDED: this script now ALSO embeds canonical `message_parts` content (M-1,
 * migration 467) — the `text`/`reasoning` kind parts' body text for messages
 * that have `schema_version IS NOT NULL` (i.e. persisted via the M-1 DAL's
 * `writeTurn`, not the legacy `parts_json` blob path). Content is read via
 * M-1's own DAL (`readTurnParts`, `@/lib/pariprashna/store/reader`) rather than
 * re-deriving the shape by hand, so this script stays byte-faithful to
 * whatever the canonical reader considers a message's parts to be.
 *
 * CROSS-CAMPAIGN COORDINATION CHECK (required before this extension landed):
 * confirmed by inspection that this script — both before and after this
 * extension — reads/writes ONLY conversation/embedding tables:
 *   READS:  conversation_messages, message_parts (NEW), conversation_message_embeddings
 *   WRITES: conversation_message_embeddings (INSERT ... ON CONFLICT DO NOTHING)
 * It touches NO chart-asset table (no `chart_*`, `bodha_*`, `kala_*`, `phala_*`,
 * `mimamsa_*`, `ganita_*`, or similar L0–L5 asset table) — the concurrent
 * Śuddha-Vāca campaign's rebuild exclusivity over those tables is undisturbed.
 *
 * STILL BATCH/OFFLINE ONLY — this extension does not change that: it remains
 * a standalone `tsx` CLI script invoked manually against a DB connection, with
 * no HTTP handler, no import from `src/app/api/**`, and no caller in the live
 * `/api/pariprashna` request path. Embedding is a deterministic transform
 * (CLAUDE.md §N.4 "deterministic-first" — embeddings are fine, generative
 * curation is not), but it is still costly per-call I/O (a Vertex AI round
 * trip) and must never run inline in the serve path; this script is the
 * correct, and only, place for it to run.
 */

import { Pool } from 'pg'
import { GoogleAuth } from 'google-auth-library'
import { readTurnParts } from '../src/lib/pariprashna/store/reader'

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

/** Shared per-row embed-and-insert step; returns true on success. */
async function embedAndStore(
  client: Awaited<ReturnType<typeof pool.connect>>,
  messageId: string,
  content: string,
): Promise<boolean> {
  const vec = await embedText(content)
  const vecStr = '[' + vec.join(',') + ']'
  await client.query(
    `INSERT INTO conversation_message_embeddings (message_id, embedding)
     VALUES ($1, $2::vector)
     ON CONFLICT (message_id) DO NOTHING`,
    [messageId, vecStr],
  )
  return true
}

/**
 * Legacy pass — unchanged extraction logic (first `text`-type `parts_json`
 * element), narrowed to `schema_version IS NULL` rows only (PB-2/M-4:
 * explicit, defensive scoping now that a `schema_version IS NOT NULL`
 * canonical row exists and is handled by `runCanonicalBackfill` instead — no
 * row is ever eligible for both passes, since the M-1 writer never populates
 * `parts_json`).
 */
async function runLegacyBackfill(client: Awaited<ReturnType<typeof pool.connect>>): Promise<{ embedded: number; errors: number }> {
  const { rows: [{ total }] } = await client.query<{ total: string }>(`
    SELECT count(*) AS total
    FROM conversation_messages cm
    WHERE cm.schema_version IS NULL
      AND EXISTS (
        SELECT 1 FROM jsonb_array_elements(cm.parts_json) AS elem
        WHERE elem->>'type' = 'text' AND (elem->>'text') IS NOT NULL AND (elem->>'text') <> ''
      )
      AND NOT EXISTS (
        SELECT 1 FROM conversation_message_embeddings e
        WHERE e.message_id = cm.id
      )
  `)
  const totalInt = parseInt(total, 10)
  console.log(`[legacy parts_json] messages to embed: ${totalInt}`)
  if (totalInt === 0) {
    console.log('[legacy parts_json] nothing to do — all legacy messages already embedded.')
    return { embedded: 0, errors: 0 }
  }

  let offset = 0
  let embedded = 0
  let errors = 0

  while (offset < totalInt) {
    const { rows } = await client.query<{ id: string; content: string }>(`
      SELECT cm.id,
             (SELECT elem->>'text'
              FROM jsonb_array_elements(cm.parts_json) AS elem
              WHERE elem->>'type' = 'text' AND (elem->>'text') IS NOT NULL AND (elem->>'text') <> ''
              LIMIT 1) AS content
      FROM conversation_messages cm
      WHERE cm.schema_version IS NULL
        AND EXISTS (
          SELECT 1 FROM jsonb_array_elements(cm.parts_json) AS elem
          WHERE elem->>'type' = 'text' AND (elem->>'text') IS NOT NULL AND (elem->>'text') <> ''
        )
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
        await embedAndStore(client, row.id, row.content)
        embedded++
        if (embedded % 10 === 0 || embedded === totalInt) {
          process.stdout.write(`\r  [legacy] Embedded ${embedded}/${totalInt} (${errors} errors)`)
        }
        await sleep(BATCH_DELAY_MS)
      } catch (err) {
        errors++
        console.error(`\n  ERROR message ${row.id}: ${(err as Error).message}`)
      }
    }

    offset += rows.length
  }

  console.log(`\n[legacy parts_json] done. Embedded: ${embedded}, Errors: ${errors}`)
  return { embedded, errors }
}

/**
 * Canonical pass — PB-2 (SMṚTI) lane M-4 addition. Embeds `message_parts`
 * `text`/`reasoning` kind content for messages persisted via the M-1 DAL
 * (`schema_version IS NOT NULL`). Content is read via M-1's own `readTurnParts`
 * DAL call (not hand-rolled SQL), then joined seq-ordered into one string per
 * message — `conversation_message_embeddings` holds one vector per message,
 * matching the existing table shape (no schema change needed).
 *
 * Content-empty messages (e.g. a turn whose only parts are `tool_call` /
 * `tool_result` / `citation` — nothing text/reasoning to embed) are skipped,
 * not treated as errors, and tracked in `skippedIds` so this run's own
 * candidate query does not keep re-offering them every batch (they would
 * otherwise resurface every iteration since no embedding row is ever written
 * for them, unlike the legacy pass's error rows, which are only retried up to
 * `totalInt` iterations by design — see the original script's docstring).
 */
async function runCanonicalBackfill(client: Awaited<ReturnType<typeof pool.connect>>): Promise<{ embedded: number; skipped: number; errors: number }> {
  const { rows: [{ total }] } = await client.query<{ total: string }>(`
    SELECT count(*) AS total
    FROM conversation_messages cm
    WHERE cm.schema_version IS NOT NULL
      AND NOT EXISTS (
        SELECT 1 FROM conversation_message_embeddings e
        WHERE e.message_id = cm.id
      )
  `)
  const totalInt = parseInt(total, 10)
  console.log(`[canonical message_parts] messages to consider: ${totalInt}`)
  if (totalInt === 0) {
    console.log('[canonical message_parts] nothing to do — all canonical messages already embedded.')
    return { embedded: 0, skipped: 0, errors: 0 }
  }

  let embedded = 0
  let skipped = 0
  let errors = 0
  const skippedIds: string[] = []
  let processed = 0

  while (processed < totalInt) {
    const { rows } = await client.query<{ id: string }>(
      `SELECT cm.id
         FROM conversation_messages cm
        WHERE cm.schema_version IS NOT NULL
          AND NOT EXISTS (
            SELECT 1 FROM conversation_message_embeddings e
            WHERE e.message_id = cm.id
          )
          AND NOT (cm.id = ANY($1::uuid[]))
        ORDER BY cm.created_at ASC
        LIMIT $2`,
      [skippedIds, BATCH_SIZE],
    )

    if (rows.length === 0) break

    for (const row of rows) {
      try {
        // Read via M-1's DAL — seq-ordered, per-kind-validated parts.
        const parts = await readTurnParts(row.id)
        const content = parts
          .filter((p) => p.kind === 'text' || p.kind === 'reasoning')
          .map((p) => (p.body as { text?: string }).text ?? '')
          .filter((t) => t.trim().length > 0)
          .join('\n\n')

        if (content.trim().length === 0) {
          skipped++
          skippedIds.push(row.id)
          continue
        }

        await embedAndStore(client, row.id, content)
        embedded++
        if (embedded % 10 === 0) {
          process.stdout.write(`\r  [canonical] Embedded ${embedded} (skipped ${skipped}, ${errors} errors)`)
        }
        await sleep(BATCH_DELAY_MS)
      } catch (err) {
        errors++
        // Treat as processed-but-failed so it doesn't spin the loop forever;
        // re-running the script retries it (same idempotent guarantee as legacy).
        skippedIds.push(row.id)
        console.error(`\n  ERROR canonical message ${row.id}: ${(err as Error).message}`)
      }
    }

    processed += rows.length
  }

  console.log(`\n[canonical message_parts] done. Embedded: ${embedded}, Skipped (no text/reasoning content): ${skipped}, Errors: ${errors}`)
  return { embedded, skipped, errors }
}

async function main() {
  const client = await pool.connect()
  try {
    const legacy = await runLegacyBackfill(client)
    const canonical = await runCanonicalBackfill(client)

    const totalEmbedded = legacy.embedded + canonical.embedded
    const totalErrors = legacy.errors + canonical.errors
    console.log(
      `\nAll passes done. Embedded: ${totalEmbedded} (legacy ${legacy.embedded} + canonical ${canonical.embedded}), ` +
        `Skipped: ${canonical.skipped}, Errors: ${totalErrors}`,
    )
    if (totalErrors > 0) {
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
