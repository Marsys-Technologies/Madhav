import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'

const repoRoot = resolve(process.cwd(), '..')
const campaignRoot = resolve(repoRoot, '00_ARCHITECTURE/briefs/nirmana/purna_anvesana')
const definition = JSON.parse(readFileSync(resolve(campaignRoot, 'CAMPAIGN_DEFINITION.json'), 'utf8'))
const events = readFileSync(resolve(campaignRoot, 'EVENTS.jsonl'), 'utf8')
  .trim().split('\n').map((line) => JSON.parse(line))
const acceptance = JSON.parse(readFileSync(resolve(campaignRoot, 'BEYOND_ACARYA_ACCEPTANCE_v1.json'), 'utf8'))
const terminal = JSON.parse(readFileSync(resolve(campaignRoot, 'TERMINAL_QUARANTINE_v1.json'), 'utf8'))

describe('Purna Anvesana W6-P2 terminal contract', () => {
  it('has evidence for every declared packet without rewriting a negative acceptance verdict', () => {
    const declaredPackets = definition.packets.map((packet: { id: string }) => packet.id).sort()
    const terminalPackets = terminal.packet_evidence.map((packet: { packet_id: string }) => packet.packet_id).sort()
    const eventIds = new Set(events.map((event: { event_id: string }) => event.event_id))

    expect(terminalPackets).toEqual(declaredPackets)
    expect(terminal.packet_evidence.every((packet: { status: string }) => packet.status === 'COMPLETE')).toBe(true)
    for (const packet of terminal.packet_evidence as Array<{ event_ids: string[] }>) {
      expect(packet.event_ids.length).toBeGreaterThan(0)
      expect(packet.event_ids.every((eventId) => eventIds.has(eventId))).toBe(true)
    }
    expect(terminal.acceptance_disposition).toMatchObject({
      verdict: 'NOT_ACCEPTED_SOURCE_LOCAL',
      report_hash: acceptance.report_hash,
    })
  })

  it('assigns every residual a concrete owner, trigger and authority gate', () => {
    expect(terminal.residuals.length).toBeGreaterThanOrEqual(10)
    expect(new Set(terminal.residuals.map((item: { residual_id: string }) => item.residual_id)).size)
      .toBe(terminal.residuals.length)
    for (const residual of terminal.residuals as Array<Record<string, string>>) {
      expect(residual.status).toBe('QUARANTINED')
      expect(residual.owner.length).toBeGreaterThan(3)
      expect(residual.trigger.length).toBeGreaterThan(20)
      expect(residual.authority_required.length).toBeGreaterThan(10)
    }
  })

  it('preserves and dispositions the original R1-R12 register without renumbering', () => {
    const expected = Array.from({ length: 12 }, (_, index) => `R${index + 1}`)
    const dispositions = terminal.original_residual_disposition as Array<{
      original_id: string
      status: string
      event_ids: string[]
      terminal_residual_ids: string[]
    }>
    const eventIds = new Set(events.map((event: { event_id: string }) => event.event_id))
    const residualIds = new Set(terminal.residuals.map((item: { residual_id: string }) => item.residual_id))

    expect(dispositions.map((item) => item.original_id)).toEqual(expected)
    for (const disposition of dispositions) {
      expect(disposition.status).toMatch(/^(CLOSED|PARTIALLY_CLOSED|OPEN)_/)
      expect(disposition.event_ids.length).toBeGreaterThan(0)
      expect(disposition.event_ids.every((eventId) => eventIds.has(eventId))).toBe(true)
      expect(disposition.terminal_residual_ids.every((residualId) => residualIds.has(residualId))).toBe(true)
      if (disposition.status.startsWith('OPEN_')) {
        expect(disposition.terminal_residual_ids.length).toBeGreaterThan(0)
      }
    }
  })

  it('records every prohibited action as not performed or claimed', () => {
    expect(Object.keys(terminal.prohibited_actions).length).toBeGreaterThanOrEqual(10)
    expect(Object.values(terminal.prohibited_actions).every((value) => value === false)).toBe(true)
    expect(terminal.delivery).toMatchObject({
      foundation_candidate_pull_request: 2597,
      foundation_candidate_policy: 'FROZEN_UNCHANGED',
      stacked_pull_requests: [2598, 2599, 2600, 2601, 2602, 2603],
      merge_status: 'NOT_RUN',
      deployment_status: 'NOT_RUN',
    })
    expect(acceptance).toMatchObject({
      evidence_kind: 'synthetic_source_local',
      empirical_answer_quality: 'NOT_RUN',
      production_validation: 'NOT_RUN',
    })
  })

  it('cannot reach the terminal state before remote lease release is recorded', () => {
    expect(terminal.terminal_status).toBe('SOURCE_SCOPE_COMPLETE_WITH_AUTHORITY_BOUND_REMAINDER')
    expect(terminal.lease_release).toMatchObject({
      lease_id: 'MADHAV-PURNA-ANVESANA-W6-20260915',
      status: 'RELEASED',
    })
    expect(terminal.lease_release.remote_coordination_commit).toMatch(/^[a-f0-9]{40}$/)
    expect(terminal.delivery.wave6_pull_request).toEqual(expect.any(Number))
  })
})
