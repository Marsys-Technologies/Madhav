#!/usr/bin/env npx tsx
/**
 * MSR Signal-Grounding Pipeline — v3.4-S1 (Track A)
 *
 * For each ungrounded msr_signals row (source_citation IS NULL):
 *   1. Embed signal.claim_text via Vertex AI text-multilingual-embedding-002 (768-dim)
 *   2. Cosine-similarity search against FORENSIC + LEL rag_chunks / rag_embeddings
 *   3. Produce top-3 candidate citations per signal
 *   4. Write candidates to grounding_review_queue.ts (CSV + summary)
 *
 * Prerequisites:
 *   - Cloud SQL proxy: cloud-sql-proxy madhav-astrology:asia-south1:amjis-postgres --port=5433
 *   - ADC: gcloud auth application-default login
 *   - GCP_PROJECT + VERTEX_AI_LOCATION set
 *
 * Run:
 *   DATABASE_URL="postgresql://amjis_app:<pw>@127.0.0.1:5433/amjis" \
 *   GCP_PROJECT=madhav-astrology VERTEX_AI_LOCATION=asia-south1 \
 *   npx tsx scripts/grounding/msr_grounding_pipeline.ts
 *
 * Output: 00_ARCHITECTURE/grounding_review/msr_grounding_candidates_<timestamp>.csv
 */

import { Pool } from 'pg'
import { GoogleAuth } from 'google-auth-library'
import * as fs from 'fs'
import * as path from 'path'

// ── Config ───────────────────────────────────────────────────────────────────

const GCP_PROJECT     = process.env.GCP_PROJECT        ?? 'madhav-astrology'
const VERTEX_LOCATION = process.env.VERTEX_AI_LOCATION ?? 'asia-south1'
const VERTEX_MODEL    = 'text-multilingual-embedding-002'
const EMBED_DIM       = 768
const TOP_K           = 3
const BATCH_DELAY_MS  = 150  // rate-limit Vertex AI calls

const DATABASE_URL =
  process.env.DATABASE_URL ?? 'postgresql://amjis_app@127.0.0.1:5432/amjis'

const OUTPUT_DIR = path.join(
  process.cwd(), '..', '00_ARCHITECTURE', 'grounding_review'
)

// ── DB pool ───────────────────────────────────────────────────────────────────

const pool = new Pool({ connectionString: DATABASE_URL })
const auth = new GoogleAuth({ scopes: ['https://www.googleapis.com/auth/cloud-platform'] })

// ── Schema setup ─────────────────────────────────────────────────────────────
// Add grounding columns to msr_signals if not present. No formal migration
// needed — these columns are specific to the grounding campaign.

export async function ensureGroundingColumns(): Promise<void> {
  await pool.query(`
    ALTER TABLE msr_signals
      ADD COLUMN IF NOT EXISTS source_citation   TEXT,
      ADD COLUMN IF NOT EXISTS grounded_at       TIMESTAMPTZ,
      ADD COLUMN IF NOT EXISTS grounded_by       TEXT
  `)
  console.log('[setup] grounding columns ensured on msr_signals')
}

// ── Embedding ─────────────────────────────────────────────────────────────────

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
      instances: [{ task_type: 'RETRIEVAL_QUERY', content: text }],
    }),
  })

  if (!res.ok) throw new Error(`Vertex AI embed error ${res.status}: ${await res.text()}`)
  const data = await res.json()
  const values = data.predictions?.[0]?.embeddings?.values as number[] | undefined
  if (!values || values.length !== EMBED_DIM) {
    throw new Error(`Unexpected embed dim: got ${values?.length ?? 0}, want ${EMBED_DIM}`)
  }
  return values
}

// ── Signal query ─────────────────────────────────────────────────────────────

export interface UngroundedSignal {
  signal_id: string
  claim_text: string
  classical_basis: string | null
  domain: string
  planet: string | null
}

