import 'server-only'
import { GoogleAuth } from 'google-auth-library'
import { buildKey, cacheGetOrCompute } from '@/lib/cache/shared_cache'

// Vertex AI text-multilingual-embedding-002 — 768 dims, ADC auth.
// Matches embed.py and vector_search.ts VERTEX_EMBED_DIM.
const VERTEX_MODEL = 'text-multilingual-embedding-002'
export const EMBED_DIM = 768

// Vertex AI :predict accepts up to 250 instances per call for embedding
// models. We keep a safety margin and chunk above this.
//   docs: https://cloud.google.com/vertex-ai/generative-ai/docs/embeddings/get-text-embeddings
const VERTEX_BATCH_LIMIT = 250

// Embeddings are pure deterministic functions of (model, text) — safe to
// cache aggressively. 24-hour TTL is conservative.
const EMBED_CACHE_TTL_SECONDS = 24 * 60 * 60

// ── Shared infra: cached auth client (re-used across calls) ───────────────────

let _auth: GoogleAuth | null = null
function getAuth(): GoogleAuth {
  if (!_auth) {
    _auth = new GoogleAuth({ scopes: ['https://www.googleapis.com/auth/cloud-platform'] })
  }
  return _auth
}

function predictEndpoint(): string {
  const project = process.env['GCP_PROJECT'] ?? ''
  const location = process.env['VERTEX_AI_LOCATION'] ?? ''
  if (!project) throw new Error('GCP_PROJECT not set')
  if (!location) throw new Error('VERTEX_AI_LOCATION not set')
  return (
    `https://${location}-aiplatform.googleapis.com/v1/projects/${project}` +
    `/locations/${location}/publishers/google/models/${VERTEX_MODEL}:predict`
  )
}

interface PredictResponse {
  predictions?: Array<{ embeddings?: { values?: number[] } }>
}

async function callPredict(instances: Array<{ task_type: string; content: string }>): Promise<number[][]> {
  const client = await getAuth().getClient()
  const { token } = await client.getAccessToken()
  const response = await fetch(predictEndpoint(), {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token ?? ''}`,
    },
    body: JSON.stringify({ instances }),
  })
  if (!response.ok) {
    throw new Error(`Vertex AI embeddings returned ${response.status}`)
  }
  const data = (await response.json()) as PredictResponse
  const preds = data.predictions ?? []
  if (preds.length !== instances.length) {
    throw new Error(
      `Vertex AI returned ${preds.length} predictions for ${instances.length} instances`,
    )
  }
  const out: number[][] = []
  for (let i = 0; i < preds.length; i++) {
    const values = preds[i].embeddings?.values
    if (!values || values.length !== EMBED_DIM) {
      throw new Error(
        `Unexpected embedding dim at instance ${i}: got ${values?.length ?? 0}, expected ${EMBED_DIM}`,
      )
    }
    out.push(values)
  }
  return out
}

// ── Public API ────────────────────────────────────────────────────────────────

/**
 * Embed a single text string. Cached via Memorystore-backed shared cache
 * (24h TTL); on miss, delegates to the batched compute path.
 *
 * For N > 1 callers should prefer `embedTexts(texts)` directly to avoid
 * N round-trips (the batch path is uncached — callers that want caching
 * for individual texts call this in a loop).
 */
export async function embedText(text: string): Promise<number[]> {
  const key = buildKey('vertex-embed', { model: VERTEX_MODEL, text })
  return cacheGetOrCompute('vertex-embed', key, EMBED_CACHE_TTL_SECONDS, async () => {
    const [v] = await embedTexts([text])
    return v
  })
}

/**
 * Embed a batch of text strings in as few Vertex AI :predict round-trips as
 * possible.
 *
 * Vertex accepts up to VERTEX_BATCH_LIMIT instances per call; we chunk above
 * that. A 50-text input therefore consumes 1 request (not 50) — closing the
 * latency + cost regression flagged in audit §4.1.
 */
export async function embedTexts(texts: string[]): Promise<number[][]> {
  if (texts.length === 0) return []

  const out: number[][] = new Array(texts.length)
  for (let start = 0; start < texts.length; start += VERTEX_BATCH_LIMIT) {
    const slice = texts.slice(start, start + VERTEX_BATCH_LIMIT)
    const instances = slice.map(content => ({ task_type: 'RETRIEVAL_DOCUMENT', content }))
    const vectors = await callPredict(instances)
    for (let i = 0; i < vectors.length; i++) {
      out[start + i] = vectors[i]
    }
  }
  return out
}

