import type { CatalogFetchResult, RawModelEntry } from './types'

const ENDPOINT = 'https://integrate.api.nvidia.com/v1/models'
const TIMEOUT_MS = 15_000

export async function fetchNimCatalog(): Promise<CatalogFetchResult> {
  const apiKey = process.env.NVIDIA_NIM_API_KEY
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
    const raw = json.data ?? []
    return {
      status: 'ok',
      models: raw.map(m => ({ id: m.id, owned_by: m.owned_by })) as unknown as CatalogFetchResult['models'],
      raw: json,
      fetched_at: new Date().toISOString(),
    }
  } catch (err: unknown) {
    clearTimeout(timer)
    const isAbort = err instanceof Error && err.name === 'AbortError'
    return {
      status: isAbort ? 'timeout' : 'error',
      models: [],
      raw: { error: err instanceof Error ? err.message.replace(apiKey, '[REDACTED]') : String(err) },
      fetched_at: new Date().toISOString(),
    }
  }
}
