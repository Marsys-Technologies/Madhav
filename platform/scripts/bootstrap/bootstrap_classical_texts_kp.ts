#!/usr/bin/env npx tsx
/**
 * bootstrap_classical_texts_kp.ts
 * MCP Transformation v3.2-S2 — KP Reader (Vols 1–4) indexing into rag_chunks.
 *
 * Ingests Krishnamurti Padhdhati Reader Volumes 1–4 from djvu.txt files
 * sourced from archive.org (identifier: kp-readers).
 *
 * Structure of the source texts (OCR djvu.txt):
 *   - KP Reader is topic/concept-based rather than verse/sutra based.
 *   - Section headers are ALL-CAPS lines (potential topic boundaries).
 *   - Content is prose paragraphs organized by topic.
 *   - Each "chunk" is one logical topic section (prose passage).
 *
 * Since KP Reader lacks verse/sutra numbering, we use paragraph-window chunking:
 *   - Identify paragraph blocks (separated by blank lines).
 *   - Group consecutive paragraphs into windows of ~300 tokens.
 *   - Assign sequential chunk IDs per volume: KP_VOL1.001, KP_VOL1.002, …
 *
 * What this script does:
 *   1. Reads kp_reader_vol{1-4}_djvu.txt from SOURCE_DATA_DIR.
 *   2. Parses each volume into paragraph windows using sliding windows.
 *   3. Creates RawVerse-compatible records (work=KP_VOL1 etc).
 *   4. Chunks and inserts into rag_chunks (canonical_id='classical_texts/KP_VOLn').
 *   5. Embeds via Vertex AI text-multilingual-embedding-002 (768 dim).
 *
 * Acceptance criteria (from CLAUDECODE_BRIEF_MCPT_V32_S2_v1_0.md):
 *   AC.S2.3: rag_chunks WHERE canonical_id LIKE '%kp%' (or metadata->>'work' LIKE 'KP_%') ≥ 1
 *
 * Prerequisites:
 *   1. Cloud SQL proxy running: cloud-sql-proxy madhav-astrology:asia-south1:amjis-postgres --port=5433
 *   2. ADC auth: gcloud auth application-default login
 *   3. DATABASE_URL env var set.
 *   4. Source files in SOURCE_DATA_DIR/kp_reader_vol{1-4}_djvu.txt.
 *
 * Usage:
 *   DATABASE_URL="postgresql://amjis_app:<pw>@localhost:5433/amjis" \
 *   GCP_PROJECT=madhav-astrology \
 *   npx tsx platform/scripts/bootstrap/bootstrap_classical_texts_kp.ts
 *
 *   With --dry-run: parse and report without writing to DB.
 *   With --volumes 1,2: only process specified volumes.
 */

import { Pool } from 'pg';
import { readFileSync, existsSync } from 'fs';
import { join } from 'path';
import {
  estimateTokens,
  type RawVerse,
  type ClassicalChunk,
  chunkVerse,
} from './lib/classical_text_chunker.js';
import { embedAndPersistChunks } from './lib/classical_text_embedder.js';

// ── Configuration ──────────────────────────────────────────────────────────────

const DATABASE_URL =
  process.env.DATABASE_URL ?? 'postgresql://amjis_app@localhost:5433/amjis';

// Resolve SOURCE_DATA_DIR relative to repo root.
// __dirname = platform/scripts/bootstrap → go up 3 to worktree root.
// Override with KP_SOURCE_DIR env var if needed.
const REPO_ROOT = join(__dirname, '..', '..', '..');
const SOURCE_DATA_DIR =
  process.env.KP_SOURCE_DIR ??
  join(REPO_ROOT, '00_ARCHITECTURE/SOURCE_DATA/classical_texts/KP');

const BUILD_TIMESTAMP = new Date()
  .toISOString()
  .slice(0, 16)
  .replace('T', '-')
  .replace(':', '');
const BUILD_ID = `mcpt-v32-kp-${BUILD_TIMESTAMP}`;

const TARGET_WINDOW_TOKENS = 300; // target tokens per paragraph window
const MIN_PARA_LENGTH = 40; // filter OCR noise paragraphs shorter than this

