#!/usr/bin/env node
/**
 * claim_audit_gate.mjs — SATYA-ŚEṢA W6 claim-detection heuristic (mechanical, not judgment).
 *
 * Implements the audit-gate rule codified in UAT_BATTERY_v1_0.md (appended 2026-07-25):
 *   Any answer containing an ABSENCE_CLAIM ("not in your data", "no X exists", "isn't in your
 *   computed chart data") or a COVERAGE_CLAIM ("clean", "no adverse window", "nothing found",
 *   "comes back clean") receives adversarial DB-audit at 100%, as a BLOCKING gate before any
 *   grade is recorded. Sampling (partial audit) remains acceptable for all other answers.
 *
 * Pattern seeds (per SATYA_SHESHA_BRIEF_v1_0.md §2 W6):
 *   - EL-07 (ELEVATION_REGISTER_v1_0.md): "isn't actually in your computed chart data"
 *   - EL-09 (ELEVATION_REGISTER_v1_0.md): the general "confident checkable claim" class —
 *     motivates the informational (non-blocking) PRECISION_CLAIM class below, kept separate
 *     from the two BLOCKING classes the rule actually mandates.
 *   - EL-21 (ELEVATION_REGISTER_v1_0.md): "absence claims / exact values / phase-timing
 *     assertions" as the claim shapes a serving-time claim-checker must verify.
 *   - S4-03 verbatim (UAT_DARPANA_ANSWER_APPENDIX_v1_0.md): "I can't give you an exact Gulika
 *     placement, because it isn't actually in your computed chart data" / "...simply isn't
 *     among them."
 *   - S4-05 verbatim (UAT_DARPANA_ANSWER_APPENDIX_v1_0.md): "...it comes back clean — no adverse
 *     window flagged across roughly the next three years."
 *
 * This is deliberately MECHANICAL (regex, no LLM judgment) so the gate is reproducible and
 * auditable itself. It is intentionally over-inclusive (see the dry-run report) — the goal is an
 * appropriately strict gate, not one hand-tuned to only the two known vetoes.
 *
 * Usage:
 *   node claim_audit_gate.mjs [path-to-answer-appendix.md]
 *   (defaults to the sibling UAT_DARPANA_ANSWER_APPENDIX_v1_0.md)
 *
 * Exit code is always 0 — this is a reporting tool, not a CI gate in itself (W6 wires the RULE
 * into the battery spec/process; this script is the mechanical detector the rule cites).
 */

import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

const __dirname = dirname(fileURLToPath(import.meta.url));
const defaultAppendixPath = resolve(
  __dirname,
  "..",
  "UAT_DARPANA_ANSWER_APPENDIX_v1_0.md"
);
const appendixPath = process.argv[2]
  ? resolve(process.cwd(), process.argv[2])
  : defaultAppendixPath;

// --- Claim-class pattern list -----------------------------------------------------------------
// BLOCKING classes (per the codified rule — either one triggers 100% adversarial audit):

