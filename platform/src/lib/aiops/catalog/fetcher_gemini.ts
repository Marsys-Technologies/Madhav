import type { CatalogFetchResult, RawModelEntry } from './types'

const ENDPOINT = 'https://generativelanguage.googleapis.com/v1beta/models'
const TIMEOUT_MS = 15_000

interface GeminiModel {
  name: string
  displayName?: string
  inputTokenLimit?: number
  outputTokenLimit?: number
  supportedGenerationMethods?: string[]
}

export async function fetchGeminiCatalog(): Promise<CatalogFetchResult> {
  const apiKey = process.env.GOOGLE_API_KEY ?? process.env.GOOGLE_GENERATIVE_AI_API_KEY
  if (!apiKey) {
    return { status: 'unconfigured', models: [], raw: null, fetched_at: new Date().toISOString() }
  }

  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS)

  try {
    const url = `${ENDPOINT}?key=${apiKey}&pageSize=100`
    const res = await fetch(url, { signal: controller.signal })
    clearTimeout(timer)

    if (res.status === 401 || res.status === 403) {
      return { status: 'auth_fail', models: [], raw: null, fetched_at: new Date().toISOString() }
    }
    if (!res.ok) {
      return { status: 'error', models: [], raw: { status: res.status }, fetched_at: new Date().toISOString() }
    }

    const json = await res.json() as { models?: GeminiModel[] }
    const raw = json.models ?? []
    // Strip the "models/" prefix from name → model_id
    const entries: RawModelEntry[] = raw.map(m => ({
      id:       m.name.replace(/^models\//, ''),
      label:    m.displayName ?? m.name.replace(/^models\//, ''),
      owned_by: 'google',
    }))

    return { status: 'ok', models: entries as unknown as CatalogFetchResult['models'], raw: json, fetched_at: new Date().toISOString() }
  } catch (err: unknown) {
    clearTimeout(timer)
    const isAbort = err instanceof Error && err.name === 'AbortError'
    const msg = err instanceof Error ? err.message.replace(apiKey, '[REDACTED]') : String(err)
    return { status: isAbort ? 'timeout' : 'error', models: [], raw: { error: msg }, fetched_at: new Date().toISOString() }
  }
}
