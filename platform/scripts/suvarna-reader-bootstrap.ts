/**
 * Suvarṇa D6 one-shot administrator bootstrap: a genuinely read-only login `suvarna_reader`.
 *
 *   SUVARNA_READER_ADMIN_DATABASE_URL=postgres://postgres:…@127.0.0.1:5433/amjis \
 *     npx --no-install tsx scripts/suvarna-reader-bootstrap.ts [--dry-run | --apply --expect-plan=<sha256>]
 *       [--data-plane-gate-amended] [--accept-secdef=<schema.fn(argtypes)>]… [--accept-pii=<schema.rel>]…
 *       [--accept-view=<schema.rel>]…
 *
 * Why a privileged one-shot and not a migration: the routine migration runner (amjis_app) lost
 * CREATEROLE and table-grant rights in the data-plane / Nirmāṇa ownership handoffs. This follows the
 * administrator-bootstrap pattern of data-plane-ownership-preflight.ts: a dedicated admin URL that
 * authenticates directly as postgres, every grant made AS the object's owner (SET LOCAL ROLE), any
 * owner membership the admin lacks added only for the transaction and removed before it can commit.
 *
 * --dry-run (default): everything runs inside one transaction, the plan and every verification result
 *   are printed, then ROLLBACK. Nothing persists; no secret or file is written. The plan is printed in
 *   full together with its sha256 (targets + column-level grant spec + exclusion decisions).
 * --apply --expect-plan=<sha256>: the same transaction; the plan must hash to the reviewed dry-run
 *   value; if and only if every verification passes, the password is added to Secret Manager, the
 *   transaction COMMITs (if the COMMIT outcome is unknown the new secret version is disabled), the new
 *   login is proven by connecting as it, and only then is ~/.config/suvarna/pgenv.sh replaced. The
 *   previous (write-capable app-login) file is backed up to ~/.config/madhav-admin/ — never next to
 *   the reader credential — and older secret versions are disabled.
 * --rollback [--dry-run | --apply]: revokes every grant the reader holds AS ITS GRANTOR, drops the
 *   role, proves the same invariants, and (apply) restores pgenv.sh from
 *   ~/.config/madhav-admin/pgenv.app-login.bak, only if the current file is the reader's.
 *
 * The password is generated here (crypto random), never printed or logged. The database receives only
 * a client-computed SCRAM-SHA-256 verifier, so no statement text or server log carries the password.
 * The verifier itself can reach pg_stat_statements and server logs; after apply the matching
 * pg_stat_statements entries are reset (best effort, reported).
 *
 * DATA-PLANE GATE: `data-plane-ownership-status.ts` (run by every deploy) pins the public-schema ACL
 * exactly and allow-lists the grantees of every protected L1/L2 table. A reader with USAGE on public
 * and SELECT on those tables makes that gate fail the next deploy. Without --data-plane-gate-amended
 * this script therefore reports a DATA-PLANE GATE CONFLICT and fails; pass the flag only after a
 * reviewed amendment that tolerates `suvarna_reader` has been deployed (see the D6 runbook). The flag
 * is refused unless the checked-out sibling data-plane-ownership-status.ts names `suvarna_reader`.
 *
 * Every transaction starts with SET LOCAL search_path = pg_catalog, pg_temp and every relation is
 * schema-qualified, so no object in a user schema can shadow a catalog name or function.
 */
import { spawnSync } from 'node:child_process'
import { createHash, createHmac, pbkdf2Sync, randomBytes, randomInt } from 'node:crypto'
import {
  chmodSync, closeSync, constants as fsConstants, copyFileSync, existsSync, fsyncSync, lstatSync,
  mkdirSync, openSync, readFileSync, renameSync, unlinkSync, writeSync,
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
/** The reader's role defaults, exactly (pg_catalog.pg_db_role_setting, database-agnostic row). The Monitor
 *  compares against the same set (suvarna_tracker/monitor.py EXPECTED_ROLE_CONFIG). */
export const READER_ROLE_CONFIG = [
  ['default_transaction_read_only', 'on'],
  ['statement_timeout', '120s'],
  ['idle_in_transaction_session_timeout', '60s'],
  ['lock_timeout', '5s'],
] as const
// temp_file_limit is deliberately NOT a role default (review of 4b979ce52, M6): it is superuser-only, and the
// instance-level Cloud SQL flag bounds temp-file use for every role, the reader included.
/** Credential directory (read by the Monitor) and the separate admin directory that holds any
 *  backup of the write-capable app-login file — never the credential directory. */
export const CREDENTIAL_DIR = (): string => join(homedir(), '.config', 'suvarna')
export const ADMIN_BACKUP_DIR = (): string => join(homedir(), '.config', 'madhav-admin')
const APP_LOGIN_BACKUP = 'pgenv.app-login.bak'
const PASSWORD_LENGTH = 48
const PASSWORD_ALPHABET = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
const READ_SCHEMAS = ['public', 'nirmana_evidence'] as const

/** Always granted (must exist): control-plane tables Suvarṇa reads, plus `chart_grants` because the
 *  `charts` RLS policy reads it as the querying role. `charts` is granted COLUMN-level only (below). */
export const FIXED_READ_SET = [
  'asset_registry', 'asset_throughput', 'build_runs', 'build_run_assets',
  'asset_provenance_receipts', '_migrations_applied', 'charts', 'chart_grants',
] as const

/** Never granted, in public/nirmana_evidence (SQL LIKE patterns; schema `auth` is denied wholesale).
 *  Widening needs a reviewed edit of this list — that edit IS the native's approval. `mcp_api_keys` is
 *  added beyond the first review's list: it holds API-key material of the same class as `mcp_oauth_%`.
 *  Security review 2 added sessions/message parts, audit logs, AI user configuration and CLI grants,
 *  subject consent, managed prashna jobs, and the legacy user-content tables. */
export const DENY_PATTERNS = [
  'profiles', 'access_requests', 'conversation_%', 'mcp_oauth_%', 'ai_provider_connections',
  'mv_session_summary', 'query_baseline_stats', 'mcp_api_keys',
  'message_parts', 'mcp_sessions', 'planner_managed_prashna_jobs', 'admin_audit_log', 'audit_log',
  'audit_events', 'ai_custom_configurations', 'ai_user_defaults', 'ai_cli_grants', 'chart_subject_consent%',
  'messages', 'documents', 'reports', 'chat_attachments', 'message_feedback',
] as const

/** Tables data-plane-ownership-status.ts (the deploy gate) reads, so the post-apply gate run works as
 *  the reader (review of 4b979ce52, L7). Granted when present; absent while the data-plane boundary is unmarked. */
export const GATE_READ_SET = [
  'l1_data_plane_function_attestations', 'l1_data_plane_policy_attestations', 'l1_data_plane_view_attestations',
  'l1_data_plane_trigger_attestations', 'l1_data_plane_sequence_attestations',
  'l2_data_plane_function_attestations', 'l2_data_plane_policy_attestations', 'l2_data_plane_view_attestations',
  'l2_data_plane_trigger_attestations', 'l2_data_plane_sequence_attestations', 'l2_data_plane_manifest_attestations',
  'l2_data_plane_asset_outputs',
] as const

/** Column-level SELECT only (from 001_baseline.sql / 0001_brahma_baseline.sql). `charts`: columns with
 *  no birth data and no personal identifier. `chart_grants`: exactly what charts' chart_grant_policy
 *  subquery reads (chart_id, principal_id). Every other column — including any production column not
 *  named here — is withheld and printed as such. */
export const CHARTS_RELATION = 'charts'
export const CHARTS_GRANTED_COLUMNS = [
  'id', 'chart_id', 'role', 'ayanamsa', 'house_system', 'created_at', 'created_at_iso',
] as const
export const CHART_GRANTS_RELATION = 'chart_grants'
export const CHART_GRANTS_GRANTED_COLUMNS = ['chart_id', 'principal_id'] as const
export const COLUMN_GRANTS: Readonly<Record<string, readonly string[]>> = {
  [CHARTS_RELATION]: CHARTS_GRANTED_COLUMNS,
  [CHART_GRANTS_RELATION]: CHART_GRANTS_GRANTED_COLUMNS,
}

/** PII/identifier-looking column names (review of 4b979ce52, M2 widened). json/jsonb columns are flagged too. */
export const PII_COLUMN_REGEX =
  '(^|_)(email|phone|mobile|birth|dob|name|first_name|last_name|full_name|display_name|subject_name|preferred_name|'
  + 'lat|lng|lon|latitude|longitude|place|city|location|tz|timezone|address|ip|uid|principal_id|client_id|owner_id|'
  + 'user_id|granted_by|triggered_by|native_id|password|token|secret|api_key)(_|$)'

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
export interface Options {
  mode: Mode; rollback: boolean; dataPlaneGateAmended: boolean; acceptSecdef: string[]
  acceptPii: string[]; acceptView: string[]; expectPlan: string | null
}

/** Never echo argument text (it could be a pasted secret): a `--flag[=…]` shows only the flag name
 *  before '=' (and only if it looks like a flag name); anything else is "positional argument". */
export function describeArgument(arg: string): string {
  if (!arg.startsWith('--')) return 'positional argument'
  const name = arg.split('=', 1)[0]
  return /^--[A-Za-z0-9-]{1,40}$/.test(name) ? name : 'unrecognised flag'
}

export function parseArgs(argv: readonly string[]): Options | 'help' {
  let mode: Mode | null = null
  let rollback = false
  let dataPlaneGateAmended = false
  let expectPlan: string | null = null
  const acceptSecdef: string[] = []
  const acceptPii: string[] = []
  const acceptView: string[] = []
  const valueOf = (arg: string, flag: string): string | null =>
    arg.startsWith(`${flag}=`) && arg.length > flag.length + 1 ? arg.slice(flag.length + 1).trim() : null
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
    } else if (valueOf(arg, '--accept-secdef') !== null) {
      acceptSecdef.push(valueOf(arg, '--accept-secdef') as string)
    } else if (valueOf(arg, '--accept-pii') !== null) {
      acceptPii.push(valueOf(arg, '--accept-pii') as string)
    } else if (valueOf(arg, '--accept-view') !== null) {
      acceptView.push(valueOf(arg, '--accept-view') as string)
    } else if (valueOf(arg, '--expect-plan') !== null) {
      const sha = (valueOf(arg, '--expect-plan') as string).toLowerCase()
      if (!/^[0-9a-f]{64}$/.test(sha)) throw new Error('--expect-plan takes the 64-hex sha256 the dry run printed.')
      expectPlan = sha
    } else {
      throw new Error(`Unknown argument: ${describeArgument(arg)}`)
    }
  }
  if (rollback && (dataPlaneGateAmended || acceptSecdef.length || acceptPii.length || acceptView.length || expectPlan)) {
    throw new Error('--rollback takes only --dry-run or --apply.')
  }
  const resolved: Mode = mode ?? 'dry-run'
  if (!rollback && resolved === 'apply' && !expectPlan) {
    throw new Error('--apply requires --expect-plan=<sha256> from a reviewed dry run.')
  }
  return { mode: resolved, rollback, dataPlaneGateAmended, acceptSecdef, acceptPii, acceptView, expectPlan }
}

/** Strip TS and SQL comments so a comment can never satisfy the amendment match. Stripping can only
 *  remove text, so an odd case (a `--` inside a string) fails closed. */