const ABSENCE_CLAIM_PATTERNS = [
  // S4-03 exact phrasing + direct paraphrases
  /isn'?t\s+(?:actually\s+)?in\s+your\s+(?:computed\s+)?(?:chart\s+)?data/i,
  /not\s+in\s+your\s+(?:computed\s+)?(?:chart\s+)?data/i,
  /simply\s+isn'?t\s+among\s+them/i,
  /isn'?t\s+among\s+them/i,
  // EL-07's generalized shape: "not in your data" / "no X exists" / "not available/computed"
  /\bno[t]?\s+available\s+in\s+your\s+data/i,
  /\bnot\s+(?:computed|available|present)\s+for\s+you/i,
  /\b(?:not|isn'?t)\s+(?:computed|available|present)\s+in\s+your\b/i,
  /\bdoesn'?t\s+exist\s+in\s+your/i,
  /\bno\s+[\w-]+(?:\s+[\w-]+){0,4}\s+exists?\b/i, // generic "no X exists" (bounded span)
  /\bI\s+can'?t\s+give\s+you\b[^.?!]{0,80}\bbecause\s+it\s+isn'?t\b/i,
  /\bisn'?t\s+available\s+in\s+your\b/i,
  /\bnothing\s+(?:on\s+file|on\s+record)\s+for\b/i,
];

const COVERAGE_CLAIM_PATTERNS = [
  // S4-05 exact phrasing + direct paraphrases
  /comes?\s+back\s+clean/i,
  /came\s+back\s+clean/i,
  /clean\s*[—\-–:]\s*no\s+adverse/i,
  /\bno\s+adverse\s+window/i,
  /\ball[\s-]clear\b/i,
  /\bnothing\s+flagged\b/i,
  /\bnothing\s+found\b/i,
  /\bno\s+rough\s+patch\b/i,
  /\bno\s+red\s+flags?\b/i,
  /\bclean\s+across\b/i,
  /\breads?\s+(?:as\s+)?clean\b/i,
  /\bclean\s+bill\s+of\s+health\b/i,
];

// INFORMATIONAL (non-blocking) class — motivated by EL-09/EL-21's broader "confident checkable
// claim" concept (exact values, phase-timing precision). NOT part of the W6-mandated blocking
// gate; reported separately so the gate itself stays scoped to what the brief's rule actually
// requires, while flagging this as the natural next class for a future extension.
const PRECISION_CLAIM_PATTERNS = [
  /\bexalted\b/i,
  /\bit'?s\s+exact(?:ly)?\b/i,
  /\bprecisely\b/i,
  /\b(?:19|20)\d{2}\b.{0,20}\b(?:to|through|until|–|-)\b.{0,20}\b(?:19|20)\d{2}\b/i, // date ranges
];

const CLAIM_CLASSES = [
  { id: "ABSENCE_CLAIM", blocking: true, patterns: ABSENCE_CLAIM_PATTERNS },
  { id: "COVERAGE_CLAIM", blocking: true, patterns: COVERAGE_CLAIM_PATTERNS },
  { id: "PRECISION_CLAIM (informational, non-blocking)", blocking: false, patterns: PRECISION_CLAIM_PATTERNS },
];

// --- Appendix parsing --------------------------------------------------------------------------
// Each query block: "## <QUERY_ID> (<STREAM>) [optional trailing note]" ... up to the next "## "
// or EOF. The answer is everything from the "**A:**" marker to the end of the block.

function parseAppendix(text) {
  const blocks = [];
  const headingRe = /^##\s+([A-Za-z]+\d*-\d+)\s+\(([A-Za-z]+\d*)\)[^\n]*$/gm;
  const matches = [...text.matchAll(headingRe)];
  for (let i = 0; i < matches.length; i++) {
    const m = matches[i];
    const queryId = m[1];
    const stream = m[2];
    const start = m.index + m[0].length;
    const end = i + 1 < matches.length ? matches[i + 1].index : text.length;
    const blockText = text.slice(start, end);
    const answerMatch = blockText.match(/\*\*A:\*\*\s*([\s\S]*)/);
    const answerText = answerMatch ? answerMatch[1] : blockText;
    blocks.push({ queryId, stream, answerText });
  }
  return blocks;
}

function detectClaims(answerText) {
  const hits = [];
  for (const cls of CLAIM_CLASSES) {
    for (const pattern of cls.patterns) {
      const match = answerText.match(pattern);
      if (match) {
        hits.push({
          claimClass: cls.id,
          blocking: cls.blocking,
          pattern: pattern.source,
          snippet: match[0],
        });
      }
    }
  }
  return hits;
}

// --- Run -----------------------------------------------------------------------------------

function main() {
  const text = readFileSync(appendixPath, "utf8");
  const blocks = parseAppendix(text);

  const results = blocks.map((b) => ({
    queryId: b.queryId,
    stream: b.stream,
    hits: detectClaims(b.answerText),
  }));

  const blockingFlagged = results.filter((r) => r.hits.some((h) => h.blocking));
  const infoOnlyFlagged = results.filter(
    (r) => !r.hits.some((h) => h.blocking) && r.hits.some((h) => !h.blocking)
  );
  const clean = results.filter((r) => r.hits.length === 0);

  console.log(`claim_audit_gate.mjs — scanned ${results.length} answers from ${appendixPath}\n`);

  console.log(
    `BLOCKING (absence/coverage claim present — 100% adversarial audit required before grading): ${blockingFlagged.length}/${results.length}`
  );
  for (const r of blockingFlagged) {
    const classes = [...new Set(r.hits.filter((h) => h.blocking).map((h) => h.claimClass))];
    const snippets = r.hits
      .filter((h) => h.blocking)
      .map((h) => `"${h.snippet}"`)
      .join(", ");
    console.log(`  - ${r.queryId} (${r.stream}) [${classes.join(", ")}] — ${snippets}`);
  }

  console.log(
    `\nINFO-ONLY (precision claim present, non-blocking): ${infoOnlyFlagged.length}/${results.length}`
  );
  for (const r of infoOnlyFlagged) {
    console.log(`  - ${r.queryId} (${r.stream})`);
  }

  console.log(`\nCLEAN (no claim class matched): ${clean.length}/${results.length}`);
  for (const r of clean) {
    console.log(`  - ${r.queryId} (${r.stream})`);
  }

  const s403 = results.find((r) => r.queryId === "S4-03");
  const s405 = results.find((r) => r.queryId === "S4-05");
  const s403Flagged = !!s403 && s403.hits.some((h) => h.blocking);
  const s405Flagged = !!s405 && s405.hits.some((h) => h.blocking);

  console.log(`\n--- Required-catch check ---`);
  console.log(`S4-03 flagged BLOCKING: ${s403Flagged ? "YES" : "NO — GATE FAILURE"}`);
  console.log(`S4-05 flagged BLOCKING: ${s405Flagged ? "YES" : "NO — GATE FAILURE"}`);

  if (!s403Flagged || !s405Flagged) {
    process.exitCode = 1;
  }
}

main();
