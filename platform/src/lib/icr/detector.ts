// IntraSignalDetector — ICR stream, Class A implementation
// ICR-S1: interface + skeleton (2026-05-21)
// ICR-S3: detectClassA() + detectAll() implemented (2026-05-21)

import { readFileSync } from 'node:fs';
import type { ConflictRecord } from './types';

export interface DetectorConfig {
  msr_path: string;
  forensic_path: string;
}

// ─────────────────────────────────────────────────────────────────────────────
// Zodiac sign list (order matters for display, not for detection)
// ─────────────────────────────────────────────────────────────────────────────

const ZODIAC_SIGNS = [
  'Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
  'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces',
] as const;

type ZodiacSign = typeof ZODIAC_SIGNS[number];

// ─────────────────────────────────────────────────────────────────────────────
// Parsed signal — minimal structure needed by Class A detector
// ─────────────────────────────────────────────────────────────────────────────

export interface ParsedSignal {
  /** e.g. "SIG.MSR.377" */
  id: string;
  /** short numeric part, e.g. "377" */
  num: string;
  signal_name: string;
  falsifier: string;
}

// ─────────────────────────────────────────────────────────────────────────────
// Parser
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Parse MSR markdown content and return a list of signals with their
 * signal_name and falsifier fields.
 *
 * Signal blocks are delimited by "^SIG.MSR.NNN:$" lines (possibly inside
 * a wider YAML-like markdown document). The parser is intentionally simple
 * and line-by-line — no full YAML parser is used.
 */
export function parseMsrSignals(content: string): ParsedSignal[] {
  const lines = content.split('\n');
  const signals: ParsedSignal[] = [];

  // Regex to detect a signal header line
  const SIGNAL_HEADER = /^(SIG\.MSR\.(\d+)):$/;
  // Regex to capture signal_name value (quoted string on the same line)
  const SIGNAL_NAME_RE = /^\s+signal_name:\s+"(.+)"$/;
  // Regex to capture falsifier value (quoted string on the same line)
  const FALSIFIER_RE = /^\s+falsifier:\s+"(.+)"$/;

  let currentId: string | null = null;
  let currentNum: string | null = null;
  let currentSignalName: string | null = null;
  let currentFalsifier: string | null = null;

  const flush = () => {
    if (currentId !== null) {
      signals.push({
        id: currentId,
        num: currentNum!,
        signal_name: currentSignalName ?? '',
        falsifier: currentFalsifier ?? '',
      });
    }
    currentId = null;
    currentNum = null;
    currentSignalName = null;
    currentFalsifier = null;
  };

  for (const line of lines) {
    const headerMatch = SIGNAL_HEADER.exec(line);
    if (headerMatch) {
      // Save the previous signal before starting a new one
      flush();
      currentId = headerMatch[1];
      currentNum = headerMatch[2];
      continue;
    }

    if (currentId === null) continue; // not inside a signal block

    const nameMatch = SIGNAL_NAME_RE.exec(line);
    if (nameMatch && currentSignalName === null) {
      currentSignalName = nameMatch[1];
      continue;
    }

    const falsifierMatch = FALSIFIER_RE.exec(line);
    if (falsifierMatch && currentFalsifier === null) {
      currentFalsifier = falsifierMatch[1];
      continue;
    }
  }

  // Flush the last signal
  flush();

  return signals;
}

// ─────────────────────────────────────────────────────────────────────────────
// Sign extractor
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Return the set of zodiac sign names mentioned in a string.
 */
function extractSigns(text: string): Set<ZodiacSign> {
  const found = new Set<ZodiacSign>();
  for (const sign of ZODIAC_SIGNS) {
    // Use word boundary to avoid partial matches (e.g. "Leo" in "Leonardo")
    const re = new RegExp(`\\b${sign}\\b`);
    if (re.test(text)) {
      found.add(sign);
    }
  }
  return found;
}

// ─────────────────────────────────────────────────────────────────────────────
// Class A: sign/house mismatch detector
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Extract signs that appear in a "confirmed" conclusion within the falsifier.
 *
 * A "confirmed conclusion" is the portion of the falsifier text that ends with
 * or is shortly followed by the word "confirmed". We look for patterns like:
 *   - "<Sign> = confirmed"
 *   - "<Sign> <H> = confirmed"
 *   - "= <Sign> ... = confirmed" within the same clause
 *
 * Strategy: find each occurrence of "confirmed" in the text, then look
 * backwards within a 60-character window for a zodiac sign name.
 */
