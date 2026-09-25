import { readFileSync } from 'node:fs'
import path from 'node:path'

import { describe, expect, it } from 'vitest'

import { ASSETS } from '../seed/asset_registry_seed'

/**
 * W-L0-5 (L0 Brahmagyan elevation, strategy v2.1 §4.2 "Provenance completion",
 * final item; strategy §2.1 boundary table row "A registry description must not
 * assert a provenance the table does not have" — marked **gap**, "1079 was a
 * one-off correction; the description-vs-table check has no detector").
 *
 * This is the standing detector for that boundary. The defect class: an
 * asset_registry `english_description` asserts a fact about the underlying
 * table or writer that the source of truth does not bear out. Two observed
 * instances:
 *
 *   - migration 1079 (bg_transit_rules): the description claimed table-wide
 *     provenance when the table carries per-row citations only.
 *   - migration 642 (bg_vidhi_floors): the description claimed "12/14 intent
 *     floors are writer-tagged [MANDATORY] (settled)" when the writer source
 *     carries 1 [MANDATORY], 2 [CANDIDATE], 11 untagged. Repaired in this
 *     packet (migration 1124 + seed, same truthful text both sides).
 *
 * What this detector checks, and what it deliberately does not:
 *
 *   It verifies description claims against the writer/seed SOURCES OF TRUTH in
 *   the repo (the writer module the table is written from). It does not query
 *   production: description↔production drift is the census/integrity_check_sql
 *   path, not this gate. A description that matches its writer but not the live
 *   table is a reconciliation finding (see the W-L0-5 packet report's
 *   writer/production drift caveat), not a description lie.
 *
 * The claim grammar is fail-closed: any bg_* description making a claim shape
 * this detector knows MUST verify against a registered source of truth, and a
 * claim shape with no registered truth source is itself a failure — a new
 * claim cannot slip through by being unparseable. Three shapes are known:
 *
 *   1. Writer-tag distribution claims ("N/M … writer-tagged [MANDATORY]",
 *      "N/M carry no writer tag") — truth: the writer's own tag distribution
 *      (642 class).
 *   2. Category-count claims ("N classical transit rules: A favourable,
 *      B unfavourable, [and] C double-transit") — truth: the writer module's
 *      rule literals for the writer-owned categories, plus internal arithmetic
 *      (N = A + B + C). The 7 double-transit rows are migration-397-owned (see
 *      l0_transit.py F-145) and are not re-derived here.
 *   3. Provenance-column name claims (a backticked identifier from the known
 *      provenance-column vocabulary) — truth: the asset's registered writer
 *      module must actually write that column (1079 class). No current
 *      description makes such a claim; the checker is exercised by the
 *      synthetic tests below so it cannot rot vacuously.
 */

const VIDHI_FLOORS_WRITER = path.resolve(
  __dirname,
  '../../python-sidecar/pipeline/orchestrator/writers/bg_vidhi_floors.py',
)
const TRANSIT_WRITER = path.resolve(
  __dirname,
  '../../python-sidecar/brahmagyan/l0_transit.py',
)

/** Provenance-bearing column names a description may claim by name. */
const PROVENANCE_COLUMNS = [
  'school',
  'school_tag',
  'source_ref',
  'source_authority',
  'source_chunk_ids',
  'classical_citation',
  'unlinked_reason',
  'qualification_state',
  'extraction_pass_log',
  'verse_ref',
  'text_id',
] as const

/** Writer module that owns each asset's table, for claim shape 3. */
const WRITER_BY_ASSET: Record<string, string> = {
  bg_rules: path.resolve(__dirname, '../../python-sidecar/brahmagyan/l0_rules.py'),
  bg_transit_rules: TRANSIT_WRITER,
  bg_parihara_rules: path.resolve(
    __dirname,
    '../../python-sidecar/pipeline/orchestrator/writers/bg_parihara_rules.py',
  ),
  bg_vidhi_floors: VIDHI_FLOORS_WRITER,
  bg_vidhi_primitives: path.resolve(
    __dirname,
    '../../python-sidecar/pipeline/orchestrator/writers/bg_vidhi_primitives.py',
  ),
}

// ── Claim extraction ─────────────────────────────────────────────────────────

