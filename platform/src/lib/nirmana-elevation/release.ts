import 'server-only'
import { RevisionsClient, ServicesClient } from '@google-cloud/run'

const PROJECT = process.env.GOOGLE_CLOUD_PROJECT ?? 'madhav-astrology'
const REGION = process.env.GOOGLE_CLOUD_REGION ?? 'asia-south1'
const SERVICE = process.env.NIRMANA_RELEASE_SERVICE ?? 'amjis-web'
const GITHUB_REPOSITORY = 'Marsys-Technologies/Madhav'
const TIMEOUT_MS = 5_000

export type NirmanaReleaseSourceState = 'fresh' | 'unavailable' | 'unknown'

export interface NirmanaReleaseSource {
  source_id: 'github_main' | 'cloud_run_web' | 'artifact_registry_commit'
  provenance: string
  state: NirmanaReleaseSourceState
  observed_at: string | null
  age_seconds: number | null
  error_code: 'NIRMANA_RELEASE_SOURCE_UNAVAILABLE' | 'NIRMANA_RELEASE_PROVENANCE_UNAVAILABLE' | null
  error_message: string | null
}

export interface NirmanaReleaseStatus {
  release: {
    main_sha: string | null
    deployed_sha: string | null
    deployed_revision: string | null
    production_in_sync: boolean | null
    observed_at: string | null
  }
  sources: NirmanaReleaseSource[]
  gaps: string[]
}

type FetchFn = typeof fetch
type CloudRunClient = Pick<ServicesClient, 'getService'> & Pick<RevisionsClient, 'getRevision'>
type CloudRunServiceObservation = {
  trafficStatuses?: Array<{
    percent?: number | null
    revision?: string | null
    type?: string | number | null
  }> | null
  latestReadyRevision?: string | null
}

let servicesClient: ServicesClient | null = null
let revisionsClient: RevisionsClient | null = null

function cloudRunServices(): ServicesClient {
  if (!servicesClient) servicesClient = new ServicesClient()
  return servicesClient
}

function cloudRunRevisions(): RevisionsClient {
  if (!revisionsClient) revisionsClient = new RevisionsClient()
  return revisionsClient
}

function cloudRun(): CloudRunClient {
  const services = cloudRunServices()
  const revisions = cloudRunRevisions()
  return {
    getService: services.getService.bind(services),
    getRevision: revisions.getRevision.bind(revisions),
  }
}

function bounded<T>(operation: Promise<T>): Promise<T> {
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => reject(new Error(`timed out after ${TIMEOUT_MS}ms`)), TIMEOUT_MS)
    operation.then(
      (value) => {
        clearTimeout(timer)
        resolve(value)
      },
      (error: unknown) => {
        clearTimeout(timer)
        reject(error)
      },
    )
  })
}

function logSourceFailure(source_id: NirmanaReleaseSource['source_id'], cause: unknown): void {
  console.error('[nirmana-elevation] release source query failed', { source_id, cause })
}

async function loadGithubMainSha(fetchFn: FetchFn): Promise<string> {
  const apiResponse = await bounded(fetchFn(`https://api.github.com/repos/${GITHUB_REPOSITORY}/commits/main`, {
    headers: { Accept: 'application/vnd.github+json', 'User-Agent': 'madhav-nirmana-elevation' },
    cache: 'no-store',
  }))
  if (apiResponse.ok) {
    const body = await bounded(apiResponse.json() as Promise<{ sha?: unknown }>)
    if (typeof body.sha === 'string' && /^[a-f0-9]{40}$/i.test(body.sha)) return body.sha
    throw new Error('GitHub main response has no valid commit SHA')
  }

  // GitHub's unauthenticated REST quota is shared by the Cloud Run egress IP
  // and can be exhausted independently of repository availability.  The
  // commits feed is an independent, GitHub-hosted observation of the same ref.
  const feedResponse = await bounded(fetchFn(`https://github.com/${GITHUB_REPOSITORY}/commits/main.atom`, {
    headers: { Accept: 'application/atom+xml', 'User-Agent': 'madhav-nirmana-elevation' },
    cache: 'no-store',
  }))
  if (!feedResponse.ok) {
    throw new Error(`GitHub main returned HTTP ${apiResponse.status}; commits feed returned HTTP ${feedResponse.status}`)
  }
  const feed = await bounded(feedResponse.text())
  const firstEntry = feed.match(/<entry>[\s\S]*?<\/entry>/i)?.[0]
  const sha = firstEntry?.match(/<id>\s*tag:github\.com,\d+:Grit::Commit\/([a-f0-9]{40})\s*<\/id>/i)?.[1]
  if (!sha) throw new Error('GitHub commits feed has no valid main commit SHA')
  return sha
}

