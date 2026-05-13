import 'server-only'
import { NextResponse } from 'next/server'
import { res } from '@/lib/errors'
import { guardAiopsRoute } from '@/app/api/admin/aiops/_guard'
import { fetchProviderCatalog } from '@/lib/aiops/catalog/fetcher'
import type { Provider } from '@/lib/models/registry'

export const dynamic = 'force-dynamic'

type Params = { provider: string }

const VALID_PROVIDERS: Provider[] = ['nvidia', 'google', 'deepseek', 'openai', 'anthropic']

// GET /api/admin/aiops/catalog/[provider]
export async function GET(_req: Request, { params }: { params: Promise<Params> }) {
  const guard = await guardAiopsRoute()
  if (guard instanceof NextResponse) return guard

  const { provider } = await params
  if (!VALID_PROVIDERS.includes(provider as Provider)) {
    return res.badRequest(`Unknown provider: ${provider}. Must be one of: ${VALID_PROVIDERS.join(', ')}`)
  }

  try {
    const result = await fetchProviderCatalog(provider as Provider)
    return NextResponse.json(result)
  } catch (err) {
    console.error('[aiops/catalog] GET error:', err)
    return res.internal('Failed to fetch catalog.')
  }
}
