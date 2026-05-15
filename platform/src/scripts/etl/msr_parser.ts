import type { MsrSignal } from '../../lib/db/types'

/**
 * Strip surrounding quotes from a string value.
 */
function stripQuotes(value: string): string {
  const trimmed = value.trim()
  if (
    (trimmed.startsWith('"') && trimmed.endsWith('"')) ||
    (trimmed.startsWith("'") && trimmed.endsWith("'"))
  ) {
    return trimmed.slice(1, -1)
  }
  return trimmed
}

/**
 * Parse a YAML-style inline array: "[item1, item2, item3]" → ["item1", "item2", "item3"]
 */
function parseInlineArray(value: string): string[] {
  const trimmed = value.trim()
  if (!trimmed.startsWith('[') || !trimmed.endsWith(']')) {
    return []
  }
  const inner = trimmed.slice(1, -1).trim()
  if (!inner) return []
  return inner.split(',').map((s) => s.trim()).filter((s) => s.length > 0)
}

/**
 * Extract the first matching entity by prefix from an array of entity strings.
 * e.g. prefix "PLN." → "PLN.SATURN" → strip prefix → "SATURN"
 */
function extractEntityByPrefix(entities: string[], prefix: string): string | null {
  const match = entities.find((e) => e.startsWith(prefix))
  return match ? match.slice(prefix.length) : null
}

/**
 * Extract the first house entity (HSE.N) and parse the integer.
 */
function extractHouse(entities: string[]): number | null {
  const match = entities.find((e) => e.startsWith('HSE.'))
  if (!match) return null
  const num = parseInt(match.slice(4), 10)
  return isNaN(num) ? null : num
}

/**
 * Extract a single field value from a block of text.
 * Matches lines of the form: "  field_name: value"
 * Returns null if not found.
 */
function extractField(block: string, fieldName: string): string | null {
  // Use a line-by-line approach to find the field
  const lines = block.split('\n')
  for (const line of lines) {
    // Match "  field_name: ..." at indented level
    const match = line.match(new RegExp(`^\\s{2}${fieldName}:\\s*(.*)$`))
    if (match) {
      return match[1].trim()
    }
  }
  return null
}

/**
 * Parse the MSR markdown content and return an array of MsrSignal objects.
 */
