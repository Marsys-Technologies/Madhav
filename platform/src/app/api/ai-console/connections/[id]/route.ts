import { z } from 'zod'
import { deleteConnection, renameConnection, replaceConnectionCredential } from '@/lib/ai-console/repository'
import { encryptCredential } from '@/lib/ai-console/crypto'
import { validateConnection } from '@/lib/ai-console/validation'
import { CredentialSchema, DeleteSchema, NameSchema, VALIDATION_DISCLOSURE, dependencyPreview, json, ownedConnection,
  projectConnection, projectValidation, readBody, readId, withAiConsole, withAiConsoleMutation, withValidationAdmission, type IdContext } from '../../_shared'

export const dynamic = 'force-dynamic'

// One mutation per request. Clients use two explicit requests to change name and key.
const PatchSchema = z.union([
  z.object({ name: NameSchema }).strict(),
  z.object({ apiKey: CredentialSchema, acknowledgeCharge: z.literal(true) }).strict(),
])

export async function GET(_request: Request, context: IdContext) {
  return withAiConsole(async userId => {
    const id = await readId(context)
    const { connection } = await ownedConnection(userId, id)
    return json({ connection, dependencies: await dependencyPreview(userId, 'connection', id), validationDisclosure: VALIDATION_DISCLOSURE })
  })
}

export async function PATCH(request: Request, context: IdContext) {
  return withAiConsoleMutation(async userId => {
    const id = await readId(context)
    const input = await readBody(request, PatchSchema)
    if (!('apiKey' in input)) {
      await ownedConnection(userId, id)
      return json({ connection: projectConnection(await renameConnection(userId, id, input.name)) })
    }
    return withValidationAdmission(userId, id, async () => {
      await ownedConnection(userId, id)
      const replaced = await replaceConnectionCredential(userId, id, encryptCredential(input.apiKey))
      const validation = projectValidation(await validateConnection(userId, id, { credentialVersion: replaced.credentialVersion, signal: request.signal }))
      const connection = (await ownedConnection(userId, id)).connection
      return json({ connection: { ...connection, validationState: validation.state }, validation, validationDisclosure: VALIDATION_DISCLOSURE })
    })
  })
}

export async function DELETE(request: Request, context: IdContext) {
  return withAiConsoleMutation(async userId => {
    const id = await readId(context)
    const input = await readBody(request, DeleteSchema, true)
    await ownedConnection(userId, id)
    const dependencies = await dependencyPreview(userId, 'connection', id)
    if (input.confirm !== true) return json({ error: 'confirmation_required', dependencies }, 409)
    await deleteConnection(userId, id, true)
    return json({ deleted: true, id, dependencies })
  })
}
