import { z } from 'zod'
import { testAndAddManualCliModel } from '@/lib/ai-console/cli/validation'
import { json, readBody, readCliId, withAiConsoleMutation, withCliValidationAdmission, type CliContext } from '../../../_shared'

export const dynamic = 'force-dynamic'

const CandidateSchema = z.object({ modelId: z.string().min(1).max(512) }).strict()

export async function POST(request: Request, context: CliContext) {
  return withAiConsoleMutation(async userId => {
    const cliId = await readCliId(context)
    const { modelId } = await readBody(request, CandidateSchema)
    return withCliValidationAdmission(userId, cliId, async () => {
      await testAndAddManualCliModel(userId, cliId, modelId, request.signal)
      return json({ added: true, modelId })
    })
  })
}
