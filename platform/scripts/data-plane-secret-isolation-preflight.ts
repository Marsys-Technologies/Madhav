/** Fail-closed GCP IAM gate before any protected data-plane credential is used or bound. */
import { execFileSync } from 'node:child_process'

const project = process.env.GCP_PROJECT ?? 'madhav-astrology'
const region = process.env.GCP_REGION ?? 'asia-south1'
export const BUILDER_SERVICE_ACCOUNT = `data-plane-builder-runtime@${project}.iam.gserviceaccount.com`
export const BUILDER_SECRET = 'data-plane-builder-db-url'

interface IamBinding { role: string; members?: string[]; condition?: unknown }
interface IamPolicy { bindings?: IamBinding[] }
interface ServiceAccount { disabled?: boolean }
interface CloudRunEntry { metadata?: { name?: string } }
interface EffectivePolicy { resource?: string; policy?: IamPolicy }

export function extractRunIdentityAndSecrets(definition: unknown): { serviceAccount: string; secrets: string[] } {
  let serviceAccount = ''
  const secrets = new Set<string>()
  const walk = (value: unknown): void => {
    if (!value || typeof value !== 'object') return
    if (Array.isArray(value)) { value.forEach(walk); return }
    const object = value as Record<string, unknown>
    for (const [key, child] of Object.entries(object)) {
      if ((key === 'serviceAccountName' || key === 'serviceAccount') && typeof child === 'string' && child.includes('@')) {
        if (serviceAccount && serviceAccount !== child) throw new Error('Cloud Run definition contains multiple service accounts.')
        serviceAccount = child
      }
      if (key === 'secretKeyRef' && child && typeof child === 'object') {
        const ref = child as Record<string, unknown>
        const name = typeof ref.name === 'string' ? ref.name : typeof ref.secret === 'string' ? ref.secret : ''
        if (!name) throw new Error('Cloud Run secretKeyRef has no exact secret name.')
        secrets.add(name)
      }
      walk(child)
    }
  }
  walk(definition)
  if (!serviceAccount) throw new Error('Cloud Run definition has no exact service account.')
  return { serviceAccount, secrets: [...secrets].sort() }
}

export function assertSurfaceSecretGrant(serviceAccount: string, secretName: string, policy: IamPolicy): void {
  const member = `serviceAccount:${serviceAccount}`
  const grants = (policy.bindings ?? [])
    .filter((binding) => binding.role === 'roles/secretmanager.secretAccessor')
    .flatMap((binding) => binding.members ?? [])
  if (!grants.includes(member)) throw new Error(`Cloud Run identity ${serviceAccount} lacks an explicit resource grant on ${secretName}.`)
}

function gcloud<T>(args: string[]): T {
  return JSON.parse(execFileSync('gcloud', [...args, '--format=json'], { encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] })) as T
}

export function assertSecretIsolation(projectPolicy: IamPolicy, secretPolicy: IamPolicy, serviceAccount: ServiceAccount, topicPolicy?: IamPolicy): void {
  const broadMembers = (projectPolicy.bindings ?? [])
    .filter((binding) => binding.role === 'roles/secretmanager.secretAccessor')
    .flatMap((binding) => binding.members ?? [])
  if (broadMembers.length > 0) {
    throw new Error(`Project-wide Secret Manager accessor binding remains (${broadMembers.length} member(s)); protected credential provisioning/binding is forbidden.`)
  }
  const grants = (secretPolicy.bindings ?? [])
    .filter((binding) => binding.role === 'roles/secretmanager.secretAccessor')
    .flatMap((binding) => binding.members ?? [])
  const expected = `serviceAccount:${BUILDER_SERVICE_ACCOUNT}`
  if (grants.length !== 1 || grants[0] !== expected) {
    throw new Error(`Builder secret must grant accessor to exactly ${expected} and no other principal.`)
  }
  if (serviceAccount.disabled === true) throw new Error('Dedicated data-plane builder service account is disabled.')
  const projectRoles = (projectPolicy.bindings ?? [])
    .filter((binding) => (binding.members ?? []).includes(expected))
    .map((binding) => binding.role)
  if (projectRoles.length !== 1 || projectRoles[0] !== 'roles/cloudsql.client') {
    throw new Error('Dedicated builder must have exactly project role roles/cloudsql.client.')
  }
  if (topicPolicy) {
    const publisher = (topicPolicy.bindings ?? []).find((binding) => binding.role === 'roles/pubsub.publisher')
    if (!(publisher?.members ?? []).includes(expected)) throw new Error('Dedicated builder lacks publisher on exact cockpit-events topic.')
  }
}

