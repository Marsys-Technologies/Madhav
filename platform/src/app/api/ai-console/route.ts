import { listAiConsoleState } from '@/lib/ai-console/repository'
import { json, projectState, withAiConsole } from './_shared'

export const dynamic = 'force-dynamic'

export async function GET() {
  return withAiConsole(async userId => json(projectState(await listAiConsoleState(userId))))
}