export function parseMsrSignals(content: string): MsrSignal[] {
  const signals: MsrSignal[] = []

  // Skip frontmatter (lines between first and second "---")
  let workingContent = content
  const frontmatterStart = content.indexOf('---')
  if (frontmatterStart !== -1) {
    const frontmatterEnd = content.indexOf('---', frontmatterStart + 3)
    if (frontmatterEnd !== -1) {
      workingContent = content.slice(frontmatterEnd + 3)
    }
  }

  // Split into signal blocks: each block starts at a line matching /^SIG\.MSR\.\d+:/
  const lines = workingContent.split('\n')
  const blockStarts: number[] = []

  for (let i = 0; i < lines.length; i++) {
    if (/^SIG\.MSR\.\w+:/.test(lines[i])) {
      blockStarts.push(i)
    }
  }

  for (let b = 0; b < blockStarts.length; b++) {
    const startLine = blockStarts[b]
    const endLine = b + 1 < blockStarts.length ? blockStarts[b + 1] : lines.length
    const blockLines = lines.slice(startLine, endLine)
    const block = blockLines.join('\n')

    // Extract signal_id from the first line
    const keyMatch = blockLines[0].match(/^(SIG\.MSR\.\w+):/)
    if (!keyMatch) continue
    const signal_id = keyMatch[1]

    // signal_name → claim_text
    const signalNameRaw = extractField(block, 'signal_name')
    const claim_text = signalNameRaw ? stripQuotes(signalNameRaw) : ''

    // classical_source → classical_basis
    const classicalSourceRaw = extractField(block, 'classical_source')
    const classical_basis = classicalSourceRaw ? stripQuotes(classicalSourceRaw) : null

    // domains_affected: [...] → first element, lowercase
    const domainsRaw = extractField(block, 'domains_affected')
    let domain = 'unknown'
    if (domainsRaw) {
      const domainItems = parseInlineArray(domainsRaw)
      if (domainItems.length > 0) {
        domain = domainItems[0].toLowerCase()
      }
    }

    // strength_score → significance
    const strengthRaw = extractField(block, 'strength_score')
    const significance = strengthRaw ? parseFloat(strengthRaw) : 0

    // confidence
    const confidenceRaw = extractField(block, 'confidence')
    const confidence = confidenceRaw ? parseFloat(confidenceRaw) : 0

    // temporal_activation — stored raw + derived is_forward_looking
    const temporalRaw = extractField(block, 'temporal_activation')
    const is_forward_looking = temporalRaw
      ? temporalRaw.trim() !== 'natal-permanent'
      : false
    const temporal_activation = temporalRaw ? temporalRaw.trim() : null

    // falsifier
    const falsifierRaw = extractField(block, 'falsifier')
    const falsifier = falsifierRaw ? stripQuotes(falsifierRaw) : null

    // entities_involved: [...] → planet, house, nakshatra + raw array
    const entitiesRaw = extractField(block, 'entities_involved')
    let planet: string | null = null
    let house: number | null = null
    let nakshatra: string | null = null
    let entities_involved: string[] | null = null

    if (entitiesRaw) {
      const entities = parseInlineArray(entitiesRaw)
      planet = extractEntityByPrefix(entities, 'PLN.')
      house = extractHouse(entities)
      nakshatra = extractEntityByPrefix(entities, 'NAK.')
      entities_involved = entities.length > 0 ? entities : null
    }

    // signal_type
    const signal_type = extractField(block, 'signal_type')

    // valence (raw, not normalized)
    const valenceFieldRaw = extractField(block, 'valence')
    const valence = valenceFieldRaw ? valenceFieldRaw.trim() : null

    // supporting_rules — multi-line YAML list; collect lines that start with "    - "
    const supportingRulesLines: string[] = []
    const blockLinesForRules = block.split('\n')
    let inRules = false
    for (const line of blockLinesForRules) {
      if (/^\s{2}supporting_rules:/.test(line)) {
        inRules = true
        continue
      }
      if (inRules) {
        const ruleMatch = line.match(/^\s{4}-\s+(.+)$/)
        if (ruleMatch) {
          supportingRulesLines.push(ruleMatch[1].trim())
        } else if (/^\s{2}\w/.test(line)) {
          inRules = false
        }
      }
    }
    const supporting_rules = supportingRulesLines.length > 0 ? supportingRulesLines : null

    // rpt_deep_dive
    const rptRaw = extractField(block, 'rpt_deep_dive')
    const rpt_deep_dive = rptRaw ? stripQuotes(rptRaw) : null

    // v6_ids_consumed: [...] inline array
    const v6Raw = extractField(block, 'v6_ids_consumed')
    const v6_ids_consumed = v6Raw ? (parseInlineArray(v6Raw).length > 0 ? parseInlineArray(v6Raw) : null) : null

    // prior_id
    const priorRaw = extractField(block, 'prior_id')
    const prior_id = priorRaw ? priorRaw.trim() : null

    signals.push({
      signal_id,
      native_id: 'abhisek_mohanty',
      domain,
      planet,
      house,
      nakshatra,
      dasha_lord: null,
      confidence,
      significance,
      is_forward_looking,
      claim_text,
      classical_basis,
      falsifier,
      source_file: 'MSR_v5_0.md',
      source_version: '5.0',
      ingested_at: new Date().toISOString(),
      signal_type,
      temporal_activation,
      valence,
      entities_involved,
      supporting_rules,
      rpt_deep_dive,
      v6_ids_consumed,
      prior_id,
    })
  }

  return signals
}
