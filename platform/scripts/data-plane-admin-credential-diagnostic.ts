/** Read-only, non-secret diagnostic for the protected administrator connector. */
import { Pool } from 'pg'
import { inspectDataPlaneAdminCredential, validationAdminProxyConfig } from './data-plane-cutover-preflight'

function required(name: string): string {
  const value = process.env[name]?.trim()
  if (!value) throw new Error(`${name} is required for the data-plane credential diagnostic.`)
  return value
}

async function main(): Promise<void> {
  const databaseUrl = required('DATA_PLANE_ADMIN_DATABASE_URL')
  const proxyPort = required('DATA_PLANE_RESTORE_VALIDATION_PROXY_PORT')
  const diagnostic = inspectDataPlaneAdminCredential(databaseUrl, { proxyPort })
  console.log(JSON.stringify({
    kind: 'data_plane_admin_credential_component_preflight',
    parseable: diagnostic.parseable,
    safe_to_route: diagnostic.safeToRoute,
    invalid_components: diagnostic.invalidComponents,
  }))
  if (!diagnostic.safeToRoute) process.exitCode = 1
  if (!diagnostic.safeToRoute) return

  const pool = new Pool(validationAdminProxyConfig(databaseUrl, { proxyPort }))
  try {
    await pool.query('SELECT 1 AS isolated_proxy_authenticated')
    console.log(JSON.stringify({ kind: 'data_plane_admin_isolated_proxy_authentication', authenticated: true }))
  } catch {
    console.log(JSON.stringify({ kind: 'data_plane_admin_isolated_proxy_authentication', authenticated: false }))
    process.exitCode = 1
  } finally {
    await pool.end()
  }
}

void main().catch(() => {
  console.log(JSON.stringify({ kind: 'data_plane_admin_credential_component_preflight', fatal: true }))
  process.exitCode = 1
})
