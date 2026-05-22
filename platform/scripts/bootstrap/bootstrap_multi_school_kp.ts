#!/usr/bin/env npx tsx
/**
 * bootstrap_multi_school_kp.ts
 * MCP Transformation v3.2-S4 — KP school_signal_coverage backfill.
 *
 * Upserts KP stances for all 573 MSR signals into school_signal_coverage.
 * Currently all 514 existing KP rows are 'silent'; this script upgrades
 * applicable signals to 'primary' or 'secondary' and inserts the 59 missing rows.
 *
 * KP stance logic (chart_facts-grounded):
 *
 *   PRIMARY (confidence 0.70) — signal's planet or house directly maps to a
 *     KP significator or sub-lord for a relevant cusp:
 *     - Planet is a significator of the house matching the signal's domain
 *     - Planet is the sub-lord of a cuspal group matching the signal's domain
 *     - Planet is its own sub-lord (pure significator — strong KP position)
 *
 *   SECONDARY (confidence 0.60) — planet appears in the star-lord hierarchy
 *     for a relevant cusp, or the signal's house is covered by KP significators:
 *     - Planet is the star-lord of a relevant cusp
 *     - Signal house is in the KP significator list for the domain's cusp
 *     - Planet's own sub-lord matches a significator of the relevant cusp
 *
 *   SILENT — no KP relevance: signal involves neither a KP significator
 *     for the relevant domain cusp nor a planet with KP sub-lord significance.
 *
 * Native KP Chart Data (from chart_facts):
 *
 *   Cusp sub-lords (authoritative from chart_facts kp_cusp):
 *     Cusp 1  (Lagna/Self)        — sub_lord: Mercury,  star_lord: Ketu
 *     Cusp 2  (Wealth)            — sub_lord: Rahu,     star_lord: Moon
 *     Cusp 3  (Effort/Courage)    — sub_lord: Rahu,     star_lord: Rahu
 *     Cusp 4  (Home/Education)    — sub_lord: Rahu,     star_lord: Jupiter
 *     Cusp 5  (Creativity/Child)  — sub_lord: Venus,    star_lord: Ketu
 *     Cusp 6  (Job/Debt/Health)   — sub_lord: Saturn,   star_lord: Sun
 *     Cusp 7  (Partners)          — sub_lord: Saturn,   star_lord: Rahu
 *     Cusp 8  (Transformation)    — sub_lord: Mars,     star_lord: Saturn
 *     Cusp 9  (Dharma/Luck)       — sub_lord: Jupiter,  star_lord: Ketu
 *     Cusp 10 (Career)            — sub_lord: Saturn,   star_lord: Sun
 *     Cusp 11 (Gains)             — sub_lord: Mercury,  star_lord: Mars
 *     Cusp 12 (Loss/Moksha)       — sub_lord: Saturn,   star_lord: Saturn
 *
 *   Planet sub-lords (authoritative from chart_facts kp_planet):
 *     Jupiter sub_lord = Saturn; star_lord = Ketu
 *     Ketu    sub_lord = Ketu;   star_lord = Mercury
 *     Mars    sub_lord = Moon;   star_lord = Rahu
 *     Mercury sub_lord = Rahu;   star_lord = Sun
 *     Moon    sub_lord = Venus;  star_lord = Jupiter
 *     Rahu    sub_lord = Mercury; star_lord = Moon
 *     Saturn  sub_lord = Saturn; star_lord = Jupiter
 *     Sun     sub_lord = Venus;  star_lord = Moon
 *     Venus   sub_lord = Rahu;   star_lord = Venus
 *
 *   KP Significators (from chart_facts kp_significator):
 *     House 1  → Mars, Ketu
 *     House 2  → Rahu, Venus
 *     House 6  → Mars, Ketu, Mercury
 *     House 7  → Moon, Saturn, Venus
 *     House 10 → Mercury, Venus, Mars, Ketu, Sun, Saturn
 *     House 11 → Sun, Rahu, Moon, Saturn
 *     House 12 → Saturn, Jupiter
 *
 * Domain → KP house mapping:
 *   career        → cusps 10, 6, 11
 *   wealth        → cusps 2, 11, 10
 *   relationships → cusps 7, 11
 *   health        → cusps 6, 1, 8
 *   children      → cusps 5, 11
 *   spirit        → cusps 9, 12, 8
 *   travel        → cusps 9, 12, 3
 *   mind          → cusps 1, 3, 4
 *   parents       → cusps 9, 4
 *   education     → cusps 4, 5, 9
 *
 * Usage:
 *   DATABASE_URL="postgresql://amjis_app:<pw>@localhost:5433/amjis" \
 *   npx tsx platform/scripts/bootstrap/bootstrap_multi_school_kp.ts
 *
 *   With --dry-run: compute stances and report without DB writes.
 *   With --verbose: log each signal's assigned stance.
 */

