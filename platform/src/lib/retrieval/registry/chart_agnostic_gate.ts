/**
 * Chart-Agnostic CI Gate (D1 contract, principle #14)
 * =====================================================
 * Static check that FAILS the build if any registered capability
 * violates the chart-agnostic mandate.
 *
 * FREEZE DECLARATION (D1 contract, 2026-06-28):
 * This gate is FROZEN. The forbidden-pattern set may only be EXPANDED
 * (additional checks added) via a versioned amendment — patterns may
 * never be weakened or removed.
 *
 * Usage (CI):
 *   import { runChartAgnosticGate } from '@/lib/retrieval/registry/chart_agnostic_gate'
 *   runChartAgnosticGate() // throws on any violation
 *
 * Wire into CI alongside parity_check via npm script:
 *   "registry:chart-agnostic-gate": "tsx src/lib/retrieval/registry/chart_agnostic_gate.ts"
 */

import type { CapabilityDescriptor, CapabilityUri } from './types'

// ── Forbidden patterns ────────────────────────────────────────────────────────

/**
 * The canonical native chart_id.
 * Any occurrence of this string in a capability descriptor (URI, description,
 * title, or handler source) is a CRITICAL chart-agnostic violation.
 */
export const NATIVE_CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

/**
 * The phantom chart_id (dead, but should never appear in new code either).
 */
export const PHANTOM_CHART_ID = '362f9f17'

