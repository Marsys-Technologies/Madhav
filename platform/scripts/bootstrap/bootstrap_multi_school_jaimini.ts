#!/usr/bin/env npx tsx
/**
 * bootstrap_multi_school_jaimini.ts
 * MCP Transformation v3.2-S4 — Jaimini school_signal_coverage backfill.
 *
 * Upserts Jaimini stances for all 573 MSR signals into school_signal_coverage.
 * Signals already at 'primary' or 'secondary' are only upgraded, never downgraded.
 * Signals new to Jaimini (59 missing rows) are INSERT-ed.
 * Signals upgrading from 'silent' to substantive are UPDATE-d.
 *
 * Jaimini stance logic (FORENSIC-grounded):
 *
 *   PRIMARY (confidence 0.65) — signal directly involves a Jaimini mechanism:
 *     - signal_type = 'jaimini-pattern' (explicit Jaimini signals)
 *     - planet IS the Atmakaraka (Moon), Amatyakaraka (Saturn), Darakaraka (Mercury),
 *       Putrakaraka (Mars), Gnatikaraka (Jupiter), Matrukaraka (Venus), or Bhratikaraka (Sun)
 *       AND domain matches the karaka's primary domain
 *     - signal involves Arudha placements (AL=10H, A7=11H, A6=2H, UL=3H)
 *     - house IS a Pada Lagna (4H = Lagna Pada by some reckonings)
 *
 *   SECONDARY (confidence 0.55) — signal involves a planet that is a chara karaka
 *     in any capacity, regardless of domain match; or involves a house that Jaimini
 *     rashi drishti engages (Jaimini aspects cover 2H/7H/10H/11H from fixed signs,
 *     and dual signs aspect all other dual signs).
 *
 *   SILENT — signals where no meaningful Jaimini lens applies (timing-only signals,
 *     nadi patterns, KP-specific stances, etc.) but a row must still exist.
 *
 * Native Jaimini chart (from FORENSIC §10.1, §13.1):
 *   Atmakaraka (AK)      = Moon   (27°02′, 11H Aquarius)
 *   Amatyakaraka (AmK)   = Saturn (22°27′,  7H Libra)
 *   Bhratikaraka (BK)    = Sun    (22°02′, 10H Capricorn)
 *   Matrukaraka (MK)     = Venus  (19°09′,  9H Sagittarius)
 *   Putrakaraka (PK)     = Mars   (18°31′,  7H Libra)
 *   Gnatikaraka (GK)     = Jupiter(09°48′,  9H Sagittarius)
 *   Darakaraka (DK)      = Mercury(00°50′, 10H Capricorn)
 *   Arudha Lagna (AL)    = 10H Capricorn
 *   Upapada (UL)         = 3H  Gemini
 *   A7 (Darapada)        = 11H Aquarius
 *   A6 (Shatrupada)      = 2H  Taurus
 *   Karakamsa            = Gemini (D9 Moon sign)
 *
 * Jaimini Rashi Drishti houses aspected by native's planets:
 *   Movable signs (Aries/Cancer/Libra/Capricorn) aspect all other movable signs
 *     except adjacent → 7H Libra aspects 1H/4H/10H (not 4H adjacent = wrong — Cancer IS adjacent,
 *     but actually Movable aspects Movable except adjacent sign).
 *   Fixed signs (Taurus/Leo/Scorpio/Aquarius) aspect all movable signs except the adjacent one.
 *   Dual signs (Gemini/Virgo/Sagittarius/Pisces) aspect each other.
 *
 * Simplified applicable-house set for the native (houses with Jaimini significance):
 *   Primary: 2, 7, 10, 11 (occupied movable/fixed signs with karakas)
 *   Secondary Jaimini houses: 1, 3, 4, 8, 9 (aspected or pada-significant)
 *
 * Usage:
 *   DATABASE_URL="postgresql://amjis_app:<pw>@localhost:5433/amjis" \
 *   npx tsx platform/scripts/bootstrap/bootstrap_multi_school_jaimini.ts
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

// ── Native Chart Constants (FORENSIC §10.1, §13.1) ───────────────────────────

/** Chara Karakas (7-karaka system) — planet → karaka role */
const CHARA_KARAKAS: Record<string, string> = {
  MOON: 'AK',     // Atmakaraka
  SATURN: 'AmK',  // Amatyakaraka
  SUN: 'BK',      // Bhratikaraka
  VENUS: 'MK',    // Matrukaraka
  MARS: 'PK',     // Putrakaraka
  JUPITER: 'GK',  // Gnatikaraka
  MERCURY: 'DK',  // Darakaraka
};

