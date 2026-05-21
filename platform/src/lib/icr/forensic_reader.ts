/**
 * forensic_reader.ts — Thin reader for FORENSIC_ASTROLOGICAL_DATA_v8_0.md
 *
 * ICR-S3 (2026-05-21): Extracts field values from the FORENSIC L1 record
 * for use by the Class A conflict detector.
 *
 * Design principles:
 * - No LLM calls. Pure filesystem read + regex extraction.
 * - No caching. Fresh read on each call.
 * - Returns null if field is not found.
 */

import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

// ─────────────────────────────────────────────────────────────────────────────
// Field catalogue
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Well-known FORENSIC field IDs with their display labels.
 * The reader supports arbitrary fieldRef strings too; this list is used
 * for alias resolution.
 */
const FIELD_ALIASES: Record<string, string[]> = {
  'VRS.MUNTHA.SIGN': ['Muntha', 'VRS.MUNTHA.SIGN'],
  'VRS.MUNTHA.LORD': ['Muntha Lord', 'VRS.MUNTHA.LORD'],
  'LAGNA': ['Lagna', 'Ascendant', 'Rising sign'],
  'MOON.SIGN': ['Moon sign', 'Rashi'],
  'SUN.SIGN': ['Sun sign'],
};

// ─────────────────────────────────────────────────────────────────────────────
// Public API
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Extract the value for a named field from the FORENSIC markdown file.
 *
 * Strategy: scan for a markdown table row of the form:
 *   | `<ID>` | <label> | <value> |
 * or
 *   | `<ID>` | <label> | <value> |
 *
 * The lookup tries:
 * 1. Exact match on the backtick-quoted ID in the first column: `VRS.MUNTHA.SIGN`
 * 2. Partial label match in the second column: "Muntha"
 *
 * Returns the trimmed value string, or null if not found.
 */
export function readForensicField(
  fieldRef: string,
  forensicFilePath: string,
): string | null {
  let content: string;
  try {
    content = readFileSync(forensicFilePath, 'utf-8');
  } catch {
    return null;
  }

  const lines = content.split('\n');

  // Strategy 1: look for exact backtick-quoted ID in table row
  // Pattern: | `VRS.MUNTHA.SIGN` | Muntha | Libra (7th House) |
  const idPattern = new RegExp(
    `\\|\\s*\`${escapeRegex(fieldRef)}\`\\s*\\|[^|]*\\|([^|]+)\\|`,
  );
  for (const line of lines) {
    const m = line.match(idPattern);
    if (m) {
      return m[1].trim();
    }
  }

  // Strategy 2: look for the fieldRef as a label in second column
  // Pattern: | `some_id` | <fieldRef> | <value> |
  const labelPattern = new RegExp(
    `\\|[^|]*\\|\\s*${escapeRegex(fieldRef)}\\s*\\|([^|]+)\\|`,
    'i',
  );
  for (const line of lines) {
    const m = line.match(labelPattern);
    if (m) {
      return m[1].trim();
    }
  }

  // Strategy 3: resolve aliases and retry
  const aliases = FIELD_ALIASES[fieldRef] ?? [];
  for (const alias of aliases) {
    if (alias === fieldRef) continue; // avoid infinite loop
    const result = readForensicField(alias, forensicFilePath);
    if (result !== null) return result;
  }

  return null;
}

/**
 * Convenience: read a field using a repo-root-relative forensic path.
 * Pass the repo root so callers can control path resolution.
 */
export function readForensicFieldFromRepo(
  fieldRef: string,
  repoRoot: string,
): string | null {
  const forensicPath = resolve(
    repoRoot,
    '01_FACTS_LAYER',
    'FORENSIC_ASTROLOGICAL_DATA_v8_0.md',
  );
  return readForensicField(fieldRef, forensicPath);
}

// ─────────────────────────────────────────────────────────────────────────────
// Utilities
// ─────────────────────────────────────────────────────────────────────────────

function escapeRegex(str: string): string {
  return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}
