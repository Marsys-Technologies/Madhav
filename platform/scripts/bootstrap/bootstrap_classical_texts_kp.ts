#!/usr/bin/env npx tsx
/**
 * bootstrap_classical_texts_kp.ts
 * L0-K — KP Reader V/VI indexing into the served classical_text_chunks corpus.
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
 *   1. Reads the local OCR files for volumes 5 and 6 from SOURCE_DATA_DIR.
 *   2. Parses each volume into paragraph windows using sliding windows.
 *   3. Creates RawVerse-compatible records (work=KP_VOL1 etc).
 *   4. Chunks and inserts into classical_text_chunks (text_id='kp_reader').
 *   5. Does not embed or call a provider; the established corpus embedding path owns that work.
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
import { pathToFileURL } from 'url';

// ── Configuration ──────────────────────────────────────────────────────────────

const DATABASE_URL = process.env.DATABASE_URL;

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

// --volumes 5,6 — only the two locally verified volumes are in L0-K scope.
const VOL_IDX = args.findIndex(a => a === '--volumes');
const volumeArgument = VOL_IDX >= 0 ? args[VOL_IDX + 1] : undefined;
if (VOL_IDX >= 0 && volumeArgument === undefined) {
  throw new Error('INVALID_VOLUMES: --volumes requires 5,6');
}
if (volumeArgument !== undefined && !/^\d+(?:,\d+)*$/.test(volumeArgument)) {
  throw new Error('INVALID_VOLUMES: --volumes must be comma-separated whole-number volume IDs');
}
const VOLUMES: number[] = volumeArgument === undefined ? [5, 6] : volumeArgument.split(',').map(Number);
if (new Set(VOLUMES).size !== VOLUMES.length || VOLUMES.some(vol => vol !== 5 && vol !== 6)) {
  throw new Error('OUT_OF_SCOPE_VOLUME: L0-K only permits KP Reader volumes 5 and 6');
}

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
    vol: 5,
    workKey: 'KP_VOL5',
    title: 'Transit (Gocharapala Nirnayam)',
    filename: 'kp_reader_vol5_djvu.txt',
    sourceEdition: 'K.S. Krishnamurti, KP Reader Vol.5 (archive.org kp-readers)',
  },
  {
    vol: 6,
    workKey: 'KP_VOL6',
    title: 'Horary Astrology',
    filename: 'kp_reader_vol6_djvu.txt',
    sourceEdition: 'K.S. Krishnamurti, KP Reader Vol.6 (archive.org kp-readers)',
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
export interface KPChunk {
  chunkId: string;
  chapter: number;
  verseRef: string;
  content: string;
  sourceCitation: string;
}

export interface KPQueryClient {
  query: (text: string, values?: readonly unknown[]) => Promise<{ rowCount: number | null; rows: Array<Record<string, string>> }>;
}

export interface KPIngestionResult {
  inserted: number;
  total: number;
  perVolume: Record<number, number>;
}

export const KP_CHUNK_INSERT_SQL = `INSERT INTO classical_text_chunks
  (text_id, chunk_id, verse_ref, chapter, verse_start, verse_end, content_en, source_citation)
VALUES ('kp_reader', $1, $2, $3, $3, $3, $4, $5)
ON CONFLICT (chunk_id) DO NOTHING`;

/**
 * Persist parsed KP chunks into the same served table queried by
 * `search_classical_texts`. Keeping this boundary injectable lets the
 * bootstrap behaviour be exercised against a disposable corpus in tests.
 */
export async function ingestKPChunks(
  client: KPQueryClient,
  chunks: readonly KPChunk[],
  volumeStats: ReadonlyArray<{ vol: number; paragraphs: number; chunks: number }>,
): Promise<KPIngestionResult> {
  const text = await client.query("SELECT 1 FROM classical_texts WHERE text_id = 'kp_reader'");
  if (text.rowCount !== 1) {
    throw new Error('MISSING_SERVED_TEXT: classical_texts.kp_reader must exist before ingestion');
  }

  let inserted = 0;
  for (const chunk of chunks) {
    const result = await client.query(
      KP_CHUNK_INSERT_SQL,
      [chunk.chunkId, chunk.verseRef, chunk.chapter, chunk.content, chunk.sourceCitation],
    );
    inserted += result.rowCount ?? 0;
  }

  const finalCount = await client.query(
    "SELECT count(*) FROM classical_text_chunks WHERE text_id = 'kp_reader' AND chunk_id LIKE 'KP_VOL%'",
  );
  const total = parseInt(finalCount.rows[0].count, 10);
  const perVolume: Record<number, number> = {};
  for (const stat of volumeStats) {
    const count = await client.query(
      `SELECT count(*) FROM classical_text_chunks WHERE text_id = 'kp_reader' AND chunk_id LIKE $1`,
      [`KP_VOL${stat.vol}.%`],
    );
    perVolume[stat.vol] = parseInt(count.rows[0].count, 10);
  }
  return { inserted, total, perVolume };
}

