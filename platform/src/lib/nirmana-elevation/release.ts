import 'server-only'
import { ServicesClient } from '@google-cloud/run'

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
  error: string | null
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
type CloudRunClient = Pick<ServicesClient, 'getService'>

let servicesClient: ServicesClient | null = null

function cloudRunServices(): ServicesClient {
  if (!servicesClient) servicesClient = new ServicesClient()
  return servicesClient
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

function message(error: unknown): string {
  return error instanceof Error ? error.message.slice(0, 240) : 'unknown release-source failure'
}

export async function loadNirmanaReleaseStatus({
  now = new Date(),
  fetchFn = fetch,
  cloudRunClient = cloudRunServices(),
}: {
  now?: Date
  fetchFn?: FetchFn
  cloudRunClient?: CloudRunClient
} = {}): Promise<NirmanaReleaseStatus> {
  const observed_at = now.toISOString()
  let main_sha: string | null = null
  let deployed_revision: string | null = null
  const gaps: string[] = []

  const [github, cloudRun] = await Promise.all([
    (async (): Promise<NirmanaReleaseSource> => {
      try {
        const response = await bounded(fetchFn(`https://api.github.com/repos/${GITHUB_REPOSITORY}/commits/main`, {
          headers: { Accept: 'application/vnd.github+json', 'User-Agent': 'madhav-nirmana-elevation' },
          cache: 'no-store',
        }))
        if (!response.ok) throw new Error(`GitHub main returned HTTP ${response.status}`)
        const body = await bounded(response.json() as Promise<{ sha?: unknown }>)
        if (typeof body.sha !== 'string' || !/^[a-f0-9]{40}$/i.test(body.sha)) throw new Error('GitHub main response has no valid commit SHA')
        main_sha = body.sha
        return { source_id: 'github_main', provenance: 'GitHub public commits API', state: 'fresh', observed_at, age_seconds: 0, error: null }
      } catch (error) {
        gaps.push('Authoritative GitHub main revision is unavailable; release sync is withheld.')
        return { source_id: 'github_main', provenance: 'GitHub public commits API', state: 'unavailable', observed_at, age_seconds: null, error: message(error) }
      }
    })(),
    (async (): Promise<NirmanaReleaseSource> => {
      try {
        const name = `projects/${PROJECT}/locations/${REGION}/services/${SERVICE}`
        const [service] = await bounded(cloudRunClient.getService({ name }))
        const active = (service.traffic ?? []).filter((target) => (target.percent ?? 0) > 0)
        const servingRevision = active.length === 1 ? active[0]?.revision : null
        if (!servingRevision) throw new Error('Cloud Run service has no single serving revision')
        deployed_revision = servingRevision.split('/').at(-1) ?? null
        if (!deployed_revision) throw new Error('Cloud Run serving revision name is invalid')
        return { source_id: 'cloud_run_web', provenance: 'Cloud Run Service traffic via ADC', state: 'fresh', observed_at, age_seconds: 0, error: null }
      } catch (error) {
        gaps.push('Authoritative Cloud Run serving revision is unavailable; release sync is withheld.')
        return { source_id: 'cloud_run_web', provenance: 'Cloud Run Service traffic via ADC', state: 'unavailable', observed_at, age_seconds: null, error: message(error) }
      }
    })(),
  ])

  gaps.push('Serving revision commit SHA is not published as immutable Cloud Run provenance; production sync is withheld.')
  const artifact: NirmanaReleaseSource = {
    source_id: 'artifact_registry_commit',
    provenance: 'Serving revision immutable commit provenance',
    state: 'unknown',
    observed_at,
    age_seconds: null,
    error: 'No immutable deployment commit SHA is present on the serving revision.',
  }

  return {
    release: { main_sha, deployed_sha: null, deployed_revision, production_in_sync: null, observed_at },
    sources: [github, cloudRun, artifact],
    gaps,
  }
}
