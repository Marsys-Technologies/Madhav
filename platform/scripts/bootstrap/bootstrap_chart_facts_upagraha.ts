/**
 * bootstrap_chart_facts_upagraha.ts
 *
 * MCPT v3.3-S2 — Upagraha ingestion (FORENSIC mode)
 *
 * Source: FORENSIC_ASTROLOGICAL_DATA_v8_0.md §11.1
 *
 * Upagrahas ingested (time-based; B.10 discipline — values from FORENSIC only):
 *   Gulika          — Gemini  13°57′  Ardra        → House 3
 *   Mandi           — Cancer  14°13′  Pushya       → House 4
 *   Yamaghantaka    — Taurus  01°54′  Krittika     → House 2
 *   Ardhaprahara    — Aries   10°52′  Ashwini      → House 1
 *
 * Sun-based upagrahas also in §11.1 (Dhuma, Vyatipata, Parivesha, Indrachapa, Upaketu)
 * are ingested as additional rows for completeness.
 *
 * House derivation: Lagna = Aries (H1), so H2=Taurus, H3=Gemini, H4=Cancer,
 *   H5=Leo, H6=Virgo, H7=Libra, H8=Scorpio, H9=Sagittarius, H10=Capricorn,
 *   H11=Aquarius, H12=Pisces. (FORENSIC §3.1 HSE.1–HSE.12)
 *
 * B.10 compliance: All values read directly from FORENSIC v8.0. No values fabricated.
 *   House numbers derived from sign-to-house mapping in FORENSIC §3.1.
 *
 * Usage:
 *   cd /Users/Dev/Vibe-Coding/Apps/MadhavMCPT-DPT
 *   DATABASE_URL=postgresql://... npx tsx platform/scripts/bootstrap/bootstrap_chart_facts_upagraha.ts
 */

import * as path from 'node:path'
import * as dotenv from 'dotenv'
import { makePool, upsertChartFacts, insertBuildManifest } from './lib/chart_facts_ingester'
import type { ChartFactRow } from './lib/chart_facts_ingester'

dotenv.config({ path: path.join(process.cwd(), '.env.local') })

// ── Build ID ────────────────────────────────────────────────────────────────

const TIMESTAMP = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19)
const BUILD_ID = `mcpt-v33-s2-upagraha-${TIMESTAMP}`

// ── Provenance ──────────────────────────────────────────────────────────────

const PROVENANCE = {
  source_uri: '01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md',
  source_version: '8.0',
  source_canonical_id: 'FORENSIC_v8_0',
  extracted_at: new Date().toISOString(),
  extraction_method: 'manual_extraction_from_forensic_v8_0',
}

// ── Sign → House mapping (from FORENSIC §3.1) ──────────────────────────────
// Lagna = Aries (H1); whole-sign houses

const SIGN_TO_HOUSE: Record<string, number> = {
  Aries: 1,
  Taurus: 2,
  Gemini: 3,
  Cancer: 4,
  Leo: 5,
  Virgo: 6,
  Libra: 7,
  Scorpio: 8,
  Sagittarius: 9,
  Capricorn: 10,
  Aquarius: 11,
  Pisces: 12,
}

// ── §11.1 Upagraha Data ─────────────────────────────────────────────────────
//
// FORENSIC §11.1 table: ID | Upagraha | Type | Sign | Degree | Nakshatra
// Time-based upagrahas + Sun-based upagrahas

