/** Temporarily bridge the Pūrṇa owner through the protected schema owner. */
import { Pool } from 'pg'
import { migratorProxyConfig } from './data-plane-protected-cutover'

const MIGRATOR_URL = 'DATA_PLANE_MIGRATOR_DATABASE_URL'

export type PurnaSchemaCapabilityAction = 'grant' | 'revoke'

export async function grantPurnaServingSchemaUsage(
  databaseUrl = process.env[MIGRATOR_URL],
): Promise<void> {
  if (!databaseUrl) {
    throw new Error(`${MIGRATOR_URL} is required for the durable Pūrṇa serving schema capability.`)
  }
  const pool = new Pool({ ...migratorProxyConfig(databaseUrl), max: 1 })
  const client = await pool.connect()
  try {
    const actor = await client.query<{ session_user: string; current_user: string; schema_owner_member: boolean }>(`
      SELECT session_user, current_user,
             pg_has_role(session_user, 'data_plane_schema_owner', 'member') AS schema_owner_member
    `)
    if (actor.rows[0]?.session_user !== 'data_plane_migrator'
      || actor.rows[0]?.current_user !== 'data_plane_migrator'
      || !actor.rows[0]?.schema_owner_member) {
      throw new Error('Pūrṇa serving schema capability requires the direct protected data_plane_migrator route.')
    }

    await client.query('BEGIN')
    await client.query('SET LOCAL ROLE data_plane_schema_owner')
    await client.query('GRANT USAGE ON SCHEMA public TO role_web_serve')
    await client.query('RESET ROLE')
    const final = await client.query<{ can_create: boolean; can_use: boolean }>(`
      SELECT has_schema_privilege('role_web_serve', 'public', 'CREATE') AS can_create,
             has_schema_privilege('role_web_serve', 'public', 'USAGE') AS can_use
    `)
    if (final.rows[0]?.can_create || !final.rows[0]?.can_use) {
      throw new Error('Pūrṇa serving role did not converge to USAGE-only public schema capability.')
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

export async function setPurnaInquirySchemaCapability(
  action: PurnaSchemaCapabilityAction,
  databaseUrl = process.env[MIGRATOR_URL],
): Promise<void> {
  if (!databaseUrl) {
    throw new Error(`${MIGRATOR_URL} is required for the temporary Pūrṇa schema capability.`)
  }
  const pool = new Pool({ ...migratorProxyConfig(databaseUrl), max: 1 })
  const client = await pool.connect()
  try {
    const actor = await client.query<{ session_user: string; current_user: string; schema_owner_member: boolean }>(`
      SELECT session_user, current_user,
             pg_has_role(session_user, 'data_plane_schema_owner', 'member') AS schema_owner_member
    `)
    if (actor.rows[0]?.session_user !== 'data_plane_migrator'
      || actor.rows[0]?.current_user !== 'data_plane_migrator'
      || !actor.rows[0]?.schema_owner_member) {
      throw new Error('Pūrṇa schema capability requires the direct protected data_plane_migrator route.')
    }

    await client.query('BEGIN')
    await client.query('SET LOCAL ROLE data_plane_schema_owner')
    if (action === 'grant') {
      const owner = await client.query<{ normalized: boolean }>(`
        SELECT EXISTS (
          SELECT 1 FROM pg_roles
           WHERE rolname='purna_inquiry_owner'
             AND NOT rolcanlogin AND NOT rolinherit AND NOT rolsuper
             AND NOT rolcreatedb AND NOT rolcreaterole
             AND NOT rolreplication AND NOT rolbypassrls
        ) AS normalized
      `)
      if (!owner.rows[0]?.normalized) {
        throw new Error('Pūrṇa owner must exist in its normalized NOLOGIN state before schema capability is granted.')
      }
      await client.query('GRANT USAGE, CREATE ON SCHEMA public TO purna_inquiry_owner')
    } else {
      await client.query(`
        DO $$ BEGIN
          IF to_regrole('purna_inquiry_owner') IS NOT NULL THEN
            REVOKE USAGE, CREATE ON SCHEMA public FROM purna_inquiry_owner;
          END IF;
        END $$
      `)
    }
    await client.query('RESET ROLE')

    const final = await client.query<{ can_create: boolean; can_use: boolean }>(`
      SELECT coalesce((
        SELECT has_schema_privilege(oid, 'public', 'CREATE')
          FROM pg_roles WHERE rolname='purna_inquiry_owner'
      ), false) AS can_create,
      coalesce((
        SELECT has_schema_privilege(oid, 'public', 'USAGE')
          FROM pg_roles WHERE rolname='purna_inquiry_owner'
      ), false) AS can_use
    `)
    const expected = action === 'grant'
    if (final.rows[0]?.can_create !== expected || final.rows[0]?.can_use !== expected) {
      throw new Error(`Pūrṇa owner schema capability did not ${action === 'grant' ? 'arm' : 'close'}.`)
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
  if (action === 'grant-serving-usage') {
    grantPurnaServingSchemaUsage()
      .then(() => process.stdout.write('Pūrṇa serving schema USAGE grant complete.\n'))
      .catch((error) => { console.error(error); process.exitCode = 1 })
  } else if (action !== 'grant' && action !== 'revoke') {
    console.error('Use grant, revoke, or grant-serving-usage for the Pūrṇa schema capability action.')
    process.exitCode = 1
  } else {
    setPurnaInquirySchemaCapability(action)
      .then(() => process.stdout.write(`Pūrṇa schema capability ${action} complete.\n`))
      .catch((error) => { console.error(error); process.exitCode = 1 })
  }
}
