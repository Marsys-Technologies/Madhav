import { z } from 'zod'
import { duplicateConfiguration, listAiConsoleState, saveConfiguration } from '@/lib/ai-console/repository'
import { AssignmentsInputSchema, IdSchema, NameSchema, json, ownedConfiguration, projectConfiguration, projectState, readBody, withAiConsole } from '../_shared'

export const dynamic = 'force-dynamic'

const CreateSchema = z.union([
  z.object({ name: NameSchema, roles: AssignmentsInputSchema }).strict(),
  z.object({ name: NameSchema, duplicateFrom: IdSchema }).strict(),
])

export async function GET() {
  return withAiConsole(async userId => json({ configurations: projectState(await listAiConsoleState(userId)).configurations }))
}

export async function POST(request: Request) {
  return withAiConsole(async userId => {
    const input = await readBody(request, CreateSchema)
    if ('duplicateFrom' in input) {
      await ownedConfiguration(userId, input.duplicateFrom)
      return json({ configuration: projectConfiguration(await duplicateConfiguration(userId, input.duplicateFrom, input.name)) }, 201)
    }
    return json({ configuration: projectConfiguration(await saveConfiguration(userId, input)) }, 201)
  })
}
