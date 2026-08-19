/**
 * Paripraśna safety — THE SENSITIVE CAPABILITY CLASS (lane G1-A).
 *
 * Two requirements share one list, which is why the list lives in its own file:
 *
 *  · HS-1/HS-4 point (a) — plan-time capability exclusion. "Mortality-window
 *    capabilities are excluded from plans for query_class sensitive/mortality
 *    unless the aggregate-framing path is chosen." A plan that never carries
 *    `get_ayurdaya` cannot produce an individualized mortality window from it.
 *  · Abuse case A6 / architecture §2 — "Sensitive-class capabilities MUST be
 *    excluded from the `consult` profile." The raw-MCP plane has no prose gate,
 *    so enforcement there is capability-level.
 *
 * ── WHY THIS LIST AND NOT A HEURISTIC ────────────────────────────────────────
 * A name-pattern rule (`/medical|health|ayur/`) would be shorter and would also
 * silently change membership every time someone names a new tool. An explicit,
 * reviewed list makes an addition a diff. The cost is that a NEW sensitive tool
 * is not covered until someone adds it here — which is exactly why
 * `sensitive_capability_parity.test.ts` also asserts the platform-mcp mirror
 * matches, and why the list is annotated with what is deliberately NOT in it.
 *
 * ── WHAT IS DELIBERATELY NOT IN IT ───────────────────────────────────────────
 * `get_sensitive_degrees` / `get_sensitive_points` are NOT here. Their
 * "sensitive" is the astrological sense (gaṇḍānta, sandhi, mṛtyu-bhāga degrees),
 * not the disclosure-class sense. Including them on the strength of the word
 * would be pattern-matching on a name rather than on what the capability serves.
 * Note the one genuine tension recorded rather than hidden: `mṛtyu-bhāga` IS a
 * mortality-adjacent degree, and a caller who reads it raw can reason toward a
 * mortality claim. The defense there is the CLASSIFIER (a question that reaches
 * for it trips the HS-4 lexicon) plus the pre-wire scan, not capability
 * exclusion — because excluding the degree table would break a large amount of
 * ordinary chart work for a leak path prose-side controls already cover.
 */

/**
 * Mortality-domain capabilities. HS-1 point (a) excludes these from any plan
 * whose safety decision carries `hs1_date_of_death` or `hs4_mortality_window`
 * without a released aggregate-framing path.
 */
export const MORTALITY_CLASS_CAPABILITIES: readonly string[] = [
  'get_ayurdaya',
  'ganita_ayurdaya_get',
] as const

/**
 * Health/medical capabilities. HS-3 does not exclude these at plan time — a
 * health reading is permitted, it just cannot LEAVE the session unreviewed — so
 * this set is used by the `consult`-profile exclusion and by the classifier's
 * capability rules, not by the plan-time filter.
 */
export const MEDICAL_CLASS_CAPABILITIES: readonly string[] = [
  'assess_health',
  'get_medical_indications',
  'ganita_medical_get',
  'query_medical_mappings',
  'query_nakshatra_medical',
  'query_sign_medical',
  'ref_sign_medical_get',
] as const

/** The union — the "sensitive class" the architecture's §2 door table names. */
export const SENSITIVE_CLASS_CAPABILITIES: readonly string[] = [
  ...MORTALITY_CLASS_CAPABILITIES,
  ...MEDICAL_CLASS_CAPABILITIES,
].sort()

export function isSensitiveClassCapability(toolName: string): boolean {
  return SENSITIVE_CLASS_CAPABILITIES.includes(toolName)
}

/**
 * HS-1/HS-4 plan-time exclusion (enforcement point (a)).
 *
 * Returns the capability names that must NOT be authorized for this turn.
 * Empty unless a mortality class was detected — a health question does not lose
 * its health tools, and a career question loses nothing at all.
 */
export function capabilitiesExcludedFor(classes: readonly string[]): string[] {
  const mortality =
    classes.includes('hs1_date_of_death') || classes.includes('hs4_mortality_window')
  if (!mortality) return []
  return [...MORTALITY_CLASS_CAPABILITIES]
}

/**
 * Apply the exclusion to an authorized-tool list.
 *
 * Pure and total: returns the kept list and the stripped names, so the caller
 * can report a COUNT on the wire (gate 11 [integrity] — never the raw names)
 * while logging the names server-side.
 */
export function applyCapabilityExclusion(
  toolNames: readonly string[],
  excluded: readonly string[],
): { kept: string[]; stripped: string[] } {
  if (excluded.length === 0) return { kept: [...toolNames], stripped: [] }
  const excludedSet = new Set(excluded)
  const kept: string[] = []
  const stripped: string[] = []
  for (const t of toolNames) (excludedSet.has(t) ? stripped : kept).push(t)
  return { kept, stripped }
}