import { Pool } from 'pg';

// ── Configuration ──────────────────────────────────────────────────────────────

const DATABASE_URL =
  process.env.DATABASE_URL ?? 'postgresql://amjis_app@localhost:5433/amjis';

const DRY_RUN = process.argv.includes('--dry-run');
const VERBOSE = process.argv.includes('--verbose');

// ── Native KP Chart Data (FORENSIC-grounded, from chart_facts) ───────────────

/** Cusp sub-lords: cusp number → sub_lord planet */
const CUSP_SUB_LORDS: Record<number, string> = {
  1: 'Mercury', 2: 'Rahu', 3: 'Rahu', 4: 'Rahu',
  5: 'Venus', 6: 'Saturn', 7: 'Saturn', 8: 'Mars',
  9: 'Jupiter', 10: 'Saturn', 11: 'Mercury', 12: 'Saturn',
};

/** Cusp star-lords: cusp number → star_lord planet */
const CUSP_STAR_LORDS: Record<number, string> = {
  1: 'Ketu', 2: 'Moon', 3: 'Rahu', 4: 'Jupiter',
  5: 'Ketu', 6: 'Sun', 7: 'Rahu', 8: 'Saturn',
  9: 'Ketu', 10: 'Sun', 11: 'Mars', 12: 'Saturn',
};

/** KP Significators: house number → set of significator planets */
const KP_SIGNIFICATORS: Record<number, Set<string>> = {
  1: new Set(['Mars', 'Ketu']),
  2: new Set(['Rahu', 'Venus']),
  6: new Set(['Mars', 'Ketu', 'Mercury']),
  7: new Set(['Moon', 'Saturn', 'Venus']),
  10: new Set(['Mercury', 'Venus', 'Mars', 'Ketu', 'Sun', 'Saturn']),
  11: new Set(['Sun', 'Rahu', 'Moon', 'Saturn']),
  12: new Set(['Saturn', 'Jupiter']),
};

/** Planet sub-lords (from chart_facts kp_planet) */
const PLANET_SUB_LORDS: Record<string, string> = {
  Jupiter: 'Saturn', Ketu: 'Ketu', Mars: 'Moon', Mercury: 'Rahu',
  Moon: 'Venus', Rahu: 'Mercury', Saturn: 'Saturn', Sun: 'Venus', Venus: 'Rahu',
};

/** Planet star-lords (from chart_facts kp_planet) */
const PLANET_STAR_LORDS: Record<string, string> = {
  Jupiter: 'Ketu', Ketu: 'Mercury', Mars: 'Rahu', Mercury: 'Sun',
  Moon: 'Jupiter', Rahu: 'Moon', Saturn: 'Jupiter', Sun: 'Moon', Venus: 'Venus',
};

/** Domain → relevant KP cusps (primary cusp first) */
const DOMAIN_CUSP_MAP: Record<string, number[]> = {
  career: [10, 6, 11],
  wealth: [2, 11, 10],
  relationships: [7, 11],
  health: [6, 1, 8],
  children: [5, 11],
  spirit: [9, 12, 8],
  spirituality: [9, 12],
  travel: [9, 12, 3],
  mind: [1, 3, 4],
  psychological: [1, 8],
  psychology: [1, 8],
  parents: [9, 4],
  education: [4, 5, 9],
  other: [1],
  unknown: [],
  timing: [],
};

