import { z } from 'zod'
import { validateCli } from '@/lib/ai-console/cli/validation'
import {
  json, readBody, readCliId, withAiConsoleMutation, withCliValidationAdmission, type CliContext,
} from '../../../_shared'

export const dynamic = 'force-dynamic'

export async function POST(request: Request, context: CliContext) {
  return withAiConsoleMutation(async userId => {
    const cliId = await readCliId(context)
    return withCliValidationAdmission(userId, cliId, async () => {
      await readBody(request, z.object({}).strict(), true)
      return json({ validation: await validateCli(userId, cliId, request.signal) })
    })
  })
}
