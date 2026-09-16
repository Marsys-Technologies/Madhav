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

export type MigrationDatabaseRoute = 'prod' | 'purna-admin'

export function validateMigrationDatabaseRoutes(
  environment: RouteEnvironment = process.env,
  routes: readonly MigrationDatabaseRoute[] = ['prod', 'purna-admin'],
): void {
  const selected = ROUTES.filter((spec) => routes.includes(
    spec.name === 'PROD_DATABASE_URL' ? 'prod' : 'purna-admin',
  ))
  if (selected.length !== routes.length || selected.length === 0) {
    throw new Error('A known migration database route is required.')
  }

  for (const spec of selected) {
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
  }
}

if (require.main === module) {
  try {
    const mode = process.argv[2]
    if (mode !== '--prod' && mode !== '--purna-admin') {
      throw new Error('Use --prod or --purna-admin to select one migration database route.')
    }
    validateMigrationDatabaseRoutes(process.env, [mode === '--prod' ? 'prod' : 'purna-admin'])
    process.stdout.write('Migration database routes validated.\n')
  } catch (error) {
    console.error(error instanceof Error ? error.message : 'Migration database route validation failed.')
    process.exitCode = 1
  }
}