// ── CLI arguments ──────────────────────────────────────────────────────────────

const args = process.argv.slice(2);
const DRY_RUN = args.includes('--dry-run');

// --volumes 1,2,3,4 — which volumes to process (default: all)
const VOL_IDX = args.findIndex(a => a === '--volumes');
const VOLUMES: number[] =
  VOL_IDX >= 0
    ? args[VOL_IDX + 1].split(',').map(v => parseInt(v.trim(), 10))
    : [1, 2, 3, 4];

// ── KP Volume metadata ─────────────────────────────────────────────────────────

interface KPVolumeSpec {
  vol: number;
  workKey: string;
  title: string;
  filename: string;
  sourceEdition: string;
}

const KP_VOLUMES: KPVolumeSpec[] = [
  {
    vol: 1,
    workKey: 'KP_VOL1',
    title: 'Casting the Horoscope',
    filename: 'kp_reader_vol1_djvu.txt',
    sourceEdition: 'K.S. Krishnamurti, KP Reader Vol.1 (archive.org kp-readers)',
  },
  {
    vol: 2,
    workKey: 'KP_VOL2',
    title: 'Fundamental Principles of Astrology',
    filename: 'kp_reader_vol2_djvu.txt',
    sourceEdition: 'K.S. Krishnamurti, KP Reader Vol.2 (archive.org kp-readers)',
  },
  {
    vol: 3,
    workKey: 'KP_VOL3',
    title: 'Predictive Stellar Astrology',
    filename: 'kp_reader_vol3_djvu.txt',
    sourceEdition: 'K.S. Krishnamurti, KP Reader Vol.3 (archive.org kp-readers)',
  },
  {
    vol: 4,
    workKey: 'KP_VOL4',
    title: 'Marriage, Married Life & Children',
    filename: 'kp_reader_vol4_djvu.txt',
    sourceEdition: 'K.S. Krishnamurti, KP Reader Vol.4 (archive.org kp-readers)',
  },
];

// ── Parser: KP Reader paragraph-window chunking ───────────────────────────────

/**
 * Strip OCR page-header noise lines from KP Reader text.
 * Page headers in KP djvu.txt are typically short repeated lines like
 * "KRISHNAMURTI PADHDHATI" or page numbers.
 */
function stripKPPageNoise(text: string): string {
  const lines = text.split('\n');
  const filtered: string[] = [];

  // Track repeated short lines (page headers)
  const lineFrequency = new Map<string, number>();
  for (const line of lines) {
    const trimmed = line.trim();
    if (trimmed.length > 0 && trimmed.length < 60) {
      lineFrequency.set(trimmed, (lineFrequency.get(trimmed) ?? 0) + 1);
    }
  }

  // Lines appearing more than 5 times and < 60 chars are likely page headers
  for (const line of lines) {
    const trimmed = line.trim();
    const freq = lineFrequency.get(trimmed) ?? 0;
    if (freq > 5 && trimmed.length < 60 && trimmed.length > 0) {
      continue; // skip page noise
    }
    filtered.push(line);
  }

  return filtered.join('\n');
}

/**
 * Parse KP Reader djvu.txt into paragraph-window RawVerse records.
 *
 * Since KP Reader is prose (not sutras), we:
 * 1. Split by blank lines into paragraphs.
 * 2. Filter noise paragraphs (< MIN_PARA_LENGTH chars).
 * 3. Group consecutive paragraphs into windows of ~TARGET_WINDOW_TOKENS.
 * 4. Each window becomes one RawVerse-compatible record.
 */
