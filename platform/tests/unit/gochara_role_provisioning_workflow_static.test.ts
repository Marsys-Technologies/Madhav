/** The one-shot Gochara role-provisioning workflow + script (native ruling #1, option A): static properties a reviewer must be able to rely on. */
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'
import { parse } from 'yaml'

const root = resolve(__dirname, '../../..')
const workflowText = readFileSync(resolve(root, '.github/workflows/gochara-role-provisioning-oneshot.yml'), 'utf8')
const scriptText = readFileSync(resolve(root, 'platform/scripts/gochara-provision-roles.sh'), 'utf8')
const wf = parse(workflowText) as any
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
    const steps = wf.jobs.provision.steps as any[]
    for (const s of steps) if (s.run) expect(s.run).not.toContain('${{')
    const run = steps.find((s) => s.name?.startsWith('Run the reviewed provisioning script'))
    expect(run.env.ADMIN_DATABASE_URL).toBe('${{ secrets.DATA_PLANE_OWNERSHIP_ADMIN_DATABASE_URL }}')
    expect(run.run).toBe('bash platform/scripts/gochara-provision-roles.sh')
    expect(run.shell).toBe('bash')
    expect(JSON.stringify(wf.jobs.provision.steps.filter((s: any) => s !== run))).not.toContain('secrets.')
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
    expect(alters.length).toBe(2)                                           // the verifier ALTER and the sealer activation transaction
    for (const l of alters) expect(l).toContain('>/dev/null 2>&1')
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
  it('is idempotent by refusal and refuses a non-loopback connection', () => {
    expect(c).toContain('already exists')
    expect(c).toContain('must point at the loopback Cloud SQL proxy')
  })
})