/** Karaka → primary domain mapping */
const KARAKA_DOMAIN_MAP: Record<string, string[]> = {
  AK: ['spirit', 'mind', 'psychology', 'psychological'],
  AmK: ['career'],
  BK: ['career', 'parents'],
  MK: ['parents', 'health'],
  PK: ['children', 'creativity'],
  GK: ['health', 'spirit', 'parents'],
  DK: ['relationships'],
};

/** Arudha houses — house number → arudha significance */
const ARUDHA_HOUSES = new Set([2, 3, 10, 11]); // A6=2H, UL=3H, AL=10H, A7=11H

/** Houses with direct Jaimini significance for the native */
const JAIMINI_PRIMARY_HOUSES = new Set([2, 7, 10, 11]); // karaka placements + arudhas
const JAIMINI_SECONDARY_HOUSES = new Set([1, 3, 4, 8, 9]); // aspected / pada houses

/** Jaimini-pattern signal types */
const JAIMINI_TYPE_KEYWORDS = ['jaimini-pattern', 'jaimini'];

/** Planets that are chara karakas (all 7 non-nodal planets) */
const KARAKA_PLANETS = new Set(Object.keys(CHARA_KARAKAS));

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
 * Determine Jaimini coverage stance for a single MSR signal.
 *
 * Decision tree (highest wins):
 *   1. signal_type contains 'jaimini' → PRIMARY
 *   2. planet is a chara karaka AND domain matches karaka's domain → PRIMARY
 *   3. house is in JAIMINI_PRIMARY_HOUSES → PRIMARY
 *   4. planet is any chara karaka (regardless of domain) → SECONDARY
 *   5. house is in JAIMINI_SECONDARY_HOUSES → SECONDARY
 *   6. domain is 'spirit' or 'spirit'-adjacent → SECONDARY (Jaimini is soul-centric)
 *   7. otherwise → SILENT
 */
