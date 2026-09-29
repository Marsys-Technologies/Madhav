/**
 * Suvarṇa D6 one-shot administrator bootstrap: a genuinely read-only login `suvarna_reader`.
 *
 *   SUVARNA_READER_ADMIN_DATABASE_URL=postgres://postgres:…@127.0.0.1:5433/amjis \
 *     npx tsx scripts/suvarna-reader-bootstrap.ts [--dry-run | --apply]
 *       [--data-plane-gate-amended] [--accept-secdef=<schema.fn(argtypes)>]…
 *
 * Why a privileged one-shot and not a migration: the routine migration runner (amjis_app) lost
 * CREATEROLE and table-grant rights in the data-plane / Nirmāṇa ownership handoffs. This follows the
 * administrator-bootstrap pattern of data-plane-ownership-preflight.ts: a dedicated admin URL that
 * authenticates directly as postgres, every grant made AS the object's owner (SET LOCAL ROLE), any
 * owner membership the admin lacks added only for the transaction and removed before it can commit.
 *
 * --dry-run (default): everything runs inside one transaction, the plan and every verification result
 *   are printed, then ROLLBACK. Nothing persists; no secret or file is written.
 * --apply: the same transaction; if and only if every verification passes, the password is added to
 *   Secret Manager, the transaction COMMITs, the new login is proven by connecting as it, and only
 *   then is ~/.config/suvarna/pgenv.sh replaced (previous file kept as pgenv.app-login.bak).
 * --rollback [--dry-run | --apply]: revokes every grant the reader holds AS ITS GRANTOR, drops the
 *   role, proves the same invariants, and (apply) restores pgenv.sh from pgenv.app-login.bak.
 *
 * The password is generated here (crypto random), never printed or logged. The database receives only
 * a client-computed SCRAM-SHA-256 verifier, so no statement text or server log ever carries it.
 *
 * DATA-PLANE GATE: `data-plane-ownership-status.ts` (run by every deploy) pins the public-schema ACL
 * exactly and allow-lists the grantees of every protected L1/L2 table. A reader with USAGE on public
 * and SELECT on those tables makes that gate fail the next deploy. Without --data-plane-gate-amended
 * this script therefore reports a DATA-PLANE GATE CONFLICT and fails; pass the flag only after a
 * reviewed amendment that tolerates `suvarna_reader` has been deployed (see the D6 runbook).
 */
import { spawnSync } from 'node:child_process'
import { createHash, createHmac, pbkdf2Sync, randomBytes, randomInt } from 'node:crypto'
import {
  chmodSync, closeSync, constants as fsConstants, copyFileSync, existsSync, fsyncSync, mkdirSync,
  openSync, readFileSync, renameSync, unlinkSync, writeSync,
} from 'node:fs'
import { homedir } from 'node:os'
import { join } from 'node:path'
import { Pool, type PoolClient } from 'pg'
import { L1_ACTIVE_TABLES, L2_ACTIVE_TABLES } from './data-plane-ownership-preflight'

export const ADMIN_URL = 'SUVARNA_READER_ADMIN_DATABASE_URL'
export const READER = 'suvarna_reader'
export const SECRET_NAME = 'suvarna-reader-password'
export const GCP_PROJECT = 'madhav-astrology'
const ADMIN_ROLE = 'postgres'
const CENSUS_ROLE = 'retrieval_census_ro'
const CONNECTION_LIMIT = 10
const PASSWORD_LENGTH = 48
const PASSWORD_ALPHABET = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
const READ_SCHEMAS = ['public', 'nirmana_evidence'] as const

/** Always granted (must exist): control-plane tables Suvarṇa reads, plus `chart_grants` because the
 *  `charts` RLS policy reads it as the querying role. `charts` holds birth-data PII (reported). */
export const FIXED_READ_SET = [
  'asset_registry', 'asset_throughput', 'build_runs', 'build_run_assets',
  'asset_provenance_receipts', '_migrations_applied', 'charts', 'chart_grants',
] as const

/** Never granted, in public/nirmana_evidence (SQL LIKE patterns; schema `auth` is denied wholesale).
 *  Widening needs a reviewed edit of this list — that edit IS the native's approval. `mcp_api_keys` is
 *  added beyond the review's list: it holds API-key material of the same class as `mcp_oauth_%`. */
export const DENY_PATTERNS = [
  'profiles', 'access_requests', 'conversation_%', 'mcp_oauth_%', 'ai_provider_connections',
  'mv_session_summary', 'query_baseline_stats', 'mcp_api_keys',
] as const

const PII_RELATIONS = ['charts'] as const
const PII_COLUMN_REGEX =
  '(^|_)(email|phone|mobile|birth|dob|first_name|last_name|full_name|display_name|address|ip|uid|password|token|secret|api_key|latitude|longitude)(_|$)'

const NIRMANA_ROLES = ['nirmana_evidence_owner', 'nirmana_evidence_ingress_writer', 'nirmana_campaign_control_writer', 'nirmana_migrator'] as const
const NIRMANA_TABLES = ['nirmana_elevation_campaign_definitions', 'nirmana_elevation_campaign_events', 'nirmana_elevation_asset_labels'] as const
const NIRMANA_FUNCTIONS = [
  'nirmana_elevation_prevent_event_mutation', 'nirmana_elevation_guard_definition_mutation',
  'nirmana_elevation_prevent_label_mutation', 'nirmana_elevation_guard_server_reconstructed_insert',
  'nirmana_elevation_guard_control_writer', 'nirmana_elevation_prevent_campaign_truncate',
] as const
const NIRMANA_MARKER = '633_nirmana_evidence_writer_ownership.sql'
const DATA_PLANE_MARKERS = ['1035_data_plane_l1_producer_history.sql', '1036_data_plane_l2_producer_generations.sql'] as const
const PURNA_MARKER = '1040_planner_inquiry_successor_lifecycle.sql'

// ------------------------------------------------------------------------------------------------
// Pure helpers (exported for review/testing; no I/O)
// ------------------------------------------------------------------------------------------------

export type Mode = 'dry-run' | 'apply'
export interface Options { mode: Mode; rollback: boolean; dataPlaneGateAmended: boolean; acceptSecdef: string[] }

export function parseArgs(argv: readonly string[]): Options | 'help' {
  let mode: Mode | null = null
  let rollback = false
  let dataPlaneGateAmended = false
  const acceptSecdef: string[] = []
  for (const arg of argv) {
    if (arg === '--help' || arg === '-h') return 'help'
    if (arg === '--dry-run' || arg === '--apply') {
      const next: Mode = arg === '--apply' ? 'apply' : 'dry-run'
      if (mode && mode !== next) throw new Error('Choose one of --dry-run or --apply.')
      mode = next
    } else if (arg === '--rollback') {
      rollback = true
    } else if (arg === '--data-plane-gate-amended') {
      dataPlaneGateAmended = true
    } else if (arg.startsWith('--accept-secdef=') && arg.length > '--accept-secdef='.length) {
      acceptSecdef.push(arg.slice('--accept-secdef='.length).trim())
    } else {
      throw new Error(`Unknown argument: ${arg.slice(0, 40)}`)
    }
  }
  if (rollback && (dataPlaneGateAmended || acceptSecdef.length)) {
    throw new Error('--rollback takes only --dry-run or --apply.')
  }
  return { mode: mode ?? 'dry-run', rollback, dataPlaneGateAmended, acceptSecdef }
}

export interface AdminRoute { host: string; port: number; database: string }

const FORBIDDEN_QUERY_KEYS = new Set([
  'database', 'dbname', 'host', 'hostaddr', 'password', 'port', 'service', 'user', 'username', 'options',
])

/** The admin URL must authenticate directly as postgres through the local proxy. Nothing about the
 *  URL (which carries the admin password) is ever printed. */
