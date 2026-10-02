/** DP-SD-018 extension: the Gochara verification pair (verifier SA + secret + one named job). */
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { afterEach, beforeEach, describe, expect, it } from 'vitest'
import {
  extractRunIdentityAndSecrets, parseSecretsAnnotation,
  assertEffectiveIsolation, assertVerifierInheritedControl, assertVerifierIsolation, assertVerifierServiceAccountPolicyExact, BUILDER_SERVICE_ACCOUNT, grantsServiceAccountControl, VERIFIER_JOB,
  VERIFIER_SECRET, VERIFIER_SERVICE_ACCOUNT, type VerifierState,
} from '../../scripts/data-plane-secret-isolation-preflight'

const DEPLOYER = 'serviceAccount:github-actions@example'
const verifier = `serviceAccount:${VERIFIER_SERVICE_ACCOUNT}`
const projectPolicy = { bindings: [{ role: 'roles/cloudsql.client', members: [verifier] }] }
const good = (): VerifierState => ({
  serviceAccountEmails: [VERIFIER_SERVICE_ACCOUNT],
  secretNames: [VERIFIER_SECRET],
  serviceAccount: { disabled: false },
  serviceAccountPolicy: { bindings: [{ role: 'roles/iam.serviceAccountUser', members: [DEPLOYER] }] },
  secretPolicy: { bindings: [{ role: 'roles/secretmanager.secretAccessor', members: [verifier] }] },
  userManagedKeys: 0,
})
const check = (state: VerifierState, project: Parameters<typeof assertVerifierIsolation>[0] = projectPolicy, phase: 'staged' | 'deployable' | undefined = 'deployable') =>
  assertVerifierIsolation(project, state, {}, DEPLOYER, phase)

describe('assertVerifierIsolation', () => {
  it('passes the exact pair, and passes while the resources do not exist yet', () => {
    expect(() => check(good())).not.toThrow()
    expect(() => check({ serviceAccountEmails: [], secretNames: [] })).not.toThrow()
    // act 3 done, act 4 not yet: service account without its secret
    const staged = good(); staged.secretNames = []; delete staged.secretPolicy
    expect(() => check(staged)).not.toThrow()
  })
  it('refuses any gochara-named service account or secret that is not the pair (the sealer has none)', () => {
    const sealerSecret = good(); sealerSecret.secretNames = [VERIFIER_SECRET, 'gochara-sealer-db-url']
    expect(() => check(sealerSecret)).toThrow(/gochara-seal environment/)
    const rogueAccount = good(); rogueAccount.serviceAccountEmails = [VERIFIER_SERVICE_ACCOUNT, 'gochara-sealer@x.iam.gserviceaccount.com']
    expect(() => check(rogueAccount)).toThrow(/Unknown gochara service account/)
  })
  it('refuses a verifier secret with no dedicated service account', () => {
    const orphan = good(); orphan.serviceAccountEmails = []
    expect(() => check(orphan)).toThrow(/without its dedicated service account/)
  })
  it('refuses extra project roles, conditional roles, a missing cloudsql.client, a disabled account and any key', () => {
    expect(() => check(good(), { bindings: [
      { role: 'roles/cloudsql.client', members: [verifier] },
      { role: 'roles/logging.logWriter', members: [verifier] },
    ] })).toThrow(/exactly project role/)
    expect(() => check(good(), { bindings: [
      { role: 'roles/cloudsql.client', members: [verifier], condition: { expression: 'true' } },
    ] })).toThrow(/exactly project role/)
    expect(() => check(good(), { bindings: [] })).toThrow(/exactly project role/)
    const disabled = good(); disabled.serviceAccount = { disabled: true }
    expect(() => check(disabled)).toThrow(/disabled/)
    const keyed = good(); keyed.userManagedKeys = 1
    expect(() => check(keyed)).toThrow(/no user-managed keys/)
    const unmeasured = good(); delete unmeasured.userManagedKeys
    expect(() => check(unmeasured)).toThrow(/no user-managed keys/)
  })
  it('refuses any secret accessor other than the verifier, conditional or not, including the builder', () => {
    const builderToo = good()
    builderToo.secretPolicy = { bindings: [{ role: 'roles/secretmanager.secretAccessor', members: [verifier, `serviceAccount:${BUILDER_SERVICE_ACCOUNT}`] }] }
    expect(() => check(builderToo)).toThrow(/exactly/)
    const conditional = good()
    conditional.secretPolicy = { bindings: [
      { role: 'roles/secretmanager.secretAccessor', members: [verifier] },
      { role: 'roles/secretmanager.secretAccessor', members: ['serviceAccount:rogue@example'], condition: { expression: 'true' } },
    ] }
    expect(() => check(conditional)).toThrow(/exactly/)
    const none = good(); none.secretPolicy = { bindings: [] }
    expect(() => check(none)).toThrow(/exactly/)
  })
  it('allows impersonation of the verifier only by the one deployer, and only unconditionally', () => {
    const none = good(); none.serviceAccountPolicy = { bindings: [] }
    expect(() => check(none, projectPolicy, 'staged')).not.toThrow()
    const other = good(); other.serviceAccountPolicy = { bindings: [{ role: 'roles/iam.serviceAccountUser', members: ['user:someone@example.com'] }] }
    expect(() => check(other)).toThrow(/exact allow-list/)
    const wrongRole = good(); wrongRole.serviceAccountPolicy = { bindings: [{ role: 'roles/iam.serviceAccountTokenCreator', members: [DEPLOYER] }] }
    expect(() => check(wrongRole)).toThrow(/exact allow-list/)
    const two = good(); two.serviceAccountPolicy = { bindings: [{ role: 'roles/iam.serviceAccountUser', members: [DEPLOYER, 'user:someone@example.com'] }] }
    expect(() => check(two)).toThrow(/exact allow-list/)
    const conditional = good(); conditional.serviceAccountPolicy = { bindings: [{ role: 'roles/iam.serviceAccountUser', members: [DEPLOYER], condition: { expression: 'true' } }] }
    expect(() => check(conditional)).toThrow(/exact allow-list/)
    expect(() => assertVerifierIsolation(projectPolicy, good(), {}, undefined, 'deployable')).toThrow(/exact allow-list/)
  })
})

