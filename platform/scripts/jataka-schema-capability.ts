/**
 * Arm or close the temporary public-schema capability used only by the
 * explicitly authorised Jataka 1120-1123 production migration window.
 */
import { Pool } from 'pg'
import { migratorProxyConfig } from './data-plane-protected-cutover'

const MIGRATOR_URL = 'DATA_PLANE_MIGRATOR_DATABASE_URL'

export type JatakaSchemaCapabilityAction = 'grant' | 'revoke'

export async function setJatakaSchemaCapability(
  action: JatakaSchemaCapabilityAction,
  databaseUrl = process.env[MIGRATOR_URL],
): Promise<void> {
  if (!databaseUrl) {
    throw new Error(`${MIGRATOR_URL} is required for the temporary Jataka schema capability.`)
  }

  const pool = new Pool({ ...migratorProxyConfig(databaseUrl), max: 1 })
  const client = await pool.connect()
  try {
    const actor = await client.query<{
      session_user: string
      current_user: string
      schema_owner_member: boolean
    }>(`
      SELECT session_user, current_user,
             pg_has_role(session_user, 'data_plane_schema_owner', 'member') AS schema_owner_member
    `)
    if (actor.rows[0]?.session_user !== 'data_plane_migrator'
      || actor.rows[0]?.current_user !== 'data_plane_migrator'
      || !actor.rows[0]?.schema_owner_member) {
      throw new Error('Jataka schema capability requires the direct protected data_plane_migrator route.')
    }

    await client.query('BEGIN')
    await client.query('SET LOCAL ROLE data_plane_schema_owner')

    const appRole = await client.query<{ normalized: boolean }>(`
      SELECT EXISTS (
        SELECT 1 FROM pg_roles
         WHERE rolname='amjis_app'
           AND rolcanlogin AND NOT rolinherit AND NOT rolsuper
           AND NOT rolcreatedb AND NOT rolcreaterole
           AND NOT rolreplication AND NOT rolbypassrls
      ) AS normalized
    `)
    if (!appRole.rows[0]?.normalized) {
      throw new Error('amjis_app must remain the normalized application migration role.')
    }

    const before = await client.query<{ can_create: boolean; can_use: boolean }>(`
      SELECT has_schema_privilege('amjis_app', 'public', 'CREATE') AS can_create,
             has_schema_privilege('amjis_app', 'public', 'USAGE') AS can_use
    `)
    if (action === 'grant') {
      if (before.rows[0]?.can_create) {
        throw new Error('amjis_app already has public-schema CREATE; refusing to widen an unclosed prior window.')
      }
      if (!before.rows[0]?.can_use) {
        throw new Error('amjis_app lacks its expected durable public-schema USAGE capability.')
      }
      await client.query('GRANT CREATE ON SCHEMA public TO amjis_app')
    } else {
      await client.query('REVOKE CREATE ON SCHEMA public FROM amjis_app')
      await client.query('GRANT USAGE ON SCHEMA public TO amjis_app')
    }

    await client.query('RESET ROLE')
    const final = await client.query<{ can_create: boolean; can_use: boolean }>(`
      SELECT has_schema_privilege('amjis_app', 'public', 'CREATE') AS can_create,
             has_schema_privilege('amjis_app', 'public', 'USAGE') AS can_use
    `)
    if (final.rows[0]?.can_create !== (action === 'grant') || !final.rows[0]?.can_use) {
      throw new Error(`Jataka schema capability did not ${action === 'grant' ? 'arm' : 'close'}.`)
    }
    await client.query('COMMIT')
  } catch (error) {
    await client.query('ROLLBACK').catch(() => undefined)
    throw error
  } finally {
    client.release()
    await pool.end()
  }
}

if (require.main === module) {
  const action = process.argv[2]
  if (action !== 'grant' && action !== 'revoke') {
    console.error('Use grant or revoke for the Jataka schema capability action.')
    process.exitCode = 1
  } else {
    setJatakaSchemaCapability(action)
      .then(() => process.stdout.write(`Jataka schema capability ${action} complete.\n`))
      .catch((error) => { console.error(error); process.exitCode = 1 })
  }
}
