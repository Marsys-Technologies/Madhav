/** Fail-closed GCP IAM gate before any protected data-plane credential is used or bound. */
import { execFileSync } from 'node:child_process'

const project = process.env.GOOGLE_CLOUD_PROJECT ?? 'madhav-astrology'
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
const GCLOUD_JSON_MAX_BUFFER = 64 * 1024 * 1024
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

function isDeclaredControlPlaneAdminGrant(
  binding: IamBinding,
  member: string,
  controlPlaneAdminPrincipal: string,
): boolean {
  return /^user:[^@\s]+@[^@\s]+$/.test(controlPlaneAdminPrincipal)
    && binding.role === 'roles/owner'
    && binding.condition === undefined
    && member === controlPlaneAdminPrincipal
}

function isCanonicalGoogleServiceAgentGrant(
  binding: IamBinding,
  member: string,
  projectNumber: string,
): boolean {
  if (!/^\d+$/.test(projectNumber) || binding.condition !== undefined) return false
  const expectedByRole: Record<string, string> = {
    'roles/aiplatform.serviceAgent': `serviceAccount:service-${projectNumber}@gcp-sa-aiplatform.iam.gserviceaccount.com`,
    'roles/appengine.serviceAgent': `serviceAccount:service-${projectNumber}@gcp-gae-service.iam.gserviceaccount.com`,
    'roles/cloudbuild.serviceAgent': `serviceAccount:service-${projectNumber}@gcp-sa-cloudbuild.iam.gserviceaccount.com`,
    'roles/cloudscheduler.serviceAgent': `serviceAccount:service-${projectNumber}@gcp-sa-cloudscheduler.iam.gserviceaccount.com`,
    'roles/cloudtasks.serviceAgent': `serviceAccount:service-${projectNumber}@gcp-sa-cloudtasks.iam.gserviceaccount.com`,
    'roles/compute.instanceGroupManagerServiceAgent': `serviceAccount:${projectNumber}@cloudservices.gserviceaccount.com`,
    'roles/compute.serviceAgent': `serviceAccount:service-${projectNumber}@compute-system.iam.gserviceaccount.com`,
    'roles/container.serviceAgent': `serviceAccount:service-${projectNumber}@container-engine-robot.iam.gserviceaccount.com`,
    'roles/pubsub.serviceAgent': `serviceAccount:service-${projectNumber}@gcp-sa-pubsub.iam.gserviceaccount.com`,
    'roles/run.serviceAgent': `serviceAccount:service-${projectNumber}@serverless-robot-prod.iam.gserviceaccount.com`,
  }
  return expectedByRole[binding.role] === member
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

const scalar = (value: unknown): value is string | number | boolean =>
  ['string','number','boolean'].includes(typeof value)

export function isSensitiveCredentialName(name: string): boolean {
  const words = name
    .replace(/([a-z0-9])([A-Z])/g, '$1_$2')
    .toLowerCase()
    .split(/[^a-z0-9]+/)
    .filter(Boolean)
  const compact = words.join('')
  if (words.some((word) => [
    'password','passwd','passphrase','passcode','pgpassword','token','secret','credential',
  ].includes(word))) return true
  if (words.includes('pass')) return true
  if (words.some((word, index) =>
    (word === 'api' && words[index + 1] === 'key')
    || (word === 'private' && words[index + 1] === 'key')
    || ((word === 'database' || word === 'db') && words[index + 1] === 'url')
    || (word === 'access' && words[index + 1] === 'token')
    || (word === 'client' && words[index + 1] === 'secret'))) return true
  return /^(?:pg|db|database)?pass(?:word|wd|phrase|code)?$/.test(compact)
    || /(?:db|database|pg)pass(?:word|wd|phrase|code)?$/.test(compact)
    || /(?:access|refresh|identity|id)token$/.test(compact)
    || /clientsecret$/.test(compact)
    || /(?:api|private)key$/.test(compact)
    || /(?:database|db)url$/.test(compact)
}

function containsCredentialLiteral(value: string): boolean {
  return /(?:postgres(?:ql)?|mysql):\/\/[^\s]+/i.test(value)
    || /-----BEGIN [A-Z ]*PRIVATE KEY-----/.test(value)
    || /(?:^|\s)-{1,2}[^\s=]*(?:pass(?:word|wd)?|token|secret|api[-_]?key)[^\s=]*=\S+/i.test(value)
}

function exactSecretName(value: string): boolean {
  return /^[A-Za-z0-9_-]+$/.test(value)
    || /^projects\/(?:[A-Za-z0-9-]+|\d+)\/secrets\/[A-Za-z0-9_-]+$/.test(value)
}

function exactSecretKeyRef(value: unknown): boolean {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return false
  const ref = value as Record<string, unknown>
  const hasName = typeof ref.name === 'string' && ref.name.trim().length > 0
  const hasSecret = typeof ref.secret === 'string' && ref.secret.trim().length > 0
  if (hasName === hasSecret) return false
  const allowed = hasName ? new Set(['name','key']) : new Set(['secret','version'])
  return Object.entries(ref).every(([key, child]) =>
    allowed.has(key) && typeof child === 'string' && child.trim().length > 0
      && (key === 'name' || key === 'secret' ? exactSecretName(child) : /^[A-Za-z0-9_-]+$/.test(child)))
}

function assertEnvSurface(value: unknown): void {
  if (!Array.isArray(value)) throw new Error('Cloud Run env surface is not an exact array.')
  for (const candidate of value) {
    if (!candidate || typeof candidate !== 'object' || Array.isArray(candidate)) {
      throw new Error('Cloud Run env entry is not an exact object.')
    }
    const entry = candidate as Record<string, unknown>
    if (typeof entry.name !== 'string' || !entry.name.trim()) throw new Error('Cloud Run env entry has no exact name.')
    if (entry.name.trimStart().startsWith('#') && Object.keys(entry).length === 1) continue
    if (entry.name === 'NEXT_PUBLIC_FIREBASE_API_KEY'
        && Object.keys(entry).sort().join(',') === 'name,value'
        && typeof entry.value === 'string'
        && /^AIza[0-9A-Za-z_-]{35}$/.test(entry.value)) continue
    const sensitive = isSensitiveCredentialName(entry.name)
    const directLiteral = Object.prototype.hasOwnProperty.call(entry, 'value')
    const valueFrom = entry.valueFrom && typeof entry.valueFrom === 'object' && !Array.isArray(entry.valueFrom)
      ? (entry.valueFrom as Record<string, unknown>).secretKeyRef : undefined
    const valueSource = entry.valueSource && typeof entry.valueSource === 'object' && !Array.isArray(entry.valueSource)
      ? (entry.valueSource as Record<string, unknown>).secretKeyRef : undefined
    const references = [valueFrom,valueSource].filter((reference) => reference !== undefined)
    const sourcePresent = Object.prototype.hasOwnProperty.call(entry, 'valueFrom')
      || Object.prototype.hasOwnProperty.call(entry, 'valueSource')
    const wrapper = entry.valueFrom ?? entry.valueSource
    const exactWrapper = Boolean(wrapper && typeof wrapper === 'object' && !Array.isArray(wrapper)
      && Object.keys(wrapper as Record<string, unknown>).length === 1
      && Object.prototype.hasOwnProperty.call(wrapper, 'secretKeyRef'))
    const exactEntry = Object.keys(entry).every((key) => ['name','valueFrom','valueSource'].includes(key))
    const invalidReference = references.length !== 1 || !exactSecretKeyRef(references[0])
      || !exactWrapper || !exactEntry
    if ((sensitive && (directLiteral || invalidReference))
        || (sourcePresent && (directLiteral || invalidReference))) {
      throw new Error(`Cloud Run env ${entry.name} must use exactly one explicit Secret Manager reference and never a literal.`)
    }
    if (typeof entry.value === 'string' && containsCredentialLiteral(entry.value)) {
      throw new Error(`Cloud Run env ${entry.name} contains a literal credential.`)
    }
  }
}

function assertArgsSurface(value: unknown, surface: string): void {
  if (!Array.isArray(value) || value.some((argument) => typeof argument !== 'string')) {
    throw new Error(`Cloud Run ${surface} surface is not an exact string array.`)
  }
  for (const argument of value as string[]) {
    const assignment = argument.match(/^([^=]+)=(.*)$/s)
    const flagName = argument.match(/^-{1,2}([^=]+)(?:=.*)?$/s)?.[1]
    if ((flagName && isSensitiveCredentialName(flagName))
        || (assignment && isSensitiveCredentialName(assignment[1]))) {
      throw new Error(`Cloud Run ${surface} contains credential argument ${argument.split('=')[0]}.`)
    }
    if (containsCredentialLiteral(argument)) {
      throw new Error(`Cloud Run ${surface} contains a literal credential.`)
    }
  }
}

function assertAnnotationsSurface(value: unknown): void {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    throw new Error('Cloud Run annotations surface is not an exact object.')
  }
  for (const [key, annotation] of Object.entries(value as Record<string, unknown>)) {
    if (key === 'run.googleapis.com/secrets') {
      if (typeof annotation !== 'string') throw new Error('Cloud Run secrets annotation is not valid JSON.')
      let references: unknown
      try { references = JSON.parse(annotation) }
      catch { throw new Error('Cloud Run secrets annotation is not valid JSON.') }
      if (!references || typeof references !== 'object' || Array.isArray(references)
          || Object.values(references as Record<string, unknown>).some((reference) =>
            typeof reference !== 'string'
            || !/^(?:projects\/(?:[A-Za-z0-9-]+|\d+)\/secrets\/)?[A-Za-z0-9_-]+(?::|\/versions\/)[A-Za-z0-9_-]+$/.test(reference))) {
        throw new Error('Cloud Run secrets annotation is not an exact Secret Manager reference map.')
      }
      continue
    }
    if (typeof annotation !== 'string') {
      throw new Error(`Cloud Run annotation ${key} is not an exact string value.`)
    }
    if (isSensitiveCredentialName(key)) {
      throw new Error(`Cloud Run annotation ${key} contains a literal credential.`)
    }
    if (containsCredentialLiteral(annotation)) {
      throw new Error(`Cloud Run annotation ${key} contains a literal credential.`)
    }
  }
}

