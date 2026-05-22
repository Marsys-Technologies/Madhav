#!/usr/bin/env npx tsx
/**
 * bootstrap_classical_texts_jaimini.ts
 * MCP Transformation v3.2-S2 — Jaimini Sutram indexing into rag_chunks.
 *
 * Ingests Jaimini Sutras (B.S. Rao / B.V. Raman edition, 1955) from djvu.txt
 * sourced from archive.org (identifier: Jaiminisutras1955EditionByBSRao).
 *
 * Structure of the source text:
 *   - 2 Adhyayas × 4 Padas each = 8 sections
 *   - Section headers: "ADHYAYA N—PADA M" or "ADHYAYA N-PADA M"
 *   - Sutras: "Su. N. — Sanskrit transliteration." then translation paragraph
 *   - Commentary follows each sutra in prose paragraphs
 *
 * What this script does:
 *   1. Reads jaimini_bsrao_1955_djvu.txt from SOURCE_DATA_DIR.
 *   2. Parses into pseudo-RawVerse records using sutra numbers as verse IDs.
 *      Adhyaya = chapter, Pada = sub-chapter encoded in verse_id.
 *   3. Chunks each sutra into ClassicalChunk objects via chunkVerse().
 *   4. Inserts into rag_chunks (canonical_id = 'classical_texts/JAIMINI') with
 *      ON CONFLICT DO NOTHING (idempotent).
 *   5. Embeds each chunk via Vertex AI text-multilingual-embedding-002 (768 dim).
 *   6. Inserts embeddings into rag_embeddings.
 *
 * Acceptance criteria (from CLAUDECODE_BRIEF_MCPT_V32_S2_v1_0.md):
 *   AC.S2.2: rag_chunks WHERE canonical_id LIKE '%jaimini%' (or metadata->>'work'='JAIMINI') ≥ 1
 *   In practice: all 35 sutras across 8 Adhyaya-Pada sections should be ingested.
 *
 * Prerequisites:
 *   1. Cloud SQL proxy running: cloud-sql-proxy madhav-astrology:asia-south1:amjis-postgres --port=5433
 *   2. ADC auth: gcloud auth application-default login
 *   3. DATABASE_URL env var set.
 *   4. Source file present at SOURCE_DATA_DIR/jaimini_bsrao_1955_djvu.txt.
 *
 * Usage:
 *   DATABASE_URL="postgresql://amjis_app:<pw>@localhost:5433/amjis" \
 *   GCP_PROJECT=madhav-astrology \
 *   npx tsx platform/scripts/bootstrap/bootstrap_classical_texts_jaimini.ts
 *
 *   With --dry-run: parse and report counts without writing to DB.
 */

import { Pool } from 'pg';
import { readFileSync, existsSync } from 'fs';
import { join } from 'path';
import {
  chunkVerse,
  estimateTokens,
  type RawVerse,
  type ClassicalChunk,
} from './lib/classical_text_chunker.js';
import { embedAndPersistChunks } from './lib/classical_text_embedder.js';

// ── Configuration ──────────────────────────────────────────────────────────────

const DATABASE_URL =
  process.env.DATABASE_URL ?? 'postgresql://amjis_app@localhost:5433/amjis';

// Resolve SOURCE_DATA_DIR relative to repo root.
// __dirname = platform/scripts/bootstrap → go up 3 to worktree root.
// The BPHS script uses 5 levels (a known quirk); we use 3 which is correct.
// Override with JAIMINI_SOURCE_DIR env var if needed.
const REPO_ROOT = join(__dirname, '..', '..', '..');
const SOURCE_DATA_DIR =
  process.env.JAIMINI_SOURCE_DIR ??
  join(REPO_ROOT, '00_ARCHITECTURE/SOURCE_DATA/classical_texts/JAIMINI');

const BUILD_TIMESTAMP = new Date()
  .toISOString()
  .slice(0, 16)
  .replace('T', '-')
  .replace(':', '');
const BUILD_ID = `mcpt-v32-jaimini-${BUILD_TIMESTAMP}`;

const MAX_TOKENS_PER_CHUNK = 400;
const SOURCE_FILENAME = 'jaimini_bsrao_1955_djvu.txt';

// ── CLI arguments ──────────────────────────────────────────────────────────────

const args = process.argv.slice(2);
const DRY_RUN = args.includes('--dry-run');

// ── Parser: Jaimini Sutras ─────────────────────────────────────────────────────

/**
 * Parse a block of Jaimini section text into sutra records using a line-based approach.
 *
 * Sutra lines start with "Su. N." or "Su. N .—" at the beginning of the line.
 * Body text follows until the next "Su." line, section break, or "End of" marker.
 */