export async function fetchUngroundedSignals(): Promise<UngroundedSignal[]> {
  const { rows } = await pool.query<UngroundedSignal>(`
    SELECT signal_id, claim_text, classical_basis, domain, planet
    FROM msr_signals
    WHERE (source_citation IS NULL OR source_citation = '')
      AND native_id = 'abhisek'
    ORDER BY signal_id
  `)
  return rows
}

// ── Candidate search ──────────────────────────────────────────────────────────

export interface GroundingCandidate {
  chunk_id: string
  source_file: string
  section_label: string
  content_excerpt: string
  cosine_distance: number
}

const SQL_CANDIDATE_SEARCH = `
  SELECT
    e.chunk_id,
    c.source_file,
    COALESCE(c.metadata->>'section_id', c.metadata->>'section', '') AS section_label,
    LEFT(c.content, 300)                                             AS content_excerpt,
    (e.embedding <=> $1::vector)                                     AS cosine_distance
  FROM rag_embeddings e
  JOIN rag_chunks c ON e.chunk_id = c.chunk_id
  WHERE c.is_stale = false
    AND (
      c.source_file ILIKE '%FORENSIC%'
      OR c.source_file ILIKE '%LIFE_EVENT%'
      OR c.source_file ILIKE '%LEL%'
      OR c.canonical_id IN ('FORENSIC_v8_0', 'LEL_v1_6')
    )
  ORDER BY e.embedding <=> $1::vector
  LIMIT $2
`.trim()

export async function findCandidates(
  embedding: number[]
): Promise<GroundingCandidate[]> {
  const vecLiteral = `[${embedding.join(',')}]`
  const { rows } = await pool.query<{
    chunk_id: string
    source_file: string
    section_label: string
    content_excerpt: string
    cosine_distance: number
  }>(SQL_CANDIDATE_SEARCH, [vecLiteral, TOP_K])
  return rows.map((r) => ({
    chunk_id: r.chunk_id,
    source_file: r.source_file,
    section_label: r.section_label,
    content_excerpt: r.content_excerpt,
    cosine_distance: Number(r.cosine_distance),
  }))
}

// ── CSV row type ──────────────────────────────────────────────────────────────

export interface GroundingCsvRow {
  signal_id: string
  domain: string
  planet: string
  claim_excerpt: string
  candidate_1_chunk_id: string
  candidate_1_source: string
  candidate_1_section: string
  candidate_1_score: string
  candidate_1_excerpt: string
  candidate_2_chunk_id: string
  candidate_2_source: string
  candidate_2_section: string
  candidate_2_score: string
  candidate_2_excerpt: string
  candidate_3_chunk_id: string
  candidate_3_source: string
  candidate_3_section: string
  candidate_3_score: string
  candidate_3_excerpt: string
  accepted_candidate: string  // operator fills: 1|2|3|reject|defer
  override_citation: string   // operator fills: free-text custom citation if needed
}

function buildCsvRow(
  signal: UngroundedSignal,
  candidates: GroundingCandidate[]
): GroundingCsvRow {
  const c = (i: number): GroundingCandidate => candidates[i] ?? {
    chunk_id: '', source_file: '', section_label: '', content_excerpt: '', cosine_distance: 0
  }
  return {
    signal_id: signal.signal_id,
    domain: signal.domain,
    planet: signal.planet ?? '',
    claim_excerpt: signal.claim_text.substring(0, 120).replace(/\n/g, ' '),
    candidate_1_chunk_id: c(0).chunk_id,
    candidate_1_source: c(0).source_file,
    candidate_1_section: c(0).section_label,
    candidate_1_score: c(0).cosine_distance.toFixed(4),
    candidate_1_excerpt: c(0).content_excerpt.replace(/\n/g, ' ').substring(0, 200),
    candidate_2_chunk_id: c(1).chunk_id,
    candidate_2_source: c(1).source_file,
    candidate_2_section: c(1).section_label,
    candidate_2_score: c(1).cosine_distance.toFixed(4),
    candidate_2_excerpt: c(1).content_excerpt.replace(/\n/g, ' ').substring(0, 200),
    candidate_3_chunk_id: c(2).chunk_id,
    candidate_3_source: c(2).source_file,
    candidate_3_section: c(2).section_label,
    candidate_3_score: c(2).cosine_distance.toFixed(4),
    candidate_3_excerpt: c(2).content_excerpt.replace(/\n/g, ' ').substring(0, 200),
    accepted_candidate: '',
    override_citation: '',
  }
}

