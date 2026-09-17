/** Execute the one-shot protected owner/migration transition under one DB lease. */
import { attestDataPlaneMigrations } from './data-plane-migration-attestation'
import { runDataPlaneOwnershipPreflight } from './data-plane-ownership-preflight'
import { readDataPlaneOwnershipStatus } from './data-plane-ownership-status'
import { validationAdminProxyConfig, withDataPlaneCutoverLease } from './data-plane-cutover-preflight'
import type { PoolConfig } from 'pg'

function required(name: string): string {
  const value = process.env[name]?.trim()
  if (!value) throw new Error(`${name} is required for the protected data-plane cutover.`)
  return value
}

/**
 * The ownership credential is a credential carrier for the production proxy
 * already started by privileged-bootstrap.  Unlike the isolated validation
 * route, this transaction mutates the production database, so no caller-
 * supplied host, port, database, or libpq query override may select its
 * destination.
 */
export function ownershipAdminProxyConfig(databaseUrl: string): Readonly<PoolConfig> {
  let route: URL
  try {
    route = new URL(databaseUrl)
  } catch {
    throw new Error('Data-plane ownership credential is not a valid production-proxy connection string.')
  }
  if (!['postgres:', 'postgresql:'].includes(route.protocol)
      || route.hostname !== '127.0.0.1' || route.port !== '5432'
      || route.pathname !== '/amjis' || route.search) {
    throw new Error('Data-plane ownership credential is not pinned to the authenticated production proxy route.')
  }
  const config = validationAdminProxyConfig(databaseUrl, { proxyPort: '5432' })
  if (config.user !== 'postgres' || config.database !== 'amjis') {
    throw new Error('Data-plane ownership credential must authenticate as postgres to the production amjis database.')
  }
  return config
}

export async function executeProtectedDataPlaneCutover(): Promise<void> {
  const validationAdminUrl = required('DATA_PLANE_ADMIN_DATABASE_URL')
  const ownershipAdminUrl = required('DATA_PLANE_OWNERSHIP_ADMIN_DATABASE_URL')
  const migratorUrl = required('DATA_PLANE_MIGRATOR_DATABASE_URL')
  // Validate the protected administrator credential before consuming any
  // backup/restore evidence or attempting the native cutover. The actual
  // connection remains pinned to the authenticated validation proxy inside
  // withDataPlaneCutoverLease.
  validationAdminProxyConfig(validationAdminUrl, {
    proxyPort: required('DATA_PLANE_RESTORE_VALIDATION_PROXY_PORT'),
  })
  const ownershipAdminProxy = ownershipAdminProxyConfig(ownershipAdminUrl)
  await withDataPlaneCutoverLease(async () => {
    await runDataPlaneOwnershipPreflight(ownershipAdminProxy)
    await attestDataPlaneMigrations(migratorUrl)
    if (await readDataPlaneOwnershipStatus(migratorUrl) !== 'marked') {
      throw new Error('Protected data-plane cutover did not earn semantic marked status.')
    }
  })
}

if (require.main === module) executeProtectedDataPlaneCutover().catch((error) => {
  console.error(error)
  process.exitCode = 1
})