function extractConfirmedSigns(falsifier: string): Set<ZodiacSign> {
  const found = new Set<ZodiacSign>();
  const confirmPattern = /confirmed/g;
  let m: RegExpExecArray | null;

  while ((m = confirmPattern.exec(falsifier)) !== null) {
    // Look back up to 80 chars before "confirmed"
    const windowStart = Math.max(0, m.index - 80);
    const window = falsifier.slice(windowStart, m.index);
    for (const sign of ZODIAC_SIGNS) {
      // The sign must appear in the window, and not solely as part of
      // a bracketed enumeration (e.g. "(Aries=1, Taurus=2, Gemini=3, ...")
      // We check: the sign appears in window AND the window contains
      // an "= <sign>" pattern (i.e., result of a computation is this sign)
      const assignRe = new RegExp(`=\\s*${sign}\\b`);
      if (assignRe.test(window)) {
        found.add(sign);
      }
    }
  }

  return found;
}

/**
 * Detect a Class A intra-signal conflict for a single signal.
 *
 * Logic:
 *   1. Extract zodiac signs from signal_name.
 *   2. Extract "confirmed" conclusion signs from falsifier — signs that appear
 *      in an assignment context immediately before a "confirmed" clause.
 *   3. If confirmed signs are non-empty AND at least one sign in signal_name
 *      is NOT in the confirmed set → Class A conflict.
 *
 * conflict_id assignment:
 *   - "DIS.013" for the known MSR.377 case
 *   - "DIS.AUTO.<signalNum>" for all others
 */
export function detectSignHouseMismatch(
  signalId: string,
  signalName: string,
  falsifier: string,
): ConflictRecord | null {
  // Only flag when falsifier explicitly confirms something
  if (!falsifier.includes('confirmed')) return null;

  const nameSign = extractSigns(signalName);

  // Extract only signs that are "confirmed" conclusions in the falsifier
  const confirmedSigns = extractConfirmedSigns(falsifier);

  // Need signs in both fields to make a comparison
  if (nameSign.size === 0 || confirmedSigns.size === 0) return null;

  // Find signs claimed in signal_name that are NOT among the confirmed conclusions
  const mismatched: ZodiacSign[] = [];
  for (const sign of nameSign) {
    if (!confirmedSigns.has(sign)) {
      mismatched.push(sign);
    }
  }

  if (mismatched.length === 0) return null;

  // Determine conflict ID
  // Extract numeric part from signalId (e.g. "SIG.MSR.377" → "377")
  const numMatch = /(\d+)$/.exec(signalId);
  const isKnownDIS013 = signalId === 'SIG.MSR.377';
  const conflictId = isKnownDIS013
    ? 'DIS.013'
    : `DIS.AUTO.${numMatch ? numMatch[1] : signalId}`;

  // Build a short MSR reference (e.g. "MSR.377")
  const msr_ref = signalId.replace('SIG.', '');

  const nameSigns = [...nameSign].join(', ');
  const confirmedSignsList = [...confirmedSigns].join(', ');

  return {
    conflict_id: conflictId,
    conflict_class: 'A',
    signal_ids_affected: [msr_ref],
    description:
      `signal_name asserts sign(s) [${nameSigns}] but falsifier confirms [${confirmedSignsList}] — sign/house mismatch within the same signal.`,
    detected_at: new Date().toISOString(),
    evidence:
      `signal_name: "${signalName}" | falsifier: "${falsifier}" | ` +
      `mismatched signs in signal_name not confirmed by falsifier: [${mismatched.join(', ')}]`,
  };
}

// ─────────────────────────────────────────────────────────────────────────────
// IntraSignalDetector class
// ─────────────────────────────────────────────────────────────────────────────

export class IntraSignalDetector {
  constructor(private config: DetectorConfig) {}

  /**
   * Detect Class A conflicts: a signal's claim disagrees with its cited FORENSIC sources.
   * Specifically: sign/house mismatch between signal_name and falsifier.
   */
  async detectClassA(): Promise<ConflictRecord[]> {
    const msrContent = readFileSync(this.config.msr_path, 'utf-8');
    const signals = parseMsrSignals(msrContent);
    const conflicts: ConflictRecord[] = [];

    for (const signal of signals) {
      const conflict = detectSignHouseMismatch(
        signal.id,
        signal.signal_name,
        signal.falsifier,
      );
      if (conflict) conflicts.push(conflict);
    }

    return conflicts;
  }

  /**
   * Detect Class B conflicts: two signals make incompatible claims about the same chart point.
   * Implementation deferred to ICR-S4+.
   */
  async detectClassB(): Promise<ConflictRecord[]> {
    // Not yet implemented — return empty (not throw)
    return [];
  }

  /**
   * Detect Class C conflicts: a signal's interpretation contradicts the synthesis layer.
   * Implementation deferred to ICR-S4+.
   */
  async detectClassC(): Promise<ConflictRecord[]> {
    // Not yet implemented — return empty (not throw)
    return [];
  }

  /**
   * Run all detectors and return combined conflict list.
   */
  async detectAll(): Promise<ConflictRecord[]> {
    const [classA, classB, classC] = await Promise.all([
      this.detectClassA(),
      this.detectClassB(),
      this.detectClassC(),
    ]);
    return [...classA, ...classB, ...classC];
  }
}