function estimateTokens(text: string): number {
  return Math.ceil(text.split(/\s+/).filter(Boolean).length * 1.35);
}

export function parseKPVolume(text: string, spec: KPVolumeSpec): KPChunk[] {
  const chunks: KPChunk[] = [];

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

      chunks.push({
        chunkId: verseId,
        chapter: windowIdx,
        verseRef: `${spec.workKey}.${windowIdx}`,
        content: windowText,
        sourceCitation: spec.sourceEdition,
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

    chunks.push({
      chunkId: verseId,
      chapter: windowIdx,
      verseRef: `${spec.workKey}.${windowIdx}`,
      content: windowText,
      sourceCitation: spec.sourceEdition,
    });
  }

  return chunks;
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

  const allChunks: KPChunk[] = [];
  const volumeStats: Array<{ vol: number; paragraphs: number; chunks: number }> = [];

  for (const spec of KP_VOLUMES.filter(s => VOLUMES.includes(s.vol))) {
    const filepath = join(SOURCE_DATA_DIR, spec.filename);

    if (!existsSync(filepath)) {
      throw new Error(`MISSING_SOURCE_DATA: ${filepath}`);
    }

    const text = readFileSync(filepath, 'utf-8');
    console.log(`\n  Vol ${spec.vol} (${spec.title}): ${text.length.toLocaleString()} chars`);

    // Parse into paragraph windows (RawVerse-like records)
    const chunks = parseKPVolume(text, spec);
    console.log(`    Paragraph windows: ${chunks.length}`);

    if (chunks.length === 0) {
      throw new Error(`NO_CHUNKS: No content extracted from ${spec.filename}`);
    }

    console.log(`    Chunks: ${chunks.length}`);

    // Report token stats
    const tokenStats = chunks.map(c => estimateTokens(c.content));
    const avg = tokenStats.reduce((a, b) => a + b, 0) / tokenStats.length;
    console.log(`    Token avg=${avg.toFixed(0)} min=${Math.min(...tokenStats)} max=${Math.max(...tokenStats)}`);

    // Sample
    if (chunks.length > 0) {
      console.log(`    Sample: ${chunks[0].chunkId}: ${chunks[0].content.slice(0, 100)}...`);
    }

    allChunks.push(...chunks);
    volumeStats.push({ vol: spec.vol, paragraphs: chunks.length, chunks: chunks.length });
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

  if (!DATABASE_URL) {
    throw new Error('DATABASE_URL_REQUIRED: non-dry-run ingestion requires an explicit database URL');
  }

  console.log('\n[2] Connecting to database...');
  const pool = new Pool({ connectionString: DATABASE_URL });

  try {
    // ── 3. Embed and insert ────────────────────────────────────────────────

    console.log(`\n[3] Inserting ${allChunks.length} served-corpus chunks (build_id: ${BUILD_ID})...`);
    const ingestion = await ingestKPChunks(pool, allChunks, volumeStats);
    console.log(`  Newly inserted: ${ingestion.inserted}`);

    // ── 4. Final verification ──────────────────────────────────────────────

    console.log('\n[4] Verification queries...');
    const finalKP = ingestion.total;
    console.log(`  classical_text_chunks KP rows: ${finalKP}`);

    // Per-volume breakdown
    for (const s of volumeStats) {
      console.log(`  KP_VOL${s.vol}: ${ingestion.perVolume[s.vol]} chunks`);
    }

    console.log('\n[4] Acceptance criteria check:');
    const acPass = finalKP >= 1;
    console.log(`  L0-K served corpus rows ≥ 1: ${acPass ? 'PASS' : 'FAIL'} (${finalKP})`);

    console.log('\n' + '='.repeat(70));
    console.log('KP Reader ingestion complete.');
    console.log(`build_id: ${BUILD_ID}`);
    console.log(`classical_text_chunks KP rows: ${finalKP}`);
    console.log('='.repeat(70));
  } finally {
    await pool.end();
  }
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch(err => {
    console.error('Fatal error:', err);
    process.exit(1);
  });
}