describe('assertEffectiveIsolation: verifier and sealer on Cloud Run surfaces', () => {
  let previous: string | undefined
  beforeEach(() => { previous = process.env.DATA_PLANE_DEPLOY_PRINCIPAL; process.env.DATA_PLANE_DEPLOY_PRINCIPAL = DEPLOYER })
  afterEach(() => { if (previous === undefined) delete process.env.DATA_PLANE_DEPLOY_PRINCIPAL; else process.env.DATA_PLANE_DEPLOY_PRINCIPAL = previous })
  const builderPolicy = { bindings: [{ role: 'roles/iam.serviceAccountUser', members: [DEPLOYER] }] }
  const buildJob = { kind: 'job' as const, name: 'brahma-build-pipeline-job', definition: {
    serviceAccount: BUILDER_SERVICE_ACCOUNT, secretKeyRef: { name: 'data-plane-builder-db-url' },
  } }
  const verifierJob = (definition: unknown, name = VERIFIER_JOB) => ({ kind: 'job' as const, name, definition })
  const exact = { serviceAccount: VERIFIER_SERVICE_ACCOUNT, secretKeyRef: { name: VERIFIER_SECRET } }
  const run = (...surfaces: ReturnType<typeof verifierJob>[]) =>
    assertEffectiveIsolation([], builderPolicy, [buildJob, ...surfaces])

  it('accepts the verifier job bound exactly, and no verifier job at all', () => {
    expect(() => run()).not.toThrow()
    expect(() => run(verifierJob(exact))).not.toThrow()
  })
  it('refuses the verifier secret or identity anywhere but the one named job', () => {
    expect(() => run(verifierJob(exact, 'some-other-job'))).toThrow(/outside the one named verification job/)
    expect(() => run({ kind: 'revision' as never, name: 'web', definition: { serviceAccount: 'web@example', secretKeyRef: { name: VERIFIER_SECRET } } }))
      .toThrow(/outside the one named verification job/)
    expect(() => run({ kind: 'service' as never, name: 'web', definition: { serviceAccount: VERIFIER_SERVICE_ACCOUNT } }))
      .toThrow(/outside the one named verification job/)
  })
  it('refuses the named job when it is not exactly the verifier identity with exactly its one secret', () => {
    expect(() => run(verifierJob({ serviceAccount: 'web@example', secretKeyRef: { name: VERIFIER_SECRET } }))).toThrow(/lacks the exact verifier/)
    expect(() => run(verifierJob({ serviceAccount: VERIFIER_SERVICE_ACCOUNT }))).toThrow(/lacks the exact verifier/)
    expect(() => run(verifierJob({ serviceAccount: VERIFIER_SERVICE_ACCOUNT, secretKeyRef: { name: 'amjis-pipeline-db-url' } }))).toThrow(/lacks the exact verifier/)
    expect(() => run(verifierJob({ serviceAccount: VERIFIER_SERVICE_ACCOUNT, a: { secretKeyRef: { name: VERIFIER_SECRET } }, b: { secretKeyRef: { name: 'unrelated-secret' } } })))
      .toThrow(/lacks the exact verifier/)
  })
  it('refuses the builder credential on the verifier job and the verifier credential on the build job', () => {
    expect(() => run(verifierJob({ serviceAccount: VERIFIER_SERVICE_ACCOUNT, a: { secretKeyRef: { name: VERIFIER_SECRET } }, b: { secretKeyRef: { name: 'data-plane-builder-db-url' } } })))
      .toThrow(/Builder credential is mounted outside/)
    expect(() => assertEffectiveIsolation([], builderPolicy, [{ kind: 'job', name: 'brahma-build-pipeline-job', definition: {
      serviceAccount: BUILDER_SERVICE_ACCOUNT, a: { secretKeyRef: { name: 'data-plane-builder-db-url' } }, b: { secretKeyRef: { name: VERIFIER_SECRET } },
    } }])).toThrow(/outside the one named verification job/)
  })
  it('refuses any sealer reference on any Cloud Run surface', () => {
    expect(() => run(verifierJob({ ...exact, env: [{ name: 'GOCHARA_SEALER_DB_URL', valueFrom: { secretKeyRef: { name: 'gochara-sealer-db-url', key: 'latest' } } }] })))
      .toThrow(/Sealer credential or identity/)
    expect(() => run({ kind: 'service' as never, name: 'web', definition: { serviceAccount: 'web@example', secretKeyRef: { name: 'gochara-sealer-db-url' } } }))
      .toThrow(/Sealer credential or identity/)
  })
})

