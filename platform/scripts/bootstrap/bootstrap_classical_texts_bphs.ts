#!/usr/bin/env npx tsx
/**
 * bootstrap_classical_texts_bphs.ts
 * MCP Transformation v3.2-S1 — BPHS indexing into rag_chunks.
 *
 * Ingests Brihat Parashara Hora Shastra from djvu.txt source files
 * (R. Santhanam translation, sourced from archive.org BPHSEnglish).
 *
 * What this script does:
 *   1. Reads bphs_vol1_rsanthanam_djvu.txt and bphs_vol2_rsanthanam_djvu.txt
 *      from SOURCE_DATA_DIR (default: 00_ARCHITECTURE/SOURCE_DATA/classical_texts/BPHS/).
 *   2. Parses each file into RawVerse records using parseBphsDjvuText().
 *   3. Deduplicates by verse_id (last occurrence wins).
 *   4. Chunks each verse into ClassicalChunk objects via chunkVerse().
 *   5. Inserts into rag_chunks (canonical_id = 'classical_texts/BPHS') with
 *      ON CONFLICT DO NOTHING (idempotent).
 *   6. Embeds each chunk via Vertex AI text-multilingual-embedding-002 (768 dim).
 *   7. Inserts embeddings into rag_embeddings.
 *
 * Acceptance criteria (from CLAUDECODE_BRIEF_MCPT_V32_S1_v1_0.md):
 *   AC.S1.1: classical_texts WHERE work='BPHS' returns ≥ 1000
 *            NOTE: The existing classical_texts schema has one row per work (text_key='bphs').
 *            Migration 072 adds the `work` computed column. The ≥1000 row count
 *            is satisfied by rag_chunks (AC.S1.3), not classical_texts.
 *   AC.S1.3: rag_chunks WHERE canonical_id LIKE 'classical_texts/BPHS%' ≥ 1000.
 *
 * Prerequisites:
 *   1. Cloud SQL proxy running: cloud-sql-proxy madhav-astrology:asia-south1:amjis-postgres --port=5433
 *   2. ADC auth: gcloud auth application-default login
 *   3. DATABASE_URL env var set.
 *   4. Source files present in SOURCE_DATA_DIR.
 *
 * Usage:
 *   DATABASE_URL="postgresql://amjis_app:<pw>@localhost:5433/amjis" \
 *   GCP_PROJECT=madhav-astrology \
 *   npx tsx platform/scripts/bootstrap/bootstrap_classical_texts_bphs.ts
 *
 *   With --dry-run: parse and report counts without writing to DB.
 *   With --limit-chapters N: only ingest first N chapters (for smoke testing).
 */

import { Pool } from 'pg';
import { readFileSync, existsSync } from 'fs';
import { join } from 'path';
import {
  parseBphsDjvuText,
  deduplicateVerses,
  chunkVerse,
  type RawVerse,
  type ClassicalChunk,
} from './lib/classical_text_chunker';
import { embedAndPersistChunks } from './lib/classical_text_embedder';

// ── Configuration ──────────────────────────────────────────────────────────────

const DATABASE_URL =
  process.env.DATABASE_URL ?? 'postgresql://amjis_app@localhost:5433/amjis';

// Resolve SOURCE_DATA_DIR relative to repo root (two levels up from platform/scripts/bootstrap/)
const REPO_ROOT = join(__dirname, '..', '..', '..', '..', '..');
const SOURCE_DATA_DIR =
  process.env.BPHS_SOURCE_DIR ??
  join(REPO_ROOT, '00_ARCHITECTURE/SOURCE_DATA/classical_texts/BPHS');

const BUILD_TIMESTAMP = new Date()
  .toISOString()
  .slice(0, 16)
  .replace('T', '-')
  .replace(':', '');
const BUILD_ID = `mcpt-v32-bphs-${BUILD_TIMESTAMP}`;

const MAX_TOKENS_PER_CHUNK = 400;

// ── CLI arguments ──────────────────────────────────────────────────────────────

const args = process.argv.slice(2);
const DRY_RUN = args.includes('--dry-run');
const LIMIT_IDX = args.findIndex(a => a === '--limit-chapters');
const LIMIT_CHAPTERS: number | null =
  LIMIT_IDX >= 0 ? parseInt(args[LIMIT_IDX + 1], 10) : null;

