/**
 * Paripraśna consent — SUBJECT-SCOPED DELETION SCOPE.
 *
 * §4: "Withdrawal triggers the §3.5.D verified-deletion workflow (L2+ corpus
 * destruction — compatible with §N.3 delete-then-insert; receipt snapshots
 * resolved by subject-scoped snapshot deletion with a tombstone hash so audit
 * integrity survives content deletion)."
 *
 * ── WHY DISCOVERY, NOT A HARDCODED LIST ──────────────────────────────────────
 * A hardcoded table list is a signal with a decaying detector (CLAUDE.md §N.8):
 * it is correct on the day it is written and silently wrong the first time a
 * new `bodha_*` / `kala_*` table lands. Worse, the failure mode is the one that
 * matters — a subject who withdrew keeps data nobody noticed. So the scope is
 * DERIVED from the live schema: every BASE TABLE in `public` that has a
 * `chart_id` column, filtered by an L2+ prefix allowlist plus a small explicit
 * extras list, minus an explicit denylist.
 *
 * Migration 470's header warns that the conversational tables
 * (`brahma_mimamsa_prediction_ledger`, `brahma_prospective_ledger`,
 * `message_parts`, `conversation_summaries`) are deliberately NOT registered in
 * `asset_registry` — so the existing cockpit-clear sweep, which is registry
 * driven, would silently miss them. Discovery does not: the two `brahma_*`
 * ledgers carry `chart_id` and match the prefix allowlist, and the two
 * conversation-child tables are reached by ON DELETE CASCADE from
 * `conversations` (verified in the baseline squash:
 * `conversation_messages_conversation_id_fkey ... ON DELETE CASCADE`).
 *
 * ── WHAT IS DELIBERATELY *NOT* IN SCOPE ──────────────────────────────────────
 * L1 Gaṇita and build bookkeeping. §8/A9 is explicit: "build itself may proceed
 * (L1 facts are computation) but INTERPRETIVE serving refuses." A withdrawal
 * destroys the L2+ interpretive corpus about the subject; it does not pretend
 * to un-compute an ephemeris. This boundary is precisely what §3.5.D.2's
 * deletion-scope DISPUTE mechanism exists to contest — see `dispute.ts`.
 */

import type { ConsentQueryable } from './types'

/** L2+ interpretive layers, by table-name prefix. */
export const SUBJECT_SCOPE_PREFIXES: readonly string[] = [
  'bodha_',
  'kala_',
  'phala_',
  'mimamsa_',
  'gochara_',
  'l25_',
  'pariprashna_',
  'brahma_mimamsa_',
  'brahma_prospective_',
]

/** Chart-scoped interpretive tables whose names carry no layer prefix. */
export const SUBJECT_SCOPE_EXTRA_TABLES: readonly string[] = [
  'conversations', // children cascade: conversation_messages, message_parts, summaries, …
  'mcp_predictions',
  'convergence_scores',
  'school_analysis_runs',
  'school_disagreements',
  'school_signal_coverage',
  'prashna_followup_schedule',
  'layer_approvals',
  'pyramid_layers',
]

/**
 * Never swept. Three groups, each for a different stated reason:
 *   · the consent machinery itself — deleting the receipt with the data would
 *     defeat the entire point of a tombstone;
 *   · L1 / root identity — computation and the chart record itself;
 *   · build bookkeeping — operational (C4), not subject content.
 */
export const SUBJECT_SCOPE_DENY_TABLES: readonly string[] = [
  // consent machinery
  'chart_subject_consent',
  'chart_subject_consent_events',
  'chart_subject_exclusions',
  'chart_subject_deletion_tombstones',
  'chart_subject_deletion_disputes',
  // root identity + L1
  'charts',
  'chart_grants',
  'chart_facts',
  'chart_fact_identity',
  'chart_facts_history',
  'chart_facts_supersedence',
  'chart_dashas',
  'chart_divisionals',
  'chart_panchanga',
  'chart_panchanga_cache',
  'chart_vichara',
  'prashna_charts',
  // build bookkeeping / operational
  'builds',
  'build_runs',
  'build_events',
  'build_substep_progress',
  'build_protected_assets',
  'asset_throughput',
  'orchestrator_event_register',
  'runtime_config',
  'layer_approvals_audit',
]

const DENY = new Set(SUBJECT_SCOPE_DENY_TABLES)
const EXTRAS = new Set(SUBJECT_SCOPE_EXTRA_TABLES)

/** Pure predicate — unit-testable without a database. */
export function isSubjectScopedTable(tableName: string): boolean {
  if (DENY.has(tableName)) return false
  if (EXTRAS.has(tableName)) return true
  // `ganita_*` and `ga_*` are L1 and are excluded by simply not being allowlisted.
  return SUBJECT_SCOPE_PREFIXES.some((p) => tableName.startsWith(p))
}

/**
 * The live, sorted set of tables a withdrawal sweep will clear for one subject.
 *
 * Derived from `information_schema`, so a table that does not exist in this
 * deployment is simply absent — the sweep never claims to have cleared a table
 * that was not there (the tombstone's `table_present` column records that
 * distinction explicitly for anything that was named but missing).
 */
export async function discoverSubjectScopedTables(db: ConsentQueryable): Promise<string[]> {
  const { rows } = await db.query<{ table_name: string }>(
    `SELECT c.table_name
       FROM information_schema.columns c
       JOIN information_schema.tables t
         ON t.table_schema = c.table_schema AND t.table_name = c.table_name
      WHERE c.table_schema = 'public'
        AND c.column_name  = 'chart_id'
        AND t.table_type   = 'BASE TABLE'
      ORDER BY c.table_name`,
  )
  return rows.map((r) => r.table_name).filter(isSubjectScopedTable)
}
