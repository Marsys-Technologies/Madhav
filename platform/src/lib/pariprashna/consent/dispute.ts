/**
 * Paripraśna consent — DELETION-SCOPE DISPUTE → DISAGREEMENT_REGISTER HOOK.
 *
 * §4 / §3.5.D.2, carried verbatim: "Deletion-scope disputes open a
 * DISAGREEMENT_REGISTER entry."
 *
 * ── WHAT THE "HOOK" ACTUALLY IS (investigated, not assumed) ──────────────────
 * `00_ARCHITECTURE/DISAGREEMENT_REGISTER_v1_0.md` is NOT a table and NOT an
 * escalation function. It is a LIVING, append-only markdown artifact: §2 defines
 * a YAML `disagreement_register_entry` block, §4 is the entry table, and entries
 * are appended by whichever governance SESSION opens or resolves the
 * disagreement. Its own `consumers:` frontmatter names the two machine
 * producers that exist — `mirror_enforcer.py`, which EMITS an entry rather than
 * silently overwriting, and `divergence_detector.ts`, which does NOT write the
 * register at all and instead attaches its classification to audit events.
 *
 * So there are two honest options and one dishonest one. The dishonest one is a
 * runtime web process committing to a governance markdown file — it cannot (no
 * checkout, no review, no session id) and it must not (the register's integrity
 * is that a session owns each append). This module takes the
 * `mirror_enforcer.py` shape instead: it PRODUCES the fully-formed §2-schema
 * entry, persists it in `chart_subject_deletion_disputes.dr_entry_yaml`, and
 * leaves `dr_id` NULL until a governance session lands it in the register and
 * writes the assigned `DIS.NNN` back. A NULL `dr_id` is a visible "not yet
 * registered", not an assumed one.
 *
 * ── ONE OPEN GOVERNANCE DEPENDENCY, STATED ───────────────────────────────────
 * The register's §1 class list does not yet contain `deletion_scope_dispute`,
 * and its own rule is explicit: "Additional classes may be added in a
 * minor-version bump (v1.X). Adding or removing a class at runtime without a
 * version bump fails schema validation." Adding the class is a GOVERNANCE act
 * (a v1.1 bump of the register artifact), not a code act, and this lane does not
 * perform it. Entries produced here therefore carry the class name the schema
 * will need, and the first governance session to land one must bump the
 * register first. That dependency is written down here rather than discovered
 * at append time.
 */

import { appendConsentEvent } from './withdrawal'
import { isConsentEnforcementEnabled } from './flag'
import {
  ConsentFeatureDisabledError,
  type ConsentDb,
  type ConsentQueryable,
  type DeletionDisputeRow,
} from './types'

export const DELETION_SCOPE_DISPUTE_CLASS = 'deletion_scope_dispute'

export interface DeletionScopeDisputeInput {
  chartId: string
  /** The session opening the dispute — matches the register's `opened_by_session`. */
  openedBySession: string
  /** e.g. ['subject', 'native-arbitrator'] — the register's `parties` field. */
  parties: string[]
  /** 2–5 sentences, per the §2 schema's own instruction for `description`. */
  description: string
  /** Tables the disputing party asserts SHOULD be destroyed. */
  requestedScope: string[]
  /** Tables the sweep as designed WOULD destroy. */
  appliedScope: string[]
}

/**
 * Render the exact YAML block a governance session appends to
 * `DISAGREEMENT_REGISTER_v1_0.md §4`. Field-for-field the §2 schema; fields that
 * do not apply to a deletion-scope dispute are present with their honest null,
 * not omitted (an omitted field reads as an oversight; an explicit null reads as
 * an answer).
 */
export function renderDisagreementRegisterEntry(
  input: DeletionScopeDisputeInput & { openedOn: string; drId?: string | null },
): string {
  const y = (s: string) => JSON.stringify(s) // safe double-quoted YAML scalar
  const list = (items: string[]) =>
    items.length === 0 ? '[]' : `[${items.map(y).join(', ')}]`
  const onlyRequested = input.requestedScope.filter((t) => !input.appliedScope.includes(t))
  const onlyApplied = input.appliedScope.filter((t) => !input.requestedScope.includes(t))

  return [
    'disagreement_register_entry:',
    `  dr_id: ${input.drId ?? 'DIS.PENDING'}`,
    `  class: ${DELETION_SCOPE_DISPUTE_CLASS}`,
    `  opened_on: ${input.openedOn.slice(0, 10)}`,
    `  opened_by_session: ${y(input.openedBySession)}`,
    '',
    `  parties: ${list(input.parties)}`,
    '  description: >',
    ...input.description
      .trim()
      .split('\n')
      .map((line) => `    ${line.trim()}`),
    '',
    '  authoritative_side: none',
    '  evidence_side_a:',
    `    source: ${y(`chart_subject_deletion_disputes:${input.chartId}`)}`,
    `    excerpt: ${y(`requested deletion scope (${input.requestedScope.length} tables); only in requested: ${onlyRequested.join(', ') || 'none'}`)}`,
    '    sha256: null',
    '  evidence_side_b:',
    '    source: "platform/src/lib/pariprashna/consent/scope.ts"',
    `    excerpt: ${y(`applied deletion scope (${input.appliedScope.length} tables); only in applied: ${onlyApplied.join(', ') || 'none'}`)}`,
    '    sha256: null',
    '',
    '  arbitration_steps_taken: []',
    '',
    '  status: open',
    '  resolution: null',
    '  resolved_on: null',
    '  resolved_by_session: null',
    '',
    '  state_hashes:',
    '    side_a_before: null',
    '    side_a_after: null',
    '    side_b_before: null',
    '    side_b_after: null',
    '',
    '  linked_artifacts:',
    '    - path: "platform/supabase/migrations/575_pariprashna_chart_subject_consent.sql"',
    '      linkage: cause',
    '    - path: "00_ARCHITECTURE/PARIPRASHNA_ARCHITECTURE_v1_0.md"',
    '      linkage: evidence',
    '',
  ].join('\n')
}