function parseSutrasFromSectionLines(
  lines: string[],
  adhyaya: number,
  pada: number,
): RawVerse[] {
  const verses: RawVerse[] = [];
  const sutraLinePattern = /^Su\.\s*(\d+)\s*\.?\s*[-—–.]+\s*(.*)/;
  const SOURCE_EDITION = 'B.S. Rao / B.V. Raman, IBH Prakashana 1955 (archive.org Jaiminisutras1955EditionByBSRao)';

  const chapterCode = adhyaya * 10 + pada;

  let currentSutraNum: number | null = null;
  let currentTranslit = '';
  let bodyLines: string[] = [];

  const flushCurrentSutra = () => {
    if (currentSutraNum === null) return;

    const bodyText = bodyLines.join('\n').trim();
    const paragraphs = bodyText
      .split(/\n\s*\n/)
      .map(p => p.replace(/\s+/g, ' ').trim())
      .filter(p => p.length > 20);

    const translationText = paragraphs[0] ?? bodyText.replace(/\s+/g, ' ').trim();
    const commentaryText = paragraphs.slice(1).join(' ').trim();

    if (translationText.length < 20) {
      // Too short — likely OCR noise
      currentSutraNum = null;
      bodyLines = [];
      return;
    }

    const sutraNumPadded = String(currentSutraNum).padStart(3, '0');
    const verseId = `JAIMINI.A${adhyaya}.P${pada}.${sutraNumPadded}`;
    const verseRef = `A${adhyaya}P${pada}.${currentSutraNum}`;

    verses.push({
      work: 'JAIMINI',
      chapter: chapterCode,
      verse_start: currentSutraNum,
      verse_end: currentSutraNum,
      verse_ref: verseRef,
      verse_id: verseId,
      sanskrit_text: currentTranslit || undefined,
      translation_text: translationText,
      commentary_text: commentaryText || undefined,
      source_edition: SOURCE_EDITION,
    });

    currentSutraNum = null;
    bodyLines = [];
    currentTranslit = '';
  };

  for (const rawLine of lines) {
    const line = rawLine.trim();

    // Check for sutra marker at line start
    const sutraMatch = sutraLinePattern.exec(line);
    if (sutraMatch) {
      flushCurrentSutra();
      currentSutraNum = parseInt(sutraMatch[1], 10);
      currentTranslit = (sutraMatch[2] ?? '').trim();
      bodyLines = [];
      continue;
    }

    // Section break markers
    if (line.startsWith('End of') || /^ADHYAYA\s*\d+/.test(line)) {
      flushCurrentSutra();
      continue;
    }

    // Accumulate body lines for current sutra
    if (currentSutraNum !== null) {
      bodyLines.push(rawLine);
    }
  }

  flushCurrentSutra();
  return verses;
}

/**
 * Parse Jaimini Sutras djvu.txt into RawVerse records.
 *
 * Structure:
 *   - Adhyaya/Pada headers: "ADHYAYA N—PADA M" (or with hyphen variants)
 *   - Sutra markers: "Su. N. —" or "Su. N .—" at line start
 *   - Sanskrit transliteration follows on same line after the dash
 *   - English translation paragraph follows until next sutra or section break
 *
 * verse_id format: JAIMINI.A{adhyaya}.P{pada}.{sutra_num:03d}
 * work: 'JAIMINI'
 * chapter: adhyaya * 10 + pada (e.g. adhyaya=1, pada=2 → chapter=12)
 */
function parseJaiminiDjvuText(text: string): RawVerse[] {
  const lines = text.split('\n');

  // Find all section header line indices
  const sectionHeaderPattern = /^ADHYAYA\s*(\d+)\s*[-—–]+\s*PADA\s*(\d+)\b/;

  interface SectionHeader {
    adhyaya: number;
    pada: number;
    lineIdx: number;
  }

  const sectionHeaders: SectionHeader[] = [];
  for (let i = 0; i < lines.length; i++) {
    const m = sectionHeaderPattern.exec(lines[i].trim());
    if (m) {
      sectionHeaders.push({
        adhyaya: parseInt(m[1], 10),
        pada: parseInt(m[2], 10),
        lineIdx: i,
      });
    }
  }

  if (sectionHeaders.length === 0) {
    console.warn('[WARN] No ADHYAYA-PADA section headers found. Attempting global fallback parse.');
    return parseJaiminiGlobalLineBased(lines);
  }

  console.log(`  Found ${sectionHeaders.length} Adhyaya-Pada sections`);

  const allVerses: RawVerse[] = [];

  for (let i = 0; i < sectionHeaders.length; i++) {
    const header = sectionHeaders[i];
    const startLine = header.lineIdx + 1; // lines after the header
    const endLine = i + 1 < sectionHeaders.length ? sectionHeaders[i + 1].lineIdx : lines.length;

    const sectionLines = lines.slice(startLine, endLine);
    const sectionVerses = parseSutrasFromSectionLines(sectionLines, header.adhyaya, header.pada);
    allVerses.push(...sectionVerses);
  }

  return allVerses;
}

