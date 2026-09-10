/**
 * no_auto_promotion_manifest.ts — the machine-readable definition of "a
 * prediction promotion" and "the confined set of files allowed to trigger
 * one", shared by the no-auto-promotion CI gate (Paripraśna P1 G1-H,
 * PB-9-DETECTOR). Mirrors the house style of `serving_path_manifest.ts`
 * (PB-3 lane L-6 COLLECT-ONLY gate) but inverted: that gate asserts an
 * ALLOWLIST of files carries ZERO forbidden lines; this gate asserts every
 * occurrence of a FORBIDDEN pattern (a promotion write) is confined to an
 * explicit ALLOWLIST of files, and additionally that each allowlisted
 * entry-point file actually re-checks authentication before it promotes.
 *
 * ── The claim this proves ──────────────────────────────────────────────────
 * PARIPRASHNA_IMPLEMENTATION_ROADMAP_v1_0.md row G1-H: "The no-auto-promotion
 * CI detector — proves no code path promotes a prediction to `confirmed`/
 * `open` without human action (currently true by inspection only)."
 *
 * The claim is about ONE table: `brahma_mimamsa_prediction_ledger`
 * (migration 470, schema.ts LIFECYCLE_STATES) — the SAMĪKṢĀ prediction
 * ledger, the only prediction store in the estate whose lifecycle literally
 * includes both `confirmed` AND `open` as distinct states (verified by
 * inspection against the two sibling stores: `brahma_prospective_ledger`
 * uses `matched` — never a literal `confirmed` write, see
 * `src/lib/lel/prospective_ledger.ts` line ~749 — and `mimamsa_predictions`
 * has no live INSERT/UPDATE-to-confirmed code path at all in this repo; the
 * MCP `record_outcome` tool that could have written it is RETIRED
 * (`platform-mcp/src/tools/mimamsa_outcome.ts` — throws unconditionally,
 * CR-115/CR-128). Scoped to the live claim, not padded to look broader.
 *
 * ── The two-layer confinement ──────────────────────────────────────────────
 * Layer 1 — DAL/orchestration files (`PROMOTION_DAL_FILES`): the only files
 *   permitted to contain a line that WRITES lifecycle_status='confirmed' or
 *   ='open' (via the parameterized DAL — `writer.ts` — or the two typed
 *   orchestration modules that call it, `confirm.ts` / `reviewConfirm.ts`).
 *   A raw, literal SQL write of these values (bypassing the DAL's bound
 *   parameters) is zero-tolerance FORBIDDEN EVERYWHERE, including inside
 *   these files — the real DAL never does this (verified: `writer.ts`'s SQL
 *   text uses `lifecycle_status = $2`, never an inlined literal).
 * Layer 2 — human-gated entry points (`HUMAN_GATED_ENTRY_POINTS`): the only
 *   files permitted to CALL the Layer-1 orchestration functions
 *   (`confirmCandidate`, `confirmDetectedCandidate`) that trigger a
 *   promotion. Each entry point is additionally asserted to contain a real
 *   auth-gate call BEFORE the promotion call (`AUTH_GATE_MARKERS`) — a
 *   detector that only checked "is this file on the allowlist" would be a
 *   flag with no code path that could fail it (§N.8); requiring the auth
 *   marker's presence gives the gate something that actually breaks if a
 *   future edit removes the auth check but keeps the file name.
 *
 * ── False-positive traps this file deliberately avoids ─────────────────────
 * (1) A READ of lifecycle_status (a `WHERE lifecycle_status = 'open'` filter,
 *     e.g. `daily_job.ts`'s window-close sweep, `prospective_ledger.ts`'s
 *     open-prediction lookup) is not a promotion. FORBIDDEN_DAL_PATTERNS
 *     therefore anchor on `SET` / `INSERT ... VALUES`, never a bare
 *     equality, and the call-site patterns target the specific promoting
 *     functions/params, never the state token alone.
 * (2) A pure-comment line documenting the flow (`// detected → confirmed`)
 *     is not a code path. The scanner skips pure-comment lines exactly as
 *     `serving_path_manifest.ts` does.
 * (3) `transitionLifecycle(id, 'window_closed', ...)` and
 *     `transitionLifecycle(id, 'dismissed', ...)` are legal, unconfined
 *     transitions (the daily cron and any dismiss action may call them) —
 *     the call-site pattern below matches ONLY the two literals that matter
 *     ('confirmed' | 'open'), never every call to transitionLifecycle.
 */

