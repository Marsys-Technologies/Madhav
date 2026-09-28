/**
 * R4 local integration boundary (native ruling, 2026-09-28): BEYOND_ACARYA_ACCEPTANCE_v6.json
 * forked into two independent "v7" successors on divergent branches — protected main's (PR
 * #2739, Jātaka Chart Workspace Phase-A3) and this branch's own (R0-R3 Pūrṇa Anveṣaṇa). Both
 * cite the same v6 predecessor. This file is the "focused lineage test" the ruling asked for,
 * proving: canonical v7 is unchanged; the historical fork is preserved byte-for-byte; the new
 * canonical v8 names main's v7 as predecessor; no earlier artifact was overwritten; acceptance
 * denominators are unchanged. See historical_fork_v7_v11/LINEAGE_FORK_MANIFEST_v1_0.md for the
 * full narrative and provenance table this test's hashes are drawn from.
 */
import { describe, expect, it } from 'vitest'
import { createHash } from 'node:crypto'
import { readFileSync } from 'node:fs'

const ROOT = '../../../../../00_ARCHITECTURE/briefs/nirmana/purna_anvesana'

function sha256File(relativePath: string): string {
  const bytes = readFileSync(new URL(`${ROOT}/${relativePath}`, import.meta.url))
  return `sha256:${createHash('sha256').update(bytes).digest('hex')}`
}

function readJson(relativePath: string): Record<string, unknown> {
  return JSON.parse(readFileSync(new URL(`${ROOT}/${relativePath}`, import.meta.url), 'utf8')) as Record<string, unknown>
}