export interface TagClaim {
  kind: 'MANDATORY' | 'CANDIDATE' | 'UNTAGGED'
  claimed: number
  denominator: number
}

export function extractTagClaims(description: string): TagClaim[] {
  const claims: TagClaim[] = []
  for (const m of description.matchAll(
    /(\d+)\/(\d+)[^,.\n]*?writer-tagged \[(MANDATORY|CANDIDATE)\]/g,
  )) {
    claims.push({ kind: m[3] as 'MANDATORY' | 'CANDIDATE', claimed: Number(m[1]), denominator: Number(m[2]) })
  }
  for (const m of description.matchAll(/(\d+)\/(\d+)[^,.\n]*?carry no writer tag/g)) {
    claims.push({ kind: 'UNTAGGED', claimed: Number(m[1]), denominator: Number(m[2]) })
  }
  return claims
}

export interface TransitClaim {
  total: number
  favourable: number
  unfavourable: number
  doubleTransit: number
}

export function extractTransitClaim(description: string): TransitClaim | null {
  // The "and" before the double-transit count is optional: the pre-repair text
  // read "…26 unfavourable, and 7 double-transit", the 2026-09 L0 repair text
  // (migration 1079) reads "…26 unfavourable, 7 double-transit". Both parse;
  // any other shape still returns null and the pinned test below refuses it.
  const m = description.match(
    /(\d+) classical transit rules: (\d+) favourable, (\d+) unfavourable,(?: and)? (\d+) double-transit/,
  )
  if (!m) return null
  return {
    total: Number(m[1]),
    favourable: Number(m[2]),
    unfavourable: Number(m[3]),
    doubleTransit: Number(m[4]),
  }
}

export function extractProvenanceColumnClaims(description: string): string[] {
  const claimed = new Set<string>()
  for (const m of description.matchAll(/`([a-z_][a-z0-9_]*)`/g)) {
    if ((PROVENANCE_COLUMNS as readonly string[]).includes(m[1])) claimed.add(m[1])
  }
  return [...claimed].sort()
}

// ── Truth sources ────────────────────────────────────────────────────────────

export interface TagDistribution {
  mandatory: number
  candidate: number
  untagged: number
  total: number
}

