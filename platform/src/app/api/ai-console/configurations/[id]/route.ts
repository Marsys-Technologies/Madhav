import { z } from 'zod'
import { deleteConfiguration, saveConfiguration } from '@/lib/ai-console/repository'
import { AssignmentsInputSchema, ConfigurationScopeInputSchema, DeleteSchema, NameSchema, dependencyPreview, json, ownedConfiguration, projectConfiguration,
  readBody, readId, validConfigurationScope, withAiConsole, withAiConsoleMutation, type IdContext } from '../../_shared'

export const dynamic = 'force-dynamic'

// A full atomic edit (including rename) carries all four roles and the viewed version.
const EditSchema = z.object({ name: NameSchema, expectedVersion: z.number().int().positive(), roles: AssignmentsInputSchema })
  .merge(ConfigurationScopeInputSchema).strict().refine(validConfigurationScope)

export async function GET(_request: Request, context: IdContext) {
  return withAiConsole(async userId => {
    const id = await readId(context)
    const configuration = await ownedConfiguration(userId, id)
    return json({ configuration, dependencies: await dependencyPreview(userId, 'configuration', id) })
  })
}

export async function PATCH(request: Request, context: IdContext) {
  return withAiConsoleMutation(async userId => {
    const id = await readId(context)
    const input = await readBody(request, EditSchema)
    await ownedConfiguration(userId, id)
    return json({ configuration: projectConfiguration(await saveConfiguration(userId, { id, ...input })) })
  })
}

export async function DELETE(request: Request, context: IdContext) {
  return withAiConsoleMutation(async userId => {
    const id = await readId(context)
    const input = await readBody(request, DeleteSchema, true)
    await ownedConfiguration(userId, id)
    const dependencies = await dependencyPreview(userId, 'configuration', id)
    if (input.confirm !== true) return json({ error: 'confirmation_required', dependencies }, 409)
    await deleteConfiguration(userId, id, true)
    return json({ deleted: true, id, dependencies })
  })
}
