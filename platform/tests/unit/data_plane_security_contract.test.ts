import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'
import { assertGeneralRunnerMayApply } from '../../scripts/migrate'
import { assertEffectiveIsolation, assertSecretIsolation, assertSurfaceSecretGrant, BUILDER_SERVICE_ACCOUNT, extractRunIdentityAndSecrets, iamSearchScopes } from '../../scripts/data-plane-secret-isolation-preflight'
import { stripTransactionWrapper } from '../../scripts/data-plane-migration-attestation'
import { parseBackupRestoreReceipt } from '../../scripts/data-plane-cutover-preflight'
import { L1_ACTIVE_TABLES, L2_ACTIVE_TABLES } from '../../scripts/data-plane-ownership-preflight'

describe('DP-SD-018 protected migration routing', () => {
  it.each(['1035_data_plane_l1_producer_history.sql', '1036_data_plane_l2_producer_generations.sql'])(
    'blocks %s in the general application runner', (filename) => {
      expect(() => assertGeneralRunnerMayApply(filename)).toThrow(/general DATABASE_URL runner cannot create protected objects/)
    },
  )
  it('strips only the exact outer transaction wrapper', () => {
    expect(stripTransactionWrapper('\nBEGIN;\nSELECT 1;\nCOMMIT;\n')).toContain('SELECT 1;')
    expect(() => stripTransactionWrapper('SELECT 1')).toThrow(/wrapper/)
  })
})

