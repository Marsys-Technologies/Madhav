/**
 * classical_text_embedder.ts
 * Shared Vertex AI 768-dim embedder for classical text ingestion.
 * MCP Transformation v3.2 — MARSYS-JIS project.
 *
 * Uses Vertex AI text-multilingual-embedding-002 (768 dims) via ADC.
 * Shared with v3.2-S2 (Jaimini), v3.2-S3 (KP Reader / Tajaka).
 *
 * Idempotent: existing chunk_id rows in rag_chunks are skipped (INSERT ... ON CONFLICT DO NOTHING).
 *
 * Prerequisites:
 *   - Cloud SQL proxy on localhost:5433
 *   - ADC auth: gcloud auth application-default login
 *   - GCP_PROJECT env var (default: madhav-astrology)
 *   - VERTEX_AI_LOCATION env var (default: asia-south1)
 */

import { Pool, PoolClient } from 'pg';
import { GoogleAuth } from 'google-auth-library';
import type { ClassicalChunk } from './classical_text_chunker.js';

export const VERTEX_MODEL = 'text-multilingual-embedding-002';
export const EMBED_DIM = 768;
export const DEFAULT_BATCH_SIZE = 20;
export const DEFAULT_BATCH_DELAY_MS = 300;

const GCP_PROJECT = process.env.GCP_PROJECT ?? 'madhav-astrology';
const VERTEX_LOCATION = process.env.VERTEX_AI_LOCATION ?? 'asia-south1';

let _auth: GoogleAuth | null = null;
function getAuth(): GoogleAuth {
  if (!_auth) {
    _auth = new GoogleAuth({ scopes: ['https://www.googleapis.com/auth/cloud-platform'] });
  }
  return _auth;
}

/**
 * Embed a single text using Vertex AI.
 * Throws on HTTP error or unexpected embedding dimension.
 */