function realizedServingRevision(service: CloudRunServiceObservation): string {
  const active = (service.trafficStatuses ?? []).filter((target) => (target.percent ?? 0) > 0)
  const target = active.length === 1 ? active[0] : null
  const revision = target?.revision || (
    target?.type === 'TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST'
      ? service.latestReadyRevision
      : null
  )
  if (!revision) throw new Error('Cloud Run service has no single realized serving revision')
  return revision.includes('/')
    ? revision
    : `projects/${PROJECT}/locations/${REGION}/revisions/${revision}`
}

export async function loadNirmanaReleaseStatus({
  now = new Date(),
  fetchFn = fetch,
  cloudRunClient = cloudRun(),
}: {
  now?: Date
  fetchFn?: FetchFn
  cloudRunClient?: CloudRunClient
} = {}): Promise<NirmanaReleaseStatus> {
  const observed_at = now.toISOString()
  let main_sha: string | null = null
  let deployed_sha: string | null = null
  let deployed_revision: string | null = null
  const gaps: string[] = []

  const [github, cloudRun] = await Promise.all([
    (async (): Promise<NirmanaReleaseSource> => {
      try {
        main_sha = await loadGithubMainSha(fetchFn)
        return { source_id: 'github_main', provenance: 'GitHub commits API/feed', state: 'fresh', observed_at, age_seconds: 0, error_code: null, error_message: null }
      } catch (error) {
        logSourceFailure('github_main', error)
        gaps.push('Authoritative GitHub main revision is unavailable; release sync is withheld.')
        return { source_id: 'github_main', provenance: 'GitHub commits API/feed', state: 'unavailable', observed_at, age_seconds: null, error_code: 'NIRMANA_RELEASE_SOURCE_UNAVAILABLE', error_message: 'Authoritative release source is unavailable.' }
      }
    })(),
    (async (): Promise<NirmanaReleaseSource> => {
      try {
        const name = `projects/${PROJECT}/locations/${REGION}/services/${SERVICE}`
        const [service] = await bounded(cloudRunClient.getService({ name }))
        const servingRevision = realizedServingRevision(service)
        deployed_revision = servingRevision.split('/').at(-1) ?? null
        if (!deployed_revision) throw new Error('Cloud Run serving revision name is invalid')
        try {
          const [revision] = await bounded(cloudRunClient.getRevision({ name: servingRevision }))
          const commitSha = revision.labels?.['commit-sha']
          if (typeof commitSha === 'string' && /^[a-f0-9]{40}$/i.test(commitSha)) {
            deployed_sha = commitSha
          }
        } catch (error) {
          logSourceFailure('artifact_registry_commit', error)
          gaps.push('Serving Cloud Run revision provenance is unavailable; production sync is withheld.')
        }
        return { source_id: 'cloud_run_web', provenance: 'Cloud Run Service traffic via ADC', state: 'fresh', observed_at, age_seconds: 0, error_code: null, error_message: null }
      } catch (error) {
        logSourceFailure('cloud_run_web', error)
        gaps.push('Authoritative Cloud Run serving revision is unavailable; release sync is withheld.')
        return { source_id: 'cloud_run_web', provenance: 'Cloud Run Service traffic via ADC', state: 'unavailable', observed_at, age_seconds: null, error_code: 'NIRMANA_RELEASE_SOURCE_UNAVAILABLE', error_message: 'Authoritative release source is unavailable.' }
      }
    })(),
  ])

  if (!deployed_sha) gaps.push('Serving revision commit SHA is not published as immutable Cloud Run provenance; production sync is withheld.')
  const artifact: NirmanaReleaseSource = {
    source_id: 'artifact_registry_commit',
    provenance: 'Serving revision immutable commit provenance',
    state: deployed_sha ? 'fresh' : 'unknown',
    observed_at,
    age_seconds: deployed_sha ? 0 : null,
    error_code: deployed_sha ? null : 'NIRMANA_RELEASE_PROVENANCE_UNAVAILABLE',
    error_message: deployed_sha ? null : 'Immutable serving-revision commit provenance is unavailable.',
  }

  return {
    release: {
      main_sha,
      deployed_sha,
      deployed_revision,
      production_in_sync: main_sha && deployed_sha ? main_sha === deployed_sha : null,
      observed_at,
    },
    sources: [github, cloudRun, artifact],
    gaps,
  }
}
