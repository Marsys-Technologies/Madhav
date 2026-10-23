/**
 * GET /api/mcp/health/migrations — digest of the applied-migration ledger.
 *
 * Called by the MCP service's own /health (platform-mcp/src/lib/deploy_identity.ts) so that /health can state
 * `migration_set`; the MCP service has no database connection of its own. Same guard as the sibling
 * /api/mcp/health/tools and /health/coverage routes: `X-MCP-Internal-Token`, fail-closed. No auth change.
 *
 * Reads `_migrations_applied.filename` only (see migration_set_digest.ts). 200 `{ok:true, migration_set}`;
 * 503 `{ok:false, reason}` when the ledger cannot be read, never an empty digest.
 */
import 'server-only'
import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'
import { query } from '@/lib/db/client'
import { validateServiceToken } from '@/lib/mcp/service_token'
import { readMigrationSet } from '@/lib/mcp/migration_set_digest'

export const dynamic = 'force-dynamic'

export async function GET(req: NextRequest): Promise<Response> {
  if (!validateServiceToken(req)) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }
  const read = await readMigrationSet((sql) => query(sql))
  return NextResponse.json(read, { status: read.ok ? 200 : 503 })
}
