/**
 * completeness_receipt.ts — D-2 Lane V-0, BIND_D-2.md §F1.7 ledger row 3.
 *
 * Validates the shape BRIEF_D2.md §F1 Lane V-2 commits to shipping: "completeness receipt on
 * every synthesis (served/empty/dark per floor item, each dark citing its CR row)". V-2 has not
 * shipped as of this lane's build (two-cycle staging — V-2 is cycle 2; V-0 is cycle 1). Per
 * BRIEF_D2.md's own instruction for this exact situation ("write the validator now against a
 * documented expected shape; it will be exercised live once V-2 deploys in cycle 2"), this
 * module is written against the DOCUMENTED contract below, with:
 *   - a structural validator usable the moment V-2's resource/tool exists (validateReceipt);
 *   - a live-probe entrypoint (validateLiveReceipt) that calls a deployed tool/resource and
 *     validates its output — currently a controlled NO-OP until V-2 names the actual tool/field
 *     (see the TODO below), never a fabricated pass;
 *   - a register-status cross-check (crStatusIsDarkEligible) so a `dark` item's cited CR row
 *     must resolve to an OPEN or LOGGED status in the register — a `dark` item citing a CLOSED
 *     CR row is a genuine defect (BIND_D-2.md §F1.7 ledger row 3's own acceptance text).
 *
 * DOCUMENTED EXPECTED SHAPE (from BRIEF_D2.md §F1 Lane V-2 + the design's floor-item concept):
 *   {
 *     served: [{ floor_item_id: string, source: string, ... }],
 *     empty:  [{ floor_item_id: string, empty_reason: string }],
 *     dark:   [{ floor_item_id: string, cr_row: string }],   // cr_row matches /^CR-\d+$/
 *   }
 * Every floor item the compiled vidhi plan named for this reading must appear in EXACTLY ONE of
 * the three arrays (never omitted, never double-counted) — `served ∪ empty ∪ dark` = the full
 * floor-item set, and the three sets are pairwise disjoint.
 */
import { readFileSync } from 'node:fs'
import { join } from 'node:path'
import { fileURLToPath } from 'node:url'
import type { McpClient } from './mcp_client'

export type ServedItem = { floor_item_id: string; source?: string; [k: string]: unknown }
export type EmptyItem = { floor_item_id: string; empty_reason: string; [k: string]: unknown }
export type DarkItem = { floor_item_id: string; cr_row: string; [k: string]: unknown }

export type CompletenessReceipt = {
  served: ServedItem[]
  empty: EmptyItem[]
  dark: DarkItem[]
}

export type ValidationIssue = { severity: 'error' | 'warning'; message: string }

export type ValidationResult = {
  valid: boolean
  floor_item_total: number
  served: number
  empty: number
  dark: number
  issues: ValidationIssue[]
}

const CR_ROW_PATTERN = /^CR-\d+$/

function repoRoot(): string {
  const here = fileURLToPath(import.meta.url) // .../platform/scripts/audit/doctrine_harness/lib/completeness_receipt.ts
  // lib -> doctrine_harness -> audit -> scripts -> platform -> repo root
  return join(here, '..', '..', '..', '..', '..', '..')
}

/**
 * Best-effort register status lookup for a `CR-N` row, parsing
 * POST_REMEDIATION_CONSUMPTION_REGISTER_v1_0.md's table rows (`| CR-N | ... | Status |` shape).
 * Returns null when the row can't be found (the caller treats that as a WARNING, not a hard
 * failure — the register's own §N notes several CR-N rows were renumbered/merged into
 * MARSYS_DEFECT_GAP_REGISTER_v2_0.md, which this lightweight parser does not also scan).
 */