describe('DP-SD-018 GCP credential isolation', () => {
  it('rejects the current project-wide secret accessor topology', () => {
    expect(() => assertSecretIsolation({ bindings: [{ role: 'roles/secretmanager.secretAccessor', members: ['serviceAccount:amjis-web-runtime@example'] }] }, {}, {}))
      .toThrow(/Project-wide Secret Manager accessor/)
  })
  it('accepts only the dedicated builder on the exact secret', () => {
    expect(() => assertSecretIsolation({ bindings: [{ role: 'roles/cloudsql.client', members: [`serviceAccount:${BUILDER_SERVICE_ACCOUNT}`] }] }, { bindings: [{ role: 'roles/secretmanager.secretAccessor', members: [`serviceAccount:${BUILDER_SERVICE_ACCOUNT}`] }] }, { disabled: false }))
      .not.toThrow()
    expect(() => assertSecretIsolation(
      { bindings: [{ role: 'roles/cloudsql.client', members: [`serviceAccount:${BUILDER_SERVICE_ACCOUNT}`] }] },
      { bindings: [
        { role: 'roles/secretmanager.secretAccessor', members: [`serviceAccount:${BUILDER_SERVICE_ACCOUNT}`] },
        { role: 'roles/secretmanager.secretAccessor', members: ['serviceAccount:rogue@example'], condition: { expression: 'true' } },
      ] }, { disabled: false },
    )).toThrow(/exactly/)
  })
  it('aggregates conditional project bindings and rejects inherited access', () => {
    expect(() => assertSecretIsolation({ bindings: [
      { role: 'roles/secretmanager.secretAccessor', members: [] },
      { role: 'roles/secretmanager.secretAccessor', members: ['serviceAccount:web@example'], condition: { expression: 'true' } },
    ] }, {}, {})).toThrow(/Project-wide/)
    process.env.DATA_PLANE_DEPLOY_PRINCIPAL = 'serviceAccount:github-actions@example'
    expect(() => assertEffectiveIsolation([
      { resource: '//cloudresourcemanager.googleapis.com/projects/example', policy: { bindings: [{ role: 'roles/secretmanager.secretAccessor', members: ['serviceAccount:web@example'] }] } },
    ], { bindings: [{ role: 'roles/iam.serviceAccountUser', members: ['serviceAccount:github-actions@example'] }] }, []))
      .toThrow(/Inherited/)
  })
  it('permits the builder secret only on the named build job', () => {
    process.env.DATA_PLANE_DEPLOY_PRINCIPAL = 'serviceAccount:github-actions@example'
    const policy = { bindings: [{ role: 'roles/iam.serviceAccountUser', members: ['serviceAccount:github-actions@example'] }] }
    expect(() => assertEffectiveIsolation([], policy, [{ kind: 'revision', name: 'amjis-web', definition: { serviceAccount: 'web@example', secretKeyRef: { name: 'data-plane-builder-db-url' } } }]))
      .toThrow(/outside the one named build job/)
    expect(() => assertEffectiveIsolation([], policy, [{ kind: 'job', name: 'brahma-build-pipeline-job', definition: { secretKeyRef: { name: 'data-plane-builder-db-url' }, serviceAccount: BUILDER_SERVICE_ACCOUNT } }]))
      .not.toThrow()
  })
  it('requires exactly one deployer impersonation grant and searches project ancestry', () => {
    process.env.DATA_PLANE_DEPLOY_PRINCIPAL = 'serviceAccount:github-actions@example'
    const surface = [{ kind: 'job' as const, name: 'brahma-build-pipeline-job', definition: { serviceAccount: BUILDER_SERVICE_ACCOUNT, secretKeyRef: { name: 'data-plane-builder-db-url' } } }]
    expect(() => assertEffectiveIsolation([], { bindings: [] }, surface)).toThrow(/impersonation policy/)
    expect(() => assertEffectiveIsolation([], { bindings: [
      { role: 'roles/iam.serviceAccountUser', members: ['serviceAccount:github-actions@example'] },
      { role: 'roles/iam.serviceAccountTokenCreator', members: ['serviceAccount:conditional@example'], condition: { expression: 'true' } },
    ] }, surface)).toThrow(/impersonation policy/)
    expect(iamSearchScopes([
      { type: 'project', id: 'madhav-astrology' },
      { type: 'folder', id: '123' },
      { type: 'organization', id: '456' },
    ])).toEqual([`projects/${process.env.GCP_PROJECT ?? 'madhav-astrology'}`, 'projects/madhav-astrology', 'folders/123', 'organizations/456'].filter((scope, index, all) => all.indexOf(scope) === index))
  })
  it('rejects builder identity or deployment-only secrets on every other surface', () => {
    process.env.DATA_PLANE_DEPLOY_PRINCIPAL = 'serviceAccount:github-actions@example'
    const policy = { bindings: [{ role: 'roles/iam.serviceAccountUser', members: ['serviceAccount:github-actions@example'] }] }
    expect(() => assertEffectiveIsolation([], policy, [{ kind: 'revision', name: 'web', definition: { serviceAccount: BUILDER_SERVICE_ACCOUNT } }]))
      .toThrow(/Builder identity is used outside/)
    expect(() => assertEffectiveIsolation([], policy, [{ kind: 'revision', name: 'web', definition: { serviceAccount: 'web@example', secretKeyRef: { name: 'data-plane-admin-db-url' } } }]))
      .toThrow(/DBA\/migrator credential/)
  })
  it('extracts every revision secret and requires an explicit per-secret runtime grant', () => {
    const inventory = extractRunIdentityAndSecrets({ spec: { template: { spec: {
      serviceAccountName: 'web@example.iam.gserviceaccount.com',
      containers: [{ env: [{ valueFrom: { secretKeyRef: { name: 'alpha' } } }, { valueFrom: { secretKeyRef: { secret: 'beta' } } }] }],
    } } } })
    expect(inventory).toEqual({ serviceAccount: 'web@example.iam.gserviceaccount.com', secrets: ['alpha', 'beta'] })
    expect(() => assertSurfaceSecretGrant(inventory.serviceAccount, 'alpha', { bindings: [] })).toThrow(/explicit resource grant/)
    expect(extractRunIdentityAndSecrets({ spec: { template: { spec: {
      serviceAccountName: 'web@example.iam.gserviceaccount.com',
      volumes: [{ secret: { secretName: 'volume-secret' } }],
    } } } }).secrets).toEqual(['volume-secret'])
    expect(() => assertSurfaceSecretGrant(inventory.serviceAccount, 'alpha', { bindings: [{
      role: 'roles/secretmanager.secretAccessor', members: ['serviceAccount:web@example.iam.gserviceaccount.com'],
      condition: { expression: 'true' },
    }] })).toThrow(/explicit resource grant/)
  })
  it('rejects inherited builder impersonation and builder identity on a service template', () => {
    process.env.DATA_PLANE_DEPLOY_PRINCIPAL = 'serviceAccount:github-actions@example'
    const policy = { bindings: [{ role: 'roles/iam.serviceAccountUser', members: ['serviceAccount:github-actions@example'] }] }
    expect(() => assertEffectiveIsolation([{ resource: '//cloudresourcemanager.googleapis.com/projects/example', policy: {
      bindings: [{ role: 'roles/iam.serviceAccountTokenCreator', members: ['serviceAccount:rogue@example'], condition: { expression: 'true' } }],
    } }], policy, [])).toThrow(/aggregate builder service-account impersonation/)
    expect(() => assertEffectiveIsolation([], policy, [{ kind: 'service', name: 'web', definition: {
      serviceAccount: BUILDER_SERVICE_ACCOUNT,
    } }])).toThrow(/Builder identity is used outside/)
  })
})

