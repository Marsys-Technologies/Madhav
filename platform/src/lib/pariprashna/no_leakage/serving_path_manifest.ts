/**
 * serving_path_manifest.ts — the machine-readable definition of "the serving
 * path" and "a calibration write / priors bump", shared by the COLLECT-ONLY
 * grep gate (PB-3 lane L-6, §14.6 C1 + wave ruling W-3).
 *
 * BRIEF_PB-3 §F1 Lane L-6 requires COLLECT-ONLY be proven as *absent code with a
 * grep test + runtime assertion, not config*. W-3 is the load-bearing rule: "NO
 * — collect-only stands for the entire campaign (§14.6 C1). No priors bump, no
 * envelope annotation, no minimum-n exception." A calibration write
 * (`mimamsa_calibration` upsert, `record_outcome`, `update_calibration`) may
 * happen — L-5 builds exactly that — but NOTHING downstream of it may bump a
 * `priors_version` or annotate a phala/kala/pariprashna serving envelope.
 *
 * The gate is: no CODE line of any SERVING_PATH_FILE below contains any
 * FORBIDDEN_PATTERN below. The scanner is separately unit-tested against
 * synthetic fixtures (`scannerSelfProof`), so the DETECTOR itself is
 * demonstrated-can-fail (it provably flags a real violation AND provably does
 * NOT flag an honest read), per FOLLOWUP_PB-2_BYTE_EQUALITY_FIXTURE_COVERAGE's
 * rule that a gate which can never go red "actively launders false confidence."
 *
 * ── The false-positive trap this file deliberately avoids ─────────────────────
 * (1) The D-16 provenance stamp legitimately READS `priors_version` and copies
 *     it into a DB-only audit stamp that is never streamed. FORBIDDEN_PATTERNS
 *     therefore match only WRITE / BUMP / SERVE-annotation operations, never a
 *     plain read of the token.
 * (2) A serving file may DOCUMENT a forbidden construct in a comment (e.g.
 *     `envelope.ts` explains how it ALIGNS with `record_outcome()`). A comment
 *     is not a code path. The scanner therefore skips PURE-COMMENT lines (lines
 *     whose first non-whitespace run is `//`, `*`, or block-comment open) rather
 *     than doing general comment-stripping — full comment-stripping risks a
 *     string-literal false-NEGATIVE (`'a//b'; record_outcome()`), and for an
 *     integrity gate a false negative is worse than a false positive. A real
 *     forbidden call lives on a code line, not a pure-comment line.
 */

/**
 * Repo-relative (from the `platform/` package root) paths of every source file
 * that assembles a served phala / kāla / pariprashna reading envelope. Explicit
 * allowlist (not a glob) so a NEW serving-path file added later cannot silently
 * escape the gate, and the gate test asserts every listed path resolves to a
 * real file (a rename that drops coverage fails loudly, not vacuously).
 */
export const SERVING_PATH_FILES: readonly string[] = [
  'src/app/api/pariprashna/route.ts',
  'src/app/api/chat/consult/route.ts',
  'src/app/api/mcp/prashna_ask/route.ts',
  'src/lib/retrieval/envelope.ts',
  'src/lib/retrieval/registry/layers/L4_phala/query_predictive_anchors.ts',
  'src/lib/retrieval/registry/layers/L3_kala/query_projections.ts',
  'src/lib/retrieval/registry/layers/L3_kala/query_convergence_windows.ts',
  // The pariprashna provenance stamp — the ONE serving file that legitimately
  // reads priors_version; included precisely so the gate proves the read is not
  // a bump/write (false-positive trap 1 above).
  'src/lib/pariprashna/provenance/stamp.ts',
  // ── G5 (SAMĀPTI §8.1 / BRIEF_PB-3.1 G5) — the spine-bundle chain ─────────────
  // `query_spine_bundle` pre-joins signal → activation → anchors → CALIBRATION and
  // serves the result as a first-class capability, so these four files assemble a
  // served payload that carries a `calibration` section. The original manifest
  // omitted them, which meant the single most calibration-adjacent serving chain in
  // the estate was the one chain the gate did not scan. Adding them makes the
  // coverage match the claim; all four are CLEAN under FORBIDDEN_PATTERNS today
  // (they READ calibration tables via query_calibration's handler — no write, no
  // priors bump, no envelope annotation), which is precisely what the gate now
  // holds in place.
  'src/lib/retrieval/spine/compute_spine_bundle.ts',
  'src/lib/retrieval/spine/materialize.ts',
  'src/lib/retrieval/registry/layers/register_spine_bundle.ts',
  'src/lib/retrieval/registry/layers/L5_mimamsa/query_calibration.ts',
]

