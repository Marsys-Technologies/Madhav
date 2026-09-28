import { validateConnection } from '@/lib/ai-console/validation'
import { ChargeSchema, VALIDATION_DISCLOSURE, json, ownedConnection, projectValidation, readBody, readId, withAiConsole, withAiConsoleMutation, withValidationAdmission, type IdContext } from '../../../_shared'

export const dynamic = 'force-dynamic'

export async function GET(_request: Request, context: IdContext) {
  return withAiConsole(async userId => {
    await ownedConnection(userId, await readId(context))
    return json({ validationDisclosure: VALIDATION_DISCLOSURE })
  })
}

export async function POST(request: Request, context: IdContext) {
  return withAiConsoleMutation(async userId => {
    const id = await readId(context)
    return withValidationAdmission(userId, id, async () => {
      await readBody(request, ChargeSchema)
      const { credentialVersion } = await ownedConnection(userId, id)
      const validation = projectValidation(await validateConnection(userId, id, { credentialVersion, signal: request.signal }))
      return json({ validation, validationDisclosure: VALIDATION_DISCLOSURE })
    })
  })
}