export function validateAdminRoute(value: string | undefined): AdminRoute {
  if (!value) throw new Error(`${ADMIN_URL} is required (a postgres URL to the local Cloud SQL proxy).`)
  let route: URL
  try { route = new URL(value) } catch { throw new Error(`${ADMIN_URL} must be a valid PostgreSQL URL.`) }
  const database = decodeURIComponent(route.pathname.replace(/^\//, ''))
  const hasForbiddenQuery = [...route.searchParams.keys()].some((key) => FORBIDDEN_QUERY_KEYS.has(key.toLowerCase()))
  if (!['postgres:', 'postgresql:'].includes(route.protocol)
    || route.hostname !== '127.0.0.1'
    || decodeURIComponent(route.username) !== ADMIN_ROLE
    || !/^[A-Za-z0-9_]+$/.test(database)
    || hasForbiddenQuery
    || route.hash !== '') {
    throw new Error(`${ADMIN_URL} must authenticate as ${ADMIN_ROLE} through 127.0.0.1 to a plain database name, with no routing/principal query overrides.`)
  }
  return { host: route.hostname, port: Number(route.port || '5432'), database }
}

export function generatePassword(length = PASSWORD_LENGTH): string {
  let out = ''
  for (let i = 0; i < length; i += 1) out += PASSWORD_ALPHABET[randomInt(PASSWORD_ALPHABET.length)]
  return out
}

/** RFC 5802/7677 SCRAM-SHA-256 verifier in PostgreSQL's stored format. The generated password is
 *  ASCII alphanumeric, so SASLprep is the identity and PostgreSQL derives the identical verifier. */
export function scramVerifier(password: string, salt: Buffer = randomBytes(16), iterations = 4096): string {
  const salted = pbkdf2Sync(password, salt, iterations, 32, 'sha256')
  const clientKey = createHmac('sha256', salted).update('Client Key').digest()
  const storedKey = createHash('sha256').update(clientKey).digest()
  const serverKey = createHmac('sha256', salted).update('Server Key').digest()
  return `SCRAM-SHA-256$${iterations}:${salt.toString('base64')}$${storedKey.toString('base64')}:${serverKey.toString('base64')}`
}

export const qi = (value: string): string => `"${value.replaceAll('"', '""')}"`

export function diffLines(before: readonly string[], after: readonly string[]): { added: string[]; removed: string[] } {
  const b = new Set(before)
  const a = new Set(after)
  return { added: after.filter((line) => !b.has(line)), removed: before.filter((line) => !a.has(line)) }
}

// ------------------------------------------------------------------------------------------------
// Output (every line passes through redaction of the password and its verifier)
// ------------------------------------------------------------------------------------------------

class Reporter {
  private readonly secrets: string[] = []
  readonly failures: string[] = []
  protect(secret: string): void { if (secret) this.secrets.push(secret) }
  redact(text: string): string {
    let out = text
    for (const secret of this.secrets) out = out.split(secret).join('[redacted]')
    return out
  }
  line(text = ''): void { process.stdout.write(`${this.redact(text)}\n`) }
  section(title: string): void { this.line(''); this.line(`== ${title}`) }
  list(label: string, items: readonly string[], limit = 400): void {
    this.line(`   ${label} (${items.length})${items.length ? ':' : ''}`)
    for (const item of items.slice(0, limit)) this.line(`     - ${item}`)
    if (items.length > limit) this.line(`     … ${items.length - limit} more`)
  }
  check(id: string, ok: boolean, detail: string): void {
    this.line(`   ${ok ? 'PASS' : 'FAIL'}  ${id}: ${detail}`)
    if (!ok) this.failures.push(`${id}: ${detail}`)
  }
  info(id: string, detail: string): void { this.line(`   INFO  ${id}: ${detail}`) }
}

// ------------------------------------------------------------------------------------------------
// Database session helpers
// ------------------------------------------------------------------------------------------------

class Session {
  readonly temporaryMemberships: string[] = []
  constructor(readonly client: PoolClient, readonly out: Reporter) {}

  async rows<T>(sql: string, params: unknown[] = []): Promise<T[]> {
    return (await this.client.query(sql, params)).rows as T[]
  }

  async exec(sql: string): Promise<void> { await this.client.query(sql) }

  /** Run `fn` as `role` (SET LOCAL ROLE). If the admin is not already a member of `role`, a
   *  membership is granted for this transaction only and recorded for mandatory removal. */
  async asRole<T>(role: string, fn: () => Promise<T>): Promise<T> {
    if (role === ADMIN_ROLE) return fn()
    const [info] = await this.rows<{ exists: boolean; superuser: boolean; member: boolean }>(`
      SELECT EXISTS (SELECT 1 FROM pg_roles WHERE rolname=$1) AS exists,
             COALESCE((SELECT rolsuper FROM pg_roles WHERE rolname=$1), false) AS superuser,
             COALESCE((SELECT pg_has_role(session_user, oid, 'MEMBER') FROM pg_roles WHERE rolname=$1), false) AS member
    `, [role])
    if (!info?.exists) throw new Error(`Owner role ${role} does not exist.`)
    if (info.superuser) throw new Error(`Refusing to act as superuser-owned object owner ${role}.`)
    if (!info.member) {
      await this.exec(`GRANT ${qi(role)} TO ${qi(ADMIN_ROLE)}`)
      this.temporaryMemberships.push(role)
    }
    await this.exec(`SET LOCAL ROLE ${qi(role)}`)
    const result = await fn()
    await this.exec('RESET ROLE')
    return result
  }

  async removeTemporaryMemberships(): Promise<void> {
    await this.exec('RESET ROLE')
    for (const role of this.temporaryMemberships) await this.exec(`REVOKE ${qi(role)} FROM ${qi(ADMIN_ROLE)}`)
    const [left] = await this.rows<{ count: string }>(`
      SELECT count(*)::text AS count FROM pg_auth_members m
        JOIN pg_roles parent ON parent.oid=m.roleid JOIN pg_roles member ON member.oid=m.member
       WHERE member.rolname=$1 AND parent.rolname=ANY($2::text[])
    `, [ADMIN_ROLE, this.temporaryMemberships])
    if (left?.count !== '0') throw new Error('Temporary owner memberships did not converge to zero.')
  }
}

async function readerOid(s: Session): Promise<string | null> {
  const [row] = await s.rows<{ oid: string }>(`SELECT oid::text AS oid FROM pg_roles WHERE rolname=$1`, [READER])
  return row?.oid ?? null
}

// ------------------------------------------------------------------------------------------------
// Snapshots: everything this run could conceivably disturb, excluding suvarna_reader's own rows.
// ------------------------------------------------------------------------------------------------

interface Snapshot { memberships: string[]; roles: string[]; acl: string[] }

async function takeSnapshot(s: Session, reader: string | null): Promise<Snapshot> {
  const memberships = (await s.rows<{ line: string }>(`
    SELECT format('%s|%s|%s|%s', pg_get_userbyid(roleid), pg_get_userbyid(member), pg_get_userbyid(grantor), admin_option) AS line
      FROM pg_auth_members WHERE roleid IS DISTINCT FROM $1::oid AND member IS DISTINCT FROM $1::oid ORDER BY 1
  `, [reader])).map((r) => r.line)
  const roles = (await s.rows<{ line: string }>(`
    SELECT format('%s|super=%s|inherit=%s|createrole=%s|createdb=%s|login=%s|replication=%s|bypassrls=%s|connlimit=%s',
                  rolname, rolsuper, rolinherit, rolcreaterole, rolcreatedb, rolcanlogin, rolreplication, rolbypassrls, rolconnlimit) AS line
      FROM pg_roles WHERE oid IS DISTINCT FROM $1::oid ORDER BY 1
  `, [reader])).map((r) => r.line)
  // NULL ACLs are expanded to their defaults, so a GRANT that materialises an ACL does not register
  // as a change to anyone but the grantee.
  const acl = (await s.rows<{ line: string }>(`
    WITH scope AS (SELECT oid FROM pg_namespace WHERE nspname !~ '^pg_toast' AND nspname !~ '^pg_temp_'),
         user_scope AS (SELECT oid FROM scope WHERE oid NOT IN (SELECT oid FROM pg_namespace WHERE nspname IN ('pg_catalog','information_schema'))),
    entries AS (
      SELECT 'rel' AS kind, format('%I.%I', n.nspname, c.relname) AS object, a.grantor, a.grantee, a.privilege_type, a.is_grantable
        FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
        CROSS JOIN LATERAL aclexplode(COALESCE(c.relacl, acldefault(CASE WHEN c.relkind='S' THEN 's'::"char" ELSE 'r'::"char" END, c.relowner))) a
       WHERE c.relnamespace IN (SELECT oid FROM scope) AND c.relkind IN ('r','p','v','m','f','S')
      UNION ALL
      SELECT 'col', format('%I.%I(%I)', n.nspname, c.relname, at.attname), a.grantor, a.grantee, a.privilege_type, a.is_grantable
        FROM pg_attribute at JOIN pg_class c ON c.oid=at.attrelid JOIN pg_namespace n ON n.oid=c.relnamespace
        CROSS JOIN LATERAL aclexplode(at.attacl) a WHERE at.attacl IS NOT NULL
      UNION ALL
      SELECT 'nsp', n.nspname::text, a.grantor, a.grantee, a.privilege_type, a.is_grantable
        FROM pg_namespace n CROSS JOIN LATERAL aclexplode(COALESCE(n.nspacl, acldefault('n', n.nspowner))) a
      UNION ALL
      SELECT 'fn', format('%s:%s', p.oid, p.proname), a.grantor, a.grantee, a.privilege_type, a.is_grantable
        FROM pg_proc p CROSS JOIN LATERAL aclexplode(COALESCE(p.proacl, acldefault('f', p.proowner))) a
       WHERE p.pronamespace IN (SELECT oid FROM user_scope)
      UNION ALL
      SELECT 'type', format('%s:%s', t.oid, t.typname), a.grantor, a.grantee, a.privilege_type, a.is_grantable
        FROM pg_type t CROSS JOIN LATERAL aclexplode(COALESCE(t.typacl, acldefault('T', t.typowner))) a
       WHERE t.typnamespace IN (SELECT oid FROM user_scope)
      UNION ALL
      SELECT 'db', d.datname::text, a.grantor, a.grantee, a.privilege_type, a.is_grantable
        FROM pg_database d CROSS JOIN LATERAL aclexplode(COALESCE(d.datacl, acldefault('d', d.datdba))) a
      UNION ALL
      SELECT 'defacl', format('%s/%s/%s', pg_get_userbyid(d.defaclrole), d.defaclnamespace, d.defaclobjtype), a.grantor, a.grantee, a.privilege_type, a.is_grantable
        FROM pg_default_acl d CROSS JOIN LATERAL aclexplode(d.defaclacl) a
    )
    SELECT format('%s|%s|by=%s|to=%s|%s|grantable=%s', kind, object, pg_get_userbyid(grantor),
                  CASE WHEN grantee=0 THEN 'PUBLIC' ELSE pg_get_userbyid(grantee) END, privilege_type, is_grantable) AS line
      FROM entries WHERE grantee IS DISTINCT FROM $1::oid ORDER BY line
  `, [reader])).map((r) => r.line)
  return { memberships, roles, acl }
}

// ------------------------------------------------------------------------------------------------
// Handoff invariants: read-only re-implementations of what the deploy re-checks
//   N* — nirmana-evidence-ownership-preflight.ts handoffState + migration 633's attestation
//   D* — data-plane-ownership-status.ts (the deploy gate for the DP-SD-018 boundary)
//   P* — purna-inquiry-ownership-status.ts owner/serving topology
// All lookups are by OID so that no statement needs USAGE on a schema the admin cannot use.
// ------------------------------------------------------------------------------------------------

interface Invariant { id: string; ok: boolean }

async function nirmanaInvariants(s: Session): Promise<Invariant[]> {
  const [row] = await s.rows<Record<string, boolean>>(`
    WITH ids AS (
      SELECT (SELECT oid FROM pg_namespace WHERE nspname='nirmana_evidence') AS ev_ns,
             (SELECT oid FROM pg_namespace WHERE nspname='public') AS pub_ns,
             (SELECT oid FROM pg_roles WHERE rolname='amjis_app') AS app,
             (SELECT oid FROM pg_roles WHERE rolname='nirmana_evidence_owner') AS ev_owner,
             (SELECT oid FROM pg_roles WHERE rolname='nirmana_evidence_ingress_writer') AS ingress,
             (SELECT oid FROM pg_roles WHERE rolname='nirmana_campaign_control_writer') AS control,
             (SELECT oid FROM pg_roles WHERE rolname='nirmana_migrator') AS migrator
    )
    SELECT
      COALESCE(EXISTS (SELECT 1 FROM pg_roles WHERE rolname='nirmana_evidence_owner' AND NOT rolcanlogin AND NOT rolinherit
        AND NOT rolsuper AND NOT rolcreatedb AND NOT rolcreaterole AND NOT rolreplication AND NOT rolbypassrls), false) AS n1_evidence_owner_normalized,
      COALESCE(NOT EXISTS (SELECT 1 FROM pg_auth_members m JOIN pg_roles r ON r.oid=m.roleid OR r.oid=m.member
        WHERE r.rolname=ANY($1::text[])), false) AS n2_protected_roles_no_memberships,
      COALESCE(EXISTS (SELECT 1 FROM pg_namespace ns JOIN pg_roles o ON o.oid=ns.nspowner WHERE ns.nspname='nirmana_evidence' AND o.rolname='nirmana_evidence_owner')
        AND (SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace JOIN pg_roles o ON o.oid=c.relowner
             WHERE n.nspname='nirmana_evidence' AND c.relname=ANY($2::text[]) AND c.relkind IN ('r','p') AND o.rolname='nirmana_evidence_owner') = 3
        AND (SELECT count(*) FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace JOIN pg_roles o ON o.oid=p.proowner
             WHERE n.nspname='nirmana_evidence' AND p.proname=ANY($3::text[]) AND o.rolname='nirmana_evidence_owner') = 6, false) AS n3_evidence_ownership,
      COALESCE(EXISTS (SELECT 1 FROM pg_roles WHERE rolname='amjis_app' AND rolcanlogin
        AND NOT (rolinherit OR rolcreatedb OR rolcreaterole OR rolsuper OR rolreplication OR rolbypassrls)), false) AS n4_app_attributes,
      COALESCE((SELECT NOT EXISTS (SELECT 1 FROM pg_auth_members m WHERE m.roleid=ids.app OR m.member=ids.app)
        AND NOT EXISTS (SELECT 1 FROM pg_database d WHERE d.datname=current_database() AND (d.datdba=ids.app OR pg_has_role(ids.app, d.datdba, 'MEMBER')))
        AND NOT has_database_privilege(ids.app, current_database(), 'CREATE')
        AND NOT has_schema_privilege(ids.app, ids.ev_ns, 'CREATE')
        AND has_schema_privilege(ids.app, ids.ev_ns, 'USAGE') FROM ids), false) AS n5_app_no_administration,
      COALESCE(NOT EXISTS (
        WITH RECURSIVE provider_roots(oid, depth) AS (
          SELECT datdba, 0 FROM pg_database WHERE datname=current_database()
          UNION ALL
          SELECT m.member, parent.depth + 1 FROM pg_auth_members m JOIN provider_roots parent ON parent.oid=m.roleid
        )
        SELECT 1 FROM provider_roots root JOIN pg_roles role ON role.oid=root.oid
          JOIN pg_database database ON database.datname=current_database()
         WHERE NOT (root.oid=database.datdba
           OR (root.depth=1 AND role.rolname='postgres' AND NOT role.rolsuper AND NOT role.rolreplication AND NOT role.rolbypassrls)
           OR (root.depth=1 AND role.rolname IN ('cloudsqlagent','cloudsqlimportexport','cloudsqllogical')))
      ), false) AS n6_provider_topology_bounded,
      COALESCE((SELECT count(*) FROM pg_roles WHERE rolname IN ('nirmana_evidence_ingress_writer','nirmana_campaign_control_writer','nirmana_migrator')
        AND rolcanlogin AND NOT rolinherit AND NOT rolsuper AND NOT rolcreatedb AND NOT rolcreaterole AND NOT rolreplication AND NOT rolbypassrls) = 3, false) AS n7_writer_logins_normalized,
      COALESCE((SELECT NOT EXISTS (SELECT 1 FROM pg_class c WHERE c.relnamespace=ids.ev_ns AND c.relname=ANY($2::text[])
        AND (has_table_privilege(ids.app, c.oid, 'INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER') OR NOT has_table_privilege(ids.app, c.oid, 'SELECT'))) FROM ids), false) AS n8_app_select_only_on_campaign,
      COALESCE((SELECT has_schema_privilege(ids.ingress, ids.ev_ns, 'USAGE') AND has_schema_privilege(ids.control, ids.ev_ns, 'USAGE')
        AND NOT has_schema_privilege(ids.ingress, ids.ev_ns, 'CREATE') AND NOT has_schema_privilege(ids.control, ids.ev_ns, 'CREATE')
        AND NOT has_schema_privilege(ids.migrator, ids.ev_ns, 'USAGE')
        AND NOT has_schema_privilege(ids.ev_owner, ids.pub_ns, 'CREATE') AND NOT has_schema_privilege(ids.ingress, ids.pub_ns, 'CREATE')
        AND NOT has_schema_privilege(ids.control, ids.pub_ns, 'CREATE') AND NOT has_schema_privilege(ids.migrator, ids.pub_ns, 'CREATE')
        AND has_schema_privilege(ids.ingress, ids.pub_ns, 'USAGE') AND has_schema_privilege(ids.control, ids.pub_ns, 'USAGE')
        AND has_schema_privilege(ids.migrator, ids.pub_ns, 'USAGE') FROM ids), false) AS n9_writer_schema_envelopes
  `, [[...NIRMANA_ROLES], [...NIRMANA_TABLES], [...NIRMANA_FUNCTIONS]])
  return Object.entries(row ?? {}).map(([id, ok]) => ({ id, ok: ok === true }))
}

/** `tolerateReader` = the gate as it would read after an amendment admitting suvarna_reader's own
 *  SELECT/USAGE entries (and nothing else). The strict form is the gate exactly as deployed today. */
async function dataPlaneInvariants(s: Session, tolerateReader: boolean): Promise<Invariant[]> {
  const [row] = await s.rows<Record<string, boolean>>(`
    WITH pub AS (SELECT oid FROM pg_namespace WHERE nspname='public'),
    protected AS (
      SELECT c.oid, c.relname, c.relowner, c.relacl, CASE WHEN c.relname=ANY($1::text[]) THEN 'L1' ELSE 'L2' END AS layer
        FROM pg_class c WHERE c.relnamespace=(SELECT oid FROM pub) AND c.relname=ANY($1::text[] || $2::text[])
    ),
    history AS (
      SELECT c.oid, c.relname, c.relowner, c.relacl,
             CASE WHEN starts_with(c.relname,'l1_data_plane_') THEN 'L1' ELSE 'L2' END AS layer
        FROM pg_class c WHERE c.relnamespace=(SELECT oid FROM pub) AND c.relkind IN ('r','p','v','m')
         AND (starts_with(c.relname,'l1_data_plane_') OR starts_with(c.relname,'l2_data_plane_') OR c.relname='data_plane_l2_producer_generations')
    ),
    prot_actual AS (
      SELECT p.relname, p.layer, COALESCE(r.rolname,'PUBLIC') AS grantee, pg_get_userbyid(p.relowner) AS owner_name, a.privilege_type
        FROM protected p CROSS JOIN LATERAL aclexplode(COALESCE(p.relacl, acldefault('r', p.relowner))) a LEFT JOIN pg_roles r ON r.oid=a.grantee
    ),
    hist_actual AS (
      SELECT h.relname, h.layer, COALESCE(r.rolname,'PUBLIC') AS grantee, pg_get_userbyid(h.relowner) AS owner_name, a.privilege_type
        FROM history h CROSS JOIN LATERAL aclexplode(COALESCE(h.relacl, acldefault('r', h.relowner))) a LEFT JOIN pg_roles r ON r.oid=a.grantee
    ),
    allowed(grantee, privilege_type) AS (VALUES
      ('data_plane_builder','SELECT'),('data_plane_builder','INSERT'),('data_plane_builder','UPDATE'),('data_plane_builder','DELETE'),
      ('amjis_app','SELECT'),('data_plane_verifier','SELECT'),('data_plane_migrator','SELECT')
    ),
    schema_actual AS (
      SELECT COALESCE(r.rolname,'PUBLIC') AS grantee, a.privilege_type
        FROM pg_namespace n CROSS JOIN LATERAL aclexplode(COALESCE(n.nspacl, acldefault('n', n.nspowner))) a
        LEFT JOIN pg_roles r ON r.oid=a.grantee WHERE n.nspname='public'
    ),
    schema_expected(grantee, privilege_type) AS (
      SELECT * FROM (VALUES
        ('data_plane_schema_owner','USAGE'),('data_plane_schema_owner','CREATE'),
        ('data_plane_l1_owner','USAGE'),('data_plane_l1_owner','CREATE'),
        ('data_plane_l2_owner','USAGE'),('data_plane_l2_owner','CREATE'),
        ('data_plane_migrator','USAGE'),('data_plane_builder','USAGE'),
        ('data_plane_verifier','USAGE'),('amjis_app','USAGE'),('role_web_serve','USAGE')
      ) base(grantee, privilege_type)
      UNION ALL SELECT 'purna_inquiry_owner','USAGE' WHERE EXISTS (SELECT 1 FROM pg_roles WHERE rolname='purna_inquiry_owner')
      UNION ALL SELECT $3::text,'USAGE' WHERE $4::boolean AND EXISTS (SELECT 1 FROM pg_roles WHERE rolname=$3::text)
    ),
    seq_protected AS (
      SELECT DISTINCT seq.oid FROM pg_class tab
        JOIN pg_depend dep ON dep.refobjid=tab.oid AND dep.refclassid='pg_class'::regclass AND dep.classid='pg_class'::regclass AND dep.deptype IN ('a','i')
        JOIN pg_class seq ON seq.oid=dep.objid AND seq.relkind='S'
       WHERE tab.relnamespace=(SELECT oid FROM pub) AND tab.relname=ANY($1::text[] || $2::text[])
    ),
    seq_actual AS (
      SELECT p.oid, COALESCE(r.rolname,'PUBLIC') AS grantee, pg_get_userbyid(c.relowner) AS owner_name, a.privilege_type
        FROM seq_protected p JOIN pg_class c ON c.oid=p.oid
        CROSS JOIN LATERAL aclexplode(COALESCE(c.relacl, acldefault('s', c.relowner))) a LEFT JOIN pg_roles r ON r.oid=a.grantee
    ),
    seq_expected(grantee, privilege_type) AS (VALUES
      ('data_plane_builder','SELECT'),('data_plane_builder','USAGE'),('amjis_app','SELECT'),('data_plane_verifier','SELECT'),('data_plane_migrator','SELECT')
    ),
    roles AS (
      SELECT (SELECT oid FROM pg_roles WHERE rolname='amjis_app') AS app,
             (SELECT oid FROM pg_roles WHERE rolname='data_plane_builder') AS builder,
             (SELECT oid FROM pg_roles WHERE rolname='role_orchestrator') AS orchestrator
    )
    SELECT
      COALESCE((SELECT count(*) FROM pg_roles
        WHERE (rolname IN ('data_plane_schema_owner','data_plane_l1_owner','data_plane_l2_owner')
               AND NOT rolcanlogin AND NOT rolinherit AND NOT rolsuper AND NOT rolcreaterole AND NOT rolcreatedb AND NOT rolreplication AND NOT rolbypassrls)
           OR (rolname IN ('data_plane_migrator','data_plane_builder','data_plane_verifier')
               AND rolcanlogin AND NOT rolinherit AND NOT rolsuper AND NOT rolcreaterole AND NOT rolcreatedb AND NOT rolreplication AND NOT rolbypassrls)) = 6
        AND NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname LIKE 'data\\_plane\\_%' ESCAPE '\\' AND rolname <> ALL(ARRAY[
          'data_plane_schema_owner','data_plane_l1_owner','data_plane_l2_owner','data_plane_migrator','data_plane_builder','data_plane_verifier'])), false)
        AS d1_roles_normalized,
      COALESCE(pg_get_userbyid((SELECT nspowner FROM pg_namespace WHERE nspname='public'))='data_plane_schema_owner'
        AND NOT EXISTS (
          WITH controlled(role_name) AS (SELECT unnest(ARRAY['data_plane_schema_owner','data_plane_l1_owner','data_plane_l2_owner','data_plane_migrator','data_plane_builder','data_plane_verifier'])),
          actual AS (SELECT parent.rolname AS parent_role, member.rolname AS member_role FROM pg_auth_members m
                       JOIN pg_roles parent ON parent.oid=m.roleid JOIN pg_roles member ON member.oid=m.member
                      WHERE parent.rolname IN (SELECT role_name FROM controlled) OR member.rolname IN (SELECT role_name FROM controlled)),
          expected(parent_role, member_role) AS (VALUES ('data_plane_schema_owner','data_plane_migrator'),('data_plane_l1_owner','data_plane_migrator'),('data_plane_l2_owner','data_plane_migrator'))
          SELECT 1 FROM actual a FULL JOIN expected e USING (parent_role, member_role) WHERE a.parent_role IS NULL OR e.parent_role IS NULL)
        AND NOT EXISTS (
          WITH RECURSIVE reach(roleid, member) AS (
            SELECT roleid, member FROM pg_auth_members
            UNION SELECT r.roleid, m.member FROM reach r JOIN pg_auth_members m ON m.roleid=r.member)
          SELECT 1 FROM reach x JOIN pg_roles owner ON owner.oid=x.roleid JOIN pg_roles member ON member.oid=x.member
           WHERE owner.rolname IN ('data_plane_schema_owner','data_plane_l1_owner','data_plane_l2_owner') AND member.rolname<>'data_plane_migrator'), false)
        AS d2_membership_topology,
      COALESCE(NOT EXISTS (SELECT 1 FROM schema_actual a FULL JOIN schema_expected e USING (grantee, privilege_type)
        WHERE a.grantee IS NULL OR e.grantee IS NULL), false) AS d3_public_schema_acl_exact,
      COALESCE(NOT EXISTS (SELECT 1 FROM prot_actual a WHERE
          NOT EXISTS (SELECT 1 FROM allowed x WHERE x.grantee=a.grantee AND x.privilege_type=a.privilege_type)
          AND NOT (a.layer='L1' AND a.grantee='data_plane_l2_owner' AND a.privilege_type='SELECT')
          AND NOT ($4::boolean AND a.grantee=$3::text AND a.privilege_type='SELECT')
          AND a.grantee<>a.owner_name)
        AND NOT EXISTS (SELECT 1 FROM protected p CROSS JOIN allowed x
          WHERE NOT EXISTS (SELECT 1 FROM prot_actual a WHERE a.relname=p.relname AND a.grantee=x.grantee AND a.privilege_type=x.privilege_type)), false)
        AS d4_protected_table_acl,
      COALESCE(NOT EXISTS (SELECT 1 FROM hist_actual a WHERE a.grantee<>a.owner_name
          AND NOT (a.privilege_type='SELECT' AND a.grantee IN ('data_plane_builder','data_plane_verifier','data_plane_migrator','amjis_app'))
          AND NOT (a.layer='L1' AND a.grantee='data_plane_l2_owner' AND (a.privilege_type='SELECT'
               OR (a.relname='l1_data_plane_generation_heads' AND a.privilege_type='UPDATE')))
          AND NOT ($4::boolean AND a.grantee=$3::text AND a.privilege_type='SELECT'))
        AND NOT EXISTS (SELECT 1 FROM history h CROSS JOIN unnest(ARRAY['data_plane_builder','data_plane_verifier','data_plane_migrator','amjis_app']) g
          WHERE NOT EXISTS (SELECT 1 FROM hist_actual a WHERE a.relname=h.relname AND a.grantee=g AND a.privilege_type='SELECT')), false)
        AS d5_protected_history_acl,
      COALESCE(NOT EXISTS (SELECT 1 FROM seq_actual a WHERE a.grantee<>a.owner_name
          AND NOT EXISTS (SELECT 1 FROM seq_expected e WHERE e.grantee=a.grantee AND e.privilege_type=a.privilege_type))
        AND NOT EXISTS (SELECT 1 FROM seq_protected p CROSS JOIN seq_expected e
          WHERE NOT EXISTS (SELECT 1 FROM seq_actual a WHERE a.oid=p.oid AND a.grantee=e.grantee AND a.privilege_type=e.privilege_type)), false)
        AS d6_protected_sequence_acl,
      COALESCE((SELECT NOT (has_schema_privilege(roles.app, (SELECT oid FROM pub), 'CREATE')
          OR has_schema_privilege(roles.builder, (SELECT oid FROM pub), 'CREATE')
          OR EXISTS (SELECT 1 FROM protected p WHERE has_table_privilege(roles.builder, p.oid, 'TRUNCATE,TRIGGER,REFERENCES'))
          OR EXISTS (SELECT 1 FROM protected p WHERE has_table_privilege(roles.app, p.oid, 'INSERT,UPDATE,DELETE,TRUNCATE,TRIGGER'))
          OR EXISTS (SELECT 1 FROM protected p WHERE has_table_privilege(roles.orchestrator, p.oid, 'INSERT,UPDATE,DELETE,TRUNCATE,TRIGGER')))
        FROM roles), false) AS d7_no_protected_write_or_ddl
  `, [[...L1_ACTIVE_TABLES], [...L2_ACTIVE_TABLES], READER, tolerateReader])
  return Object.entries(row ?? {}).map(([id, ok]) => ({ id, ok: ok === true }))
}

async function purnaInvariants(s: Session): Promise<Invariant[]> {
  const [row] = await s.rows<Record<string, boolean>>(`
    SELECT
      COALESCE(EXISTS (SELECT 1 FROM pg_roles r WHERE r.rolname='purna_inquiry_owner'
        AND NOT r.rolcanlogin AND NOT r.rolinherit AND NOT r.rolsuper AND NOT r.rolcreatedb AND NOT r.rolcreaterole AND NOT r.rolreplication AND NOT r.rolbypassrls
        AND NOT EXISTS (SELECT 1 FROM pg_auth_members m WHERE m.roleid=r.oid OR m.member=r.oid)
        AND NOT has_schema_privilege(r.oid, (SELECT oid FROM pg_namespace WHERE nspname='public'), 'CREATE')
        AND has_schema_privilege(r.oid, (SELECT oid FROM pg_namespace WHERE nspname='public'), 'USAGE')), false) AS p1_owner_protected,
      COALESCE(EXISTS (SELECT 1 FROM pg_roles r WHERE r.rolname='amjis_inquiry_serve'
        AND r.rolcanlogin AND r.rolinherit AND NOT r.rolsuper AND NOT r.rolcreatedb AND NOT r.rolcreaterole AND NOT r.rolreplication AND NOT r.rolbypassrls
        AND (SELECT count(*) FROM pg_auth_members m WHERE m.member=r.oid) = 1
        AND EXISTS (SELECT 1 FROM pg_auth_members m JOIN pg_roles p ON p.oid=m.roleid WHERE p.rolname='role_web_serve' AND m.member=r.oid)
        AND NOT EXISTS (SELECT 1 FROM pg_auth_members m WHERE m.roleid=r.oid)), false) AS p2_serving_login_normalized,
      COALESCE((SELECT count(*) = 0 FROM pg_auth_members m JOIN pg_roles r ON r.oid=m.roleid OR r.oid=m.member
        WHERE r.rolname='purna_inquiry_bootstrap'), false) AS p3_bootstrap_no_memberships
  `)
  return Object.entries(row ?? {}).map(([id, ok]) => ({ id, ok: ok === true }))
}

interface InvariantState { nirmana: Invariant[]; dataPlaneStrict: Invariant[]; dataPlaneTolerant: Invariant[]; purna: Invariant[] }

async function invariantState(s: Session): Promise<InvariantState> {
  return {
    nirmana: await nirmanaInvariants(s),
    dataPlaneStrict: await dataPlaneInvariants(s, false),
    dataPlaneTolerant: await dataPlaneInvariants(s, true),
    purna: await purnaInvariants(s),
  }
}

// ------------------------------------------------------------------------------------------------
// The pre-existing role
// ------------------------------------------------------------------------------------------------

interface ReaderEdges { memberOf: string[]; membersOfReader: string[]; tolerated: string[] }

/** On PostgreSQL 16+, CREATE ROLE by a non-superuser CREATEROLE role auto-grants the new role back to
 *  its creator WITH ADMIN OPTION, INHERIT FALSE, SET FALSE. That one edge gives the creator no access
 *  through the reader and the reader nothing; it is tolerated and reported. (Production is 15.x.) */
async function readerEdges(s: Session, reader: string, version: number): Promise<ReaderEdges> {
  const pg16 = version >= 160000
  const edges = await s.rows<{ parent: string; member: string; admin: boolean; inherit: boolean; set: boolean }>(`
    SELECT pg_get_userbyid(roleid) AS parent, pg_get_userbyid(member) AS member, admin_option AS admin,
           ${pg16 ? 'inherit_option' : 'false'} AS inherit, ${pg16 ? 'set_option' : 'false'} AS set
      FROM pg_auth_members WHERE roleid=$1::oid OR member=$1::oid ORDER BY 1, 2
  `, [reader])
  const out: ReaderEdges = { memberOf: [], membersOfReader: [], tolerated: [] }
  for (const e of edges) {
    const label = `${e.member} ∈ ${e.parent}${e.admin ? ' (admin)' : ''}`
    if (e.member === READER) out.memberOf.push(label)
    else if (pg16 && e.member === ADMIN_ROLE && e.admin && !e.inherit && !e.set) out.tolerated.push(label)
    else out.membersOfReader.push(label)
  }
  return out
}

interface ReaderGrant { kind: string; object: string; objectOid: string; subkind: string; grantor: string; privilege: string }

async function readerGrants(s: Session, reader: string): Promise<ReaderGrant[]> {
  return s.rows<ReaderGrant>(`
    SELECT 'relation' AS kind, format('%I.%I', n.nspname, c.relname) AS object, c.oid::text AS "objectOid", c.relkind::text AS subkind,
           pg_get_userbyid(a.grantor) AS grantor, a.privilege_type AS privilege
      FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace CROSS JOIN LATERAL aclexplode(c.relacl) a WHERE a.grantee=$1::oid
    UNION ALL
    SELECT 'column', format('%I.%I(%I)', n.nspname, c.relname, at.attname), c.oid::text, '', pg_get_userbyid(a.grantor), a.privilege_type
      FROM pg_attribute at JOIN pg_class c ON c.oid=at.attrelid JOIN pg_namespace n ON n.oid=c.relnamespace
      CROSS JOIN LATERAL aclexplode(at.attacl) a WHERE a.grantee=$1::oid
    UNION ALL
    SELECT 'schema', n.nspname, n.oid::text, '', pg_get_userbyid(a.grantor), a.privilege_type
      FROM pg_namespace n CROSS JOIN LATERAL aclexplode(n.nspacl) a WHERE a.grantee=$1::oid
    UNION ALL
    SELECT 'function', p.oid::regprocedure::text, p.oid::text, '', pg_get_userbyid(a.grantor), a.privilege_type
      FROM pg_proc p CROSS JOIN LATERAL aclexplode(p.proacl) a WHERE a.grantee=$1::oid
    UNION ALL
    SELECT 'type', t.oid::regtype::text, t.oid::text, '', pg_get_userbyid(a.grantor), a.privilege_type
      FROM pg_type t CROSS JOIN LATERAL aclexplode(t.typacl) a WHERE a.grantee=$1::oid
    UNION ALL
    SELECT 'database', d.datname, d.oid::text, CASE WHEN d.datname=current_database() THEN 'current' ELSE 'other' END,
           pg_get_userbyid(a.grantor), a.privilege_type
      FROM pg_database d CROSS JOIN LATERAL aclexplode(d.datacl) a WHERE a.grantee=$1::oid
    UNION ALL
    SELECT 'default_acl', format('%s/%s/%s', pg_get_userbyid(d.defaclrole), d.defaclnamespace, d.defaclobjtype), '', '',
           pg_get_userbyid(a.grantor), a.privilege_type
      FROM pg_default_acl d CROSS JOIN LATERAL aclexplode(d.defaclacl) a WHERE a.grantee=$1::oid
    ORDER BY 1, 2, 6
  `, [reader])
}

/** Only the shapes this script itself creates are acceptable on a pre-existing reader. */
function unexpectedReaderGrants(grants: readonly ReaderGrant[]): ReaderGrant[] {
  return grants.filter((g) => !(
    (g.kind === 'relation' && g.privilege === 'SELECT' && ['r', 'p', 'v', 'm', 'f'].includes(g.subkind))
    || (g.kind === 'schema' && g.privilege === 'USAGE' && (READ_SCHEMAS as readonly string[]).includes(g.object))
    || (g.kind === 'database' && g.subkind === 'current' && g.privilege === 'CONNECT')
  ))
}

async function inspectExistingReader(s: Session, reader: string, version: number): Promise<ReaderGrant[]> {
  const [attrs] = await s.rows<{ elevated: boolean }>(`
    SELECT rolsuper OR rolcreaterole OR rolcreatedb OR rolreplication OR rolbypassrls AS elevated FROM pg_roles WHERE oid=$1::oid
  `, [reader])
  if (attrs?.elevated) throw new Error(`Refusing pre-existing ${READER}: it carries elevated role attributes.`)
  const edges = await readerEdges(s, reader, version)
  if (edges.memberOf.length || edges.membersOfReader.length) {
    throw new Error(`Refusing pre-existing ${READER}: it has role memberships (${[...edges.memberOf, ...edges.membersOfReader].join('; ')}).`)
  }
  const [owns] = await s.rows<{ count: string }>(`
    SELECT ((SELECT count(*) FROM pg_shdepend WHERE refclassid='pg_authid'::regclass AND refobjid=$1::oid AND deptype='o')
          + (SELECT count(*) FROM pg_database WHERE datdba=$1::oid))::text AS count
  `, [reader])
  if (owns?.count !== '0') throw new Error(`Refusing pre-existing ${READER}: it owns ${owns?.count} object(s) (any database).`)
  const grants = await readerGrants(s, reader)
  const unexpected = unexpectedReaderGrants(grants)
  if (unexpected.length) {
    throw new Error(`Refusing pre-existing ${READER}: it holds grants this bootstrap never makes: ${
      unexpected.slice(0, 20).map((g) => `${g.privilege} on ${g.kind} ${g.object} (by ${g.grantor})`).join('; ')}`)
  }
  return grants
}

// ------------------------------------------------------------------------------------------------
// The read set
// ------------------------------------------------------------------------------------------------

interface Relation { oid: string; schema: string; name: string; relkind: string; owner: string; sources: string[] }
const fq = (r: { schema: string; name: string }): string => `${r.schema}.${r.name}`

interface ReadSet {
  targets: Relation[]
  denied: Array<Relation & { reason: string }>
  unresolvedRegistry: string[]
}

async function computeReadSet(s: Session): Promise<ReadSet> {
  const [census] = await s.rows<{ exists: boolean }>(`SELECT EXISTS (SELECT 1 FROM pg_roles WHERE rolname=$1) AS exists`, [CENSUS_ROLE])
  if (!census?.exists) throw new Error(`${CENSUS_ROLE} is absent: the census half of the read set cannot be derived. Refusing.`)
  // asset_registry is only readable through its owner's public-schema USAGE.
  const registryRaw = await s.asRole('amjis_app', () => s.rows<{ t: string }>(`
    SELECT DISTINCT btrim(target_table) AS t FROM public.asset_registry
     WHERE target_table IS NOT NULL AND btrim(target_table) <> '' ORDER BY 1
  `))
  const registryNames = registryRaw.map((r) => r.t.replace(/^public\./, ''))
  const relations = await s.rows<Relation>(`
    WITH schemas AS (SELECT oid, nspname FROM pg_namespace WHERE nspname=ANY($3::text[])),
    rels AS (SELECT c.oid, c.relname, c.relkind, c.relowner, s.nspname FROM pg_class c JOIN schemas s ON s.oid=c.relnamespace
              WHERE c.relkind IN ('r','p','v','m','f')),
    census AS (SELECT r.oid, 'census' AS src FROM rels r WHERE has_table_privilege((SELECT oid FROM pg_roles WHERE rolname=$4), r.oid, 'SELECT')),
    registry AS (SELECT r.oid, 'asset_registry' AS src FROM rels r WHERE r.nspname='public' AND r.relname=ANY($1::text[])),
    fixed AS (SELECT r.oid, 'fixed' AS src FROM rels r WHERE r.nspname='public' AND r.relname=ANY($2::text[])),
    evidence AS (SELECT r.oid, 'nirmana_evidence' AS src FROM rels r WHERE r.nspname='nirmana_evidence'),
    sources AS (SELECT * FROM census UNION ALL SELECT * FROM registry UNION ALL SELECT * FROM fixed UNION ALL SELECT * FROM evidence)
    SELECT r.oid::text AS oid, r.nspname AS schema, r.relname AS name, r.relkind::text AS relkind,
           pg_get_userbyid(r.relowner) AS owner, array_agg(DISTINCT s.src ORDER BY s.src) AS sources
      FROM sources s JOIN rels r ON r.oid=s.oid GROUP BY 1, 2, 3, 4, 5 ORDER BY 2, 3
  `, [registryNames, [...FIXED_READ_SET], [...READ_SCHEMAS], CENSUS_ROLE])
  const present = new Set(relations.filter((r) => r.schema === 'public').map((r) => r.name))
  const missingFixed = FIXED_READ_SET.filter((name) => !present.has(name))
  if (missingFixed.length) throw new Error(`Required read-set relations are absent from public: ${missingFixed.join(', ')}.`)
  const unresolvedRegistry = registryRaw.map((r) => r.t).filter((t) => !present.has(t.replace(/^public\./, '')))

  const deniedByName = new Set((await s.rows<{ oid: string }>(`
    SELECT c.oid::text AS oid FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
     WHERE n.nspname=ANY($2::text[]) AND c.relname LIKE ANY($1::text[])
  `, [[...DENY_PATTERNS], [...READ_SCHEMAS]])).map((r) => r.oid))
  const viewOids = relations.filter((r) => r.relkind === 'v' || r.relkind === 'm').map((r) => r.oid)
  const viewDeps = new Map((await s.rows<{ oid: string; via: string }>(`
    WITH RECURSIVE dep(root, ref) AS (
      SELECT r.ev_class, d.refobjid FROM pg_rewrite r
        JOIN pg_depend d ON d.classid='pg_rewrite'::regclass AND d.objid=r.oid AND d.refclassid='pg_class'::regclass AND d.refobjid<>r.ev_class
       WHERE r.ev_class=ANY($1::oid[])
      UNION
      SELECT dep.root, d.refobjid FROM dep JOIN pg_rewrite r ON r.ev_class=dep.ref
        JOIN pg_depend d ON d.classid='pg_rewrite'::regclass AND d.objid=r.oid AND d.refclassid='pg_class'::regclass AND d.refobjid<>r.ev_class
    )
    SELECT dep.root::text AS oid, string_agg(DISTINCT format('%I.%I', tn.nspname, t.relname), ', ') AS via
      FROM dep JOIN pg_class t ON t.oid=dep.ref JOIN pg_namespace tn ON tn.oid=t.relnamespace
     WHERE tn.nspname='auth' OR (tn.nspname=ANY($3::text[]) AND t.relname LIKE ANY($2::text[]))
     GROUP BY dep.root
  `, [viewOids, [...DENY_PATTERNS], [...READ_SCHEMAS]])).map((r) => [r.oid, r.via] as const))

  const targets: Relation[] = []
  const denied: Array<Relation & { reason: string }> = []
  for (const r of relations) {
    if (deniedByName.has(r.oid)) denied.push({ ...r, reason: 'deny-list' })
    else if (viewDeps.has(r.oid)) denied.push({ ...r, reason: `view reads denied/auth relation(s): ${viewDeps.get(r.oid)}` })
    else targets.push(r)
  }
  return { targets, denied, unresolvedRegistry }
}

// ------------------------------------------------------------------------------------------------
// Grants
// ------------------------------------------------------------------------------------------------

async function grantReadSet(s: Session, set: ReadSet, staleSelects: ReaderGrant[]): Promise<void> {
  const out = s.out
  out.section('Grants (each made as the object owner)')
  await s.exec(`DO $$ BEGIN EXECUTE format('GRANT CONNECT ON DATABASE %I TO ${qi(READER)}', current_database()); END $$`)
  out.line(`   CONNECT on the current database (as ${ADMIN_ROLE}, via the database owner's grant option)`)
  const schemas = await s.rows<{ name: string; owner: string }>(`
    SELECT nspname AS name, pg_get_userbyid(nspowner) AS owner FROM pg_namespace WHERE nspname=ANY($1::text[]) ORDER BY 1
  `, [[...READ_SCHEMAS]])
  for (const schema of schemas) {
    await s.asRole(schema.owner, () => s.exec(`GRANT USAGE ON SCHEMA ${qi(schema.name)} TO ${qi(READER)}`))
    out.line(`   USAGE on schema ${schema.name} (as ${schema.owner})`)
  }
  if (!schemas.some((x) => x.name === 'nirmana_evidence')) out.info('schema', 'nirmana_evidence is absent; no USAGE granted there')

  const targetOids = new Set(set.targets.map((t) => t.oid))
  const stale = staleSelects.filter((g) => g.kind === 'relation' && !targetOids.has(g.objectOid))
  for (const g of stale) {
    await s.asRole(g.grantor, () => s.exec(`REVOKE SELECT ON TABLE ${g.object} FROM ${qi(READER)}`))
    out.line(`   REVOKED stale SELECT on ${g.object} (as ${g.grantor}) — no longer in the read set`)
  }

  const byOwner = new Map<string, Relation[]>()
  for (const r of set.targets) byOwner.set(r.owner, [...(byOwner.get(r.owner) ?? []), r])
  for (const [owner, rels] of [...byOwner.entries()].sort(([a], [b]) => a.localeCompare(b))) {
    await s.asRole(owner, async () => {
      for (let i = 0; i < rels.length; i += 100) {
        const chunk = rels.slice(i, i + 100)
        await s.exec(`GRANT SELECT ON TABLE ${chunk.map((r) => `${qi(r.schema)}.${qi(r.name)}`).join(', ')} TO ${qi(READER)}`)
      }
    })
    out.line(`   SELECT on ${rels.length} relation(s) as owner ${owner}`)
  }
  out.line('   Sequences: none (by design).')
}

// ------------------------------------------------------------------------------------------------
// Verification (effective privileges, evaluated for suvarna_reader inside the transaction)
// ------------------------------------------------------------------------------------------------

async function verify(s: Session, reader: string, version: number, set: ReadSet, options: Options): Promise<void> {
  const out = s.out
  out.section('Verification — effective privileges of suvarna_reader')

  const [attrs] = await s.rows<{ ok: boolean; ro: boolean }>(`
    SELECT rolcanlogin AND NOT rolinherit AND NOT rolsuper AND NOT rolcreaterole AND NOT rolcreatedb AND NOT rolreplication AND NOT rolbypassrls AS ok,
           'default_transaction_read_only=on'=ANY(COALESCE(rolconfig, ARRAY[]::text[])) AS ro
      FROM pg_roles WHERE oid=$1::oid
  `, [reader])
  out.check('V0 role attributes', attrs?.ok === true, 'LOGIN NOINHERIT, not superuser/createrole/createdb/replication/bypassrls')
  out.check('V0 role default', attrs?.ro === true, 'ALTER ROLE … SET default_transaction_read_only=on recorded')

  const [db] = await s.rows<{ connect: boolean; create: boolean; temp: boolean }>(`
    SELECT has_database_privilege($1::oid, current_database(), 'CONNECT') AS connect,
           has_database_privilege($1::oid, current_database(), 'CREATE') AS "create",
           has_database_privilege($1::oid, current_database(), 'TEMPORARY') AS temp
  `, [reader])
  out.check('V1 CONNECT', db?.connect === true, 'CONNECT on the current database')
  out.check('V6 no database CREATE', db?.create === false, 'cannot CREATE schemas in the database')
  out.info('V6b TEMPORARY', db?.temp ? 'effective (normally via PUBLIC): session-local temp tables only, no persistent write; not revocable per-role without touching PUBLIC' : 'not effective')

  const usage = await s.rows<{ name: string; ok: boolean }>(`
    SELECT nspname AS name, has_schema_privilege($1::oid, oid, 'USAGE') AS ok FROM pg_namespace WHERE nspname=ANY($2::text[]) ORDER BY 1
  `, [reader, [...READ_SCHEMAS]])
  for (const u of usage) out.check(`V2 USAGE ${u.name}`, u.ok, `USAGE on schema ${u.name}`)
  if (!usage.some((u) => u.name === 'public')) out.check('V2 USAGE public', false, 'schema public not found')

  const missing = await s.rows<{ name: string }>(`
    SELECT format('%I.%I', n.nspname, c.relname) AS name FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
     WHERE c.oid=ANY($2::oid[]) AND NOT has_table_privilege($1::oid, c.oid, 'SELECT') ORDER BY 1
  `, [reader, set.targets.map((t) => t.oid)])
  out.check('V3 SELECT on every target', missing.length === 0, `${set.targets.length - missing.length}/${set.targets.length} effective`)
  if (missing.length) out.list('not selectable', missing.map((m) => m.name))

  const edges = await readerEdges(s, reader, version)
  out.check('V4 no memberships', edges.memberOf.length === 0 && edges.membersOfReader.length === 0,
    edges.memberOf.length + edges.membersOfReader.length === 0 ? 'member of nothing; nobody can SET ROLE into it'
      : [...edges.memberOf, ...edges.membersOfReader].join('; '))
  if (edges.tolerated.length) out.info('V4b PG16 creator edge', `${edges.tolerated.join('; ')} (ADMIN only, INHERIT/SET false)`)

  const [owns] = await s.rows<{ count: string }>(`
    SELECT ((SELECT count(*) FROM pg_shdepend WHERE refclassid='pg_authid'::regclass AND refobjid=$1::oid AND deptype='o')
          + (SELECT count(*) FROM pg_database WHERE datdba=$1::oid))::text AS count
  `, [reader])
  out.check('V5 owns nothing', owns?.count === '0', `${owns?.count} owned object(s) across all databases`)

  const schemaCreate = await s.rows<{ name: string }>(`
    SELECT nspname AS name FROM pg_namespace WHERE nspname !~ '^pg_toast' AND nspname !~ '^pg_temp_'
       AND has_schema_privilege($1::oid, oid, 'CREATE') ORDER BY 1
  `, [reader])
  out.check('V7 no schema CREATE', schemaCreate.length === 0, schemaCreate.length ? schemaCreate.map((x) => x.name).join(', ') : 'none')

  const relWrite = await s.rows<{ name: string; privs: string }>(`
    SELECT format('%I.%I', n.nspname, c.relname) AS name,
           concat_ws(',', CASE WHEN has_table_privilege($1::oid, c.oid, 'INSERT') THEN 'INSERT' END,
                          CASE WHEN has_table_privilege($1::oid, c.oid, 'UPDATE') THEN 'UPDATE' END,
                          CASE WHEN has_table_privilege($1::oid, c.oid, 'DELETE') THEN 'DELETE' END,
                          CASE WHEN has_table_privilege($1::oid, c.oid, 'TRUNCATE') THEN 'TRUNCATE' END,
                          CASE WHEN has_table_privilege($1::oid, c.oid, 'REFERENCES') THEN 'REFERENCES' END,
                          CASE WHEN has_table_privilege($1::oid, c.oid, 'TRIGGER') THEN 'TRIGGER' END) AS privs
      FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
     WHERE c.relkind IN ('r','p','v','m','f') AND n.nspname !~ '^pg_toast' AND n.nspname !~ '^pg_temp_'
       AND has_table_privilege($1::oid, c.oid, 'INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER') ORDER BY 1
  `, [reader])
  out.check('V8 no relation write privilege', relWrite.length === 0, `${relWrite.length} relation(s) with INSERT/UPDATE/DELETE/TRUNCATE/REFERENCES/TRIGGER`)
  if (relWrite.length) out.list('writable relations', relWrite.map((r) => `${r.name} [${r.privs}]`))

  const colWrite = await s.rows<{ name: string }>(`
    SELECT format('%I.%I', n.nspname, c.relname) AS name FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
     WHERE c.relkind IN ('r','p','v','m','f') AND n.nspname !~ '^pg_toast' AND n.nspname !~ '^pg_temp_'
       AND has_any_column_privilege($1::oid, c.oid, 'INSERT,UPDATE,REFERENCES') ORDER BY 1
  `, [reader])
  out.check('V8b no column write privilege', colWrite.length === 0, `${colWrite.length} relation(s) with column INSERT/UPDATE/REFERENCES`)
  if (colWrite.length) out.list('column-writable relations', colWrite.map((r) => r.name))

  const seq = await s.rows<{ name: string }>(`
    SELECT format('%I.%I', n.nspname, c.relname) AS name FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
     WHERE c.relkind='S' AND n.nspname !~ '^pg_toast' AND n.nspname !~ '^pg_temp_'
       AND has_sequence_privilege($1::oid, c.oid, 'USAGE,UPDATE') ORDER BY 1
  `, [reader])
  out.check('V9 no sequence USAGE/UPDATE', seq.length === 0, `${seq.length} sequence(s)`)
  if (seq.length) out.list('advanceable sequences', seq.map((r) => r.name))

  const secdef = await s.rows<{ sig: string; owner: string }>(`
    SELECT p.oid::regprocedure::text AS sig, pg_get_userbyid(p.proowner) AS owner
      FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace
     WHERE p.prosecdef AND n.nspname <> 'pg_catalog'
       AND has_function_privilege($1::oid, p.oid, 'EXECUTE') AND has_schema_privilege($1::oid, n.oid, 'USAGE') ORDER BY 1
  `, [reader])
  const accepted = new Set(options.acceptSecdef)
  const secdefRejected = secdef.filter((f) => !accepted.has(f.sig))
  out.check('V10 no reachable SECURITY DEFINER function', secdefRejected.length === 0,
    `${secdef.length} reachable outside pg_catalog, ${secdef.length - secdefRejected.length} accepted via --accept-secdef`)
  if (secdef.length) out.list('reachable SECURITY DEFINER functions (runs as owner)', secdef.map((f) => `${f.sig} owner=${f.owner}${accepted.has(f.sig) ? ' [ACCEPTED]' : ''}`))
  const unusedAccept = options.acceptSecdef.filter((sig) => !secdef.some((f) => f.sig === sig))
  if (unusedAccept.length) out.info('V10b', `--accept-secdef values matching nothing reachable: ${unusedAccept.join('; ')}`)

  const [auth] = await s.rows<{ exists: boolean; usage: boolean; granted: string }>(`
    WITH auth AS (SELECT oid FROM pg_namespace WHERE nspname='auth')
    SELECT EXISTS (SELECT 1 FROM auth) AS exists,
           COALESCE((SELECT has_schema_privilege($1::oid, oid, 'USAGE') FROM auth), false) AS usage,
           (SELECT count(*)::text FROM pg_class c WHERE c.relnamespace IN (SELECT oid FROM auth)
              AND has_any_column_privilege($1::oid, c.oid, 'SELECT')) AS granted
  `, [reader])
  const authViews = await s.rows<{ name: string }>(`
    WITH RECURSIVE dep(root, ref) AS (
      SELECT r.ev_class, d.refobjid FROM pg_rewrite r
        JOIN pg_depend d ON d.classid='pg_rewrite'::regclass AND d.objid=r.oid AND d.refclassid='pg_class'::regclass AND d.refobjid<>r.ev_class
      UNION
      SELECT dep.root, d.refobjid FROM dep JOIN pg_rewrite r ON r.ev_class=dep.ref
        JOIN pg_depend d ON d.classid='pg_rewrite'::regclass AND d.objid=r.oid AND d.refclassid='pg_class'::regclass AND d.refobjid<>r.ev_class
    )
    SELECT DISTINCT format('%I.%I', vn.nspname, v.relname) AS name
      FROM dep JOIN pg_class t ON t.oid=dep.ref JOIN pg_namespace tn ON tn.oid=t.relnamespace
      JOIN pg_class v ON v.oid=dep.root JOIN pg_namespace vn ON vn.oid=v.relnamespace
     WHERE (tn.nspname='auth' OR (tn.nspname=ANY($3::text[]) AND t.relname LIKE ANY($2::text[])))
       AND vn.nspname <> 'auth'
       AND has_schema_privilege($1::oid, vn.oid, 'USAGE') AND has_any_column_privilege($1::oid, v.oid, 'SELECT')
     ORDER BY 1
  `, [reader, [...DENY_PATTERNS], [...READ_SCHEMAS]])
  out.check('V11 schema auth unreachable', auth?.usage === false,
    auth?.exists ? `USAGE=${auth.usage} (auth relations carrying a SELECT grant reachable only with USAGE: ${auth.granted})` : 'schema auth absent')
  out.check('V11b no readable view over auth or deny-listed relations', authViews.length === 0, `${authViews.length} view(s)`)
  if (authViews.length) out.list('views leaking auth/deny-listed data', authViews.map((v) => v.name))

  const deniedReadable = await s.rows<{ name: string }>(`
    SELECT format('%I.%I', n.nspname, c.relname) AS name FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
     WHERE c.relkind IN ('r','p','v','m','f')
       AND (n.nspname='auth' OR (n.nspname=ANY($3::text[]) AND c.relname LIKE ANY($2::text[])))
       AND has_schema_privilege($1::oid, n.oid, 'USAGE') AND has_any_column_privilege($1::oid, c.oid, 'SELECT') ORDER BY 1
  `, [reader, [...DENY_PATTERNS], [...READ_SCHEMAS]])
  out.check('V12 deny-listed relations unreadable', deniedReadable.length === 0, `${deniedReadable.length} readable`)
  if (deniedReadable.length) out.list('readable deny-listed relations (table or column SELECT)', deniedReadable.map((r) => r.name))

  const defacl = await s.rows<{ line: string }>(`
    SELECT format('%s in %s on %s: %s', pg_get_userbyid(d.defaclrole), d.defaclnamespace, d.defaclobjtype, a.privilege_type) AS line
      FROM pg_default_acl d CROSS JOIN LATERAL aclexplode(d.defaclacl) a WHERE a.grantee=$1::oid
  `, [reader])
  out.check('V13 no default-privilege grants name suvarna_reader', defacl.length === 0, defacl.map((d) => d.line).join('; ') || 'none')

  const extra = await s.rows<{ name: string }>(`
    SELECT format('%I.%I', n.nspname, c.relname) AS name FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
     WHERE c.relkind IN ('r','p','v','m','f') AND n.nspname NOT IN ('pg_catalog','information_schema') AND n.nspname !~ '^pg_toast'
       AND NOT (c.oid=ANY($2::oid[])) AND has_schema_privilege($1::oid, n.oid, 'USAGE') AND has_table_privilege($1::oid, c.oid, 'SELECT')
     ORDER BY 1
  `, [reader, set.targets.map((t) => t.oid)])
  out.info('V14 readable beyond the read set', extra.length ? `${extra.length} relation(s), normally via PUBLIC grants: ${extra.map((e) => e.name).join(', ')}` : 'none')
}

// ------------------------------------------------------------------------------------------------
// Report: RLS and PII the native must knowingly accept
// ------------------------------------------------------------------------------------------------

async function reportRlsAndPii(s: Session, reader: string, set: ReadSet): Promise<void> {
  const out = s.out
  out.section('Row-level security on the read set (no policy is added — the native decides)')
  const rls = await s.rows<{ name: string; applicable: boolean; policies: string | null }>(`
    SELECT format('%I.%I', n.nspname, c.relname) AS name,
           EXISTS (SELECT 1 FROM pg_policy p WHERE p.polrelid=c.oid AND p.polpermissive AND p.polcmd IN ('r','*')
                     AND (0=ANY(p.polroles) OR $1::oid=ANY(p.polroles))) AS applicable,
           (SELECT string_agg(format('%s[%s,cmd=%s,to=%s]', p.polname, CASE WHEN p.polpermissive THEN 'permissive' ELSE 'restrictive' END, p.polcmd,
                     (SELECT string_agg(CASE WHEN r=0 THEN 'PUBLIC' ELSE pg_get_userbyid(r) END, '|') FROM unnest(p.polroles) r)), '; ' ORDER BY p.polname)
              FROM pg_policy p WHERE p.polrelid=c.oid) AS policies
      FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
     WHERE c.oid=ANY($2::oid[]) AND c.relrowsecurity ORDER BY 1
  `, [reader, set.targets.map((t) => t.oid)])
  out.list('RLS on, NO applicable SELECT policy → suvarna_reader silently sees ZERO rows',
    rls.filter((r) => !r.applicable).map((r) => `${r.name}  policies: ${r.policies ?? 'none'}`))
  out.list('RLS on, a PUBLIC/reader policy applies → rows filtered by the policy expression',
    rls.filter((r) => r.applicable).map((r) => `${r.name}  policies: ${r.policies ?? 'none'}`))
  const policyDeps = await s.rows<{ line: string }>(`
    SELECT format('%I.%I policy %s needs %s', n.nspname, c.relname, p.polname,
             CASE WHEN d.refclassid='pg_class'::regclass THEN d.refobjid::regclass::text ELSE d.refobjid::regprocedure::text END) AS line
      FROM pg_policy p JOIN pg_class c ON c.oid=p.polrelid JOIN pg_namespace n ON n.oid=c.relnamespace
      JOIN pg_depend d ON d.classid='pg_policy'::regclass AND d.objid=p.oid AND d.refclassid IN ('pg_class'::regclass, 'pg_proc'::regclass)
     WHERE c.oid=ANY($2::oid[]) AND c.relrowsecurity AND p.polcmd IN ('r','*') AND (0=ANY(p.polroles) OR $1::oid=ANY(p.polroles))
       AND NOT (d.refclassid='pg_class'::regclass AND d.refobjid=c.oid)
       AND NOT CASE WHEN d.refclassid='pg_class'::regclass
             THEN has_schema_privilege($1::oid, (SELECT relnamespace FROM pg_class WHERE oid=d.refobjid), 'USAGE')
                  AND has_any_column_privilege($1::oid, d.refobjid, 'SELECT')
             ELSE has_schema_privilege($1::oid, (SELECT pronamespace FROM pg_proc WHERE oid=d.refobjid), 'USAGE')
                  AND has_function_privilege($1::oid, d.refobjid, 'EXECUTE') END
     ORDER BY 1
  `, [reader, set.targets.map((t) => t.oid)])
  out.list('applicable policies that reference objects suvarna_reader cannot use (queries will ERROR)', policyDeps.map((p) => p.line))

  out.section('PII in the read set')
  out.list('known PII relations included', PII_RELATIONS.filter((name) => set.targets.some((t) => t.schema === 'public' && t.name === name))
    .map((name) => `public.${name} — birth data (date/time/place); Suvarṇa needs it for chart ids`))
  const piiCols = await s.rows<{ name: string; cols: string }>(`
    SELECT format('%I.%I', n.nspname, c.relname) AS name, string_agg(a.attname, ', ' ORDER BY a.attnum) AS cols
      FROM pg_attribute a JOIN pg_class c ON c.oid=a.attrelid JOIN pg_namespace n ON n.oid=c.relnamespace
     WHERE c.oid=ANY($1::oid[]) AND a.attnum > 0 AND NOT a.attisdropped AND a.attname ~* $2
     GROUP BY 1 ORDER BY 1
  `, [set.targets.map((t) => t.oid), PII_COLUMN_REGEX])
  out.list('name-heuristic review list: included relations with PII/credential-looking columns (not excluded)',
    piiCols.map((p) => `${p.name}: ${p.cols}`))
}

// ------------------------------------------------------------------------------------------------
// Invariant reporting
// ------------------------------------------------------------------------------------------------

interface Markers { nirmana: boolean; dataPlane: number; dataPlaneHistory: boolean; purna: boolean }

async function readMarkers(s: Session): Promise<Markers> {
  const [row] = await s.asRole('amjis_app', () => s.rows<{ nirmana: boolean; data_plane: number; purna: boolean }>(`
    SELECT EXISTS (SELECT 1 FROM public._migrations_applied WHERE filename=$1) AS nirmana,
           (SELECT count(DISTINCT filename)::int FROM public._migrations_applied WHERE filename=ANY($2::text[])) AS data_plane,
           EXISTS (SELECT 1 FROM public._migrations_applied WHERE filename=$3) AS purna
  `, [NIRMANA_MARKER, [...DATA_PLANE_MARKERS], PURNA_MARKER]))
  const [history] = await s.rows<{ present: boolean }>(`
    SELECT EXISTS (SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
      WHERE n.nspname='public' AND c.relname IN ('l1_data_plane_generations','data_plane_l2_producer_generations')) AS present
  `)
  return { nirmana: row?.nirmana === true, dataPlane: row?.data_plane ?? 0, dataPlaneHistory: history?.present === true, purna: row?.purna === true }
}

function reportInvariants(out: Reporter, markers: Markers, before: InvariantState, after: InvariantState, options: Options): void {
  out.section('Handoff invariants (baseline → after; read-only re-implementations of the deploy checks)')
  const dataPlaneApplies = markers.dataPlane > 0 || markers.dataPlaneHistory
  const pair = (list: Invariant[], other: Invariant[], id: string): [boolean, boolean] =>
    [list.find((x) => x.id === id)?.ok ?? false, other.find((x) => x.id === id)?.ok ?? false]

  if (!markers.nirmana) out.info('N*', `Nirmāṇa handoff unmarked (${NIRMANA_MARKER} absent): N checks not applicable`)
  else for (const { id } of before.nirmana) {
    const [b, a] = pair(before.nirmana, after.nirmana, id)
    out.check(`${id}`, b && a, `baseline=${b ? 'pass' : 'FAIL'} after=${a ? 'pass' : 'FAIL'}${!b ? ' (pre-existing drift: refusing to act on a drifted handoff)' : ''}`)
  }

  if (!dataPlaneApplies) out.info('D*', 'data-plane boundary unmarked: D checks not applicable (the deploy gate returns "unmarked")')
  else {
    if (markers.dataPlane !== DATA_PLANE_MARKERS.length) out.check('d0_markers', false, `partial data-plane marker state (${markers.dataPlane}/2): the deploy gate refuses this state`)
    for (const { id } of before.dataPlaneStrict) {
      const tolerantOnly = ['d3_public_schema_acl_exact', 'd4_protected_table_acl', 'd5_protected_history_acl'].includes(id)
      const [bStrict, aStrict] = pair(before.dataPlaneStrict, after.dataPlaneStrict, id)
      const [bTol, aTol] = pair(before.dataPlaneTolerant, after.dataPlaneTolerant, id)
      if (!tolerantOnly) {
        out.check(id, bStrict && aStrict, `baseline=${bStrict ? 'pass' : 'FAIL'} after=${aStrict ? 'pass' : 'FAIL'}`)
        continue
      }
      if (!bTol) { out.check(id, false, 'baseline FAIL even when suvarna_reader entries are tolerated (pre-existing drift)'); continue }
      if (options.dataPlaneGateAmended) {
        out.check(id, aTol, `after=${aTol ? 'pass' : 'FAIL'} under the amended gate (suvarna_reader SELECT/USAGE tolerated, nothing else)${aStrict ? '' : '; the UNAMENDED gate would fail'}`)
      } else {
        out.check(id, aStrict, aStrict ? 'after=pass under the gate as deployed'
          : `DATA-PLANE GATE CONFLICT: after=FAIL under the deployed gate only because of suvarna_reader's own entries (tolerant form ${aTol ? 'passes' : 'ALSO FAILS'}). `
            + 'Land and deploy the gate amendment, then re-run with --data-plane-gate-amended.')
      }
    }
  }

  if (!markers.purna) out.info('P*', `Pūrṇa marker ${PURNA_MARKER} absent: P checks reported, compared for no-regression only`)
  for (const { id } of before.purna) {
    const [b, a] = pair(before.purna, after.purna, id)
    out.check(id, b === a, `baseline=${b ? 'pass' : 'fail'} after=${a ? 'pass' : 'fail'} (must not change)`)
  }
}

function reportSnapshots(out: Reporter, before: Snapshot, after: Snapshot): void {
  out.section('Everything else left exactly as found (catalog snapshots, suvarna_reader rows excluded)')
  for (const key of ['memberships', 'roles', 'acl'] as const) {
    const d = diffLines(before[key], after[key])
    out.check(`S ${key}`, d.added.length === 0 && d.removed.length === 0,
      `${before[key].length} rows before, ${after[key].length} after, +${d.added.length} −${d.removed.length}`)
    if (d.added.length) out.list(`${key} added`, d.added, 30)
    if (d.removed.length) out.list(`${key} removed`, d.removed, 30)
  }
}

// ------------------------------------------------------------------------------------------------
// Secret Manager + credential file (apply only)
// ------------------------------------------------------------------------------------------------

function gcloud(args: string[], input?: string): { status: number; stdout: string; stderr: string } {
  const result = spawnSync('gcloud', args, {
    input, encoding: 'utf8', timeout: 120_000,
    stdio: [input === undefined ? 'ignore' : 'pipe', 'pipe', 'pipe'],
  })
  if (result.error) return { status: -1, stdout: '', stderr: result.error.message }
  return { status: result.status ?? -1, stdout: result.stdout ?? '', stderr: result.stderr ?? '' }
}

const short = (text: string): string => text.replace(/\s+/g, ' ').trim().slice(0, 300)

/** In --apply a problem here is a failure (and the secret is created if missing, before any database
 *  work). In --dry-run it is a read-only preview reported as INFO, so it never fails the dry run. */
function gcloudReadiness(out: Reporter, apply: boolean): boolean {
  const report = (id: string, ok: boolean, detail: string): void => {
    if (apply) out.check(id, ok, detail)
    else out.info(id, `${ok ? 'ready' : 'NOT READY for --apply'} — ${detail}`)
  }
  const version = gcloud(['--version'])
  if (version.status !== 0) { report('G gcloud', false, `gcloud not runnable: ${short(version.stderr)}`); return false }
  const auth = gcloud(['auth', 'list', '--filter=status:ACTIVE', '--format=value(account)'])
  const authed = auth.status === 0 && auth.stdout.trim() !== ''
  report('G gcloud authenticated', authed, authed ? 'an active account is present' : 'no active gcloud account (run gcloud auth login)')
  if (!authed) return false
  const describe = gcloud(['secrets', 'describe', SECRET_NAME, `--project=${GCP_PROJECT}`, '--format=value(name)'])
  if (describe.status === 0) { report('G secret', true, `${SECRET_NAME} exists in ${GCP_PROJECT}`); return true }
  if (!/NOT_FOUND|not found/i.test(describe.stderr)) {
    report('G secret', false, `cannot describe ${SECRET_NAME} in ${GCP_PROJECT}: ${short(describe.stderr)}`)
    return false
  }
  if (!apply) { report('G secret', true, `${SECRET_NAME} absent in ${GCP_PROJECT}; --apply creates it`); return true }
  const created = gcloud(['secrets', 'create', SECRET_NAME, `--project=${GCP_PROJECT}`, '--replication-policy=automatic',
    '--labels=campaign=suvarna,decision=d6'])
  report('G secret created', created.status === 0, created.status === 0 ? `${SECRET_NAME} created (no version yet)` : short(created.stderr))
  return created.status === 0
}

function addSecretVersion(password: string): void {
  const added = gcloud(['secrets', 'versions', 'add', SECRET_NAME, '--data-file=-', `--project=${GCP_PROJECT}`, '--format=value(name)'], password)
  if (added.status !== 0) throw new Error(`Secret Manager version add failed: ${short(added.stderr)}`)
}

export function credentialFileBody(database: string, password: string, today: string): string {
  if (!/^[A-Za-z0-9_]+$/.test(database) || !/^[A-Za-z0-9]+$/.test(password)) throw new Error('Unsafe credential file values.')
  return [
    `# Suvarṇa read-only credential (D6, ${today}). Login: ${READER}. Written by suvarna-reader-bootstrap.ts.`,
    '# Never print, copy or commit this file.',
    'export PGHOST=127.0.0.1',
    'export PGPORT=5433',
    `export PGDATABASE='${database}'`,
    `export PGUSER=${READER}`,
    `export PGPASSWORD='${password}'`,
    "export PGOPTIONS='-c default_transaction_read_only=on'",
    '',
  ].join('\n')
}

function writeCredentialFile(out: Reporter, database: string, password: string): void {
  const dir = join(homedir(), '.config', 'suvarna')
  const cred = join(dir, 'pgenv.sh')
  const backup = join(dir, 'pgenv.app-login.bak')
  mkdirSync(dir, { recursive: true, mode: 0o700 })
  chmodSync(dir, 0o700)
  if (existsSync(cred)) {
    if (!existsSync(backup)) {
      copyFileSync(cred, backup, fsConstants.COPYFILE_EXCL)
      chmodSync(backup, 0o600)
      out.line('   previous credential file kept as ~/.config/suvarna/pgenv.app-login.bak (mode 600)')
    } else if (!readFileSync(cred).equals(readFileSync(backup))) {
      const extra = join(dir, `pgenv.previous.${new Date().toISOString().replace(/[:.]/g, '-')}.bak`)
      copyFileSync(cred, extra, fsConstants.COPYFILE_EXCL)
      chmodSync(extra, 0o600)
      out.line(`   pgenv.app-login.bak already exists and is kept; the current file was also kept as ${extra.replace(homedir(), '~')} (mode 600)`)
    } else {
      out.line('   pgenv.app-login.bak already holds the current file; kept')
    }
  }
  const tmp = join(dir, `.pgenv.${process.pid}.${randomBytes(6).toString('hex')}.tmp`)
  const fd = openSync(tmp, 'wx', 0o600)
  try {
    writeSync(fd, credentialFileBody(database, password, new Date().toISOString().slice(0, 10)))
    fsyncSync(fd)
  } catch (error) {
    closeSync(fd)
    unlinkSync(tmp)
    throw error
  }
  closeSync(fd)
  renameSync(tmp, cred)
  chmodSync(cred, 0o600)
  out.line('   ~/.config/suvarna/pgenv.sh replaced atomically (mode 600)')
}

/** After COMMIT: prove the credential by connecting as suvarna_reader and running the same
 *  self-evaluable checks the Monitor runs. */
async function proveReaderLogin(out: Reporter, route: AdminRoute, password: string): Promise<boolean> {
  const pool = new Pool({
    host: route.host, port: route.port, database: route.database, user: READER, password,
    options: '-c default_transaction_read_only=on', max: 1, connectionTimeoutMillis: 15_000,
  })
  try {
    const { rows: [r] } = await pool.query<{ who: string; ro: string; writes: string; creates: boolean }>(`
      SELECT current_user::text AS who, current_setting('default_transaction_read_only') AS ro,
        ((SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
           WHERE n.nspname !~ '^pg_toast' AND n.nspname !~ '^pg_temp_' AND (
             (c.relkind IN ('r','p','v','m','f') AND (has_table_privilege(current_user, c.oid, 'INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER')
                OR has_any_column_privilege(current_user, c.oid, 'INSERT,UPDATE,REFERENCES')))
             OR (c.relkind='S' AND has_sequence_privilege(current_user, c.oid, 'USAGE,UPDATE'))))
         + (SELECT count(*) FROM pg_namespace WHERE nspname !~ '^pg_toast' AND nspname !~ '^pg_temp_' AND has_schema_privilege(current_user, oid, 'CREATE'))
        )::text AS writes,
        has_database_privilege(current_user, current_database(), 'CREATE') AS creates
    `)
    const ok = r?.who === READER && r?.ro === 'on' && r?.writes === '0' && r?.creates === false
    out.check('L login as suvarna_reader', ok, `current_user=${r?.who} default_transaction_read_only=${r?.ro} write paths=${r?.writes} database CREATE=${r?.creates}`)
    return ok
  } catch (error) {
    out.check('L login as suvarna_reader', false, `could not connect/query as ${READER}: ${short(error instanceof Error ? error.message : String(error))}`)
    return false
  } finally {
    await pool.end().catch(() => undefined)
  }
}

/** Rollback: put the previous credential file back (atomically, mode 600). The backup is kept. */
function restoreCredentialFile(out: Reporter): void {
  const dir = join(homedir(), '.config', 'suvarna')
  const cred = join(dir, 'pgenv.sh')
  const backup = join(dir, 'pgenv.app-login.bak')
  if (!existsSync(backup)) {
    out.info('file', 'no ~/.config/suvarna/pgenv.app-login.bak: credential file left untouched — restore it yourself')
    return
  }
  const tmp = join(dir, `.pgenv.${process.pid}.${randomBytes(6).toString('hex')}.tmp`)
  const fd = openSync(tmp, 'wx', 0o600)
  try {
    writeSync(fd, readFileSync(backup))
    fsyncSync(fd)
  } catch (error) {
    closeSync(fd)
    unlinkSync(tmp)
    throw error
  }
  closeSync(fd)
  renameSync(tmp, cred)
  chmodSync(cred, 0o600)
  out.line('   ~/.config/suvarna/pgenv.sh restored from pgenv.app-login.bak (atomic, mode 600; backup kept)')
}

// ------------------------------------------------------------------------------------------------
// Main
// ------------------------------------------------------------------------------------------------

async function beginAsAdmin(s: Session, route: AdminRoute): Promise<{ version: number }> {
  await s.exec('BEGIN')
  await s.exec(`SET LOCAL lock_timeout = '15s'`)
  await s.exec(`SET LOCAL statement_timeout = '10min'`)
  const [actor] = await s.rows<{ session_user: string; current_user: string; can_manage: boolean; version: number; database: string }>(`
    SELECT session_user::text AS session_user, current_user::text AS current_user,
           (r.rolsuper OR r.rolcreaterole) AS can_manage, current_setting('server_version_num')::int AS version,
           current_database()::text AS database
      FROM pg_roles r WHERE r.rolname=current_user
  `)
  if (actor?.session_user !== ADMIN_ROLE || actor.current_user !== ADMIN_ROLE || actor.can_manage !== true) {
    throw new Error(`The reader bootstrap requires direct ${ADMIN_ROLE} administrative authentication (with CREATEROLE).`)
  }
  if (actor.database !== route.database) throw new Error('Connected database differs from the admin URL database.')
  s.out.line(`   actor: ${ADMIN_ROLE} (CREATEROLE), server_version_num=${actor.version}`)
  return { version: actor.version }
}

/** --rollback: every grant suvarna_reader holds is revoked AS ITS GRANTOR (a plain REVOKE by postgres
 *  cannot remove an owner-made grant after the handoffs), then DROP ROLE — in one transaction with
 *  the same snapshot/invariant proof. On --apply, the previous credential file is restored. */
export async function runSuvarnaReaderRollback(options: Options, env: NodeJS.ProcessEnv = process.env): Promise<boolean> {
  const out = new Reporter()
  const route = validateAdminRoute(env[ADMIN_URL])
  out.line(`Suvarṇa D6 reader ROLLBACK — mode: ${options.mode.toUpperCase()}`)
  out.line(`Target: database "${route.database}" via ${route.host}:${route.port} as ${ADMIN_ROLE} (URL itself never printed)`)
  const pool = new Pool({ connectionString: env[ADMIN_URL], max: 1, application_name: 'suvarna-reader-rollback' })
  const client = await pool.connect()
  const s = new Session(client, out)
  let committed = false
  try {
    const actor = await beginAsAdmin(s, route)
    const reader = await readerOid(s)
    if (!reader) {
      await s.exec('ROLLBACK')
      out.line(`RESULT: NOTHING TO DO — ${READER} does not exist.`)
      if (options.mode === 'apply') restoreCredentialFile(out)
      return true
    }
    const snapshotBefore = await takeSnapshot(s, reader)
    const invariantsBefore = await invariantState(s)
    const markers = await readMarkers(s)

    out.section('Revocations (each as the grantor)')
    const [owns] = await s.rows<{ count: string }>(`
      SELECT ((SELECT count(*) FROM pg_shdepend WHERE refclassid='pg_authid'::regclass AND refobjid=$1::oid AND deptype='o')
            + (SELECT count(*) FROM pg_database WHERE datdba=$1::oid))::text AS count
    `, [reader])
    if (owns?.count !== '0') throw new Error(`${READER} owns ${owns?.count} object(s); refusing an automatic rollback (DROP OWNED would destroy them).`)
    const grants = await readerGrants(s, reader)
    const manual = grants.filter((g) => !['relation', 'schema', 'database'].includes(g.kind))
    if (manual.length) {
      throw new Error(`${READER} holds grants this bootstrap never makes; clean them by hand first: ${
        manual.slice(0, 20).map((g) => `${g.privilege} on ${g.kind} ${g.object} (by ${g.grantor})`).join('; ')}`)
    }
    const seen = new Set<string>()
    for (const g of grants) {
      const key = `${g.kind}|${g.objectOid}|${g.grantor}`
      if (seen.has(key)) continue
      seen.add(key)
      const target = g.kind === 'relation' ? `${g.subkind === 'S' ? 'SEQUENCE' : 'TABLE'} ${g.object}`
        : g.kind === 'schema' ? `SCHEMA ${qi(g.object)}` : `DATABASE ${qi(g.object)}`
      await s.asRole(g.grantor, () => s.exec(`REVOKE ALL ON ${target} FROM ${qi(READER)}`))
    }
    out.line(`   revoked ${seen.size} grant group(s) from ${READER}`)
    const edges = await readerEdges(s, reader, actor.version)
    if (edges.memberOf.length || edges.membersOfReader.length) {
      throw new Error(`${READER} has memberships (${[...edges.memberOf, ...edges.membersOfReader].join('; ')}); refusing.`)
    }
    await s.removeTemporaryMemberships()
    await s.exec(`DROP ROLE ${qi(READER)}`)
    out.line(`   DROP ROLE ${READER} (its ALTER ROLE … SET default goes with it)`)
    out.line(`   temporary owner memberships used and removed: ${s.temporaryMemberships.join(', ') || 'none'}`)

    const invariantsAfter = await invariantState(s)
    reportInvariants(out, markers, invariantsBefore, invariantsAfter, { ...options, dataPlaneGateAmended: false })
    reportSnapshots(out, snapshotBefore, await takeSnapshot(s, null))

    out.section('Outcome')
    if (out.failures.length) {
      out.list('violations', out.failures)
      await s.exec('ROLLBACK')
      out.line(`RESULT: FAIL — ${out.failures.length} violation(s); transaction rolled back, nothing persisted.`)
      return false
    }
    if (options.mode === 'dry-run') {
      await s.exec('ROLLBACK')
      out.line('RESULT: PASS (dry run) — the rollback would succeed; transaction rolled back, nothing persisted.')
      return true
    }
    await s.exec('COMMIT')
    committed = true
    out.line(`   COMMIT: ${READER} dropped`)
  } catch (error) {
    if (!committed) await client.query('ROLLBACK').catch(() => undefined)
    throw error
  } finally {
    client.release()
    await pool.end().catch(() => undefined)
  }
  restoreCredentialFile(out)
  out.line(`   Secret Manager: ${SECRET_NAME} left in place; disable its versions yourself if wanted:`)
  out.line(`     gcloud secrets versions list ${SECRET_NAME} --project=${GCP_PROJECT}`)
  out.line('RESULT: ROLLED BACK')
  return true
}

export async function runSuvarnaReaderBootstrap(options: Options, env: NodeJS.ProcessEnv = process.env): Promise<boolean> {
  const out = new Reporter()
  const route = validateAdminRoute(env[ADMIN_URL])
  const password = generatePassword()
  const verifier = scramVerifier(password)
  out.protect(password)
  out.protect(verifier)

  out.line(`Suvarṇa D6 reader bootstrap — mode: ${options.mode.toUpperCase()}${options.dataPlaneGateAmended ? ' (data-plane gate declared amended)' : ''}`)
  out.line(`Target: database "${route.database}" via ${route.host}:${route.port} as ${ADMIN_ROLE} (URL itself never printed)`)

  out.section(options.mode === 'apply' ? 'Apply prerequisites' : 'Apply prerequisites (read-only preview)')
  const gcloudReady = gcloudReadiness(out, options.mode === 'apply')
  if (options.mode === 'apply' && (!gcloudReady || out.failures.length)) {
    out.line('RESULT: FAIL — Secret Manager is not ready; nothing was changed.')
    return false
  }

  const pool = new Pool({ connectionString: env[ADMIN_URL], max: 1, application_name: 'suvarna-reader-bootstrap' })
  const client = await pool.connect()
  const s = new Session(client, out)
  let committed = false
  try {
    const actor = await beginAsAdmin(s, route)

    // Baseline — before any mutation, including temporary memberships.
    const existingBefore = await readerOid(s)
    const snapshotBefore = await takeSnapshot(s, existingBefore)
    const invariantsBefore = await invariantState(s)

    let staleSelects: ReaderGrant[] = []
    out.section('Role')
    if (existingBefore) {
      staleSelects = await inspectExistingReader(s, existingBefore, actor.version)
      await s.exec(`ALTER ROLE ${qi(READER)} LOGIN NOINHERIT NOCREATEDB NOCREATEROLE CONNECTION LIMIT ${CONNECTION_LIMIT} PASSWORD ${client.escapeLiteral(verifier)}`)
      out.line(`   ${READER} exists and passed normalisation checks (not elevated, no memberships, owns nothing, only SELECT/USAGE/CONNECT grants); password reset`)
    } else {
      await s.exec(`CREATE ROLE ${qi(READER)} LOGIN NOINHERIT NOCREATEDB NOCREATEROLE CONNECTION LIMIT ${CONNECTION_LIMIT} PASSWORD ${client.escapeLiteral(verifier)}`)
      out.line(`   ${READER} created: LOGIN NOINHERIT NOCREATEDB NOCREATEROLE CONNECTION LIMIT ${CONNECTION_LIMIT}, SCRAM verifier computed client-side`)
    }
    await s.exec(`ALTER ROLE ${qi(READER)} SET default_transaction_read_only = on`)
    out.line('   role default: default_transaction_read_only = on (belt; the grants below are the real boundary)')
    const reader = await readerOid(s)
    if (!reader) throw new Error(`${READER} not visible after creation.`)

    const markers = await readMarkers(s)
    const set = await computeReadSet(s)

    out.section('Plan — read set')
    const bySource = (src: string): number => set.targets.filter((t) => t.sources.includes(src)).length
    out.line(`   ${set.targets.length} relation(s) to be SELECT-able: census=${bySource('census')} asset_registry=${bySource('asset_registry')} fixed=${bySource('fixed')} nirmana_evidence=${bySource('nirmana_evidence')} (overlapping)`)
    out.list('owners (grants are made as each)', [...new Set(set.targets.map((t) => t.owner))].sort()
      .map((owner) => `${owner}: ${set.targets.filter((t) => t.owner === owner).length}`))
    out.list('relations', set.targets.map((t) => `${fq(t)} [${t.relkind}] owner=${t.owner} from=${t.sources.join('+')}`))
    out.list('EXCLUDED (deny-list or view over denied/auth data)', set.denied.map((d) => `${fq(d)} — ${d.reason}`))
    if (set.unresolvedRegistry.length) out.list('asset_registry.target_table values with no relation in public (ignored)', set.unresolvedRegistry)

    await grantReadSet(s, set, staleSelects)
    await s.removeTemporaryMemberships()
    out.line(`   temporary owner memberships used and removed in this transaction: ${s.temporaryMemberships.join(', ') || 'none'}`)

    await verify(s, reader, actor.version, set, options)
    const invariantsAfter = await invariantState(s)
    reportInvariants(out, markers, invariantsBefore, invariantsAfter, options)
    reportSnapshots(out, snapshotBefore, await takeSnapshot(s, reader))
    await reportRlsAndPii(s, reader, set)

    out.section('Outcome')
    if (out.failures.length) {
      out.list('violations', out.failures)
      await s.exec('ROLLBACK')
      out.line(`RESULT: FAIL — ${out.failures.length} violation(s); transaction rolled back, nothing persisted.`)
      return false
    }
    if (options.mode === 'dry-run') {
      await s.exec('ROLLBACK')
      out.line('RESULT: PASS (dry run) — every check passed; transaction rolled back, nothing persisted.')
      return true
    }

    addSecretVersion(password)
    out.line(`   Secret Manager: new version of ${SECRET_NAME} added (${GCP_PROJECT}); value fed via stdin, never printed`)
    await s.exec('COMMIT')
    committed = true
    out.line('   COMMIT: role, grants and password are live')
  } catch (error) {
    if (!committed) await client.query('ROLLBACK').catch(() => undefined)
    throw new Error(out.redact(error instanceof Error ? error.message : String(error)))
  } finally {
    client.release()
    await pool.end().catch(() => undefined)
  }

  out.section('Post-commit')
  if (!(await proveReaderLogin(out, route, password))) {
    out.line('RESULT: APPLIED BUT UNPROVEN — the role is committed and the password is in Secret Manager, but logging in as')
    out.line(`suvarna_reader failed; the credential file was NOT changed. Investigate, then re-run --apply (it resets the password).`)
    return false
  }
  writeCredentialFile(out, route.database, password)
  out.line('RESULT: APPLIED — suvarna_reader live, secret stored, credential file switched. Run the Monitor next.')
  return true
}

const USAGE = `Usage: SUVARNA_READER_ADMIN_DATABASE_URL=postgres://postgres:…@127.0.0.1:5433/<db> \\
  npx tsx scripts/suvarna-reader-bootstrap.ts [--dry-run | --apply] [--data-plane-gate-amended] [--accept-secdef=<sig>]…
  npx tsx scripts/suvarna-reader-bootstrap.ts --rollback [--dry-run | --apply]`

if (require.main === module) {
  let options: Options | 'help'
  try { options = parseArgs(process.argv.slice(2)) } catch (error) {
    console.error(error instanceof Error ? error.message : String(error))
    console.error(USAGE)
    process.exit(2)
  }
  if (options === 'help') { process.stdout.write(`${USAGE}\n`); process.exit(0) }
  const run = options.rollback ? runSuvarnaReaderRollback : runSuvarnaReaderBootstrap
  run(options).then((ok) => { process.exitCode = ok ? 0 : 1 }).catch((error) => {
    console.error(`suvarna-reader-bootstrap: ${error instanceof Error ? error.message : String(error)}`)
    process.exitCode = 1
  })
}
