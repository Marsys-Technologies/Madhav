import { existsSync, readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'

const repoRoot = resolve(process.cwd(), '..')
const campaignRoot = resolve(repoRoot, '00_ARCHITECTURE/briefs/nirmana/purna_anvesana')
const recoveryPath = resolve(campaignRoot, 'RECOVERY_DEFINITION_v1.json')
const localEvidencePath = resolve(campaignRoot, 'W7_LOCAL_DISPOSABLE_EVIDENCE_v1.json')
const authorityPacketPath = resolve(campaignRoot, 'W7_COMPLETION_AUTHORITY_PACKET_v1.json')
const empiricalProtocolPath = resolve(campaignRoot, 'EMPIRICAL_ANSWER_QUALITY_PROTOCOL_v1.json')

function readJson(path: string) {
  return JSON.parse(readFileSync(path, 'utf8'))
}

describe('Purna Anvesana Wave 7 recovery evidence', () => {
  it('dispositions every frozen PA-R01 through PA-R13 residual without claiming an external result', () => {
    expect(existsSync(localEvidencePath)).toBe(true)
    if (!existsSync(localEvidencePath)) return

    const recovery = readJson(recoveryPath)
    const evidence = readJson(localEvidencePath)
    const expectedIds = Array.from({ length: 13 }, (_, index) => `PA-R${String(index + 1).padStart(2, '0')}`)

    expect(evidence.recovery_id).toBe(recovery.recovery_id)
    expect(evidence.immutable_base).toBe(recovery.immutable_base)
    expect(evidence.scope).toBe('SOURCE_LOCAL_DISPOSABLE_ONLY')
    expect(evidence.terminal_ceiling).toBe('SOURCE_LOCAL_ACCEPTED')
    expect(evidence.residual_dispositions.map((item: { residual_id: string }) => item.residual_id))
      .toEqual(expectedIds)
    expect(new Set(evidence.residual_dispositions.map((item: { residual_id: string }) => item.residual_id)).size)
      .toBe(13)
    expect(evidence.residual_dispositions.every((item: {
      local_status: string
      evidence_refs: string[]
      external_result: string
    }) => item.local_status !== 'OPEN_UNDIAGNOSED'
      && item.evidence_refs.length > 0
      && item.external_result === 'NOT_RUN')).toBe(true)
    expect(evidence.prohibited_actions).toEqual({
      merge: false,
      deploy: false,
      shared_or_production_migration: false,
      shared_or_production_data_mutation: false,
      credentials_or_signing_key_change: false,
      infrastructure_change: false,
      asset_retirement: false,
      expert_or_empirical_acceptance: false,
      production_acceptance: false,
    })
  })

  it('contains a minimized authority packet with executable gates and receipt contracts', () => {
    expect(existsSync(authorityPacketPath)).toBe(true)
    if (!existsSync(authorityPacketPath)) return

    const packet = readJson(authorityPacketPath)
    const externalIds = new Set(packet.external_actions.flatMap(
      (action: { residual_ids: string[] }) => action.residual_ids,
    ))

    expect(packet.status).toBe('AWAITING_SEPARATE_AUTHORITY')
    expect(packet.authorizes_execution).toBe(false)
    expect(packet.source_local_preconditions.verdict).toBe('ACCEPTED_SOURCE_LOCAL')
    expect(packet.external_actions.length).toBeGreaterThan(0)
    expect(packet.external_actions.every((action: {
      authority_required: string
      owner: string
      commands: string[]
      required_receipts: string[]
      success_condition: string
      status: string
    }) => action.authority_required.length > 10
      && action.owner.length > 3
      && action.commands.length > 0
      && action.required_receipts.length > 0
      && action.success_condition.length > 20
      && action.status === 'NOT_RUN')).toBe(true)
    for (const residualId of ['PA-R01', 'PA-R06', 'PA-R07', 'PA-R08', 'PA-R09', 'PA-R10', 'PA-R12', 'PA-R13']) {
      expect(externalIds.has(residualId)).toBe(true)
    }
    for (const sourceClosedId of ['PA-R02', 'PA-R03', 'PA-R04', 'PA-R05', 'PA-R11']) {
      expect(externalIds.has(sourceClosedId)).toBe(false)
    }
  })

  it('predeclares a blinded empirical protocol and leaves every empirical result unset', () => {
    expect(existsSync(empiricalProtocolPath)).toBe(true)
    if (!existsSync(empiricalProtocolPath)) return

    const protocol = readJson(empiricalProtocolPath)

    expect(protocol.status).toBe('SOURCE_READY_NOT_EXECUTED')
    expect(protocol.authorizes_execution).toBe(false)
    expect(protocol.outcome_fields).toEqual({
      corpus_hash: null,
      execution_receipt_ids: [],
      reviewer_identities: [],
      dimension_results: null,
      aggregate_result: null,
      acceptance_verdict: 'NOT_RUN',
    })
    expect(protocol.blinding.generation_arm_hidden_from_reviewers).toBe(true)
    expect(protocol.blinding.held_out_items_hidden_from_implementers_until_freeze).toBe(true)
    expect(protocol.blinding.no_outcome_conditioned_edits).toBe(true)
    expect(protocol.review.minimum_independent_domain_experts).toBeGreaterThanOrEqual(2)
    expect(protocol.corpus.minimum_items).toBeGreaterThanOrEqual(20)
    expect(protocol.metrics.every((metric: {
      id: string
      scale: string
      pass_threshold: string
      result: unknown
    }) => metric.id.length > 0
      && metric.scale.length > 0
      && metric.pass_threshold.length > 0
      && metric.result === null)).toBe(true)
  })
})
