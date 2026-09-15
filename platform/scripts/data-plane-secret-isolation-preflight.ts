/** Fail-closed GCP IAM gate before any protected data-plane credential is used or bound. */
import { execFileSync } from 'node:child_process'

const project = process.env.GCP_PROJECT ?? 'madhav-astrology'
export const BUILDER_SERVICE_ACCOUNT = `data-plane-builder-runtime@${project}.iam.gserviceaccount.com`
export const BUILDER_SECRET = 'data-plane-builder-db-url'

interface IamBinding { role: string; members?: string[]; condition?: unknown }
interface IamPolicy { bindings?: IamBinding[] }
interface ServiceAccount { disabled?: boolean }
interface CloudRunEntry { metadata?: { name?: string; labels?: Record<string, string> }; location?: string }
interface EffectivePolicy { resource?: string; policy?: IamPolicy }
interface ResourceAncestor { type?: string; id?: string }
type CloudRunSurface = { kind: 'service' | 'revision' | 'job'; name: string; definition: unknown }
type RolePermissions = Record<string, string[]>

const IMPERSONATION_ROLES = [
  'roles/iam.serviceAccountUser',
  'roles/iam.serviceAccountTokenCreator',
  'roles/iam.serviceAccountOpenIdTokenCreator',
  'roles/iam.workloadIdentityUser',
] as const
const SECRET_ACCESS_PERMISSION = 'secretmanager.versions.access'
const IMPERSONATION_PERMISSIONS = new Set([
  'iam.serviceAccounts.actAs','iam.serviceAccounts.getAccessToken',
  'iam.serviceAccounts.getOpenIdToken','iam.serviceAccounts.implicitDelegation',
  'iam.serviceAccounts.signBlob','iam.serviceAccounts.signJwt',
])

function grantsPermission(role: string, permission: string, resolved: RolePermissions): boolean {
  if (resolved[role]?.includes(permission)) return true
  if (permission === SECRET_ACCESS_PERMISSION && role === 'roles/secretmanager.secretAccessor') return true
  if (IMPERSONATION_PERMISSIONS.has(permission) && IMPERSONATION_ROLES.includes(role as typeof IMPERSONATION_ROLES[number])) return true
  return false
}

function grantsImpersonation(role: string, resolved: RolePermissions): boolean {
  return [...IMPERSONATION_PERMISSIONS].some((permission) => grantsPermission(role, permission, resolved))
}

export function iamSearchScopes(ancestors: ResourceAncestor[]): string[] {
  const scopes = new Set<string>([`projects/${project}`])
  for (const ancestor of ancestors) {
    if (!ancestor.type || !ancestor.id || !['project', 'folder', 'organization'].includes(ancestor.type)) {
      throw new Error('Could not resolve the complete project/folder/organization IAM ancestry.')
    }
    if (ancestor.type === 'project') scopes.add(`projects/${ancestor.id}`)
    if (ancestor.type === 'folder') scopes.add(`folders/${ancestor.id}`)
    if (ancestor.type === 'organization') scopes.add(`organizations/${ancestor.id}`)
  }
  return [...scopes]
}

export function extractRunIdentityAndSecrets(definition: unknown): { serviceAccount: string; secrets: string[] } {
  let serviceAccount = ''
  const secrets = new Set<string>()
  const addSecret = (candidate: string): void => {
    const resource = candidate.match(/(?:^|\/)secrets\/([^/:]+)(?::|\/versions\/|$)/)
    if (resource?.[1]) { secrets.add(resource[1]); return }
    const short = candidate.match(/^([A-Za-z0-9_-]+)(?::[^:]*)?$/)
    if (short?.[1]) secrets.add(short[1])
  }
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
        addSecret(name)
      }
      if ((key === 'secretName' || key === 'secret') && typeof child === 'string') addSecret(child)
      if (key === 'run.googleapis.com/secrets' && typeof child === 'string') {
        let annotation: unknown
        try { annotation = JSON.parse(child) }
        catch { throw new Error('Cloud Run secrets annotation is not valid JSON.') }
        if (!annotation || typeof annotation !== 'object' || Array.isArray(annotation)) {
          throw new Error('Cloud Run secrets annotation is not an exact object map.')
        }
        for (const secret of Object.values(annotation as Record<string, unknown>)) {
          if (typeof secret !== 'string') throw new Error('Cloud Run secrets annotation contains a non-string reference.')
          addSecret(secret)
        }
      }
      walk(child)
    }
  }
  walk(definition)
  if (!serviceAccount) throw new Error('Cloud Run definition has no exact service account.')
  return { serviceAccount, secrets: [...secrets].sort() }
}