let registerStatusCache: Map<string, string> | null = null
export function crRegisterStatus(crRow: string): string | null {
  if (!registerStatusCache) {
    registerStatusCache = new Map()
    try {
      const path = join(
        repoRoot(),
        '00_ARCHITECTURE/llm_consumption_audit/POST_REMEDIATION_CONSUMPTION_REGISTER_v1_0.md'
      )
      const text = readFileSync(path, 'utf8')
      // Table rows: | CR-54 | ... | ... | ... | ... | ... | OPEN — ELEVATED |
      // The status is the LAST `|`-delimited cell on a row that starts with `| CR-N |`.
      const rowPattern = /^\|\s*(CR-\d+)\s*\|.*\|\s*([^|]+?)\s*\|\s*$/gm
      let m: RegExpExecArray | null
      while ((m = rowPattern.exec(text)) !== null) {
        registerStatusCache.set(m[1], m[2].trim())
      }
    } catch {
      // Register unreadable (moved/renamed) — cache stays empty; every lookup returns null,
      // every dark-item CR citation becomes a WARNING (never fabricated as valid).
    }
  }
  return registerStatusCache.get(crRow) ?? null
}

/** A dark item's CR citation is "eligible" if its register status is OPEN-flavored or LOGGED —
 *  never a CLOSED/CLOSED_WITH_EVIDENCE row (citing a closed defect as the reason data is dark is
 *  itself a defect — BIND_D-2.md §F1.7 ledger row 3). Unresolvable citations (status unknown,
 *  e.g. renumbered into MARSYS_DEFECT_GAP_REGISTER_v2_0.md) are NOT auto-failed — flagged as a
 *  warning instead, since this lightweight parser only scans one of the two registers. */
export function crStatusIsDarkEligible(status: string | null): 'eligible' | 'ineligible' | 'unknown' {
  if (status === null) return 'unknown'
  const s = status.toUpperCase()
  if (s.startsWith('CLOSED')) return 'ineligible'
  if (s.startsWith('OPEN') || s.startsWith('LOGGED')) return 'eligible'
  return 'unknown'
}

export function validateReceipt(receipt: unknown): ValidationResult {
  const issues: ValidationIssue[] = []
  const r = receipt as Partial<CompletenessReceipt> | null | undefined

  if (!r || typeof r !== 'object') {
    return { valid: false, floor_item_total: 0, served: 0, empty: 0, dark: 0, issues: [{ severity: 'error', message: 'receipt is not an object' }] }
  }
  const served = Array.isArray(r.served) ? r.served : null
  const empty = Array.isArray(r.empty) ? r.empty : null
  const dark = Array.isArray(r.dark) ? r.dark : null

  if (served === null) issues.push({ severity: 'error', message: 'receipt.served is missing or not an array' })
  if (empty === null) issues.push({ severity: 'error', message: 'receipt.empty is missing or not an array' })
  if (dark === null) issues.push({ severity: 'error', message: 'receipt.dark is missing or not an array' })

  const servedIds = (served ?? []).map((s) => s.floor_item_id)
  const emptyIds = (empty ?? []).map((s) => s.floor_item_id)
  const darkIds = (dark ?? []).map((s) => s.floor_item_id)

  for (const s of served ?? []) {
    if (!s.floor_item_id) issues.push({ severity: 'error', message: `served item missing floor_item_id: ${JSON.stringify(s)}` })
  }
  for (const e of empty ?? []) {
    if (!e.floor_item_id) issues.push({ severity: 'error', message: `empty item missing floor_item_id: ${JSON.stringify(e)}` })
    if (!e.empty_reason || e.empty_reason.length === 0) {
      issues.push({ severity: 'error', message: `empty item ${e.floor_item_id ?? '(no id)'} has no empty_reason — an unexplained empty is a B.10 violation` })
    }
  }
  for (const d of dark ?? []) {
    if (!d.floor_item_id) issues.push({ severity: 'error', message: `dark item missing floor_item_id: ${JSON.stringify(d)}` })
    if (!d.cr_row || !CR_ROW_PATTERN.test(d.cr_row)) {
      issues.push({ severity: 'error', message: `dark item ${d.floor_item_id ?? '(no id)'} cr_row "${d.cr_row}" does not match /^CR-\\d+$/` })
      continue
    }
    const status = crRegisterStatus(d.cr_row)
    const eligibility = crStatusIsDarkEligible(status)
    if (eligibility === 'ineligible') {
      issues.push({
        severity: 'error',
        message: `dark item ${d.floor_item_id} cites ${d.cr_row} which is ${status} (CLOSED) — a dark item cannot cite a closed defect as its reason`,
      })
    } else if (eligibility === 'unknown') {
      issues.push({
        severity: 'warning',
        message: `dark item ${d.floor_item_id} cites ${d.cr_row} — status not resolvable in POST_REMEDIATION_CONSUMPTION_REGISTER_v1_0.md (may be renumbered into MARSYS_DEFECT_GAP_REGISTER_v2_0.md — not auto-failed)`,
      })
    }
  }

  // Disjointness + totality: every id appears in exactly one bucket.
  const allIds = [...servedIds, ...emptyIds, ...darkIds]
  const seen = new Set<string>()
  for (const id of allIds) {
    if (seen.has(id)) issues.push({ severity: 'error', message: `floor_item_id "${id}" appears in more than one of served/empty/dark — must be disjoint` })
    seen.add(id)
  }
  if (allIds.length === 0) {
    issues.push({ severity: 'error', message: 'receipt has zero floor items across served/empty/dark — a completeness receipt with nothing to account for is not a receipt' })
  }

  const hasErrors = issues.some((i) => i.severity === 'error')
  return {
    valid: !hasErrors,
    floor_item_total: seen.size,
    served: servedIds.length,
    empty: emptyIds.length,
    dark: darkIds.length,
    issues,
  }
}

