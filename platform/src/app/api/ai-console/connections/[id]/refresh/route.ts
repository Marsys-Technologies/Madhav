import { z } from 'zod'
import { refreshProviderCatalog } from '@/lib/ai-console/catalog-refresh'
import { json, readBody, readId, withAiConsoleMutation, type IdContext } from '../../../_shared'

export const dynamic = 'force-dynamic'

const RefreshSchema = z.object({ force: z.boolean().optional() }).strict()

export async function POST(request: Request, context: IdContext) {
  return withAiConsoleMutation(async userId => {
    const id = await readId(context)
    const { force } = await readBody(request, RefreshSchema, true)
    return json(await refreshProviderCatalog(userId, id, { force, signal: request.signal }))
  })
}
