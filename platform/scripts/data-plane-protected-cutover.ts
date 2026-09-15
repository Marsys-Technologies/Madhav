/** Execute the one-shot protected owner/migration transition under one DB lease. */
import { attestDataPlaneMigrations } from './data-plane-migration-attestation'
import { runDataPlaneOwnershipPreflight } from './data-plane-ownership-preflight'
import { readDataPlaneOwnershipStatus } from './data-plane-ownership-status'
import { withDataPlaneCutoverLease } from './data-plane-cutover-preflight'

function required(name: string): string {
  const value = process.env[name]?.trim()
  if (!value) throw new Error(`${name} is required for the protected data-plane cutover.`)
  return value
}

export async function executeProtectedDataPlaneCutover(): Promise<void> {
  const adminUrl = required('DATA_PLANE_ADMIN_DATABASE_URL')
  const migratorUrl = required('DATA_PLANE_MIGRATOR_DATABASE_URL')
  await withDataPlaneCutoverLease(async () => {
    await runDataPlaneOwnershipPreflight(adminUrl)
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