export function assertNoLiteralCredentials(definition: unknown): void {
  const credentialKey = (key: string): boolean => /(?:^|[_./-])(?:password|passwd|token|secret|api[_-]?key|private[_-]?key|credential|database[_-]?url|db[_-]?url)(?:$|[_./-])/i
    .test(key.replace(/([a-z0-9])([A-Z])/g, '$1_$2'))
  const secretReferenceKeys = new Set(['secret', 'secretName', 'run.googleapis.com/secrets'])
  const walk = (value: unknown): void => {
    if (!value || typeof value !== 'object') return
    if (Array.isArray(value)) {
      value.forEach((child, index) => {
        if (typeof child === 'string' && /^--(?:password|passwd|token|secret|api-key|private-key|credential)$/i.test(child)
            && index + 1 < value.length && ['string','number','boolean'].includes(typeof value[index + 1])) {
          throw new Error(`Cloud Run definition contains a literal credential value after ${child}.`)
        }
        walk(child)
      })
      return
    }
    const object = value as Record<string, unknown>
    if (typeof object.name === 'string' && credentialKey(object.name)
        && ['string','number','boolean'].includes(typeof object.value)
        && String(object.value).trim()) {
      throw new Error(`Cloud Run definition contains a literal credential value for ${object.name}.`)
    }
    for (const [key, child] of Object.entries(object)) {
      if (credentialKey(key) && !secretReferenceKeys.has(key)
          && ['string','number','boolean'].includes(typeof child) && String(child).trim()) {
        throw new Error(`Cloud Run definition contains a literal credential value under ${key}.`)
      }
      if (typeof child === 'string' && (/(?:postgres(?:ql)?|mysql):\/\/[^\s]+/i.test(child)
          || /-----BEGIN [A-Z ]*PRIVATE KEY-----/.test(child)
          || /(?:--password|--token|--api-key)=\S+/i.test(child))) {
        throw new Error('Cloud Run definition contains a literal credential in env, args, or annotations.')
      }
      walk(child)
    }
  }
  walk(definition)
}

export function roleDescribeArgs(role: string): string[] {
  if (/^roles\/[A-Za-z0-9_.]+$/.test(role)) return ['iam','roles','describe',role]
  const custom = role.match(/^(projects|organizations)\/([^/]+)\/roles\/([A-Za-z0-9_.]+)$/)
  if (!custom) throw new Error(`IAM policy contains an invalid role resource: ${role}`)
  const [, parentType, parentId, roleId] = custom
  return [
    'iam','roles','describe',roleId,
    parentType === 'projects' ? '--project' : '--organization', parentId,
  ]
}

export function cloudRunLocation(entry: CloudRunEntry): string {
  const location = entry.location ?? entry.metadata?.labels?.['cloud.googleapis.com/location']
    ?? entry.metadata?.labels?.['run.googleapis.com/region']
  if (!location || !/^[a-z]+(?:-[a-z0-9]+)+[0-9]$/.test(location)) {
    throw new Error('Could not resolve the exact Cloud Run surface region.')
  }
  return location
}

export function assertSurfaceSecretGrant(serviceAccount: string, secretName: string, policy: IamPolicy, resolved: RolePermissions = {}): void {
  const member = `serviceAccount:${serviceAccount}`
  const grants = (policy.bindings ?? [])
    .filter((binding) => grantsPermission(binding.role, SECRET_ACCESS_PERMISSION, resolved) && binding.condition === undefined)
    .flatMap((binding) => binding.members ?? [])
  if (!grants.includes(member)) throw new Error(`Cloud Run identity ${serviceAccount} lacks an explicit resource grant on ${secretName}.`)
}

function gcloud<T>(args: string[]): T {
  return JSON.parse(execFileSync('gcloud', [...args, '--format=json'], { encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] })) as T
}

