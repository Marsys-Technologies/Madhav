import { z } from 'zod'
import { refreshCliCatalog } from '@/lib/ai-console/cli/refresh'
import { json, readBody, readCliId, withAiConsoleMutation, type CliContext } from '../../../_shared'

export const dynamic = 'force-dynamic'
export const maxDuration = 65
const RefreshSchema = z.object({ force: z.boolean().optional() }).strict()

export async function POST(request: Request, context: CliContext) {
  return withAiConsoleMutation(async userId => {
    const id = await readCliId(context)
    const input = await readBody(request, RefreshSchema, true)
    return json(await refreshCliCatalog(userId, id, { force: input.force, signal: request.signal }))
  })
}
