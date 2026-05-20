import 'server-only'
import { GoogleAuth } from 'google-auth-library'

// Vertex AI text-multilingual-embedding-002 — 768 dims, ADC auth.
// Matches embed.py and vector_search.ts VERTEX_EMBED_DIM.
const VERTEX_MODEL = 'text-multilingual-embedding-002'
export const EMBED_DIM = 768

export async function embedText(text: string): Promise<number[]> {
  const project = process.env.GCP_PROJECT ?? ''
  const location = process.env.VERTEX_AI_LOCATION ?? ''

  if (!project) throw new Error('GCP_PROJECT not set')
  if (!location) throw new Error('VERTEX_AI_LOCATION not set')

  const endpoint =
    `https://${location}-aiplatform.googleapis.com/v1/projects/${project}` +
    `/locations/${location}/publishers/google/models/${VERTEX_MODEL}:predict`

  const auth = new GoogleAuth({ scopes: ['https://www.googleapis.com/auth/cloud-platform'] })
  const client = await auth.getClient()
  const { token } = await client.getAccessToken()

  const response = await fetch(endpoint, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token ?? ''}`,
    },
    body: JSON.stringify({
      instances: [{ task_type: 'RETRIEVAL_DOCUMENT', content: text }],
    }),
  })

  if (!response.ok) {
    throw new Error(`Vertex AI embeddings returned ${response.status}`)
  }

  const data = await response.json()
  const values = data.predictions?.[0]?.embeddings?.values as number[] | undefined
  if (!values || values.length !== EMBED_DIM) {
    throw new Error(`Unexpected embedding dim: got ${values?.length ?? 0}, expected ${EMBED_DIM}`)
  }
  return values
}