// R14-4 (Codex round 14): the preflight passed with an unexpected principal holding roles/iam.serviceAccountKeyAdmin on the verifier
// service account while ZERO keys existed — because its permission set omitted key creation and its filter was impersonation only.
describe('R14-4: the verifier service account cannot be reached by key creation, token minting, impersonation or policy rewrite', () => {
  const STRANGER = 'user:stranger@example.com'
  const withPolicy = (bindings: { role: string; members: string[]; condition?: unknown }[]) => {
    const st = good(); st.serviceAccountPolicy = { bindings }; return st
  }
  const DEPLOYER_BINDING = { role: 'roles/iam.serviceAccountUser', members: [DEPLOYER] }

  it('ZERO existing keys + an unexpected roles/iam.serviceAccountKeyAdmin on the service account FAILS (the reproduced defect)', () => {
    const st = withPolicy([DEPLOYER_BINDING, { role: 'roles/iam.serviceAccountKeyAdmin', members: [STRANGER] }])
    expect(st.userManagedKeys).toBe(0)
    expect(() => check(st)).toThrow(/exact allow-list.*serviceAccountKeyAdmin/)
  })
  it('a custom role carrying iam.serviceAccountKeys.create / .upload / setIamPolicy fails once its permissions are resolved', () => {
    for (const permission of ['iam.serviceAccountKeys.create', 'iam.serviceAccountKeys.upload', 'iam.serviceAccounts.setIamPolicy', 'iam.serviceAccounts.getAccessToken', 'iam.serviceAccounts.actAs']) {
      const resolved = { 'projects/p/roles/custom': [permission] }
      expect(grantsServiceAccountControl('projects/p/roles/custom', resolved)).toBe(true)
      const st = withPolicy([DEPLOYER_BINDING, { role: 'projects/p/roles/custom', members: [STRANGER] }])
      expect(() => assertVerifierIsolation(projectPolicy, st, resolved, DEPLOYER, 'deployable')).toThrow(/exact allow-list/)
    }
    expect(grantsServiceAccountControl('roles/viewer', { 'roles/viewer': ['resourcemanager.projects.get'] })).toBe(false)
  })
  it('policy-rewrite capability (serviceAccountAdmin, securityAdmin, projectIamAdmin) on the service account fails', () => {
    for (const role of ['roles/iam.serviceAccountAdmin', 'roles/iam.securityAdmin', 'roles/resourcemanager.projectIamAdmin', 'roles/owner']) {
      expect(() => check(withPolicy([DEPLOYER_BINDING, { role, members: [STRANGER] }]))).toThrow(/exact allow-list/)
    }
  })
  it('the exact allow-list per phase: staged = no bindings; deployable = only serviceAccountUser for the deployer, unconditional; anything else fails', () => {
    expect(() => assertVerifierServiceAccountPolicyExact({ bindings: [] }, DEPLOYER, {}, 'staged')).not.toThrow()
    expect(() => assertVerifierServiceAccountPolicyExact(undefined, DEPLOYER, {}, 'staged')).not.toThrow()
    expect(() => assertVerifierServiceAccountPolicyExact({ bindings: [DEPLOYER_BINDING] }, DEPLOYER, {}, 'deployable')).not.toThrow()
    expect(() => assertVerifierServiceAccountPolicyExact({ bindings: [{ role: 'roles/viewer', members: [STRANGER] }] }, DEPLOYER, {}, 'deployable')).toThrow(/exact allow-list/)   // even a harmless-looking extra role
    expect(() => assertVerifierServiceAccountPolicyExact({ bindings: [DEPLOYER_BINDING, DEPLOYER_BINDING] }, DEPLOYER, {}, 'deployable')).toThrow(/exact allow-list/)
    expect(() => assertVerifierServiceAccountPolicyExact({ bindings: [{ ...DEPLOYER_BINDING, condition: { expression: 'true' } }] }, DEPLOYER, {}, 'deployable')).toThrow(/conditional binding/)
    expect(() => assertVerifierServiceAccountPolicyExact({ bindings: [DEPLOYER_BINDING] }, undefined, {}, 'deployable')).toThrow(/exact allow-list/)
  })
  it('an INHERITED binding (project / folder / organization) that can create or upload keys, mint tokens, impersonate or rewrite policy FAILS, outside the declared exceptions', () => {
    const ADMIN = 'user:owner@example.com'
    const project = process.env.GOOGLE_CLOUD_PROJECT ?? 'madhav-astrology'
    for (const [resource, role] of [[`projects/${project}`, 'roles/iam.serviceAccountKeyAdmin'], ['folders/1', 'roles/iam.serviceAccountKeyAdmin'], ['organizations/2', 'roles/iam.securityAdmin'],
                                    [`projects/${project}`, 'roles/iam.serviceAccountTokenCreator'], [`projects/${project}`, 'roles/resourcemanager.projectIamAdmin']]) {
      expect(() => assertVerifierInheritedControl([{ resource, policy: { bindings: [{ role, members: [STRANGER] }] } }], {}, ADMIN, '123', '')).toThrow(/Inherited or aggregate capability/)
    }
    // a custom/editor-style role is judged by its RESOLVED permissions
    expect(() => assertVerifierInheritedControl([{ resource: `projects/${project}`, policy: { bindings: [{ role: 'roles/editor', members: [STRANGER] }] } }],
      { 'roles/editor': ['iam.serviceAccountKeys.create'] }, ADMIN, '123', '')).toThrow(/Inherited or aggregate capability/)
    // a conditional binding is never an exception, even if declared
    expect(() => assertVerifierInheritedControl([{ resource: 'folders/1', policy: { bindings: [{ role: 'roles/iam.serviceAccountKeyAdmin', members: [STRANGER], condition: { expression: 'true' } }] } }],
      {}, ADMIN, '123', `folders/1|roles/iam.serviceAccountKeyAdmin|${STRANGER}`)).toThrow(/Inherited or aggregate capability/)
  })
  it('the NAMED control-plane exceptions pass: the declared human owner, a Google service agent, and an explicitly declared (resource|role|member) triple', () => {
    const ADMIN = 'user:owner@example.com'
    const project = process.env.GOOGLE_CLOUD_PROJECT ?? 'madhav-astrology'
    expect(() => assertVerifierInheritedControl([{ resource: `projects/${project}`, policy: { bindings: [{ role: 'roles/owner', members: [ADMIN] }] } }], {}, ADMIN, '123', '')).not.toThrow()
    expect(() => assertVerifierInheritedControl([{ resource: 'folders/1', policy: { bindings: [{ role: 'roles/iam.serviceAccountKeyAdmin', members: [STRANGER] }] } }],
      {}, ADMIN, '123', `folders/1|roles/iam.serviceAccountKeyAdmin|${STRANGER}`)).not.toThrow()
    // …but ONLY that exact triple: the same member on another resource, or another role, is still a violation
    expect(() => assertVerifierInheritedControl([{ resource: 'folders/2', policy: { bindings: [{ role: 'roles/iam.serviceAccountKeyAdmin', members: [STRANGER] }] } }],
      {}, ADMIN, '123', `folders/1|roles/iam.serviceAccountKeyAdmin|${STRANGER}`)).toThrow(/Inherited or aggregate capability/)
    // an unrelated role is never flagged
    expect(() => assertVerifierInheritedControl([{ resource: 'folders/1', policy: { bindings: [{ role: 'roles/viewer', members: [STRANGER] }] } }], { 'roles/viewer': ['resourcemanager.projects.get'] }, ADMIN, '123', '')).not.toThrow()
  })
  it('R15-1: the PHASE is explicit and enforced — zero bindings is wrong once act 10 is declared done; the deployer binding is wrong while still staged; an undeclared phase refuses', () => {
    expect(() => assertVerifierServiceAccountPolicyExact({ bindings: [] }, DEPLOYER, {}, 'deployable')).toThrow(/phase 'deployable'/)       // the act-10 postcondition
    expect(() => assertVerifierServiceAccountPolicyExact({ bindings: [DEPLOYER_BINDING] }, DEPLOYER, {}, 'staged')).toThrow(/phase 'staged'/)
    expect(() => assertVerifierIsolation(projectPolicy, good(), {}, DEPLOYER, undefined)).toThrow(/DATA_PLANE_VERIFIER_PHASE must be declared/)
  })
  it('R15-1: a CUSTOM role carrying an ancestor policy-write permission is a violation at its correct ancestor scope — with and without the exact named exception', () => {
    const ADMIN = 'user:owner@example.com'
    const project = process.env.GOOGLE_CLOUD_PROJECT ?? 'madhav-astrology'
    const cases: [string, string, string][] = [
      [`projects/${project}`, 'resourcemanager.projects.setIamPolicy', 'projects/p/roles/projectPolicyWriter'],
      ['folders/1', 'resourcemanager.folders.setIamPolicy', 'organizations/9/roles/folderPolicyWriter'],
      ['organizations/2', 'resourcemanager.organizations.setIamPolicy', 'organizations/2/roles/orgPolicyWriter'],
    ]
    for (const [resource, permission, role] of cases) {
      const resolved = { [role]: [permission] }
      expect(grantsServiceAccountControl(role, resolved)).toBe(true)
      const effective = [{ resource, policy: { bindings: [{ role, members: [STRANGER] }] } }]
      expect(() => assertVerifierInheritedControl(effective, resolved, ADMIN, '123', '')).toThrow(/Inherited or aggregate capability/)
      expect(() => assertVerifierInheritedControl(effective, resolved, ADMIN, '123', `${resource}|${role}|${STRANGER}`)).not.toThrow()       // the exact named exception
      expect(() => assertVerifierInheritedControl(effective, resolved, ADMIN, '123', `${resource}|${role}|user:other@example.com`)).toThrow(/Inherited or aggregate capability/)
    }
  })
  it('R15-1: this project\'s ID and NUMBER representations are normalised before exception comparison (an allowed service-agent / declared binding under projects/<number> is not wrongly refused)', () => {
    const ADMIN = 'user:owner@example.com'
    const project = process.env.GOOGLE_CLOUD_PROJECT ?? 'madhav-astrology'
    const byNumber = [{ resource: 'projects/123456', policy: { bindings: [{ role: 'roles/owner', members: [ADMIN] }] } }]
    expect(() => assertVerifierInheritedControl(byNumber, {}, ADMIN, '123456', '')).not.toThrow()                  // the declared owner under the NUMBER form
    const decl = [{ resource: 'projects/123456', policy: { bindings: [{ role: 'roles/iam.serviceAccountKeyAdmin', members: [STRANGER] }] } }]
    expect(() => assertVerifierInheritedControl(decl, {}, ADMIN, '123456', `projects/${project}|roles/iam.serviceAccountKeyAdmin|${STRANGER}`)).not.toThrow()   // an exception declared by ID matches the NUMBER form
    expect(() => assertVerifierInheritedControl(decl, {}, ADMIN, '999', '')).toThrow(/Inherited or aggregate capability/)                                            // another project number is NOT this project
  })
})

