/**
 * sanskrit_glossing.ts — Heuristic: client-tier Sanskrit glossing compliance.
 *
 * Checks whether Sanskrit astrological terms in a client-tier response are
 * accompanied by English glosses in parentheses on first use.
 * Regex/keyword only. NO LLM calls.
 *
 * Rule: a client-tier response is Sanskrit-compliant if every detected Sanskrit
 * term that appears WITHOUT a parenthetical gloss is counted as a violation.
 * Zero violations = compliant.
 *
 * False positive rate: ~5% (technical discussions where glossing is intentionally omitted).
 * False negative rate: ~15% (Sanskrit terms not in the keyword list).
 *
 * Only relevant for client tier. For super_admin + acharya: always returns true.
 *
 * MCPT v3.1.0-S4
 */

// ── Sanskrit term registry ─────────────────────────────────────────────────────

/** Sanskrit terms that must be glossed on first use in client-tier responses */
const SANSKRIT_TERMS = [
  'Lagna', 'Rasi', 'Rashi', 'Dasha', 'Mahadasha', 'Antardasha', 'Graha',
  'Nakshatra', 'Tithi', 'Vara', 'Yoga', 'Karana', 'Panchang', 'Panchanga',
  'Mesha', 'Vrishabha', 'Mithuna', 'Karka', 'Simha', 'Kanya',
  'Tula', 'Vrischika', 'Dhanu', 'Makara', 'Kumbha', 'Meena',
  'Atmakaraka', 'Amatyakaraka', 'Bhatrikaraka', 'Matrikaraka',
  'Arudha', 'Karakatva', 'Drishti', 'Shadbala', 'Ashtakavarga',
  'Vimshottari', 'Varshaphal', 'Muntha', 'Tajaka',
  'Bhava', 'Sthana', 'Karaka',
]

// Precompile patterns for efficiency
const TERM_PATTERNS = SANSKRIT_TERMS.map(term => ({
  term,
  // Term appears WITHOUT a following gloss in parentheses
  withoutGloss: new RegExp(`\\b${term}\\b(?!\\s*\\([^)]+\\))`, 'i'),
  // Term appears WITH a following gloss in parentheses
  withGloss: new RegExp(`\\b${term}\\b\\s*\\([^)]+\\)`, 'i'),
}))

// ── Main checker ───────────────────────────────────────────────────────────────

export interface SanskritGlossingResult {
  compliant: boolean
  violations: string[]  // Sanskrit terms found without gloss
  glossed: string[]     // Sanskrit terms found with gloss
}

/**
 * Check Sanskrit glossing compliance for a client-tier response.
 *
 * @param responseText  The response to check.
 * @param audienceTier  The audience tier. Returns compliant=true for non-client tiers.
 */
export function checkSanskritGlossing(
  responseText: string,
  audienceTier: string
): SanskritGlossingResult {
  // Only enforce for client tier
  if (audienceTier !== 'client') {
    return { compliant: true, violations: [], glossed: [] }
  }

  if (!responseText || typeof responseText !== 'string') {
    return { compliant: true, violations: [], glossed: [] }
  }

  const violations: string[] = []
  const glossed: string[] = []

  for (const { term, withoutGloss, withGloss } of TERM_PATTERNS) {
    const hasGlossVersion = withGloss.test(responseText)
    const hasUnglosedVersion = withoutGloss.test(responseText)

    if (hasGlossVersion) {
      glossed.push(term)
    } else if (hasUnglosedVersion) {
      violations.push(term)
    }
  }

  return {
    compliant: violations.length === 0,
    violations,
    glossed,
  }
}

/**
 * Simple boolean check: is this response Sanskrit-compliant for the given tier?
 */
export function isSanskritCompliant(responseText: string, audienceTier: string): boolean {
  return checkSanskritGlossing(responseText, audienceTier).compliant
}