/** The one table this gate is scoped to (see header for why not the siblings). */
export const PROMOTION_TABLE = 'brahma_mimamsa_prediction_ledger' as const

/**
 * Files permitted to contain a promotion WRITE (DAL + the two typed
 * orchestration modules that call it). Repo-relative from the `platform/`
 * package root, explicit allowlist (not a glob) so a new writer added later
 * cannot silently join the confined set — the gate test asserts every listed
 * path resolves to a real file.
 */
export const PROMOTION_DAL_FILES: readonly string[] = [
  // The sole DAL: enforces the legal-transition matrix before any write and
  // is the only place `lifecycle_status = 'confirmed'` / `= 'open'` may be
  // the literal `to` argument of a `transitionLifecycle` call.
  'src/lib/pariprashna/samiksha/writer.ts',
  // L-2: the in-stream "Log to Samīkṣā" flow — creates a row BORN confirmed.
  'src/lib/pariprashna/samiksha/confirm.ts',
  // L-3: the review-tab flow — detected → confirmed → open in one orchestration.
  'src/lib/pariprashna/samiksha/reviewConfirm.ts',
]

/**
 * Files permitted to CALL a Layer-1 promotion trigger
 * (`confirmCandidate` / `confirmDetectedCandidate`). Each must ALSO contain
 * one of AUTH_GATE_MARKERS before the call — asserted separately below, not
 * folded into this list's mere membership, so the two checks fail
 * independently and legibly.
 */
export const HUMAN_GATED_ENTRY_POINTS: readonly string[] = [
  // POST /api/pariprashna/samiksha/confirm — requires getServerUser() +
  // authorizeChartAccess() before calling confirmCandidate/dismissCandidate.
  'src/app/api/pariprashna/samiksha/confirm/route.ts',
  // Server action invoked from the review tab's confirm button — requires
  // assertCanWrite() (resolveChartPageAccess) before calling
  // confirmDetectedCandidate.
  'src/app/clients/[id]/samiksha/actions.ts',
]