describe('R15-3: Cloud Run secret aliases (`run.googleapis.com/secrets`) — documented comma-separated format, resolved to canonical project + secret', () => {
  const project = process.env.GOOGLE_CLOUD_PROJECT ?? 'madhav-astrology'
  const def = (annotation: string | undefined, refName = 'gochara-verifier-db-url') => ({
    metadata: annotation === undefined ? {} : { annotations: { 'run.googleapis.com/secrets': annotation } },
    spec: { template: { spec: { serviceAccountName: 'x@example.iam.gserviceaccount.com', containers: [{ env: [{ valueFrom: { secretKeyRef: { name: refName, key: 'latest' } } }] }] } } },
  })
  it('parses the SDK\'s normal comma-separated format (not JSON)', () => {
    expect(parseSecretsAnnotation(`a:projects/${project}/secrets/s1,b:projects/other/secrets/s2`)).toEqual([
      { alias: 'a', canonical: 's1' }, { alias: 'b', canonical: 'projects/other/secrets/s2' }])
    expect(() => extractRunIdentityAndSecrets(def(`gochara-verifier-db-url:projects/${project}/secrets/gochara-verifier-db-url`))).not.toThrow()
  })
  it('a FOREIGN-project alias is inventoried as the foreign secret and the alias reference counts as it — never as the expected local name', () => {
    const inv = extractRunIdentityAndSecrets(def('gochara-verifier-db-url:projects/foreign-project/secrets/another-database'))
    expect(inv.secrets).toEqual(['projects/foreign-project/secrets/another-database'])
    expect(inv.secrets).not.toContain('gochara-verifier-db-url')
  })
  it('a same-project alias resolves to the bare secret name; by NUMBER too when the project number is known', () => {
    expect(extractRunIdentityAndSecrets(def(`alias1:projects/${project}/secrets/real-secret`, 'alias1')).secrets).toEqual(['real-secret'])
    expect(parseSecretsAnnotation('alias1:projects/123456/secrets/real-secret', '123456')).toEqual([{ alias: 'alias1', canonical: 'real-secret' }])
  })
  it('duplicate-but-conflicting aliases and malformed entries refuse; an identical repeat is fine', () => {
    expect(() => parseSecretsAnnotation(`a:projects/${project}/secrets/s1,a:projects/${project}/secrets/s2`)).toThrow(/two different secrets/)
    expect(() => parseSecretsAnnotation(`a:projects/${project}/secrets/s1,a:projects/${project}/secrets/s1`)).not.toThrow()
    for (const bad of ['', 'a', 'a:', ':projects/p/secrets/s', '{"a":"s"}', 'a:projects/p/secrets/s,', 'a:projects/p/notsecrets/s', 'a b:s']) {
      expect(() => parseSecretsAnnotation(bad)).toThrow()
    }
  })
  it('an annotation-bearing resource elsewhere no longer makes the inventory refuse with "not valid JSON"', () => {
    expect(() => extractRunIdentityAndSecrets(def(`x:projects/${project}/secrets/y`, 'x'))).not.toThrow()
  })
})


describe('deploy.yml wires the preflight\'s operator-declared inputs (Fable F-R16-1 / F-R16-2)', () => {
  const deploy = readFileSync(resolve(__dirname, '../../../.github/workflows/deploy.yml'), 'utf8')
  const stepsRunningPreflight = deploy.split(/\n {6}- /).filter((blk) => blk.includes('data-plane-secret-isolation-preflight'))
  it('every routine step that runs the isolation preflight passes the phase AND the control-exceptions variables', () => {
    expect(stepsRunningPreflight.length).toBeGreaterThanOrEqual(4)
    for (const blk of stepsRunningPreflight) {
      expect(blk).toContain('DATA_PLANE_VERIFIER_PHASE: ${{ vars.DATA_PLANE_VERIFIER_PHASE }}')
      expect(blk).toContain('DATA_PLANE_VERIFIER_CONTROL_EXCEPTIONS: ${{ vars.DATA_PLANE_VERIFIER_CONTROL_EXCEPTIONS }}')
    }
  })
})
