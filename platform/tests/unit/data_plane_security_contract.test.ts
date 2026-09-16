import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { runInNewContext } from 'node:vm'
import { load } from 'js-yaml'
import { describe, expect, it } from 'vitest'
import { assertGeneralRunnerMayApply } from '../../scripts/migrate'
import { assertEffectiveIsolation, assertNoLiteralCredentials, assertSecretIsolation, assertSurfaceSecretGrant, BUILDER_SERVICE_ACCOUNT, cloudRunLocation, extractRunIdentityAndSecrets, iamSearchScopes, requiresRuntimeSecretGrant, roleDescribeArgs } from '../../scripts/data-plane-secret-isolation-preflight'
import { stripTransactionWrapper } from '../../scripts/data-plane-migration-attestation'
import { assertBackupReceiptBinding, assertGitHubAutomatedCutoverEvidence, assertRestoreAuditBinding, assertValidationConnectorBinding, DATA_PLANE_CUTOVER_AUTHORITY, DATA_PLANE_CUTOVER_EXECUTION_MODE, parseBackupRestoreReceipt } from '../../scripts/data-plane-cutover-preflight'
import { L1_ACTIVE_TABLES, L2_ACTIVE_TABLES } from '../../scripts/data-plane-ownership-preflight'

type WorkflowStep = { name?: string; if?: string; env?: Record<string, string>; run?: string }
type WorkflowJob = {
  needs?: string[]
  if?: string
  environment?: string
  concurrency?: { group?: string; 'cancel-in-progress'?: boolean }
  outputs?: Record<string, string>
  steps?: WorkflowStep[]
}

const workflow = readFileSync(resolve(__dirname, '../../../.github/workflows/deploy.yml'), 'utf8')
const workflowJobs = (load(workflow) as { jobs: Record<string, WorkflowJob> }).jobs
const iamTerraform = readFileSync(resolve(__dirname, '../../../infra/iam/main.tf'), 'utf8')

