/**
 * P1 G1-B — deletion scope (what a withdrawal destroys) and the
 * DISAGREEMENT_REGISTER dispute hook (what happens when that scope is contested).
 */

import { afterEach, beforeEach, describe, expect, it } from 'vitest'

import { configService } from '@/lib/config'

import {
  SUBJECT_SCOPE_DENY_TABLES,
  SUBJECT_SCOPE_EXTRA_TABLES,
  discoverSubjectScopedTables,
  isSubjectScopedTable,
} from '../scope'
import {
  DELETION_SCOPE_DISPUTE_CLASS,
  openDeletionScopeDispute,
  renderDisagreementRegisterEntry,
  resolveDeletionScopeDispute,
} from '../dispute'
import { buildSubjectExportManifest } from '../export_manifest'
import { withdrawConsentAndDelete } from '../withdrawal'
import { CONSENT_FLAG } from '../flag'
import { ConsentFeatureDisabledError, type ConsentDb } from '../types'

beforeEach(() => configService.setFlag(CONSENT_FLAG, false))
afterEach(() => configService.setFlag(CONSENT_FLAG, false))

describe('isSubjectScopedTable — the L2+ boundary', () => {
  it('includes the interpretive layers', () => {
    for (const t of [
      'bodha_msr_signals',
      'bodha_cgm_edges',
      'kala_field',
      'kala_gochara_windows_v2',
      'phala_anchors',
      'mimamsa_predictions',
      'gochara_resonance_map',
      'l25_msr_signals',
      'pariprashna_stream_capture',
      'brahma_mimamsa_prediction_ledger',
      'brahma_prospective_ledger',
    ]) {
      expect(isSubjectScopedTable(t), t).toBe(true)
    }
  })

  it('includes the prefix-less chart-scoped extras', () => {
    for (const t of SUBJECT_SCOPE_EXTRA_TABLES) expect(isSubjectScopedTable(t), t).toBe(true)
  })

  it('EXCLUDES L1 computation, root identity, and build bookkeeping', () => {
    for (const t of [
      'charts',
      'chart_grants',
      'chart_facts',
      'chart_fact_identity',
      'chart_dashas',
      'chart_divisionals',
      'chart_panchanga',
      'ganita_positions',
      'ga_something',
      'builds',
      'asset_throughput',
      'l1_tajik_varsha_year_lords',
      'prashna_charts',
    ]) {
      expect(isSubjectScopedTable(t), t).toBe(false)
    }
  })

  it('EXCLUDES the consent machinery itself — a receipt deleted with the data is no receipt', () => {
    for (const t of [
      'chart_subject_consent',
      'chart_subject_consent_events',
      'chart_subject_exclusions',
      'chart_subject_deletion_tombstones',
      'chart_subject_deletion_disputes',
    ]) {
      expect(isSubjectScopedTable(t), t).toBe(false)
      expect(SUBJECT_SCOPE_DENY_TABLES).toContain(t)
    }
  })

  it('discovery filters the live information_schema result through the same predicate', async () => {
    const db = {
      async query() {
        return {
          rows: [
            { table_name: 'bodha_msr_signals' },
            { table_name: 'charts' },
            { table_name: 'chart_facts' },
            { table_name: 'chart_subject_consent' },
            { table_name: 'kala_field' },
            { table_name: 'conversations' },
            // A table nobody has written yet: prefix allowlisting picks it up
            // WITHOUT anyone remembering to edit a list.
            { table_name: 'bodha_some_future_table' },
          ] as never[],
        }
      },
    }
    expect(await discoverSubjectScopedTables(db)).toEqual([
      'bodha_msr_signals',
      'kala_field',
      'conversations',
      'bodha_some_future_table',
    ])
  })
})

describe('renderDisagreementRegisterEntry', () => {
  const input = {
    chartId: '482012f1-710e-4a25-994a-93821f5871aa',
    openedBySession: 'Madhav_P1_G1B_Consent',
    parties: ['subject', 'native-arbitrator'],
    description:
      'The subject asserts that withdrawal must also destroy the L1 computed facts.\n' +
      'The implemented scope destroys the L2+ interpretive corpus only.',
    requestedScope: ['bodha_msr_signals', 'chart_facts'],
    appliedScope: ['bodha_msr_signals', 'kala_field'],
    openedOn: '2026-08-19T10:00:00.000Z',
  }

  it('emits the register §2 schema shape', () => {
    const yaml = renderDisagreementRegisterEntry(input)
    for (const field of [
      'disagreement_register_entry:',
      '  class: deletion_scope_dispute',
      '  opened_on: 2026-08-19',
      '  parties:',
      '  description: >',
      '  authoritative_side: none',
      '  evidence_side_a:',
      '  evidence_side_b:',
      '  arbitration_steps_taken: []',
      '  status: open',
      '  resolution: null',
      '  state_hashes:',
      '  linked_artifacts:',
    ]) {
      expect(yaml, field).toContain(field)
    }
  })

  it('names the actual scope disagreement on both evidence sides', () => {
    const yaml = renderDisagreementRegisterEntry(input)
    expect(yaml).toContain('chart_facts') // only-in-requested
    expect(yaml).toContain('kala_field') // only-in-applied
  })

  it('marks dr_id PENDING until a governance session assigns one', () => {
    expect(renderDisagreementRegisterEntry(input)).toContain('dr_id: DIS.PENDING')
    expect(renderDisagreementRegisterEntry({ ...input, drId: 'DIS.007' })).toContain(
      'dr_id: DIS.007',
    )
  })

  it('uses the class name the register will need a v1.1 bump to accept', () => {
    expect(DELETION_SCOPE_DISPUTE_CLASS).toBe('deletion_scope_dispute')
  })
})

describe('flag OFF — every mutating entry point is unreachable', () => {
  const db = {
    async query() {
      throw new Error('the database must not be touched while the flag is OFF')
    },
    async withTransaction() {
      throw new Error('the database must not be touched while the flag is OFF')
    },
  } as unknown as ConsentDb

  it('withdrawConsentAndDelete throws ConsentFeatureDisabledError', async () => {
    await expect(
      withdrawConsentAndDelete({ chartId: 'c', db, actorPrincipalId: 'u' }),
    ).rejects.toBeInstanceOf(ConsentFeatureDisabledError)
  })

  it('openDeletionScopeDispute throws ConsentFeatureDisabledError', async () => {
    await expect(
      openDeletionScopeDispute(db, {
        chartId: 'c',
        openedBySession: 's',
        parties: [],
        description: 'd',
        requestedScope: [],
        appliedScope: [],
      }),
    ).rejects.toBeInstanceOf(ConsentFeatureDisabledError)
  })

  it('resolveDeletionScopeDispute throws ConsentFeatureDisabledError', async () => {
    await expect(
      resolveDeletionScopeDispute(db, { disputeId: 1, chartId: 'c', drId: null, resolution: 'r' }),
    ).rejects.toBeInstanceOf(ConsentFeatureDisabledError)
  })

  it('buildSubjectExportManifest throws ConsentFeatureDisabledError', async () => {
    await expect(buildSubjectExportManifest({ chartId: 'c', db })).rejects.toBeInstanceOf(
      ConsentFeatureDisabledError,
    )
  })

  it('the error names the flag, so the fix is obvious from the message alone', async () => {
    await expect(
      withdrawConsentAndDelete({ chartId: 'c', db, actorPrincipalId: 'u' }),
    ).rejects.toThrow(/SUBJECT_CONSENT_ENFORCEMENT/)
  })
})
