import 'server-only'
import { AiConsoleError, normalizeAiError } from '../errors'
import { claimCliCatalogRefresh, finishCliCatalogRefresh } from '../repository'
import { CliIdSchema } from '../types'
import { validateCli } from './validation'

/** Refresh the configured host's metadata without generating a model response. */
export async function refreshCliCatalog(userId: string, cliId: unknown,
  options: { force?: boolean; signal?: AbortSignal } = {}) {
  const id = CliIdSchema.parse(cliId)
  if (options.signal?.aborted) throw new AiConsoleError('AI_EXECUTION_FAILED')
  const epoch = await claimCliCatalogRefresh(userId, id, options.force === true)
  if (!epoch) return { status: 'skipped' as const }
  const deadline = AbortSignal.timeout(60_000)
  const signal = options.signal ? AbortSignal.any([options.signal, deadline]) : deadline
  let result: Awaited<ReturnType<typeof validateCli>>
  try {
    if (signal.aborted) throw new AiConsoleError('AI_EXECUTION_FAILED')
    result = await validateCli(userId, id, signal, { metadataOnly: true })
    if (signal.aborted) throw new AiConsoleError('AI_EXECUTION_FAILED')
  } catch (error) {
    const safe = normalizeAiError(options.signal?.aborted ? new AiConsoleError('AI_EXECUTION_FAILED')
      : deadline.aborted ? new AiConsoleError('AI_CLI_TIMEOUT') : error, { source: 'cli' })
    // A cleanup outage must not leak a raw database message. The bounded lease
    // can expire naturally if release fails; do not retry another epoch's lease.
    try { await finishCliCatalogRefresh(id, epoch, safe.code) } catch { /* lease expires */ }
    throw new AiConsoleError(safe.code)
  }
  try {
    if (!await finishCliCatalogRefresh(id, epoch, result.errorCode)) throw new AiConsoleError('AI_EXECUTION_FAILED')
  } catch (error) { throw new AiConsoleError(normalizeAiError(error, { source: 'cli' }).code) }
  return { status: 'refreshed' as const, ...result }
}