/** The writer's own floor-tag distribution, parsed from the FLOORS block. */
export function vidhiFloorTagDistribution(writerSource: string): TagDistribution {
  const block = writerSource.match(/^FLOORS = \[([\s\S]*?)^\]/m)
  if (!block) throw new Error('FLOORS block not found in bg_vidhi_floors.py')
  const starts = [...block[1].matchAll(/^\s*\(\s*["']([a-z_0-9]+)["']/gm)]
  if (starts.length === 0) throw new Error('no floor tuples found in FLOORS block')
  let mandatory = 0
  let candidate = 0
  for (let i = 0; i < starts.length; i++) {
    const segment = block[1].slice(
      starts[i].index,
      i + 1 < starts.length ? starts[i + 1].index : undefined,
    )
    const tags = [...segment.matchAll(/\[(MANDATORY|CANDIDATE)\]/g)].map(m => m[1])
    if (new Set(tags).size > 1) {
      throw new Error(`floor ${starts[i][1]} carries conflicting writer tags`)
    }
    if (tags[0] === 'MANDATORY') mandatory++
    else if (tags[0] === 'CANDIDATE') candidate++
  }
  return { mandatory, candidate, untagged: starts.length - mandatory - candidate, total: starts.length }
}

/** Writer-owned rule_type literal counts in l0_transit.py (F-145 boundary). */
export function transitWriterCounts(writerSource: string): { favourable: number; unfavourable: number } {
  const favourable = writerSource.match(/"rule_type": "favourable"/g)?.length ?? 0
  const unfavourable = writerSource.match(/"rule_type": "unfavourable"/g)?.length ?? 0
  if (favourable === 0 || unfavourable === 0) {
    throw new Error('rule_type literals not found in l0_transit.py — writer shape changed')
  }
  return { favourable, unfavourable }
}

/** Registered tag truth sources, keyed by asset_id. Fail-closed: a writer-tag
 *  claim on any other asset is a violation, not a skip. */
const TAG_TRUTH_BY_ASSET: Record<string, () => TagDistribution> = {
  bg_vidhi_floors: () => vidhiFloorTagDistribution(readFileSync(VIDHI_FLOORS_WRITER, 'utf8')),
}

/** Registered category-count truth sources, keyed by asset_id. */
const TRANSIT_TRUTH_BY_ASSET: Record<string, () => { favourable: number; unfavourable: number }> = {
  bg_transit_rules: () => transitWriterCounts(readFileSync(TRANSIT_WRITER, 'utf8')),
}

// ── Verification ─────────────────────────────────────────────────────────────

export function verifyDescriptionClaims(assetId: string, description: string): string[] {
  const violations: string[] = []

  const tagClaims = extractTagClaims(description)
  if (tagClaims.length > 0) {
    const truth = TAG_TRUTH_BY_ASSET[assetId]
    if (!truth) {
      violations.push(`${assetId}: writer-tag claim but no tag truth source is registered`)
    } else {
      const dist = truth()
      for (const claim of tagClaims) {
        if (claim.denominator !== dist.total) {
          violations.push(
            `${assetId}: claims a /${claim.denominator} denominator; the writer carries ${dist.total}`,
          )
        }
        const actual = claim.kind === 'MANDATORY' ? dist.mandatory
          : claim.kind === 'CANDIDATE' ? dist.candidate
            : dist.untagged
        if (claim.claimed !== actual) {
          violations.push(
            `${assetId}: claims ${claim.claimed}/${claim.denominator} ${claim.kind}; the writer source carries ${actual}/${dist.total}`,
          )
        }
      }
    }
  }

  const transitClaim = extractTransitClaim(description)
  if (transitClaim) {
    const truth = TRANSIT_TRUTH_BY_ASSET[assetId]
    if (!truth) {
      violations.push(`${assetId}: transit category-count claim but no count truth source is registered`)
    } else {
      const counts = truth()
      if (transitClaim.favourable !== counts.favourable) {
        violations.push(
          `${assetId}: claims ${transitClaim.favourable} favourable; the writer carries ${counts.favourable}`,
        )
      }
      if (transitClaim.unfavourable !== counts.unfavourable) {
        violations.push(
          `${assetId}: claims ${transitClaim.unfavourable} unfavourable; the writer carries ${counts.unfavourable}`,
        )
      }
      if (transitClaim.total !== transitClaim.favourable + transitClaim.unfavourable + transitClaim.doubleTransit) {
        violations.push(
          `${assetId}: total ${transitClaim.total} ≠ ${transitClaim.favourable}+${transitClaim.unfavourable}+${transitClaim.doubleTransit}`,
        )
      }
    }
  }

  const columnClaims = extractProvenanceColumnClaims(description)
  for (const column of columnClaims) {
    const writerPath = WRITER_BY_ASSET[assetId]
    if (!writerPath) {
      violations.push(`${assetId}: claims provenance column '${column}' but no writer is registered`)
      continue
    }
    const writer = readFileSync(writerPath, 'utf8')
    if (!writer.includes(column)) {
      violations.push(
        `${assetId}: description claims provenance column '${column}' but its writer never writes it`,
      )
    }
  }

  return violations
}

// ── The standing gate over the real corpus ───────────────────────────────────

const bgAssets = ASSETS.filter(a => a.asset_id.startsWith('bg_'))

describe('L0 description truthfulness (W-L0-5; the 642/1079 defect class)', () => {
  it('runs over exactly the 40 registered bg_* assets', () => {
    // Same measured anchor as l0_registry_parity.test.ts: 40 assets, production
    // and strategy §1.1 agree. The guard exists so the gate cannot silently
    // stop covering the corpus.
    expect(bgAssets).toHaveLength(40)
  })

  it('no bg_* description asserts a claim its source of truth contradicts', () => {
    const violations = bgAssets.flatMap(a =>
      verifyDescriptionClaims(a.asset_id, a.english_description ?? ''),
    )
    expect(violations).toEqual([])
  })

  it('bg_vidhi_floors: the repaired text matches the writer tag distribution 1/2/11 of 14', () => {
    const floors = bgAssets.find(a => a.asset_id === 'bg_vidhi_floors')
    expect(floors, 'bg_vidhi_floors must have a seed row').toBeDefined()
    const claims = extractTagClaims(floors!.english_description ?? '')
    // All three distribution claims must be present — a partial claim set is
    // how the 642 text hid ("12/14 [MANDATORY]" with no untagged accounting).
    expect(claims.map(c => c.kind).sort()).toEqual(['CANDIDATE', 'MANDATORY', 'UNTAGGED'])
    expect(vidhiFloorTagDistribution(readFileSync(VIDHI_FLOORS_WRITER, 'utf8'))).toEqual({
      mandatory: 1, candidate: 2, untagged: 11, total: 14,
    })
    expect(verifyDescriptionClaims('bg_vidhi_floors', floors!.english_description ?? '')).toEqual([])
  })

  it('bg_transit_rules: the category claim matches the writer-owned counts', () => {
    // Writer truth: 43 favourable + 26 unfavourable literals; the 7
    // double-transit rows are migration-397-owned (l0_transit.py F-145), so
    // 76 = 43+26+7 is the honest total against the writer boundary. Before the
    // 2026-09 L0 repair (b6690928f) the boundary was 75 and the live table's
    // 76th row was unresolved writer/production drift; the repair moved the 6
    // Rahu/Ketu UNSOURCED rows into the writer and inserted the Mercury
    // 8th-transit/1st-vedha pair, so writer and live table now agree at 76.
    const transit = bgAssets.find(a => a.asset_id === 'bg_transit_rules')
    expect(transit, 'bg_transit_rules must have a seed row').toBeDefined()
    expect(extractTransitClaim(transit!.english_description ?? '')).toEqual({
      total: 76, favourable: 43, unfavourable: 26, doubleTransit: 7,
    })
    expect(verifyDescriptionClaims('bg_transit_rules', transit!.english_description ?? '')).toEqual([])
  })
})

// ── Synthetic proofs that the detector bites (cannot rot vacuously) ──────────

describe('the detector itself', () => {
  it('catches the 642 defect verbatim', () => {
    const defect =
      'catalog_status=DRAFT is intentional, not stale: 12/14 intent floors are writer-tagged [MANDATORY] (settled), ' +
      'but education_deepdive and progeny_deepdive remain writer-tagged [CANDIDATE].'
    const violations = verifyDescriptionClaims('bg_vidhi_floors', defect)
    expect(violations.some(v => v.includes('claims 12/14 MANDATORY; the writer source carries 1/14'))).toBe(true)
    expect(violations.some(v => v.includes('claims 2/14 CANDIDATE') || v.includes('CANDIDATE'))).toBe(false)
  })

  it('fails closed on a writer-tag claim with no registered truth source', () => {
    const violations = verifyDescriptionClaims('bg_yogas', '3/10 entries are writer-tagged [MANDATORY].')
    expect(violations).toEqual([
      'bg_yogas: writer-tag claim but no tag truth source is registered',
    ])
  })

  it('catches a transit category lie and a broken total', () => {
    expect(
      verifyDescriptionClaims(
        'bg_transit_rules',
        '75 classical transit rules: 41 favourable, 26 unfavourable, and 7 double-transit rules.',
      ).some(v => v.includes('claims 41 favourable; the writer carries 43')),
    ).toBe(true)
    expect(
      verifyDescriptionClaims(
        'bg_transit_rules',
        '99 classical transit rules: 42 favourable, 26 unfavourable, and 7 double-transit rules.',
      ).some(v => v.includes('total 99 ≠ 42+26+7')),
    ).toBe(true)
  })

  it('fails closed on a provenance-column claim the writer does not write', () => {
    const violations = verifyDescriptionClaims(
      'bg_transit_rules',
      'Every row carries `qualification_state` provenance.',
    )
    expect(violations).toEqual([
      "bg_transit_rules: description claims provenance column 'qualification_state' but its writer never writes it",
    ])
  })

  it('accepts a provenance-column claim the writer does write', () => {
    // l0_transit.py writes classical_citation per row (the honest post-1079 shape).
    expect(
      verifyDescriptionClaims('bg_transit_rules', 'Per-row `classical_citation`, never table-wide.'),
    ).toEqual([])
  })

  it('fails closed on a provenance-column claim with no registered writer', () => {
    expect(
      verifyDescriptionClaims('bg_yogas', 'Rows carry `school`.'),
    ).toEqual([
      "bg_yogas: claims provenance column 'school' but no writer is registered",
    ])
  })
})
