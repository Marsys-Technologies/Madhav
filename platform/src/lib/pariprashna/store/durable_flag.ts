/**
 * Paripraśna durable persistence — the ONE flag read site.
 *
 * Mirrors `consent/flag.ts`'s idiom exactly (see that file's header for why
 * `configService.getFlag` rather than the bare `getFlag` helper): every entry
 * point in `durable_outbox.ts` / `durable_writer.ts` routes its gate through
 * `isDurablePersistenceEnabled()`, so "nothing here changes behavior until the
 * flag is ON" is one line, and a test can prove it by that one line.
 */

import { configService } from '@/lib/config/index'

/** The feature flag that arms the write-ahead outbox path. Default OFF. */
export const DURABLE_PERSISTENCE_FLAG = 'PARIPRASHNA_DURABLE_PERSISTENCE_ENABLED' as const

export function isDurablePersistenceEnabled(): boolean {
  return configService.getFlag(DURABLE_PERSISTENCE_FLAG)
}
