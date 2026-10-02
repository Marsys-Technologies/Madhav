/** DP-SD-018 extension: the Gochara verification pair (verifier SA + secret + one named job). */
import { afterEach, beforeEach, describe, expect, it } from 'vitest'
import {
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
const check = (state: VerifierState, project: Parameters<typeof assertVerifierIsolation>[0] = projectPolicy) =>
  assertVerifierIsolation(project, state, {}, DEPLOYER)

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
    expect(() => check(none)).not.toThrow()
    const other = good(); other.serviceAccountPolicy = { bindings: [{ role: 'roles/iam.serviceAccountUser', members: ['user:someone@example.com'] }] }
    expect(() => check(other)).toThrow(/exact allow-list/)
    const wrongRole = good(); wrongRole.serviceAccountPolicy = { bindings: [{ role: 'roles/iam.serviceAccountTokenCreator', members: [DEPLOYER] }] }
    expect(() => check(wrongRole)).toThrow(/exact allow-list/)
    const two = good(); two.serviceAccountPolicy = { bindings: [{ role: 'roles/iam.serviceAccountUser', members: [DEPLOYER, 'user:someone@example.com'] }] }
    expect(() => check(two)).toThrow(/exact allow-list/)
    const conditional = good(); conditional.serviceAccountPolicy = { bindings: [{ role: 'roles/iam.serviceAccountUser', members: [DEPLOYER], condition: { expression: 'true' } }] }
    expect(() => check(conditional)).toThrow(/exact allow-list/)
    expect(() => assertVerifierIsolation(projectPolicy, good(), {}, undefined)).toThrow(/exact allow-list/)
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
      expect(() => assertVerifierIsolation(projectPolicy, st, resolved, DEPLOYER)).toThrow(/exact allow-list/)
    }
    expect(grantsServiceAccountControl('roles/viewer', { 'roles/viewer': ['resourcemanager.projects.get'] })).toBe(false)
  })
  it('policy-rewrite capability (serviceAccountAdmin, securityAdmin, projectIamAdmin) on the service account fails', () => {
    for (const role of ['roles/iam.serviceAccountAdmin', 'roles/iam.securityAdmin', 'roles/resourcemanager.projectIamAdmin', 'roles/owner']) {
      expect(() => check(withPolicy([DEPLOYER_BINDING, { role, members: [STRANGER] }]))).toThrow(/exact allow-list/)
    }
  })
  it('the exact allow-list per phase: staged = no bindings; deployable = only serviceAccountUser for the deployer, unconditional; anything else fails', () => {
    expect(() => assertVerifierServiceAccountPolicyExact({ bindings: [] }, DEPLOYER)).not.toThrow()
    expect(() => assertVerifierServiceAccountPolicyExact(undefined, DEPLOYER)).not.toThrow()
    expect(() => assertVerifierServiceAccountPolicyExact({ bindings: [DEPLOYER_BINDING] }, DEPLOYER)).not.toThrow()
    expect(() => assertVerifierServiceAccountPolicyExact({ bindings: [{ role: 'roles/viewer', members: [STRANGER] }] }, DEPLOYER)).toThrow(/exact allow-list/)   // even a harmless-looking extra role
    expect(() => assertVerifierServiceAccountPolicyExact({ bindings: [DEPLOYER_BINDING, DEPLOYER_BINDING] }, DEPLOYER)).toThrow(/exact allow-list/)
    expect(() => assertVerifierServiceAccountPolicyExact({ bindings: [{ ...DEPLOYER_BINDING, condition: { expression: 'true' } }] }, DEPLOYER)).toThrow(/conditional binding/)
    expect(() => assertVerifierServiceAccountPolicyExact({ bindings: [DEPLOYER_BINDING] }, undefined)).toThrow(/exact allow-list/)
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
})
