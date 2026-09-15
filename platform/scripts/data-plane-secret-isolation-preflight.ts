/** Fail-closed GCP IAM gate before any protected data-plane credential is used or bound. */
import { execFileSync } from 'node:child_process'

const project = process.env.GCP_PROJECT ?? 'madhav-astrology'
const region = process.env.GCP_REGION ?? 'asia-south1'
export const BUILDER_SERVICE_ACCOUNT = `data-plane-builder-runtime@${project}.iam.gserviceaccount.com`
export const BUILDER_SECRET = 'data-plane-builder-db-url'

interface IamBinding { role: string; members?: string[] }
interface IamPolicy { bindings?: IamBinding[] }
interface ServiceAccount { disabled?: boolean }
interface CloudRunEntry { metadata?: { name?: string } }

function gcloud<T>(args: string[]): T {
  return JSON.parse(execFileSync('gcloud', [...args, '--format=json'], { encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] })) as T
}

export function assertSecretIsolation(projectPolicy: IamPolicy, secretPolicy: IamPolicy, serviceAccount: ServiceAccount, topicPolicy?: IamPolicy): void {
  const broad = (projectPolicy.bindings ?? []).find((binding) => binding.role === 'roles/secretmanager.secretAccessor')
  const broadMembers = broad?.members ?? []
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

export function runDataPlaneSecretIsolationPreflight(): void {
  const projectPolicy = gcloud<IamPolicy>(['projects', 'get-iam-policy', project])
  const secretPolicy = gcloud<IamPolicy>(['secrets', 'get-iam-policy', BUILDER_SECRET, '--project', project])
  const serviceAccount = gcloud<ServiceAccount>(['iam', 'service-accounts', 'describe', BUILDER_SERVICE_ACCOUNT, '--project', project])
  const topicPolicy = gcloud<IamPolicy>(['pubsub', 'topics', 'get-iam-policy', 'cockpit-events', '--project', project])
  assertSecretIsolation(projectPolicy, secretPolicy, serviceAccount, topicPolicy)

  const surfaces: Array<[string, CloudRunEntry[]]> = [
    ['services', gcloud<CloudRunEntry[]>(['run', 'services', 'list', '--project', project, '--region', region])],
    ['jobs', gcloud<CloudRunEntry[]>(['run', 'jobs', 'list', '--project', project, '--region', region])],
  ]
  for (const [kind, entries] of surfaces) {
    for (const entry of entries) {
      const name = entry?.metadata?.name
      if (!name) throw new Error(`Could not resolve a Cloud Run ${kind} name for credential inspection.`)
      const serialized = JSON.stringify(gcloud<unknown>(['run', kind, 'describe', name, '--project', project, '--region', region]))
      if (/data-plane-migrator|DATA_PLANE_MIGRATOR_DATABASE_URL/i.test(serialized)) {
        throw new Error(`Deployment-only data-plane migrator credential is mounted on Cloud Run ${kind}/${name}.`)
      }
    }
  }
}

if (require.main === module) {
  try { runDataPlaneSecretIsolationPreflight() }
  catch (error) { console.error(error); process.exitCode = 1 }
}