/**
 * Fallback: parse sutras globally (no section awareness) if section headers not found.
 */
function parseJaiminiGlobalLineBased(lines: string[]): RawVerse[] {
  const sutraLinePattern = /^Su\.\s*(\d+)\s*\.?\s*[-—–.]+\s*(.*)/;
  const SOURCE_EDITION = 'B.S. Rao / B.V. Raman, IBH Prakashana 1955 (archive.org Jaiminisutras1955EditionByBSRao)';
  const verses: RawVerse[] = [];

  let currentSutraNum: number | null = null;
  let currentTranslit = '';
  let bodyLines: string[] = [];

  const flushCurrentSutra = () => {
    if (currentSutraNum === null) return;
    const bodyText = bodyLines.join('\n').trim();
    const paragraphs = bodyText
      .split(/\n\s*\n/)
      .map(p => p.replace(/\s+/g, ' ').trim())
      .filter(p => p.length > 20);
    const translationText = paragraphs[0] ?? bodyText.replace(/\s+/g, ' ').trim();
    if (translationText.length < 20) {
      currentSutraNum = null;
      bodyLines = [];
      return;
    }
    const sutraNumPadded = String(currentSutraNum).padStart(3, '0');
    const verseId = `JAIMINI.G.${sutraNumPadded}`;
    verses.push({
      work: 'JAIMINI',
      chapter: 1,
      verse_start: currentSutraNum,
      verse_end: currentSutraNum,
      verse_ref: `G.${currentSutraNum}`,
      verse_id: verseId,
      sanskrit_text: currentTranslit || undefined,
      translation_text: translationText,
      commentary_text: paragraphs.slice(1).join(' ').trim() || undefined,
      source_edition: SOURCE_EDITION,
    });
    currentSutraNum = null;
    bodyLines = [];
    currentTranslit = '';
  };

  for (const rawLine of lines) {
    const line = rawLine.trim();
    const sutraMatch = sutraLinePattern.exec(line);
    if (sutraMatch) {
      flushCurrentSutra();
      currentSutraNum = parseInt(sutraMatch[1], 10);
      currentTranslit = (sutraMatch[2] ?? '').trim();
      bodyLines = [];
    } else if (currentSutraNum !== null) {
      bodyLines.push(rawLine);
    }
  }
  flushCurrentSutra();
  return verses;
}

// ── Main ───────────────────────────────────────────────────────────────────────