function computeJaiminiStance(sig: MsrSignal): StanceResult {
  const planet = sig.planet?.toUpperCase() ?? null;
  const house = sig.house ?? null;
  const domain = sig.domain?.toLowerCase() ?? '';
  const signalType = sig.signal_type?.toLowerCase() ?? '';

  // Rule 1: Explicit jaimini signal type
  if (JAIMINI_TYPE_KEYWORDS.some((kw) => signalType.includes(kw))) {
    return {
      signal_id: sig.signal_id,
      coverage_type: 'primary',
      confidence: 0.90,
      notes:
        'Explicit jaimini-pattern signal — directly encodes Jaimini mechanism (chara karaka, rashi drishti, arudha, or pada).',
    };
  }

  // Rule 2: Planet is a chara karaka AND domain matches karaka's primary domain
  if (planet && KARAKA_PLANETS.has(planet)) {
    const role = CHARA_KARAKAS[planet];
    const karakaDomains = KARAKA_DOMAIN_MAP[role] ?? [];
    if (karakaDomains.includes(domain)) {
      return {
        signal_id: sig.signal_id,
        coverage_type: 'primary',
        confidence: 0.65,
        notes: `Planet ${planet} is ${role} (chara karaka) and domain '${domain}' matches karaka's primary domain — Jaimini karaka lens directly applies.`,
      };
    }
  }

  // Rule 3: House is a primary Jaimini-significant house (occupied by karakas or arudha)
  if (house !== null && JAIMINI_PRIMARY_HOUSES.has(house)) {
    return {
      signal_id: sig.signal_id,
      coverage_type: 'primary',
      confidence: 0.60,
      notes: `House ${house}H is a primary Jaimini house (karaka placement or arudha: AL=10H, A7=11H, A6=2H, AmK/PK=7H).`,
    };
  }

  // Rule 4: Planet is any chara karaka (different domain — secondary lens)
  if (planet && KARAKA_PLANETS.has(planet)) {
    const role = CHARA_KARAKAS[planet];
    return {
      signal_id: sig.signal_id,
      coverage_type: 'secondary',
      confidence: 0.55,
      notes: `Planet ${planet} is chara karaka ${role} — Jaimini secondary lens applies (karaka's cross-domain influence).`,
    };
  }

  // Rule 5: House is in secondary Jaimini houses (aspected or pada-relevant)
  if (house !== null && JAIMINI_SECONDARY_HOUSES.has(house)) {
    return {
      signal_id: sig.signal_id,
      coverage_type: 'secondary',
      confidence: 0.50,
      notes: `House ${house}H receives Jaimini rashi drishti or is pada-relevant (1H=Lagna, 3H=UL, 4H=lagna pada, 8H=ketu, 9H=dharma-GK).`,
    };
  }

  // Rule 6: Spirit/soul domain — Jaimini is inherently soul-centric (AK-driven)
  if (['spirit', 'spirituality', 'psychological', 'psychology', 'mind'].includes(domain)) {
    return {
      signal_id: sig.signal_id,
      coverage_type: 'secondary',
      confidence: 0.48,
      notes:
        'Domain is soul/spirit/psychological — Jaimini AK (Moon) lens is applicable even without direct karaka-planet match.',
    };
  }

  // Default: silent
  return {
    signal_id: sig.signal_id,
    coverage_type: 'silent',
    confidence: 0.30,
    notes: 'No direct Jaimini mechanism identified — signal involves neither a chara karaka nor a primary Jaimini house.',
  };
}

// ── Database operations ───────────────────────────────────────────────────────