// ── Helpers ────────────────────────────────────────────────────────────────────

function loadSourceFile(filename: string): { text: string; path: string } | null {
  const filepath = join(SOURCE_DATA_DIR, filename);
  if (!existsSync(filepath)) {
    console.warn(`  [WARN] Source file not found: ${filepath}`);
    return null;
  }
  const text = readFileSync(filepath, 'utf-8');
  console.log(`  Loaded ${filename}: ${text.length.toLocaleString()} chars`);
  return { text, path: filepath };
}

// ── Main ───────────────────────────────────────────────────────────────────────

async function main(): Promise<void> {
  console.log('='.repeat(70));
  console.log('MARSYS-JIS MCP v3.2-S1 — BPHS Ingestion Bootstrap');
  console.log(`build_id: ${BUILD_ID}`);
  console.log(`source_dir: ${SOURCE_DATA_DIR}`);
  console.log(`dry_run: ${DRY_RUN}`);
  if (LIMIT_CHAPTERS) console.log(`limit_chapters: ${LIMIT_CHAPTERS}`);
  console.log('='.repeat(70));

  // ── 1. Load source files ───────────────────────────────────────────────────

  console.log('\n[1] Loading source files...');
  const vol1 = loadSourceFile('bphs_vol1_rsanthanam_djvu.txt');
  const vol2 = loadSourceFile('bphs_vol2_rsanthanam_djvu.txt');

  const missing: string[] = [];
  if (!vol1) missing.push('bphs_vol1_rsanthanam_djvu.txt');
  if (!vol2) missing.push('bphs_vol2_rsanthanam_djvu.txt');

  if (missing.length === 2) {
    console.error('MISSING_SOURCE_DATA: Neither Vol. 1 nor Vol. 2 found.');
    console.error(`Missing files: ${missing.join(', ')}`);
    process.exit(2);
  }
  if (missing.length === 1) {
    console.warn(`[WARN] Partial source: ${missing[0]} not found. Continuing with available volume(s).`);
  }

  // ── 2. Parse verses ────────────────────────────────────────────────────────

  console.log('\n[2] Parsing verse records...');
  let allVerses: RawVerse[] = [];

  if (vol1) {
    const verses1 = parseBphsDjvuText(vol1.text, 'Vol. 1');
    console.log(`  Vol. 1: ${verses1.length} verse records`);
    allVerses.push(...verses1);
  }
  if (vol2) {
    const verses2 = parseBphsDjvuText(vol2.text, 'Vol. 2');
    console.log(`  Vol. 2: ${verses2.length} verse records`);
    allVerses.push(...verses2);
  }

  // Deduplicate by verse_id
  allVerses = deduplicateVerses(allVerses);
  console.log(`  After deduplication: ${allVerses.length} unique verse records`);

  // Filter by chapter limit if specified
  if (LIMIT_CHAPTERS !== null) {
    allVerses = allVerses.filter(v => v.chapter <= LIMIT_CHAPTERS);
    console.log(`  After chapter limit (≤${LIMIT_CHAPTERS}): ${allVerses.length} verses`);
  }

  // Filter out OCR noise: verses with very short translation text (< 40 chars = OCR artifacts)
  const beforeNoise = allVerses.length;
  allVerses = allVerses.filter(v => v.translation_text.trim().length >= 40);
  const noiseFiltered = beforeNoise - allVerses.length;
  if (noiseFiltered > 0) {
    console.log(`  Filtered ${noiseFiltered} OCR noise verses (< 40 chars); remaining: ${allVerses.length}`);
  }

  // Chapter distribution report
  const chapterNums = [...new Set(allVerses.map(v => v.chapter))].sort((a, b) => a - b);
  console.log(`\n  Chapters indexed: ${chapterNums.length} (${chapterNums[0]}–${chapterNums[chapterNums.length - 1]})`);
  console.log(`  Chapter list: ${chapterNums.join(', ')}`);

  if (allVerses.length < 1000 && !LIMIT_CHAPTERS) {
    console.warn(`[WARN] Only ${allVerses.length} verses found; AC.S1.3 requires ≥1000 in rag_chunks.`);
  }

  // ── 3. Chunk verses ────────────────────────────────────────────────────────

  console.log('\n[3] Chunking verses...');
  const allChunks: ClassicalChunk[] = allVerses.flatMap(v =>
    chunkVerse(v, MAX_TOKENS_PER_CHUNK),
  );
  console.log(`  Total chunks: ${allChunks.length}`);

  const tokenStats = allChunks.map(c => c.token_count);
  const avgTokens = tokenStats.reduce((a, b) => a + b, 0) / tokenStats.length;
  console.log(`  Token count: avg=${avgTokens.toFixed(0)} min=${Math.min(...tokenStats)} max=${Math.max(...tokenStats)}`);

  if (DRY_RUN) {
    console.log('\n[DRY-RUN] Not writing to DB. Sample chunks:');
    allChunks.slice(0, 3).forEach(c => {
      console.log(`  ${c.chunk_id} [${c.token_count} tok]: ${c.content.slice(0, 120)}...`);
    });
    console.log('\n[DRY-RUN] Complete.');
    return;
  }

  // ── 4. Connect and persist ─────────────────────────────────────────────────

  console.log('\n[4] Connecting to database...');
  const pool = new Pool({ connectionString: DATABASE_URL });

  try {
    // Verify connection
    const { rows } = await pool.query('SELECT count(*) FROM rag_chunks');
    console.log(`  Connected. Current rag_chunks rows: ${rows[0].count}`);

    // Check existing BPHS chunks
    const existing = await pool.query(
      "SELECT count(*) FROM rag_chunks WHERE canonical_id = 'classical_texts/BPHS'",
    );
    console.log(`  Existing BPHS rag_chunks: ${existing.rows[0].count}`);

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
    console.log(`  Chunks processed: ${results.length}`);
    console.log(`  Newly inserted:   ${inserted}`);
    console.log(`  Already existed:  ${results.length - inserted}`);
    console.log(`  Embeddings:       ${embedded}`);
    console.log(`  Errors:           ${errors}`);

    // ── 6. Final verification ──────────────────────────────────────────────

    console.log('\n[6] Verification queries...');
    const finalCount = await pool.query(
      "SELECT count(*) FROM rag_chunks WHERE canonical_id LIKE 'classical_texts/BPHS%'",
    );
    const finalBphs = parseInt(finalCount.rows[0].count, 10);
    console.log(`  rag_chunks WHERE canonical_id LIKE 'classical_texts/BPHS%': ${finalBphs}`);

    const chapterCount = await pool.query(
      `SELECT count(DISTINCT (metadata->>'chapter')::int) as distinct_chapters
       FROM rag_chunks
       WHERE canonical_id LIKE 'classical_texts/BPHS%'`,
    );
    const distinctChapters = chapterCount.rows[0].distinct_chapters;
    console.log(`  Distinct chapters in rag_chunks: ${distinctChapters}`);

    const ctCount = await pool.query(
      "SELECT count(*) FROM classical_texts WHERE work='BPHS'",
    );
    console.log(`  classical_texts WHERE work='BPHS': ${ctCount.rows[0].count} (expected 1 — one-row-per-work schema)`);

    console.log('\n[6] Acceptance criteria check:');
    console.log(`  AC.S1.1 (classical_texts WHERE work='BPHS' ≥ 1000): SCHEMA_MISMATCH — 1 row (one-per-work schema)`);
    console.log(`           Real verse count: ${finalBphs} in rag_chunks`);
    console.log(`  AC.S1.3 (rag_chunks 'classical_texts/BPHS%' ≥ 1000): ${finalBphs >= 1000 ? 'PASS' : 'FAIL'} (${finalBphs})`);
    console.log(`  AC.S1.4 (build_manifests): SKIPPED — asset_id column does not exist`);

    if (errors > 0) {
      console.warn(`\n[WARN] ${errors} embedding errors. Re-run to retry failed chunks.`);
    }

    console.log('\n' + '='.repeat(70));
    console.log('BPHS ingestion complete.');
    console.log(`build_id: ${BUILD_ID}`);
    console.log('='.repeat(70));
  } finally {
    await pool.end();
  }
}

main().catch(err => {
  console.error('Fatal error:', err);
  process.exit(1);
});
