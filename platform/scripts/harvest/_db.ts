/**
 * _db.ts — shared read-only Postgres connection helper for the W1 Lane L1b harvest
 * pipeline (W-25, RETRIEVAL_PLANE_ELEVATION_PLAN §9.6-2, E1-E4 extractors).
 *
 * Deliberately NOT the app's `src/lib/db/client.ts` (that pool authenticates as the
 * app's writer role and imports `server-only`, which requires the Next.js
 * `--conditions=react-server` tsx flag and is wired for a different credential).
 * The harvest extractors connect as `retrieval_census_ro` — a SELECT-only role
 * (W0.5, brief W-18) — via the Cloud SQL Auth Proxy, exactly like a psql session.
 *
 * Connection is read from env vars so no credential is ever hardcoded or committed:
 *   HARVEST_DB_HOST      default 127.0.0.1
 *   HARVEST_DB_PORT      default 6544 (this session's chosen local proxy port —
 *                        NOT a project-wide convention; pass explicitly if you use
 *                        a different port for the Cloud SQL Auth Proxy)
 *   HARVEST_DB_USER      default retrieval_census_ro
 *   HARVEST_DB_PASSWORD  REQUIRED — fetch via:
 *                        gcloud secrets versions access latest \
 *                          --secret=retrieval-census-ro-db-password \
 *                          --project=madhav-astrology
 *   HARVEST_DB_NAME      default amjis
 *
 * Usage (each extractor):
 *   cloud-sql-proxy --port 6544 madhav-astrology:asia-south1:amjis-postgres &
 *   export HARVEST_DB_PASSWORD=$(gcloud secrets versions access latest \
 *     --secret=retrieval-census-ro-db-password --project=madhav-astrology)
 *   npx tsx scripts/harvest/e2_db_truth_extractor.ts
 */
import { Client } from 'pg'

export function harvestDbConfig() {
  const password = process.env.HARVEST_DB_PASSWORD
  if (!password) {
    throw new Error(
      'HARVEST_DB_PASSWORD not set. Fetch it via: gcloud secrets versions access latest ' +
        '--secret=retrieval-census-ro-db-password --project=madhav-astrology',
    )
  }
  return {
    host: process.env.HARVEST_DB_HOST ?? '127.0.0.1',
    port: Number(process.env.HARVEST_DB_PORT ?? '6544'),
    user: process.env.HARVEST_DB_USER ?? 'retrieval_census_ro',
    password,
    database: process.env.HARVEST_DB_NAME ?? 'amjis',
    // Cloud SQL Auth Proxy terminates TLS itself; the local hop is plaintext loopback.
    ssl: false,
  }
}

/** Open a fresh client for one script run. Caller is responsible for `.end()`. */
export async function openHarvestClient(): Promise<Client> {
  const client = new Client(harvestDbConfig())
  await client.connect()
  // Belt-and-braces: confirm we really are the read-only role before doing anything,
  // so a misconfigured env var can never silently run extraction logic against a
  // writer credential.
  const who = await client.query<{ current_user: string }>('SELECT current_user')
  const role = who.rows[0]?.current_user
  if (role !== 'retrieval_census_ro') {
    await client.end()
    throw new Error(
      `Refusing to proceed: connected as '${role}', expected 'retrieval_census_ro'. ` +
        'Harvest extractors are SELECT-only by contract (brief W-18).',
    )
  }
  return client
}