function assertVolumesSurface(value: unknown): void {
  if (!Array.isArray(value)) throw new Error('Cloud Run volumes surface is not an exact array.')
  const walk = (candidate: unknown, inSecretReference = false): void => {
    if (!candidate || typeof candidate !== 'object') return
    if (Array.isArray(candidate)) { candidate.forEach((child) => walk(child, inSecretReference)); return }
    for (const [key, child] of Object.entries(candidate as Record<string, unknown>)) {
      if (key === 'secretKeyRef') {
        if (!exactSecretKeyRef(child)) throw new Error('Cloud Run volume secretKeyRef is not an exact Secret Manager reference.')
        continue
      }
      if (key === 'secret' && child && typeof child === 'object' && !Array.isArray(child)) {
        walk(child, true)
        continue
      }
      if (inSecretReference && (key === 'secret' || key === 'secretName')) {
        if (typeof child !== 'string' || !exactSecretName(child)) {
          throw new Error('Cloud Run volume has an invalid Secret Manager reference.')
        }
        continue
      }
      if (isSensitiveCredentialName(key) && scalar(child)) {
        throw new Error(`Cloud Run volume ${key} contains a literal credential.`)
      }
      if (typeof child === 'string' && containsCredentialLiteral(child)) {
        throw new Error(`Cloud Run volume ${key} contains a literal credential.`)
      }
      walk(child, inSecretReference)
    }
  }
  walk(value)
}