export function assertEffectiveIsolation(
  effective: EffectivePolicy[],
  builderServiceAccountPolicy: IamPolicy,
  surfaces: Array<{ kind: 'revision' | 'job'; name: string; definition: unknown }>,
): void {
  for (const hit of effective) {
    const accessors = (hit.policy?.bindings ?? [])
      .filter((binding) => binding.role === 'roles/secretmanager.secretAccessor')
      .flatMap((binding) => binding.members ?? [])
    if (accessors.length && !/\/secrets\/[^/]+$/.test(hit.resource ?? '')) {
      throw new Error(`Inherited or aggregate Secret Manager accessor binding remains on ${hit.resource ?? 'unknown resource'}.`)
    }
  }
  const impersonators = (builderServiceAccountPolicy.bindings ?? [])
    .filter((binding) => ['roles/iam.serviceAccountTokenCreator','roles/iam.serviceAccountOpenIdTokenCreator'].includes(binding.role)
      || binding.role === 'roles/iam.serviceAccountUser')
    .flatMap((binding) => (binding.members ?? []).map((member) => `${binding.role}:${member}`))
  const expectedDeployer = process.env.DATA_PLANE_DEPLOY_PRINCIPAL
  if (!expectedDeployer || impersonators.some((entry) => entry !== `roles/iam.serviceAccountUser:${expectedDeployer}`)) {
    throw new Error('Builder service-account impersonation policy is not the exact deployment-only allowlist.')
  }
  for (const surface of surfaces) {
    const serialized = JSON.stringify(surface.definition)
    if (/data-plane-migrator|DATA_PLANE_MIGRATOR_DATABASE_URL|DATA_PLANE_ADMIN_DATABASE_URL/i.test(serialized)) {
      throw new Error(`Deployment-only DBA/migrator credential is mounted on Cloud Run ${surface.kind}/${surface.name}.`)
    }
    const hasBuilderSecret = serialized.includes(BUILDER_SECRET)
    if (hasBuilderSecret && (surface.kind !== 'job' || surface.name !== 'brahma-build-pipeline-job'
        || !serialized.includes(BUILDER_SERVICE_ACCOUNT))) {
      throw new Error(`Builder credential is mounted outside the one named build job (${surface.kind}/${surface.name}).`)
    }
    if (surface.kind === 'job' && surface.name === 'brahma-build-pipeline-job'
        && (!hasBuilderSecret || !serialized.includes(BUILDER_SERVICE_ACCOUNT))) {
      throw new Error('Named build job lacks the exact builder identity and secret binding.')
    }
  }
}

export function runDataPlaneSecretIsolationPreflight(): void {
  const projectPolicy = gcloud<IamPolicy>(['projects', 'get-iam-policy', project])
  const secretPolicy = gcloud<IamPolicy>(['secrets', 'get-iam-policy', BUILDER_SECRET, '--project', project])
  const serviceAccount = gcloud<ServiceAccount>(['iam', 'service-accounts', 'describe', BUILDER_SERVICE_ACCOUNT, '--project', project])
  const serviceAccountPolicy = gcloud<IamPolicy>(['iam', 'service-accounts', 'get-iam-policy', BUILDER_SERVICE_ACCOUNT, '--project', project])
  const topicPolicy = gcloud<IamPolicy>(['pubsub', 'topics', 'get-iam-policy', 'cockpit-events', '--project', project])
  assertSecretIsolation(projectPolicy, secretPolicy, serviceAccount, topicPolicy)
  const effective = gcloud<EffectivePolicy[]>([
    'asset', 'search-all-iam-policies', '--scope', `projects/${project}`,
    '--query', 'policy:roles/secretmanager.secretAccessor',
  ])

  const surfaces: Array<{ kind: 'revision' | 'job'; name: string; definition: unknown }> = []
  for (const entry of gcloud<CloudRunEntry[]>(['run', 'revisions', 'list', '--project', project, '--region', region])) {
    const name = entry?.metadata?.name
    if (!name) throw new Error('Could not resolve a Cloud Run revision name for credential inspection.')
    surfaces.push({ kind: 'revision', name, definition: gcloud<unknown>(['run', 'revisions', 'describe', name, '--project', project, '--region', region]) })
  }
  for (const entry of gcloud<CloudRunEntry[]>(['run', 'jobs', 'list', '--project', project, '--region', region])) {
    const name = entry?.metadata?.name
    if (!name) throw new Error('Could not resolve a Cloud Run job name for credential inspection.')
    surfaces.push({ kind: 'job', name, definition: gcloud<unknown>(['run', 'jobs', 'describe', name, '--project', project, '--region', region]) })
  }
  assertEffectiveIsolation(effective, serviceAccountPolicy, surfaces)
  const checked = new Set<string>()
  for (const surface of surfaces) {
    const inventory = extractRunIdentityAndSecrets(surface.definition)
    for (const secretName of inventory.secrets) {
      const key = `${inventory.serviceAccount}:${secretName}`
      if (checked.has(key)) continue
      assertSurfaceSecretGrant(
        inventory.serviceAccount,
        secretName,
        gcloud<IamPolicy>(['secrets', 'get-iam-policy', secretName, '--project', project]),
      )
      checked.add(key)
    }
  }
}

if (require.main === module) {
  try { runDataPlaneSecretIsolationPreflight() }
  catch (error) { console.error(error); process.exitCode = 1 }
}
