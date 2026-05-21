// IntraSignalDetector — ICR stream implementation
// ICR-S1: interface + empty class skeleton (2026-05-21)
// ICR-S3: Class A detector implemented (2026-05-21)

import { readFileSync } from 'node:fs';
import type { ConflictRecord } from './types';
import { readForensicField } from './forensic_reader';

export interface DetectorConfig {
  msr_path: string;
  forensic_path: string;
}

// ─────────────────────────────────────────────────────────────────────────────
// MSR parser types
// ─────────────────────────────────────────────────────────────────────────────

interface ParsedSignal {
  /** e.g. "MSR.377" */
  id: string;
  /** e.g. "SIG.MSR.377" */
  full_id: string;
  /** signal_name line value */
  signal_name: string;
  /** Full block text for the signal */
  block: string;
  /** Line number where the signal starts (1-indexed) */
  line_start: number;
}

// ─────────────────────────────────────────────────────────────────────────────
// Sign canonicalisation helpers
// ─────────────────────────────────────────────────────────────────────────────

/** Zodiac signs in order (index 0 = Aries). */
const SIGNS = [
  'Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
  'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces',
] as const;

type Sign = typeof SIGNS[number];

/**
 * Extract the first zodiac sign mentioned in a text string.
 * Returns the canonical sign name or null.
 */
function extractSign(text: string): Sign | null {
  for (const sign of SIGNS) {
    // word-bounded match (case-insensitive)
    if (new RegExp(`\\b${sign}\\b`, 'i').test(text)) {
      return sign;
    }
  }
  return null;
}

/**
 * Normalise a sign string so comparisons work regardless of capitalisation or
 * trailing house labels like "Libra (7th House)".
 */
function canonicaliseSign(raw: string): Sign | null {
  return extractSign(raw);
}

// ─────────────────────────────────────────────────────────────────────────────
// MSR file parser
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Parse an MSR markdown file into an array of ParsedSignal objects.
 *
 * Format expected:
 *   SIG.MSR.NNN:
 *     signal_name: "..."
 *     ...
 *
 * Signals are delimited by blank lines followed by the next SIG.MSR. header
 * or end-of-file.
 */
export function parseMsrSignals(content: string): ParsedSignal[] {
  const signals: ParsedSignal[] = [];
  const lines = content.split('\n');

  // Walk lines accumulating signal blocks
  let currentId: string | null = null;
  let currentFullId: string | null = null;
  let blockLines: string[] = [];
  let lineStart = 0;

  const SIG_HEADER = /^(SIG\.(MSR\.\d+)):/;

  function flush() {
    if (!currentId || !currentFullId) return;
    const block = blockLines.join('\n');
    // Extract signal_name
    const nameMatch = block.match(/^\s*signal_name:\s*"(.+?)"\s*$/m);
    const signal_name = nameMatch ? nameMatch[1] : '';
    signals.push({
      id: currentId,
      full_id: currentFullId,
      signal_name,
      block,
      line_start: lineStart,
    });
  }

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const m = line.match(SIG_HEADER);
    if (m) {
      flush();
      currentFullId = m[1]; // e.g. "SIG.MSR.377"
      currentId = m[2];     // e.g. "MSR.377"
      blockLines = [line];
      lineStart = i + 1;
    } else if (currentId) {
      blockLines.push(line);
    }
  }
  flush();

  return signals;
}

// ─────────────────────────────────────────────────────────────────────────────
// Class A conflict rules
// ─────────────────────────────────────────────────────────────────────────────

/**
 * A Muntha placement rule: if a signal's name asserts a specific sign for
 * Muntha, compare it against the FORENSIC VRS.MUNTHA.SIGN field.
 *
 * Signal_name format observed:
 *   "Tajika — Muntha Position at Age 42 (2026): Muntha in Gemini 3H = ..."
 *
 * FORENSIC field VRS.MUNTHA.SIGN:
 *   "Libra (7th House)"
 *
 * Conflict: signal name says Gemini; FORENSIC says Libra.
 */
