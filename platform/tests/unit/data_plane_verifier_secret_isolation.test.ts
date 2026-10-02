/** DP-SD-018 extension: the Gochara verification pair (verifier SA + secret + one named job). */
import { afterEach, beforeEach, describe, expect, it } from 'vitest'
import {
  assertEffectiveIsolation, assertVerifierIsolation, BUILDER_SERVICE_ACCOUNT, VERIFIER_JOB,
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
    expect(() => check(other)).toThrow(/deployment-only allowlist/)
    const wrongRole = good(); wrongRole.serviceAccountPolicy = { bindings: [{ role: 'roles/iam.serviceAccountTokenCreator', members: [DEPLOYER] }] }
    expect(() => check(wrongRole)).toThrow(/deployment-only allowlist/)
    const two = good(); two.serviceAccountPolicy = { bindings: [{ role: 'roles/iam.serviceAccountUser', members: [DEPLOYER, 'user:someone@example.com'] }] }
    expect(() => check(two)).toThrow(/deployment-only allowlist/)
    const conditional = good(); conditional.serviceAccountPolicy = { bindings: [{ role: 'roles/iam.serviceAccountUser', members: [DEPLOYER], condition: { expression: 'true' } }] }
    expect(() => check(conditional)).toThrow(/deployment-only allowlist/)
    expect(() => assertVerifierIsolation(projectPolicy, good(), {}, undefined)).toThrow(/deployment-only allowlist/)
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
