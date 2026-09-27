import { z } from 'zod'
import { createConnection, listAiConsoleState } from '@/lib/ai-console/repository'
import { encryptCredential } from '@/lib/ai-console/crypto'
import { validateConnection } from '@/lib/ai-console/validation'
import { ProviderIdSchema } from '@/lib/ai-console/types'
import { CredentialSchema, NameSchema, VALIDATION_DISCLOSURE, json, projectConnection, projectState, projectValidation, readBody, reserveValidationFlight, withAiConsole, withAiConsoleMutation, withValidationAdmission } from '../_shared'

export const dynamic = 'force-dynamic'

const CreateSchema = z.object({ name: NameSchema, providerId: ProviderIdSchema,
  apiKey: CredentialSchema, acknowledgeCharge: z.literal(true) }).strict()

export async function GET() {
  return withAiConsole(async userId => {
    const state = projectState(await listAiConsoleState(userId))
    return json({ connections: state.connections, models: state.models, validationDisclosure: VALIDATION_DISCLOSURE })
  })
}

export async function POST(request: Request) {
  return withAiConsoleMutation(async userId => withValidationAdmission(userId, 'create', async () => {
    const input = await readBody(request, CreateSchema)
    const connection = projectConnection(await createConnection(userId,
      { name: input.name, providerId: input.providerId }, encryptCredential(input.apiKey)))
    // The new identity is now observable. Reserve it synchronously before any next
    // await, while the outer create flight still prevents overlapping creation.
    const release = reserveValidationFlight(userId, connection.id)
    try {
      const validation = projectValidation(await validateConnection(userId, connection.id, { credentialVersion: 1, signal: request.signal }))
      return json({ connection: { ...connection, validationState: validation.state }, validation, validationDisclosure: VALIDATION_DISCLOSURE }, 201)
    } finally { release() }
  }))
}