export function assertNoLiteralCredentials(definition: unknown): void {
  const walk = (value: unknown): void => {
    if (!value || typeof value !== 'object') return
    if (Array.isArray(value)) { value.forEach(walk); return }
    for (const [key, child] of Object.entries(value as Record<string, unknown>)) {
      if (key === 'env') assertEnvSurface(child)
      else if (key === 'args' || key === 'command') assertArgsSurface(child, key)
      else if (key === 'annotations') assertAnnotationsSurface(child)
      else if (key === 'volumes') assertVolumesSurface(child)
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
  return JSON.parse(execFileSync('gcloud', [...args, '--format=json'], {
    encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'], maxBuffer: GCLOUD_JSON_MAX_BUFFER,
  })) as T
}

export function assertSecretIsolation(
  projectPolicy: IamPolicy,
  secretPolicy: IamPolicy,
  serviceAccount: ServiceAccount,
  topicPolicy?: IamPolicy,
  resolved: RolePermissions = {},
  controlPlaneAdminPrincipal = '',
): void {
  const broadGrants = (projectPolicy.bindings ?? [])
    .filter((binding) => grantsPermission(binding.role, SECRET_ACCESS_PERMISSION, resolved))
    .flatMap((binding) => (binding.members ?? []).map((member) => ({ binding, member })))
  const allowedAdminGrants = broadGrants.filter(({ binding, member }) =>
    isDeclaredControlPlaneAdminGrant(binding, member, controlPlaneAdminPrincipal))
  const forbiddenGrants = broadGrants.filter(({ binding, member }) =>
    !isDeclaredControlPlaneAdminGrant(binding, member, controlPlaneAdminPrincipal))
  const expectedAdminCount = controlPlaneAdminPrincipal ? 1 : 0
  if (forbiddenGrants.length > 0 || allowedAdminGrants.length !== expectedAdminCount) {
    throw new Error(`Project-wide Secret Manager accessor or equivalent secret access remains for an undeclared or runtime principal (${forbiddenGrants.length} forbidden grant(s)); protected credential provisioning/binding is forbidden.`)
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
  controlPlaneAdminPrincipal = '',
  projectNumber = '',
): void {
  for (const hit of effective) {
    const accessors = (hit.policy?.bindings ?? [])
      .filter((binding) => grantsPermission(binding.role, SECRET_ACCESS_PERMISSION, resolved))
      .flatMap((binding) => (binding.members ?? [])
        .filter((member) => !(hit.resource === `projects/${project}`
          && isDeclaredControlPlaneAdminGrant(binding, member, controlPlaneAdminPrincipal))))
    if (accessors.length && !/\/secrets\/[^/]+$/.test(hit.resource ?? '')) {
      throw new Error(`Inherited or aggregate Secret Manager accessor binding remains on ${hit.resource ?? 'unknown resource'}.`)
    }
  }
  const inheritedImpersonators = effective.flatMap((hit) => (hit.policy?.bindings ?? [])
    .filter((binding) => grantsImpersonation(binding.role, resolved))
    .flatMap((binding) => (binding.members ?? []).map((member) => ({
      resource: hit.resource ?? '', member, binding,
    }))))
    .filter(({ resource }) => {
      const suffix = `/serviceAccounts/${BUILDER_SERVICE_ACCOUNT}`
      const encodedSuffix = `/serviceAccounts/${encodeURIComponent(BUILDER_SERVICE_ACCOUNT)}`
      return !resource.endsWith(suffix) && !resource.endsWith(encodedSuffix)
    })
    .filter(({ resource, member, binding }) => !(resource === `projects/${project}`
      && (isDeclaredControlPlaneAdminGrant(binding, member, controlPlaneAdminPrincipal)
        || isCanonicalGoogleServiceAgentGrant(binding, member, projectNumber))))
  if (inheritedImpersonators.length > 0) {
    const detail = inheritedImpersonators
      .map(({ resource, member, binding }) => `${resource}:${binding.role}:${member}`)
      .sort().join(', ')
    throw new Error(`Inherited or aggregate builder service-account impersonation grant remains: ${detail}`)
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
    if (surface.kind !== 'revision') {
      try { assertNoLiteralCredentials(surface.definition) }
      catch (error) {
        const message = error instanceof Error ? error.message : String(error)
        throw new Error(`Cloud Run ${surface.kind}/${surface.name} credential surface is invalid: ${message}`)
      }
    }
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
  const controlPlaneAdminPrincipal = process.env.DATA_PLANE_CONTROL_PLANE_ADMIN_PRINCIPAL?.trim() ?? ''
  if (!/^user:[^@\s]+@[^@\s]+$/.test(controlPlaneAdminPrincipal)) {
    throw new Error('DATA_PLANE_CONTROL_PLANE_ADMIN_PRINCIPAL must name the exact human user principal that owns the project control plane.')
  }
  const projectPolicy = gcloud<IamPolicy>(['projects', 'get-iam-policy', project])
  const projectIdentity = gcloud<{ projectNumber?: string }>(['projects', 'describe', project])
  const projectNumber = projectIdentity.projectNumber?.trim() ?? ''
  if (!/^\d+$/.test(projectNumber)) throw new Error('Could not resolve the exact GCP project number.')
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
  assertSecretIsolation(projectPolicy, secretPolicy, serviceAccount, topicPolicy, resolved, controlPlaneAdminPrincipal)

  const surfaces: CloudRunSurface[] = []
  for (const entry of gcloud<CloudRunEntry[]>(['run', 'services', 'list', '--project', project, '--platform', 'managed'])) {
    const name = entry?.metadata?.name
    if (!name) throw new Error('Could not resolve a Cloud Run service name for credential inspection.')
    surfaces.push({ kind: 'service', name, definition: gcloud<unknown>(['run', 'services', 'describe', name, '--project', project, '--region', cloudRunLocation(entry)]) })
  }
  for (const entry of gcloud<CloudRunEntry[]>(['run', 'revisions', 'list', '--project', project, '--platform', 'managed'])) {
    const name = entry?.metadata?.name
    if (!name) throw new Error('Could not resolve a Cloud Run revision name for credential inspection.')
    // The list response already contains the complete immutable revision spec.
    // Reusing it avoids thousands of redundant describe calls without sampling
    // or reducing the inventory.
    surfaces.push({ kind: 'revision', name, definition: entry })
  }
  for (const entry of gcloud<CloudRunEntry[]>(['run', 'jobs', 'list', '--project', project])) {
    const name = entry?.metadata?.name
    if (!name) throw new Error('Could not resolve a Cloud Run job name for credential inspection.')
    surfaces.push({ kind: 'job', name, definition: gcloud<unknown>(['run', 'jobs', 'describe', name, '--project', project, '--region', cloudRunLocation(entry)]) })
  }
  assertEffectiveIsolation(
    effective, serviceAccountPolicy, surfaces, resolved, controlPlaneAdminPrincipal, projectNumber,
  )
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
