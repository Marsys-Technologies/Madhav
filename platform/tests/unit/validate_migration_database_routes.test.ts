import { describe, expect, it } from 'vitest'
import { validateMigrationDatabaseRoutes } from '../../scripts/validate-migration-database-routes'

const VALID = {
  PROD_DATABASE_URL: 'postgresql://amjis_app:prod@127.0.0.1:5432/amjis?keepalives=1',
  PURNA_INQUIRY_ADMIN_DATABASE_URL:
    'postgresql://purna_inquiry_bootstrap:bootstrap@127.0.0.1:5433/amjis',
}

describe('validateMigrationDatabaseRoutes', () => {
  it('accepts the two approved localhost routes and benign connection tuning', () => {
    expect(() => validateMigrationDatabaseRoutes(VALID)).not.toThrow()
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
