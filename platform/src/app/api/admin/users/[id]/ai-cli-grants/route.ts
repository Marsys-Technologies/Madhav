import { NextResponse } from 'next/server'
import { z } from 'zod'
import { requireSuperAdmin } from '@/lib/auth/access-control'
import { getFlag } from '@/lib/config'
import { AiConsoleError } from '@/lib/ai-console/errors'
import { listAdminCliGrants, setCliGrant } from '@/lib/ai-console/repository'
import { CLI_REGISTRY } from '@/lib/ai-console/cli/registry'
import { CliIdSchema } from '@/lib/ai-console/types'
import { checkAiConsoleMutationRate, json, readBody, requestErrorResponse } from '@/app/api/ai-console/_shared'

export const dynamic = 'force-dynamic'
type Context = { params: Promise<{ id: string }> }
const Body = z.object({ cliId: CliIdSchema, granted: z.boolean() }).strict()

async function authorize(context: Context): Promise<
  { response: NextResponse } | { actorId: string; userId: string }
> {
  if (!getFlag('AI_CONSOLE_BYOK')) return { response: json({ error: 'not_found' }, 404) }
  const auth = await requireSuperAdmin()
  if (auth instanceof NextResponse) return { response: auth }
  const userId = z.string().min(1).max(256).safeParse((await context.params).id)
  if (!userId.success) return { response: json({ error: 'invalid_request' }, 400) }
  return { actorId: auth.user.uid, userId: userId.data }
}

export async function GET(_request: Request, context: Context) {
  const authorized = await authorize(context)
  if ('response' in authorized) return authorized.response
  try {
    const rows = await listAdminCliGrants(authorized.actorId, authorized.userId)
    return json({ grants: rows.map(row => {
      const cliId = CliIdSchema.parse(row.cli_id)
      return { cliId, productName: CLI_REGISTRY[cliId].productName,
        granted: row.granted_at != null && row.revoked_at == null,
        hostState: CLI_REGISTRY[cliId].execution
          ? z.enum(['reachable', 'unavailable']).parse(row.host_state) : 'unavailable' as const }
    }) })
  } catch (error) {
    return error instanceof AiConsoleError && error.code === 'AI_PERMISSION_DENIED'
      ? json({ error: 'forbidden' }, 403) : json({ error: 'internal_error' }, 500)
  }
}

export async function PATCH(request: Request, context: Context) {
  const authorized = await authorize(context)
  if ('response' in authorized) return authorized.response
  try {
    checkAiConsoleMutationRate(authorized.actorId, 'admin-cli-grant')
    const body = await readBody(request, Body)
    await setCliGrant(authorized.actorId, authorized.userId, body.cliId, body.granted)
    return json({ cliId: body.cliId, granted: body.granted })
  } catch (error) {
    const requestError = requestErrorResponse(error)
    if (requestError) return requestError
    if (error instanceof AiConsoleError && error.code === 'AI_PERMISSION_DENIED') {
      return json({ error: 'forbidden' }, 403)
    }
    return json({ error: 'internal_error' }, 500)
  }
}
