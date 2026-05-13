import type { CatalogFetchResult, RawModelEntry } from './types'

const ENDPOINT = 'https://api.openai.com/v1/models'
const TIMEOUT_MS = 15_000

export async function fetchOpenaiCatalog(): Promise<CatalogFetchResult> {
  const apiKey = process.env.OPENAI_API_KEY
  if (!apiKey) {
    return { status: 'unconfigured', models: [], raw: null, fetched_at: new Date().toISOString() }
  }

  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS)

  try {
    const res = await fetch(ENDPOINT, {
      headers: { Authorization: `Bearer ${apiKey}` },
      signal: controller.signal,
    })
    clearTimeout(timer)

    if (res.status === 401 || res.status === 403) {
      return { status: 'auth_fail', models: [], raw: null, fetched_at: new Date().toISOString() }
    }
    if (!res.ok) {
      return { status: 'error', models: [], raw: { status: res.status }, fetched_at: new Date().toISOString() }
    }

    const json = await res.json() as { data?: RawModelEntry[] }
    // Filter to gpt-* models only; the endpoint returns embeddings, Whisper, DALL-E, etc.
    const raw = (json.data ?? []).filter(m => typeof m.id === 'string' && m.id.startsWith('gpt-'))
    return { status: 'ok', models: raw as unknown as CatalogFetchResult['models'], raw: json, fetched_at: new Date().toISOString() }
  } catch (err: unknown) {
    clearTimeout(timer)
    const isAbort = err instanceof Error && err.name === 'AbortError'
    const msg = err instanceof Error ? err.message.replace(apiKey, '[REDACTED]') : String(err)
    return { status: isAbort ? 'timeout' : 'error', models: [], raw: { error: msg }, fetched_at: new Date().toISOString() }
  }
}