describe('DP-SD-018 lifecycle SQL contract', () => {
  for (const file of ['1035_data_plane_l1_producer_history.sql', '1036_data_plane_l2_producer_generations.sql']) {
    const sql = readFileSync(resolve(__dirname, '../../supabase/migrations', file), 'utf8')
    it(`${file} pins definer search paths and direct actor validation`, () => {
      expect(sql).toContain('SECURITY DEFINER')
      expect(sql).toContain('SET search_path = pg_catalog, public, pg_temp')
      expect(sql).toMatch(/session_user <> 'data_plane_builder'/)
      expect(sql).toMatch(/session_user <> 'data_plane_migrator'/)
      expect(sql).not.toMatch(/IF v_asset IS NULL OR v_asset = '' THEN\s+RETURN NEW/)
      expect(sql).toMatch(/mutation_guard BEFORE INSERT OR UPDATE OR DELETE/)
      expect(sql).toMatch(/protected capture contains/)
      expect(sql).toMatch(/v_old jsonb/)
      expect(sql).toMatch(/v_new jsonb/)
      expect(sql).toMatch(/cannot transfer natural-key column/)
      expect(sql).toMatch(/data_plane_view_attestations/)
      expect(sql).toMatch(/data_plane_trigger_attestations/)
      expect(sql).toMatch(/pg_get_viewdef/)
      expect(sql).toMatch(/pg_get_triggerdef/)
      expect(sql).not.toMatch(/GRANT EXECUTE[\s\S]{0,200}TO role_orchestrator/)
    })
  }
  it('installs the admission guard across the exhaustive protected-table inventory', () => {
    const l1 = readFileSync(resolve(__dirname, '../../supabase/migrations/1035_data_plane_l1_producer_history.sql'), 'utf8')
    const l2 = readFileSync(resolve(__dirname, '../../supabase/migrations/1036_data_plane_l2_producer_generations.sql'), 'utf8')
    const l1Installed = [...l1.matchAll(/SELECT public\.l1_data_plane_install_active_guards\('([^']+)'\)/g)].map((match) => match[1])
    const l2Installed = [...l2.matchAll(/SELECT public\.l2_data_plane_install_capture_trigger\('([^']+)'/g)].map((match) => match[1])
    expect(new Set(l1Installed)).toEqual(new Set(L1_ACTIVE_TABLES))
    expect(new Set(l2Installed)).toEqual(new Set(L2_ACTIVE_TABLES))
    expect(l2).toContain('l2_data_plane_input_bind_receipts')
    expect(l2).toContain('L2 exact-input bind receipt is missing, forged, or mismatched')
    expect(l1).toMatch(/fact_category[\s\S]*owning_asset_id = v_asset/)
    expect(l2).toContain('producer_asset_id')
    expect(l2).toMatch(/l2_data_plane_msr_delete_receipt[\s\S]*asset_id text NOT NULL/)
  })
  it('normalizes the complete pre-existing table, sequence, and schema ACL surface', () => {
    const preflight = readFileSync(resolve(__dirname, '../../scripts/data-plane-ownership-preflight.ts'), 'utf8')
    expect(preflight).toContain('CROSS JOIN LATERAL aclexplode')
    expect(preflight).toContain("revokeAllRelationGrantees(client, 'TABLE'")
    expect(preflight).toContain("revokeAllRelationGrantees(client, 'SEQUENCE'")
    expect(preflight).toContain('revokeAllPublicSchemaGrantees(client)')
    expect(preflight).toContain('revokeAllDefaultPrivilegeGrantees(client')
    const transfer = preflight.slice(preflight.indexOf('async function transferTables'), preflight.indexOf('export async function runDataPlaneOwnershipPreflight'))
    expect(transfer).not.toMatch(/GRANT SELECT, INSERT, UPDATE, DELETE/)
  })
  it('publishes builder DML only after protected guards are installed', () => {
    for (const file of ['1035_data_plane_l1_producer_history.sql', '1036_data_plane_l2_producer_generations.sql']) {
      const sql = readFileSync(resolve(__dirname, '../../supabase/migrations', file), 'utf8')
      const guard = Math.max(sql.lastIndexOf('install_active_guards'), sql.lastIndexOf('install_capture_trigger'))
      const grant = sql.lastIndexOf('GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE')
      expect(guard).toBeGreaterThan(0)
      expect(grant).toBeGreaterThan(guard)
      expect(sql.indexOf('COMMIT;', grant)).toBeGreaterThan(grant)
    }
  })
})

describe('DP-SD-018 deployment ordering', () => {
  const workflow = readFileSync(resolve(__dirname, '../../../.github/workflows/deploy.yml'), 'utf8')
  it('gates IAM before DBA/migrator use and routes the build job to the dedicated credential', () => {
    expect(workflow.indexOf('Verify data-plane secret and runtime isolation')).toBeLessThan(workflow.indexOf('Execute protected cutover under backup'))
    expect(workflow.indexOf('Execute protected cutover under backup')).toBeLessThan(workflow.indexOf('Run general database migrations'))
    expect(workflow).toContain('--service-account=data-plane-builder-runtime@madhav-astrology.iam.gserviceaccount.com')
    expect(workflow).toContain('--update-secrets=DATABASE_URL=data-plane-builder-db-url:latest')
    expect(workflow).toContain('environment: data-plane-production-cutover')
    expect(workflow).toContain('DATA_PLANE_BACKUP_RESTORE_ID')
    expect(workflow).toContain('group: data-plane-production-cutover')
    expect(workflow).toMatch(/deploy-pipeline-job:[\s\S]*?needs: \[changes, migrate\]/)
    expect(workflow.indexOf('Re-attest protected data-plane semantic state')).toBeLessThan(workflow.indexOf('Run general database migrations'))
  })
  it('requires exact backup and successful-restore identifiers as one receipt', () => {
    const preflight = readFileSync(resolve(__dirname, '../../scripts/data-plane-cutover-preflight.ts'), 'utf8')
    expect(parseBackupRestoreReceipt('123:restore-op-456')).toEqual({ backupId: '123', restoreOperationId: 'restore-op-456' })
    expect(() => parseBackupRestoreReceipt('123')).toThrow(/backup-id:restore-operation-id/)
    expect(preflight).toContain("restore.targetId !== 'amjis-postgres'")
    expect(preflight).toMatch(/LOCK TABLE public\.build_runs, public\.build_run_assets[\s\S]*SHARE ROW EXCLUSIVE MODE NOWAIT/)
  })
})