/**
 * Live probe: fetches a synthesis's completeness receipt from the deployed connector and
 * validates it. V-2 has not yet shipped its resource/tool/field name (BIND_D-2.md: cycle-2
 * lane), so the TOOL_NAME/FIELD_PATH below are TODO placeholders — this function returns a
 * SKIPPED result (not a fabricated pass) until V-2 lands. Once V-2 ships, only the two constants
 * below need updating (the validator logic itself does not change).
 *
 * TODO(V-2): confirm the actual tool name serving `judgment_query`-style syntheses' completeness
 * receipt (BRIEF_D2.md §F1 Lane V-2: "completeness receipt on every synthesis") and the JSON
 * path to the `{served, empty, dark}` object within its response envelope, then flip
 * RECEIPT_TOOL_NAME/RECEIPT_FIELD_PATH below out of the SKIPPED branch.
 */
const RECEIPT_TOOL_NAME: string | null = null // TODO(V-2): e.g. 'judgment_query' with a `completeness_receipt` v3-envelope field
const RECEIPT_FIELD_PATH: string | null = null // TODO(V-2): e.g. 'completeness_receipt'

export async function validateLiveReceipt(
  client: McpClient,
  chartId: string,
  domain: string
): Promise<{ status: 'validated' | 'skipped_v2_not_shipped'; result?: ValidationResult; detail: string }> {
  if (RECEIPT_TOOL_NAME === null || RECEIPT_FIELD_PATH === null) {
    return {
      status: 'skipped_v2_not_shipped',
      detail:
        'V-2 (MCP delivery + receipts, cycle-2 lane) has not shipped the completeness-receipt tool/field yet — ' +
        'validator is structurally ready (validateReceipt) but has no live surface to call. Not a fabricated pass.',
    }
  }
  const { content } = await client.callTool(RECEIPT_TOOL_NAME, { chart_id: chartId, domain })
  const receipt = (content as Record<string, unknown>)[RECEIPT_FIELD_PATH]
  const result = validateReceipt(receipt)
  return { status: 'validated', result, detail: `validated live receipt from ${RECEIPT_TOOL_NAME}.${RECEIPT_FIELD_PATH}` }
}