/**
 * Open a deletion-scope dispute. While one is open the withdrawal sweep is
 * BLOCKED (see `withdrawal.ts`) — the dispute is not advisory.
 */
export async function openDeletionScopeDispute(
  db: ConsentDb,
  input: DeletionScopeDisputeInput,
): Promise<DeletionDisputeRow> {
  if (!isConsentEnforcementEnabled()) throw new ConsentFeatureDisabledError('openDeletionScopeDispute')

  const openedOn = new Date().toISOString()
  const yaml = renderDisagreementRegisterEntry({ ...input, openedOn })

  return db.withTransaction(async (tx) => {
    const { rows } = await tx.query<DeletionDisputeRow>(
      `INSERT INTO chart_subject_deletion_disputes
         (chart_id, dr_class, opened_by_session, parties, description,
          requested_scope, applied_scope, dr_entry_yaml)
       VALUES ($1, $2, $3, $4::jsonb, $5, $6::jsonb, $7::jsonb, $8)
       RETURNING *`,
      [
        input.chartId,
        DELETION_SCOPE_DISPUTE_CLASS,
        input.openedBySession,
        JSON.stringify(input.parties),
        input.description,
        JSON.stringify(input.requestedScope),
        JSON.stringify(input.appliedScope),
        yaml,
      ],
    )
    // The consent chain records that the dispute happened, so a later audit of
    // the chain alone shows why a withdrawal did not complete.
    await appendConsentEvent(tx, {
      chartId: input.chartId,
      eventKind: 'deletion_disputed',
      actorPrincipalId: null,
      payload: {
        dispute_id: rows[0].dispute_id ?? null,
        opened_by_session: input.openedBySession,
        requested_scope_size: input.requestedScope.length,
        applied_scope_size: input.appliedScope.length,
      },
    })
    return rows[0]
  })
}

export async function listOpenDeletionScopeDisputes(
  db: ConsentQueryable,
  chartId: string,
): Promise<DeletionDisputeRow[]> {
  const { rows } = await db.query<DeletionDisputeRow>(
    `SELECT * FROM chart_subject_deletion_disputes
      WHERE chart_id = $1 AND status IN ('open', 'reopened', 'escalated')
      ORDER BY opened_at`,
    [chartId],
  )
  return rows
}

export interface ResolveDisputeInput {
  disputeId: number
  chartId: string
  /** The `DIS.NNN` the governance session assigned when it landed the entry. */
  drId: string | null
  resolution: string
}

/**
 * Close a dispute after native arbitration (§3 step 4 of the register's
 * protocol). Unblocks the sweep; the caller re-runs `withdrawConsentAndDelete`.
 */
export async function resolveDeletionScopeDispute(
  db: ConsentDb,
  input: ResolveDisputeInput,
): Promise<DeletionDisputeRow> {
  if (!isConsentEnforcementEnabled()) throw new ConsentFeatureDisabledError('resolveDeletionScopeDispute')

  return db.withTransaction(async (tx) => {
    const { rows } = await tx.query<DeletionDisputeRow>(
      `UPDATE chart_subject_deletion_disputes
          SET status = 'resolved', resolution = $3, resolved_at = now(), dr_id = $4
        WHERE dispute_id = $1 AND chart_id = $2
        RETURNING *`,
      [input.disputeId, input.chartId, input.resolution, input.drId],
    )
    if (!rows[0]) throw new Error(`DISPUTE_NOT_FOUND: ${input.disputeId} on chart ${input.chartId}`)
    await appendConsentEvent(tx, {
      chartId: input.chartId,
      eventKind: 'deletion_dispute_resolved',
      actorPrincipalId: null,
      payload: { dispute_id: input.disputeId, dr_id: input.drId },
    })
    return rows[0]
  })
}