function checkMunthaSignPlacement(
  signal: ParsedSignal,
  forensicPath: string,
): ConflictRecord | null {
  // Does the signal_name mention Muntha + a sign placement?
  if (!/\bMuntha\b/i.test(signal.signal_name)) return null;

  // Extract the sign asserted in the signal_name
  // Pattern: "Muntha in <Sign>" — look specifically after "Muntha in"
  const inSignMatch = signal.signal_name.match(/\bMuntha\s+in\s+([A-Za-z]+)/i);
  if (!inSignMatch) return null;

  const assertedSignRaw = inSignMatch[1];
  const assertedSign = canonicaliseSign(assertedSignRaw);
  if (!assertedSign) return null;

  // Read the FORENSIC Muntha sign
  const forensicRaw = readForensicField('VRS.MUNTHA.SIGN', forensicPath);
  if (!forensicRaw) return null;

  const forensicSign = canonicaliseSign(forensicRaw);
  if (!forensicSign) return null;

  // Compare
  if (assertedSign.toLowerCase() === forensicSign.toLowerCase()) {
    return null; // agreement — no conflict
  }

  // Conflict detected
  const now = new Date().toISOString();
  return {
    conflict_id: 'DIS.013',
    conflict_class: 'A',
    signal_ids_affected: [signal.id],
    description:
      `Signal ${signal.id} name asserts "Muntha in ${assertedSign}" ` +
      `but FORENSIC VRS.MUNTHA.SIGN = "${forensicRaw}". ` +
      `The signal name is inconsistent with the L1 canonical Varshaphal record.`,
    detected_at: now,
    evidence:
      `signal_name: "${signal.signal_name}" → asserted_sign: "${assertedSign}" | ` +
      `FORENSIC VRS.MUNTHA.SIGN: "${forensicRaw}" → forensic_sign: "${forensicSign}" | ` +
      `MISMATCH: ${assertedSign} ≠ ${forensicSign}`,
  };
}

// ─────────────────────────────────────────────────────────────────────────────
// Detector class
// ─────────────────────────────────────────────────────────────────────────────

export class IntraSignalDetector {
  constructor(private config: DetectorConfig) {}

  /**
   * Detect Class A conflicts: a signal's claim disagrees with its cited FORENSIC sources.
   *
   * Class A rules implemented (ICR-S3):
   * 1. Muntha sign placement — if signal_name asserts "Muntha in <Sign>" but
   *    FORENSIC VRS.MUNTHA.SIGN disagrees, emit ConflictRecord (DIS.013).
   */
  async detectClassA(): Promise<ConflictRecord[]> {
    const content = readFileSync(this.config.msr_path, 'utf-8');
    const signals = parseMsrSignals(content);
    const conflicts: ConflictRecord[] = [];

    for (const signal of signals) {
      const c = checkMunthaSignPlacement(signal, this.config.forensic_path);
      if (c) conflicts.push(c);
    }

    return conflicts;
  }

  /**
   * Detect Class B conflicts: two signals make incompatible claims about the same chart point.
   * Implementation deferred to a future ICR session.
   */
  async detectClassB(): Promise<ConflictRecord[]> {
    // ICR-S3 scope: Class A only. Class B deferred.
    return [];
  }

  /**
   * Detect Class C conflicts: a signal's interpretation contradicts the synthesis layer.
   * Implementation deferred to a future ICR session.
   */
  async detectClassC(): Promise<ConflictRecord[]> {
    // ICR-S3 scope: Class A only. Class C deferred.
    return [];
  }

  /**
   * Run all detectors and return combined conflict list.
   */
  async detectAll(): Promise<ConflictRecord[]> {
    const [a, b, c] = await Promise.all([
      this.detectClassA(),
      this.detectClassB(),
      this.detectClassC(),
    ]);
    return [...a, ...b, ...c];
  }
}
