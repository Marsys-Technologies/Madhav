import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'
import { assertGeneralRunnerMayApply } from '../../scripts/migrate'
import { assertEffectiveIsolation, assertSecretIsolation, assertSurfaceSecretGrant, BUILDER_SERVICE_ACCOUNT, extractRunIdentityAndSecrets } from '../../scripts/data-plane-secret-isolation-preflight'
import { stripTransactionWrapper } from '../../scripts/data-plane-migration-attestation'
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
    expect(() => assertEffectiveIsolation([], policy, [{ kind: 'revision', name: 'amjis-web', definition: { secret: 'data-plane-builder-db-url' } }]))
      .toThrow(/outside the one named build job/)
    expect(() => assertEffectiveIsolation([], policy, [{ kind: 'job', name: 'brahma-build-pipeline-job', definition: { secret: 'data-plane-builder-db-url', serviceAccount: BUILDER_SERVICE_ACCOUNT } }]))
      .not.toThrow()
  })
  it('extracts every revision secret and requires an explicit per-secret runtime grant', () => {
    const inventory = extractRunIdentityAndSecrets({ spec: { template: { spec: {
      serviceAccountName: 'web@example.iam.gserviceaccount.com',
      containers: [{ env: [{ valueFrom: { secretKeyRef: { name: 'alpha' } } }, { valueFrom: { secretKeyRef: { secret: 'beta' } } }] }],
    } } } })
    expect(inventory).toEqual({ serviceAccount: 'web@example.iam.gserviceaccount.com', secrets: ['alpha', 'beta'] })
    expect(() => assertSurfaceSecretGrant(inventory.serviceAccount, 'alpha', { bindings: [] })).toThrow(/explicit resource grant/)
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
  })
})

describe('DP-SD-018 deployment ordering', () => {
  const workflow = readFileSync(resolve(__dirname, '../../../.github/workflows/deploy.yml'), 'utf8')
  it('gates IAM before DBA/migrator use and routes the build job to the dedicated credential', () => {
    expect(workflow.indexOf('Verify data-plane secret and runtime isolation')).toBeLessThan(workflow.indexOf('One-shot protected data-plane DBA preflight'))
    expect(workflow.indexOf('One-shot protected data-plane DBA preflight')).toBeLessThan(workflow.indexOf('Attest protected data-plane migrations as deployment-only migrator'))
    expect(workflow.indexOf('Attest protected data-plane migrations as deployment-only migrator')).toBeLessThan(workflow.indexOf('Run general database migrations'))
    expect(workflow).toContain('--service-account=data-plane-builder-runtime@madhav-astrology.iam.gserviceaccount.com')
    expect(workflow).toContain('--update-secrets=DATABASE_URL=data-plane-builder-db-url:latest')
    expect(workflow).toContain('environment: data-plane-production-cutover')
    expect(workflow).toContain('DATA_PLANE_BACKUP_RESTORE_ID')
    expect(workflow.indexOf('Re-attest protected data-plane semantic state')).toBeLessThan(workflow.indexOf('Run general database migrations'))
  })
})
