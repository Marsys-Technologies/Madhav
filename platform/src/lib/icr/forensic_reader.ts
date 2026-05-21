/**
 * forensic_reader.ts — Thin reader for FORENSIC canonical artifact
 *
 * ICR-S3 (2026-05-21): Extracts section content from
 * 01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md by section reference.
 * Used by ICR-S4 (propose-patch step) to cross-check claim values against
 * the canonical FORENSIC source.
 *
 * The FORENSIC file is READ-ONLY — this module never writes to it.
 */

import { readFileSync } from 'node:fs';

// ─────────────────────────────────────────────────────────────────────────────
// Types
// ─────────────────────────────────────────────────────────────────────────────

export interface ForensicSection {
  /** The section reference that was searched (e.g. "§7.4" or "Varshaphala") */
  ref: string;
  /** Up to 500 chars of section text, or null if not found */
  content: string | null;
}

// ─────────────────────────────────────────────────────────────────────────────
// Section matcher
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Build a regex that matches a Markdown heading line containing `sectionRef`.
 *
 * Examples of headings matched by readForensicField("§7.4", ...):
 *   ## §7.4 — Tajika / Varshaphala
 *   ### §7.4
 *
 * Also matches plain keyword searches like "Varshaphala":
 *   ## §7 — Varshaphala & Tajika System
 */
function buildHeadingPattern(sectionRef: string): RegExp {
  // Escape special regex chars in the section reference
  const escaped = sectionRef.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  return new RegExp(`^#{1,6}\\s+.*${escaped}`, 'm');
}

// ─────────────────────────────────────────────────────────────────────────────
// Public API
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Read the FORENSIC file and return the text content of the section that
 * matches `sectionRef` (up to 500 characters).
 *
 * @param forensicPath  Absolute path to FORENSIC_ASTROLOGICAL_DATA_v8_0.md
 * @param sectionRef    Section label to find, e.g. "§7.4" or "Varshaphala"
 * @returns             Up to 500 chars of section body, or null if not found
 */
export function readForensicField(
  forensicPath: string,
  sectionRef: string,
): string | null {
  const content = readFileSync(forensicPath, 'utf-8');
  const pattern = buildHeadingPattern(sectionRef);

  const match = pattern.exec(content);
  if (!match) return null;

  // Extract text from just after the matched heading to either:
  //   (a) the next heading of equal or higher level, or
  //   (b) up to 500 chars, whichever comes first
  const startIdx = match.index + match[0].length;
  const afterHeading = content.slice(startIdx);

  // Take up to 500 chars, stopping at the next heading if sooner
  const nextHeadingMatch = /^#{1,6}\s+/m.exec(afterHeading);
  const endIdx = nextHeadingMatch
    ? Math.min(nextHeadingMatch.index, 500)
    : 500;

  const sectionBody = afterHeading.slice(0, endIdx).trim();
  return sectionBody.length > 0 ? sectionBody : null;
}

/**
 * Convenience wrapper: reads a field and returns a structured result.
 *
 * @param forensicPath  Absolute path to FORENSIC_ASTROLOGICAL_DATA_v8_0.md
 * @param sectionRef    Section label to find
 * @returns             ForensicSection with ref + content (null if not found)
 */
export function readForensicSection(
  forensicPath: string,
  sectionRef: string,
): ForensicSection {
  return {
    ref: sectionRef,
    content: readForensicField(forensicPath, sectionRef),
  };
}