/** Native-default fallback patterns (regex) found in source/descriptions */
export const NATIVE_DEFAULT_PATTERNS = [
  /\?\?\s*['"`]482012f1/,
  /\.default\s*\(\s*['"`]?482012f1/,
  /\?\?\s*NATIVE_CHART_ID/,
  /\?\?\s*NATIVE[^_]/,
  /env(?:ironment)?\s*\.\s*NATIVE_CHART_ID\s*\?\?/,
  /NATIVE_CHART_ID\s*\?\?/,
  /process\.env\[['"]NATIVE_CHART_ID['"]\]/,
] as const

/** Native identifiers that must NOT appear in LLM-visible descriptions */
export const NATIVE_IDENTIFIERS_IN_DESCRIPTION = [
  NATIVE_CHART_ID,
  'Abhisek Mohanty',
  '1984-02-05',
  'Bhubaneswar',
] as const

/**
 * Native-cardinality leak pattern (GT-32/GT-43, 2026-07-19 audit): a thousands-separated
 * literal figure (e.g. "27,554", "601,443") embedded in served text. This is the DB's exact
 * row count for the canonical/native chart baked into a description or empty_reason string
 * served to every caller regardless of chart context — a chart-agnostic-mandate violation
 * distinct from (but the same class as) a literal chart_id or PII leak. Matches any 4+ digit
 * figure with at least one thousands-separator comma; does not match bare 1-3 digit numbers,
 * years, or dimension counts (e.g. "768-dim") which carry no comma.
 */
export const NATIVE_CARDINALITY_PATTERN = /\b\d{1,3}(?:,\d{3}){1,2}\b/

/** Phrase pattern for "native chart" / "the native" leaking into served text (GT-54). */
export const NATIVE_CHART_PHRASE_PATTERN = /\bnative chart\b/i

// ── Violation type ────────────────────────────────────────────────────────────

export interface GateViolation {
  uri: CapabilityUri
  rule: string
  detail: string
}

// ── Rule implementations ──────────────────────────────────────────────────────

/**
 * Rule 1: per_chart capability missing chart_id in required_inputs.
 */
function checkPerChartRequiresChartId(cap: CapabilityDescriptor): GateViolation | null {
  if (cap.scope !== 'per_chart') return null
  const required = cap.required_inputs ?? []
  if (!required.includes('chart_id')) {
    return {
      uri: cap.uri,
      rule: 'RULE-1-PER_CHART_MISSING_CHART_ID',
      detail: `scope=per_chart but required_inputs does not include 'chart_id'. ` +
        `required_inputs=${JSON.stringify(required)}`,
    }
  }
  return null
}

/**
 * Rule 2: literal native or phantom chart_id in description or name.
 */
function checkNoNativeIdInDescription(cap: CapabilityDescriptor): GateViolation | null {
  const text = `${cap.description} ${cap.name} ${cap.uri}`
  if (text.includes(NATIVE_CHART_ID)) {
    return {
      uri: cap.uri,
      rule: 'RULE-2-NATIVE_ID_IN_DESCRIPTION',
      detail: `Literal native chart_id '${NATIVE_CHART_ID}' found in description/name/uri. ` +
        `Replace with '<chart_uuid>' placeholder.`,
    }
  }
  if (text.includes(PHANTOM_CHART_ID)) {
    return {
      uri: cap.uri,
      rule: 'RULE-2-PHANTOM_ID_IN_DESCRIPTION',
      detail: `Phantom chart_id prefix '${PHANTOM_CHART_ID}' found in description/name/uri.`,
    }
  }
  return null
}

/**
 * Rule 3: native identifier (name, birthdate, birthplace) in LLM-visible description.
 * These bias the model to fill in the native when the user did not specify a chart.
 *
 * Applies uniformly to every primitive_type — tool AND resource. There is NO exemption
 * for native-scoped resources (e.g. ephemeris_cache_native_lifetime): a resource being
 * "about" the native's lifetime window does not require restating the native's PII
 * (name/DOB/birth-time/birthplace) in a description served to every caller regardless
 * of chart context. GT-42 (2026-07-19 audit): a prior deliberate exception carved out
 * for `marsys://resource/ephemeris-cache/native-lifetime` was itself the reason this
 * gate missed a full-PII leak in that resource's description — removed, not weakened
 * (the freeze declaration governs the forbidden-pattern set, not narrow per-URI
 * carve-outs that undermine it).
 */
function checkNoNativeIdentifierInDescription(cap: CapabilityDescriptor): GateViolation | null {
  const desc = cap.description
  for (const id of NATIVE_IDENTIFIERS_IN_DESCRIPTION) {
    if (id === NATIVE_CHART_ID) continue // already checked in rule 2
    if (desc.includes(id)) {
      return {
        uri: cap.uri,
        rule: 'RULE-3-NATIVE_IDENTIFIER_IN_DESCRIPTION',
        detail: `Native identifier '${id}' found in description. ` +
          `Descriptions are LLM-visible — native identifiers bias the model. ` +
          `Remove or replace with a generic placeholder.`,
      }
    }
  }
  return null
}

/**
 * Rule 4: per_chart capability's input_schema chart_id field has a default value.
 * A default value on chart_id is a native-default vector even if not an explicit UUID.
 */
function checkNoDefaultOnChartId(cap: CapabilityDescriptor): GateViolation | null {
  if (cap.scope !== 'per_chart') return null
  const chartIdSchema = cap.input_schema?.['chart_id']
  if (chartIdSchema && 'default' in chartIdSchema && chartIdSchema.default !== undefined) {
    return {
      uri: cap.uri,
      rule: 'RULE-4-CHART_ID_HAS_DEFAULT',
      detail: `per_chart capability has a 'default' on the chart_id input_schema field. ` +
        `chart_id must be required with no default (error-if-missing). ` +
        `Found: default=${JSON.stringify(chartIdSchema.default)}`,
    }
  }
  return null
}

/**
 * Rule 5: input_schema chart_id description contains a literal UUID.
 * Specifically catches the old pattern: description: 'UUID of the chart (canonical native: 482012f1-...)'
 */
function checkNoNativeIdInChartIdDescription(cap: CapabilityDescriptor): GateViolation | null {
  const chartIdDesc = cap.input_schema?.['chart_id']?.description ?? ''
  if (chartIdDesc.includes(NATIVE_CHART_ID)) {
    return {
      uri: cap.uri,
      rule: 'RULE-5-NATIVE_ID_IN_CHART_ID_FIELD_DESCRIPTION',
      detail: `Literal native chart_id found in input_schema.chart_id.description. ` +
        `Replace with '<chart_uuid>' or a generic description. ` +
        `Found in: ${cap.uri} → input_schema.chart_id.description`,
    }
  }
  if (chartIdDesc.includes(PHANTOM_CHART_ID)) {
    return {
      uri: cap.uri,
      rule: 'RULE-5-PHANTOM_ID_IN_CHART_ID_FIELD_DESCRIPTION',
      detail: `Phantom chart_id prefix found in input_schema.chart_id.description.`,
    }
  }
  return null
}

/**
 * Rule 6: 'global' scope capability lists chart_id in required_inputs.
 * Global capabilities must not require a chart_id — they are chart-agnostic.
 * (This catches accidental misclassification.)
 */
function checkGlobalNotRequiringChartId(cap: CapabilityDescriptor): GateViolation | null {
  if (cap.scope !== 'global') return null
  const required = cap.required_inputs ?? []
  if (required.includes('chart_id')) {
    return {
      uri: cap.uri,
      rule: 'RULE-6-GLOBAL_SCOPE_HAS_CHART_ID_REQUIRED',
      detail: `scope=global capability has 'chart_id' in required_inputs. ` +
        `If this capability is per-chart, set scope='per_chart'. ` +
        `If it is truly global, remove chart_id from required_inputs.`,
    }
  }
  return null
}

/**
 * Rule 7: Missing required D1 contract fields (scope, archetype, traversal_level, tool_role,
 * emits_references, lel_capable). Detects capabilities that were not retrofitted.
 */
function checkD1ContractFieldsPresent(cap: CapabilityDescriptor): GateViolation | null {
  const missing: string[] = []

  // scope is enforced by the discriminated union but check at runtime too
  if (cap.scope === undefined || cap.scope === null) missing.push('scope')
  if (cap.archetype === undefined || cap.archetype === null) missing.push('archetype')
  if (cap.traversal_level === undefined || cap.traversal_level === null) missing.push('traversal_level')
  if (cap.tool_role === undefined || cap.tool_role === null) missing.push('tool_role')
  if (cap.emits_references === undefined || cap.emits_references === null) missing.push('emits_references')
  if (cap.lel_capable === undefined || cap.lel_capable === null) missing.push('lel_capable')

  if (missing.length > 0) {
    return {
      uri: cap.uri,
      rule: 'RULE-7-MISSING_D1_CONTRACT_FIELDS',
      detail: `Missing required D1 contract fields: ${missing.join(', ')}. ` +
        `All capabilities must be retrofitted to the D1 contract (scope, archetype, ` +
        `traversal_level, tool_role, emits_references, lel_capable).`,
    }
  }
  return null
}

/**
 * Rule 9: literal thousands-separated cardinality figure (native/chart row count) embedded
 * in LLM-visible description text (GT-32/GT-43, 2026-07-19 audit — e.g. "27,554 rows per
 * chart", "601,443 rows for the native"). Descriptions are served to every caller regardless
 * of chart context; a specific figure is (a) a chart-agnostic-mandate violation of the same
 * class as a literal chart_id, and (b) liable to go stale/wrong relative to the live table
 * (GT-43: 601,443 vs. the canonical L1 seal's 536,471). Say "bounded" / "paginated" / omit
 * the figure entirely instead.
 */
function checkNoNativeCardinalityInDescription(cap: CapabilityDescriptor): GateViolation | null {
  const desc = cap.description ?? ''
  const match = desc.match(NATIVE_CARDINALITY_PATTERN)
  if (match) {
    return {
      uri: cap.uri,
      rule: 'RULE-9-NATIVE_CARDINALITY_IN_DESCRIPTION',
      detail: `Literal thousands-separated figure '${match[0]}' found in description — likely an ` +
        `embedded native/chart-specific row count (GT-32/GT-43). Strip the literal figure; ` +
        `descriptions are served to every caller regardless of chart context.`,
    }
  }
  if (NATIVE_CHART_PHRASE_PATTERN.test(desc)) {
    return {
      uri: cap.uri,
      rule: 'RULE-9B-NATIVE_CHART_PHRASE_IN_DESCRIPTION',
      detail: `Phrase 'native chart' found in description — served text must not reference ` +
        `"the native" or "the native chart" (chart-agnostic mandate).`,
    }
  }
  return null
}

/**
 * Reusable, non-capability-scoped text scanner (GT-54, 2026-07-19 audit).
 * Applies the same forbidden-pattern set as Rules 2/3/9 to an arbitrary served string that
 * is NOT a CapabilityDescriptor.description field — e.g. a dynamically constructed
 * `empty_reason` string built inside a handler body (invisible to checkCapability, which
 * only ever sees the static descriptor object). d8's TEMPORAL_EMPTY_REASON leaked a
 * native-derived count ("native chart 0/13,364 dated on lahiri") via exactly this code path.
 * Call directly wherever a served free-text literal is constructed, or from a test that
 * imports the literal.
 */
export function checkTextForNativeLeak(text: string, label = 'served_text'): GateViolation[] {
  const violations: GateViolation[] = []

  if (text.includes(NATIVE_CHART_ID)) {
    violations.push({
      uri: label,
      rule: 'RULE-2-NATIVE_ID_IN_DESCRIPTION',
      detail: `Literal native chart_id '${NATIVE_CHART_ID}' found in ${label}.`,
    })
  }
  if (text.includes(PHANTOM_CHART_ID)) {
    violations.push({
      uri: label,
      rule: 'RULE-2-PHANTOM_ID_IN_DESCRIPTION',
      detail: `Phantom chart_id prefix '${PHANTOM_CHART_ID}' found in ${label}.`,
    })
  }
  for (const id of NATIVE_IDENTIFIERS_IN_DESCRIPTION) {
    if (id === NATIVE_CHART_ID) continue // already checked above
    if (text.includes(id)) {
      violations.push({
        uri: label,
        rule: 'RULE-3-NATIVE_IDENTIFIER_IN_DESCRIPTION',
        detail: `Native identifier '${id}' found in ${label}. Served text must not carry native PII.`,
      })
    }
  }
  const cardinalityMatch = text.match(NATIVE_CARDINALITY_PATTERN)
  if (cardinalityMatch) {
    violations.push({
      uri: label,
      rule: 'RULE-9-NATIVE_CARDINALITY_IN_DESCRIPTION',
      detail: `Literal thousands-separated figure '${cardinalityMatch[0]}' found in ${label} — ` +
        `likely an embedded native/chart-specific row count (GT-32/GT-43/GT-54).`,
    })
  }
  if (NATIVE_CHART_PHRASE_PATTERN.test(text)) {
    violations.push({
      uri: label,
      rule: 'RULE-9B-NATIVE_CHART_PHRASE_IN_DESCRIPTION',
      detail: `Phrase 'native chart' found in ${label} — served text must not reference ` +
        `"the native" or "the native chart" (chart-agnostic mandate).`,
    })
  }
  return violations
}

// ── Gate runner ───────────────────────────────────────────────────────────────

/**
 * Check a single capability against all chart-agnostic gate rules.
 * Returns an array of violations (empty = pass).
 */
export function checkCapability(cap: CapabilityDescriptor): GateViolation[] {
  const violations: GateViolation[] = []

  const checks = [
    checkPerChartRequiresChartId,
    checkNoNativeIdInDescription,
    checkNoNativeIdentifierInDescription,
    checkNoDefaultOnChartId,
    checkNoNativeIdInChartIdDescription,
    checkGlobalNotRequiringChartId,
    checkD1ContractFieldsPresent,
    checkNoNativeCardinalityInDescription,
  ]

  for (const check of checks) {
    const violation = check(cap)
    if (violation) violations.push(violation)
  }

  return violations
}

/**
 * Run the chart-agnostic gate across all registered capabilities.
 * Returns all violations found.
 */
export function checkAllCapabilities(capabilities: CapabilityDescriptor[]): GateViolation[] {
  const all: GateViolation[] = []
  for (const cap of capabilities) {
    all.push(...checkCapability(cap))
  }
  return all
}

/**
 * Format violations into a human-readable report.
 */
export function formatViolations(violations: GateViolation[]): string {
  if (violations.length === 0) return '[chart_agnostic_gate] PASS — no violations found'

  const lines: string[] = [
    `[chart_agnostic_gate] FAIL — ${violations.length} violation(s) found`,
    '',
  ]

  for (const v of violations) {
    lines.push(`  URI:    ${v.uri}`)
    lines.push(`  Rule:   ${v.rule}`)
    lines.push(`  Detail: ${v.detail}`)
    lines.push('')
  }

  return lines.join('\n')
}

/**
 * Run the gate and throw on any violation.
 * For use in CI alongside runParityCheck().
 */
export function runChartAgnosticGate(capabilities: CapabilityDescriptor[]): void {
  const violations = checkAllCapabilities(capabilities)

  if (violations.length > 0) {
    throw new Error(formatViolations(violations))
  }

  console.log(
    `[chart_agnostic_gate] PASS — ${capabilities.length} capabilities checked, 0 violations`
  )
}

// ── Rule 8: MCP Tool File Hygiene (amendment 2026-06-28) ─────────────────────

/**
 * Rule 8 (MCP Tool Hygiene Gate) — Extension amendment 2026-06-28.
 * Scans platform-mcp/src/tools/**\/*.ts files for native identifier contamination.
 * Called separately from the capability registry scan (which covers registered capabilities only).
 * This covers ALL tool files — wired and unwired — to catch future contamination before wiring.
 */
export const MCP_TOOLS_DIR_PATTERNS = [
  /482012f1/,
  /NATIVE_CHART_ID/,
  /Abhisek\s+Mohanty/,
] as const

export interface McpToolFileViolation {
  file: string
  line: number
  pattern: string
  text: string
}

export function scanMcpToolFileContent(
  filePath: string,
  content: string
): McpToolFileViolation[] {
  const violations: McpToolFileViolation[] = []
  const lines = content.split('\n')
  for (let i = 0; i < lines.length; i++) {
    for (const pattern of MCP_TOOLS_DIR_PATTERNS) {
      if (pattern.test(lines[i])) {
        violations.push({
          file: filePath,
          line: i + 1,
          pattern: pattern.toString(),
          text: lines[i].trim(),
        })
      }
    }
  }
  return violations
}

// ── CLI entry point ───────────────────────────────────────────────────────────

// When run directly (tsx chart_agnostic_gate.ts), load and check the registry.
if (require.main === module || (typeof process !== 'undefined' && process.argv[1]?.includes('chart_agnostic_gate'))) {
  ;(async () => {
    // Dynamic import to avoid circular dependency at module-load time
    const { getAllCapabilities } = await import('./index')
    const caps = getAllCapabilities()
    try {
      runChartAgnosticGate(caps)
      process.exit(0)
    } catch (err) {
      console.error(err instanceof Error ? err.message : String(err))
      process.exit(1)
    }
  })()
}
