import { z } from 'zod'
import { deselectProviderModel } from '@/lib/ai-console/repository'
import { testAndSelectProviderModel } from '@/lib/ai-console/validation'
import { json, readBody, readId, withAiConsoleMutation, withValidationAdmission, type IdContext } from '../../../_shared'

export const dynamic = 'force-dynamic'

const ModelSchema = z.object({ modelId: z.string().min(1).max(512) }).strict()
const TestSchema = ModelSchema.extend({ acknowledgeCharge: z.literal(true) })

export async function POST(request: Request, context: IdContext) {
  return withAiConsoleMutation(async userId => {
    const id = await readId(context)
    const { modelId } = await readBody(request, TestSchema)
    return withValidationAdmission(userId, `model:${id}:${modelId}`, async () => {
      await testAndSelectProviderModel(userId, id, modelId, request.signal)
      return json({ selected: true, modelId })
    })
  })
}

export async function DELETE(request: Request, context: IdContext) {
  return withAiConsoleMutation(async userId => {
    const id = await readId(context)
    const { modelId } = await readBody(request, ModelSchema)
    await deselectProviderModel(userId, id, modelId)
    return json({ selected: false, modelId })
  })
}