export async function embedText(text: string): Promise<number[]> {
  const endpoint =
    `https://${VERTEX_LOCATION}-aiplatform.googleapis.com/v1/projects/${GCP_PROJECT}` +
    `/locations/${VERTEX_LOCATION}/publishers/google/models/${VERTEX_MODEL}:predict`;

  const auth = getAuth();
  const client = await auth.getClient();
  const { token } = await client.getAccessToken();

  const res = await fetch(endpoint, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token ?? ''}`,
    },
    body: JSON.stringify({
      instances: [{ task_type: 'RETRIEVAL_DOCUMENT', content: text }],
    }),
  });

  if (!res.ok) {
    throw new Error(`Vertex AI ${res.status}: ${await res.text()}`);
  }

  const data = (await res.json()) as {
    predictions?: Array<{ embeddings?: { values?: number[] } }>;
  };
  const values = data.predictions?.[0]?.embeddings?.values;
  if (!values || values.length !== EMBED_DIM) {
    throw new Error(`Unexpected embedding dim: got ${values?.length ?? 0}, expected ${EMBED_DIM}`);
  }
  return values;
}

export function sleep(ms: number): Promise<void> {
  return new Promise(r => setTimeout(r, ms));
}

/**
 * Result of inserting a chunk into rag_chunks + rag_embeddings.
 */
export interface InsertResult {
  chunk_id: string;
  inserted: boolean; // false = already existed (ON CONFLICT DO NOTHING)
  embedded: boolean; // false = skipped or failed
  error?: string;
}

/**
 * Insert a single ClassicalChunk into rag_chunks.
 * Uses ON CONFLICT DO NOTHING so it is idempotent.
 */
export async function insertRagChunk(
  db: PoolClient,
  chunk: ClassicalChunk,
  buildId: string,
): Promise<{ inserted: boolean }> {
  const result = await db.query(
    `INSERT INTO rag_chunks
       (chunk_id, doc_type, layer, source_file, source_version, content, token_count, canonical_id, metadata)
     VALUES ($1, 'classical_text', 'L8', $2, $3, $4, $5, $6, $7)
     ON CONFLICT (chunk_id) DO NOTHING`,
    [
      chunk.chunk_id,
      `classical_texts/${chunk.verse.work}/${chunk.verse.chapter}`,
      chunk.verse.source_edition,
      chunk.content,
      chunk.token_count,
      chunk.source_canonical_id, // stored in canonical_id column (rag_chunks actual schema)
      JSON.stringify({
        work: chunk.verse.work,
        chapter: chunk.verse.chapter,
        verse_start: chunk.verse.verse_start,
        verse_end: chunk.verse.verse_end,
        verse_id: chunk.verse.verse_id,
        verse_ref: chunk.verse.verse_ref,
        build_id: buildId,
        source_edition: chunk.verse.source_edition,
      }),
    ],
  );
  return { inserted: (result.rowCount ?? 0) > 0 };
}

/**
 * Insert a 768-dim embedding into rag_embeddings.
 * Uses ON CONFLICT DO NOTHING for idempotency.
 */
export async function insertRagEmbedding(
  db: PoolClient,
  chunkId: string,
  embedding: number[],
): Promise<void> {
  await db.query(
    `INSERT INTO rag_embeddings (chunk_id, model, embedding)
     VALUES ($1, $2, $3::vector)
     ON CONFLICT (chunk_id, model) DO NOTHING`,
    [chunkId, VERTEX_MODEL, `[${embedding.join(',')}]`],
  );
}

/**
 * Embed and persist a batch of ClassicalChunk objects.
 *
 * @param pool - pg Pool (connected to production DB)
 * @param chunks - chunks to embed and insert
 * @param buildId - build identifier string
 * @param opts - optional overrides for batch size and delay
 * @returns array of InsertResult, one per chunk
 */
export async function embedAndPersistChunks(
  pool: Pool,
  chunks: ClassicalChunk[],
  buildId: string,
  opts: { batchSize?: number; batchDelayMs?: number; verbose?: boolean } = {},
): Promise<InsertResult[]> {
  const batchSize = opts.batchSize ?? DEFAULT_BATCH_SIZE;
  const batchDelayMs = opts.batchDelayMs ?? DEFAULT_BATCH_DELAY_MS;
  const verbose = opts.verbose ?? true;

  const results: InsertResult[] = [];
  let inserted = 0;
  let skipped = 0;
  let embedded = 0;
  let errors = 0;

  for (let i = 0; i < chunks.length; i += batchSize) {
    const batch = chunks.slice(i, i + batchSize);
    const db = await pool.connect();

    try {
      for (const chunk of batch) {
        const result: InsertResult = { chunk_id: chunk.chunk_id, inserted: false, embedded: false };

        // Insert chunk text
        const { inserted: wasInserted } = await insertRagChunk(db, chunk, buildId);
        result.inserted = wasInserted;
        if (wasInserted) inserted++; else skipped++;

        // Embed and store (only if chunk was newly inserted OR no embedding exists yet)
        const existingEmbed = await db.query(
          'SELECT 1 FROM rag_embeddings WHERE chunk_id = $1 AND model = $2',
          [chunk.chunk_id, VERTEX_MODEL],
        );
        if (existingEmbed.rows.length === 0) {
          try {
            const embedding = await embedText(chunk.content);
            await insertRagEmbedding(db, chunk.chunk_id, embedding);
            result.embedded = true;
            embedded++;
          } catch (err) {
            result.error = err instanceof Error ? err.message : String(err);
            errors++;
            if (verbose) {
              console.error(`  [embed error] ${chunk.chunk_id}: ${result.error}`);
            }
          }
        } else {
          result.embedded = true; // already had embedding
          embedded++;
        }

        results.push(result);
      }
    } finally {
      db.release();
    }

    if (verbose) {
      const progress = Math.min(i + batchSize, chunks.length);
      console.log(`  Progress: ${progress}/${chunks.length} chunks | inserted=${inserted} skipped=${skipped} embedded=${embedded} errors=${errors}`);
    }

    if (i + batchSize < chunks.length) {
      await sleep(batchDelayMs);
    }
  }

  if (verbose) {
    console.log(`\nEmbedding complete: inserted=${inserted} skipped=${skipped} embedded=${embedded} errors=${errors}`);
  }

  return results;
}
