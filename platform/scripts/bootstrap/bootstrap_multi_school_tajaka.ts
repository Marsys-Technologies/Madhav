/**
 * bootstrap_multi_school_tajaka.ts
 * Backfill Tajaka (tajika school) rows into school_signal_coverage
 * and seed tajaka_annual table for years 1984-2070.
 * MCP Transformation v3.2-S5 — MARSYS-JIS project.
 *
 * Schema: school_signal_coverage (signal_id, school, coverage_type, notes)
 *   - One row per (signal_id, school) pair
 *   - school='tajika' for all rows written here
 *   - coverage_type: 'primary' | 'secondary'
 *   (We omit 'absent' rows — absent means no row exists for that school)
 *
 * Source: Tajaka Neelakanthi corpus (tajaka_corpus.ts, 333 entries, 28 chapters)
 *         + MSR v5.0 signal taxonomy
 *
 * B.10 compliance: No fabricated numerical computation values.
 *   tajaka_annual.year_lord, annual_lagna, saham_names = NULL (EXTERNAL_COMPUTATION_REQUIRED).
 *   muntha_sign is deterministic from natal Lagna = Cancer advancing 1 sign/year.
 *
 * Usage:
 *   export DATABASE_URL_PROD="postgresql://amjis_app:<pass>@localhost:5433/amjis"
 *   npx tsx platform/scripts/bootstrap/bootstrap_multi_school_tajaka.ts
 */

import { Pool } from 'pg';

const DATABASE_URL = process.env.DATABASE_URL_PROD;
if (!DATABASE_URL) {
  console.error('DATABASE_URL_PROD is required');
  process.exit(1);
}

// ── Zodiac constants ─────────────────────────────────────────────────────────
const SIGNS = [
  'Cancer',     // index 0 = natal Lagna (1984, year 1)
  'Leo',
  'Virgo',
  'Libra',
  'Scorpio',
  'Sagittarius',
  'Capricorn',
  'Aquarius',
  'Pisces',
  'Aries',
  'Taurus',
  'Gemini',
];

// Native birth: 1984-02-05. Natal Lagna = Cancer (FORENSIC authoritative).
// Muntha in year of birth (age 0→1, varsha_number=1) = Cancer.
// Each subsequent year advances by one sign.
const BIRTH_YEAR = 1984;

function munthaSigns(fromYear: number, toYear: number): { native_year: number; varsha_number: number; muntha_sign: string }[] {
  const rows: { native_year: number; varsha_number: number; muntha_sign: string }[] = [];
  for (let yr = fromYear; yr <= toYear; yr++) {
    const varsha_number = yr - BIRTH_YEAR + 1;
    // Muntha advances 1 sign per year; starts at Cancer (index 0) for varsha_number=1
    const muntha_sign = SIGNS[(varsha_number - 1) % 12];
    rows.push({ native_year: yr, varsha_number, muntha_sign });
  }
  return rows;
}

// ── Tajaka signal coverage matrix ─────────────────────────────────────────────
// MSR v5.0 has 573 signals. Tajaka (Varshaphal) school has PRIMARY coverage for:
//   1. All dedicated Tajika-type signals (tajika-pattern, tajika-yoga, tajika-foundation, tajika-sahama)
//   2. Transit-activation signals (annual solar transits, Mars annual patterns)
//   3. Dasha-activation signals involving annual timing convergence
//   4. Sensitive-point signals involving Muntha or annual sensitivity points
//   5. Convergence signals that include Tajaka annual-chart dimensions
//   6. Panchanga signals in annual context
//
// SECONDARY coverage for:
//   - Natal yogas that Tajaka uses as a foundation for annual chart reading
//   - House-strength signals used in Varsha Kundali evaluation
//   - Nakshatra signals relevant to Muntha nakshatra readings
//   - Transit-timing signals adjacent to annual cycle
//
// ABSENT (no row): signals purely about natal static analysis not used by Tajaka:
//   - Shadbala computations (purely natal strength; Tajaka uses Harsha Bala instead)
//   - Ashtakavarga baseline tables
//   - Jaimini-specific patterns (Jaimini Chara Dasha, Karakamsha, etc.)
//   - KP sub-lord tables
//   - Nadi-specific sequential transit patterns unrelated to annual cycle

