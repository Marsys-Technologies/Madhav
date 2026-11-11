import 'server-only'

import { readMigrationSet, type MigrationSetRead } from '@/lib/mcp/migration_set_digest'
import { query } from './client'

export function readAppliedMigrationSet(): Promise<MigrationSetRead> {
  return readMigrationSet(query)
}
