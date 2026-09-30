// RETIRED (skipped): Nirmana is superseded by Suvarna (NIRMANA-SUPERSESSION). These pins fail on ANY writer change by any
// workstream, so they only taxed every PR to protect a retired campaign. Runtime code and the pins data are untouched.
import { createHash } from 'node:crypto'
import { describe, expect, it } from 'vitest'
import writerDigestInventory from '../nirmana-writer-digests.json'
import layerPinRecord from '../nirmana-analysis-layer-pins.json'
import {
  NIRMANA_ANALYSIS_LAYERS,
  NIRMANA_ANALYSIS_LAYER_PINS,
  NIRMANA_ANALYSIS_RECEIPT_HISTORY,
  NIRMANA_ANALYSIS_RECEIPTS,
  assertNirmanaWriterInventoryMatchesConvergence,
  getNirmanaAnalysisReceiptBase,
  getHistoricalNirmanaAnalysisReceiptBase,
  nirmanaAnalysisReceiptsAvailable,
  type NirmanaAnalysisLayer,
} from '../nirmana-analysis-receipts'
import {
  NIRMANA_L0_ANALYSIS_RECEIPTS,
} from '../nirmana-l0-analysis-receipts'

const writerDigests = writerDigestInventory.writers as Record<string, string>

describe.skip('nirmana analysis receipt spine (all layers)', () => {
  it('produces the pinned receipt count for every layer', () => {
    for (const layer of NIRMANA_ANALYSIS_LAYERS) {
      expect(nirmanaAnalysisReceiptsAvailable(layer)).toBe(true)
      expect(Object.keys(NIRMANA_ANALYSIS_RECEIPTS[layer]))
        .toHaveLength(NIRMANA_ANALYSIS_LAYER_PINS[layer].receipt_count)
    }
  })

  it('binds the layer into every receipt base, so a base cannot cross layers', () => {
    for (const layer of NIRMANA_ANALYSIS_LAYERS) {
      for (const base of Object.values(NIRMANA_ANALYSIS_RECEIPTS[layer])) {
        expect(base.layer).toBe(layer)
        expect(base.grounding.convergence_commit)
          .toBe(NIRMANA_ANALYSIS_LAYER_PINS[layer].convergence_commit)
      }
    }
  })

  it('refuses to resolve a real asset under the wrong layer', () => {
    // ga_positions genuinely exists -- but only as an L1 receipt base.
    expect(getNirmanaAnalysisReceiptBase('ga_positions', 'L1')).toBeDefined()
    expect(getNirmanaAnalysisReceiptBase('ga_positions', 'L2')).toBeUndefined()
    expect(getNirmanaAnalysisReceiptBase('bg_prashna_rules', 'L0')).toBeDefined()
    expect(getNirmanaAnalysisReceiptBase('bg_prashna_rules', 'L1')).toBeUndefined()
  })

  it('re-derives each layer aggregate from the live inventory, so a hand-edited pin fails', () => {
    for (const layer of NIRMANA_ANALYSIS_LAYERS) {
      const { asset_prefix, writer_inventory_sha256 } = NIRMANA_ANALYSIS_LAYER_PINS[layer]
      const slice = Object.fromEntries(Object.entries(writerDigests)
        .filter(([assetId]) => assetId.startsWith(asset_prefix))
        .sort(([left], [right]) => left.localeCompare(right)))
      expect(createHash('sha256').update(JSON.stringify(slice)).digest('hex'))
        .toBe(writer_inventory_sha256)
    }
  })

  it('fails closed for the drifted layer ONLY, never globally', () => {
    // Substituting one L1 writer digest must invalidate L1 and leave L0 valid.
    const drifted = { ...writerDigests, ga_positions: '0'.repeat(64) }
    expect(() => assertNirmanaWriterInventoryMatchesConvergence('L1', drifted))
      .toThrow(/L1 writer inventory/i)
    expect(() => assertNirmanaWriterInventoryMatchesConvergence('L0', drifted))
      .not.toThrow()
  })

  it('every layer carries a distinct aggregate, which is what makes per-layer isolation real', () => {
    const aggregates = NIRMANA_ANALYSIS_LAYERS
      .map((layer) => NIRMANA_ANALYSIS_LAYER_PINS[layer].writer_inventory_sha256)
    expect(new Set(aggregates).size).toBe(NIRMANA_ANALYSIS_LAYERS.length)
  })
})