// ── Stance computation ────────────────────────────────────────────────────────

interface MsrSignal {
  signal_id: string;
  domain: string;
  planet: string | null;
  house: number | null;
  signal_type: string;
  valence: string;
}

interface StanceResult {
  signal_id: string;
  coverage_type: 'primary' | 'secondary' | 'silent';
  confidence: number;
  notes: string;
}

/**
 * Determine KP coverage stance for a single MSR signal.
 *
 * Decision tree:
 *   1. Signal's planet is a significator for the primary cusp of the signal's domain
 *      AND planet is its own sub-lord → PRIMARY (purest KP position)
 *   2. Signal's planet is a significator for the primary cusp of the signal's domain → PRIMARY
 *   3. Signal's planet is the sub-lord of the primary cusp of the signal's domain → PRIMARY
 *   4. Signal's house matches one of the domain's cusps AND a KP significator list exists → PRIMARY
 *   5. Signal's planet is the star-lord of a relevant cusp → SECONDARY
 *   6. Signal's planet appears as significator for secondary cusps → SECONDARY
 *   7. Signal's planet's own sub-lord is a significator of the relevant cusp → SECONDARY
 *   8. No KP relevance → SILENT
 */
function computeKpStance(sig: MsrSignal): StanceResult {
  const planet = sig.planet ? capitalizeFirst(sig.planet) : null;
  const house = sig.house ?? null;
  const domain = sig.domain?.toLowerCase() ?? '';

  const relevantCusps = DOMAIN_CUSP_MAP[domain] ?? [];
  const primaryCusp = relevantCusps[0] ?? null;

  // Rule 1: Planet is significator of primary cusp AND is own sub-lord
  if (planet && primaryCusp !== null) {
    const sigs = KP_SIGNIFICATORS[primaryCusp];
    if (sigs?.has(planet) && PLANET_SUB_LORDS[planet] === planet) {
      return {
        signal_id: sig.signal_id,
        coverage_type: 'primary',
        confidence: 0.75,
        notes: `${planet} is a KP significator of cusp ${primaryCusp} (${domain} domain) AND is its own sub-lord — strongest KP testimony.`,
      };
    }
  }

  // Rule 2: Planet is significator of primary cusp
  if (planet && primaryCusp !== null) {
    const sigs = KP_SIGNIFICATORS[primaryCusp];
    if (sigs?.has(planet)) {
      return {
        signal_id: sig.signal_id,
        coverage_type: 'primary',
        confidence: 0.70,
        notes: `${planet} is a KP significator of cusp ${primaryCusp} (${domain} domain primary cusp).`,
      };
    }
  }

  // Rule 3: Planet is the sub-lord of the primary cusp
  if (planet && primaryCusp !== null) {
    if (CUSP_SUB_LORDS[primaryCusp] === planet) {
      return {
        signal_id: sig.signal_id,
        coverage_type: 'primary',
        confidence: 0.70,
        notes: `${planet} is the sub-lord of cusp ${primaryCusp} (${domain} domain primary cusp) — KP sub-lord testimony directly applies.`,
      };
    }
  }

  // Rule 4: Signal's house directly maps to a cusp with KP significators
  if (house !== null) {
    const sigs = KP_SIGNIFICATORS[house];
    if (sigs && sigs.size > 0 && relevantCusps.includes(house)) {
      const sigList = Array.from(sigs).join(', ');
      return {
        signal_id: sig.signal_id,
        coverage_type: 'primary',
        confidence: 0.65,
        notes: `House ${house}H matches domain cusp (${domain}) and has KP significators: ${sigList}.`,
      };
    }
  }

  // Rule 5: Planet is the star-lord of any relevant cusp
  if (planet) {
    for (const cusp of relevantCusps) {
      if (CUSP_STAR_LORDS[cusp] === planet) {
        return {
          signal_id: sig.signal_id,
          coverage_type: 'secondary',
          confidence: 0.60,
          notes: `${planet} is the star-lord of cusp ${cusp} (${domain} domain) — KP star-lord level testimony.`,
        };
      }
    }
  }

  // Rule 6: Planet is significator of a secondary cusp for the domain
  if (planet && relevantCusps.length > 1) {
    for (const cusp of relevantCusps.slice(1)) {
      const sigs = KP_SIGNIFICATORS[cusp];
      if (sigs?.has(planet)) {
        return {
          signal_id: sig.signal_id,
          coverage_type: 'secondary',
          confidence: 0.60,
          notes: `${planet} is a KP significator of secondary cusp ${cusp} (${domain} domain) — secondary KP testimony.`,
        };
      }
    }
  }

  // Rule 7: Planet's own sub-lord is a significator of the primary cusp
  if (planet && primaryCusp !== null) {
    const planetSubLord = PLANET_SUB_LORDS[planet];
    const primarySigs = KP_SIGNIFICATORS[primaryCusp];
    if (planetSubLord && primarySigs?.has(planetSubLord)) {
      return {
        signal_id: sig.signal_id,
        coverage_type: 'secondary',
        confidence: 0.55,
        notes: `${planet}'s sub-lord (${planetSubLord}) is a KP significator of cusp ${primaryCusp} (${domain}) — indirect KP chain.`,
      };
    }
  }

  // Rule 8: House is listed in KP significator system (even if not primary domain match)
  if (house !== null && KP_SIGNIFICATORS[house]) {
    return {
      signal_id: sig.signal_id,
      coverage_type: 'secondary',
      confidence: 0.50,
      notes: `House ${house}H has KP significators in the system — KP cuspal relevance exists.`,
    };
  }

  // Silent: no KP testimony found
  return {
    signal_id: sig.signal_id,
    coverage_type: 'silent',
    confidence: 0.30,
    notes: 'No KP significator or sub-lord testimony identified for this signal.',
  };
}