/** One auth-gate call signature; a matching entry point must contain at least one. */
export const AUTH_GATE_MARKERS: readonly RegExp[] = [
  /\bgetServerUser\s*\(/,
  /\bassertCanWrite\s*\(/,
  /\bresolveChartPageAccess\s*\(/,
  /\bauthorizeChartAccess\s*\(/,
]

/** One promotion-detection construct: a write or a triggering call. */
export interface PromotionPattern {
  readonly id: string
  readonly pattern: RegExp
  readonly reason: string
  /** 'dal-write' → must be confined to PROMOTION_DAL_FILES.
   *  'entry-call' → must be confined to HUMAN_GATED_ENTRY_POINTS.
   *  'raw-bypass' → forbidden EVERYWHERE, no allowlist (zero-tolerance). */
  readonly confinement: 'dal-write' | 'entry-call' | 'raw-bypass'
  /**
   * When set, a line ALSO matching this regex is NOT counted as a hit — used
   * to exclude a function/export DECLARATION line (`export async function
   * confirmCandidate(`) from patterns that are meant to catch a CALL site,
   * not the definition itself. Declarations live in the allowlisted DAL
   * files by construction; without this exclusion the scanner would flag its
   * own definition as an "unconfined call".
   */
  readonly excludeDeclaration?: RegExp
}

/**
 * The forbidden/confined constructs. Every pattern targets a MUTATION or a
 * MUTATION-TRIGGERING call for `confirmed`/`open` specifically — never a
 * bare read of the token, never every legal transition.
 */
export const PROMOTION_PATTERNS: readonly PromotionPattern[] = [
  {
    id: 'raw-sql-set-confirmed-or-open',
    pattern: new RegExp(
      `\\bSET\\s+lifecycle_status\\s*=\\s*['"](confirmed|open)['"]`,
      'i',
    ),
    reason:
      'Raw SQL literal-assigns lifecycle_status to confirmed/open, bypassing the parameterized DAL ' +
      '(writer.ts) and its legal-transition guard entirely. The real DAL never inlines this literal — ' +
      'zero-tolerance, no allowlist exception.',
    confinement: 'raw-bypass',
  },
  {
    id: 'raw-sql-insert-literal-confirmed-or-open',
    pattern: new RegExp(
      `\\bINSERT\\s+INTO\\s+${PROMOTION_TABLE}\\b[\\s\\S]{0,400}?\\bVALUES\\b[\\s\\S]{0,400}?['"](confirmed|open)['"]`,
      'i',
    ),
    reason:
      `A raw INSERT into ${PROMOTION_TABLE} carries a literal 'confirmed'/'open' value, bypassing the ` +
      'DAL createLedgerRow() path (whose INSERT binds `status` as a parameter, never a literal). ' +
      'Zero-tolerance, no allowlist exception.',
    confinement: 'raw-bypass',
  },
  {
    id: 'initial-status-confirmed',
    pattern: /\binitial_status\s*:\s*['"]confirmed['"]/,
    reason:
      "A row is created BORN 'confirmed' (createLedgerRow's initial_status). Confined to the L-2 " +
      'in-stream confirm orchestration (confirm.ts).',
    confinement: 'dal-write',
  },
  {
    id: 'transition-to-confirmed',
    pattern: /\btransitionLifecycle\s*\([^)]*['"]confirmed['"]/,
    reason:
      "A transitionLifecycle call literally targets 'confirmed'. Confined to the DAL's own " +
      'confirmDetectedRow() convenience wrapper (writer.ts).',
    confinement: 'dal-write',
  },
  {
    id: 'transition-to-open',
    pattern: /\btransitionLifecycle\s*\([^)]*['"]open['"]/,
    reason:
      "A transitionLifecycle call literally targets 'open'. Confined to the L-3 review-tab " +
      'orchestration (reviewConfirm.ts, confirmed → open).',
    confinement: 'dal-write',
  },
  {
    id: 'confirm-detected-row-call',
    pattern: /\bconfirmDetectedRow\s*\(/,
    reason:
      "A call to the DAL's detected→confirmed convenience wrapper. Confined to reviewConfirm.ts " +
      '(its sole production caller — writer.ts only DEFINES it).',
    confinement: 'dal-write',
    excludeDeclaration: /\bfunction\s+confirmDetectedRow\b/,
  },
  {
    id: 'confirm-candidate-entry-call',
    pattern: /\bconfirmCandidate\s*\(/,
    reason:
      'A call to the L-2 confirm orchestration that creates a row BORN confirmed. Confined to the ' +
      'authenticated POST /api/pariprashna/samiksha/confirm route.',
    confinement: 'entry-call',
    excludeDeclaration: /\bfunction\s+confirmCandidate\b/,
  },
  {
    id: 'confirm-detected-candidate-entry-call',
    pattern: /\bconfirmDetectedCandidate\s*\(/,
    reason:
      'A call to the L-3 review-tab confirm orchestration (detected → confirmed → open). Confined ' +
      'to the authenticated confirmCandidateAction server action.',
    confinement: 'entry-call',
    excludeDeclaration: /\bfunction\s+confirmDetectedCandidate\b/,
  },
]

/** One detected occurrence, for reporting. */
export interface ScanHit {
  readonly patternId: string
  readonly reason: string
  readonly confinement: PromotionPattern['confinement']
  readonly line: number
  readonly excerpt: string
}

/** True if a line is a pure-comment line (first non-whitespace run is //, *, or block-comment open). */
function isPureCommentLine(line: string): boolean {
  return /^\s*(\/\/|\*\/?|\/\*)/.test(line)
}

/**
 * Line-oriented scan for the single-line patterns (all except the multiline
 * INSERT check, which needs whole-file context and is scanned separately by
 * `scanForMultilinePromotion`). Skips pure-comment lines (false-positive trap 2).
 */
export function scanForPromotion(source: string): ScanHit[] {
  const hits: ScanHit[] = []
  const lines = source.split('\n')
  const linePatterns = PROMOTION_PATTERNS.filter((p) => p.id !== 'raw-sql-insert-literal-confirmed-or-open')
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i]
    if (isPureCommentLine(line)) continue
    for (const pp of linePatterns) {
      if (pp.excludeDeclaration?.test(line)) continue
      if (pp.pattern.test(line)) {
        hits.push({
          patternId: pp.id,
          reason: pp.reason,
          confinement: pp.confinement,
          line: i + 1,
          excerpt: line.trim().slice(0, 160),
        })
      }
    }
  }
  return hits
}

/**
 * Whole-file scan for the multiline INSERT pattern (a literal INSERT can
 * legitimately span several lines of column/VALUES text). Reports the 1-based
 * line the match STARTS on.
 */
export function scanForMultilinePromotion(source: string): ScanHit[] {
  const pp = PROMOTION_PATTERNS.find((p) => p.id === 'raw-sql-insert-literal-confirmed-or-open')
  if (!pp) return []
  const hits: ScanHit[] = []
  const re = new RegExp(pp.pattern.source, pp.pattern.flags.includes('g') ? pp.pattern.flags : pp.pattern.flags + 'g')
  let m: RegExpExecArray | null
  while ((m = re.exec(source)) !== null) {
    const line = source.slice(0, m.index).split('\n').length
    hits.push({
      patternId: pp.id,
      reason: pp.reason,
      confinement: pp.confinement,
      line,
      excerpt: m[0].replace(/\s+/g, ' ').slice(0, 160),
    })
    if (m[0].length === 0) re.lastIndex++ // guard against zero-width infinite loop
  }
  return hits
}

/** Every hit in a file (single-line + multiline patterns combined). */
export function scanFileForPromotion(source: string): ScanHit[] {
  return [...scanForPromotion(source), ...scanForMultilinePromotion(source)]
}

/**
 * Self-consistency fixtures used by the gate test to keep the DETECTOR
 * demonstrated-can-fail (§N.8): a synthetic forbidden pattern IS flagged, a
 * synthetic honest read/comment/legal-but-different-target transition is
 * NOT flagged. If any expectation breaks, the gate test goes red.
 */
export function scannerSelfProof(): {
  readOnlyWhereFixture: string
  commentFixture: string
  legalOtherTransitionFixture: string
  rawSqlSetFixture: string
  rawSqlInsertFixture: string
  initialStatusConfirmedFixture: string
  transitionToOpenFixture: string
  confirmDetectedRowCallFixture: string
  confirmCandidateEntryCallFixture: string
  confirmDetectedCandidateEntryCallFixture: string
} {
  return {
    readOnlyWhereFixture: `WHERE lifecycle_status = 'open' AND "window" IS NOT NULL`,
    commentFixture: '  // await confirmDetectedRow(rowId, stamp, exec) — documented only, not a real call',
    legalOtherTransitionFixture: `await transitionLifecycle(id, 'window_closed', {}, exec)`,
    rawSqlSetFixture: `SET lifecycle_status = 'confirmed', updated_at = now()`,
    rawSqlInsertFixture: `INSERT INTO brahma_mimamsa_prediction_ledger (chart_id, lifecycle_status)\n       VALUES ($1, 'confirmed')`,
    initialStatusConfirmedFixture: `      initial_status: 'confirmed',`,
    transitionToOpenFixture: `  return transitionLifecycle(rowId, 'open', {}, exec)`,
    confirmDetectedRowCallFixture: `  await confirmDetectedRow(rowId, stamp, exec)`,
    confirmCandidateEntryCallFixture: `      const row = await confirmCandidate({`,
    confirmDetectedCandidateEntryCallFixture: `  await confirmDetectedCandidate({ rowId: input.rowId, probability: input.probability, stamp })`,
  }
}