export function assertSecretIsolation(projectPolicy: IamPolicy, secretPolicy: IamPolicy, serviceAccount: ServiceAccount, topicPolicy?: IamPolicy, resolved: RolePermissions = {}): void {
  const broadMembers = (projectPolicy.bindings ?? [])
    .filter((binding) => grantsPermission(binding.role, SECRET_ACCESS_PERMISSION, resolved))
    .flatMap((binding) => binding.members ?? [])
  if (broadMembers.length > 0) {
    throw new Error(`Project-wide Secret Manager accessor binding remains (${broadMembers.length} member(s)); protected credential provisioning/binding is forbidden.`)
  }
  const secretAccessorBindings = (secretPolicy.bindings ?? [])
    .filter((binding) => grantsPermission(binding.role, SECRET_ACCESS_PERMISSION, resolved))
  const grants = secretAccessorBindings
    .flatMap((binding) => binding.members ?? [])
  const expected = `serviceAccount:${BUILDER_SERVICE_ACCOUNT}`
  if (secretAccessorBindings.some((binding) => binding.condition !== undefined)
      || grants.length !== 1 || grants[0] !== expected) {
    throw new Error(`Builder secret must grant accessor to exactly ${expected} and no other principal.`)
  }
  if (serviceAccount.disabled === true) throw new Error('Dedicated data-plane builder service account is disabled.')
  const projectBindings = (projectPolicy.bindings ?? [])
    .filter((binding) => (binding.members ?? []).includes(expected))
  const projectRoles = projectBindings
    .map((binding) => binding.role)
  if (projectBindings.some((binding) => binding.condition !== undefined)
      || projectRoles.length !== 1 || projectRoles[0] !== 'roles/cloudsql.client') {
    throw new Error('Dedicated builder must have exactly project role roles/cloudsql.client.')
  }
  if (topicPolicy) {
    const publisher = (topicPolicy.bindings ?? []).find((binding) => binding.role === 'roles/pubsub.publisher' && binding.condition === undefined)
    if (!(publisher?.members ?? []).includes(expected)) throw new Error('Dedicated builder lacks publisher on exact cockpit-events topic.')
  }
}

export function assertEffectiveIsolation(
  effective: EffectivePolicy[],
  builderServiceAccountPolicy: IamPolicy,
  surfaces: CloudRunSurface[],
  resolved: RolePermissions = {},
): void {
  for (const hit of effective) {
    const accessors = (hit.policy?.bindings ?? [])
      .filter((binding) => grantsPermission(binding.role, SECRET_ACCESS_PERMISSION, resolved))
      .flatMap((binding) => binding.members ?? [])
    if (accessors.length && !/\/secrets\/[^/]+$/.test(hit.resource ?? '')) {
      throw new Error(`Inherited or aggregate Secret Manager accessor binding remains on ${hit.resource ?? 'unknown resource'}.`)
    }
  }
  const inheritedImpersonators = effective.flatMap((hit) => (hit.policy?.bindings ?? [])
    .filter((binding) => grantsImpersonation(binding.role, resolved))
    .flatMap((binding) => (binding.members ?? []).map((member) => ({ resource: hit.resource ?? '', member }))))
    .filter(({ resource }) => {
      const suffix = `/serviceAccounts/${BUILDER_SERVICE_ACCOUNT}`
      const encodedSuffix = `/serviceAccounts/${encodeURIComponent(BUILDER_SERVICE_ACCOUNT)}`
      return !resource.endsWith(suffix) && !resource.endsWith(encodedSuffix)
    })
  if (inheritedImpersonators.length > 0) {
    throw new Error('Inherited or aggregate builder service-account impersonation grant remains.')
  }
  const impersonators = (builderServiceAccountPolicy.bindings ?? [])
    .filter((binding) => grantsImpersonation(binding.role, resolved))
    .flatMap((binding) => (binding.members ?? []).map((member) => `${binding.role}:${member}`))
  const expectedDeployer = process.env.DATA_PLANE_DEPLOY_PRINCIPAL
  const conditionalImpersonation = (builderServiceAccountPolicy.bindings ?? []).some((binding) =>
    grantsImpersonation(binding.role, resolved) && binding.condition !== undefined)
  if (!expectedDeployer || conditionalImpersonation || impersonators.length !== 1
      || impersonators[0] !== `roles/iam.serviceAccountUser:${expectedDeployer}`) {
    throw new Error('Builder service-account impersonation policy is not the exact deployment-only allowlist.')
  }
  for (const surface of surfaces) {
    assertNoLiteralCredentials(surface.definition)
    const serialized = JSON.stringify(surface.definition)
    const inventory = extractRunIdentityAndSecrets(surface.definition)
    if (/data-plane-(?:migrator|admin|dba)|DATA_PLANE_MIGRATOR_DATABASE_URL|DATA_PLANE_ADMIN_DATABASE_URL/i.test(serialized)) {
      throw new Error(`Deployment-only DBA/migrator credential is mounted on Cloud Run ${surface.kind}/${surface.name}.`)
    }
    const hasBuilderSecret = inventory.secrets.includes(BUILDER_SECRET)
    if (hasBuilderSecret && (surface.kind !== 'job' || surface.name !== 'brahma-build-pipeline-job'
        || inventory.serviceAccount !== BUILDER_SERVICE_ACCOUNT)) {
      throw new Error(`Builder credential is mounted outside the one named build job (${surface.kind}/${surface.name}).`)
    }
    if (inventory.serviceAccount === BUILDER_SERVICE_ACCOUNT
        && (surface.kind !== 'job' || surface.name !== 'brahma-build-pipeline-job')) {
      throw new Error(`Builder identity is used outside the one named build job (${surface.kind}/${surface.name}).`)
    }
    if (surface.kind === 'job' && surface.name === 'brahma-build-pipeline-job'
        && (!hasBuilderSecret || inventory.serviceAccount !== BUILDER_SERVICE_ACCOUNT)) {
      throw new Error('Named build job lacks the exact builder identity and secret binding.')
    }
  }
  if (surfaces.filter((surface) => surface.kind === 'job' && surface.name === 'brahma-build-pipeline-job').length !== 1) {
    throw new Error('Cloud Run inventory must contain exactly one named build job.')
  }
}

