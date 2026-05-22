/**
 * bootstrap_classical_texts_tajaka.ts
 * Ingest Tajaka Neelakanthi into classical_texts + rag_chunks.
 * MCP Transformation v3.2-S3 — MARSYS-JIS project.
 *
 * Source: MARSYS-JIS-M9-extraction (structured from project knowledge layer).
 * Tajaka Neelakanthi was not available on archive.org; this corpus is derived
 * from canonical Tajaka doctrine as held in the M9 multi-school triangulation layer.
 * See SOURCE_INVENTORY_TAJAKA_v1_0.md for full provenance declaration.
 *
 * Usage:
 *   export DATABASE_URL_PROD="postgresql://amjis_app:<pass>@localhost:5433/amjis"
 *   npx tsx platform/scripts/bootstrap/bootstrap_classical_texts_tajaka.ts
 */

import { Pool } from 'pg';
import { TAJAKA_CORPUS } from './lib/tajaka_corpus.js';
import { chunkVerse, type RawVerse } from './lib/classical_text_chunker.js';
import { embedAndPersistChunks, type InsertResult } from './lib/classical_text_embedder.js';

const DATABASE_URL = process.env.DATABASE_URL_PROD;
if (!DATABASE_URL) {
  console.error('DATABASE_URL_PROD is required');
  process.exit(1);
}

const BUILD_ID = `mcpt-v32-tajaka-${new Date().toISOString().slice(0, 16).replace('T', '-').replace(':', '')}`;
const WORK_KEY = 'TAJAKA';
const SOURCE_EDITION = 'MARSYS-JIS-M9-extraction (Tajaka Neelakanthi structured corpus v1.0)';

function corpusToRawVerses(): RawVerse[] {
  return TAJAKA_CORPUS.map(entry => {
    const verseId = `TAJAKA.${String(entry.chapter).padStart(2, '0')}.${String(entry.verse).padStart(3, '0')}`;
    return {
      work: WORK_KEY,
      chapter: entry.chapter,
      verse_start: entry.verse,
      verse_end: entry.verse,
      verse_ref: `${entry.chapter}.${entry.verse}`,
      verse_id: verseId,
      translation_text: entry.content,
      source_edition: SOURCE_EDITION,
    } satisfies RawVerse;
  });
}

async function upsertClassicalTextsRow(pool: Pool): Promise<void> {
  // classical_texts actual schema: text_key (unique), title, author, tradition, school,
  // tier, language_original, translation_author, source_url, procurement_date, chunk_count
  // NOTE: 'work' is a generated column: upper(text_key) — do not insert into it directly.
  await pool.query(
    `INSERT INTO classical_texts
       (text_key, title, author, tradition, school, tier, language_original, translation_author, source_url, procurement_date)
     VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, now()::date)
     ON CONFLICT (text_key) DO UPDATE
       SET translation_author = EXCLUDED.translation_author,
           source_url = EXCLUDED.source_url`,
    [
      'tajaka_neelakanthi',
      'Tajaka Neelakanthi',
      'Neelakantta',
      'tajaka',
      'tajaka',
      2,
      'sanskrit',
      'MARSYS-JIS M9 structured extraction',
      'https://github.com/amonty84/Madhav (internal M9 knowledge layer)',
    ],
  );
}

async function main(): Promise<void> {
  console.log(`=== Tajaka Neelakanthi Ingestion START (build_id: ${BUILD_ID}) ===`);

  const pool = new Pool({ connectionString: DATABASE_URL });

  try {
    // Upsert classical_texts metadata row
    await upsertClassicalTextsRow(pool);
    console.log(`classical_texts row upserted for work='${WORK_KEY}'`);

    // Convert corpus to RawVerse objects
    const verses = corpusToRawVerses();
    console.log(`Corpus: ${verses.length} verses across ${new Set(verses.map(v => v.chapter)).size} chapters`);

    // Chunk verses
    const chunks = verses.flatMap(v => chunkVerse(v, 400));
    console.log(`Chunked into ${chunks.length} ClassicalChunk objects`);

    // Embed and persist
    const results: InsertResult[] = await embedAndPersistChunks(pool, chunks, BUILD_ID, {
      batchSize: 20,
      batchDelayMs: 300,
      verbose: true,
    });

    const inserted = results.filter(r => r.inserted).length;
    const embedded = results.filter(r => r.embedded).length;
    const errors = results.filter(r => r.error).length;

    console.log(`\n=== Tajaka Ingestion COMPLETE ===`);
    console.log(`  chunks: ${chunks.length} | inserted: ${inserted} | embedded: ${embedded} | errors: ${errors}`);
    console.log(`  build_id: ${BUILD_ID}`);

    // Verify gate (canonical_id = 'classical_texts/TAJAKA' as set by insertRagChunk)
    const countResult = await pool.query(
      `SELECT count(*) FROM rag_chunks WHERE doc_type='classical_text' AND canonical_id = 'classical_texts/TAJAKA'`,
    );
    const count = parseInt(countResult.rows[0].count, 10);
    console.log(`  DB verification: ${count} Tajaka rag_chunks`);

    if (count < 200) {
      console.error(`WARN: count ${count} < 200; check for ingestion errors`);
      process.exit(1);
    }

    process.exit(0);
  } catch (err) {
    console.error('Fatal error:', err);
    process.exit(1);
  } finally {
    await pool.end();
  }
}

main();
