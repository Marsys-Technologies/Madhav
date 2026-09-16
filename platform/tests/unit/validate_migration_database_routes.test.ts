import { describe, expect, it } from 'vitest'
import { validateMigrationDatabaseRoutes } from '../../scripts/validate-migration-database-routes'

const POSTGRES_SCHEME = 'postgresql:'
const VALID = {
  PROD_DATABASE_URL: `${POSTGRES_SCHEME}//amjis_app:synthetic@127.0.0.1:5432/amjis?keepalives=1`,
  PURNA_INQUIRY_ADMIN_DATABASE_URL:
    `${POSTGRES_SCHEME}//purna_inquiry_bootstrap:synthetic@127.0.0.1:5433/amjis`,
}

describe('validateMigrationDatabaseRoutes', () => {
  it('accepts the two approved localhost routes and benign connection tuning', () => {
    expect(() => validateMigrationDatabaseRoutes(VALID)).not.toThrow()
  })

  it('allows routine marked-state delivery to validate PROD with the admin secret absent', () => {
    expect(() => validateMigrationDatabaseRoutes({
      PROD_DATABASE_URL: VALID.PROD_DATABASE_URL,
    }, ['prod'])).not.toThrow()
  })

  it('fails closed when a bootstrap or cleanup state lacks its one-shot admin route', () => {
    expect(() => validateMigrationDatabaseRoutes({}, ['purna-admin']))
      .toThrow('PURNA_INQUIRY_ADMIN_DATABASE_URL is required.')
  })

  it('fails closed when a bootstrap or cleanup state misroutes its one-shot admin route', () => {
    expect(() => validateMigrationDatabaseRoutes({
      PURNA_INQUIRY_ADMIN_DATABASE_URL:
        VALID.PURNA_INQUIRY_ADMIN_DATABASE_URL.replace(':5433/', ':9999/'),
    }, ['purna-admin'])).toThrow('PURNA_INQUIRY_ADMIN_DATABASE_URL must use the approved principal')
  })

  it.each(['host', 'port', 'user', 'password'])(
    'rejects a PostgreSQL query override for %s',
    (key) => {
      expect(() => validateMigrationDatabaseRoutes({
        ...VALID,
        PROD_DATABASE_URL: `${VALID.PROD_DATABASE_URL}&${key}=override`,
      })).toThrow('PROD_DATABASE_URL must use the approved principal')
    },
  )

  it('rejects fragments and sanitizes invalid URL errors', () => {
    expect(() => validateMigrationDatabaseRoutes({
      ...VALID,
      PROD_DATABASE_URL: `${VALID.PROD_DATABASE_URL}#override`,
    })).toThrow('PROD_DATABASE_URL must use the approved principal')

    expect(() => validateMigrationDatabaseRoutes({
      ...VALID,
      PROD_DATABASE_URL: 'not a URL containing secret material',
    })).toThrow('PROD_DATABASE_URL must be a valid PostgreSQL URL.')
  })
})