function parseKPVolume(text: string, spec: KPVolumeSpec): RawVerse[] {
  const verses: RawVerse[] = [];

  // Strip page noise
  const cleanText = stripKPPageNoise(text);

  // Split into paragraphs
  const rawParagraphs = cleanText
    .split(/\n\s*\n+/)
    .map(p => p.replace(/\s+/g, ' ').trim())
    .filter(p => p.length >= MIN_PARA_LENGTH);

  if (rawParagraphs.length === 0) {
    console.warn(`  [WARN] No paragraphs extracted from ${spec.filename}`);
    return [];
  }

  // Group paragraphs into windows of ~TARGET_WINDOW_TOKENS
  let windowIdx = 0;
  let currentWindow: string[] = [];
  let currentTokens = 0;

  for (const para of rawParagraphs) {
    const paraTokens = estimateTokens(para);

    // If adding this paragraph would exceed target, flush current window
    if (currentTokens + paraTokens > TARGET_WINDOW_TOKENS && currentWindow.length > 0) {
      windowIdx++;
      const windowText = currentWindow.join(' ');
      const windowNumPadded = String(windowIdx).padStart(4, '0');
      const verseId = `${spec.workKey}.${windowNumPadded}`;

      verses.push({
        work: spec.workKey,
        chapter: windowIdx,
        verse_start: windowIdx,
        verse_end: windowIdx,
        verse_ref: `${spec.workKey}.${windowIdx}`,
        verse_id: verseId,
        translation_text: windowText,
        source_edition: spec.sourceEdition,
      });

      currentWindow = [para];
      currentTokens = paraTokens;
    } else {
      currentWindow.push(para);
      currentTokens += paraTokens;
    }
  }

  // Flush final window
  if (currentWindow.length > 0) {
    windowIdx++;
    const windowText = currentWindow.join(' ');
    const windowNumPadded = String(windowIdx).padStart(4, '0');
    const verseId = `${spec.workKey}.${windowNumPadded}`;

    verses.push({
      work: spec.workKey,
      chapter: windowIdx,
      verse_start: windowIdx,
      verse_end: windowIdx,
      verse_ref: `${spec.workKey}.${windowIdx}`,
      verse_id: verseId,
      translation_text: windowText,
      source_edition: spec.sourceEdition,
    });
  }

  return verses;
}

// ── Main ───────────────────────────────────────────────────────────────────────

