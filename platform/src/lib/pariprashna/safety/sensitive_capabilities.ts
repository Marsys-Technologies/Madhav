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

/**
 * ELECTION / TIMING capabilities — the ones that answer "give me a DATE".
 *
 * ── WHY THIS SET EXISTS (hardening round, C-1) ───────────────────────────────
 * The first build excluded nothing at all for HS-2: `capabilitiesExcludedFor
 * (['hs2_suicide_adjacent'])` returned `[]`. In isolation that looked
 * defensible — HS-2 hard-stops before the planner, so there is no plan to strip
 * a capability from.
 *
 * It is not defensible in combination with two other facts. First, HS-2 is not
 * only reached pre-plan: `reclassifyAfterPlan` can raise a turn to HS-2 at
 * plan time, and a hard-stop decision that names no excluded capability is one
 * ordering bug away from an elected date. Second, and decisively, the class of
 * question this round added to the classifier IS an election request — "which
 * tithi is best for prayopaveśa", "the most auspicious muhūrta to leave this
 * body". For that question the electional finder is not incidental: it is the
 * exact instrument the asker came for. A caught HS-2 turn must never be able to
 * receive an elected date, and "the hard stop happens to run first" is a
 * property of the current call order, not a control.
 *
 * So the exclusion is stated on the DECISION, where it is a fact about the turn
 * that any later stage can enforce, rather than left implicit in the ordering.
 *
 * Names are the real registry/MCP capability ids, verified against
 * `retrieval/registry/tool_name_bridge.ts` and `canonical_faces.json` — not
 * guessed. `kala_muhurta_get` is the (deprecated) MCP alias, `kala_elect_get`
 * its successor, `query_muhurat` the platform-internal L4 electional finder
 * that both resolve to, `muhurta_finder` its legacy alias, and the two
 * `query_*_lattice/graph` readers the contender-lattice engine sits on.
 */
export const ELECTION_CLASS_CAPABILITIES: readonly string[] = [
  'kala_elect_get',
  'kala_muhurta_get',
  'muhurta_finder',
  'query_muhurat',
  'query_muhurta_lattice',
  'query_parihara_graph',
  'gochara_election_avoidance_get',
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
 * Plan-time capability exclusion (HS-1/HS-4 enforcement point (a), plus the
 * HS-2 election exclusion added by the hardening round).
 *
 * Returns the capability names that must NOT be authorized for this turn:
 *   · HS-1 / HS-4  → the mortality capabilities. A plan that never carries
 *     `get_ayurdaya` cannot produce an individualized mortality window from it.
 *   · HS-2         → the mortality capabilities AND the ELECTION capabilities.
 *     A caught suicide-adjacent turn must never be able to receive an elected
 *     date; see `ELECTION_CLASS_CAPABILITIES` for why this is stated on the
 *     decision rather than left to the fact that the hard stop runs first.
 *
 * Empty otherwise — a health question does not lose its health tools (HS-3
 * gates on RELEASE, not on retrieval), and a career question loses nothing.
 *
 * NOTE what is deliberately NOT done: the election capabilities are excluded
 * PER TURN here, and are NOT added to `SENSITIVE_CLASS_CAPABILITIES`. That set
 * governs the standing `consult`-profile exclusion, and removing muhūrta from
 * the profile outright would break electional astrology — one of the things
 * this instrument legitimately exists to do — for every user on every turn.
 * The exclusion belongs to the turn that earned it, not to the product.
 */
export function capabilitiesExcludedFor(classes: readonly string[]): string[] {
  const excluded = new Set<string>()
  if (classes.includes('hs1_date_of_death') || classes.includes('hs4_mortality_window')) {
    for (const c of MORTALITY_CLASS_CAPABILITIES) excluded.add(c)
  }
  if (classes.includes('hs2_suicide_adjacent')) {
    for (const c of MORTALITY_CLASS_CAPABILITIES) excluded.add(c)
    for (const c of ELECTION_CLASS_CAPABILITIES) excluded.add(c)
  }
  return [...excluded]
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
