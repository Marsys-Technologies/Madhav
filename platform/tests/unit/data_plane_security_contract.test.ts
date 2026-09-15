import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'
import { assertGeneralRunnerMayApply } from '../../scripts/migrate'
import { assertSecretIsolation, BUILDER_SERVICE_ACCOUNT } from '../../scripts/data-plane-secret-isolation-preflight'
import { stripTransactionWrapper } from '../../scripts/data-plane-migration-attestation'

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
})

describe('DP-SD-018 lifecycle SQL contract', () => {
  for (const file of ['1035_data_plane_l1_producer_history.sql', '1036_data_plane_l2_producer_generations.sql']) {
    const sql = readFileSync(resolve(__dirname, '../../supabase/migrations', file), 'utf8')
    it(`${file} pins definer search paths and direct actor validation`, () => {
      expect(sql).toContain('SECURITY DEFINER')
      expect(sql).toContain('SET search_path = pg_catalog, public, pg_temp')
      expect(sql).toMatch(/session_user <> 'data_plane_builder'/)
      expect(sql).toMatch(/session_user <> 'data_plane_migrator'/)
      expect(sql).not.toMatch(/GRANT EXECUTE[\s\S]{0,200}TO role_orchestrator/)
    })
  }
})

describe('DP-SD-018 deployment ordering', () => {
  const workflow = readFileSync(resolve(__dirname, '../../../.github/workflows/deploy.yml'), 'utf8')
  it('gates IAM before DBA/migrator use and routes the build job to the dedicated credential', () => {
    expect(workflow.indexOf('Verify data-plane secret and runtime isolation')).toBeLessThan(workflow.indexOf('One-shot protected data-plane DBA preflight'))
    expect(workflow.indexOf('One-shot protected data-plane DBA preflight')).toBeLessThan(workflow.indexOf('Attest protected data-plane migrations as deployment-only migrator'))
    expect(workflow.indexOf('Attest protected data-plane migrations as deployment-only migrator')).toBeLessThan(workflow.indexOf('Run general database migrations'))
    expect(workflow).toContain('--service-account=data-plane-builder-runtime@madhav-astrology.iam.gserviceaccount.com')
    expect(workflow).toContain('--update-secrets=DATABASE_URL=data-plane-builder-db-url:latest')
  })
})