async function main(): Promise<void> {
  console.log('='.repeat(70));
  console.log('MARSYS-JIS MCP v3.2-S2 — KP Reader Ingestion Bootstrap');
  console.log(`build_id: ${BUILD_ID}`);
  console.log(`source_dir: ${SOURCE_DATA_DIR}`);
  console.log(`volumes: ${VOLUMES.join(', ')}`);
  console.log(`dry_run: ${DRY_RUN}`);
  console.log('='.repeat(70));

  // ── 1. Load and parse all volumes ─────────────────────────────────────────

  console.log('\n[1] Loading and parsing KP Reader volumes...');

  const allChunks: ClassicalChunk[] = [];
  const volumeStats: Array<{ vol: number; paragraphs: number; chunks: number }> = [];

  for (const spec of KP_VOLUMES.filter(s => VOLUMES.includes(s.vol))) {
    const filepath = join(SOURCE_DATA_DIR, spec.filename);

    if (!existsSync(filepath)) {
      console.warn(`  [WARN] Missing: ${filepath} — skipping Vol ${spec.vol}`);
      continue;
    }

    const text = readFileSync(filepath, 'utf-8');
    console.log(`\n  Vol ${spec.vol} (${spec.title}): ${text.length.toLocaleString()} chars`);

    // Parse into paragraph windows (RawVerse-like records)
    const verses = parseKPVolume(text, spec);
    console.log(`    Paragraph windows: ${verses.length}`);

    if (verses.length === 0) {
      console.warn(`    [WARN] No content extracted from Vol ${spec.vol}`);
      continue;
    }

    // Chunk (paragraph windows are already ~target size, but chunker handles overflow)
    const chunks = verses.flatMap(v => chunkVerse(v, 400));
    console.log(`    Chunks: ${chunks.length}`);

    // Report token stats
    const tokenStats = chunks.map(c => c.token_count);
    const avg = tokenStats.reduce((a, b) => a + b, 0) / tokenStats.length;
    console.log(`    Token avg=${avg.toFixed(0)} min=${Math.min(...tokenStats)} max=${Math.max(...tokenStats)}`);

    // Sample
    if (chunks.length > 0) {
      console.log(`    Sample: ${chunks[0].chunk_id}: ${chunks[0].content.slice(0, 100)}...`);
    }

    allChunks.push(...chunks);
    volumeStats.push({ vol: spec.vol, paragraphs: verses.length, chunks: chunks.length });
  }

  console.log('\n[1] Summary:');
  for (const s of volumeStats) {
    console.log(`  Vol ${s.vol}: ${s.paragraphs} windows → ${s.chunks} chunks`);
  }
  console.log(`  Total chunks: ${allChunks.length}`);

  if (allChunks.length === 0) {
    console.error('NO_CHUNKS: No content extracted from any volume.');
    process.exit(3);
  }

  if (DRY_RUN) {
    console.log('\n[DRY-RUN] Not writing to DB.');
    console.log('[DRY-RUN] Complete.');
    return;
  }

  // ── 2. Connect to DB ───────────────────────────────────────────────────────

  console.log('\n[2] Connecting to database...');
  const pool = new Pool({ connectionString: DATABASE_URL });

  try {
    const { rows } = await pool.query('SELECT count(*) FROM rag_chunks');
    console.log(`  Connected. Current rag_chunks rows: ${rows[0].count}`);

    const existingKP = await pool.query(
      "SELECT count(*) FROM rag_chunks WHERE canonical_id LIKE 'classical_texts/KP_%'",
    );
    console.log(`  Existing KP rag_chunks: ${existingKP.rows[0].count}`);

    // ── 3. Embed and insert ────────────────────────────────────────────────

    console.log(`\n[3] Embedding and inserting ${allChunks.length} chunks (build_id: ${BUILD_ID})...`);
    const results = await embedAndPersistChunks(pool, allChunks, BUILD_ID, {
      batchSize: 20,
      batchDelayMs: 300,
      verbose: true,
    });

    const inserted = results.filter(r => r.inserted).length;
    const embedded = results.filter(r => r.embedded).length;
    const errors = results.filter(r => r.error).length;

    console.log('\n[3] Summary:');
    console.log(`  Chunks processed:  ${results.length}`);
    console.log(`  Newly inserted:    ${inserted}`);
    console.log(`  Already existed:   ${results.length - inserted}`);
    console.log(`  Embeddings:        ${embedded}`);
    console.log(`  Errors:            ${errors}`);

    // ── 4. Final verification ──────────────────────────────────────────────

    console.log('\n[4] Verification queries...');
    const finalCount = await pool.query(
      "SELECT count(*) FROM rag_chunks WHERE canonical_id LIKE 'classical_texts/KP_%'",
    );
    const finalKP = parseInt(finalCount.rows[0].count, 10);
    console.log(`  rag_chunks WHERE canonical_id LIKE 'classical_texts/KP_%': ${finalKP}`);

    // Per-volume breakdown
    for (const s of volumeStats) {
      const volCount = await pool.query(
        `SELECT count(*) FROM rag_chunks WHERE canonical_id = $1`,
        [`classical_texts/KP_VOL${s.vol}`],
      );
      console.log(`  KP_VOL${s.vol}: ${volCount.rows[0].count} chunks`);
    }

    // metadata-based fallback count
    const metaCount = await pool.query(
      "SELECT count(*) FROM rag_chunks WHERE metadata->>'work' LIKE 'KP_%'",
    );
    console.log(`  By metadata->>'work' LIKE 'KP_%': ${metaCount.rows[0].count}`);

    console.log('\n[4] Acceptance criteria check:');
    const acPass = finalKP >= 1;
    console.log(`  AC.S2.3 (KP chunks ≥ 1): ${acPass ? 'PASS' : 'FAIL'} (${finalKP})`);
    console.log(`  AC.S2.4 (build_manifests): SKIPPED — asset_id column does not exist (per brief)`);

    if (errors > 0) {
      console.warn(`\n[WARN] ${errors} embedding errors. Re-run to retry.`);
    }

    console.log('\n' + '='.repeat(70));
    console.log('KP Reader ingestion complete.');
    console.log(`build_id: ${BUILD_ID}`);
    console.log(`rag_chunks inserted: ${finalKP}`);
    console.log('='.repeat(70));
  } finally {
    await pool.end();
  }
}

main().catch(err => {
  console.error('Fatal error:', err);
  process.exit(1);
});