const UPAGRAHA_DATA: Array<{
  name: string
  upg_type: 'time-based' | 'sun-based'
  sign: string
  degree: string
  nakshatra: string
  forensic_id: string
}> = [
  // Time-based upagrahas — FORENSIC §11.1 UPG.GULIKA through UPG.ARDHAPRAHARA
  { name: 'Gulika',       upg_type: 'time-based', sign: 'Gemini',      degree: '13°57′', nakshatra: 'Ardra',           forensic_id: 'UPG.GULIKA'       },
  { name: 'Mandi',        upg_type: 'time-based', sign: 'Cancer',      degree: '14°13′', nakshatra: 'Pushya',          forensic_id: 'UPG.MANDI'        },
  { name: 'Yamaghantaka', upg_type: 'time-based', sign: 'Taurus',      degree: '01°54′', nakshatra: 'Krittika',        forensic_id: 'UPG.YAMAGHANTAKA' },
  { name: 'Ardhaprahara', upg_type: 'time-based', sign: 'Aries',       degree: '10°52′', nakshatra: 'Ashwini',         forensic_id: 'UPG.ARDHAPRAHARA' },
  // Sun-based upagrahas — FORENSIC §11.1 UPG.DHUMA through UPG.UPAKETU
  { name: 'Dhuma',        upg_type: 'sun-based',  sign: 'Gemini',      degree: '05°17′', nakshatra: 'Mrigasira',       forensic_id: 'UPG.DHUMA'        },
  { name: 'Vyatipata',    upg_type: 'sun-based',  sign: 'Capricorn',   degree: '24°42′', nakshatra: 'Dhanishta',       forensic_id: 'UPG.VYATIPATA'    },
  { name: 'Parivesha',    upg_type: 'sun-based',  sign: 'Cancer',      degree: '24°42′', nakshatra: 'Ashlesha',        forensic_id: 'UPG.PARIVESHA'    },
  { name: 'Indrachapa',   upg_type: 'sun-based',  sign: 'Sagittarius', degree: '05°17′', nakshatra: 'Moola',           forensic_id: 'UPG.INDRACHAPA'   },
  { name: 'Upaketu',      upg_type: 'sun-based',  sign: 'Sagittarius', degree: '21°57′', nakshatra: 'Purva Ashadha',   forensic_id: 'UPG.UPAKETU'      },
]

function buildUpagrahaRows(): ChartFactRow[] {
  const rows: ChartFactRow[] = []
  for (const upg of UPAGRAHA_DATA) {
    const house = SIGN_TO_HOUSE[upg.sign]
    rows.push({
      fact_id: `UPG.${upg.name.toUpperCase()}`,
      category: 'upagraha',
      divisional_chart: 'D1',
      value_text: `${upg.sign} ${upg.degree} (${upg.nakshatra})`,
      value_number: null,
      value_json: {
        name: upg.name,
        type: upg.upg_type,
        sign: upg.sign,
        degree: upg.degree,
        nakshatra: upg.nakshatra,
        house,
        forensic_id: upg.forensic_id,
      },
      source_section: 'FORENSIC_v8_0_§11.1',
      build_id: BUILD_ID,
      provenance: PROVENANCE,
    })
  }
  return rows
}

// ── Main ────────────────────────────────────────────────────────────────────

async function main() {
  const pool = makePool()
  try {
    const rows = buildUpagrahaRows()
    const timeBased = rows.filter((r) => (r.value_json as Record<string, unknown>)?.type === 'time-based')
    const sunBased  = rows.filter((r) => (r.value_json as Record<string, unknown>)?.type === 'sun-based')

    console.log(`[Upagraha Bootstrap] build_id = ${BUILD_ID}`)
    console.log(`[Upagraha Bootstrap] total rows:       ${rows.length}  (expected ≥ 5)`)
    console.log(`[Upagraha Bootstrap]   time-based:     ${timeBased.length}  (Gulika, Mandi, Yamaghantaka, Ardhaprahara)`)
    console.log(`[Upagraha Bootstrap]   sun-based:      ${sunBased.length}   (Dhuma, Vyatipata, Parivesha, Indrachapa, Upaketu)`)

    // Insert build_manifests row first (chart_facts.build_id FK requires it)
    await insertBuildManifest(pool, {
      build_id: BUILD_ID,
      triggered_by: 'manual:mcpt-v33-s2',
      registry_fingerprint: 'FORENSIC_v8_0_sha256_be76cc7aa84f3c1e',
      pipeline_image_uri: 'mcpt-depth-bootstrap:v3.3-S2',
      embedding_model: 'none',
      embedding_dim: 0,
      chunk_count: rows.length,
      embedding_count: 0,
      status: 'live',
      manifest_uri: 'local://mcpt-v33-s2-upagraha',
      notes: 'Upagraha ingestion from FORENSIC v8.0 §11.1; mode=FORENSIC; 4 time-based + 5 sun-based = 9 rows',
    })
    console.log(`[Upagraha Bootstrap] build_manifests row inserted`)

    const inserted = await upsertChartFacts(pool, rows)
    console.log(`[Upagraha Bootstrap] upserted: ${inserted} rows — DONE`)
  } finally {
    await pool.end()
  }
}

main().catch((err) => {
  console.error('[Upagraha Bootstrap] FATAL:', err)
  process.exit(1)
})