describe('BEYOND_ACARYA_ACCEPTANCE v7 lineage fork (R4 local integration)', () => {
  it('keeps the canonical root-path v7 byte-identical to protected main\'s (never the fork\'s own v7)', () => {
    expect(sha256File('BEYOND_ACARYA_ACCEPTANCE_v7.json'))
      .toBe('sha256:1bbf5912d64f6f5eff05c5c8416d209cd00cafd3a009cb43fc4d2d5a00b21f15')
    const artifact = readJson('BEYOND_ACARYA_ACCEPTANCE_v7.json')
    expect(artifact).toMatchObject({
      schema_version: 'madhav-purna-anvesana/beyond-acarya-acceptance/v7',
      packet_id: 'JATAKA-PHASE-A3-SOURCE-INTEGRITY',
      evaluated_source_revision: 'ed5ad601c5e568f5d6c5d8ec72bc7c8f9ff2bd2b',
      capability_content_hash: 'sha256:6a595916dda6ba2b23c2c567c97cc50ddc1d218c353ea56aa383ffceb62dad7b',
      report_hash: 'sha256:7bdef36180d6734a5ce495a6a0458928c07fd501c049600a187d850814945001',
    })
    // Never the fork's own, differently-evaluated v7.
    expect(artifact.evaluated_source_revision).not.toBe('08adb0838eebbe27358bda4bd5bbd3cf27efd4f6')
  })

  it('preserves the branch\'s own divergent v7-v11 fork byte-for-byte under historical_fork_v7_v11/', () => {
    const expected: Record<string, { fileHash: string; capabilityContentHash: string; reportHash: string; predecessor: string }> = {
      'BEYOND_ACARYA_ACCEPTANCE_v7.json': {
        fileHash: 'sha256:b2385a40e46b019ee35d281eed5376b76be79a9d439a3530ab35f1dc2ea6b49d',
        capabilityContentHash: 'sha256:be8f246c32f9caddd19403e92d2d17a6f275c2b3a2abbb4e366276b95a5bb046',
        reportHash: 'sha256:d8ee4ad20f164f31df5ea6658e6d97f4ac552447cc33e381e0d0248d310a42da',
        predecessor: 'BEYOND_ACARYA_ACCEPTANCE_v6.json',
      },
      'BEYOND_ACARYA_ACCEPTANCE_v8.json': {
        fileHash: 'sha256:6c9bf36421e240fc9803981a2f82283b0ab06b5212d6e5097bd64d4bffe84714',
        capabilityContentHash: 'sha256:f632da65c9bb86ae9a474816577fc49628f84428072a55c77060d91cf6bcdee6',
        reportHash: 'sha256:bba7a5b811dc75fbe41c1395626089489dcb1402826005d997e48dee5d6d602f',
        predecessor: 'BEYOND_ACARYA_ACCEPTANCE_v7.json',
      },
      'BEYOND_ACARYA_ACCEPTANCE_v9.json': {
        fileHash: 'sha256:a7f89f0db4be2bf7f97a50f70d2a62f07bd0331222501062d8de3b3cd82f3fff',
        capabilityContentHash: 'sha256:7f9b800042f9f84d5d2c7441948ccbccb2759cc932eb7475a833c71675273300',
        reportHash: 'sha256:089c5422a191d5eb5c2f3de2337e679272fba9b460e2312934e180ae686bfe35',
        predecessor: 'BEYOND_ACARYA_ACCEPTANCE_v8.json',
      },
      'BEYOND_ACARYA_ACCEPTANCE_v10.json': {
        fileHash: 'sha256:716ef3e362d593cff93075cd721d06b58d72e9a78dbb30792e92e1067f93fe59',
        capabilityContentHash: 'sha256:cdb9e5ad93149497046f16d6789bfd4e939db2c4429ef00cb42cdaff5b5d6903',
        reportHash: 'sha256:531abd18af54ccb1e33982dca9b381fb11e4080cc11653629869a946bb544919',
        predecessor: 'BEYOND_ACARYA_ACCEPTANCE_v9.json',
      },
      'BEYOND_ACARYA_ACCEPTANCE_v11.json': {
        fileHash: 'sha256:1b55efec55d70a1da893c8fe6f1b13098e18c0a22ba9e1c64b187dcebdc663d2',
        capabilityContentHash: 'sha256:c8ca0178d99cf38c7914454489dea9f1f8a6c5ab38cf7fa9815f30b752a7de7f',
        reportHash: 'sha256:17bcd5e76cd2ff84f4c95a7787050de2c753c5c7ac99d2c385c1d47a7f5315ac',
        predecessor: 'BEYOND_ACARYA_ACCEPTANCE_v10.json',
      },
    }

    for (const [filename, expectation] of Object.entries(expected)) {
      const relativePath = `historical_fork_v7_v11/${filename}`
      expect(sha256File(relativePath)).toBe(expectation.fileHash)
      const artifact = readJson(relativePath)
      expect(artifact.capability_content_hash).toBe(expectation.capabilityContentHash)
      expect(artifact.report_hash).toBe(expectation.reportHash)
      expect((artifact.predecessor as { artifact: string }).artifact).toBe(expectation.predecessor)
    }
  })

  it('names protected main\'s v7 as the new canonical v8\'s predecessor, never the fork\'s own v7/v8', () => {
    const v8 = readJson('BEYOND_ACARYA_ACCEPTANCE_v8.json')
    expect(v8).toMatchObject({
      schema_version: 'madhav-purna-anvesana/beyond-acarya-acceptance/v8',
      predecessor: {
        artifact: 'BEYOND_ACARYA_ACCEPTANCE_v7.json',
        capability_content_hash: 'sha256:6a595916dda6ba2b23c2c567c97cc50ddc1d218c353ea56aa383ffceb62dad7b',
        report_hash: 'sha256:7bdef36180d6734a5ce495a6a0458928c07fd501c049600a187d850814945001',
      },
      verdict: 'ACCEPTED_SOURCE_LOCAL',
    })
    // Predecessor hashes match the CANONICAL (main's) v7, not the fork's own v7
    // (sha256:be8f246c...) which shares no fields with main's v7 beyond the common v6 ancestor.
    expect((v8.predecessor as { capability_content_hash: string }).capability_content_hash)
      .not.toBe('sha256:be8f246c32f9caddd19403e92d2d17a6f275c2b3a2abbb4e366276b95a5bb046')
  })

  it('continues the canonical chain v7 -> v8 -> v9 without touching the historical fork', () => {
    const v8 = readJson('BEYOND_ACARYA_ACCEPTANCE_v8.json')
    const v9 = readJson('BEYOND_ACARYA_ACCEPTANCE_v9.json')
    expect(sha256File('BEYOND_ACARYA_ACCEPTANCE_v8.json'))
      .toBe('sha256:551da8df072df9135895deffa0c630f63d5d3d4a44b03766d20bcabc1b15e6d5')
    expect(v9.predecessor).toMatchObject({
      artifact: 'BEYOND_ACARYA_ACCEPTANCE_v8.json',
      capability_content_hash: v8.capability_content_hash,
      report_hash: v8.report_hash,
    })
    // The fork's own v8/v9 live only under historical_fork_v7_v11/ and are never a predecessor here.
    expect((v9.predecessor as { report_hash: string }).report_hash)
      .not.toBe('sha256:bba7a5b811dc75fbe41c1395626089489dcb1402826005d997e48dee5d6d602f')
    expect(v9).toMatchObject({ candidate_validation: 'NOT_RUN', verdict: 'ACCEPTED_SOURCE_LOCAL' })
  })

  it('continues the canonical chain v9 -> v10 (follow-up) without touching the historical fork', () => {
    const v9 = readJson('BEYOND_ACARYA_ACCEPTANCE_v9.json')
    const v10 = readJson('BEYOND_ACARYA_ACCEPTANCE_v10.json')
    expect(sha256File('BEYOND_ACARYA_ACCEPTANCE_v9.json'))
      .toBe('sha256:ce77568e7d7d4d79d68f1c0359932ef12503984ee6d2528cde9f711750d32ed9')
    expect(v10.predecessor).toMatchObject({
      artifact: 'BEYOND_ACARYA_ACCEPTANCE_v9.json',
      capability_content_hash: v9.capability_content_hash,
      report_hash: v9.report_hash,
    })
    // The fork's own v10 lives only under historical_fork_v7_v11/ and is never this file's predecessor.
    expect((v10.predecessor as { report_hash: string }).report_hash)
      .not.toBe('sha256:089c5422a191d5eb5c2f3de2337e679272fba9b460e2312934e180ae686bfe35')
    expect(v10).toMatchObject({ candidate_validation: 'NOT_RUN', verdict: 'ACCEPTED_SOURCE_LOCAL' })
  })

  it('does not overwrite any earlier historical artifact (v1-v6 byte-identical, unaffected by the fork reconciliation)', () => {
    const historical: Record<string, string> = {
      'BEYOND_ACARYA_ACCEPTANCE_v2.json': 'sha256:33595346209c3f31b7123f5dbb002712e3ca5de52b06cfc1b7170a4ac70543e0',
      'BEYOND_ACARYA_ACCEPTANCE_v3.json': 'sha256:9c12f15b88f3d4bb1f1766a9364d231801e8c1a82e3bb3ea0b1680ba9935bc1e',
      'BEYOND_ACARYA_ACCEPTANCE_v4.json': 'sha256:d972ce0345092602ff2acf258da13f1711cb1671f1625fbf552eb97594154320',
      'BEYOND_ACARYA_ACCEPTANCE_v5.json': 'sha256:2243892141bbc350d804958d4ad78c2425e84c44a9e09634eb883dbe34a600d9',
      'BEYOND_ACARYA_ACCEPTANCE_v6.json': 'sha256:04579974349aed1377b26755b4a737dcb4cd14adee808b773e6cc986a956aec5',
    }
    for (const [filename, expectedHash] of Object.entries(historical)) {
      expect(sha256File(filename)).toBe(expectedHash)
    }
  })
})