// ── CSV write ─────────────────────────────────────────────────────────────────

const CSV_HEADERS: (keyof GroundingCsvRow)[] = [
  'signal_id', 'domain', 'planet', 'claim_excerpt',
  'candidate_1_chunk_id', 'candidate_1_source', 'candidate_1_section', 'candidate_1_score', 'candidate_1_excerpt',
  'candidate_2_chunk_id', 'candidate_2_source', 'candidate_2_section', 'candidate_2_score', 'candidate_2_excerpt',
  'candidate_3_chunk_id', 'candidate_3_source', 'candidate_3_section', 'candidate_3_score', 'candidate_3_excerpt',
  'accepted_candidate', 'override_citation',
]

function escapeCsv(v: string): string {
  if (v.includes('"') || v.includes(',') || v.includes('\n')) {
    return `"${v.replace(/"/g, '""')}"`
  }
  return v
}

export function writeCsv(rows: GroundingCsvRow[], outputPath: string): void {
  const lines = [
    CSV_HEADERS.join(','),
    ...rows.map((r) => CSV_HEADERS.map((h) => escapeCsv(r[h])).join(',')),
  ]
  fs.mkdirSync(path.dirname(outputPath), { recursive: true })
  fs.writeFileSync(outputPath, lines.join('\n'), 'utf8')
}

// ── Progress file (for resumption) ───────────────────────────────────────────

export interface PipelineProgress {
  timestamp: string
  total: number
  processed: number
  csv_path: string
}

// ── Main ─────────────────────────────────────────────────────────────────────

async function sleep(ms: number): Promise<void> {
  return new Promise((r) => setTimeout(r, ms))
}

export async function runPipeline(options?: {
  limit?: number
  dryRun?: boolean
}): Promise<{ csvPath: string; processed: number; total: number }> {
  console.log('[pipeline] MSR signal-grounding pipeline starting...')

  await ensureGroundingColumns()

  const signals = await fetchUngroundedSignals()
  console.log(`[pipeline] found ${signals.length} ungrounded signals`)

  const limit = options?.limit ?? signals.length
  const subset = signals.slice(0, limit)

  const rows: GroundingCsvRow[] = []
  let processed = 0

  for (const signal of subset) {
    try {
      const embedding = await embedText(signal.claim_text)
      const candidates = await findCandidates(embedding)
      rows.push(buildCsvRow(signal, candidates))
      processed++

      if (processed % 50 === 0) {
        console.log(`[pipeline] ${processed}/${subset.length} processed`)
      }

      if (!options?.dryRun) {
        await sleep(BATCH_DELAY_MS)
      }
    } catch (err) {
      console.error(`[pipeline] ERROR on signal ${signal.signal_id}:`, err)
      rows.push(buildCsvRow(signal, []))
    }
  }

  const ts = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19)
  const csvPath = path.join(OUTPUT_DIR, `msr_grounding_candidates_${ts}.csv`)

  if (!options?.dryRun) {
    writeCsv(rows, csvPath)
    console.log(`[pipeline] CSV written → ${csvPath}`)
    console.log(`[pipeline] NEXT: open CSV, fill 'accepted_candidate' column, then run apply_grounded_citations.ts`)
  }

  return { csvPath, processed, total: signals.length }
}

// Script entry
if (require.main === module || process.argv[1]?.endsWith('msr_grounding_pipeline.ts')) {
  runPipeline()
    .then(({ csvPath, processed, total }) => {
      console.log(`\n[done] ${processed} signals processed. CSV: ${csvPath}`)
      console.log(`[done] ${total - processed} signals remaining (run again to continue)`)
      process.exit(0)
    })
    .catch((err) => {
      console.error('[fatal]', err)
      process.exit(1)
    })
    .finally(() => pool.end())
}