describe.skip('L0 preservation and versioned supersession (DP-SD-018)', () => {
  it('keeps the prior L0 receipt bases byte-reconstructable after successor admission', () => {
    // Hardcoded here on purpose: this test is the detector for "no L0 capsule is
    // re-accepted, and no UNRATIFIED re-pin lands silently". Deriving these from
    // the same record the implementation reads would make it assert nothing.
    //
    // writer_inventory_sha256 updated 2026-09-06 (D-NATIVE-06, native-ratified
    // transparent re-derivation): bg_yogas's writer was fixed (a dict-row-as-tuple
    // bug silently yielded 0 corpus-extracted yogas on every real dispatch), which
    // changes bg_yogas's own writer digest and therefore the L0 aggregate. Verified
    // before this update: regenerating the writer-digest inventory changed exactly
    // one entry (bg_yogas); all other 35 frozen L0 writers' digests are
    // byte-identical to before, and this aggregate is not part of any per-asset
    // NirmanaAnalysisReceiptBase (see buildLayerReceipts in
    // nirmana-analysis-receipts.ts), so no other asset's already-accepted
    // analysis_digest is affected. convergence_commit and receipt_count are
    // unchanged -- this re-pin touches exactly the one value that changed.
    //
    // Updated again 2026-09-07 (issue #2122, F-D21/F-D23): bg_vidhi_primitives.py's
    // from_moon_view entry corrected (inert reference_point arg -> the real
    // ganita_transit_anchors_get consumer). Same discipline: regenerating the
    // inventory changed exactly one entry (bg_vidhi_primitives); all other 35
    // frozen L0 writers (bg_yogas included) are byte-identical to the prior re-pin.
    const generation = 'l0:49bb5c98b864:5125cccb6871'
    const historicalReceipts = NIRMANA_ANALYSIS_RECEIPT_HISTORY.L0[generation]
    expect(Object.keys(historicalReceipts)).toHaveLength(40)
    expect(createHash('sha256').update(JSON.stringify(historicalReceipts)).digest('hex'))
      .toBe('bac97201ca2b3ecc070459b54e83d970c904bef3149f37823f231624a0858d2a')
    expect(historicalReceipts.bg_prashna_rules).toEqual({
      schema_version: 'nirmana-asset-analysis-receipt-base/v1',
      asset_id: 'bg_prashna_rules',
      layer: 'L0',
      writer_digest_sha256: '07b6ac8065abbcfb98cc76ea37dc7c32ad7a4f7edcafe8c08ccf35b15c3db6eb',
      grounding: {
        convergence_commit: '49bb5c98b864a2cb2fee037cdb7f14f6892a8263',
        frozen_manifest_source: 'nirmana_elevation_campaign_definitions.manifest',
        writer_digest_ref: 'platform/src/generated/nirmana-writer-digests.json',
      },
    })
    expect(getHistoricalNirmanaAnalysisReceiptBase('bg_prashna_rules', 'L0', generation))
      .toEqual(historicalReceipts.bg_prashna_rules)
    expect(getHistoricalNirmanaAnalysisReceiptBase('ga_positions', 'L0', generation))
      .toBeUndefined()
  })

  it('serves the identical L0 bases through the deprecated shim and the generic module', () => {
    expect(NIRMANA_L0_ANALYSIS_RECEIPTS).toEqual(NIRMANA_ANALYSIS_RECEIPTS.L0)
  })

  it('admits the L0-repair successors for exactly L0, L2 and L3, append-only', () => {
    const decision = 'NATIVE-2026-09-24-L0-REPAIR-REPIN'
    // approval identity vs pinned source are different commits on purpose: the inventory at
    // the approved state was stale, so the source is the commit that regenerates it
    // (L0_REPAIR_ANALYSIS_REPIN_DECISION_ADDENDUM_v1_0.md)
    const approved = '101171f76517fa3c6b0b44fa9d1cc46358612eee'
    const source = '7d40f8c706406ee8187eadb5c3930553800a1a4a'
    const expected = {
      L0: { generation: 'l0:7d40f8c70640:64b8859fe692', supersedes: 'l0:d2369b888e76:3dda261170ee', changed: 9, history: 2 },
      L2: { generation: 'l2:7d40f8c70640:dbbbb24c09cb', supersedes: 'l2:149f8479ac4e:51d3164426ac', changed: 23, history: 3 },
      L3: { generation: 'l3:7d40f8c70640:dfcf30d8b3d2', supersedes: 'l3:87cc8c9baf89:002a118b218e', changed: 6, history: 5 },
    } as const
    for (const layer of ['L0', 'L2', 'L3'] as const) {
      // L0 and L2 repair successors are still the live pins. On L3 the later
      // D-E022 merge readmission successor (PR #2731) and the D-PINS-A2
      // successor (pravaha/a2-kernel-geometry, Pravaha A2.3) are live after
      // it, so the repair successor is the archived entry at -2. Every
      // assertion is unchanged, only rebased onto that entry.
      const pin = layer === 'L3'
        ? layerPinRecord.history.L3.at(-2)!.pin
        : layerPinRecord.layers[layer]
      const want = expected[layer]
      expect(pin.generation_id).toBe(want.generation)
      expect(pin.supersedes_generation_id).toBe(want.supersedes)
      expect(pin.convergence_commit).toBe(source)
      expect(pin.admission?.authority_decision).toBe(decision)
      expect(pin.admission?.authority_commit).toBe(approved)
      expect(pin.admission?.source_commit).toBe(source)
      expect(pin.admission?.changed_assets).toHaveLength(want.changed)
      expect(Object.keys(pin.admission?.delta_classifications ?? {})).toEqual(pin.admission?.changed_assets)
      expect(Object.values(pin.admission?.delta_classifications ?? {})).not.toContain('unapproved_foreign_source')
      // the predecessor is archived whole, and named by the successor
      const archived = layer === 'L3'
        ? layerPinRecord.history.L3.at(-3)!
        : layerPinRecord.history[layer].at(-1)!
      expect(archived.generation_id).toBe(want.supersedes)
      expect(archived.superseded_by_generation_id).toBe(want.generation)
      expect(layerPinRecord.history[layer]).toHaveLength(layer === 'L3' ? 6 : want.history)
    }
    // L4 is untouched by both the L0 repair and the D-E022 readmission. L1 and
    // L3 now carry the later D-E022 merge readmission successors (asserted in
    // the D-E022 test below). L5 has one later, independently authorized
    // CCD-018 successor, asserted below.
    expect(layerPinRecord.history.L4).toHaveLength(1)
    expect(layerPinRecord.history.L5).toHaveLength(1)
    // the predecessors' receipts stay re-derivable from the archived generation
    expect(Object.keys(NIRMANA_ANALYSIS_RECEIPT_HISTORY.L2)).toContain('l2:149f8479ac4e:51d3164426ac')
    expect(Object.keys(NIRMANA_ANALYSIS_RECEIPT_HISTORY.L3)).toContain('l3:87cc8c9baf89:002a118b218e')
    expect(Object.keys(NIRMANA_ANALYSIS_RECEIPT_HISTORY.L0)).toContain('l0:d2369b888e76:3dda261170ee')
  })

  it('keeps the four L0 non-writer assets receipt-addressable', () => {
    for (const assetId of layerPinRecord.layers.L0.non_writer_assets) {
      const base = getNirmanaAnalysisReceiptBase(assetId, 'L0' as NirmanaAnalysisLayer)
      expect(base).toBeDefined()
      expect(base?.writer_digest_sha256).toBeNull()
    }
  })

  it('preserves prior ruled successors and admits only the DP-SD-019 L3 delta', () => {
    const priorL2 = layerPinRecord.history.L2[1].pin
    const priorL2Admission = priorL2.admission!
    expect(new Set(Object.values(priorL2Admission.delta_classifications))).toEqual(
      new Set(['approved_intentional_and_derived_import_change']),
    )
    expect(priorL2Admission.review_artifacts.map(({ path }) => path)).toEqual([
      '00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_L2_PRODUCER_READY_ACCEPTANCE_v1_0.md',
      '00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_L3_W2_FIRST_FRONTIER_SOURCE_v1_0.md',
    ])
    const priorL3 = layerPinRecord.history.L3[1].pin
    expect(priorL3.admission?.changed_assets).toEqual(['ka_sangam'])
    expect(priorL3.admission?.delta_classifications).toEqual({
      ka_sangam: 'derived_import_change',
    })
    const priorYojaka = layerPinRecord.history.L3[2].pin
    expect(priorYojaka.admission?.changed_assets).toEqual(['ka_yojaka'])
    expect(priorYojaka.admission?.delta_classifications).toEqual({
      ka_yojaka: 'approved_intentional_change',
    })
    expect(priorYojaka.admission?.source_commit)
      .toBe('64facb9763d13eece7098b5b24cc03dfb8e3ba81')
    expect(priorYojaka.admission?.review_artifacts).toEqual([{
      commit: '64facb9763d13eece7098b5b24cc03dfb8e3ba81',
      decision_binding: 'status: SOURCE_PACKET_ACCEPTED',
      path: '00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_DP019_SOURCE_ACCEPTANCE_v1_0.md',
      sha256: 'a24f4ad257d755359dd82d3ad52af928f74d625aaf183f2638c5ec08f07858c5',
    }])
    // The Kshetra (DP-SD-019) successor was the active L3 pin when this was written; the
    // L0-repair successor (PR #2727) and the D-E022 merge readmission (PR #2731) are now
    // appended after it, so it is an archived entry. Every assertion below is unchanged,
    // only rebased onto that entry.
    const kshetraL3 = layerPinRecord.history.L3[3].pin
    expect(kshetraL3.generation_id).toBe('l3:87cc8c9baf89:002a118b218e')
    expect(kshetraL3.admission?.changed_assets).toEqual(['ka_kshetra'])
    expect(kshetraL3.admission?.delta_classifications).toEqual({
      ka_kshetra: 'approved_intentional_change',
    })
    expect(kshetraL3.admission?.authority_decision).toBe('DP-SD-019')
    expect(kshetraL3.admission?.source_commit)
      .toBe('87cc8c9baf894c615e167672c6c7af57a15cf71c')
    expect(kshetraL3.admission?.review_artifacts).toEqual([{
      commit: '58b7d455d803c54238bdae050c1770f9f514d21e',
      decision_binding: 'status: SOURCE_PACKET_ACCEPTED',
      path: '00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_DP019_KSHETRA_GATE_ACCEPTANCE_v1_0.md',
      sha256: '687eed0309e906730364a394fb674ebac17ce58220309308bfcf071ac972175d',
    }])
    expect(layerPinRecord.history.L3).toHaveLength(6)
    expect(layerPinRecord.layers.L4.admission.delta_classifications).toEqual({
      ph_muhurta: 'derived_import_change',
      ph_rectification: 'derived_import_change',
    })
    expect(layerPinRecord.layers.L4.admission.review_artifacts).toEqual([{
      commit: 'f6fed12c794224329f6b3b436f8b1b814499d06d',
      decision_binding: 'status: VALIDATED_INDEPENDENT_CHALLENGE_PASS',
      path: '00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_L0_SWISS_STATE_BOUNDARY_VALIDATION_v1_0.md',
      sha256: '0f87dc072590179cc9a5e8b928bf30a0436de5d13b3d1e9ed4c20ce31aceee79',
    }])
    // L5 was untouched by the L0 repair. The later Jataka context-staleness
    // changes are a separate CCD-018 successor: the original L5 pin is archived
    // whole, membership remains unchanged, and exactly the four reviewed writer
    // identities are classified.
    const l5 = layerPinRecord.layers.L5
    expect(l5.generation_id).toBe('l5:ed5ad601c5e5:9d222087056d')
    expect(l5.supersedes_generation_id).toBe('l5:fd4c102e3ce5:df295e3ac158')
    expect(l5.convergence_commit).toBe('ed5ad601c5e568f5d6c5d8ec72bc7c8f9ff2bd2b')
    expect(l5.non_writer_assets).toEqual(['lel_events'])
    expect(l5.receipt_count).toBe(15)
    expect(l5.writer_inventory_sha256)
      .toBe('9d222087056d2133991c52a53ca48ee20cafe06f5c9d3401565ad9e2436e99db')
    expect(l5.admission.authority_decision).toBe('CCD-018')
    expect(l5.admission.authority_commit)
      .toBe('463c1dd66796356380fe2cab3103ad68b0d08d21')
    expect(l5.admission.changed_assets).toEqual([
      'mi_bhara', 'mi_gunanaka', 'mi_pariksha', 'mi_pramana',
    ])
    expect(new Set(Object.values(l5.admission.delta_classifications)))
      .toEqual(new Set(['approved_intentional_change']))
    expect(l5.admission.review_artifacts).toEqual([{
      commit: 'a97fc8ffb0268954fb4bf8c7fb7e838c4bf6e558',
      decision_binding: '**Reviewed technical head:** `ed5ad601c5e568f5d6c5d8ec72bc7c8f9ff2bd2b`.',
      path: '00_ARCHITECTURE/SESSION_LOG.md',
      sha256: '78273beef6032e0216916167f52b943e49605d6e11a7248f626d2b3205bf779f',
    }])
    const archivedL5 = layerPinRecord.history.L5[0]
    expect(archivedL5.generation_id).toBe('l5:fd4c102e3ce5:df295e3ac158')
    expect(archivedL5.superseded_by_generation_id).toBe(l5.generation_id)
    expect(archivedL5.historical_snapshot_commit)
      .toBe('6b26f3ff05ee0aba3cdd964bce62292496ae6b62')
    expect(Object.keys(NIRMANA_ANALYSIS_RECEIPT_HISTORY.L5))
      .toContain('l5:fd4c102e3ce5:df295e3ac158')
  })

  it('admits only the exact SECURITY CLEAR L1/L2 compatibility closure', () => {
    const expectedSourceAcceptance = {
      common_base_commit: '5142109f7f219ea860f859e322646f79d875bee8',
      integrated_equivalent_commit: 'd22533825613c3d428bd844a5dfdc2c0c283b088',
      reviewed_source_commit: 'da498ebd980cac87796eceb889c7f1c42cfb952b',
      schema_version: 'nirmana-analysis-source-acceptance/v1',
      source_surface_sha256: '59a1845b74fb0777274f18b876de0ddae3ac873cea95e405f959d1163ad4d876',
    }
    const expectedReviewedPaths = [
      '.github/workflows/deploy.yml',
      '00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_RI02_SECURITY_CUTOVER_v1_0.md',
      'platform/package-lock.json',
      'platform/package.json',
      'platform/pnpm-lock.yaml',
      'platform/python-sidecar/bodha_writers/_idempotency.py',
      'platform/python-sidecar/ga_writers/_idempotency.py',
      'platform/python-sidecar/ga_writers/ga_condition_writer.py',
      'platform/python-sidecar/ga_writers/ga_dashas_writer.py',
      'platform/python-sidecar/pipeline/dispatcher.py',
      'platform/python-sidecar/tests/test_bodha_idempotency.py',
      'platform/python-sidecar/tests/test_ga_idempotency.py',
      'platform/scripts/data-plane-cutover-preflight.ts',
      'platform/scripts/data-plane-migration-attestation.ts',
      'platform/scripts/data-plane-ownership-preflight.ts',
      'platform/scripts/data-plane-ownership-status.ts',
      'platform/scripts/data-plane-protected-cutover.ts',
      'platform/scripts/data-plane-secret-isolation-preflight.ts',
      'platform/scripts/migrate.ts',
      'platform/supabase/migrations/1035_data_plane_l1_producer_history.sql',
      'platform/supabase/migrations/1036_data_plane_l2_producer_generations.sql',
      'platform/tests/integration/data_plane_protected_roles.db.test.ts',
      'platform/tests/unit/data_plane_security_contract.test.ts',
    ]
    // The L1 security successor was active when this was written; the D-E022 merge
    // readmission (PR #2731) now follows it, so it is the archived predecessor. The
    // L2 security successor was active when this was written; the L0-repair
    // successor (PR #2727) now follows it, so it is the archived predecessor.
    const securityL1 = layerPinRecord.history.L1[2].pin
    const securityL2 = layerPinRecord.history.L2[2].pin
    expect(securityL1.generation_id).toBe('l1:149f8479ac4e:93de3b2c84b7')
    expect(securityL2.generation_id).toBe('l2:149f8479ac4e:51d3164426ac')
    expect(securityL1.admission.changed_assets).toEqual([
      'ga_ayurdaya', 'ga_condition', 'ga_dashas', 'ga_nakshatra', 'ga_panchanga',
      'ga_positions', 'ga_sade_sati', 'ga_sensitive', 'ga_sensitive_degree',
      'ga_strength', 'ga_structural', 'ga_tajaka', 'ga_vargas', 'ga_yoga',
    ])
    expect(securityL2.admission?.changed_assets).toEqual([
      'bo_arudha', 'bo_bimba', 'bo_grounding', 'bo_karanajala', 'bo_laksana',
      'bo_laksana_rerank', 'bo_nakshatra_semantic', 'bo_pramana_mapa',
      'bo_samskara', 'bo_sangati', 'bo_special_lagna', 'bo_sudarshana',
      'bo_upaya', 'bo_vargottama_dhana',
    ])
    for (const acceptance of [
      securityL1.admission.source_acceptance,
      securityL2.admission?.source_acceptance,
    ]) {
      expect(acceptance).toMatchObject(expectedSourceAcceptance)
      expect(acceptance!.reviewed_surface.map(item => item.path)).toEqual(expectedReviewedPaths)
      expect(acceptance!.reviewed_surface).toHaveLength(23)
      expect(acceptance!.reviewed_surface.every(item => /^[a-f0-9]{40}$/.test(item.blob_oid))).toBe(true)
    }
    expect(securityL1.admission.review_artifacts).toEqual(
      securityL2.admission?.review_artifacts,
    )
    expect(securityL1.admission.review_artifacts[0]).toEqual({
      commit: '149f8479ac4e22874aabe9a5e5b340fb86bc16fb',
      decision_binding: 'status: SECURITY_CLEAR_SOURCE_ACCEPTED',
      path: '00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_RI02_SECURITY_SOURCE_ACCEPTANCE_v1_0.md',
      sha256: '94cbe76aff7d1a15d5efd1d3f355a6f49a6af49fafc14edf7b708bb8f454c084',
    })
    expect(layerPinRecord.history.L1).toHaveLength(3)
    expect(layerPinRecord.history.L2).toHaveLength(3)
    expect(Object.keys(NIRMANA_ANALYSIS_RECEIPT_HISTORY.L1)).toContain(
      'l1:d2369b888e76:3e8816fc708a',
    )
    expect(Object.keys(NIRMANA_ANALYSIS_RECEIPT_HISTORY.L2)).toContain(
      'l2:d2369b888e76:ad143c22bd8d',
    )
    const priorL1Receipts = NIRMANA_ANALYSIS_RECEIPT_HISTORY.L1[
      'l1:d2369b888e76:3e8816fc708a'
    ]
    const priorL2Receipts = NIRMANA_ANALYSIS_RECEIPT_HISTORY.L2[
      'l2:d2369b888e76:ad143c22bd8d'
    ]
    expect(Object.keys(priorL1Receipts)).toHaveLength(19)
    expect(Object.keys(priorL2Receipts)).toHaveLength(22)
    expect(createHash('sha256').update(JSON.stringify(priorL1Receipts)).digest('hex'))
      .toBe('b3aca5b72855a472ab9cdb819e69f9012ab1eea380aa03eeb2605fb7f3fbaa57')
    expect(createHash('sha256').update(JSON.stringify(priorL2Receipts)).digest('hex'))
      .toBe('e3dbe7017b66f003a703d5a3e163941ea425b571c923f70e4238b8155b9d2ee5')
  })

  it('admits the D-E022 merge readmission successors for exactly L1 and L3, append-only', () => {
    // PR #2731 / Pravaha A0.3: the origin/main merge moved L1 and L3 writer
    // digests (membership unchanged). Re-admission authorised by the native
    // (D-E022) per MERGE_HYGIENE_12_10c_RUNBOOK step 2. Authority identity and
    // pinned source are different commits on purpose: the source is the
    // origin/main merge commit on the lane, whose committed writer inventory
    // equals the merged tree's inventory. A0.6 delivery re-base: the merge
    // queue squashes #2731 onto main, so the A0.3 lane-local admission shape
    // (one L1 successor, two L3 successors) could never name deliverable
    // historical snapshots; both layers were rewound to the protected baseline
    // byte-for-byte and re-admitted ONCE each, the L3 admission carrying the
    // exact union of the two withdrawn lane-local deltas. The lane-local
    // generation l3:f4cba9d606ab:64ca6e06c175 never reached main.
    // Evidence: 00_ARCHITECTURE/briefs/nirmana/l3_autonomous/gochara_wp0_7/D_E022_PINS_READMISSION_AUTHORITY_v1_0.md
    const decision = 'D-E022'
    const authority = '442f1ed955a701008b2a975c7df80d543fbbc67a'
    const source = '333eb7abcac33deefa4f89dc417e73d4f28d74bd'
    const expected = {
      L1: { generation: 'l1:333eb7abcac3:b3674dfbfa91', supersedes: 'l1:149f8479ac4e:93de3b2c84b7', changed: 6, history: 3 },
      L3: { generation: 'l3:333eb7abcac3:d1bf773c4d94', supersedes: 'l3:7d40f8c70640:dfcf30d8b3d2', changed: 7, history: 5 },
    } as const
    for (const layer of ['L1', 'L3'] as const) {
      // On L3 the D-PINS-A2 successor (pravaha/a2-kernel-geometry, Pravaha
      // A2.3) is live after the D-E022 successor, so the D-E022 pin is the
      // archived entry at -1 and its own predecessor sits at -2. On L1 the
      // D-E022 successor is still the live pin. Assertions unchanged, only
      // rebased.
      const pin = layer === 'L3'
        ? layerPinRecord.history.L3.at(-1)!.pin
        : layerPinRecord.layers[layer]
      const want = expected[layer]
      expect(pin.generation_id).toBe(want.generation)
      expect(pin.supersedes_generation_id).toBe(want.supersedes)
      expect(pin.convergence_commit).toBe(source)
      expect(pin.admission?.authority_decision).toBe(decision)
      expect(pin.admission?.authority_commit).toBe(authority)
      expect(pin.admission?.source_commit).toBe(source)
      expect(pin.admission?.changed_assets).toHaveLength(want.changed)
      expect(Object.keys(pin.admission?.delta_classifications ?? {})).toEqual(pin.admission?.changed_assets)
      expect(Object.values(pin.admission?.delta_classifications ?? {})).not.toContain('unapproved_foreign_source')
      const archived = layer === 'L3'
        ? layerPinRecord.history.L3.at(-2)!
        : layerPinRecord.history[layer].at(-1)!
      expect(archived.generation_id).toBe(want.supersedes)
      expect(archived.superseded_by_generation_id).toBe(want.generation)
      expect(layerPinRecord.history[layer]).toHaveLength(layer === 'L3' ? 6 : want.history)
    }
    // every other layer is untouched by the readmission
    expect(layerPinRecord.layers.L0.generation_id).toBe('l0:7d40f8c70640:64b8859fe692')
    expect(layerPinRecord.layers.L2.generation_id).toBe('l2:7d40f8c70640:dbbbb24c09cb')
    expect(layerPinRecord.layers.L4.generation_id).toBe('l4:d2369b888e76:e73988c0dd03')
    expect(layerPinRecord.layers.L5.generation_id).toBe('l5:ed5ad601c5e5:9d222087056d')
    // the classified causes, recorded per asset
    expect(layerPinRecord.layers.L1.admission?.delta_classifications).toEqual({
      ga_ayurdaya: 'derived_import_change',
      ga_sensitive: 'approved_intentional_change',
      ga_sensitive_degree: 'derived_import_change',
      ga_strength: 'approved_intentional_change',
      ga_structural: 'derived_import_change',
      ga_yoga: 'derived_import_change',
    })
    // the live L3 admission carries the union of both withdrawn lane-local
    // deltas: the merge delta and the knots.py (DP-SD-010) cascade — archived
    // at -1 since the D-PINS-A2 successor (A2.3) became the live L3 pin
    expect(layerPinRecord.history.L3.at(-1)!.pin.admission?.delta_classifications).toEqual({
      ka_gochara: 'derived_import_change',
      ka_gochara_resonance: 'approved_intentional_and_derived_import_change',
      ka_gochara_v3_century_materialize: 'approved_intentional_and_derived_import_change',
      ka_kshetra: 'approved_intentional_and_derived_import_change',
      ka_moorti_nirnaya: 'approved_intentional_and_derived_import_change',
      ka_sangam: 'derived_import_change',
      ka_vedha_gochara: 'approved_intentional_and_derived_import_change',
    })
  })

  it('admits the D-PINS-A2 merge readmission successor for exactly L3, append-only', () => {
    // pravaha/a2-kernel-geometry / Pravaha A2.3: the origin/main merge into the
    // branch (merge commit eccd32d14) plus the A2.2-accepted Tier 0-G kernel
    // geometry rework moved four L3 writers' import closures (membership
    // unchanged, no own-module edits). Re-admission authorised by the steward on
    // the native's 2026-09-30 standing authority (D-PINS-A2). Authority identity
    // and pinned source are different commits on purpose (the D-E022 pattern):
    // the source is the branch's writer-digest regeneration commit, whose
    // committed inventory equals the merged tree's derived inventory.
    // Evidence: 00_ARCHITECTURE/briefs/nirmana/l3_autonomous/gochara_wp0_7/D_PINS_A2_PINS_READMISSION_AUTHORITY_v1_0.md
    const decision = 'D-PINS-A2'
    const authority = 'fa0b0a9a003624b8f39e30600e98460a60170bb2'
    const source = 'f4c69a6d0cd40c05ea6dc64eba789b7c4efdea24'
    const pin = layerPinRecord.layers.L3
    expect(pin.generation_id).toBe('l3:f4c69a6d0cd4:829354703812')
    expect(pin.supersedes_generation_id).toBe('l3:333eb7abcac3:d1bf773c4d94')
    expect(pin.convergence_commit).toBe(source)
    expect(pin.admission?.authority_decision).toBe(decision)
    expect(pin.admission?.authority_commit).toBe(authority)
    expect(pin.admission?.source_commit).toBe(source)
    expect(pin.admission?.changed_assets).toEqual([
      'ka_gochara_v3_century_materialize', 'ka_moorti_nirnaya',
      'ka_sangam', 'ka_vedha_gochara',
    ])
    expect(Object.keys(pin.admission?.delta_classifications ?? {})).toEqual(pin.admission?.changed_assets)
    // every changed asset moved only through its import closure
    expect(Object.values(pin.admission?.delta_classifications ?? {}))
      .toEqual(Array(4).fill('derived_import_change'))
    // the D-E022 predecessor is archived whole and named by the successor
    const archived = layerPinRecord.history.L3.at(-1)!
    expect(archived.generation_id).toBe('l3:333eb7abcac3:d1bf773c4d94')
    expect(archived.superseded_by_generation_id).toBe(pin.generation_id)
    expect(layerPinRecord.history.L3).toHaveLength(6)
    // every other layer is untouched by the A2.3 readmission
    expect(layerPinRecord.layers.L0.generation_id).toBe('l0:7d40f8c70640:64b8859fe692')
    expect(layerPinRecord.layers.L1.generation_id).toBe('l1:333eb7abcac3:b3674dfbfa91')
    expect(layerPinRecord.layers.L2.generation_id).toBe('l2:7d40f8c70640:dbbbb24c09cb')
    expect(layerPinRecord.layers.L4.generation_id).toBe('l4:d2369b888e76:e73988c0dd03')
    expect(layerPinRecord.layers.L5.generation_id).toBe('l5:ed5ad601c5e5:9d222087056d')
  })
})
