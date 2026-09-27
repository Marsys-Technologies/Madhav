import { z } from 'zod'
import { setUserDefault } from '@/lib/ai-console/repository'
import { ChoiceInputSchema, json, readBody, withAiConsoleMutation } from '../_shared'

export const dynamic = 'force-dynamic'
const DefaultSchema = z.object({ choice: ChoiceInputSchema }).strict()

export async function PUT(request: Request) {
  return withAiConsoleMutation(async userId => {
    const { choice } = await readBody(request, DefaultSchema)
    await setUserDefault(userId, choice)
    return json({ defaultChoice: choice })
  })
}
