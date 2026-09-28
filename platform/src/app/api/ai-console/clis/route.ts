import { listAiConsoleState } from '@/lib/ai-console/repository'
import { json, projectCliCards, withAiConsole } from '../_shared'

export const dynamic = 'force-dynamic'

export async function GET() {
  return withAiConsole(async userId => json({ clis: projectCliCards(await listAiConsoleState(userId)) }))
}
