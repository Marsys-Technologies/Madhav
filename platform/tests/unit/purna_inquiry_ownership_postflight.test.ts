import { beforeEach, describe, expect, it, vi } from 'vitest'

const harness = vi.hoisted(() => ({
  queries: [] as string[],
  failOnAclRevoke: false,
  statusAclDependencies: 0,
  statusMarker: true,
  statusFunctions: 13,
  servingNormalized: true,
  ownerCanUsePublic: true,
}))

vi.mock('pg', () => ({
  Pool: class {
    async query(sql: string) {
      return this.execute(sql)
    }
    async connect() {
      return {
        query: async (sql: string) => this.execute(sql),
        release: () => undefined,
      }
    }
    private async execute(sql: string) {
      harness.queries.push(sql)
      if (harness.failOnAclRevoke && sql.includes('REVOKE SELECT ON TABLE public._migrations_applied')) {
        throw new Error('fixture ACL revoke failure')
      }
      if (sql.includes('SELECT session_user, current_user')) {
        return { rows: [{ session_user: 'purna_inquiry_bootstrap', current_user: 'purna_inquiry_bootstrap', provider_admin: true }] }
      }
      if (sql.includes('AS marker')) {
        return { rows: [{
          marker: harness.statusMarker,
          tables_total: 4,
          tables_owned: 4,
          functions_total: harness.statusFunctions,
          functions_owned: harness.statusFunctions,
          owner_normalized: true,
          owner_memberships: 0,
          owner_can_create_public: false,
          owner_can_use_public: harness.ownerCanUsePublic,
          serving_normalized: harness.servingNormalized,
          bootstrap_disabled: true,
          bootstrap_armed: false,
          bootstrap_memberships: 0,
          bootstrap_acl_dependencies: harness.statusAclDependencies,
        }] }
      }
      if (sql.includes('bootstrap_acl_dependencies')) {
        return { rows: [{
          owner_can_create: false,
          owner_can_use: true,
          serving_can_create: false,
          serving_can_use: true,
          bootstrap_disabled: true,
          bootstrap_memberships: 0,
          bootstrap_acl_dependencies: 0,
        }] }
      }
      return { rows: [] }
    }
    async end() { return undefined }
  },
}))

const { runPurnaInquiryOwnershipPostflight } = await import('../../scripts/purna-inquiry-ownership-postflight')
const { purnaOwnershipState } = await import('../../scripts/purna-inquiry-ownership-status')

describe('Pūrṇa ownership postflight recovery path', () => {
  beforeEach(() => {
    harness.queries.length = 0
    harness.failOnAclRevoke = false
    harness.statusAclDependencies = 0
    harness.statusMarker = true
    harness.statusFunctions = 13
    harness.servingNormalized = true
    harness.ownerCanUsePublic = true
  })

  it('re-establishes only the app role, revokes ACL residue, and removes membership before commit', async () => {
    await expect(runPurnaInquiryOwnershipPostflight('postgresql://fixture')).resolves.toBeUndefined()
    const joined = harness.queries.join('\n')
    const grantIndex = joined.indexOf('GRANT amjis_app TO purna_inquiry_bootstrap')
    const aclIndex = joined.indexOf('REVOKE SELECT ON TABLE public._migrations_applied')
    const membershipIndex = joined.indexOf("REVOKE %I FROM purna_inquiry_bootstrap', parent_name")
    const commitIndex = joined.indexOf('COMMIT')

    expect(grantIndex).toBeGreaterThan(-1)
    expect(aclIndex).toBeGreaterThan(grantIndex)
    expect(membershipIndex).toBeGreaterThan(aclIndex)
    expect(commitIndex).toBeGreaterThan(membershipIndex)
  })

  it('rolls the transaction back when ACL cleanup fails', async () => {
    harness.failOnAclRevoke = true
    await expect(runPurnaInquiryOwnershipPostflight('postgresql://fixture'))
      .rejects.toThrow('fixture ACL revoke failure')
    expect(harness.queries).toContain('ROLLBACK')
    expect(harness.queries).not.toContain('COMMIT')
  })

  it('requires explicit rearm when a disabled memberless bootstrap retains ACL residue', async () => {
    harness.statusAclDependencies = 2
    await expect(purnaOwnershipState('postgresql://fixture')).resolves.toBe('rearm_required')
    harness.statusAclDependencies = 0
    await expect(purnaOwnershipState('postgresql://fixture')).resolves.toBe('marked')
  })

  it('rejects marked state when the serving role cannot resolve public functions', async () => {
    harness.servingNormalized = false
    await expect(purnaOwnershipState('postgresql://fixture')).resolves.toBe('invalid')
  })

  it('rejects marked state when the protected definer owner cannot resolve public objects', async () => {
    harness.ownerCanUsePublic = false
    await expect(purnaOwnershipState('postgresql://fixture')).resolves.toBe('invalid')
  })

  it('requires explicit rearm to apply the successor migration after the 1039 seal', async () => {
    harness.statusMarker = false
    harness.statusFunctions = 12
    await expect(purnaOwnershipState('postgresql://fixture')).resolves.toBe('rearm_required')
  })
})
