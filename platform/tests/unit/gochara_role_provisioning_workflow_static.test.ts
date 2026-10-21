/** The one-shot Gochara role-provisioning workflow + script (native ruling #1, option A): static properties a reviewer must be able to rely on. */
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'
import { parse } from 'yaml'

const root = resolve(__dirname, '../../..')
const workflowText = readFileSync(resolve(root, '.github/workflows/gochara-role-provisioning-oneshot.yml'), 'utf8')
const scriptText = readFileSync(resolve(root, 'platform/scripts/gochara-provision-roles.sh'), 'utf8')
type WorkflowStep = { name?: string; run?: string; shell?: string; env?: Record<string, string> }
type Workflow = {
  on: Record<string, unknown>
  permissions: Record<string, string>
  concurrency: Record<string, string | boolean>
  jobs: Record<string, { if: string; environment: string; steps: WorkflowStep[] }>
}
const wf = parse(workflowText) as Workflow
const code = (text: string) => text.split('\n').filter((l) => !l.trim().startsWith('#')).join('\n')

describe('gochara-role-provisioning-oneshot.yml', () => {
  it('is workflow_dispatch ONLY (no push, pull_request, schedule or other trigger)', () => {
    expect(Object.keys(wf.on)).toEqual(['workflow_dispatch'])
  })
  it('requires the exact confirmation phrase and runs only on main, in the one governed environment that holds the admin secret', () => {
    const job = wf.jobs.provision
    expect(job.if).toContain("github.ref == 'refs/heads/main'")
    expect(job.if).toContain("inputs.confirm == 'PROVISION-GOCHARA-ROLES'")
    expect(job.environment).toBe('data-plane-production-cutover')
    expect(Object.keys(wf.jobs)).toEqual(['provision'])
  })
  it('has minimal permissions, one concurrency group that never cancels, and uploads no artifact', () => {
    expect(wf.permissions).toEqual({ contents: 'read', 'id-token': 'write' })
    expect(wf.concurrency['cancel-in-progress']).toBe(false)
    expect(workflowText).not.toMatch(/upload-artifact|actions\/cache|tee |>>\s*"?\$GITHUB_(OUTPUT|ENV|STEP_SUMMARY)/)
  })
  it('passes inputs only through env (never interpolated into a shell script) and reads the admin secret only into ADMIN_DATABASE_URL', () => {
    const steps = wf.jobs.provision.steps
    for (const s of steps) if (s.run) expect(s.run).not.toContain('${{')
    const run = steps.find((s) => s.name?.startsWith('Run the reviewed provisioning script'))
    if (!run?.env) throw new Error('Provisioning step and environment are required')
    expect(run.env.ADMIN_DATABASE_URL).toBe('${{ secrets.DATA_PLANE_OWNERSHIP_ADMIN_DATABASE_URL }}')
    // owner step 1 fix (2026-10-21): stage grant-l1-reads runs over the protected migrator route, the same secret kala-verifier-role-oneshot.yml uses — in env only, never in argv
    expect(run.env.MIGRATOR_DATABASE_URL).toBe('${{ secrets.DATA_PLANE_MIGRATOR_DATABASE_URL }}')
    expect(Object.entries(run.env).filter(([, v]) => v.includes('secrets.')).map(([k]) => k).sort())
      .toEqual(['ADMIN_DATABASE_URL', 'MIGRATOR_DATABASE_URL', 'SEALER_PASSWORD_STAGING'])
    expect(code(workflowText).match(/(?<![A-Z_])MIGRATOR_DATABASE_URL/g)).toHaveLength(1)                 // named once, in that env block: nowhere in a command line
    expect(run.run).toBe('bash platform/scripts/gochara-provision-roles.sh')
    expect(run.shell).toBe('bash')
    expect(JSON.stringify(wf.jobs.provision.steps.filter((s) => s !== run))).not.toContain('secrets.')
  })
  it('offers exactly the five reviewed stages (J-4b-a55j adds grant-l1-reads and sealer-credential; O-W56-C adds layer-verifier-credential) and no free-form one', () => {
    const on = wf.on as { workflow_dispatch: { inputs: { stage: { type: string; options: string[] } } } }
    expect(on.workflow_dispatch.inputs.stage.type).toBe('choice')
    expect(on.workflow_dispatch.inputs.stage.options).toEqual(['create-roles', 'sealer-password', 'grant-l1-reads', 'sealer-credential', 'layer-verifier-credential'])
  })
  it('verifies the downloaded Cloud SQL proxy against a pinned sha256 before running it', () => {
    const proxy = (wf.jobs.provision.steps).find((s) => s.name === 'Start Cloud SQL Auth Proxy')
    if (!proxy?.run) throw new Error('Proxy startup script is required')
    expect(proxy.run).toContain('276139ff5d5dc484c51e1a9c065d69a9f6e47d5b726f94dced253b0227df2056  cloud-sql-proxy' .replace('$PIN', '276139ff5d5dc484c51e1a9c065d69a9f6e47d5b726f94dced253b0227df2056'))
    expect(proxy.run.indexOf('sha256sum -c')).toBeLessThan(proxy.run.indexOf('chmod +x'))
  })
  it('never uses gcloud sql users or the console route, and no step turns on xtrace', () => {
    expect(code(workflowText)).not.toMatch(/gcloud sql users|set -x|xtrace|ACTIONS_STEP_DEBUG/)
  })
})

describe('gochara-provision-roles.sh', () => {
  const c = code(scriptText)
  it('creates roles with SQL CREATE ROLE only, PASSWORD NULL, least privilege, and never gcloud sql users', () => {
    expect(c).not.toMatch(/gcloud sql users|gcloud_bin sql|"\$GCLOUD_BIN" sql/)
    expect(c).toContain('CREATE ROLE $role LOGIN $CREATE_COMMON CONNECTION LIMIT $limit PASSWORD NULL')
    expect(c).toContain('NOINHERIT NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS')
    expect(c).toContain("pg_has_role('$role','cloudsqlsuperuser','MEMBER')")
  })
  it('keeps secrets out of argv, files and xtrace', () => {
    expect(scriptText).toMatch(/^set \+x$/m)
    expect(c).not.toMatch(/set -[a-zA-Z]*x|xtrace/)
    expect(c).not.toMatch(/PASSWORD '\$\{?PW|--password|-W /)                       // the password is only ever printf'd to a pipe
    expect(c).toContain('--data-file=-')
    expect(c).not.toMatch(/>\s*[^&\s/][^\s]*\.(txt|env|json)/)                      // no redirect of anything into a file
    expect(c).toMatch(/openssl rand -hex 48/)
  })
  it('writes the secret store BEFORE setting the role password, and masks the generated value', () => {
    expect(c.indexOf('secrets versions add')).toBeGreaterThan(-1)
    expect(c.indexOf('secrets versions add')).toBeLessThan(c.indexOf('ALTER ROLE %s PASSWORD'))
    expect(c).toContain('echo "::add-mask::$PW"')
  })
  it('discards the stderr of every statement that carries a password (a server error can quote it) and rolls back / compensates its own partial work on every exit path', () => {
    const alters = c.split('\n').filter((l) => /psql_admin -f -/.test(l))
    expect(alters.length).toBe(4)                                           // the verifier ALTER, the shared sealer activation transaction, the L1-read grants (which carry no secret) and the layer-verifier activation
    expect(alters.filter((l) => l.includes('>/dev/null 2>&1')).length).toBe(3)
    expect(c).toContain('trap rollback EXIT')
    expect(c).toContain("trap 'exit 143' TERM")                              // a cancelled run still runs the compensation
    expect(c).toContain('secrets versions destroy')
    expect(c).toContain('DROP ROLE IF EXISTS')
    expect(c).toContain('COMPENSATING the sealer activation')
    expect(c).toContain('ROLLBACK INCOMPLETE — THE SEALER MAY BE ACTIVE')
  })
  it('keeps the admin connection out of argv: it is parsed once into PG* and never passed to psql', () => {
    expect(c).not.toMatch(/"\$PSQL_BIN"\s+"\$ADMIN_DATABASE_URL"/)
    expect(c).not.toMatch(/psql_admin\s+"\$/)
    expect(c).toContain('unset ADMIN_DATABASE_URL')
    expect(c).toContain('PGPASSWORD')
  })
  it('asks Secret Manager for exactly add / list / destroy and never for access (the secretVersionManager model, act 11)', () => {
    const verbs = [...c.matchAll(/secrets versions (\w+)/g)].map((m) => m[1])
    expect(new Set(verbs)).toEqual(new Set(['add', 'list', 'destroy']))
    expect(c).not.toMatch(/secrets versions access/)
  })
  it('makes sealer activation and its postconditions one transaction', () => {
    expect(c).toContain('printf "BEGIN;')
    expect(c).toContain('COMMIT;')
    expect(c).toMatch(/postcondition: sealer is a member of cloudsqlsuperuser/)
  })
  it('J-4b-a55j + C-04: the L1 grant is SELECT-only on exactly chart_facts and chart_dashas, and the schema grant is USAGE-only on public, for exactly the two principals, checked in the same transaction', () => {
    const grants = [...c.matchAll(/^GRANT .*$/gm)].map((m) => m[0])
    expect(grants).toEqual([
      'GRANT SELECT ON public.chart_facts, public.chart_dashas TO $VERIFIER_ROLE, $SEALER_ROLE;',
      'GRANT USAGE ON SCHEMA public TO $VERIFIER_ROLE, $SEALER_ROLE;',
    ])
    expect(c).toContain('the L1 grant is read-only')
    expect(c).toContain('the schema grant is USAGE only')
    expect(c).toContain('WITH GRANT OPTION')
    const stage = c.slice(c.indexOf('  grant-l1-reads)'), c.indexOf('  sealer-credential)'))
    expect(stage.indexOf('GRANT USAGE ON SCHEMA public')).toBeLessThan(stage.indexOf('COMMIT;'))   // inside the one transaction
    expect(stage.indexOf('BEGIN;')).toBeLessThan(stage.indexOf('GRANT USAGE ON SCHEMA public'))
  })
  it('owner step 1 fix: each GRANT is issued AS its owning role (SET LOCAL ROLE) inside the one transaction, before COMMIT, and the stage refuses any login but data_plane_migrator first', () => {
    const stage = c.slice(c.indexOf('  grant-l1-reads)'), c.indexOf('  sealer-credential)'))
    const sql = stage.slice(stage.indexOf('BEGIN;'), stage.indexOf('COMMIT;'))
    expect(sql.indexOf('SET LOCAL ROLE data_plane_l1_owner;')).toBeGreaterThan(-1)
    expect(sql.indexOf('SET LOCAL ROLE data_plane_l1_owner;')).toBeLessThan(sql.indexOf('GRANT SELECT ON public.chart_facts'))
    expect(sql.indexOf('GRANT SELECT ON public.chart_facts')).toBeLessThan(sql.indexOf('SET LOCAL ROLE data_plane_schema_owner;'))
    expect(sql.indexOf('SET LOCAL ROLE data_plane_schema_owner;')).toBeLessThan(sql.indexOf('GRANT USAGE ON SCHEMA public'))
    expect(sql.indexOf('GRANT USAGE ON SCHEMA public')).toBeLessThan(sql.indexOf('DO \\$post\\$'))      // the closure check runs after both grants, in the same transaction
    expect(stage.indexOf('data_plane_migrator|data_plane_migrator|true|true')).toBeGreaterThan(-1)
    expect(stage.indexOf('data_plane_migrator|data_plane_migrator|true|true')).toBeLessThan(stage.indexOf('BEGIN;'))
    expect(stage.indexOf("has_schema_privilege(current_user, 'public', 'USAGE')")).toBeLessThan(stage.indexOf("to_regclass('public.$t')"))   // permission asked before existence
    expect(c).toContain('MIGRATOR_DATABASE_URL:?')                                                                                          // required for this stage
    expect(c).toContain('unset MIGRATOR_DATABASE_URL')                                                                                      // never inherited by a child
  })
  it('J-4b-a55j: the sealer credential goes secret-store first, shares the one activation transaction, and the rollback destroys the version of the secret it wrote', () => {
    const stage = c.slice(c.indexOf('  sealer-credential)'), c.indexOf('  *) fail "unknown STAGE'))
    expect(stage.indexOf('secrets versions add "$SEALER_SECRET"')).toBeGreaterThan(-1)
    expect(stage.indexOf('secrets versions add')).toBeLessThan(stage.indexOf('activate_sealer "$PW"'))
    expect(stage).toContain('echo "::add-mask::$PW"')
    expect(stage).toContain('--data-file=-')
    expect(c).toContain('--secret "${CREATED_SECRET:-$VERIFIER_SECRET}"')
    expect(c).toContain('SEALER_SECRET="${SEALER_SECRET:-gochara-sealer-db-url}"')
  })
  it('O-W56-C: the layer-verifier credential goes secret-store first, activates in one transaction, is observed AS verifier_principal, grants nothing, and compensates before it destroys', () => {
    const stage = c.slice(c.indexOf('  layer-verifier-credential)'), c.indexOf('  *) fail "unknown STAGE'))
    expect(stage.length).toBeGreaterThan(200)
    expect(stage.indexOf('secrets versions add "$LAYER_VERIFIER_SECRET"')).toBeGreaterThan(-1)
    expect(stage.indexOf('secrets versions add')).toBeLessThan(stage.indexOf('activate_layer_verifier "$PW"'))
    expect(stage.indexOf('activate_layer_verifier "$PW"')).toBeLessThan(stage.indexOf('lv_login_ok "$PW"'))
    expect(stage).toContain('echo "::add-mask::$PW"')
    expect(stage).toContain('--data-file=-')
    expect(stage).not.toMatch(/\bGRANT\b/)                                                              // the stage grants nothing: the role's grants are migrations 1330/1334/1390 + grant-usage
    const activation = c.slice(c.indexOf('activate_layer_verifier() {'), c.indexOf('case "$STAGE" in'))
    expect(activation.indexOf('BEGIN;')).toBeGreaterThan(-1)
    expect(activation.indexOf('BEGIN;')).toBeLessThan(activation.indexOf("ALTER ROLE %s LOGIN PASSWORD"))
    expect(activation.indexOf("ALTER ROLE %s LOGIN PASSWORD")).toBeLessThan(activation.indexOf('DO \\$post\\$'))
    expect(activation.indexOf('DO \\$post\\$')).toBeLessThan(activation.indexOf('COMMIT;'))
    expect(c).toContain('LAYER_VERIFIER_SECRET="${LAYER_VERIFIER_SECRET:-kala-layer-verifier-db-url}"')
    expect(c).toContain('COMPENSATING the layer-verifier activation')
    expect(c).toContain('ROLLBACK INCOMPLETE — THE LAYER VERIFIER MAY BE ACTIVE')
    expect(c.indexOf('COMPENSATING the layer-verifier activation')).toBeLessThan(c.indexOf('secrets versions destroy'))
  })
  it('is idempotent by refusal and refuses a non-loopback connection', () => {
    expect(c).toContain('already exists')
    expect(c).toContain('must point at the loopback Cloud SQL proxy')
  })
})