/** A single forbidden construct: a calibration-write or priors-bump signature. */
export interface ForbiddenPattern {
  readonly id: string
  readonly pattern: RegExp
  readonly reason: string
}

/**
 * The forbidden constructs. Every pattern targets a MUTATION or a SERVE-side
 * annotation of calibration data — never a read of a token.
 */
export const FORBIDDEN_PATTERNS: readonly ForbiddenPattern[] = [
  {
    id: 'calibration-sql-write',
    pattern: /\b(INSERT\s+INTO|UPDATE|UPSERT|DELETE\s+FROM)\s+mimamsa_calibration\b/i,
    reason: 'A serving-path file writes to mimamsa_calibration. Calibration writes belong to the out-of-process L-5 outcome path only (§14.6 C1 / W-3).',
  },
  {
    id: 'calibration-write-call',
    pattern: /\b(update_calibration|updateCalibration|record_outcome|recordOutcome|upsertCalibration|writeCalibration)\s*\(/,
    reason: 'A serving-path file calls a calibration-write function. Collect-only forbids any serving code path to a calibration write (W-3).',
  },
  {
    id: 'calibration-writer-import',
    pattern: /(from|require)\s*\(?\s*['"][^'"]*(calibration_producer|ppl_writer|mimamsa\/outcome|mimamsa_outcome)['"]/,
    reason: 'A serving-path file imports a calibration/outcome writer module. The serving path must not depend on the write side at all (W-3).',
  },
  {
    id: 'priors-version-bump',
    pattern: /\bpriors_version\s*(\+\+|\+=)|\bpriors_version\s*=\s*priors_version\b|\b(bump|increment|advance|next)Priors(Version)?\s*\(|SET\s+priors_version\b/i,
    reason: 'A serving-path file bumps priors_version. W-3: "No priors bump" — a calibration write must never advance the priors version, for the entire campaign.',
  },
  {
    id: 'serving-envelope-calibration-annotation',
    pattern: /\b(brier[_-]?score|calibration[_-]?(annotation|badge|adjustment|weight)|priors[_-]?bumped|calibration_applied)\b\s*[:=]/i,
    reason: 'A serving-path file annotates an envelope with a calibration-derived field. W-3: "no envelope annotation" — collect-only means served phala/kala envelopes are byte-identical whether or not calibration data exists.',
  },
]

/** One detected violation, for reporting. */
export interface ScanHit {
  readonly patternId: string
  readonly reason: string
  readonly line: number
  readonly excerpt: string
}

/** True if a line is a pure-comment line (first non-whitespace run is //, *, or /*). */
function isPureCommentLine(line: string): boolean {
  return /^\s*(\/\/|\*\/?|\/\*)/.test(line)
}

/**
 * Pure scanner: returns every forbidden-pattern hit in `source`, skipping
 * pure-comment lines (false-positive trap 2). Line-oriented so the gate can
 * report file:line.
 */
export function scanForForbidden(source: string): ScanHit[] {
  const hits: ScanHit[] = []
  const lines = source.split('\n')
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i]
    if (isPureCommentLine(line)) continue
    for (const fp of FORBIDDEN_PATTERNS) {
      if (fp.pattern.test(line)) {
        hits.push({
          patternId: fp.id,
          reason: fp.reason,
          line: i + 1,
          excerpt: line.trim().slice(0, 160),
        })
      }
    }
  }
  return hits
}

/**
 * Self-consistency fixtures used by the gate test to keep the DETECTOR
 * demonstrated-can-fail:
 *   - a READ-ONLY priors_version line MUST NOT be flagged (no false positive);
 *   - a comment mentioning record_outcome() MUST NOT be flagged (trap 2);
 *   - a BUMP / WRITE / ANNOTATION line MUST each be flagged (real violation caught).
 * If any expectation breaks, the gate test goes red — which is the point.
 */
export function scannerSelfProof(): {
  readOnlyFixture: string
  commentFixture: string
  bumpFixture: string
  writeFixture: string
  annotationFixture: string
} {
  return {
    readOnlyFixture: 'const stamp = { priors_version: current.priors_version }',
    commentFixture: ' * carries an observed outcome (that is record_outcome()’s sole write path).',
    bumpFixture: 'priors_version += 1',
    writeFixture: "await query('UPDATE mimamsa_calibration SET brier = $1', [b])",
    annotationFixture: 'envelope.calibration_badge = deriveBadge(brierScore)',
  }
}
