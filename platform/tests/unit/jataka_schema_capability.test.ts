import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { load } from 'js-yaml'
import { beforeEach, describe, expect, it, vi } from 'vitest'

const harness = vi.hoisted(() => ({
  queries: [] as string[],
  canCreate: false,
  canUse: true,
  directActor: true,
  appRoleNormalized: true,
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
          if (sql.includes('AS normalized')) return { rows: [{ normalized: harness.appRoleNormalized }] }
          if (sql.includes('AS can_create')) {
            return { rows: [{ can_create: harness.canCreate, can_use: harness.canUse }] }
          }
          if (sql.includes('GRANT CREATE ON SCHEMA public TO amjis_app')) harness.canCreate = true
          if (sql.includes('REVOKE CREATE ON SCHEMA public FROM amjis_app')) harness.canCreate = false
          if (sql.includes('GRANT USAGE ON SCHEMA public TO amjis_app')) harness.canUse = true
          return { rows: [] }
        },
        release: () => undefined,
      }
    }
    async end() { return undefined }
  },
}))

const { setJatakaSchemaCapability } = await import('../../scripts/jataka-schema-capability')
const {
  PROTECTED_PUBLIC_SCHEMA_MIGRATIONS,
  assertGeneralRunnerMayApplyPublicSchema,
} = await import('../../scripts/migrate')

const GOCHARA_CONTRACT_MIGRATIONS = [
  '1153_gochara_sky_event_substrate.sql',
  '1154_gochara_rule_path_registry.sql',
  '1155_gochara_relationship_record.sql',
  '1156_gochara_eval_window.sql',
  '1157_gochara_av_polarity_declaration.sql',
  '1204_gochara_av_qualifier_object_role.sql',
  '1206_gochara_search_inventory_completeness.sql',
  '1232_gochara_search_moon_scope_domain.sql',
  '1233_gochara_p1_period_anchor.sql',
  '1240_gochara_window_verification_gate.sql',
]

describe('Protected public-schema temporary capability', () => {
  beforeEach(() => {
    harness.queries.length = 0
    harness.canCreate = false
    harness.canUse = true
    harness.directActor = true
    harness.appRoleNormalized = true
  })

  it('grants only CREATE to the normalized app migration role through the protected owner', async () => {
    await expect(setJatakaSchemaCapability('grant', 'postgresql://fixture')).resolves.toBeUndefined()
    const joined = harness.queries.join('\n')
    expect(joined).toContain('SET LOCAL ROLE data_plane_schema_owner')
    expect(joined).toContain('GRANT CREATE ON SCHEMA public TO amjis_app')
    expect(joined).not.toContain('GRANT CREATE ON SCHEMA public TO PUBLIC')
    expect(joined.indexOf('AS can_create')).toBeLessThan(joined.indexOf('COMMIT'))
    expect(harness.canCreate).toBe(true)
  })

  it('fails closed when a prior run left CREATE armed', async () => {
    harness.canCreate = true
    await expect(setJatakaSchemaCapability('grant', 'postgresql://fixture'))
      .rejects.toThrow('already has public-schema CREATE')
    expect(harness.queries.join('\n')).not.toContain('GRANT CREATE ON SCHEMA public TO amjis_app')
  })

  it('revokes CREATE idempotently while preserving USAGE', async () => {
    harness.canCreate = true
    await expect(setJatakaSchemaCapability('revoke', 'postgresql://fixture')).resolves.toBeUndefined()
    const joined = harness.queries.join('\n')
    expect(joined).toContain('REVOKE CREATE ON SCHEMA public FROM amjis_app')
    expect(joined).toContain('GRANT USAGE ON SCHEMA public TO amjis_app')
    expect(harness.canCreate).toBe(false)
    expect(harness.canUse).toBe(true)
  })

  it('rejects a non-migrator actor or a broadened app role', async () => {
    harness.directActor = false
    await expect(setJatakaSchemaCapability('grant', 'postgresql://fixture'))
      .rejects.toThrow('direct protected data_plane_migrator route')

    harness.directActor = true
    harness.appRoleNormalized = false
    await expect(setJatakaSchemaCapability('grant', 'postgresql://fixture'))
      .rejects.toThrow('normalized application migration role')
  })
})