async function run(): Promise<void> {
  const pool = new Pool({ connectionString: DATABASE_URL });

  try {
    console.log('=== bootstrap_multi_school_jaimini ===');
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

    // 2. Fetch current Jaimini coverage to avoid downgrading
    const existingRes = await pool.query<{
      signal_id: string;
      coverage_type: string;
      confidence: string;
    }>(
      `SELECT signal_id, coverage_type, confidence
       FROM school_signal_coverage
       WHERE school = 'jaimini'`
    );
    const existing = new Map(
      existingRes.rows.map((r) => [r.signal_id, r.coverage_type])
    );
    console.log(`Existing Jaimini rows: ${existing.size}`);
    const preExistingPrimary = existingRes.rows.filter((r) => r.coverage_type === 'primary').length;
    const preExistingSecondary = existingRes.rows.filter((r) => r.coverage_type === 'secondary').length;
    const preExistingSilent = existingRes.rows.filter((r) => r.coverage_type === 'silent').length;
    console.log(`  Before: primary=${preExistingPrimary}, secondary=${preExistingSecondary}, silent=${preExistingSilent}`);
    console.log('');

    // 3. Compute stances for all signals
    const stances = signals.map(computeJaiminiStance);

    // 4. Classify into insert vs upsert-upgrade
    const toInsert: StanceResult[] = [];
    const toUpgrade: StanceResult[] = [];
    const skipped: StanceResult[] = [];

    const SUBSTANTIVE = new Set(['primary', 'secondary']);
    const RANK = { primary: 2, secondary: 1, silent: 0 };

    for (const stance of stances) {
      const currentType = existing.get(stance.signal_id);
      if (!currentType) {
        // Missing row — insert
        toInsert.push(stance);
      } else {
        const currentRank = RANK[currentType as keyof typeof RANK] ?? 0;
        const newRank = RANK[stance.coverage_type];
        if (newRank > currentRank) {
          // Upgrade (never downgrade)
          toUpgrade.push(stance);
        } else {
          skipped.push(stance);
        }
      }
    }

    console.log(`Computed stances:`);
    const totalPrimary = stances.filter((s) => s.coverage_type === 'primary').length;
    const totalSecondary = stances.filter((s) => s.coverage_type === 'secondary').length;
    const totalSilent = stances.filter((s) => s.coverage_type === 'silent').length;
    console.log(`  primary=${totalPrimary}, secondary=${totalSecondary}, silent=${totalSilent}`);
    console.log(`  to INSERT (new rows): ${toInsert.length}`);
    console.log(`  to UPGRADE (silent→substantive): ${toUpgrade.length}`);
    console.log(`  unchanged / already substantive: ${skipped.length}`);
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

    // 5. Execute INSERT for missing rows
    if (toInsert.length > 0) {
      console.log(`Inserting ${toInsert.length} new Jaimini rows...`);
      const client = await pool.connect();
      try {
        await client.query('BEGIN');
        let inserted = 0;
        for (const stance of toInsert) {
          await client.query(
            `INSERT INTO school_signal_coverage (signal_id, school, coverage_type, confidence, notes)
             VALUES ($1, 'jaimini', $2, $3, $4)
             ON CONFLICT (signal_id, school) DO NOTHING`,
            [stance.signal_id, stance.coverage_type, stance.confidence, stance.notes]
          );
          inserted++;
        }
        await client.query('COMMIT');
        console.log(`  Inserted ${inserted} rows.`);
      } catch (err) {
        await client.query('ROLLBACK');
        throw err;
      } finally {
        client.release();
      }
    }

    // 6. Execute UPDATE for upgrades (silent → substantive)
    if (toUpgrade.length > 0) {
      console.log(`Upgrading ${toUpgrade.length} Jaimini rows from silent to substantive...`);
      const client = await pool.connect();
      try {
        await client.query('BEGIN');
        let upgraded = 0;
        for (const stance of toUpgrade) {
          await client.query(
            `UPDATE school_signal_coverage
             SET coverage_type = $1, confidence = $2, notes = $3
             WHERE signal_id = $4 AND school = 'jaimini'`,
            [stance.coverage_type, stance.confidence, stance.notes, stance.signal_id]
          );
          upgraded++;
        }
        await client.query('COMMIT');
        console.log(`  Upgraded ${upgraded} rows.`);
      } catch (err) {
        await client.query('ROLLBACK');
        throw err;
      } finally {
        client.release();
      }
    }

    // 7. Final count verification
    const finalRes = await pool.query<{ coverage_type: string; count: string }>(
      `SELECT coverage_type, count(*) as count
       FROM school_signal_coverage
       WHERE school = 'jaimini'
       GROUP BY coverage_type
       ORDER BY coverage_type`
    );
    console.log('');
    console.log('Final Jaimini coverage:');
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
    const finalSubstantive = finalPrimary + finalSecondary;
    console.log(`  substantive total: ${finalSubstantive}`);

    // 8. Gate check
    if (finalSubstantive >= 100) {
      console.log('');
      console.log(`GATE PASS: ${finalSubstantive} substantive Jaimini stances (≥100 required).`);
    } else {
      console.error('');
      console.error(`GATE FAIL: only ${finalSubstantive} substantive stances — need ≥100.`);
      process.exit(1);
    }
  } finally {
    await pool.end();
  }
}

run().catch((err) => {
  console.error('Fatal error:', err);
  process.exit(1);
});