function capitalizeFirst(s: string): string {
  if (!s) return s;
  const lower = s.toLowerCase();
  return lower.charAt(0).toUpperCase() + lower.slice(1);
}

// ── Database operations ───────────────────────────────────────────────────────

async function run(): Promise<void> {
  const pool = new Pool({ connectionString: DATABASE_URL });

  try {
    console.log('=== bootstrap_multi_school_kp ===');
    console.log(`Mode: ${DRY_RUN ? 'DRY RUN' : 'LIVE'}`);
    console.log('');

    // 1. Fetch all MSR signals
    const signalRes = await pool.query<MsrSignal>(
      `SELECT signal_id, domain, planet, house, signal_type, valence
       FROM msr_signals
       ORDER BY signal_id`
    );
    const signals = signalRes.rows;
    console.log(`Fetched ${signals.length} MSR signals`);

    // 2. Fetch current KP coverage
    const existingRes = await pool.query<{
      signal_id: string;
      coverage_type: string;
    }>(
      `SELECT signal_id, coverage_type
       FROM school_signal_coverage
       WHERE school = 'kp'`
    );
    const existing = new Map(
      existingRes.rows.map((r) => [r.signal_id, r.coverage_type])
    );
    const preExistingSilent = existingRes.rows.filter((r) => r.coverage_type === 'silent').length;
    const preExistingSubstantive = existingRes.rows.length - preExistingSilent;
    console.log(`Existing KP rows: ${existing.size} (substantive: ${preExistingSubstantive}, silent: ${preExistingSilent})`);
    console.log('');

    // 3. Compute stances
    const stances = signals.map(computeKpStance);

    // 4. Classify operations
    const toInsert: StanceResult[] = [];
    const toUpgrade: StanceResult[] = [];
    const skipped: StanceResult[] = [];

    const RANK = { primary: 2, secondary: 1, silent: 0 };

    for (const stance of stances) {
      const currentType = existing.get(stance.signal_id);
      if (!currentType) {
        toInsert.push(stance);
      } else {
        const currentRank = RANK[currentType as keyof typeof RANK] ?? 0;
        const newRank = RANK[stance.coverage_type];
        if (newRank > currentRank) {
          toUpgrade.push(stance);
        } else {
          skipped.push(stance);
        }
      }
    }

    const totalPrimary = stances.filter((s) => s.coverage_type === 'primary').length;
    const totalSecondary = stances.filter((s) => s.coverage_type === 'secondary').length;
    const totalSilent = stances.filter((s) => s.coverage_type === 'silent').length;

    console.log('Computed stances:');
    console.log(`  primary=${totalPrimary}, secondary=${totalSecondary}, silent=${totalSilent}`);
    console.log(`  to INSERT (new rows): ${toInsert.length}`);
    console.log(`  to UPGRADE (silent→substantive): ${toUpgrade.length}`);
    console.log(`  unchanged: ${skipped.length}`);
    console.log('');

    if (VERBOSE) {
      for (const s of stances) {
        const action = toInsert.find((x) => x.signal_id === s.signal_id)
          ? 'INSERT'
          : toUpgrade.find((x) => x.signal_id === s.signal_id)
          ? 'UPGRADE'
          : 'skip';
        console.log(`  [${action}] ${s.signal_id} → ${s.coverage_type} (${s.confidence}) | ${s.notes}`);
      }
    }

    if (DRY_RUN) {
      console.log('DRY RUN — no DB writes performed.');
      return;
    }

    // 5. INSERT missing rows
    if (toInsert.length > 0) {
      console.log(`Inserting ${toInsert.length} new KP rows...`);
      const client = await pool.connect();
      try {
        await client.query('BEGIN');
        for (const stance of toInsert) {
          await client.query(
            `INSERT INTO school_signal_coverage (signal_id, school, coverage_type, confidence, notes)
             VALUES ($1, 'kp', $2, $3, $4)
             ON CONFLICT (signal_id, school) DO NOTHING`,
            [stance.signal_id, stance.coverage_type, stance.confidence, stance.notes]
          );
        }
        await client.query('COMMIT');
        console.log(`  Inserted ${toInsert.length} rows.`);
      } catch (err) {
        await client.query('ROLLBACK');
        throw err;
      } finally {
        client.release();
      }
    }

    // 6. UPDATE upgrades (silent → substantive)
    if (toUpgrade.length > 0) {
      console.log(`Upgrading ${toUpgrade.length} KP rows from silent to substantive...`);
      const client = await pool.connect();
      try {
        await client.query('BEGIN');
        for (const stance of toUpgrade) {
          await client.query(
            `UPDATE school_signal_coverage
             SET coverage_type = $1, confidence = $2, notes = $3
             WHERE signal_id = $4 AND school = 'kp'`,
            [stance.coverage_type, stance.confidence, stance.notes, stance.signal_id]
          );
        }
        await client.query('COMMIT');
        console.log(`  Upgraded ${toUpgrade.length} rows.`);
      } catch (err) {
        await client.query('ROLLBACK');
        throw err;
      } finally {
        client.release();
      }
    }

    // 7. Final verification
    const finalRes = await pool.query<{ coverage_type: string; count: string }>(
      `SELECT coverage_type, count(*) as count
       FROM school_signal_coverage
       WHERE school = 'kp'
       GROUP BY coverage_type
       ORDER BY coverage_type`
    );
    console.log('');
    console.log('Final KP coverage:');
    let finalPrimary = 0;
    let finalSecondary = 0;
    let finalSilent = 0;
    for (const row of finalRes.rows) {
      const n = parseInt(row.count, 10);
      console.log(`  ${row.coverage_type}: ${n}`);
      if (row.coverage_type === 'primary') finalPrimary = n;
      if (row.coverage_type === 'secondary') finalSecondary = n;
      if (row.coverage_type === 'silent') finalSilent = n;
    }
    const totalRows = finalPrimary + finalSecondary + finalSilent;
    console.log(`  total rows: ${totalRows}`);
    console.log(`  substantive: ${finalPrimary + finalSecondary}`);

    if (totalRows >= 573) {
      console.log('');
      console.log(`KP GATE PASS: ${totalRows} total rows covering all MSR signals.`);
    } else {
      console.error('');
      console.error(`KP GATE WARN: only ${totalRows} rows — expected 573.`);
    }
  } finally {
    await pool.end();
  }
}

run().catch((err) => {
  console.error('Fatal error:', err);
  process.exit(1);
});