async function main(): Promise<void> {
  console.log('='.repeat(70));
  console.log('MARSYS-JIS MCP v3.2-S2 — Jaimini Sutram Ingestion Bootstrap');
  console.log(`build_id: ${BUILD_ID}`);
  console.log(`source_dir: ${SOURCE_DATA_DIR}`);
  console.log(`dry_run: ${DRY_RUN}`);
  console.log('='.repeat(70));

  // ── 1. Load source file ────────────────────────────────────────────────────

  console.log('\n[1] Loading source file...');
  const filepath = join(SOURCE_DATA_DIR, SOURCE_FILENAME);

  if (!existsSync(filepath)) {
    console.error(`MISSING_SOURCE_DATA: ${filepath}`);
    console.error('Download from: https://archive.org/download/Jaiminisutras1955EditionByBSRao/');
    process.exit(2);
  }

  const text = readFileSync(filepath, 'utf-8');
  console.log(`  Loaded ${SOURCE_FILENAME}: ${text.length.toLocaleString()} chars`);

  // ── 2. Parse sutras ────────────────────────────────────────────────────────

  console.log('\n[2] Parsing Jaimini sutra records...');
  const allVerses = parseJaiminiDjvuText(text);
  console.log(`  Total sutras parsed: ${allVerses.length}`);

  if (allVerses.length === 0) {
    console.error('PARSE_FAILURE: No sutras extracted. OCR may be too degraded.');
    process.exit(3);
  }

  // Section distribution report
  const sectionMap = new Map<number, number>();
  for (const v of allVerses) {
    sectionMap.set(v.chapter, (sectionMap.get(v.chapter) ?? 0) + 1);
  }
  console.log('\n  Sutras per Adhyaya-Pada section:');
  for (const [chCode, count] of [...sectionMap.entries()].sort((a, b) => a[0] - b[0])) {
    const adhyaya = Math.floor(chCode / 10);
    const pada = chCode % 10;
    console.log(`    Adhyaya ${adhyaya} Pada ${pada}: ${count} sutras`);
  }

  // Quality check
  const shortTranslations = allVerses.filter(v => v.translation_text.length < 40).length;
  if (shortTranslations > 0) {
    console.log(`  [INFO] ${shortTranslations} sutras have short translations (< 40 chars) — OCR artifact risk`);
  }

  // ── 3. Chunk verses ────────────────────────────────────────────────────────

  console.log('\n[3] Chunking sutras...');
  const allChunks: ClassicalChunk[] = allVerses.flatMap(v =>
    chunkVerse(v, MAX_TOKENS_PER_CHUNK),
  );
  console.log(`  Total chunks: ${allChunks.length}`);

  const tokenStats = allChunks.map(c => c.token_count);
  if (tokenStats.length > 0) {
    const avgTokens = tokenStats.reduce((a, b) => a + b, 0) / tokenStats.length;
    console.log(`  Token count: avg=${avgTokens.toFixed(0)} min=${Math.min(...tokenStats)} max=${Math.max(...tokenStats)}`);
  }

  // Sample output
  if (allChunks.length > 0) {
    console.log('\n  Sample chunks:');
    allChunks.slice(0, 3).forEach(c => {
      console.log(`    ${c.chunk_id} [${c.token_count} tok]: ${c.content.slice(0, 120)}...`);
    });
  }

  if (DRY_RUN) {
    console.log('\n[DRY-RUN] Not writing to DB.');
    console.log('[DRY-RUN] Complete.');
    return;
  }

  // ── 4. Connect and persist ─────────────────────────────────────────────────

  console.log('\n[4] Connecting to database...');
  const pool = new Pool({ connectionString: DATABASE_URL });

  try {
    const { rows } = await pool.query('SELECT count(*) FROM rag_chunks');
    console.log(`  Connected. Current rag_chunks rows: ${rows[0].count}`);

    const existing = await pool.query(
      "SELECT count(*) FROM rag_chunks WHERE canonical_id = 'classical_texts/JAIMINI'",
    );
    console.log(`  Existing JAIMINI rag_chunks: ${existing.rows[0].count}`);

    // ── 5. Embed and insert chunks ─────────────────────────────────────────

    console.log(`\n[5] Embedding and inserting ${allChunks.length} chunks (build_id: ${BUILD_ID})...`);
    const results = await embedAndPersistChunks(pool, allChunks, BUILD_ID, {
      batchSize: 20,
      batchDelayMs: 300,
      verbose: true,
    });

    const inserted = results.filter(r => r.inserted).length;
    const embedded = results.filter(r => r.embedded).length;
    const errors = results.filter(r => r.error).length;

    console.log('\n[5] Summary:');
    console.log(`  Chunks processed:  ${results.length}`);
    console.log(`  Newly inserted:    ${inserted}`);
    console.log(`  Already existed:   ${results.length - inserted}`);
    console.log(`  Embeddings:        ${embedded}`);
    console.log(`  Errors:            ${errors}`);

    // ── 6. Final verification ──────────────────────────────────────────────

    console.log('\n[6] Verification queries...');
    const finalCount = await pool.query(
      "SELECT count(*) FROM rag_chunks WHERE canonical_id LIKE 'classical_texts/JAIMINI%'",
    );
    const finalJaimini = parseInt(finalCount.rows[0].count, 10);
    console.log(`  rag_chunks WHERE canonical_id LIKE 'classical_texts/JAIMINI%': ${finalJaimini}`);

    // Also check by metadata->>'work' as fallback
    const metaCount = await pool.query(
      "SELECT count(*) FROM rag_chunks WHERE metadata->>'work' = 'JAIMINI'",
    );
    console.log(`  rag_chunks WHERE metadata->>'work' = 'JAIMINI': ${metaCount.rows[0].count}`);

    console.log('\n[6] Acceptance criteria check:');
    const acPass = finalJaimini >= 1;
    console.log(`  AC.S2.2 (jaimini chunks ≥ 1): ${acPass ? 'PASS' : 'FAIL'} (${finalJaimini})`);
    console.log(`  AC.S2.4 (build_manifests): SKIPPED — asset_id column does not exist (per brief)`);

    if (errors > 0) {
      console.warn(`\n[WARN] ${errors} embedding errors. Re-run to retry.`);
    }

    console.log('\n' + '='.repeat(70));
    console.log('Jaimini Sutram ingestion complete.');
    console.log(`build_id: ${BUILD_ID}`);
    console.log(`rag_chunks inserted: ${finalJaimini}`);
    console.log('='.repeat(70));
  } finally {
    await pool.end();
  }
}

main().catch(err => {
  console.error('Fatal error:', err);
  process.exit(1);
});