export function runDataPlaneSecretIsolationPreflight(): void {
  const projectPolicy = gcloud<IamPolicy>(['projects', 'get-iam-policy', project])
  const secretPolicy = gcloud<IamPolicy>(['secrets', 'get-iam-policy', BUILDER_SECRET, '--project', project])
  const serviceAccount = gcloud<ServiceAccount>(['iam', 'service-accounts', 'describe', BUILDER_SERVICE_ACCOUNT, '--project', project])
  const serviceAccountPolicy = gcloud<IamPolicy>(['iam', 'service-accounts', 'get-iam-policy', BUILDER_SERVICE_ACCOUNT, '--project', project])
  const topicPolicy = gcloud<IamPolicy>(['pubsub', 'topics', 'get-iam-policy', 'cockpit-events', '--project', project])
  const ancestors = gcloud<ResourceAncestor[]>(['projects', 'get-ancestors', project])
  const effective = ancestors.map((ancestor): EffectivePolicy => {
    if (ancestor.type === 'project') return { resource: `projects/${ancestor.id}`, policy: ancestor.id === project
      ? projectPolicy : gcloud<IamPolicy>(['projects','get-iam-policy',ancestor.id!]) }
    if (ancestor.type === 'folder') return { resource: `folders/${ancestor.id}`, policy: gcloud<IamPolicy>(['resource-manager','folders','get-iam-policy',ancestor.id!]) }
    if (ancestor.type === 'organization') return { resource: `organizations/${ancestor.id}`, policy: gcloud<IamPolicy>(['organizations','get-iam-policy',ancestor.id!]) }
    throw new Error('Could not load a complete ancestor IAM policy.')
  })
  const roleNames = new Set<string>()
  for (const policy of [projectPolicy,secretPolicy,serviceAccountPolicy,topicPolicy,...effective.map((hit) => hit.policy ?? {})]) {
    for (const binding of policy.bindings ?? []) roleNames.add(binding.role)
  }
  const resolved: RolePermissions = {}
  for (const role of roleNames) {
    resolved[role] = gcloud<{ includedPermissions?: string[] }>(roleDescribeArgs(role)).includedPermissions ?? []
  }
  assertSecretIsolation(projectPolicy, secretPolicy, serviceAccount, topicPolicy, resolved)

  const surfaces: CloudRunSurface[] = []
  for (const entry of gcloud<CloudRunEntry[]>(['run', 'services', 'list', '--project', project, '--platform', 'managed'])) {
    const name = entry?.metadata?.name
    if (!name) throw new Error('Could not resolve a Cloud Run service name for credential inspection.')
    surfaces.push({ kind: 'service', name, definition: gcloud<unknown>(['run', 'services', 'describe', name, '--project', project, '--region', cloudRunLocation(entry)]) })
  }
  for (const entry of gcloud<CloudRunEntry[]>(['run', 'revisions', 'list', '--project', project, '--platform', 'managed'])) {
    const name = entry?.metadata?.name
    if (!name) throw new Error('Could not resolve a Cloud Run revision name for credential inspection.')
    surfaces.push({ kind: 'revision', name, definition: gcloud<unknown>(['run', 'revisions', 'describe', name, '--project', project, '--region', cloudRunLocation(entry)]) })
  }
  for (const entry of gcloud<CloudRunEntry[]>(['run', 'jobs', 'list', '--project', project])) {
    const name = entry?.metadata?.name
    if (!name) throw new Error('Could not resolve a Cloud Run job name for credential inspection.')
    surfaces.push({ kind: 'job', name, definition: gcloud<unknown>(['run', 'jobs', 'describe', name, '--project', project, '--region', cloudRunLocation(entry)]) })
  }
  assertEffectiveIsolation(effective, serviceAccountPolicy, surfaces, resolved)
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
        resolved,
      )
      checked.add(key)
    }
  }
}

if (require.main === module) {
  try { runDataPlaneSecretIsolationPreflight() }
  catch (error) { console.error(error); process.exitCode = 1 }
}