export function stripComments(text: string): string {
  return text.replace(/\/\*[\s\S]*?\*\//g, ' ').replace(/\/\/[^\n]*/g, ' ').replace(/--[^\n]*/g, ' ')
}

/** The tolerant clauses runbook §0 specifies, as code: the conditional schema-ACL row for the reader,
 *  and the reader's SELECT exception in both the protected-table and the history-table ACL checks.
 *  Returns what is missing (empty = amendment present). */
export function gateAmendmentMissing(gateSource: string): string[] {
  const code = stripComments(gateSource)
  const missing: string[] = []
  if (!/SELECT\s+'suvarna_reader'\s*,\s*'USAGE'\s+WHERE\s+to_regrole\(\s*'suvarna_reader'\s*\)\s+IS\s+NOT\s+NULL/i.test(code)) {
    missing.push("schemaAcl row SELECT 'suvarna_reader','USAGE' WHERE to_regrole('suvarna_reader') IS NOT NULL")
  }
  const selectException = /AND\s+NOT\s*\(\s*\w+\.grantee\s*=\s*'suvarna_reader'\s+AND\s+\w+\.privilege_type\s*=\s*'SELECT'\s*\)/gi
  const n = code.match(selectException)?.length ?? 0
  if (n < 2) missing.push(`AND NOT (a.grantee='suvarna_reader' AND a.privilege_type='SELECT') in aclSurface and historyAcl (found ${n}/2)`)
  return missing
}

/** --data-plane-gate-amended is only credible if the gate this checkout would deploy carries the
 *  amendment's actual clauses. Resolved relative to this script's directory (the checked-out
 *  branch), never the cwd. */
export function assertGateAmendmentPresent(scriptDir: string = __dirname): void {
  const gate = join(scriptDir, 'data-plane-ownership-status.ts')
  let text: string
  try { text = readFileSync(gate, 'utf8') } catch {
    throw new Error('--data-plane-gate-amended refused: data-plane-ownership-status.ts not found next to this script.')
  }
  const missing = gateAmendmentMissing(text)
  if (missing.length) {
    throw new Error(`--data-plane-gate-amended refused: the checked-out data-plane-ownership-status.ts lacks the amendment clause(s): ${missing.join('; ')}.`)
  }
}

/** The plan the native reviews, in canonical form; its sha256 binds --apply to it (review of 4b979ce52, M5). */
export interface PlanSpec {
  targets: string[]
  columnGrants: Array<{ relation: string; granted: string[]; withheld: string[] }>
  excluded: Array<{ relation: string; reason: string }>
  /** Every readable PII/json column set, accepted or not (a non-accepted one fails the run anyway). */
  pii: Array<{ relation: string; columns: string[]; accepted: boolean }>
  acceptedSecdef: string[]
  staleRevokes: string[]
  scriptSha256: string
}

/** Code-unit order (never locale order), so the hash is identical on every machine. */
const byCodeUnit = (a: string, b: string): number => (a < b ? -1 : a > b ? 1 : 0)
const sortedCodeUnit = (items: readonly string[]): string[] => [...items].sort(byCodeUnit)

export function canonicalPlan(plan: PlanSpec): string {
  const lines: string[] = []
  const add = (...parts: unknown[]): void => { lines.push(JSON.stringify(parts)) }
  add('format', 'suvarna-reader-plan v2')
  add('script-sha256', plan.scriptSha256)
  add('connection-limit', CONNECTION_LIMIT)
  add('read-schemas', sortedCodeUnit(READ_SCHEMAS))
  for (const [k, v] of READER_ROLE_CONFIG) add('role-config', k, v)
  for (const t of plan.targets) add('target', t)
  for (const c of plan.columnGrants) add('columns', c.relation, sortedCodeUnit(c.granted), sortedCodeUnit(c.withheld))
  for (const e of plan.excluded) add('excluded', e.relation, e.reason)
  for (const p of plan.pii) add('pii', p.relation, sortedCodeUnit(p.columns), p.accepted ? 'accepted' : 'not-accepted')
  for (const f of plan.acceptedSecdef) add('accepted-secdef', f)
  for (const r of plan.staleRevokes) add('stale-revoke', r)
  return `${sortedCodeUnit(lines).join('\n')}\n`
}

export const planHash = (plan: PlanSpec): string => createHash('sha256').update(canonicalPlan(plan)).digest('hex')

/** sha256 of this script file itself, bound into the plan. */
export const scriptSha256 = (file: string = __filename): string => createHash('sha256').update(readFileSync(file)).digest('hex')

/** Redact base64-looking runs (>= 20 chars) from anything gcloud writes to stderr. */
export const redactGcloud = (text: string): string => text.replace(/[A-Za-z0-9+/=_-]{20,}/g, '[redacted]')

/** Minimal environment for gcloud: never the admin URL or anything else from the operator's shell. */
export function gcloudEnv(env: NodeJS.ProcessEnv = process.env): NodeJS.ProcessEnv {
  const out: NodeJS.ProcessEnv = {
    PATH: env.PATH ?? '/usr/bin:/bin', HOME: env.HOME ?? homedir(),
    CLOUDSDK_CORE_LOG_HTTP: 'false', CLOUDSDK_CORE_VERBOSITY: 'error',
  }
  if (env.CLOUDSDK_CONFIG) out.CLOUDSDK_CONFIG = env.CLOUDSDK_CONFIG
  return out
}

/** True iff one line of the file is exactly `PGUSER=suvarna_reader` (optionally `export `-prefixed).
 *  Only that predicate leaves this function; the buffer is zeroed. */
export function credentialFileIsReader(path: string): boolean {
  let buf: Buffer
  try { buf = readFileSync(path) } catch { return false }
  try {
    return buf.toString('utf8').split(/\r?\n/).some((line) => /^\s*(export\s+)?PGUSER=suvarna_reader\s*$/.test(line))
  } finally { buf.fill(0) }
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
  /** Prints every item unless a limit is passed explicitly (only the snapshot-diff diagnostics do). */
  list(label: string, items: readonly string[], limit = Number.POSITIVE_INFINITY): void {
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
      SELECT EXISTS (SELECT 1 FROM pg_catalog.pg_roles WHERE rolname=$1) AS exists,
             COALESCE((SELECT rolsuper FROM pg_catalog.pg_roles WHERE rolname=$1), false) AS superuser,
             COALESCE((SELECT pg_has_role(session_user, oid, 'MEMBER') FROM pg_catalog.pg_roles WHERE rolname=$1), false) AS member
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
      SELECT count(*)::text AS count FROM pg_catalog.pg_auth_members m
        JOIN pg_catalog.pg_roles parent ON parent.oid=m.roleid JOIN pg_catalog.pg_roles member ON member.oid=m.member
       WHERE member.rolname=$1 AND parent.rolname=ANY($2::text[])
    `, [ADMIN_ROLE, this.temporaryMemberships])
    if (left?.count !== '0') throw new Error('Temporary owner memberships did not converge to zero.')
  }
}

async function readerOid(s: Session): Promise<string | null> {
  const [row] = await s.rows<{ oid: string }>(`SELECT oid::text AS oid FROM pg_catalog.pg_roles WHERE rolname=$1`, [READER])
  return row?.oid ?? null
}

// ------------------------------------------------------------------------------------------------
// Snapshots: everything this run could conceivably disturb, excluding suvarna_reader's own rows.
// ------------------------------------------------------------------------------------------------

interface Snapshot { memberships: string[]; roles: string[]; acl: string[] }

async function takeSnapshot(s: Session, reader: string | null): Promise<Snapshot> {
  const memberships = (await s.rows<{ line: string }>(`
    SELECT format('%s|%s|%s|%s', pg_get_userbyid(roleid), pg_get_userbyid(member), pg_get_userbyid(grantor), admin_option) AS line
      FROM pg_catalog.pg_auth_members WHERE roleid IS DISTINCT FROM $1::oid AND member IS DISTINCT FROM $1::oid ORDER BY 1
  `, [reader])).map((r) => r.line)
  const roles = (await s.rows<{ line: string }>(`
    SELECT format('%s|super=%s|inherit=%s|createrole=%s|createdb=%s|login=%s|replication=%s|bypassrls=%s|connlimit=%s|validuntil=%s|config=%s|dbconfig=%s',
                  r.rolname, r.rolsuper, r.rolinherit, r.rolcreaterole, r.rolcreatedb, r.rolcanlogin, r.rolreplication, r.rolbypassrls,
                  r.rolconnlimit, COALESCE(r.rolvaliduntil::text, 'none'),
                  COALESCE(array_to_string(ARRAY(SELECT c FROM unnest(r.rolconfig) c ORDER BY c), ','), ''),
                  COALESCE((SELECT string_agg(format('%s:%s', s.setdatabase, array_to_string(s.setconfig, ',')), ';' ORDER BY s.setdatabase)
                              FROM pg_catalog.pg_db_role_setting s WHERE s.setrole=r.oid AND s.setdatabase<>0), '')) AS line
      FROM pg_catalog.pg_roles r WHERE r.oid IS DISTINCT FROM $1::oid ORDER BY 1
  `, [reader])).map((r) => r.line)
  // NULL ACLs are expanded to their defaults, so a GRANT that materialises an ACL does not register
  // as a change to anyone but the grantee.
  const acl = (await s.rows<{ line: string }>(`
    WITH scope AS (SELECT oid FROM pg_catalog.pg_namespace WHERE nspname !~ '^pg_toast' AND nspname !~ '^pg_temp_'),
         user_scope AS (SELECT oid FROM scope WHERE oid NOT IN (SELECT oid FROM pg_catalog.pg_namespace WHERE nspname IN ('pg_catalog','information_schema'))),
    entries AS (
      SELECT 'rel' AS kind, format('%I.%I', n.nspname, c.relname) AS object, a.grantor, a.grantee, a.privilege_type, a.is_grantable
        FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace
        CROSS JOIN LATERAL aclexplode(COALESCE(c.relacl, acldefault(CASE WHEN c.relkind='S' THEN 's'::"char" ELSE 'r'::"char" END, c.relowner))) a
       WHERE c.relnamespace IN (SELECT oid FROM scope) AND c.relkind IN ('r','p','v','m','f','S')
      UNION ALL
      SELECT 'col', format('%I.%I(%I)', n.nspname, c.relname, at.attname), a.grantor, a.grantee, a.privilege_type, a.is_grantable
        FROM pg_catalog.pg_attribute at JOIN pg_catalog.pg_class c ON c.oid=at.attrelid JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace
        CROSS JOIN LATERAL aclexplode(at.attacl) a WHERE at.attacl IS NOT NULL
      UNION ALL
      SELECT 'nsp', n.nspname::text, a.grantor, a.grantee, a.privilege_type, a.is_grantable
        FROM pg_catalog.pg_namespace n CROSS JOIN LATERAL aclexplode(COALESCE(n.nspacl, acldefault('n', n.nspowner))) a
      UNION ALL
      SELECT 'fn', format('%s:%s', p.oid, p.proname), a.grantor, a.grantee, a.privilege_type, a.is_grantable
        FROM pg_catalog.pg_proc p CROSS JOIN LATERAL aclexplode(COALESCE(p.proacl, acldefault('f', p.proowner))) a
       WHERE p.pronamespace IN (SELECT oid FROM user_scope)
      UNION ALL
      SELECT 'type', format('%s:%s', t.oid, t.typname), a.grantor, a.grantee, a.privilege_type, a.is_grantable
        FROM pg_catalog.pg_type t CROSS JOIN LATERAL aclexplode(COALESCE(t.typacl, acldefault('T', t.typowner))) a
       WHERE t.typnamespace IN (SELECT oid FROM user_scope)
      UNION ALL
      SELECT 'db', d.datname::text, a.grantor, a.grantee, a.privilege_type, a.is_grantable
        FROM pg_catalog.pg_database d CROSS JOIN LATERAL aclexplode(COALESCE(d.datacl, acldefault('d', d.datdba))) a
      UNION ALL
      SELECT 'defacl', format('%s/%s/%s', pg_get_userbyid(d.defaclrole), d.defaclnamespace, d.defaclobjtype), a.grantor, a.grantee, a.privilege_type, a.is_grantable
        FROM pg_catalog.pg_default_acl d CROSS JOIN LATERAL aclexplode(d.defaclacl) a
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
      SELECT (SELECT oid FROM pg_catalog.pg_namespace WHERE nspname='nirmana_evidence') AS ev_ns,
             (SELECT oid FROM pg_catalog.pg_namespace WHERE nspname='public') AS pub_ns,
             (SELECT oid FROM pg_catalog.pg_roles WHERE rolname='amjis_app') AS app,
             (SELECT oid FROM pg_catalog.pg_roles WHERE rolname='nirmana_evidence_owner') AS ev_owner,
             (SELECT oid FROM pg_catalog.pg_roles WHERE rolname='nirmana_evidence_ingress_writer') AS ingress,
             (SELECT oid FROM pg_catalog.pg_roles WHERE rolname='nirmana_campaign_control_writer') AS control,
             (SELECT oid FROM pg_catalog.pg_roles WHERE rolname='nirmana_migrator') AS migrator
    )
    SELECT
      COALESCE(EXISTS (SELECT 1 FROM pg_catalog.pg_roles WHERE rolname='nirmana_evidence_owner' AND NOT rolcanlogin AND NOT rolinherit
        AND NOT rolsuper AND NOT rolcreatedb AND NOT rolcreaterole AND NOT rolreplication AND NOT rolbypassrls), false) AS n1_evidence_owner_normalized,
      COALESCE(NOT EXISTS (SELECT 1 FROM pg_catalog.pg_auth_members m JOIN pg_catalog.pg_roles r ON r.oid=m.roleid OR r.oid=m.member
        WHERE r.rolname=ANY($1::text[])), false) AS n2_protected_roles_no_memberships,
      COALESCE(EXISTS (SELECT 1 FROM pg_catalog.pg_namespace ns JOIN pg_catalog.pg_roles o ON o.oid=ns.nspowner WHERE ns.nspname='nirmana_evidence' AND o.rolname='nirmana_evidence_owner')
        AND (SELECT count(*) FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace JOIN pg_catalog.pg_roles o ON o.oid=c.relowner
             WHERE n.nspname='nirmana_evidence' AND c.relname=ANY($2::text[]) AND c.relkind IN ('r','p') AND o.rolname='nirmana_evidence_owner') = 3
        AND (SELECT count(*) FROM pg_catalog.pg_proc p JOIN pg_catalog.pg_namespace n ON n.oid=p.pronamespace JOIN pg_catalog.pg_roles o ON o.oid=p.proowner
             WHERE n.nspname='nirmana_evidence' AND p.proname=ANY($3::text[]) AND o.rolname='nirmana_evidence_owner') = 6, false) AS n3_evidence_ownership,
      COALESCE(EXISTS (SELECT 1 FROM pg_catalog.pg_roles WHERE rolname='amjis_app' AND rolcanlogin
        AND NOT (rolinherit OR rolcreatedb OR rolcreaterole OR rolsuper OR rolreplication OR rolbypassrls)), false) AS n4_app_attributes,
      COALESCE((SELECT NOT EXISTS (SELECT 1 FROM pg_catalog.pg_auth_members m WHERE m.roleid=ids.app OR m.member=ids.app)
        AND NOT EXISTS (SELECT 1 FROM pg_catalog.pg_database d WHERE d.datname=current_database() AND (d.datdba=ids.app OR pg_has_role(ids.app, d.datdba, 'MEMBER')))
        AND NOT has_database_privilege(ids.app, current_database(), 'CREATE')
        AND NOT has_schema_privilege(ids.app, ids.ev_ns, 'CREATE')
        AND has_schema_privilege(ids.app, ids.ev_ns, 'USAGE') FROM ids), false) AS n5_app_no_administration,
      COALESCE(NOT EXISTS (
        WITH RECURSIVE provider_roots(oid, depth) AS (
          SELECT datdba, 0 FROM pg_catalog.pg_database WHERE datname=current_database()
          UNION ALL
          SELECT m.member, parent.depth + 1 FROM pg_catalog.pg_auth_members m JOIN provider_roots parent ON parent.oid=m.roleid
        )
        SELECT 1 FROM provider_roots root JOIN pg_catalog.pg_roles role ON role.oid=root.oid
          JOIN pg_catalog.pg_database database ON database.datname=current_database()
         WHERE NOT (root.oid=database.datdba
           OR (root.depth=1 AND role.rolname='postgres' AND NOT role.rolsuper AND NOT role.rolreplication AND NOT role.rolbypassrls)
           OR (root.depth=1 AND role.rolname IN ('cloudsqlagent','cloudsqlimportexport','cloudsqllogical')))
      ), false) AS n6_provider_topology_bounded,
      COALESCE((SELECT count(*) FROM pg_catalog.pg_roles WHERE rolname IN ('nirmana_evidence_ingress_writer','nirmana_campaign_control_writer','nirmana_migrator')
        AND rolcanlogin AND NOT rolinherit AND NOT rolsuper AND NOT rolcreatedb AND NOT rolcreaterole AND NOT rolreplication AND NOT rolbypassrls) = 3, false) AS n7_writer_logins_normalized,
      COALESCE((SELECT NOT EXISTS (SELECT 1 FROM pg_catalog.pg_class c WHERE c.relnamespace=ids.ev_ns AND c.relname=ANY($2::text[])
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
    WITH pub AS (SELECT oid FROM pg_catalog.pg_namespace WHERE nspname='public'),
    protected AS (
      SELECT c.oid, c.relname, c.relowner, c.relacl, CASE WHEN c.relname=ANY($1::text[]) THEN 'L1' ELSE 'L2' END AS layer
        FROM pg_catalog.pg_class c WHERE c.relnamespace=(SELECT oid FROM pub) AND c.relname=ANY($1::text[] || $2::text[])
    ),
    history AS (
      SELECT c.oid, c.relname, c.relowner, c.relacl,
             CASE WHEN starts_with(c.relname,'l1_data_plane_') THEN 'L1' ELSE 'L2' END AS layer
        FROM pg_catalog.pg_class c WHERE c.relnamespace=(SELECT oid FROM pub) AND c.relkind IN ('r','p','v','m')
         AND (starts_with(c.relname,'l1_data_plane_') OR starts_with(c.relname,'l2_data_plane_') OR c.relname='data_plane_l2_producer_generations')
    ),
    prot_actual AS (
      SELECT p.relname, p.layer, COALESCE(r.rolname,'PUBLIC') AS grantee, pg_get_userbyid(p.relowner) AS owner_name, a.privilege_type
        FROM protected p CROSS JOIN LATERAL aclexplode(COALESCE(p.relacl, acldefault('r', p.relowner))) a LEFT JOIN pg_catalog.pg_roles r ON r.oid=a.grantee
    ),
    hist_actual AS (
      SELECT h.relname, h.layer, COALESCE(r.rolname,'PUBLIC') AS grantee, pg_get_userbyid(h.relowner) AS owner_name, a.privilege_type
        FROM history h CROSS JOIN LATERAL aclexplode(COALESCE(h.relacl, acldefault('r', h.relowner))) a LEFT JOIN pg_catalog.pg_roles r ON r.oid=a.grantee
    ),
    allowed(grantee, privilege_type) AS (VALUES
      ('data_plane_builder','SELECT'),('data_plane_builder','INSERT'),('data_plane_builder','UPDATE'),('data_plane_builder','DELETE'),
      ('amjis_app','SELECT'),('data_plane_verifier','SELECT'),('data_plane_migrator','SELECT')
    ),
    schema_actual AS (
      SELECT COALESCE(r.rolname,'PUBLIC') AS grantee, a.privilege_type
        FROM pg_catalog.pg_namespace n CROSS JOIN LATERAL aclexplode(COALESCE(n.nspacl, acldefault('n', n.nspowner))) a
        LEFT JOIN pg_catalog.pg_roles r ON r.oid=a.grantee WHERE n.nspname='public'
    ),
    schema_expected(grantee, privilege_type) AS (
      SELECT * FROM (VALUES
        ('data_plane_schema_owner','USAGE'),('data_plane_schema_owner','CREATE'),
        ('data_plane_l1_owner','USAGE'),('data_plane_l1_owner','CREATE'),
        ('data_plane_l2_owner','USAGE'),('data_plane_l2_owner','CREATE'),
        ('data_plane_migrator','USAGE'),('data_plane_builder','USAGE'),
        ('data_plane_verifier','USAGE'),('amjis_app','USAGE'),('role_web_serve','USAGE')
      ) base(grantee, privilege_type)
      UNION ALL SELECT 'purna_inquiry_owner','USAGE' WHERE EXISTS (SELECT 1 FROM pg_catalog.pg_roles WHERE rolname='purna_inquiry_owner')
      UNION ALL SELECT $3::text,'USAGE' WHERE $4::boolean AND EXISTS (SELECT 1 FROM pg_catalog.pg_roles WHERE rolname=$3::text)
    ),
    seq_protected AS (
      SELECT DISTINCT seq.oid FROM pg_catalog.pg_class tab
        JOIN pg_catalog.pg_depend dep ON dep.refobjid=tab.oid AND dep.refclassid='pg_catalog.pg_class'::regclass AND dep.classid='pg_catalog.pg_class'::regclass AND dep.deptype IN ('a','i')
        JOIN pg_catalog.pg_class seq ON seq.oid=dep.objid AND seq.relkind='S'
       WHERE tab.relnamespace=(SELECT oid FROM pub) AND tab.relname=ANY($1::text[] || $2::text[])
    ),
    seq_actual AS (
      SELECT p.oid, COALESCE(r.rolname,'PUBLIC') AS grantee, pg_get_userbyid(c.relowner) AS owner_name, a.privilege_type
        FROM seq_protected p JOIN pg_catalog.pg_class c ON c.oid=p.oid
        CROSS JOIN LATERAL aclexplode(COALESCE(c.relacl, acldefault('s', c.relowner))) a LEFT JOIN pg_catalog.pg_roles r ON r.oid=a.grantee
    ),
    seq_expected(grantee, privilege_type) AS (VALUES
      ('data_plane_builder','SELECT'),('data_plane_builder','USAGE'),('amjis_app','SELECT'),('data_plane_verifier','SELECT'),('data_plane_migrator','SELECT')
    ),
    roles AS (
      SELECT (SELECT oid FROM pg_catalog.pg_roles WHERE rolname='amjis_app') AS app,
             (SELECT oid FROM pg_catalog.pg_roles WHERE rolname='data_plane_builder') AS builder,
             (SELECT oid FROM pg_catalog.pg_roles WHERE rolname='role_orchestrator') AS orchestrator
    )
    SELECT
      COALESCE((SELECT count(*) FROM pg_catalog.pg_roles
        WHERE (rolname IN ('data_plane_schema_owner','data_plane_l1_owner','data_plane_l2_owner')
               AND NOT rolcanlogin AND NOT rolinherit AND NOT rolsuper AND NOT rolcreaterole AND NOT rolcreatedb AND NOT rolreplication AND NOT rolbypassrls)
           OR (rolname IN ('data_plane_migrator','data_plane_builder','data_plane_verifier')
               AND rolcanlogin AND NOT rolinherit AND NOT rolsuper AND NOT rolcreaterole AND NOT rolcreatedb AND NOT rolreplication AND NOT rolbypassrls)) = 6
        AND NOT EXISTS (SELECT 1 FROM pg_catalog.pg_roles WHERE rolname LIKE 'data\\_plane\\_%' ESCAPE '\\' AND rolname <> ALL(ARRAY[
          'data_plane_schema_owner','data_plane_l1_owner','data_plane_l2_owner','data_plane_migrator','data_plane_builder','data_plane_verifier'])), false)
        AS d1_roles_normalized,
      COALESCE(pg_get_userbyid((SELECT nspowner FROM pg_catalog.pg_namespace WHERE nspname='public'))='data_plane_schema_owner'
        AND NOT EXISTS (
          WITH controlled(role_name) AS (SELECT unnest(ARRAY['data_plane_schema_owner','data_plane_l1_owner','data_plane_l2_owner','data_plane_migrator','data_plane_builder','data_plane_verifier'])),
          actual AS (SELECT parent.rolname AS parent_role, member.rolname AS member_role FROM pg_catalog.pg_auth_members m
                       JOIN pg_catalog.pg_roles parent ON parent.oid=m.roleid JOIN pg_catalog.pg_roles member ON member.oid=m.member
                      WHERE parent.rolname IN (SELECT role_name FROM controlled) OR member.rolname IN (SELECT role_name FROM controlled)),
          expected(parent_role, member_role) AS (VALUES ('data_plane_schema_owner','data_plane_migrator'),('data_plane_l1_owner','data_plane_migrator'),('data_plane_l2_owner','data_plane_migrator'))
          SELECT 1 FROM actual a FULL JOIN expected e USING (parent_role, member_role) WHERE a.parent_role IS NULL OR e.parent_role IS NULL)
        AND NOT EXISTS (
          WITH RECURSIVE reach(roleid, member) AS (
            SELECT roleid, member FROM pg_catalog.pg_auth_members
            UNION SELECT r.roleid, m.member FROM reach r JOIN pg_catalog.pg_auth_members m ON m.roleid=r.member)
          SELECT 1 FROM reach x JOIN pg_catalog.pg_roles owner ON owner.oid=x.roleid JOIN pg_catalog.pg_roles member ON member.oid=x.member
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
      COALESCE(EXISTS (SELECT 1 FROM pg_catalog.pg_roles r WHERE r.rolname='purna_inquiry_owner'
        AND NOT r.rolcanlogin AND NOT r.rolinherit AND NOT r.rolsuper AND NOT r.rolcreatedb AND NOT r.rolcreaterole AND NOT r.rolreplication AND NOT r.rolbypassrls
        AND NOT EXISTS (SELECT 1 FROM pg_catalog.pg_auth_members m WHERE m.roleid=r.oid OR m.member=r.oid)
        AND NOT has_schema_privilege(r.oid, (SELECT oid FROM pg_catalog.pg_namespace WHERE nspname='public'), 'CREATE')
        AND has_schema_privilege(r.oid, (SELECT oid FROM pg_catalog.pg_namespace WHERE nspname='public'), 'USAGE')), false) AS p1_owner_protected,
      COALESCE(EXISTS (SELECT 1 FROM pg_catalog.pg_roles r WHERE r.rolname='amjis_inquiry_serve'
        AND r.rolcanlogin AND r.rolinherit AND NOT r.rolsuper AND NOT r.rolcreatedb AND NOT r.rolcreaterole AND NOT r.rolreplication AND NOT r.rolbypassrls
        AND (SELECT count(*) FROM pg_catalog.pg_auth_members m WHERE m.member=r.oid) = 1
        AND EXISTS (SELECT 1 FROM pg_catalog.pg_auth_members m JOIN pg_catalog.pg_roles p ON p.oid=m.roleid WHERE p.rolname='role_web_serve' AND m.member=r.oid)
        AND NOT EXISTS (SELECT 1 FROM pg_catalog.pg_auth_members m WHERE m.roleid=r.oid)), false) AS p2_serving_login_normalized,
      COALESCE((SELECT count(*) = 0 FROM pg_catalog.pg_auth_members m JOIN pg_catalog.pg_roles r ON r.oid=m.roleid OR r.oid=m.member
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
      FROM pg_catalog.pg_auth_members WHERE roleid=$1::oid OR member=$1::oid ORDER BY 1, 2
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

/** `relation` is the schema-qualified relation for kind relation/column (quoted identifiers). */
interface ReaderGrant { kind: string; object: string; objectOid: string; subkind: string; grantor: string; privilege: string; relation: string }

async function readerGrants(s: Session, reader: string): Promise<ReaderGrant[]> {
  return s.rows<ReaderGrant>(`
    SELECT 'relation' AS kind, format('%I.%I', n.nspname, c.relname) AS object, c.oid::text AS "objectOid", c.relkind::text AS subkind,
           pg_get_userbyid(a.grantor) AS grantor, a.privilege_type AS privilege, format('%I.%I', n.nspname, c.relname) AS relation
      FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace CROSS JOIN LATERAL aclexplode(c.relacl) a WHERE a.grantee=$1::oid
    UNION ALL
    SELECT 'column', format('%I.%I(%I)', n.nspname, c.relname, at.attname), c.oid::text, c.relkind::text, pg_get_userbyid(a.grantor), a.privilege_type,
           format('%I.%I', n.nspname, c.relname)
      FROM pg_catalog.pg_attribute at JOIN pg_catalog.pg_class c ON c.oid=at.attrelid JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace
      CROSS JOIN LATERAL aclexplode(at.attacl) a WHERE a.grantee=$1::oid
    UNION ALL
    SELECT 'schema', n.nspname, n.oid::text, '', pg_get_userbyid(a.grantor), a.privilege_type, ''
      FROM pg_catalog.pg_namespace n CROSS JOIN LATERAL aclexplode(n.nspacl) a WHERE a.grantee=$1::oid
    UNION ALL
    SELECT 'function', p.oid::regprocedure::text, p.oid::text, '', pg_get_userbyid(a.grantor), a.privilege_type, ''
      FROM pg_catalog.pg_proc p CROSS JOIN LATERAL aclexplode(p.proacl) a WHERE a.grantee=$1::oid
    UNION ALL
    SELECT 'type', t.oid::regtype::text, t.oid::text, '', pg_get_userbyid(a.grantor), a.privilege_type, ''
      FROM pg_catalog.pg_type t CROSS JOIN LATERAL aclexplode(t.typacl) a WHERE a.grantee=$1::oid
    UNION ALL
    SELECT 'database', d.datname, d.oid::text, CASE WHEN d.datname=current_database() THEN 'current' ELSE 'other' END,
           pg_get_userbyid(a.grantor), a.privilege_type, ''
      FROM pg_catalog.pg_database d CROSS JOIN LATERAL aclexplode(d.datacl) a WHERE a.grantee=$1::oid
    UNION ALL
    SELECT 'default_acl', format('%s/%s/%s', pg_get_userbyid(d.defaclrole), d.defaclnamespace, d.defaclobjtype), '', '',
           pg_get_userbyid(a.grantor), a.privilege_type, ''
      FROM pg_catalog.pg_default_acl d CROSS JOIN LATERAL aclexplode(d.defaclacl) a WHERE a.grantee=$1::oid
    ORDER BY 1, 2, 6
  `, [reader])
}

const COLUMN_GRANT_FQ = new Set(Object.keys(COLUMN_GRANTS).map((name) => `public.${name}`))

/** Only the shapes this script itself creates are acceptable on a pre-existing reader: table SELECT,
 *  column SELECT on the column-granted relations only, USAGE on the read schemas, CONNECT here. */
function unexpectedReaderGrants(grants: readonly ReaderGrant[]): ReaderGrant[] {
  return grants.filter((g) => !(
    (g.kind === 'relation' && g.privilege === 'SELECT' && ['r', 'p', 'v', 'm', 'f'].includes(g.subkind))
    || (g.kind === 'column' && g.privilege === 'SELECT' && COLUMN_GRANT_FQ.has(g.relation))
    || (g.kind === 'schema' && g.privilege === 'USAGE' && (READ_SCHEMAS as readonly string[]).includes(g.object))
    || (g.kind === 'database' && g.subkind === 'current' && g.privilege === 'CONNECT')
  ))
}

/** Catch-all: ACL shared dependencies of the reader anywhere in the cluster, except the ones its
 *  intended grants produce — relation/column SELECT (pg_catalog.pg_class) and schema USAGE (pg_catalog.pg_namespace) in the
 *  current database, and CONNECT (pg_catalog.pg_database, recorded with dbid 0 because pg_catalog.pg_database is shared).
 *  Anything else — function/type/large-object/default-ACL grants, or any grant in another database —
 *  counts. Must be 0. */
async function sharedAclDependenciesOutsideScope(s: Session, reader: string): Promise<number> {
  const [row] = await s.rows<{ count: string }>(`
    SELECT count(*)::text AS count FROM pg_catalog.pg_shdepend
     WHERE refclassid='pg_catalog.pg_authid'::regclass AND refobjid=$1::oid AND deptype='a'
       AND NOT (dbid=(SELECT oid FROM pg_catalog.pg_database WHERE datname=current_database())
                AND classid IN ('pg_catalog.pg_class'::regclass, 'pg_catalog.pg_namespace'::regclass))
       AND NOT (dbid=0 AND classid='pg_catalog.pg_database'::regclass)
  `, [reader])
  return Number(row?.count ?? -1)
}

async function inspectExistingReader(s: Session, reader: string, version: number): Promise<ReaderGrant[]> {
  const [attrs] = await s.rows<{ elevated: boolean }>(`
    SELECT rolsuper OR rolcreaterole OR rolcreatedb OR rolreplication OR rolbypassrls AS elevated FROM pg_catalog.pg_roles WHERE oid=$1::oid
  `, [reader])
  if (attrs?.elevated) throw new Error(`Refusing pre-existing ${READER}: it carries elevated role attributes.`)
  const edges = await readerEdges(s, reader, version)
  if (edges.memberOf.length || edges.membersOfReader.length) {
    throw new Error(`Refusing pre-existing ${READER}: it has role memberships (${[...edges.memberOf, ...edges.membersOfReader].join('; ')}).`)
  }
  const [owns] = await s.rows<{ count: string }>(`
    SELECT ((SELECT count(*) FROM pg_catalog.pg_shdepend WHERE refclassid='pg_catalog.pg_authid'::regclass AND refobjid=$1::oid AND deptype='o')
          + (SELECT count(*) FROM pg_catalog.pg_database WHERE datdba=$1::oid))::text AS count
  `, [reader])
  if (owns?.count !== '0') throw new Error(`Refusing pre-existing ${READER}: it owns ${owns?.count} object(s) (any database).`)
  const outside = await sharedAclDependenciesOutsideScope(s, reader)
  if (outside !== 0) throw new Error(`Refusing pre-existing ${READER}: ${outside} ACL dependenc(ies) outside this database's relations/schemas/CONNECT (pg_catalog.pg_shdepend).`)
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

interface ColumnGrant { relation: Relation; granted: string[]; withheld: string[]; missingAllowed: string[] }

interface ReadSet {
  /** Every relation the reader will read; table-level SELECT except those in columnGrants. */
  targets: Relation[]
  denied: Array<Relation & { reason: string }>
  unresolvedRegistry: string[]
  columnGrants: ColumnGrant[]
  /** Read-set views kept only because of --accept-view, with the RLS tables they reach. */
  acceptedViews: string[]
}

/** L2: amjis_app reads its own control tables. Assert each is a plain table (a view or foreign table
 *  would run someone else's code as amjis_app) and read with row_security off, so a policy can only
 *  make the read fail loudly, never filter it silently. */
async function readAsApp<T>(s: Session, tables: readonly string[], fn: () => Promise<T>): Promise<T> {
  const kinds = await s.rows<{ name: string; relkind: string | null }>(`
    SELECT t.name, c.relkind::text AS relkind FROM unnest($1::text[]) t(name)
      LEFT JOIN pg_catalog.pg_class c ON c.relname=t.name
       AND c.relnamespace=(SELECT oid FROM pg_catalog.pg_namespace WHERE nspname='public')
  `, [[...tables]])
  const bad = kinds.filter((k) => k.relkind !== 'r')
  if (bad.length) throw new Error(`Refusing to read as amjis_app: ${bad.map((k) => `public.${k.name} relkind=${k.relkind ?? 'absent'}`).join(', ')} (must be ordinary tables).`)
  await s.exec('SET LOCAL row_security = off')
  const result = await s.asRole('amjis_app', fn)
  await s.exec('SET LOCAL row_security = on')
  return result
}

/** Per view/matview root: RLS tables, column-granted relations and withheld columns in its
 *  dependency closure, and whether it (or any view on the way) runs with definer rights. */
interface ViewReach { oid: string; name: string; relkind: string; rls: string | null; cg: string | null; withheld: string | null; definer: boolean }

async function viewReach(s: Session, rootOids: readonly string[], cg: readonly ColumnGrant[]): Promise<Map<string, ViewReach>> {
  if (!rootOids.length) return new Map()
  const withheldRel = cg.flatMap((c) => c.withheld.map(() => c.relation.oid))
  const withheldCol = cg.flatMap((c) => c.withheld)
  const rows = await s.rows<ViewReach>(`
    WITH RECURSIVE dep(root, ref) AS (
      SELECT r.oid, r.oid FROM unnest($1::oid[]) r(oid)
      UNION
      SELECT dep.root, d.refobjid FROM dep JOIN pg_catalog.pg_rewrite rw ON rw.ev_class=dep.ref
        JOIN pg_catalog.pg_depend d ON d.classid='pg_catalog.pg_rewrite'::regclass AND d.objid=rw.oid
         AND d.refclassid='pg_catalog.pg_class'::regclass AND d.refobjid<>rw.ev_class
    ),
    info AS (
      SELECT c.oid, c.relkind, c.relrowsecurity, format('%s.%s', n.nspname, c.relname) AS name,
             (c.relkind='v' AND EXISTS (SELECT 1 FROM unnest(COALESCE(c.reloptions, ARRAY[]::text[])) o
                WHERE lower(o) IN ('security_invoker=true','security_invoker=on','security_invoker=1','security_invoker=yes'))) AS invoker
        FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace
    ),
    withheld_refs AS (
      SELECT DISTINCT dep.root, format('%s(%I)', a.attrelid::regclass::text, a.attname) AS col
        FROM dep JOIN pg_catalog.pg_rewrite rw ON rw.ev_class=dep.ref
        JOIN pg_catalog.pg_depend d ON d.classid='pg_catalog.pg_rewrite'::regclass AND d.objid=rw.oid
         AND d.refclassid='pg_catalog.pg_class'::regclass AND d.refobjsubid > 0
        JOIN pg_catalog.pg_attribute a ON a.attrelid=d.refobjid AND a.attnum=d.refobjsubid
        JOIN unnest($3::oid[], $4::text[]) w(rel, col) ON w.rel=a.attrelid AND w.col=a.attname
    ),
    agg AS (
      SELECT dep.root,
             string_agg(DISTINCT t.name, ', ' ORDER BY t.name) FILTER (WHERE dep.ref<>dep.root AND t.relrowsecurity AND t.relkind IN ('r','p')) AS rls,
             string_agg(DISTINCT t.name, ', ' ORDER BY t.name) FILTER (WHERE dep.ref<>dep.root AND t.oid=ANY($2::oid[])) AS cg,
             bool_or(t.relkind IN ('v','m') AND NOT t.invoker) AS definer
        FROM dep JOIN info t ON t.oid=dep.ref GROUP BY dep.root
    )
    SELECT agg.root::text AS oid, root.name, root.relkind::text AS relkind, agg.rls, agg.cg,
           (SELECT string_agg(w.col, ', ' ORDER BY w.col) FROM withheld_refs w WHERE w.root=agg.root) AS withheld,
           COALESCE(agg.definer, false) AS definer
      FROM agg JOIN info root ON root.oid=agg.root
  `, [[...rootOids], cg.map((c) => c.relation.oid), withheldRel, withheldCol])
  return new Map(rows.map((r) => [r.oid, r]))
}

/** Why a view/matview must not be readable, or null. Reading a withheld column, or reaching a
 *  column-granted relation with definer rights, is never acceptable (it would undo the column grant);
 *  reaching an RLS table with definer rights is acceptable only via --accept-view. */
export function viewVerdict(v: Pick<ViewReach, 'relkind' | 'rls' | 'cg' | 'withheld' | 'definer'>, accepted: boolean):
  { reason: string; overridable: boolean } | null {
  const kind = v.relkind === 'm' ? 'materialized view' : 'view'
  if (v.withheld) return { reason: `${kind} reads withheld column(s): ${v.withheld}`, overridable: false }
  if (v.cg && v.definer) return { reason: `${kind} with definer rights reaches column-granted relation(s): ${v.cg}`, overridable: false }
  if (v.rls && v.definer && !accepted) return { reason: `${kind} without security_invoker reaches RLS table(s): ${v.rls}`, overridable: true }
  return null
}

async function computeReadSet(s: Session, options: Options): Promise<ReadSet> {
  const [census] = await s.rows<{ exists: boolean }>(`SELECT EXISTS (SELECT 1 FROM pg_catalog.pg_roles WHERE rolname=$1) AS exists`, [CENSUS_ROLE])
  if (!census?.exists) throw new Error(`${CENSUS_ROLE} is absent: the census half of the read set cannot be derived. Refusing.`)
  // asset_registry is only readable through its owner's public-schema USAGE.
  const registryRaw = await readAsApp(s, ['asset_registry'], () => s.rows<{ t: string }>(`
    SELECT DISTINCT btrim(target_table) AS t FROM public.asset_registry
     WHERE target_table IS NOT NULL AND btrim(target_table) <> '' ORDER BY 1
  `))
  const registryNames = registryRaw.map((r) => r.t.replace(/^public\./, ''))
  const relations = await s.rows<Relation>(`
    WITH schemas AS (SELECT oid, nspname FROM pg_catalog.pg_namespace WHERE nspname=ANY($3::text[])),
    rels AS (SELECT c.oid, c.relname, c.relkind, c.relowner, s.nspname FROM pg_catalog.pg_class c JOIN schemas s ON s.oid=c.relnamespace
              WHERE c.relkind IN ('r','p','v','m','f')),
    census AS (SELECT r.oid, 'census' AS src FROM rels r WHERE has_table_privilege((SELECT oid FROM pg_catalog.pg_roles WHERE rolname=$4), r.oid, 'SELECT')),
    registry AS (SELECT r.oid, 'asset_registry' AS src FROM rels r WHERE r.nspname='public' AND r.relname=ANY($1::text[])),
    fixed AS (SELECT r.oid, 'fixed' AS src FROM rels r WHERE r.nspname='public' AND r.relname=ANY($2::text[])),
    gate AS (SELECT r.oid, 'gate' AS src FROM rels r WHERE r.nspname='public' AND r.relname=ANY($5::text[])),
    evidence AS (SELECT r.oid, 'nirmana_evidence' AS src FROM rels r WHERE r.nspname='nirmana_evidence'),
    sources AS (SELECT * FROM census UNION ALL SELECT * FROM registry UNION ALL SELECT * FROM fixed UNION ALL SELECT * FROM gate
                UNION ALL SELECT * FROM evidence)
    SELECT r.oid::text AS oid, r.nspname AS schema, r.relname AS name, r.relkind::text AS relkind,
           pg_get_userbyid(r.relowner) AS owner, array_agg(DISTINCT s.src ORDER BY s.src) AS sources
      FROM sources s JOIN rels r ON r.oid=s.oid GROUP BY 1, 2, 3, 4, 5 ORDER BY 2, 3
  `, [registryNames, [...FIXED_READ_SET], [...READ_SCHEMAS], CENSUS_ROLE, [...GATE_READ_SET]])
  const present = new Set(relations.filter((r) => r.schema === 'public').map((r) => r.name))
  const missingFixed = FIXED_READ_SET.filter((name) => !present.has(name))
  if (missingFixed.length) throw new Error(`Required read-set relations are absent from public: ${missingFixed.join(', ')}.`)
  const unresolvedRegistry = registryRaw.map((r) => r.t).filter((t) => !present.has(t.replace(/^public\./, '')))

  // Column-level grants (charts, chart_grants) are decided first: view exclusion depends on them.
  const columnGrants: ColumnGrant[] = []
  for (const [name, allowedList] of Object.entries(COLUMN_GRANTS)) {
    const rel = relations.find((t) => t.schema === 'public' && t.name === name)
    if (!rel) continue
    if (!['r', 'p'].includes(rel.relkind)) throw new Error(`public.${name} is relkind ${rel.relkind}, expected a table; refusing a column grant.`)
    const cols = (await s.rows<{ name: string }>(`
      SELECT attname::text AS name FROM pg_catalog.pg_attribute WHERE attrelid=$1::oid AND attnum > 0 AND NOT attisdropped ORDER BY attnum
    `, [rel.oid])).map((c) => c.name)
    const allowed = new Set<string>(allowedList)
    columnGrants.push({
      relation: rel,
      granted: cols.filter((c) => allowed.has(c)),
      withheld: cols.filter((c) => !allowed.has(c)),
      missingAllowed: allowedList.filter((c) => !cols.includes(c)),
    })
  }

  const deniedByName = new Set((await s.rows<{ oid: string }>(`
    SELECT c.oid::text AS oid FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace
     WHERE n.nspname=ANY($2::text[]) AND c.relname LIKE ANY($1::text[])
  `, [[...DENY_PATTERNS], [...READ_SCHEMAS]])).map((r) => r.oid))
  const viewOids = relations.filter((r) => r.relkind === 'v' || r.relkind === 'm').map((r) => r.oid)
  const viewDeps = new Map((await s.rows<{ oid: string; via: string }>(`
    WITH RECURSIVE dep(root, ref) AS (${VIEW_DEP_CTE_BODY})
    SELECT dep.root::text AS oid,
           string_agg(DISTINCT format('%I.%I', tn.nspname, t.relname), ', ' ORDER BY format('%I.%I', tn.nspname, t.relname)) AS via
      FROM dep JOIN pg_catalog.pg_class t ON t.oid=dep.ref JOIN pg_catalog.pg_namespace tn ON tn.oid=t.relnamespace
     WHERE tn.nspname='auth' OR (tn.nspname=ANY($3::text[]) AND t.relname LIKE ANY($2::text[]))
     GROUP BY dep.root
  `, [viewOids, [...DENY_PATTERNS], [...READ_SCHEMAS]])).map((r) => [r.oid, r.via] as const))
  const reach = await viewReach(s, viewOids, columnGrants)

  const acceptView = new Set(options.acceptView)
  const targets: Relation[] = []
  const denied: Array<Relation & { reason: string }> = []
  const acceptedViews: string[] = []
  for (const r of relations) {
    const v = reach.get(r.oid)
    const verdict = v ? viewVerdict(v, acceptView.has(fq(r))) : null
    if (deniedByName.has(r.oid)) denied.push({ ...r, reason: 'deny-list' })
    else if (viewDeps.has(r.oid)) denied.push({ ...r, reason: `view reads denied/auth relation(s): ${viewDeps.get(r.oid)}` })
    else if (verdict) denied.push({ ...r, reason: verdict.overridable ? `${verdict.reason} (--accept-view=${fq(r)} to keep)` : verdict.reason })
    else {
      if (v?.rls && v.definer) acceptedViews.push(`${fq(r)} reaches RLS table(s) ${v.rls} — ACCEPTED via --accept-view`)
      targets.push(r)
    }
  }
  // A column-granted relation is only granted if it survived the deny/view filters.
  const kept = columnGrants.filter((c) => targets.some((t) => t.oid === c.relation.oid))
  return { targets, denied, unresolvedRegistry, columnGrants: kept, acceptedViews }
}

/** Recursive view-dependency body: (root view/matview, relation it reads), transitively. $1 = roots. */
const VIEW_DEP_CTE_BODY = `
      SELECT r.ev_class, d.refobjid FROM pg_catalog.pg_rewrite r
        JOIN pg_catalog.pg_depend d ON d.classid='pg_catalog.pg_rewrite'::regclass AND d.objid=r.oid
         AND d.refclassid='pg_catalog.pg_class'::regclass AND d.refobjid<>r.ev_class
       WHERE r.ev_class=ANY($1::oid[])
      UNION
      SELECT dep.root, d.refobjid FROM dep JOIN pg_catalog.pg_rewrite r ON r.ev_class=dep.ref
        JOIN pg_catalog.pg_depend d ON d.classid='pg_catalog.pg_rewrite'::regclass AND d.objid=r.oid
         AND d.refclassid='pg_catalog.pg_class'::regclass AND d.refobjid<>r.ev_class`

// ------------------------------------------------------------------------------------------------
// Grants
// ------------------------------------------------------------------------------------------------

/** Returns the stale revokes made (bound into the plan hash). */
async function grantReadSet(s: Session, set: ReadSet, staleSelects: ReaderGrant[]): Promise<string[]> {
  const staleRevokes: string[] = []
  const out = s.out
  out.section('Grants (each made as the object owner)')
  await s.exec(`DO $$ BEGIN EXECUTE format('GRANT CONNECT ON DATABASE %I TO ${qi(READER)}', current_database()); END $$`)
  out.line(`   CONNECT on the current database (as ${ADMIN_ROLE}, via the database owner's grant option)`)
  const schemas = await s.rows<{ name: string; owner: string }>(`
    SELECT nspname AS name, pg_get_userbyid(nspowner) AS owner FROM pg_catalog.pg_namespace WHERE nspname=ANY($1::text[]) ORDER BY 1
  `, [[...READ_SCHEMAS]])
  for (const schema of schemas) {
    await s.asRole(schema.owner, () => s.exec(`GRANT USAGE ON SCHEMA ${qi(schema.name)} TO ${qi(READER)}`))
    out.line(`   USAGE on schema ${schema.name} (as ${schema.owner})`)
  }
  if (!schemas.some((x) => x.name === 'nirmana_evidence')) out.info('schema', 'nirmana_evidence is absent; no USAGE granted there')

  const tableTargets = set.targets.filter((t) => !set.columnGrants.some((c) => c.relation.oid === t.oid))
  const tableOids = new Set(tableTargets.map((t) => t.oid))
  // Stale: any table-level SELECT outside the table-level set, and every pre-existing grant (table or
  // column) on a column-granted relation — REVOKE … ON TABLE also removes the grantor's column grants.
  const staleKeys = new Set<string>()
  for (const g of staleSelects) {
    if (g.kind !== 'relation' && g.kind !== 'column') continue
    if (g.kind === 'relation' && tableOids.has(g.objectOid)) continue
    if (g.kind === 'column' && !set.columnGrants.some((c) => c.relation.oid === g.objectOid) && tableOids.has(g.objectOid)) continue
    const key = `${g.objectOid}|${g.grantor}`
    if (staleKeys.has(key)) continue
    staleKeys.add(key)
    await s.asRole(g.grantor, () => s.exec(`REVOKE SELECT ON TABLE ${g.relation} FROM ${qi(READER)}`))
    staleRevokes.push(`${g.relation} by ${g.grantor}`)
    out.line(`   REVOKED pre-existing SELECT on ${g.relation} (as ${g.grantor}) — not in the table-level read set; re-granted below if planned`)
  }

  for (const cg of set.columnGrants) {
    if (!cg.granted.length) throw new Error(`${fq(cg.relation)}: none of the allowed columns exist; refusing an empty column grant.`)
    await s.asRole(cg.relation.owner, () => s.exec(
      `GRANT SELECT (${cg.granted.map(qi).join(', ')}) ON TABLE ${qi(cg.relation.schema)}.${qi(cg.relation.name)} TO ${qi(READER)}`))
    out.line(`   column SELECT on ${fq(cg.relation)} (${cg.granted.join(', ')}) as owner ${cg.relation.owner}; withheld: ${cg.withheld.join(', ') || 'none'}`)
  }

  const byOwner = new Map<string, Relation[]>()
  for (const r of tableTargets) byOwner.set(r.owner, [...(byOwner.get(r.owner) ?? []), r])
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
  return staleRevokes
}

// ------------------------------------------------------------------------------------------------
// Verification (effective privileges, evaluated for suvarna_reader inside the transaction)
// ------------------------------------------------------------------------------------------------

/** Returns the accepted SECURITY DEFINER signatures actually reachable (bound into the plan hash). */
async function verify(s: Session, reader: string, version: number, set: ReadSet, options: Options): Promise<{ acceptedSecdef: string[] }> {
  const out = s.out
  out.section('Verification — effective privileges of suvarna_reader')

  const [attrs] = await s.rows<{ ok: boolean; connlimit: number }>(`
    SELECT rolcanlogin AND NOT rolinherit AND NOT rolsuper AND NOT rolcreaterole AND NOT rolcreatedb AND NOT rolreplication AND NOT rolbypassrls AS ok,
           rolconnlimit AS connlimit
      FROM pg_catalog.pg_roles WHERE oid=$1::oid
  `, [reader])
  out.check('V0 role attributes', attrs?.ok === true && attrs.connlimit === CONNECTION_LIMIT,
    `LOGIN NOINHERIT, not superuser/createrole/createdb/replication/bypassrls, CONNECTION LIMIT ${attrs?.connlimit}`)
  const settings = (await s.rows<{ entry: string }>(`
    SELECT format('%s:%s', s.setdatabase, c) AS entry FROM pg_catalog.pg_db_role_setting s CROSS JOIN LATERAL unnest(s.setconfig) c
     WHERE s.setrole=$1::oid ORDER BY 1
  `, [reader])).map((r) => r.entry)
  const expected = READER_ROLE_CONFIG.map(([k, v]) => `0:${k}=${v}`).sort()
  const roleDiff = diffLines(expected, settings)
  out.check('V0 role defaults', roleDiff.added.length === 0 && roleDiff.removed.length === 0,
    `exactly ${READER_ROLE_CONFIG.map(([k, v]) => `${k}=${v}`).join(', ')} (all databases)`
      + (roleDiff.added.length ? `; unexpected: ${roleDiff.added.join(', ')}` : '')
      + (roleDiff.removed.length ? `; missing: ${roleDiff.removed.join(', ')}` : ''))

  const [db] = await s.rows<{ connect: boolean; create: boolean; temp: boolean }>(`
    SELECT has_database_privilege($1::oid, current_database(), 'CONNECT') AS connect,
           has_database_privilege($1::oid, current_database(), 'CREATE') AS "create",
           has_database_privilege($1::oid, current_database(), 'TEMPORARY') AS temp
  `, [reader])
  out.check('V1 CONNECT', db?.connect === true, 'CONNECT on the current database')
  out.check('V6 no database CREATE', db?.create === false, 'cannot CREATE schemas in the database')
  out.info('V6b TEMPORARY', db?.temp ? 'effective (normally via PUBLIC): session-local temp tables only, no persistent write; not revocable per-role without touching PUBLIC' : 'not effective')

  const usage = await s.rows<{ name: string; ok: boolean }>(`
    SELECT nspname AS name, has_schema_privilege($1::oid, oid, 'USAGE') AS ok FROM pg_catalog.pg_namespace WHERE nspname=ANY($2::text[]) ORDER BY 1
  `, [reader, [...READ_SCHEMAS]])
  for (const u of usage) out.check(`V2 USAGE ${u.name}`, u.ok, `USAGE on schema ${u.name}`)
  if (!usage.some((u) => u.name === 'public')) out.check('V2 USAGE public', false, 'schema public not found')

  const tableTargets = set.targets.filter((t) => !set.columnGrants.some((c) => c.relation.oid === t.oid))
  const missing = await s.rows<{ name: string }>(`
    SELECT format('%I.%I', n.nspname, c.relname) AS name FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace
     WHERE c.oid=ANY($2::oid[]) AND NOT has_table_privilege($1::oid, c.oid, 'SELECT') ORDER BY 1
  `, [reader, tableTargets.map((t) => t.oid)])
  out.check('V3 SELECT on every table-level target', missing.length === 0, `${tableTargets.length - missing.length}/${tableTargets.length} effective`)
  if (missing.length) out.list('not selectable', missing.map((m) => m.name))
  for (const cg of set.columnGrants) {
    const cols = await s.rows<{ name: string; ok: boolean }>(`
      SELECT attname::text AS name, has_column_privilege($1::oid, attrelid, attnum, 'SELECT') AS ok
        FROM pg_catalog.pg_attribute WHERE attrelid=$2::oid AND attnum > 0 AND NOT attisdropped ORDER BY attnum
    `, [reader, cg.relation.oid])
    const notGranted = cols.filter((c) => cg.granted.includes(c.name) && !c.ok).map((c) => c.name)
    const leaked = cols.filter((c) => !cg.granted.includes(c.name) && c.ok).map((c) => c.name)
    const [tableLevel] = await s.rows<{ ok: boolean }>(`SELECT has_table_privilege($1::oid, $2::oid, 'SELECT') AS ok`, [reader, cg.relation.oid])
    out.check(`V3b ${fq(cg.relation)} column SELECT exact`, notGranted.length === 0 && leaked.length === 0 && tableLevel?.ok === false,
      `granted ${cg.granted.length - notGranted.length}/${cg.granted.length}; withheld columns selectable: ${leaked.join(', ') || 'none'}; table-level SELECT=${tableLevel?.ok}`)
  }

  const edges = await readerEdges(s, reader, version)
  out.check('V4 no memberships', edges.memberOf.length === 0 && edges.membersOfReader.length === 0,
    edges.memberOf.length + edges.membersOfReader.length === 0 ? 'member of nothing; nobody can SET ROLE into it'
      : [...edges.memberOf, ...edges.membersOfReader].join('; '))
  if (edges.tolerated.length) out.info('V4b PG16 creator edge', `${edges.tolerated.join('; ')} (ADMIN only, INHERIT/SET false)`)

  const [owns] = await s.rows<{ count: string }>(`
    SELECT ((SELECT count(*) FROM pg_catalog.pg_shdepend WHERE refclassid='pg_catalog.pg_authid'::regclass AND refobjid=$1::oid AND deptype='o')
          + (SELECT count(*) FROM pg_catalog.pg_database WHERE datdba=$1::oid))::text AS count
  `, [reader])
  out.check('V5 owns nothing', owns?.count === '0', `${owns?.count} owned object(s) across all databases`)

  const schemaCreate = await s.rows<{ name: string }>(`
    SELECT nspname AS name FROM pg_catalog.pg_namespace WHERE nspname !~ '^pg_toast' AND nspname !~ '^pg_temp_'
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
      FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace
     WHERE c.relkind IN ('r','p','v','m','f') AND n.nspname !~ '^pg_toast' AND n.nspname !~ '^pg_temp_'
       AND has_table_privilege($1::oid, c.oid, 'INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER') ORDER BY 1
  `, [reader])
  out.check('V8 no relation write privilege', relWrite.length === 0, `${relWrite.length} relation(s) with INSERT/UPDATE/DELETE/TRUNCATE/REFERENCES/TRIGGER`)
  if (relWrite.length) out.list('writable relations', relWrite.map((r) => `${r.name} [${r.privs}]`))

  const colWrite = await s.rows<{ name: string }>(`
    SELECT format('%I.%I', n.nspname, c.relname) AS name FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace
     WHERE c.relkind IN ('r','p','v','m','f') AND n.nspname !~ '^pg_toast' AND n.nspname !~ '^pg_temp_'
       AND has_any_column_privilege($1::oid, c.oid, 'INSERT,UPDATE,REFERENCES') ORDER BY 1
  `, [reader])
  out.check('V8b no column write privilege', colWrite.length === 0, `${colWrite.length} relation(s) with column INSERT/UPDATE/REFERENCES`)
  if (colWrite.length) out.list('column-writable relations', colWrite.map((r) => r.name))

  const seq = await s.rows<{ name: string }>(`
    SELECT format('%I.%I', n.nspname, c.relname) AS name FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace
     WHERE c.relkind='S' AND n.nspname !~ '^pg_toast' AND n.nspname !~ '^pg_temp_'
       AND has_sequence_privilege($1::oid, c.oid, 'USAGE,UPDATE') ORDER BY 1
  `, [reader])
  out.check('V9 no sequence USAGE/UPDATE', seq.length === 0, `${seq.length} sequence(s)`)
  if (seq.length) out.list('advanceable sequences', seq.map((r) => r.name))

  // No schema-USAGE condition: a function in a schema the reader cannot use is still invocable
  // through an operator, cast or aggregate. EXECUTE alone counts. Trigger and event-trigger functions
  // are excluded (L8): they cannot be called directly, only fired by DML/DDL the reader cannot issue.
  const secdef = await s.rows<{ sig: string; owner: string }>(`
    SELECT p.oid::regprocedure::text AS sig, pg_get_userbyid(p.proowner) AS owner
      FROM pg_catalog.pg_proc p JOIN pg_catalog.pg_namespace n ON n.oid=p.pronamespace
     WHERE p.prosecdef AND n.nspname <> 'pg_catalog'
       AND p.prorettype NOT IN ('pg_catalog.trigger'::regtype, 'pg_catalog.event_trigger'::regtype)
       AND has_function_privilege($1::oid, p.oid, 'EXECUTE') ORDER BY 1
  `, [reader])
  const accepted = new Set(options.acceptSecdef)
  const secdefRejected = secdef.filter((f) => !accepted.has(f.sig))
  out.check('V10 no executable SECURITY DEFINER function', secdefRejected.length === 0,
    `${secdef.length} executable outside pg_catalog (any schema), ${secdef.length - secdefRejected.length} accepted via --accept-secdef`)
  if (secdef.length) out.list('reachable SECURITY DEFINER functions (runs as owner)', secdef.map((f) => `${f.sig} owner=${f.owner}${accepted.has(f.sig) ? ' [ACCEPTED]' : ''}`))
  const unusedAccept = options.acceptSecdef.filter((sig) => !secdef.some((f) => f.sig === sig))
  if (unusedAccept.length) out.info('V10b', `--accept-secdef values matching nothing reachable: ${unusedAccept.join('; ')}`)

  const [auth] = await s.rows<{ exists: boolean; usage: boolean; granted: string }>(`
    WITH auth AS (SELECT oid FROM pg_catalog.pg_namespace WHERE nspname='auth')
    SELECT EXISTS (SELECT 1 FROM auth) AS exists,
           COALESCE((SELECT has_schema_privilege($1::oid, oid, 'USAGE') FROM auth), false) AS usage,
           (SELECT count(*)::text FROM pg_catalog.pg_class c WHERE c.relnamespace IN (SELECT oid FROM auth)
              AND has_any_column_privilege($1::oid, c.oid, 'SELECT')) AS granted
  `, [reader])
  const authViews = await s.rows<{ name: string }>(`
    WITH RECURSIVE dep(root, ref) AS (
      SELECT r.ev_class, d.refobjid FROM pg_catalog.pg_rewrite r
        JOIN pg_catalog.pg_depend d ON d.classid='pg_catalog.pg_rewrite'::regclass AND d.objid=r.oid AND d.refclassid='pg_catalog.pg_class'::regclass AND d.refobjid<>r.ev_class
      UNION
      SELECT dep.root, d.refobjid FROM dep JOIN pg_catalog.pg_rewrite r ON r.ev_class=dep.ref
        JOIN pg_catalog.pg_depend d ON d.classid='pg_catalog.pg_rewrite'::regclass AND d.objid=r.oid AND d.refclassid='pg_catalog.pg_class'::regclass AND d.refobjid<>r.ev_class
    )
    SELECT DISTINCT format('%I.%I', vn.nspname, v.relname) AS name
      FROM dep JOIN pg_catalog.pg_class t ON t.oid=dep.ref JOIN pg_catalog.pg_namespace tn ON tn.oid=t.relnamespace
      JOIN pg_catalog.pg_class v ON v.oid=dep.root JOIN pg_catalog.pg_namespace vn ON vn.oid=v.relnamespace
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
    SELECT format('%I.%I', n.nspname, c.relname) AS name FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace
     WHERE c.relkind IN ('r','p','v','m','f')
       AND (n.nspname='auth' OR (n.nspname=ANY($3::text[]) AND c.relname LIKE ANY($2::text[])))
       AND has_schema_privilege($1::oid, n.oid, 'USAGE') AND has_any_column_privilege($1::oid, c.oid, 'SELECT') ORDER BY 1
  `, [reader, [...DENY_PATTERNS], [...READ_SCHEMAS]])
  out.check('V12 deny-listed relations unreadable', deniedReadable.length === 0, `${deniedReadable.length} readable`)
  if (deniedReadable.length) out.list('readable deny-listed relations (table or column SELECT)', deniedReadable.map((r) => r.name))

  const defacl = await s.rows<{ line: string }>(`
    SELECT format('%s in %s on %s: %s', pg_get_userbyid(d.defaclrole), d.defaclnamespace, d.defaclobjtype, a.privilege_type) AS line
      FROM pg_catalog.pg_default_acl d CROSS JOIN LATERAL aclexplode(d.defaclacl) a WHERE a.grantee=$1::oid
  `, [reader])
  out.check('V13 no default-privilege grants name suvarna_reader', defacl.length === 0, defacl.map((d) => d.line).join('; ') || 'none')

  const outside = await sharedAclDependenciesOutsideScope(s, reader)
  out.check('V15 no ACL dependency outside the intended grants', outside === 0,
    `${outside} pg_catalog.pg_shdepend ACL entr(ies) other than this database's relations/schemas and CONNECT`)

  const extra = await s.rows<{ name: string }>(`
    SELECT format('%I.%I', n.nspname, c.relname) AS name FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace
     WHERE c.relkind IN ('r','p','v','m','f') AND n.nspname NOT IN ('pg_catalog','information_schema') AND n.nspname !~ '^pg_toast'
       AND NOT (c.oid=ANY($2::oid[])) AND has_schema_privilege($1::oid, n.oid, 'USAGE') AND has_table_privilege($1::oid, c.oid, 'SELECT')
     ORDER BY 1
  `, [reader, set.targets.map((t) => t.oid)])
  out.info('V14 readable beyond the read set', extra.length ? `${extra.length} relation(s), normally via PUBLIC grants: ${extra.map((e) => e.name).join(', ')}` : 'none')

  // V16 (M3): no relation the reader can read, in any schema, has a withheld column of a
  // column-granted relation in its view-dependency closure (pg_depend.refobjsubid).
  const readableViews = (await s.rows<{ oid: string }>(`
    SELECT c.oid::text AS oid FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace
     WHERE c.relkind IN ('v','m') AND n.nspname NOT IN ('pg_catalog','information_schema')
       AND has_any_column_privilege($1::oid, c.oid, 'SELECT')
  `, [reader])).map((r) => r.oid)
  const withheldReaders = [...(await viewReach(s, readableViews, set.columnGrants)).values()].filter((v) => v.withheld)
  out.check('V16 no readable relation depends on a withheld column', withheldReaders.length === 0,
    `${withheldReaders.length} readable view(s)/matview(s) over withheld ${set.columnGrants.map((c) => fq(c.relation)).join('/') || '(none)'} columns`)
  if (withheldReaders.length) out.list('readable relations reading withheld columns', withheldReaders.map((v) => `${v.name}: ${v.withheld}`))
  return { acceptedSecdef: secdef.filter((f) => accepted.has(f.sig)).map((f) => f.sig) }
}

// ------------------------------------------------------------------------------------------------
// Report: RLS and PII the native must knowingly accept
// ------------------------------------------------------------------------------------------------

interface PiiEntry { relation: string; columns: string[]; accepted: boolean }

/** M1: after the grants, audit every relation the reader can actually read — the planned targets
 *  PLUS any relation in READ_SCHEMAS readable by other means (PUBLIC grants) — for RLS, PII/json
 *  columns (only columns it can read) and definer views. Returns the PII entries (bound into the hash). */
async function auditReadable(s: Session, reader: string, set: ReadSet, options: Options): Promise<PiiEntry[]> {
  const out = s.out
  const readable = await s.rows<{ oid: string; name: string; relkind: string }>(`
    SELECT c.oid::text AS oid, format('%s.%s', n.nspname, c.relname) AS name, c.relkind::text AS relkind
      FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace
     WHERE n.nspname=ANY($2::text[]) AND c.relkind IN ('r','p','v','m','f')
       AND (c.oid=ANY($3::oid[]) OR (has_schema_privilege($1::oid, n.oid, 'USAGE') AND has_any_column_privilege($1::oid, c.oid, 'SELECT')))
     ORDER BY 2
  `, [reader, [...READ_SCHEMAS], set.targets.map((t) => t.oid)])
  const readableOids = readable.map((r) => r.oid)
  const targetOids = new Set(set.targets.map((t) => t.oid))
  const extras = readable.filter((r) => !targetOids.has(r.oid))
  out.section(`Audit of everything suvarna_reader can read in ${READ_SCHEMAS.join(', ')} (${readable.length} relation(s): ${set.targets.length} planned + ${extras.length} readable otherwise)`)
  out.list('readable beyond the plan (PUBLIC or other grants) — audited below like the plan', extras.map((e) => `${e.name} [${e.relkind}]`))

  // Definer views among ALL readable relations (the plan already excluded its own).
  const reach = await viewReach(s, readable.filter((r) => r.relkind === 'v' || r.relkind === 'm').map((r) => r.oid), set.columnGrants)
  const acceptView = new Set(options.acceptView)
  const badViews = [...reach.values()].map((v) => ({ v, verdict: viewVerdict(v, acceptView.has(v.name)) }))
    .filter((x) => x.verdict !== null)
  out.check('A1 no readable definer view over RLS / column-granted data', badViews.length === 0,
    `${badViews.length} readable view(s)/matview(s) that must not be readable (revoke the grant that exposes them, or --accept-view for RLS-only cases)`)
  out.list('readable views that fail', badViews.map((x) => `${x.v.name} — ${x.verdict?.reason}`))

  out.section('Row-level security on everything readable (no policy is added — the native decides)')
  const rls = await s.rows<{ name: string; applicable: boolean; policies: string | null }>(`
    SELECT format('%I.%I', n.nspname, c.relname) AS name,
           EXISTS (SELECT 1 FROM pg_catalog.pg_policy p WHERE p.polrelid=c.oid AND p.polpermissive AND p.polcmd IN ('r','*')
                     AND (0=ANY(p.polroles) OR $1::oid=ANY(p.polroles))) AS applicable,
           (SELECT string_agg(format('%s[%s,cmd=%s,to=%s]', p.polname, CASE WHEN p.polpermissive THEN 'permissive' ELSE 'restrictive' END, p.polcmd,
                     (SELECT string_agg(CASE WHEN r=0 THEN 'PUBLIC' ELSE pg_get_userbyid(r) END, '|') FROM unnest(p.polroles) r)), '; ' ORDER BY p.polname)
              FROM pg_catalog.pg_policy p WHERE p.polrelid=c.oid) AS policies
      FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace
     WHERE c.oid=ANY($2::oid[]) AND c.relrowsecurity ORDER BY 1
  `, [reader, readableOids])
  out.list('RLS on, NO applicable SELECT policy → suvarna_reader silently sees ZERO rows',
    rls.filter((r) => !r.applicable).map((r) => `${r.name}  policies: ${r.policies ?? 'none'}`))
  out.list('RLS on, a PUBLIC/reader policy applies → rows filtered by the policy expression',
    rls.filter((r) => r.applicable).map((r) => `${r.name}  policies: ${r.policies ?? 'none'}`))
  const policyDeps = await s.rows<{ line: string }>(`
    SELECT format('%I.%I policy %s needs %s', n.nspname, c.relname, p.polname,
             CASE WHEN d.refclassid='pg_catalog.pg_class'::regclass THEN d.refobjid::regclass::text ELSE d.refobjid::regprocedure::text END
             || CASE WHEN d.refclassid='pg_catalog.pg_class'::regclass AND d.refobjsubid > 0
                     THEN format('(%s)', (SELECT attname FROM pg_catalog.pg_attribute WHERE attrelid=d.refobjid AND attnum=d.refobjsubid)) ELSE '' END) AS line
      FROM pg_catalog.pg_policy p JOIN pg_catalog.pg_class c ON c.oid=p.polrelid JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace
      JOIN pg_catalog.pg_depend d ON d.classid='pg_catalog.pg_policy'::regclass AND d.objid=p.oid AND d.refclassid IN ('pg_catalog.pg_class'::regclass, 'pg_catalog.pg_proc'::regclass)
     WHERE c.oid=ANY($2::oid[]) AND c.relrowsecurity AND p.polcmd IN ('r','*') AND (0=ANY(p.polroles) OR $1::oid=ANY(p.polroles))
       AND NOT (d.refclassid='pg_catalog.pg_class'::regclass AND d.refobjid=c.oid)
       AND NOT CASE WHEN d.refclassid='pg_catalog.pg_class'::regclass
             THEN has_schema_privilege($1::oid, (SELECT relnamespace FROM pg_catalog.pg_class WHERE oid=d.refobjid), 'USAGE')
                  AND CASE WHEN d.refobjsubid > 0 THEN has_column_privilege($1::oid, d.refobjid, d.refobjsubid::smallint, 'SELECT')
                           ELSE has_any_column_privilege($1::oid, d.refobjid, 'SELECT') END
             ELSE has_schema_privilege($1::oid, (SELECT pronamespace FROM pg_catalog.pg_proc WHERE oid=d.refobjid), 'USAGE')
                  AND has_function_privilege($1::oid, d.refobjid, 'EXECUTE') END
     ORDER BY 1
  `, [reader, readableOids])
  out.list('applicable policies that reference objects/columns suvarna_reader cannot use (queries will ERROR)', policyDeps.map((p) => p.line))

  out.section('PII in everything readable (only columns suvarna_reader can actually SELECT)')
  const piiRows = await s.rows<{ name: string; col: string }>(`
    SELECT format('%s.%s', n.nspname, c.relname) AS name,
           a.attname || CASE WHEN a.atttypid IN ('pg_catalog.json'::regtype, 'pg_catalog.jsonb'::regtype) THEN '(' || format_type(a.atttypid, NULL) || ')' ELSE '' END AS col
      FROM pg_catalog.pg_attribute a JOIN pg_catalog.pg_class c ON c.oid=a.attrelid JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace
     WHERE c.oid=ANY($1::oid[]) AND a.attnum > 0 AND NOT a.attisdropped
       AND has_column_privilege($3::oid, c.oid, a.attnum, 'SELECT')
       AND (a.attname ~* $2 OR a.atttypid IN ('pg_catalog.json'::regtype, 'pg_catalog.jsonb'::regtype))
     ORDER BY 1, a.attnum
  `, [readableOids, PII_COLUMN_REGEX, reader])
  const acceptPii = new Set(options.acceptPii)
  const byRel = new Map<string, string[]>()
  for (const r of piiRows) byRel.set(r.name, [...(byRel.get(r.name) ?? []), r.col])
  const pii: PiiEntry[] = [...byRel.entries()].map(([relation, columns]) => ({ relation, columns, accepted: acceptPii.has(relation) }))
  const piiFailures = pii.filter((p) => !p.accepted)
  out.check('PII columns', piiFailures.length === 0,
    `${pii.length} readable relation(s) with PII/identifier-looking or json/jsonb columns, ${pii.length - piiFailures.length} accepted via --accept-pii`)
  out.list('readable PII-looking / json columns (FAIL unless --accept-pii=<schema.rel>)',
    pii.map((p) => `${p.relation}: ${p.columns.join(', ')}${p.accepted ? ' [ACCEPTED]' : ''}`))
  const unusedPii = options.acceptPii.filter((rel) => !pii.some((p) => p.relation === rel))
  if (unusedPii.length) out.info('PII accept', `--accept-pii values matching nothing readable: ${unusedPii.join('; ')}`)
  const unusedView = options.acceptView.filter((rel) => !set.acceptedViews.some((v) => v.startsWith(`${rel} `)))
  if (unusedView.length) out.info('view accept', `--accept-view values matching no RLS-reaching definer view: ${unusedView.join('; ')}`)
  return pii
}

// ------------------------------------------------------------------------------------------------
// Invariant reporting
// ------------------------------------------------------------------------------------------------

interface Markers { nirmana: boolean; dataPlane: number; dataPlaneHistory: boolean; purna: boolean }

async function readMarkers(s: Session): Promise<Markers> {
  const [row] = await readAsApp(s, ['_migrations_applied'], () => s.rows<{ nirmana: boolean; data_plane: number; purna: boolean }>(`
    SELECT EXISTS (SELECT 1 FROM public._migrations_applied WHERE filename=$1) AS nirmana,
           (SELECT count(DISTINCT filename)::int FROM public._migrations_applied WHERE filename=ANY($2::text[])) AS data_plane,
           EXISTS (SELECT 1 FROM public._migrations_applied WHERE filename=$3) AS purna
  `, [NIRMANA_MARKER, [...DATA_PLANE_MARKERS], PURNA_MARKER]))
  const [history] = await s.rows<{ present: boolean }>(`
    SELECT EXISTS (SELECT 1 FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace
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
    input, encoding: 'utf8', timeout: 120_000, env: gcloudEnv(),
    stdio: [input === undefined ? 'ignore' : 'pipe', 'pipe', 'pipe'],
  })
  // stderr is never echoed unfiltered: base64-looking runs are redacted before it reaches any output.
  if (result.error) return { status: -1, stdout: '', stderr: redactGcloud(result.error.message) }
  return { status: result.status ?? -1, stdout: result.stdout ?? '', stderr: redactGcloud(result.stderr ?? '') }
}

const short = (text: string): string => text.replace(/\s+/g, ' ').trim().slice(0, 300)

/** Version id from `projects/…/secrets/…/versions/N` or a bare `N`; null if neither. */
export function secretVersionId(name: string): string | null {
  const m = /^(?:.*\/versions\/)?(\d+)$/.exec(name.trim())
  return m ? m[1] : null
}

function disableSecretVersion(id: string): { ok: boolean; detail: string } {
  const r = gcloud(['secrets', 'versions', 'disable', id, `--secret=${SECRET_NAME}`, `--project=${GCP_PROJECT}`, '--quiet'])
  return { ok: r.status === 0, detail: r.status === 0 ? `version ${id} disabled` : `version ${id} NOT disabled: ${short(r.stderr)}` }
}

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

/** L5: disable every ENABLED version created since `sinceIso` (this run). Returns what happened. */
function disableVersionsSince(sinceIso: string): string {
  const list = gcloud(['secrets', 'versions', 'list', SECRET_NAME, `--project=${GCP_PROJECT}`,
    `--filter=state:ENABLED AND createTime>="${sinceIso}"`, '--format=value(name)'])
  if (list.status !== 0) return `could not list versions created since ${sinceIso}: ${short(list.stderr)} — disable them by hand`
  const ids = list.stdout.split(/\s+/).map((n) => secretVersionId(n)).filter((id): id is string => id !== null)
  if (!ids.length) return `no version created since ${sinceIso}`
  return ids.map((id) => disableSecretVersion(id).detail).join('; ')
}

/** Adds the password as a new version (via stdin) and returns the version id. On any failure, every
 *  version created since `runStartIso` is disabled before the error propagates (nothing commits). */
function addSecretVersion(password: string, runStartIso: string): string {
  const added = gcloud(['secrets', 'versions', 'add', SECRET_NAME, '--data-file=-', `--project=${GCP_PROJECT}`, '--format=value(name)'], password)
  const id = added.status === 0 ? secretVersionId(added.stdout) : null
  if (id) return id
  const cleanup = disableVersionsSince(runStartIso)
  throw new Error(added.status !== 0
    ? `Secret Manager version add failed: ${short(added.stderr)}; cleanup: ${cleanup}; nothing committed.`
    : `Secret Manager version add reported success but its version name could not be read; cleanup: ${cleanup}; nothing committed.`)
}

/** After a proven apply: every other ENABLED version of the secret is disabled (best effort, reported). */
function disableOlderSecretVersions(out: Reporter, current: string): void {
  const list = gcloud(['secrets', 'versions', 'list', SECRET_NAME, `--project=${GCP_PROJECT}`, '--filter=state:ENABLED', '--format=value(name)'])
  if (list.status !== 0) { out.info('secret versions', `could not list versions: ${short(list.stderr)}; disable older ones by hand`); return }
  const older = list.stdout.split(/\s+/).map((n) => secretVersionId(n)).filter((id): id is string => id !== null && id !== current)
  if (!older.length) { out.line('   Secret Manager: no older enabled versions'); return }
  for (const id of older) {
    const r = disableSecretVersion(id)
    if (r.ok) out.line(`   Secret Manager: older ${r.detail}`)
    else out.info('secret versions', r.detail)
  }
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

const tilde = (path: string): string => path.replace(homedir(), '~')
const stamp = (): string => new Date().toISOString().replace(/[:.]/g, '-')

/** Create (mode 700) and verify a private directory: a real directory, not a symlink, owned by us. */
function ensurePrivateDir(dir: string): void {
  mkdirSync(dir, { recursive: true, mode: 0o700 })
  const st = lstatSync(dir)
  if (st.isSymbolicLink() || !st.isDirectory()) throw new Error(`${tilde(dir)} must be a real directory, not a symlink.`)
  if (typeof process.getuid === 'function' && st.uid !== process.getuid()) throw new Error(`${tilde(dir)} is not owned by the current user.`)
  chmodSync(dir, 0o700)
}

/** Atomic replace: an O_EXCL mode-600 temp file in the same directory, fsync, rename. The temp file is
 *  unlinked if writing OR the rename fails. */
export function atomicWrite(dir: string, target: string, data: string | Buffer): void {
  const tmp = join(dir, `.pgenv.${process.pid}.${randomBytes(6).toString('hex')}.tmp`)
  const fd = openSync(tmp, 'wx', 0o600)
  try {
    const bytes = typeof data === 'string' ? Buffer.from(data, 'utf8') : data
    let written = 0
    while (written < bytes.length) written += writeSync(fd, bytes, written, bytes.length - written)
    fsyncSync(fd)
  } catch (error) {
    closeSync(fd)
    unlinkSync(tmp)
    throw error
  }
  closeSync(fd)
  try {
    renameSync(tmp, target)
  } catch (error) {
    try { unlinkSync(tmp) } catch { /* already gone */ }
    throw error
  }
  chmodSync(target, 0o600)
}

/** Copy `src` into ~/.config/madhav-admin/<name> (dir 700, file 600); never overwrites an existing file. */
function backupToAdminDir(src: string, name: string): string {
  const dir = ADMIN_BACKUP_DIR()
  ensurePrivateDir(dir)
  const dest = join(dir, name)
  copyFileSync(src, dest, fsConstants.COPYFILE_EXCL)
  chmodSync(dest, 0o600)
  return dest
}

/** The write-capable app-login file is backed up to ~/.config/madhav-admin/, never beside the reader
 *  credential (the Monitor warns on any pgenv*.bak* / pgenv.previous* in the credential directory). */
function writeCredentialFile(out: Reporter, database: string, password: string): void {
  const dir = CREDENTIAL_DIR()
  const cred = join(dir, 'pgenv.sh')
  ensurePrivateDir(dir)
  if (existsSync(cred)) {
    const backup = join(ADMIN_BACKUP_DIR(), APP_LOGIN_BACKUP)
    if (credentialFileIsReader(cred)) {
      const kept = backupToAdminDir(cred, `pgenv.suvarna-reader.${stamp()}.bak`)
      out.line(`   current file was already a ${READER} credential (superseded password); kept as ${tilde(kept)} (mode 600)`)
    } else if (!existsSync(backup)) {
      backupToAdminDir(cred, APP_LOGIN_BACKUP)
      out.line(`   previous credential file kept as ${tilde(backup)} (dir 700, file 600)`)
    } else if (!readFileSync(cred).equals(readFileSync(backup))) {
      const kept = backupToAdminDir(cred, `pgenv.previous.${stamp()}.bak`)
      out.line(`   ${tilde(backup)} already exists and is kept; the current file was also kept as ${tilde(kept)} (mode 600)`)
    } else {
      out.line(`   ${tilde(backup)} already holds the current file; kept`)
    }
  }
  atomicWrite(dir, cred, credentialFileBody(database, password, new Date().toISOString().slice(0, 10)))
  out.line('   ~/.config/suvarna/pgenv.sh replaced atomically (mode 600)')
}

/** After COMMIT: prove the credential by connecting as suvarna_reader and running the same
 *  self-evaluable checks the Monitor runs. */
async function proveReaderLogin(out: Reporter, route: AdminRoute, password: string): Promise<boolean> {
  const pool = new Pool({
    host: route.host, port: route.port, database: route.database, user: READER, password,
    options: '-c default_transaction_read_only=on -c search_path=pg_catalog', max: 1, connectionTimeoutMillis: 15_000,
  })
  try {
    const { rows: [r] } = await pool.query<{ who: string; ro: string; writes: string; creates: boolean }>(`
      SELECT current_user::text AS who, current_setting('default_transaction_read_only') AS ro,
        ((SELECT count(*) FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace
           WHERE n.nspname !~ '^pg_toast' AND n.nspname !~ '^pg_temp_' AND (
             (c.relkind IN ('r','p','v','m','f') AND (has_table_privilege(current_user, c.oid, 'INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER')
                OR has_any_column_privilege(current_user, c.oid, 'INSERT,UPDATE,REFERENCES')))
             OR (c.relkind='S' AND has_sequence_privilege(current_user, c.oid, 'USAGE,UPDATE'))))
         + (SELECT count(*) FROM pg_catalog.pg_namespace WHERE nspname !~ '^pg_toast' AND nspname !~ '^pg_temp_' AND has_schema_privilege(current_user, oid, 'CREATE'))
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

/** Rollback: put the app-login file back from ~/.config/madhav-admin/ — only if the current
 *  pgenv.sh is the reader's (one line checked: PGUSER=suvarna_reader). The replaced reader file is
 *  kept as a timestamped backup in ~/.config/madhav-admin/; the app-login backup is kept too. */
function restoreCredentialFile(out: Reporter): void {
  const dir = CREDENTIAL_DIR()
  const cred = join(dir, 'pgenv.sh')
  const backup = join(ADMIN_BACKUP_DIR(), APP_LOGIN_BACKUP)
  if (!existsSync(backup)) {
    out.info('file', `no ${tilde(backup)}: credential file left untouched — restore it yourself`)
    return
  }
  if (!existsSync(cred) || !credentialFileIsReader(cred)) {
    out.info('file', `~/.config/suvarna/pgenv.sh ${existsSync(cred) ? 'has no PGUSER=suvarna_reader line' : 'is absent'}: not the reader credential, left untouched`)
    return
  }
  ensurePrivateDir(dir)
  const kept = backupToAdminDir(cred, `pgenv.suvarna-reader.${stamp()}.bak`)
  atomicWrite(dir, cred, readFileSync(backup))
  out.line(`   ~/.config/suvarna/pgenv.sh restored from ${tilde(backup)} (atomic, mode 600; backup kept); the replaced reader file kept as ${tilde(kept)}`)
}

// ------------------------------------------------------------------------------------------------
// Main
// ------------------------------------------------------------------------------------------------

async function beginAsAdmin(s: Session, route: AdminRoute): Promise<{ version: number }> {
  await s.exec('BEGIN')
  // First statement of every transaction (bootstrap dry-run/apply and rollback): nothing in a user
  // schema can shadow a catalog relation, function or operator; temp objects are searched last.
  await s.exec('SET LOCAL search_path = pg_catalog, pg_temp')
  await s.exec(`SET LOCAL lock_timeout = '15s'`)
  await s.exec(`SET LOCAL statement_timeout = '10min'`)
  const [actor] = await s.rows<{ session_user: string; current_user: string; can_manage: boolean; version: number; database: string }>(`
    SELECT session_user::text AS session_user, current_user::text AS current_user,
           (r.rolsuper OR r.rolcreaterole) AS can_manage, current_setting('server_version_num')::int AS version,
           current_database()::text AS database
      FROM pg_catalog.pg_roles r WHERE r.rolname=current_user
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
      SELECT ((SELECT count(*) FROM pg_catalog.pg_shdepend WHERE refclassid='pg_catalog.pg_authid'::regclass AND refobjid=$1::oid AND deptype='o')
            + (SELECT count(*) FROM pg_catalog.pg_database WHERE datdba=$1::oid))::text AS count
    `, [reader])
    if (owns?.count !== '0') throw new Error(`${READER} owns ${owns?.count} object(s); refusing an automatic rollback (DROP OWNED would destroy them).`)
    const grants = await readerGrants(s, reader)
    const manual = grants.filter((g) => !['relation', 'column', 'schema', 'database'].includes(g.kind))
    if (manual.length) {
      throw new Error(`${READER} holds grants this bootstrap never makes; clean them by hand first: ${
        manual.slice(0, 20).map((g) => `${g.privilege} on ${g.kind} ${g.object} (by ${g.grantor})`).join('; ')}`)
    }
    const seen = new Set<string>()
    for (const g of grants) {
      // A column grant is removed by REVOKE … ON TABLE as the same grantor, so both share one key.
      const kind = g.kind === 'column' ? 'relation' : g.kind
      const key = `${kind}|${g.objectOid}|${g.grantor}`
      if (seen.has(key)) continue
      seen.add(key)
      const target = kind === 'relation' ? `${g.subkind === 'S' ? 'SEQUENCE' : 'TABLE'} ${g.relation}`
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

/** ALTER ROLE … SET for the reader's resource limits. temp_file_limit is superuser-settable
 *  (PGC_SUSET); if the admin lacks SET on it, the failure is caught at a savepoint and reported as a
 *  check failure (the run then rolls back) rather than aborting the report. */
async function setReaderRoleDefaults(s: Session): Promise<void> {
  await s.exec(`ALTER ROLE ${qi(READER)} RESET ALL`)
  for (const [name, value] of READER_ROLE_CONFIG) {
    await s.exec('SAVEPOINT reader_role_default')
    try {
      await s.exec(`ALTER ROLE ${qi(READER)} SET ${name} = ${s.client.escapeLiteral(value)}`)
      await s.exec('RELEASE SAVEPOINT reader_role_default')
      s.out.line(`   role default: ${name} = ${value}`)
    } catch (error) {
      await s.exec('ROLLBACK TO SAVEPOINT reader_role_default')
      await s.exec('RELEASE SAVEPOINT reader_role_default')
      s.out.check(`R role default ${name}`, false, `ALTER ROLE … SET ${name} = '${value}' refused: ${short(error instanceof Error ? error.message : String(error))}`)
    }
  }
}

/** The CREATE/ALTER ROLE … PASSWORD statements carry the SCRAM verifier; pg_stat_statements (with
 *  track_utility) stores their text. Reset exactly those entries, inside the transaction and before
 *  COMMIT (L1), under a savepoint so a failure can never abort the transaction; best effort. Never
 *  passes the verifier as a parameter (it would reach logs): matches on the role name and PASSWORD.
 *  `reset=false` (dry run) only reports whether a reset would be possible. On Cloud SQL expect
 *  "not reset": the reset function is normally not granted to postgres. */
async function resetVerifierStatements(s: Session, reset: boolean): Promise<void> {
  await s.exec('SAVEPOINT pgss_reset')
  try {
    const [ext] = await s.rows<{ nsp: string | null; callable: boolean }>(`
      SELECT n.nspname::text AS nsp,
             COALESCE(pg_catalog.has_schema_privilege(n.oid, 'USAGE')
                      AND pg_catalog.has_function_privilege(pg_catalog.to_regprocedure(pg_catalog.format('%I.pg_stat_statements_reset(oid,oid,bigint)', n.nspname)), 'EXECUTE'), false) AS callable
        FROM pg_catalog.pg_extension e JOIN pg_catalog.pg_namespace n ON n.oid=e.extnamespace WHERE e.extname='pg_stat_statements'
    `)
    if (!ext?.nsp) s.out.info('pg_stat_statements', 'extension not installed: nothing to reset')
    else if (!ext.callable) {
      s.out.info('pg_stat_statements', `installed in ${ext.nsp} but not callable by ${ADMIN_ROLE} (schema USAGE + EXECUTE on pg_stat_statements_reset(oid,oid,bigint)): entries NOT reset — expected on Cloud SQL; see runbook §2`)
    } else if (!reset) {
      s.out.info('pg_stat_statements', `reset is callable; --apply resets the ${READER} PASSWORD statement entries before COMMIT`)
    } else {
      const nsp = qi(ext.nsp)
      const hits = await s.rows<{ userid: string; dbid: string; queryid: string }>(`
        SELECT userid::text, dbid::text, queryid::text FROM ${nsp}.pg_stat_statements
         WHERE query ~* '^\\s*(CREATE|ALTER)\\s+ROLE' AND pg_catalog.strpos(query, $1) > 0 AND pg_catalog.strpos(pg_catalog.upper(query), 'PASSWORD') > 0
      `, [qi(READER)])
      for (const h of hits) await s.rows(`SELECT ${nsp}.pg_stat_statements_reset($1::oid, $2::oid, $3::bigint)`, [h.userid, h.dbid, h.queryid])
      s.out.line(`   pg_stat_statements: ${hits.length} ${READER} PASSWORD statement entr(ies) reset`)
    }
    await s.exec('RELEASE SAVEPOINT pgss_reset')
  } catch (error) {
    await s.exec('ROLLBACK TO SAVEPOINT pgss_reset')
    await s.exec('RELEASE SAVEPOINT pgss_reset')
    s.out.info('pg_stat_statements', `reset failed (best effort): ${short(error instanceof Error ? error.message : String(error))}`)
  }
}

/** L5: between adding the secret version and knowing the COMMIT outcome, SIGINT/SIGTERM disables the
 *  just-added version (or, if the add itself was interrupted, every version created since run start)
 *  and exits; the uncommitted transaction dies with the connection. Returns the uninstaller. */
function installSecretGuard(state: { versionId: string | null }, runStartIso: string): () => void {
  const handler = (signal: NodeJS.Signals): void => {
    const detail = state.versionId ? disableSecretVersion(state.versionId).detail : disableVersionsSince(runStartIso)
    process.stderr.write(`\n${signal}: interrupted with a Secret Manager version possibly added; ${detail}. `
      + `COMMIT outcome unknown: check pg_roles for ${READER}; re-run --apply (it resets the password).\n`)
    process.exit(130)
  }
  process.once('SIGINT', handler)
  process.once('SIGTERM', handler)
  return () => { process.removeListener('SIGINT', handler); process.removeListener('SIGTERM', handler) }
}

export async function runSuvarnaReaderBootstrap(options: Options, env: NodeJS.ProcessEnv = process.env): Promise<boolean> {
  const out = new Reporter()
  const route = validateAdminRoute(env[ADMIN_URL])
  if (options.dataPlaneGateAmended) assertGateAmendmentPresent()
  // 60 s before now: margin for clock skew against Secret Manager's createTime (L5 cleanup filter).
  const runStartIso = new Date(Date.now() - 60_000).toISOString()
  const password = generatePassword()
  const verifier = scramVerifier(password)
  out.protect(password)
  out.protect(verifier)

  out.line(`Suvarṇa D6 reader bootstrap — mode: ${options.mode.toUpperCase()}${options.dataPlaneGateAmended ? ' (data-plane gate declared amended; amendment clauses found in the checked-out gate)' : ''}`)
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
  let released = false
  const release = async (): Promise<void> => {
    if (released) return
    released = true
    client.release()
    await pool.end().catch(() => undefined)
  }
  const guardState: { versionId: string | null } = { versionId: null }
  let uninstallGuard: (() => void) | null = null
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
    await setReaderRoleDefaults(s)
    out.line('   (role defaults are a belt and resource bound; the grants below are the real boundary; temp_file_limit is the instance flag)')
    const reader = await readerOid(s)
    if (!reader) throw new Error(`${READER} not visible after creation.`)

    const markers = await readMarkers(s)
    const set = await computeReadSet(s, options)

    out.section('Plan — read set (printed in full)')
    const bySource = (src: string): number => set.targets.filter((t) => t.sources.includes(src)).length
    out.line(`   ${set.targets.length} relation(s) to be SELECT-able: census=${bySource('census')} asset_registry=${bySource('asset_registry')} fixed=${bySource('fixed')} gate=${bySource('gate')} nirmana_evidence=${bySource('nirmana_evidence')} (overlapping)`)
    out.list('owners (grants are made as each)', [...new Set(set.targets.map((t) => t.owner))].sort()
      .map((owner) => `${owner}: ${set.targets.filter((t) => t.owner === owner).length}`))
    out.list('relations', set.targets.map((t) => `${fq(t)} [${t.relkind}] owner=${t.owner} from=${t.sources.join('+')}${
      set.columnGrants.some((c) => c.relation.oid === t.oid) ? ' COLUMN-LEVEL' : ''}`))
    for (const cg of set.columnGrants) {
      out.list(`${fq(cg.relation)} columns GRANTED`, cg.granted)
      out.list(`${fq(cg.relation)} columns WITHHELD (birth data / personal identifiers / not allow-listed)`, cg.withheld)
      if (cg.missingAllowed.length) out.info('columns', `${fq(cg.relation)}: allow-listed columns absent in this database: ${cg.missingAllowed.join(', ')}`)
    }
    out.list('EXCLUDED (deny-list; view over denied/auth data; view reading withheld columns or reaching column-granted/RLS data with definer rights)',
      set.denied.map((d) => `${fq(d)} — ${d.reason}`))
    if (set.acceptedViews.length) out.list('views kept by --accept-view', set.acceptedViews)
    if (set.unresolvedRegistry.length) out.list('asset_registry.target_table values with no relation in public (ignored)', set.unresolvedRegistry)

    const staleRevokes = await grantReadSet(s, set, staleSelects)
    await s.removeTemporaryMemberships()
    out.line(`   temporary owner memberships used and removed in this transaction: ${s.temporaryMemberships.join(', ') || 'none'}`)

    const { acceptedSecdef } = await verify(s, reader, actor.version, set, options)
    const invariantsAfter = await invariantState(s)
    reportInvariants(out, markers, invariantsBefore, invariantsAfter, options)
    reportSnapshots(out, snapshotBefore, await takeSnapshot(s, reader))
    const pii = await auditReadable(s, reader, set, options)

    // M5: the hash covers the plan AND what the run measured after granting (PII, accepted secdef,
    // stale revokes), plus this script's own bytes and its fixed parameters.
    out.section('Plan hash')
    const plan: PlanSpec = {
      targets: set.targets.map(fq),
      columnGrants: set.columnGrants.map((c) => ({ relation: fq(c.relation), granted: c.granted, withheld: c.withheld })),
      excluded: set.denied.map((d) => ({ relation: fq(d), reason: d.reason })),
      pii, acceptedSecdef, staleRevokes, scriptSha256: scriptSha256(),
    }
    const sha = planHash(plan)
    out.line(`   script sha256: ${plan.scriptSha256}`)
    out.line(`   PLAN SHA256: ${sha}`)
    if (options.expectPlan) {
      out.check('PLAN matches --expect-plan', options.expectPlan === sha, options.expectPlan === sha ? 'the reviewed plan' : `expected ${options.expectPlan}, computed ${sha}: the plan, the measured state or the script changed since the reviewed dry run`)
    } else if (options.mode === 'apply') {
      out.check('PLAN matches --expect-plan', false, '--apply without --expect-plan')
    } else {
      out.info('PLAN', `to apply exactly this plan: --apply --expect-plan=${sha}`)
    }

    out.section('Outcome')
    if (out.failures.length) {
      out.list('violations', out.failures)
      await s.exec('ROLLBACK')
      out.line(`RESULT: FAIL — ${out.failures.length} violation(s); transaction rolled back, nothing persisted.`)
      return false
    }
    if (options.mode === 'dry-run') {
      await resetVerifierStatements(s, false)
      await s.exec('ROLLBACK')
      out.line(`RESULT: PASS (dry run) — every check passed; transaction rolled back, nothing persisted. PLAN SHA256: ${sha}`)
      return true
    }

    await resetVerifierStatements(s, true)
    uninstallGuard = installSecretGuard(guardState, runStartIso)
    guardState.versionId = addSecretVersion(password, runStartIso)
    out.line(`   Secret Manager: version ${guardState.versionId} of ${SECRET_NAME} added (${GCP_PROJECT}); value fed via stdin, never printed`)
  } catch (error) {
    uninstallGuard?.()
    await client.query('ROLLBACK').catch(() => undefined)
    throw new Error(out.redact(error instanceof Error ? error.message : String(error)))
  } finally {
    // Every path out of the transaction block except "secret version added, COMMIT next" releases here.
    if (guardState.versionId === null) await release()
  }
  const versionId = guardState.versionId
  if (versionId === null) throw new Error('internal: no secret version after a passing apply')

  // COMMIT in its own try (L4: only a COMMIT command tag counts; an aborted transaction answers
  // ROLLBACK). On failure or an unknown outcome the just-added secret version is disabled.
  try {
    const res = await client.query('COMMIT')
    if (res.command !== 'COMMIT') throw new Error(`server answered ${res.command ?? 'nothing'} to COMMIT`)
    out.line('   COMMIT: role, grants, role defaults and password are live')
  } catch (error) {
    const disabled = disableSecretVersion(versionId)
    uninstallGuard?.()
    out.line(`   COMMIT failed: ${short(out.redact(error instanceof Error ? error.message : String(error)))}`)
    out.line(`   Secret Manager: ${disabled.detail}`)
    out.line(`RESULT: COMMIT outcome unknown: check pg_roles for ${READER}; re-run --apply (it resets the password).`)
    await release()
    return false
  }
  uninstallGuard?.()
  await release()

  out.section('Post-commit')
  if (!(await proveReaderLogin(out, route, password))) {
    out.line('RESULT: APPLIED BUT UNPROVEN — the role is committed and the password is in Secret Manager, but logging in as')
    out.line(`suvarna_reader failed; the credential file was NOT changed. Investigate, then re-run --apply (it resets the password).`)
    return false
  }
  writeCredentialFile(out, route.database, password)
  disableOlderSecretVersions(out, versionId)
  out.line('RESULT: APPLIED — suvarna_reader live, secret stored, credential file switched. Next: data-plane-ownership-status.ts, then the Monitor.')
  return true
}

const USAGE = `Usage: SUVARNA_READER_ADMIN_DATABASE_URL=postgres://postgres:…@127.0.0.1:5433/<db> \\
  npx --no-install tsx scripts/suvarna-reader-bootstrap.ts [--dry-run | --apply --expect-plan=<sha256>] [--data-plane-gate-amended]
    [--accept-secdef=<sig>]… [--accept-pii=<schema.rel>]… [--accept-view=<schema.rel>]…
  npx --no-install tsx scripts/suvarna-reader-bootstrap.ts --rollback [--dry-run | --apply]`

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