function evaluateWorkflowCondition(expression: string, values: Record<string, string>): boolean {
  let executable = expression.replace(/always\(\)/g, 'true')
  executable = executable.replace(/\b(?:github|needs)\.[A-Za-z0-9_.-]+\b/g, (token) => JSON.stringify(values[token] ?? ''))
  if (/\b(?:github|needs)\./.test(executable) || !/^[\s()&|!='".A-Za-z0-9_-]+$/.test(executable)) {
    throw new Error(`Unsupported workflow expression: ${expression}`)
  }
  return Boolean(runInNewContext(executable, Object.create(null)))
}

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
  it('distinguishes the declared human control-plane owner from runtime-wide access', () => {
    const admin = 'user:admin@example.com'
    const ownerPermissions = {
      'roles/owner': ['secretmanager.versions.access', 'iam.serviceAccounts.getAccessToken'],
      'roles/run.serviceAgent': ['iam.serviceAccounts.getAccessToken'],
    }
    const serviceAgent = 'serviceAccount:service-123@serverless-robot-prod.iam.gserviceaccount.com'
    const ownerPolicy = { bindings: [
      { role: 'roles/owner', members: [admin] },
      { role: 'roles/run.serviceAgent', members: [serviceAgent] },
    ] }
    const builderPolicy = { bindings: [{
      role: 'roles/iam.serviceAccountUser', members: ['serviceAccount:github-actions@example'],
    }] }
    const builderSurface = [{ kind: 'job' as const, name: 'brahma-build-pipeline-job', definition: {
      serviceAccount: BUILDER_SERVICE_ACCOUNT,
      secretKeyRef: { name: 'data-plane-builder-db-url', key: 'latest' },
    } }]
    const builderSecretPolicy = { bindings: [{
      role: 'roles/secretmanager.secretAccessor', members: [`serviceAccount:${BUILDER_SERVICE_ACCOUNT}`],
    }] }
    const builderProjectPolicy = { bindings: [
      { role: 'roles/cloudsql.client', members: [`serviceAccount:${BUILDER_SERVICE_ACCOUNT}`] },
      ...ownerPolicy.bindings,
    ] }
    expect(() => assertSecretIsolation(
      builderProjectPolicy, builderSecretPolicy, {}, undefined, ownerPermissions, admin,
    )).not.toThrow()
    expect(() => assertSecretIsolation(
      builderProjectPolicy, builderSecretPolicy, {}, undefined, ownerPermissions, 'user:other@example.com',
    )).toThrow(/undeclared or runtime principal/)
    process.env.DATA_PLANE_DEPLOY_PRINCIPAL = 'serviceAccount:github-actions@example'
    expect(() => assertEffectiveIsolation(
      [{ resource: 'projects/madhav-astrology', policy: ownerPolicy }], builderPolicy,
      builderSurface, ownerPermissions, admin, '123',
    )).not.toThrow()
    expect(() => assertEffectiveIsolation(
      [{ resource: 'folders/123', policy: ownerPolicy }], builderPolicy,
      builderSurface, ownerPermissions, admin, '123',
    )).toThrow(/Inherited or aggregate/)
    expect(() => assertEffectiveIsolation(
      [{ resource: 'projects/madhav-astrology', policy: { bindings: [{
        role: 'roles/run.serviceAgent', members: ['serviceAccount:rogue@example.com'],
      }] } }], builderPolicy, builderSurface, ownerPermissions, admin, '123',
    )).toThrow(/rogue@example.com/)
  })
  it('permits the builder secret only on the named build job', () => {
    process.env.DATA_PLANE_DEPLOY_PRINCIPAL = 'serviceAccount:github-actions@example'
    const policy = { bindings: [{ role: 'roles/iam.serviceAccountUser', members: ['serviceAccount:github-actions@example'] }] }
    expect(() => assertEffectiveIsolation([], policy, [{ kind: 'revision', name: 'amjis-web', definition: { serviceAccount: 'web@example', secretKeyRef: { name: 'data-plane-builder-db-url' } } }]))
      .toThrow(/outside the one named build job/)
    expect(() => assertEffectiveIsolation([], policy, [{ kind: 'job', name: 'brahma-build-pipeline-job', definition: { secretKeyRef: { name: 'data-plane-builder-db-url' }, serviceAccount: BUILDER_SERVICE_ACCOUNT } }]))
      .not.toThrow()
    expect(() => assertEffectiveIsolation([], policy, [{ kind: 'job', name: 'brahma-build-pipeline-job', definition: {
      database: { secretKeyRef: { name: 'data-plane-builder-db-url' } },
      unrelated: { secretKeyRef: { name: 'unrelated-secret' } },
      serviceAccount: BUILDER_SERVICE_ACCOUNT,
    } }])).toThrow(/lacks the exact builder/)
    const legacy = [{ kind: 'job' as const, name: 'brahma-build-pipeline-job', definition: {
      secretKeyRef: { name: 'amjis-pipeline-db-url' },
      serviceAccount: 'amjis-web-runtime@madhav-astrology.iam.gserviceaccount.com',
    } }]
    expect(() => assertEffectiveIsolation([], policy, legacy)).toThrow(/lacks the exact builder/)
    expect(() => assertEffectiveIsolation([], policy, legacy, {}, '', '', 'pre_transition')).not.toThrow()
    expect(() => assertEffectiveIsolation([], policy, [{
      ...legacy[0], definition: { ...legacy[0].definition, secretKeyRef: { name: 'rogue-db-url' } },
    }], {}, '', '', 'pre_transition')).toThrow(/neither the exact legacy binding/)
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
    ])).toEqual([`projects/${process.env.GOOGLE_CLOUD_PROJECT ?? 'madhav-astrology'}`, 'projects/madhav-astrology', 'folders/123', 'organizations/456'].filter((scope, index, all) => all.indexOf(scope) === index))
    const preflight = readFileSync(resolve(__dirname, '../../scripts/data-plane-secret-isolation-preflight.ts'), 'utf8')
    expect(preflight).toContain('GCLOUD_JSON_MAX_BUFFER')
    expect(preflight).toContain('maxBuffer: GCLOUD_JSON_MAX_BUFFER')
    expect(preflight).not.toContain("['run', 'revisions', 'describe'")
    for (const resource of [
      'github_actions_acts_as_web_runtime',
      'github_actions_acts_as_sidecar_runtime',
      'github_actions_acts_as_mcp_runtime',
      'firebase_admin_self_token_creator',
    ]) expect(iamTerraform).toContain(`resource "google_service_account_iam_member" "${resource}"`)
    expect(iamTerraform).toContain('resource "google_project_iam_member" "github_actions_security_reviewer"')
    expect(iamTerraform).toContain('role    = "roles/iam.securityReviewer"')
    expect(iamTerraform).toContain('resource "google_service_account_iam_member" "protected_main_impersonates_github_actions"')
    expect(iamTerraform).toContain('resource "google_service_account_iam_member" "data_plane_cutover_environment_impersonates_github_actions"')
    expect(iamTerraform).toContain('repo:Marsys-Technologies/Madhav:ref:refs/heads/main')
    expect(iamTerraform).toContain('repo:Marsys-Technologies/Madhav:environment:data-plane-production-cutover')
    expect(iamTerraform).not.toContain('/attribute.repository/Marsys-Technologies/Madhav')
  })
  it('requires secret grants for runnable surfaces but not explicitly retired revisions', () => {
    expect(requiresRuntimeSecretGrant({ kind: 'service', name: 'current', definition: {} })).toBe(true)
    expect(requiresRuntimeSecretGrant({ kind: 'revision', name: 'active', definition: {
      status: { conditions: [{ type: 'Active', status: 'True' }] },
    } })).toBe(true)
    expect(requiresRuntimeSecretGrant({ kind: 'revision', name: 'unknown', definition: {} })).toBe(true)
    expect(requiresRuntimeSecretGrant({ kind: 'revision', name: 'retired', definition: {
      status: { conditions: [{ type: 'Active', status: 'False', reason: 'Retired' }] },
    } })).toBe(false)
  })
  it('rejects builder identity or deployment-only secrets on every other surface', () => {
    process.env.DATA_PLANE_DEPLOY_PRINCIPAL = 'serviceAccount:github-actions@example'
    const policy = { bindings: [{ role: 'roles/iam.serviceAccountUser', members: ['serviceAccount:github-actions@example'] }] }
    expect(() => assertEffectiveIsolation([], policy, [{ kind: 'revision', name: 'web', definition: { serviceAccount: BUILDER_SERVICE_ACCOUNT } }]))
      .toThrow(/Builder identity is used outside/)
    expect(() => assertEffectiveIsolation([], policy, [{ kind: 'revision', name: 'web', definition: { serviceAccount: 'web@example', secretKeyRef: { name: 'data-plane-admin-db-url' } } }]))
      .toThrow(/DBA\/migrator credential/)
    expect(() => assertEffectiveIsolation([], policy, [
      { kind: 'revision', name: 'historical-web', definition: {
        serviceAccount: 'web@example', env: [{ name: 'DATABASE_URL', value: 'legacy-literal' }],
      } },
      { kind: 'job', name: 'brahma-build-pipeline-job', definition: {
        serviceAccount: BUILDER_SERVICE_ACCOUNT, secretKeyRef: { name: 'data-plane-builder-db-url' },
      } },
    ])).not.toThrow()
    expect(() => assertEffectiveIsolation([], policy, [
      { kind: 'service', name: 'current-web', definition: {
        serviceAccount: 'web@example', env: [{ name: 'DATABASE_URL', value: 'legacy-literal' }],
      } },
      { kind: 'job', name: 'brahma-build-pipeline-job', definition: {
        serviceAccount: BUILDER_SERVICE_ACCOUNT, secretKeyRef: { name: 'data-plane-builder-db-url' },
      } },
    ])).toThrow(/service\/current-web/)
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
  it('evaluates custom/basic role permissions and rejects literal Cloud Run credentials', () => {
    const literalDatabaseUrl = ['postgresql://literal', ':credential@example/db'].join('')
    const clientPasswordKey = ['client', 'password'].join('_')
    const permissions = {
      'projects/example/roles/customSecretReader': ['secretmanager.versions.access'],
      'roles/owner': ['iam.serviceAccounts.getAccessToken'],
    }
    expect(() => assertSecretIsolation({ bindings: [{
      role: 'projects/example/roles/customSecretReader', members: ['serviceAccount:rogue@example'],
    }] }, {}, {}, undefined, permissions)).toThrow(/Project-wide/)
    process.env.DATA_PLANE_DEPLOY_PRINCIPAL = 'serviceAccount:github-actions@example'
    expect(() => assertEffectiveIsolation([{ resource: 'folders/123', policy: { bindings: [{
      role: 'roles/owner', members: ['user:rogue@example'], condition: { expression: 'true' },
    }] } }], { bindings: [{ role: 'roles/iam.serviceAccountUser', members: ['serviceAccount:github-actions@example'] }] }, [], permissions))
      .toThrow(/aggregate builder service-account impersonation/)
    expect(() => assertNoLiteralCredentials({ spec: { template: { spec: { containers: [{ env: [{
      name: 'DATABASE_URL', value: literalDatabaseUrl,
    }] }] } } } })).toThrow(/never a literal/)
    expect(() => assertNoLiteralCredentials({ spec: { template: { metadata: { annotations: {
      [clientPasswordKey]: 'opaque-but-still-a-secret',
    } } } } })).toThrow(/client_password/)
    expect(() => assertNoLiteralCredentials({ spec: { template: { spec: { containers: [{
      args: ['--token', 'opaque'], env: [{ name: 'SAFE_NAME', value: 'ordinary' }],
    }] } } } })).toThrow(/--token/)
    expect(() => assertNoLiteralCredentials({ spec: { template: { spec: { containers: [{
      args: ['-c', 'gcloud secrets versions access latest --secret=canary-key --project=madhav-astrology >/dev/null 2>&1 && exit 42 || exit 0'],
    }] } } } })).toThrow(/literal credential/)
    expect(() => assertNoLiteralCredentials({ spec: { template: { spec: { containers: [{
      args: ['-c', 'gcloud secrets versions access latest --secret=canary-key --project=madhav-astrology && curl example.invalid'],
    }] } } } })).toThrow(/literal credential/)
    expect(() => assertNoLiteralCredentials({ spec: { template: { spec: {
      volumes: [{ clientSecret: 12345 }],
    } } } })).toThrow(/clientSecret/)
    expect(() => assertNoLiteralCredentials({ env: [{ name: '# documentation containing token terminology' }] }))
      .not.toThrow()
    expect(() => assertNoLiteralCredentials({ env: [{
      name: '# documentation containing token terminology', value: 'not-empty',
    }] })).toThrow(/explicit Secret Manager reference/)
    expect(() => assertNoLiteralCredentials({ env: [{
      name: 'NEXT_PUBLIC_FIREBASE_API_KEY', value: `AIza${'a'.repeat(35)}`,
    }] })).not.toThrow()
    expect(() => assertNoLiteralCredentials({ env: [{
      name: 'NEXT_PUBLIC_FIREBASE_API_KEY', value: 'not-a-firebase-client-key',
    }] })).toThrow(/explicit Secret Manager reference/)
    for (const name of ['DB_PASS','PGPASSWORD','PASS','DB_PASSPHRASE','APP_ACCESS_TOKEN','app-client-secret']) {
      expect(() => assertNoLiteralCredentials({ spec: { template: { spec: { containers: [{ env: [{
        name, value: 'opaque',
      }] }] } } } })).toThrow(/explicit Secret Manager reference/)
    }
    for (const flag of ['--worker-db-pass','--prefix-access-token','--service-client-secret']) {
      expect(() => assertNoLiteralCredentials({ spec: { template: { spec: { containers: [{
        args: [flag, 'opaque'],
      }] } } } })).toThrow(new RegExp(flag))
    }
    expect(() => assertNoLiteralCredentials({ spec: { template: { spec: { containers: [{ env: [{
      name: 'DB_PASS', valueFrom: { secretKeyRef: { name: 'builder-db-pass', key: 'latest' } },
    }] }], volumes: [{ name: 'credentials', secret: { secretName: 'volume-secret' } }] } }, metadata: { annotations: {
      'run.googleapis.com/secrets': JSON.stringify({ builder: 'builder-db-pass:latest' }),
    } } } })).not.toThrow()
    expect(() => assertNoLiteralCredentials({ spec: { template: { spec: { containers: [{ env: [{
      name: 'CLIENT_SECRET', valueFrom: { secretKeyRef: { name: 'client-secret', literal: 'opaque' } },
    }] }] } } } })).toThrow(/explicit Secret Manager reference/)
    expect(() => assertNoLiteralCredentials({ spec: { template: { spec: { containers: [{ env: [{
      name: 'DB_PASS', valueFrom: { secretKeyRef: { name: literalDatabaseUrl } },
    }] }] } } } })).toThrow(/explicit Secret Manager reference/)
    expect(roleDescribeArgs('roles/owner')).toEqual(['iam','roles','describe','roles/owner'])
    expect(roleDescribeArgs('projects/exact-parent/roles/customSecretReader'))
      .toEqual(['iam','roles','describe','customSecretReader','--project','exact-parent'])
    expect(roleDescribeArgs('organizations/123456/roles/customTokenCreator'))
      .toEqual(['iam','roles','describe','customTokenCreator','--organization','123456'])
    expect(() => roleDescribeArgs('folders/123/roles/not-supported')).toThrow(/invalid role resource/)
    expect(cloudRunLocation({ metadata: { labels: { 'cloud.googleapis.com/location': 'asia-south1' } } })).toBe('asia-south1')
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
      expect(sql).toMatch(/data_plane_sequence_attestations/)
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
    expect(l2).toContain('l2_data_plane_manifest_attestations')
  })

  it('partitions both shared L2 tables and restricts cross-producer enrichment', () => {
    const sql = readFileSync(resolve(__dirname, '../../supabase/migrations/1036_data_plane_l2_producer_generations.sql'), 'utf8')
    expect(sql).toContain("'system_convergence_count','cross_system_consensus_count'")
    expect(sql).toContain("'contradicts_signals_array','graph_node_strength_contribution_jsonb'")
    expect(sql).toContain("'valence','valence_source'")
    expect(sql).toContain("WHEN v_row->>'node_type' IN ('bhava','domain','dosha','graha','yoga') THEN 'bo_bimba'")
    expect(sql).toContain("WHEN v_row->>'node_type' IN ('arudha','special_lagna') THEN 'bo_karanajala'")
    expect(sql).toContain("'pagerank_score','eigenvector_centrality'")
    expect(sql).toContain("'betweenness_centrality','harmonic_centrality'")
  })
  it('normalizes the complete pre-existing table, sequence, and schema ACL surface', () => {
    const preflight = readFileSync(resolve(__dirname, '../../scripts/data-plane-ownership-preflight.ts'), 'utf8')
    expect(preflight).toContain('CROSS JOIN LATERAL aclexplode')
    expect(preflight).toContain("revokeAllRelationGrantees(client, 'TABLE'")
    expect(preflight).toContain("revokeAllRelationGrantees(client, 'SEQUENCE'")
    expect(preflight).toContain('revokeAllPublicSchemaGrantees(client)')
    expect(preflight).toContain('revokeAllDefaultPrivilegeGrantees(client')
    expect(preflight).toContain('normalizeDataPlaneMemberships(client)')
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
  it('gates IAM before DBA/migrator use and routes the build job to the dedicated credential', () => {
    expect(workflow.indexOf('Verify data-plane pre-transition isolation before privileged access')).toBeLessThan(workflow.indexOf('Execute Native-authorized automated cutover under backup'))
    expect(workflow.indexOf('Execute Native-authorized automated cutover under backup')).toBeLessThan(workflow.indexOf('Run general database migrations'))
    expect(workflow).toContain('--service-account=data-plane-builder-runtime@madhav-astrology.iam.gserviceaccount.com')
    expect(workflow).toContain('--set-secrets=DATABASE_URL=data-plane-builder-db-url:latest')
    expect(workflow).toContain('DATA_PLANE_CONTROL_PLANE_ADMIN_PRINCIPAL: ${{ vars.DATA_PLANE_CONTROL_PLANE_ADMIN_PRINCIPAL }}')
    expect(JSON.stringify(workflowJobs['deploy-pipeline-job'])).not.toContain('DATABASE_URL=amjis-pipeline-db-url')
    expect(workflow).toContain('environment: data-plane-production-cutover')
    expect(workflow).toContain('DATA_PLANE_BACKUP_RESTORE_ID')
    expect(workflow).toContain('group: data-plane-production-cutover')
    expect(workflow).toMatch(/deploy-pipeline-job:[\s\S]*?needs: \[changes, migrate\]/)
    expect(workflow.indexOf('Re-attest protected data-plane semantic state')).toBeLessThan(workflow.indexOf('Run general database migrations'))
  })

  it('isolates one-time privileged bootstrap from routine migration and dependent delivery', () => {
    const state = workflowJobs['migration-state']
    const bootstrap = workflowJobs['privileged-bootstrap']
    const migrate = workflowJobs.migrate

    expect(state.needs).toEqual(['changes'])
    expect(state.environment).toBeUndefined()
    expect(state.outputs).toEqual({
      data_plane: '${{ steps.data-plane-ownership.outputs.state }}',
      data_plane_isolation: '${{ steps.data-plane-isolation.outputs.state }}',
      nirmana: '${{ steps.nirmana-ownership.outputs.state }}',
      purna: '${{ steps.purna-ownership.outputs.state }}',
    })
    expect(state.steps?.map((step) => step.name)).toEqual(expect.arrayContaining([
      'Inspect protected data-plane ownership state',
      'Inspect protected data-plane runtime isolation',
      'Inspect Nirmana evidence ownership handoff marker',
      'Inspect Pūrṇa inquiry protected-owner handoff',
    ]))
    const isolationInspection = state.steps?.find((step) => step.name === 'Inspect protected data-plane runtime isolation')
    expect(isolationInspection?.run).toContain('state=repair_required')
    expect(isolationInspection?.run).toContain('data-plane-secret-isolation-preflight.ts')
    expect(isolationInspection?.env?.DATA_PLANE_SECRET_ISOLATION_MODE).toBe('strict')

    expect(bootstrap.needs).toEqual(['changes', 'migration-state'])
    expect(bootstrap.environment).toBe('data-plane-production-cutover')
    expect(bootstrap.concurrency).toEqual({ group: 'data-plane-production-cutover', 'cancel-in-progress': false })
    expect(bootstrap.if).toContain("needs.migration-state.outputs.data_plane == 'unmarked'")
    expect(bootstrap.if).toContain("needs.migration-state.outputs.data_plane_isolation != 'strict'")
    expect(bootstrap.if).toContain("needs.migration-state.outputs.nirmana == 'unmarked'")
    expect(bootstrap.if).toContain("needs.migration-state.outputs.purna != 'marked'")
    expect(Object.entries(workflowJobs).filter(([, job]) => job.environment === 'data-plane-production-cutover').map(([name]) => name))
      .toEqual(['privileged-bootstrap'])
    expect(JSON.stringify(bootstrap)).toContain('DATA_PLANE_ADMIN_DATABASE_URL')
    expect(JSON.stringify(bootstrap)).toContain('DATA_PLANE_MIGRATOR_DATABASE_URL')
    expect(JSON.stringify(bootstrap)).toContain('NIRMANA_EVIDENCE_LEGACY_OWNER_DATABASE_URL')
    expect(JSON.stringify(bootstrap)).toContain('NIRMANA_MIGRATOR_DATABASE_URL')

    expect(migrate.needs).toEqual(['changes', 'migration-state', 'privileged-bootstrap'])
    expect(migrate.environment).toBeUndefined()
    expect(migrate.concurrency).toEqual({ group: 'data-plane-production-cutover', 'cancel-in-progress': false })
    expect(migrate.if).toContain('always()')
    expect(JSON.stringify(migrate)).not.toContain('DATA_PLANE_ADMIN_DATABASE_URL')
    expect(JSON.stringify(migrate)).not.toContain('DATA_PLANE_MIGRATOR_DATABASE_URL')
    expect(JSON.stringify(migrate)).not.toContain('NIRMANA_EVIDENCE_LEGACY_OWNER_DATABASE_URL')
    expect(JSON.stringify(migrate)).not.toContain('NIRMANA_MIGRATOR_DATABASE_URL')
    expect(migrate.if).not.toContain('needs.changes.outputs.')
    const routineStepNames = migrate.steps?.map((step) => step.name) ?? []
    const bootstrapRefresh = bootstrap.steps?.find((step) => step.name === 'Refresh protected bootstrap state under the exclusive lock')
    const bootstrapStepNames = bootstrap.steps?.map((step) => step.name) ?? []
    const transitionIndex = bootstrapStepNames.indexOf('Bind named build job to dedicated data-plane credential')
    const strictIndex = bootstrapStepNames.indexOf('Verify strict data-plane isolation after build-job rebind')
    expect(bootstrapRefresh?.run).toContain('PRIOR_DATA_PLANE_STATE')
    expect(bootstrapRefresh?.run).toContain('PRIOR_NIRMANA_STATE')
    expect(bootstrapRefresh?.run).toContain('PRIOR_PURNA_STATE')
    expect(bootstrapRefresh?.run).toContain('data-plane-ownership-status.ts')
    expect(bootstrapRefresh?.run).toContain('nirmana-evidence-ownership-status.ts')
    expect(bootstrapRefresh?.run).toContain('purna-inquiry-ownership-status.ts')
    expect(bootstrapRefresh?.run).toContain('state regressed after the initial inspection')
    expect(bootstrapRefresh?.run).toContain('read_protected_state()')
    expect(bootstrapRefresh?.run).toContain('for attempt in 1 2 3 4 5')
    expect(bootstrapRefresh?.run).toContain('state could not be read after 5 bounded attempts')
    expect(transitionIndex).toBeGreaterThan(bootstrapStepNames.indexOf('Execute Native-authorized automated cutover under backup, restore, lease and quiescence'))
    expect(strictIndex).toBeGreaterThan(transitionIndex)
    expect(bootstrap.steps?.[strictIndex]?.run).toContain('data-plane-secret-isolation-preflight.ts')
    expect(bootstrap.steps?.[strictIndex]?.env?.DATA_PLANE_SECRET_ISOLATION_MODE).toBe('strict')
    expect(bootstrap.steps?.[transitionIndex]?.if).toContain("needs.migration-state.outputs.data_plane_isolation != 'strict'")
    for (const stepName of [
      'Execute Native-authorized automated cutover under backup, restore, lease and quiescence',
      'One-shot Nirmana evidence ownership preflight',
      'Attest Nirmana ownership handoff as deployment-only migrator',
    ]) {
      expect(bootstrap.steps?.find((step) => step.name === stepName)?.if).toContain('steps.bootstrap-state.outputs.')
    }
    expect(routineStepNames.indexOf('Verify data-plane secret and runtime isolation'))
      .toBeLessThan(routineStepNames.indexOf('Re-attest protected data-plane semantic state with routine credential'))
    expect(routineStepNames.indexOf('Re-attest protected data-plane semantic state with routine credential'))
      .toBeLessThan(routineStepNames.indexOf('Run general database migrations'))
    expect(routineStepNames.indexOf('Re-attest Nirmana evidence ownership state with routine credential'))
      .toBeLessThan(routineStepNames.indexOf('Run general database migrations'))
    expect(migrate.steps?.find((step) => step.name === 'Run general database migrations')?.if).toBeUndefined()

    for (const secret of [
      'DATA_PLANE_ADMIN_DATABASE_URL',
      'DATA_PLANE_MIGRATOR_DATABASE_URL',
      'NIRMANA_EVIDENCE_LEGACY_OWNER_DATABASE_URL',
      'NIRMANA_MIGRATOR_DATABASE_URL',
    ]) {
      expect(Object.entries(workflowJobs).filter(([, job]) => JSON.stringify(job).includes(secret)).map(([name]) => name))
        .toEqual(['privileged-bootstrap'])
    }

    for (const jobName of ['deploy-web', 'deploy-mcp', 'deploy-pipeline-job']) {
      expect(workflowJobs[jobName].needs).toContain('migrate')
    }
  })

  it('admits only marked routine delivery or a successful required bootstrap', () => {
    const bootstrapIf = workflowJobs['privileged-bootstrap'].if as string
    const migrateIf = workflowJobs.migrate.if as string
    const base = {
      'github.event_name': 'workflow_run',
      'github.event.workflow_run.conclusion': 'success',
      'needs.changes.result': 'success',
      'needs.migration-state.result': 'success',
    }
    const scenario = (
      dataPlane: string,
      nirmana: string,
      purna: string,
      bootstrapResult: string,
      isolation = 'strict',
    ) => ({
      ...base,
      'needs.migration-state.outputs.data_plane': dataPlane,
      'needs.migration-state.outputs.data_plane_isolation': isolation,
      'needs.migration-state.outputs.nirmana': nirmana,
      'needs.migration-state.outputs.purna': purna,
      'needs.privileged-bootstrap.result': bootstrapResult,
    })

    expect(evaluateWorkflowCondition(bootstrapIf, scenario('marked', 'marked', 'marked', 'skipped'))).toBe(false)
    expect(evaluateWorkflowCondition(migrateIf, scenario('marked', 'marked', 'marked', 'skipped'))).toBe(true)
    expect(evaluateWorkflowCondition(bootstrapIf, scenario('unmarked', 'marked', 'marked', 'skipped'))).toBe(true)
    expect(evaluateWorkflowCondition(migrateIf, scenario('unmarked', 'marked', 'marked', 'success'))).toBe(true)
    expect(evaluateWorkflowCondition(bootstrapIf, scenario('marked', 'unmarked', 'marked', 'skipped'))).toBe(true)
    expect(evaluateWorkflowCondition(migrateIf, scenario('marked', 'unmarked', 'marked', 'success'))).toBe(true)
    expect(evaluateWorkflowCondition(bootstrapIf, scenario('marked', 'marked', 'armed', 'skipped'))).toBe(true)
    expect(evaluateWorkflowCondition(migrateIf, scenario('marked', 'marked', 'armed', 'success'))).toBe(true)
    expect(evaluateWorkflowCondition(bootstrapIf, scenario('marked', 'marked', 'marked', 'skipped', 'repair_required'))).toBe(true)
    expect(evaluateWorkflowCondition(migrateIf, scenario('marked', 'marked', 'marked', 'success', 'repair_required'))).toBe(true)
    expect(evaluateWorkflowCondition(migrateIf, scenario('marked', 'marked', 'marked', 'skipped', 'repair_required'))).toBe(false)

    for (const result of ['failure', 'cancelled', 'skipped']) {
      expect(evaluateWorkflowCondition(migrateIf, scenario('unmarked', 'marked', 'marked', result))).toBe(false)
    }
    expect(evaluateWorkflowCondition(migrateIf, scenario('marked', 'marked', 'marked', 'success'))).toBe(false)
    expect(evaluateWorkflowCondition(migrateIf, scenario('unknown', 'marked', 'marked', 'skipped'))).toBe(false)
    expect(evaluateWorkflowCondition(migrateIf, {
      ...scenario('marked', 'marked', 'marked', 'skipped'),
      'needs.migration-state.result': 'failure',
    })).toBe(false)
    expect(evaluateWorkflowCondition(migrateIf, {
      ...scenario('marked', 'marked', 'marked', 'skipped'),
      'github.event.workflow_run.conclusion': 'failure',
    })).toBe(false)
  })
  it('requires exact backup and successful-restore identifiers as one receipt', () => {
    const preflight = readFileSync(resolve(__dirname, '../../scripts/data-plane-cutover-preflight.ts'), 'utf8')
    const receipt = parseBackupRestoreReceipt(JSON.stringify({
      authorityDecision: DATA_PLANE_CUTOVER_AUTHORITY,
      backupId: '123', restoreOperationId: 'restore-op-456', validationInstance: 'amjis-ri02-validation',
      sourceCommit: 'a'.repeat(40), leaseId: '11111111-1111-4111-8111-111111111111',
      executionMode: DATA_PLANE_CUTOVER_EXECUTION_MODE, expiresAt: '2026-09-16T00:00:00.000Z',
      repository: 'owner/repo', workflowRunId: '123456', environment: 'data-plane-production-cutover',
    }))
    expect(receipt.backupId).toBe('123')
    expect(() => parseBackupRestoreReceipt('123')).toThrow(/receipt/)
    expect(() => assertBackupReceiptBinding(receipt, {
      validationInstance: 'amjis-postgres', sourceCommit: 'a'.repeat(40),
      leaseId: receipt.leaseId, authorityDecision: receipt.authorityDecision, executionMode: receipt.executionMode,
      repository: receipt.repository, workflowRunId: receipt.workflowRunId, environment: receipt.environment,
    }, new Date('2026-09-15T12:00:00.000Z'))).toThrow(/isolated instance/)
    expect(() => assertBackupReceiptBinding(receipt, {
      validationInstance: receipt.validationInstance, sourceCommit: receipt.sourceCommit,
      leaseId: receipt.leaseId, authorityDecision: receipt.authorityDecision, executionMode: receipt.executionMode,
      repository: receipt.repository, workflowRunId: receipt.workflowRunId, environment: receipt.environment,
    }, new Date('2026-09-15T12:00:00.000Z'))).not.toThrow()
    const protectedEnvironment = {
      name: receipt.environment,
      protection_rules: [],
      deployment_branch_policy: { protected_branches: true, custom_branch_policies: false },
    }
    const workflowRun = { id: Number(receipt.workflowRunId), head_sha: receipt.sourceCommit, repository: { full_name: receipt.repository } }
    expect(() => assertGitHubAutomatedCutoverEvidence(protectedEnvironment, workflowRun, {
      environment: receipt.environment, authorityDecision: receipt.authorityDecision, executionMode: receipt.executionMode,
      repository: receipt.repository, workflowRunId: receipt.workflowRunId, sourceCommit: receipt.sourceCommit,
    })).not.toThrow()
    expect(() => assertGitHubAutomatedCutoverEvidence({ ...protectedEnvironment, protection_rules: [{ type: 'required_reviewers', prevent_self_review: true, reviewers: [{}] }] }, workflowRun, {
      environment: receipt.environment, authorityDecision: receipt.authorityDecision, executionMode: receipt.executionMode,
      repository: receipt.repository, workflowRunId: receipt.workflowRunId, sourceCommit: receipt.sourceCommit,
    })).toThrow(/must not depend on a human/)
    expect(() => assertGitHubAutomatedCutoverEvidence(protectedEnvironment, workflowRun, {
      environment: receipt.environment, authorityDecision: 'DP-SD-019', executionMode: receipt.executionMode,
      repository: receipt.repository, workflowRunId: receipt.workflowRunId, sourceCommit: receipt.sourceCommit,
    })).toThrow(/exact Native-authorized/)
    expect(() => assertGitHubAutomatedCutoverEvidence({ ...protectedEnvironment, deployment_branch_policy: { protected_branches: false, custom_branch_policies: true } }, workflowRun, {
      environment: receipt.environment, authorityDecision: receipt.authorityDecision, executionMode: receipt.executionMode,
      repository: receipt.repository, workflowRunId: receipt.workflowRunId, sourceCommit: receipt.sourceCommit,
    })).toThrow(/only protected branches/)
    expect(() => assertGitHubAutomatedCutoverEvidence(protectedEnvironment, { ...workflowRun, head_sha: 'b'.repeat(40) }, {
      environment: receipt.environment, authorityDecision: receipt.authorityDecision, executionMode: receipt.executionMode,
      repository: receipt.repository, workflowRunId: receipt.workflowRunId, sourceCommit: receipt.sourceCommit,
    })).toThrow(/workflow run does not match/)
    const instance = { name: receipt.validationInstance, state: 'RUNNABLE', connectionName: `madhav-astrology:asia-south1:${receipt.validationInstance}` }
    const validationDatabaseUrl = ['postgresql://validator', ':secret@localhost:5433/restored'].join('')
    const poolConfig = assertValidationConnectorBinding(validationDatabaseUrl, {
      instance, validationInstance: receipt.validationInstance, connectionName: instance.connectionName,
      proxyPort: '5433', project: 'madhav-astrology',
    })
    expect(poolConfig).toMatchObject({
      host: '127.0.0.1', port: 5433, user: 'validator', database: 'restored', max: 1,
    })
    expect(poolConfig.password).toBe(['sec', 'ret'].join(''))
    expect(Object.isFrozen(poolConfig)).toBe(true)
    for (const query of [
      'host=rogue.internal','HOST_ADDR=10.0.0.5','port=5432','service=rogue',
      'socket=%2Ftmp%2Frogue.sock','socket_path=%2Ftmp%2Frogue.sock','unixSocketPath=%2Ftmp%2Frogue.sock',
      'server=rogue.internal',
    ]) {
      expect(() => assertValidationConnectorBinding(`postgresql://validator@127.0.0.1:5433/restored?${query}`, {
        instance, validationInstance: receipt.validationInstance, connectionName: instance.connectionName,
        proxyPort: '5433', project: 'madhav-astrology',
      })).toThrow(/authenticated isolated Cloud SQL proxy identity/)
    }
    expect(() => assertValidationConnectorBinding('postgresql://validator@127.0.0.1:5433/restored', {
      instance, validationInstance: receipt.validationInstance, connectionName: 'madhav-astrology:asia-south1:rogue-instance',
      proxyPort: '5433', project: 'madhav-astrology',
    })).toThrow(/authenticated isolated Cloud SQL proxy identity/)
    expect(preflight).toContain("restore.targetId === 'amjis-postgres'")
    expect(preflight).toContain('readDataPlaneOwnershipStatus(validationPoolConfig)')
    expect(preflight).toContain('new Pool(validationPoolConfig)')
    expect(workflow).toContain('DATA_PLANE_RESTORE_VALIDATION_CONNECTION_NAME')
    expect(workflow).toContain('GH_TOKEN: ${{ github.token }}')
    expect(preflight).not.toContain('/approvals')
    expect(preflight).not.toContain('approvedBy')
    expect(preflight).toMatch(/LOCK TABLE public\.build_runs, public\.build_run_assets[\s\S]*SHARE ROW EXCLUSIVE MODE NOWAIT/)
  })

  it('binds the restore operation to the exact backup through Cloud Audit Logs', () => {
    const operationId = '81fa436f-115b-4f27-82c8-93800000002f'
    const auditEntries = [
      {
        operation: { id: operationId, first: true, producer: 'cloudsql.googleapis.com' },
        protoPayload: {
          serviceName: 'cloudsql.googleapis.com',
          methodName: 'cloudsql.instances.restoreBackup',
          resourceName: 'projects/madhav-astrology/instances/amjis-ri02-validation-c720f1832',
          authorizationInfo: [{
            granted: true, permission: 'cloudsql.instances.restoreBackup',
            resource: 'projects/madhav-astrology/instances/amjis-ri02-validation-c720f1832',
          }],
          request: {
            '@type': 'type.googleapis.com/google.cloud.sql.v1beta4.SqlInstancesRestoreBackupRequest',
            project: 'madhav-astrology',
            instance: 'amjis-ri02-validation-c720f1832',
            body: { restoreBackupContext: { backupRunId: '1789559207984', instanceId: 'amjis-postgres' } },
          },
          response: { name: operationId, operationType: 'RESTORE_VOLUME', targetId: 'amjis-ri02-validation-c720f1832' },
          status: { message: 'OK' },
        },
      },
      {
        operation: { id: operationId, last: true, producer: 'cloudsql.googleapis.com' },
        protoPayload: {
          serviceName: 'cloudsql.googleapis.com',
          methodName: 'cloudsql.instances.restoreBackup',
          resourceName: 'projects/madhav-astrology/instances/amjis-ri02-validation-c720f1832',
          status: { message: 'OK' },
        },
      },
    ]
    const binding = {
      project: 'madhav-astrology', operationId, backupId: '1789559207984',
      sourceInstance: 'amjis-postgres', validationInstance: 'amjis-ri02-validation-c720f1832',
    }
    expect(() => assertRestoreAuditBinding(auditEntries, binding)).not.toThrow()
    expect(() => assertRestoreAuditBinding(auditEntries, { ...binding, backupId: '1789559207985' }))
      .toThrow(/does not bind the exact backup restore/)
    const unauthorizedEntries = structuredClone(auditEntries)
    unauthorizedEntries[0]!.protoPayload!.authorizationInfo![0]!.granted = false
    expect(() => assertRestoreAuditBinding(unauthorizedEntries, binding))
      .toThrow(/does not bind the exact backup restore/)
    expect(() => assertRestoreAuditBinding(auditEntries.slice(0, 1), binding))
      .toThrow(/does not bind the exact backup restore/)
  })
})