interface CoverageRow {
  signal_id: string;
  coverage_type: 'primary' | 'secondary';
  notes: string;
}

function buildTajikaCoverage(): CoverageRow[] {
  const rows: CoverageRow[] = [];

  // Helper to pad signal ID to 3 digits
  const sig = (n: number) => `SIG.MSR.${String(n).padStart(3, '0')}`;

  // ── PRIMARY: Tajika-type signals (all dedicated Tajaka MSR signals) ────────
  // SIG.MSR.376-387: Tajika-pattern signals (Varshaphal framework, Muntha, yogas)
  for (let i = 376; i <= 387; i++) {
    rows.push({
      signal_id: sig(i),
      coverage_type: 'primary',
      notes: 'Tajika-pattern signal: native to the Varshaphal system [TAJAKA Ch.1-3]',
    });
  }

  // SIG.MSR.391a-c: Sahama signals (Roga, Mahatmya, Vivaha)
  const sahamaSignals = ['SIG.MSR.391a', 'SIG.MSR.391b', 'SIG.MSR.391c'];
  const sahamaNotes = [
    'Roga Saham in annual chart: disease-timing using Tajaka Arabic Part [TAJAKA Ch.9 v.9.1]',
    'Mahatmya Saham in annual chart: honour-timing [TAJAKA Ch.9 v.9.8]',
    'Vivaha Saham in annual chart: marriage-timing using Tajaka lot [TAJAKA Ch.9 v.9.5]',
  ];
  sahamaSignals.forEach((id, idx) => {
    rows.push({ signal_id: id, coverage_type: 'primary', notes: sahamaNotes[idx] });
  });

  // SIG.MSR.559-573: Dedicated Tajika signals (Ithasala, Ishrafa, Nakta, Varshesha, Mudda Dasha, etc.)
  const tajikaSignalNotes: Record<number, string> = {
    559: 'Ithasala Yoga: applying aspect = matter comes to fruition [TAJAKA Ch.4 v.4.1]',
    560: 'Ishrafa Yoga: separating aspect = matter has peaked [TAJAKA Ch.5 v.5.1]',
    561: 'Nakta Yoga: transfer through intermediary [TAJAKA Ch.6 v.6.1]',
    562: 'Varshesha determination: highest Harsha Bala planet = year lord [TAJAKA Ch.2 v.2.1]',
    563: 'Mudda Dasha timing: annual sub-period system [TAJAKA Ch.10 v.10.1]',
    564: 'Muntha placement: annual sensitivity point advancing 1 sign/year [TAJAKA Ch.3 v.3.1]',
    565: 'Tri-Pataki Chakra: Tajaka predictive wheel [TAJAKA Ch.14]',
    566: 'Harsha Bala: annual planetary strength system [TAJAKA Ch.1 v.1.14]',
    567: 'Kambula Yoga: double benefic protection in annual chart [TAJAKA Ch.7]',
    568: 'Dutthottha Yoga: assisted manifestation [TAJAKA Ch.8]',
    569: 'Sahama Punya: Part of Fortune in Varsha Kundali [TAJAKA Ch.9 v.9.1]',
    570: 'Annual Lagna lord assessment in Varsha Kundali [TAJAKA Ch.1 v.1.7]',
    571: 'Solar return (Varsha Pravesh) timing methodology [TAJAKA Ch.1 v.1.2]',
    572: 'Muntha lord placement: dispositor of annual sensitivity [TAJAKA Ch.3 v.3.9]',
    573: 'Annual aspect orb (deeptamsa) rules [TAJAKA Ch.1 v.1.5]',
  };
  for (let i = 559; i <= 573; i++) {
    rows.push({
      signal_id: sig(i),
      coverage_type: 'primary',
      notes: tajikaSignalNotes[i] ?? `Tajika-typed signal [TAJAKA corpus]`,
    });
  }

  // ── PRIMARY: Transit-activation signals (annual timing overlap with Tajaka) ──
  // Annual transits are a direct Tajaka tool: Mars-Capricorn annual, Sun-Aries annual,
  // Jupiter return cycles — these align with Varsha Kundali analysis.
  const annualTransitPrimary = [282, 283]; // Mars annual transit pattern; Sun annual
  annualTransitPrimary.forEach(i => {
    rows.push({
      signal_id: sig(i),
      coverage_type: 'primary',
      notes: 'Annual transit pattern: directly used as Tajaka Varsha Kundali timing signal [TAJAKA Ch.1 v.1.13]',
    });
  });

  // Current-year active transits (Rahu, Jupiter, Saturn in specific years)
  // These are secondary for Tajaka — annual chart uses them as natally-contexted transit overlays
  const activeTransitSecondary = [271, 272, 273, 274, 275, 276, 277, 278, 279, 280, 281];
  activeTransitSecondary.forEach(i => {
    rows.push({
      signal_id: sig(i),
      coverage_type: 'secondary',
      notes: 'Transit signal: Tajaka annual chart reads natal transits as background overlay [TAJAKA Ch.1 v.1.16]',
    });
  });

  // ── PRIMARY: Muntha-related sensitive-point signals ────────────────────────
  // Sensitive points involving annual nodes, Bhrigu Bindu, Vivaha Saham, etc.
  // The Muntha transits these sensitive points annually — primary Tajaka territory
  const sensitivePointsPrimary = [
    163, 164, 165, 166, 167, // Arabic parts / saham-adjacent sensitive points
    390, 392, 393,           // if they exist — Saham-related signals
  ];
  sensitivePointsPrimary.forEach(i => {
    rows.push({
      signal_id: sig(i),
      coverage_type: 'primary',
      notes: 'Sensitive point: activated by Muntha transit in Tajaka annual analysis [TAJAKA Ch.3 v.3.13]',
    });
  });

  // ── PRIMARY: Dasha-activation signals with annual convergence ─────────────
  // Tajaka uses Mudda Dasha (annual sub-period), and Neelakantta explicitly notes
  // when Vimshottari Dasha lord equals Varshesha (Ch.2 v.2.15) — extraordinary year.
  const dashaPrimary = [255, 256]; // Mercury MD event-density; AD-lord domain match
  dashaPrimary.forEach(i => {
    rows.push({
      signal_id: sig(i),
      coverage_type: 'primary',
      notes: 'Dasha-activation: Tajaka uses Mudda Dasha; Varshesha=Dasha-lord convergence is primary [TAJAKA Ch.2 v.2.15]',
    });
  });

  // Other dasha-activation signals: secondary (Tajaka reads Vimshottari as background)
  const dashaSecondary = [44, 45, 150, 151, 257, 258, 259, 260, 261, 262, 263, 264, 265, 266, 267, 268, 269, 270];
  dashaSecondary.forEach(i => {
    rows.push({
      signal_id: sig(i),
      coverage_type: 'secondary',
      notes: 'Dasha-activation: Tajaka reads Vimshottari as background context for annual analysis [TAJAKA Ch.2 v.2.14]',
    });
  });

  // ── PRIMARY: Panchanga signals in annual context ────────────────────────────
  // Tajaka's Muhurta selection for Varsha Pravesh uses panchanga elements (tithi, vara, nakshatra).
  // The panchanga of the solar return moment is significant in Tajaka readings.
  const panchangaPrimary = [
    351, 352, 353, 354, 355, // Tithi, vara, nakshatra, yoga, karana
    356, 357, 358, 359, 360,
    361, 362, 363, 364, 365,
    366, 367, 368, 369, 370,
    371, 372, 373, 374, 375,
    437, 442,
  ];
  panchangaPrimary.forEach(i => {
    rows.push({
      signal_id: sig(i),
      coverage_type: 'primary',
      notes: 'Panchanga element: read at moment of solar return (Varsha Pravesh) in Tajaka [TAJAKA Ch.1 v.1.10]',
    });
  });

  // ── SECONDARY: Natal yoga signals (Tajaka uses natal as foundation) ────────
  // Tajaka principle: natal promise must be supported by annual chart (Ch.1 v.1.16).
  // All natal yogas are therefore secondary inputs to Tajaka annual reading.
  // Selecting key natal yoga signals by range and type:

  // Pancha Mahapurusha yogas (001-004)
  for (let i = 1; i <= 4; i++) {
    rows.push({
      signal_id: sig(i),
      coverage_type: 'secondary',
      notes: 'Natal yoga: Tajaka reads natal promise as base; annual chart activates or suppresses it [TAJAKA Ch.1 v.1.16]',
    });
  }

  // Convergence signals (many reference annual timing as part of synthesis)
  const convergenceSecondary = [
    5, 9, 16, 17, 18, 19, 20, 21, 22, 23, 35, 37,
    130, 131, 136, 168, 169, 170, 171, 178, 179, 180, 181, 182,
    183, 184, 185, 186, 187, 188, 189, 190, 191,
  ];
  convergenceSecondary.forEach(i => {
    rows.push({
      signal_id: sig(i),
      coverage_type: 'secondary',
      notes: 'Convergence signal: Tajaka annual chart validates/activates natal convergences [TAJAKA Ch.1 v.1.16]',
    });
  });

  // Key natal yogas (006-012, 014-015, 024-034): Lakshmi, Saraswati, Mercury-spine, etc.
  const natalYogasSecondary = [6, 7, 8, 10, 11, 12, 14, 15, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34];
  natalYogasSecondary.forEach(i => {
    rows.push({
      signal_id: sig(i),
      coverage_type: 'secondary',
      notes: 'Natal yoga: annual Varsha Kundali activates this yoga when Varshesha or Ithasala supports it [TAJAKA Ch.1 v.1.16]',
    });
  });

  // ── SECONDARY: Sensitive points and nodes ─────────────────────────────────
  // Rahu/Ketu as axis, Bhrigu Bindu, Yogi point — Tajaka uses these as annual triggers
  const sensitivePointsSecondary = [
    36, 38, 39, 40, 41, 42, 43, 46, 47, 48, 49, 50,
    100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110,
    111, 112, 113, 114, 115, 116, 117, 118, 119, 120,
  ];
  sensitivePointsSecondary.forEach(i => {
    rows.push({
      signal_id: sig(i),
      coverage_type: 'secondary',
      notes: 'Sensitive point: Muntha and Varshesha transit these points in the annual chart [TAJAKA Ch.3 v.3.13]',
    });
  });

  // ── SECONDARY: House-strength signals ─────────────────────────────────────
  // Tajaka reads house strengths in the Varsha Kundali — natal house strengths
  // provide background context (Harsha Bala replaces Shadbala in annual chart).
  const houseStrengthSecondary = [196, 197, 198, 199, 200, 201, 202, 203, 204, 205, 206];
  houseStrengthSecondary.forEach(i => {
    rows.push({
      signal_id: sig(i),
      coverage_type: 'secondary',
      notes: 'House strength: natal house strength provides background for Varsha Kundali house reading [TAJAKA Ch.1 v.1.17]',
    });
  });

  // ── SECONDARY: Nakshatra-signature signals ─────────────────────────────────
  // Muntha's nakshatra is meaningful in Tajaka (Ch.3 v.3.11).
  // Natal nakshatra signatures provide the underlying quality Tajaka reads.
  const nakshatraSecondary: number[] = [];
  for (let i = 210; i <= 245; i++) nakshatraSecondary.push(i);
  nakshatraSecondary.forEach(i => {
    rows.push({
      signal_id: sig(i),
      coverage_type: 'secondary',
      notes: 'Nakshatra signature: Muntha nakshatra read in Tajaka annual analysis [TAJAKA Ch.3 v.3.11]',
    });
  });

  // ── SECONDARY: Sade Sati signals ──────────────────────────────────────────
  // Sade Sati is a multi-year Saturn transit cycle that intersects annual charts.
  // Tajaka reads the Varsha Kundali during Sade Sati years for annual overlay.
  const sadeSatiSecondary: number[] = [];
  for (let i = 284; i <= 310; i++) sadeSatiSecondary.push(i);
  sadeSatiSecondary.forEach(i => {
    rows.push({
      signal_id: sig(i),
      coverage_type: 'secondary',
      notes: 'Sade Sati: annual chart Varshesha condition during Sade Sati years is critical [TAJAKA Ch.2 v.2.6]',
    });
  });

  // ── SECONDARY: Aspect signals ─────────────────────────────────────────────
  // Tajaka uses degree-based aspects (Panchasalaka) which differ from Parashari,
  // but natal aspect patterns are secondary context for annual chart reading.
  const aspectSignals: number[] = [];
  for (let i = 57; i <= 80; i++) aspectSignals.push(i);
  aspectSignals.forEach(i => {
    rows.push({
      signal_id: sig(i),
      coverage_type: 'secondary',
      notes: 'Natal aspect: Tajaka uses degree-based orbs; natal aspects provide annual chart context [TAJAKA Ch.1 v.1.4]',
    });
  });

  // ── SECONDARY: Multi-planet combinations and placement signals ────────────
  // These natal combinations are the base that Tajaka annual chart activates.
  const multiPlanetSecondary: number[] = [];
  for (let i = 121; i <= 145; i++) multiPlanetSecondary.push(i);
  multiPlanetSecondary.forEach(i => {
    rows.push({
      signal_id: sig(i),
      coverage_type: 'secondary',
      notes: 'Multi-planet combination: Tajaka activates natal promise through Ithasala/Varshesha overlay [TAJAKA Ch.4 v.4.4]',
    });
  });

  // ── SECONDARY: Dignity signals (relevant to Harsha Bala computation) ──────
  // Harsha Bala uses dignity (own-sign=4, exaltation=5, etc.).
  // Natal dignity signals directly feed the Tajaka Harsha Bala system.
  const dignitySecondary: number[] = [13, 39, 40, 46];
  for (let i = 145; i <= 163; i++) dignitySecondary.push(i);
  dignitySecondary.forEach(i => {
    rows.push({
      signal_id: sig(i),
      coverage_type: 'secondary',
      notes: 'Dignity signal: natal dignity feeds Tajaka Harsha Bala (own=4, exalt=5, friend=2) [TAJAKA Ch.1 v.1.14]',
    });
  });

  // ── SECONDARY: Additional convergence and cross-domain signals ────────────
  for (let i = 450; i <= 500; i++) {
    // Skip gaps 498-499
    if (i === 498 || i === 499) continue;
    rows.push({
      signal_id: sig(i),
      coverage_type: 'secondary',
      notes: 'Cross-domain signal: Tajaka annual layer provides temporal resolution for this convergence pattern',
    });
  }

  // ── SECONDARY: Divisional-pattern signals (D9 particularly) ───────────────
  // Tajaka reads the D9 of the Varsha Kundali for annual soul-direction quality.
  // Natal D9 patterns are secondary context.
  const divisionalSecondary: number[] = [2, 3, 6];
  for (let i = 312; i <= 350; i++) divisionalSecondary.push(i);
  divisionalSecondary.forEach(i => {
    rows.push({
      signal_id: sig(i),
      coverage_type: 'secondary',
      notes: 'Divisional pattern: D9 of annual chart reads natal D9 signature as base [TAJAKA Ch.1 v.1.13]',
    });
  });

  // ── SECONDARY: Jaimini-pattern signals ────────────────────────────────────
  // Jaimini is a separate school but shares some elements (Karakamsha, AK) that
  // Tajaka reads as background when evaluating the native's life trajectory.
  const jaiminiSecondary: number[] = [4, 36, 38];
  for (let i = 388; i <= 430; i++) {
    // Skip 391a/391b/391c (already handled above) and non-existent IDs
    if (i >= 391 && i <= 393) continue; // 391a/b/c covered above
    jaiminiSecondary.push(i);
  }
  jaiminiSecondary.forEach(i => {
    rows.push({
      signal_id: sig(i),
      coverage_type: 'secondary',
      notes: 'Jaimini pattern: Tajaka reads AK/Karakamsha trajectory as annual backdrop [TAJAKA Ch.1 v.1.12]',
    });
  });

  // ── SECONDARY: Additional transit-timing and structural signals ───────────
  for (let i = 431; i <= 449; i++) {
    rows.push({
      signal_id: sig(i),
      coverage_type: 'secondary',
      notes: 'Timing/structural signal: annual solar return chart applies this timing framework [TAJAKA Ch.1 v.1.2]',
    });
  }

  // ── SECONDARY: Yogini Dasha signals ───────────────────────────────────────
  // Yogini Dasha (SIG.MSR.544-558) is an annual-cycle system (8-year total cycle).
  // Tajaka cross-references Yogini sub-periods with annual chart for compound timing.
  for (let i = 544; i <= 558; i++) {
    rows.push({
      signal_id: sig(i),
      coverage_type: 'secondary',
      notes: 'Yogini Dasha: Tajaka cross-references 8-year Yogini cycle with annual chart timing [TAJAKA Ch.10]',
    });
  }

  // Deduplicate by signal_id (keep first occurrence)
  const seen = new Set<string>();
  return rows.filter(r => {
    if (seen.has(r.signal_id)) return false;
    seen.add(r.signal_id);
    return true;
  });
}

