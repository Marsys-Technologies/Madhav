/**
 * l1_truth_index.ts — L1 Truth Index Scorer
 *
 * ICR-S2 (2026-05-21): For each MSR signal, determine whether its content
 * contains at least one citation to FORENSIC or LEL (L1 canonical sources).
 *
 * A signal is considered "grounded" if any of the following appear anywhere
 * in its block:
 *   - FORENSIC (covers "FORENSIC §<section>" and "FORENSIC_ASTROLOGICAL_DATA_v8_0")
 *   - LIFE_EVENT_LOG
 *   - LEL (word-bounded, to avoid false matches like "paralleled")
 *   - LEL.<CATEGORY>.<N> style event IDs
 *   - EVT.\d{4} — LEL event ID format (e.g. EVT.2023.05.XX.01)
 */

// ─────────────────────────────────────────────────────────────────────────────
// Types
// ─────────────────────────────────────────────────────────────────────────────

export interface SignalResult {
  /** e.g. "SIG.MSR.001" */
  id: string;
  /** true if at least one L1 citation found */
  grounded: boolean;
}

export interface L1TruthIndexReport {
  total_signals: number;
  grounded_signals: number;
  ungrounded_signals: number;
  /** 0–100 percentage */
  coverage_score: number;
  /** IDs of signals with no L1 citation */
  ungrounded_ids: string[];
  /** Whether coverage meets the ≥95% threshold */
  passes_gate: boolean;
}

// ─────────────────────────────────────────────────────────────────────────────
// Citation patterns that qualify as an L1 grounding reference
// ─────────────────────────────────────────────────────────────────────────────

const L1_PATTERNS: RegExp[] = [
  /FORENSIC/,                    // covers FORENSIC §N, FORENSIC_ASTROLOGICAL_DATA_v8_0, etc.
  /FORENSIC_ASTROLOGICAL_DATA_v8_0/, // explicit canonical filename (also caught by above)
  /LIFE_EVENT_LOG/,              // full canonical name
  /\bLEL\b/,                    // word-bounded to avoid "paralleled" etc.
  /LEL\.[A-Z]+\.\d+/,           // LEL event ID format: LEL.CAREER.1 etc.
  /\bEVT\.\d{4}/,               // LEL log event IDs: EVT.2023.05.XX.01
];

/**
 * Return true if the signal block content contains at least one L1 citation.
 */
export function isGrounded(signalContent: string): boolean {
  return L1_PATTERNS.some((pat) => pat.test(signalContent));
}

// ─────────────────────────────────────────────────────────────────────────────
// Parser
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Parse an MSR markdown file and return per-signal grounding results.
 *
 * Signal blocks are identified by the pattern "^SIG.MSR.NNN:" on its own line
 * (after stripping YAML frontmatter). Each block extends until the next
 * SIG.MSR.NNN: header or end-of-file.
 */
export function parseMsrFile(content: string): SignalResult[] {
  // Remove YAML frontmatter (---...--- block at the start)
  const withoutFrontmatter = content.replace(/^---[\s\S]*?---\n?/, '');

  // Split on signal headers, keeping the delimiter
  const parts = withoutFrontmatter.split(/^(SIG\.MSR\.\d+):$/m);

  // parts[0] = preamble text before first signal
  // parts[1] = 'SIG.MSR.001', parts[2] = content of signal 001
  // parts[3] = 'SIG.MSR.002', parts[4] = content of signal 002, ...

  const results: SignalResult[] = [];
  for (let i = 1; i + 1 < parts.length; i += 2) {
    const id = parts[i];        // e.g. "SIG.MSR.001"
    const body = parts[i + 1];  // everything until next SIG.MSR header
    results.push({ id, grounded: isGrounded(body) });
  }

  return results;
}

// ─────────────────────────────────────────────────────────────────────────────
// Aggregator
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Compute the L1 truth index report from a list of per-signal results.
 */
export function computeReport(signals: SignalResult[]): L1TruthIndexReport {
  const grounded = signals.filter((s) => s.grounded);
  const ungrounded = signals.filter((s) => !s.grounded);
  const coverage = signals.length === 0
    ? 0
    : (grounded.length / signals.length) * 100;

  return {
    total_signals: signals.length,
    grounded_signals: grounded.length,
    ungrounded_signals: ungrounded.length,
    coverage_score: Math.round(coverage * 10) / 10,
    ungrounded_ids: ungrounded.map((s) => s.id),
    passes_gate: coverage >= 95,
  };
}
