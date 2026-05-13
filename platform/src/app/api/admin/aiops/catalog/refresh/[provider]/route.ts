import 'server-only'
import { NextResponse } from 'next/server'
import { res } from '@/lib/errors'
import { guardAiopsRoute } from '@/app/api/admin/aiops/_guard'
import { invalidateProvider } from '@/lib/aiops/catalog/cache'
import { fetchProviderCatalog } from '@/lib/aiops/catalog/fetcher'
import type { Provider } from '@/lib/models/registry'

export const dynamic = 'force-dynamic'

type Params = { provider: string }

const VALID_PROVIDERS: Provider[] = ['nvidia', 'google', 'deepseek', 'openai', 'anthropic']

// POST /api/admin/aiops/catalog/refresh/[provider]
export async function POST(_req: Request, { params }: { params: Promise<Params> }) {
  const guard = await guardAiopsRoute()
  if (guard instanceof NextResponse) return guard

  const { provider: providerRaw } = await params
  if (!VALID_PROVIDERS.includes(providerRaw as Provider)) {
    return res.badRequest(`Unknown provider: ${providerRaw}`)
  }

  const provider = providerRaw as Provider

  try {
    invalidateProvider(provider)
    const result = await fetchProviderCatalog(provider)
    return NextResponse.json({ provider, status: result.status, model_count: result.models.length, fetched_at: result.fetched_at })
  } catch (err) {
    console.error('[aiops/catalog/refresh] POST error:', err)
    return res.internal('Failed to refresh catalog.')
  }
}