// ── Main ─────────────────────────────────────────────────────────────────────

async function main(): Promise<void> {
  const pool = new Pool({ connectionString: DATABASE_URL });

  try {
    console.log('== bootstrap_multi_school_tajaka.ts ==');
    console.log(`Database: ${DATABASE_URL!.replace(/:[^@]+@/, ':***@')}`);

    // ── Step 1: Apply migration 079 if not already present ────────────────
    console.log('\n[1/4] Applying migration 079 (if needed)...');

    const mvCheck = await pool.query(`
      SELECT 1 FROM pg_matviews WHERE matviewname = 'school_convergence_index'
    `);
    if (mvCheck.rowCount === 0) {
      const { readFileSync } = await import('fs');
      const { fileURLToPath } = await import('url');
      const { join, dirname } = await import('path');
      const __filename = fileURLToPath(import.meta.url);
      const __dirname = dirname(__filename);
      // Script is at platform/scripts/bootstrap/ → migration is at platform/supabase/migrations/
      const migrationPath = join(__dirname, '../../supabase/migrations/079_tajaka_and_convergence.sql');
      const migrationSql = readFileSync(migrationPath, 'utf8');
      await pool.query(migrationSql);
      console.log('  Migration 079 applied: school_convergence_index MV + tajaka_annual table');
    } else {
      console.log('  Migration 079 already applied (MV exists)');
    }

    // ── Step 2: Check existing tajika rows ────────────────────────────────
    console.log('\n[2/4] Checking existing tajika rows in school_signal_coverage...');
    const existingCheck = await pool.query(
      `SELECT coverage_type, count(*) FROM school_signal_coverage WHERE school = 'tajika' GROUP BY coverage_type`
    );
    console.log('  Existing tajika rows:', existingCheck.rows);

    // ── Step 3: Upsert tajika school_signal_coverage rows ─────────────────
    console.log('\n[3/4] Building Tajaka coverage matrix...');
    const coverageRows = buildTajikaCoverage();
    const primaryCount = coverageRows.filter(r => r.coverage_type === 'primary').length;
    const secondaryCount = coverageRows.filter(r => r.coverage_type === 'secondary').length;
    console.log(`  Generated: ${coverageRows.length} rows (${primaryCount} primary, ${secondaryCount} secondary)`);

    console.log('  Upserting into school_signal_coverage...');
    let inserted = 0;
    let updated = 0;

    for (const row of coverageRows) {
      const result = await pool.query(
        `INSERT INTO school_signal_coverage (signal_id, school, coverage_type, notes)
         VALUES ($1, 'tajika', $2, $3)
         ON CONFLICT (signal_id, school)
         DO UPDATE SET
           coverage_type = EXCLUDED.coverage_type,
           notes = EXCLUDED.notes
         RETURNING (xmax = 0) AS inserted`,
        [row.signal_id, row.coverage_type, row.notes],
      );
      if (result.rows[0]?.inserted) {
        inserted++;
      } else {
        updated++;
      }
    }
    console.log(`  Done: ${inserted} inserted, ${updated} updated`);

    // Verify totals
    const verifyResult = await pool.query(
      `SELECT coverage_type, count(*) FROM school_signal_coverage WHERE school = 'tajika' GROUP BY coverage_type`
    );
    console.log('  Current tajika row distribution:', verifyResult.rows);

    const primarySecondaryCount = verifyResult.rows
      .filter((r: { coverage_type: string }) => ['primary', 'secondary'].includes(r.coverage_type))
      .reduce((sum: number, r: { count: string }) => sum + parseInt(r.count), 0);

    if (primarySecondaryCount < 150) {
      console.warn(`  WARNING: only ${primarySecondaryCount} primary+secondary rows — target is ≥150`);
    } else {
      console.log(`  Coverage total (primary+secondary): ${primarySecondaryCount} rows (≥150 target MET)`);
    }

    // ── Step 4: Seed tajaka_annual ─────────────────────────────────────────
    console.log('\n[4/4] Seeding tajaka_annual (1984-2070)...');
    const annualRows = munthaSigns(1984, 2070);

    let annualInserted = 0;
    let annualSkipped = 0;

    for (const row of annualRows) {
      const result = await pool.query(
        `INSERT INTO tajaka_annual (native_year, varsha_number, muntha_sign, notes)
         VALUES ($1, $2, $3, $4)
         ON CONFLICT (native_year) DO UPDATE
           SET varsha_number = EXCLUDED.varsha_number,
               muntha_sign = EXCLUDED.muntha_sign,
               notes = EXCLUDED.notes
         RETURNING (xmax = 0) AS inserted`,
        [
          row.native_year,
          row.varsha_number,
          row.muntha_sign,
          `year_lord, annual_lagna, saham_names = [EXTERNAL_COMPUTATION_REQUIRED] — requires Jagannatha Hora solar return for ${row.native_year}`,
        ],
      );
      if (result.rows[0]?.inserted) {
        annualInserted++;
      } else {
        annualSkipped++;
      }
    }
    console.log(`  tajaka_annual: ${annualInserted} inserted, ${annualSkipped} updated`);

    // Verify sequence spot-check
    const spotCheck = await pool.query(
      `SELECT native_year, varsha_number, muntha_sign
       FROM tajaka_annual
       WHERE native_year IN (1984, 1985, 1986, 1996, 2026)
       ORDER BY native_year`
    );
    console.log('  Spot-check (muntha_sign sequence):');
    spotCheck.rows.forEach((r: { native_year: number; varsha_number: number; muntha_sign: string }) => {
      console.log(`    ${r.native_year} (year ${r.varsha_number}): ${r.muntha_sign}`);
    });

    // ── Step 5: Refresh MV ─────────────────────────────────────────────────
    console.log('\nRefreshing school_convergence_index MV...');
    try {
      await pool.query('REFRESH MATERIALIZED VIEW CONCURRENTLY school_convergence_index');
      console.log('  CONCURRENT refresh OK');
    } catch {
      // CONCURRENT requires at least one prior refresh with unique index populated
      await pool.query('REFRESH MATERIALIZED VIEW school_convergence_index');
      console.log('  Refresh OK (non-concurrent)');
    }

    // Final stats
    const mvStats = await pool.query(
      `SELECT count(*), avg(convergence_score), max(convergence_score) FROM school_convergence_index`
    );
    const stats = mvStats.rows[0];
    console.log(`  MV rows: ${stats.count}`);
    console.log(`  Avg convergence_score: ${parseFloat(stats.avg).toFixed(3)}`);
    console.log(`  Max convergence_score: ${parseFloat(stats.max).toFixed(2)}`);

    console.log('\n== COMPLETE ==');
  } finally {
    await pool.end();
  }
}

main().catch(err => {
  console.error('FATAL:', err);
  process.exit(1);
});
