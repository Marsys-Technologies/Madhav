import { beforeEach, describe, expect, it, vi } from 'vitest'

const harness = vi.hoisted(() => ({
  queries: [] as string[],
  canCreate: false,
  directActor: true,
}))

vi.mock('../../scripts/data-plane-protected-cutover', () => ({
  migratorProxyConfig: vi.fn(() => ({
    host: '127.0.0.1', port: 5432, user: 'data_plane_migrator',
    password: process.env.TEST_DATABASE_PASSWORD ?? '', database: 'amjis', max: 1,
  })),
}))

vi.mock('pg', () => ({
  Pool: class {
    async connect() {
      return {
        query: async (sql: string) => {
          harness.queries.push(sql)
          if (sql.includes('SELECT session_user, current_user')) {
            return { rows: [{
              session_user: harness.directActor ? 'data_plane_migrator' : 'amjis_app',
              current_user: harness.directActor ? 'data_plane_migrator' : 'amjis_app',
              schema_owner_member: harness.directActor,
            }] }
          }
          if (sql.includes('AS normalized')) return { rows: [{ normalized: true }] }
          if (sql.includes('GRANT USAGE, CREATE ON SCHEMA public')) harness.canCreate = true
          if (sql.includes('REVOKE CREATE ON SCHEMA public')) harness.canCreate = false
          if (sql.includes('AS can_create')) return { rows: [{ can_create: harness.canCreate }] }
          return { rows: [] }
        },
        release: () => undefined,
      }
    }
    async end() { return undefined }
  },
}))

const { setPurnaInquirySchemaCapability } = await import('../../scripts/purna-inquiry-schema-capability')

describe('Pūrṇa temporary schema capability', () => {
  beforeEach(() => {
    harness.queries.length = 0
    harness.canCreate = false
    harness.directActor = true
  })

  it('grants through the protected schema owner and attests before commit', async () => {
    await expect(setPurnaInquirySchemaCapability('grant', 'postgresql://fixture')).resolves.toBeUndefined()
    const joined = harness.queries.join('\n')
    expect(joined).toContain('SET LOCAL ROLE data_plane_schema_owner')
    expect(joined).toContain('GRANT USAGE, CREATE ON SCHEMA public TO purna_inquiry_owner')
    expect(joined.indexOf('AS can_create')).toBeLessThan(joined.indexOf('COMMIT'))
    expect(harness.canCreate).toBe(true)
  })

  it('revokes CREATE idempotently through the same protected owner', async () => {
    harness.canCreate = true
    await expect(setPurnaInquirySchemaCapability('revoke', 'postgresql://fixture')).resolves.toBeUndefined()
    expect(harness.queries.join('\n')).toContain('REVOKE CREATE ON SCHEMA public FROM purna_inquiry_owner')
    expect(harness.canCreate).toBe(false)
  })

  it('fails closed unless the direct migrator owns the schema-owner edge', async () => {
    harness.directActor = false
    await expect(setPurnaInquirySchemaCapability('grant', 'postgresql://fixture'))
      .rejects.toThrow('direct protected data_plane_migrator route')
    expect(harness.queries).not.toContain('COMMIT')
  })
})