type WorkflowStep = { name?: string; if?: string; env?: Record<string, string>; run?: string }
type WorkflowJob = { needs?: string[]; if?: string; environment?: string; steps?: WorkflowStep[] }

describe('Protected public-schema migration workflow contract', () => {
  const workflow = load(readFileSync(resolve(__dirname, '../../../.github/workflows/deploy.yml'), 'utf8')) as {
    on: { workflow_dispatch: { inputs: Record<string, unknown> } }
    jobs: Record<string, WorkflowJob>
  }

  it('requires explicit manual authorization and the protected environment', () => {
    expect(workflow.on.workflow_dispatch.inputs.jataka_schema_migration).toBeTruthy()
    expect(workflow.on.workflow_dispatch.inputs.ai_console_schema_migration).toBeTruthy()
    expect(workflow.on.workflow_dispatch.inputs.ai_metering_schema_migration).toBeTruthy()
    expect(workflow.on.workflow_dispatch.inputs.gochara_schema_migration).toBeTruthy()
    expect(workflow.on.workflow_dispatch.inputs.gochara_contracts_schema_migration).toBeTruthy()
    const job = workflow.jobs['jataka-protected-migrations']
    expect(job.environment).toBe('data-plane-production-cutover')
    expect(job.if).toContain("github.event_name == 'workflow_dispatch'")
    expect(job.if).toContain('inputs.jataka_schema_migration == true')
    expect(job.if).toContain('inputs.ai_console_schema_migration == true')
    expect(job.if).toContain('inputs.ai_metering_schema_migration == true')
    expect(job.if).toContain('inputs.gochara_schema_migration == true')
    expect(job.if).toContain('inputs.gochara_contracts_schema_migration == true')
  })

  it('Pravāha A5.1: the Gochara contract migrations 1153-1157 apply ONLY through the window, in order', () => {
    const steps = workflow.jobs['jataka-protected-migrations'].steps ?? []
    const apply = steps.find((step) => step.name === 'Apply exact protected public-schema migrations')
    expect(apply?.env?.APPLY_GOCHARA_CONTRACTS_SCHEMA_MIGRATION).toContain('gochara_contracts_schema_migration')
    let previous = apply?.run?.indexOf('1125_ai_snapshot_shape_operator_precedence.sql') ?? -1
    expect(previous).toBeGreaterThan(-1)
    for (const migration of GOCHARA_CONTRACT_MIGRATIONS) {
      const at = apply?.run?.indexOf(migration) ?? -1
      expect(at, `${migration} must be listed after its predecessor`).toBeGreaterThan(previous)
      previous = at
    }
    // the runner's own refusal: routine path refuses each file; the --only window may apply it
    expect([...PROTECTED_PUBLIC_SCHEMA_MIGRATIONS].sort()).toEqual([...GOCHARA_CONTRACT_MIGRATIONS].sort())
    for (const migration of GOCHARA_CONTRACT_MIGRATIONS) {
      expect(() => assertGeneralRunnerMayApplyPublicSchema(migration, false))
        .toThrow(/gochara_contracts_schema_migration=true/)
      expect(() => assertGeneralRunnerMayApplyPublicSchema(migration, true)).not.toThrow()
    }
    expect(() => assertGeneralRunnerMayApplyPublicSchema('1152_kala_gochara_contacts_t_exact_nullable_truncated.sql', false)).not.toThrow()
  })

  it('pins the exact migration set between a grant and an always-run revoke', () => {
    const steps = workflow.jobs['jataka-protected-migrations'].steps ?? []
    const grant = steps.find((step) => step.name === 'Grant temporary public-schema capability')
    const apply = steps.find((step) => step.name === 'Apply exact protected public-schema migrations')
    const revoke = steps.find((step) => step.name === 'Revoke temporary public-schema capability')
    expect(grant?.env?.DATA_PLANE_MIGRATOR_DATABASE_URL).toContain('DATA_PLANE_MIGRATOR_DATABASE_URL')
    expect(grant?.run).toContain('jataka-schema-capability.ts grant')
    expect(apply?.env?.DATABASE_URL).toContain('PROD_DATABASE_URL')
    expect(apply?.env?.APPLY_JATAKA_SCHEMA_MIGRATIONS).toContain('jataka_schema_migration')
    expect(apply?.env?.APPLY_AI_CONSOLE_SCHEMA_MIGRATION).toContain('ai_console_schema_migration')
    expect(apply?.env?.APPLY_GOCHARA_SCHEMA_MIGRATION).toContain('gochara_schema_migration')
    for (const migration of [
      '1071_kala_gochara_windows_generation_guard.sql',
      '1120_jataka_conversation_archive_context.sql',
      '1121_jataka_correction_archive_write_guard.sql',
      '1122_jataka_chart_context_staleness.sql',
      '1123_jataka_context_staleness_deferred_surfaces.sql',
      '1124_ai_console_byok_routing.sql',
      '1125_ai_snapshot_shape_operator_precedence.sql',
      '1158_ai_console_configuration_types.sql',
    ]) {
      expect(apply?.run).toContain(migration)
    }
    expect(apply?.run?.indexOf('1071_kala_gochara_windows_generation_guard.sql')).toBeLessThan(
      apply?.run?.indexOf('1120_jataka_conversation_archive_context.sql') ?? -1,
    )
    expect(apply?.run?.indexOf('1124_ai_console_byok_routing.sql')).toBeLessThan(
      apply?.run?.indexOf('1125_ai_snapshot_shape_operator_precedence.sql') ?? -1,
    )
    expect(apply?.run?.indexOf('1125_ai_snapshot_shape_operator_precedence.sql')).toBeLessThan(
      apply?.run?.indexOf('1158_ai_console_configuration_types.sql') ?? -1,
    )
    expect(apply?.run).not.toContain('1151_ai_console_model_shortlist.sql')
    expect(apply?.run).toContain('migrate.ts --only "$only"')
    expect(revoke?.if).toContain('always()')
    expect(revoke?.run).toContain('jataka-schema-capability.ts revoke')
  })

  it('keeps AI metering table creation inside its exact protected window', () => {
    const steps = workflow.jobs['jataka-protected-migrations'].steps ?? []
    const apply = steps.find((step) => step.name === 'Apply exact protected public-schema migrations')
    const revoke = steps.find((step) => step.name === 'Revoke temporary public-schema capability')
    expect(apply?.env?.APPLY_AI_METERING_SCHEMA_MIGRATION).toContain('ai_metering_schema_migration')
    expect(apply?.run).toContain('if [ "$APPLY_AI_METERING_SCHEMA_MIGRATION" = "true" ]; then')
    expect(apply?.run).toContain('migrations+=(1202_ai_metering_ledger.sql)')
    expect(revoke?.if).toContain('always()')
    expect(() => assertGeneralRunnerMayApplyPublicSchema('1202_ai_metering_ledger.sql', false))
      .toThrow(/ai_metering_schema_migration=true/)
    expect(() => assertGeneralRunnerMayApplyPublicSchema('1202_ai_metering_ledger.sql', true)).not.toThrow()
  })

  it('holds every deploy behind the completed migration barrier', () => {
    expect(workflow.jobs.migrate.needs).toContain('jataka-protected-migrations')
    expect(workflow.jobs['deploy-sidecar'].needs).toContain('migrate')
    for (const name of ['deploy-web', 'deploy-sidecar', 'deploy-mcp', 'deploy-pipeline-job']) {
      expect(workflow.jobs[name].needs).toContain('migrate')
    }
  })
})
