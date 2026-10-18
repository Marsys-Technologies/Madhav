/**
 * GET /api/conversations/[id]/active-ayanamshas
 *
 * Returns which ayanamshas are active for a given conversation.
 *
 * Behaviour:
 *   1. Auth: 401 if unauthenticated.
 *   2. Conversation ownership: 404 if not found or belongs to a different user
 *      (super_admin may access any conversation).
 *   3. Column probe: checks whether conversations.active_ayanamshas exists via
 *      information_schema.  If the column was not yet added by migration J-01,
 *      degrades gracefully by returning all 5 canonical ayanamshas.
 *   4. If the column exists but is NULL for this row, also returns the 5-default
 *      fallback with source='default'.
 *   5. Cross-reference: if the conversation has an associated chart_id, also
 *      returns the latest build's ayanamshas for that chart.
 *   6. Cache-Control: max-age=60.
 *
 * Response shape:
 *   {
 *     conversation_id: string
 *     active_ayanamshas: string[]
 *     source: 'explicit' | 'default'
 *     chart_id: string | null
 *     chart_build_ayanamshas: string[] | null
 *     primary: 'lahiri_chitrapaksha'           // Lahiri-primary (N-339), always, whatever the list
 *     cross_check_ayanamshas: string[]         // the active ids other than Lahiri, as stored ids
 *   }
 *
 * Lahiri is the PRIMARY reading for every chart; the active list only selects
 * which of the other four are shown as the labelled cross-check. `primary` and
 * `cross_check_ayanamshas` are additive fields: the original keys are unchanged.
 * The default list is the five STORED ids (it used to carry `yukteshwar`, which
 * is not a stored ayanamsha).
 *
 * [BUILD-ORCH-D-07] /api/conversations/[id]/active-ayanamshas
 */

import { NextResponse } from 'next/server'
import { getServerUser } from '@/lib/firebase/server'
import { query } from '@/lib/db/client'
import { res } from '@/lib/errors'
import {
  AYANAMSHA_SERVE_ORDER,
  PRIMARY_AYANAMSHA,
  resolveAyanamshaArg,
} from '@/lib/retrieval/chart_facts_helpers'

export const dynamic = 'force-dynamic'

// ─── Canonical ayanamsha defaults ─────────────────────────────────────────────

// The five STORED ids in serve order (Lahiri first). Not a local alias map: the list
// is the PR-1 constant, and ids in an explicit list are normalised by the PR-1 helper.
const CANONICAL_AYANAMSHAS: readonly string[] = AYANAMSHA_SERVE_ORDER

type AyanamshaSource = 'explicit' | 'default'

// ─── Response shape ───────────────────────────────────────────────────────────

interface ActiveAyanamshasResponse {
  conversation_id: string
  active_ayanamshas: string[]
  source: AyanamshaSource
  chart_id: string | null
  chart_build_ayanamshas: string[] | null
  primary: string
  cross_check_ayanamshas: string[]
}

/** Stored ids of the active list other than the primary (unknown / "all" entries are skipped). */
function crossCheckSet(active: readonly string[]): string[] {
  const wanted = new Set<string>()
  for (const raw of active) {
    const r = resolveAyanamshaArg(raw)
    if (r.ok && r.ayanamsha_id && r.ayanamsha_id !== PRIMARY_AYANAMSHA) wanted.add(r.ayanamsha_id)
  }
  return AYANAMSHA_SERVE_ORDER.filter((id) => wanted.has(id))
}

// ─── DB row types ─────────────────────────────────────────────────────────────

interface ConversationRow {
  id: string
  user_id: string
  chart_id: string | null
  active_ayanamshas?: string[] | null
}

interface BuildRow {
  ayanamshas: string[] | null
}

interface ColumnExistsRow {
  exists: boolean
}

// ─── Helper: probe information_schema for a column ────────────────────────────

async function columnExists(table: string, column: string): Promise<boolean> {
  const result = await query<ColumnExistsRow>(
    `SELECT EXISTS (
       SELECT 1
       FROM   information_schema.columns
       WHERE  table_schema = 'public'
         AND  table_name   = $1
         AND  column_name  = $2
     ) AS exists`,
    [table, column],
  )
  return result.rows[0]?.exists ?? false
}

// ─── Helper: resolve super-admin status ───────────────────────────────────────

async function isSuperAdmin(userId: string): Promise<boolean> {
  const result = await query<{ role: string }>(
    'SELECT role FROM profiles WHERE id=$1',
    [userId],
  )
  return result.rows[0]?.role === 'super_admin'
}

// ─── Handler ──────────────────────────────────────────────────────────────────

export async function GET(
  _request: Request,
  ctx: { params: Promise<{ id: string }> },
): Promise<Response> {
  // ── Auth ─────────────────────────────────────────────────────────────────────
  const user = await getServerUser()
  if (!user) return res.unauthenticated()

  const { id: conversationId } = await ctx.params

  try {
    // ── Resolve super-admin ─────────────────────────────────────────────────────
    const admin = await isSuperAdmin(user.uid)

    // ── Check whether active_ayanamshas column exists ───────────────────────────
    const hasColumn = await columnExists('conversations', 'active_ayanamshas')

    // ── Fetch conversation (ownership check included) ───────────────────────────
    // Build SELECT list dynamically depending on column presence so we don't
    // trip a query error if the column is absent.
    const selectCols = hasColumn
      ? 'id, user_id, chart_id, active_ayanamshas'
      : 'id, user_id, chart_id'

    const ownershipClause = admin
      ? 'WHERE id=$1'
      : 'WHERE id=$1 AND user_id=$2'
    const ownershipParams: unknown[] = admin
      ? [conversationId]
      : [conversationId, user.uid]

    const convResult = await query<ConversationRow>(
      `SELECT ${selectCols} FROM conversations ${ownershipClause}`,
      ownershipParams,
    )

    const conv = convResult.rows[0]
    if (!conv) return res.notFound('conversation')

    // ── Determine active ayanamshas ─────────────────────────────────────────────
    let activeAyanamshas: string[]
    let source: AyanamshaSource

    const explicitValue = hasColumn ? conv.active_ayanamshas : null

    if (explicitValue && explicitValue.length > 0) {
      activeAyanamshas = explicitValue
      source = 'explicit'
    } else {
      activeAyanamshas = [...CANONICAL_AYANAMSHAS]
      source = 'default'
    }

    // ── Fetch chart build ayanamshas (cross-reference) ──────────────────────────
    let chartBuildAyanamshas: string[] | null = null

    // Ayanamsha-per-build tracking removed with decommissioning of `builds` table.
    if (conv.chart_id) {
      chartBuildAyanamshas = null
    }

    // ── Response ────────────────────────────────────────────────────────────────
    const body: ActiveAyanamshasResponse = {
      conversation_id: conversationId,
      active_ayanamshas: activeAyanamshas,
      source,
      chart_id: conv.chart_id ?? null,
      chart_build_ayanamshas: chartBuildAyanamshas,
      primary: PRIMARY_AYANAMSHA,
      cross_check_ayanamshas: crossCheckSet(activeAyanamshas),
    }

    return NextResponse.json(body, {
      headers: {
        'Cache-Control': 'max-age=60',
      },
    })
  } catch {
    return res.dbError()
  }
}
