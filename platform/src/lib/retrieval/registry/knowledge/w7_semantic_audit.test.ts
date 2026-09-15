import { existsSync, readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'
import snapshot from '../../../../generated/capability_knowledge.snapshot.json'

const repoRoot = resolve(import.meta.dirname, '../../../../../..')
const audit = JSON.parse(readFileSync(resolve(
  repoRoot,
  '00_ARCHITECTURE/briefs/nirmana/purna_anvesana/W7_SIX_LAYER_SEMANTIC_AUDIT_v1.json',
), 'utf8')) as {
  capability_knowledge_content_hash: string
  automated_results: Record<string, unknown>
  manual_samples: Array<{ layer: string; scu_id: string; verdict: string }>
}

function layerOf(scu: (typeof snapshot.scus)[number]): string | null {
  const match = scu.primary_binding_uri?.match(/\/L([0-5])\//)
  return match ? `L${match[1]}` : null
}

describe('Wave 7 six-layer semantic audit evidence', () => {
  it('pins the deterministic all-estate structural checks to the current snapshot', () => {
    const scuIds = new Set(snapshot.scus.map((scu) => scu.scu_id))
    const conceptIds = new Set(snapshot.concept_universe.map((concept) => concept.concept_id))
    const capabilityUris = new Set(snapshot.scus.flatMap((scu) => [
      ...scu.source_descriptor_uris,
      ...scu.bindings.map((binding) => binding.capability_uri),
    ]))
    let sourceRefsChecked = 0

    expect(audit.capability_knowledge_content_hash).toBe(snapshot.content_hash)
    expect(snapshot.scus).toHaveLength(182)
    for (const scu of snapshot.scus) {
      expect(scu.editorial).toBe(true)
      expect(scu.description.trim().length).toBeGreaterThan(0)
      expect(scu.domains.length).toBeGreaterThan(0)
      expect(scu.concepts.length).toBeGreaterThan(0)
      expect(scu.intents.length).toBeGreaterThan(0)
      expect(scu.outputs.length).toBeGreaterThan(0)
      expect(scu.concepts.every((concept) => conceptIds.has(concept))).toBe(true)
      for (const source of scu.editorial_sources) {
        sourceRefsChecked += 1
        if (source.source_ref.startsWith('platform/')) {
          const [file, anchor = ''] = source.source_ref.split('#', 2)
          expect(existsSync(resolve(repoRoot, file))).toBe(true)
          if (anchor) expect(readFileSync(resolve(repoRoot, file), 'utf8')).toContain(anchor.split(':').at(-1))
        } else {
          const uri = source.source_ref.replace(/^(CapabilityDescriptor|SemanticCapabilityDeclaration):/, '')
          expect(capabilityUris.has(uri)).toBe(true)
        }
      }
    }
    for (const edge of snapshot.edges) {
      expect(scuIds.has(edge.from_scu_id)).toBe(true)
      expect(scuIds.has(edge.to_scu_id)).toBe(true)
      expect(edge.source_ref?.length).toBeGreaterThan(0)
    }
    expect(sourceRefsChecked).toBe(358)
    expect(audit.automated_results).toMatchObject({
      editorial_scus: 182,
      descriptor_derived_stubs: 0,
      editorial_source_refs_checked: 358,
      unresolved_editorial_source_refs: 0,
      typed_concepts: 257,
      unbound_concept_uses: 0,
      semantic_edges: 53,
      invalid_edge_endpoints_or_sources: 0,
      verdict: 'PASS',
    })
  })

  it('pins the declared four-item deterministic manual sample in every layer', () => {
    const expected = Object.fromEntries(Array.from({ length: 6 }, (_, index) => {
      const layer = `L${index}`
      const stratum = snapshot.scus.filter((scu) => layerOf(scu) === layer)
        .sort((left, right) => left.scu_id.localeCompare(right.scu_id))
      const positions = [...new Set([0, Math.floor(stratum.length / 3), Math.floor(2 * stratum.length / 3), stratum.length - 1])]
      return [layer, positions.map((position) => stratum[position]?.scu_id)]
    }))
    const recorded = Object.fromEntries(Array.from({ length: 6 }, (_, index) => {
      const layer = `L${index}`
      return [layer, audit.manual_samples.filter((sample) => sample.layer === layer).map((sample) => sample.scu_id)]
    }))

    expect(recorded).toEqual(expected)
    expect(audit.manual_samples).toHaveLength(24)
    expect(audit.manual_samples.every((sample) => sample.verdict === 'PASS')).toBe(true)
  })
})
