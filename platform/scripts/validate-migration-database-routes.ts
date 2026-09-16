/** Fail-closed validation for the two production migration connection routes. */

type RouteEnvironment = Record<string, string | undefined>

type RouteSpec = {
  name: 'PROD_DATABASE_URL' | 'PURNA_INQUIRY_ADMIN_DATABASE_URL'
  port: '5432' | '5433'
  username: 'amjis_app' | 'purna_inquiry_bootstrap'
}

const ROUTES: readonly RouteSpec[] = [
  { name: 'PROD_DATABASE_URL', port: '5432', username: 'amjis_app' },
  { name: 'PURNA_INQUIRY_ADMIN_DATABASE_URL', port: '5433', username: 'purna_inquiry_bootstrap' },
]

// pg-connection-string lets these query keys override URL authority fields.
// Reject the wider libpq routing/principal vocabulary too, so future parser
// support cannot silently bypass the checked localhost path.
const FORBIDDEN_QUERY_KEYS = new Set([
  'database',
  'dbname',
  'host',
  'hostaddr',
  'password',
  'port',
  'service',
  'user',
  'username',
])

export function validateMigrationDatabaseRoutes(environment: RouteEnvironment = process.env): void {
  const parsed = new Map<RouteSpec['name'], URL>()

  for (const spec of ROUTES) {
    const value = environment[spec.name]
    if (!value) throw new Error(`${spec.name} is required.`)

    let route: URL
    try {
      route = new URL(value)
    } catch {
      throw new Error(`${spec.name} must be a valid PostgreSQL URL.`)
    }

    const hasForbiddenQueryOverride = [...route.searchParams.keys()]
      .some((key) => FORBIDDEN_QUERY_KEYS.has(key.toLowerCase()))
    if (!['postgres:', 'postgresql:'].includes(route.protocol)
      || route.hostname !== '127.0.0.1'
      || route.port !== spec.port
      || decodeURIComponent(route.username) !== spec.username
      || decodeURIComponent(route.pathname) !== '/amjis'
      || hasForbiddenQueryOverride
      || route.hash !== '') {
      throw new Error(
        `${spec.name} must use the approved principal and local proxy route for the amjis database.`,
      )
    }
    parsed.set(spec.name, route)
  }

  if (parsed.get('PROD_DATABASE_URL')?.pathname
    !== parsed.get('PURNA_INQUIRY_ADMIN_DATABASE_URL')?.pathname) {
    throw new Error('Migration credentials must target the same database through their separate proxy listeners.')
  }
}

if (require.main === module) {
  try {
    validateMigrationDatabaseRoutes()
    process.stdout.write('Migration database routes validated.\n')
  } catch (error) {
    console.error(error instanceof Error ? error.message : 'Migration database route validation failed.')
    process.exitCode = 1
  }
}
