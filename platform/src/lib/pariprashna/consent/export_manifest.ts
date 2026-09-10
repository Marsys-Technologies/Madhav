/**
 * Paripraśna consent — SUBJECT EXPORT AS A JSON MANIFEST (§4, §5).
 *
 * §4: "Subject access/export ships as a machine-readable JSON manifest + the
 * sealed-reading renderings."
 * §5: "subject access/export = the sealed-reading export plus a per-subject
 * machine-readable data manifest (cheap: everything is chart_id-scoped)."
 *
 * This module builds the MANIFEST half — the machine-readable inventory of what
 * exists for a subject. The sealed-reading renderings are a separate,
 * already-existing surface; the manifest points at them by id rather than
 * inlining prose, per §5's safe-logging rule.
 *
 * ── WHAT THE MANIFEST DOES AND DOES NOT CONTAIN ──────────────────────────────
 * It contains: the chart's identity fields, the consent record, the consent
 * chain WITH its verification result, the excluded-subject register history, the
 * tombstones, the disputes, and a per-table row-count inventory over the exact
 * same discovered scope the deletion sweep uses.
 *
 * It does NOT contain the row bodies. A subject-access manifest answers "what do
 * you hold about me, and where" — dumping 500k dasha rows into a JSON blob would
 * answer a question nobody asked while making the answer unreadable. Row bodies
 * are retrieved per-table by the operator from the inventory's own table list.
 *
 * ── ANONYMIZATION (PPR-24) ───────────────────────────────────────────────────
 * `audience: 'subject'` (the default) does NOT anonymize: the subject is the
 * recipient of their own data, and redacting a person's name from a copy handed
 * to that person is theatre. `audience: 'reviewer'` DOES honor
 * `anonymization_choice`, because that is the serve-time enforcement PPR-24
 * requires ("acharya_reviewer sees identifying data only with native consent +
 * subject's anonymization choice enforced at serve time"). The manifest states
 * which audience produced it, so a downstream consumer cannot mistake one for
 * the other.
 */

import { isConsentEnforcementEnabled } from './flag'
import { assertSafeTableIdentifier, verifyConsentChain, type ChainVerification } from './hash_chain'
import { computeAgeYears, isMinorSubject } from './minor_exclusion'
import { listExclusionHistory } from './register'
import { loadChartSubject, loadConsentRow } from './resolve'
import { discoverSubjectScopedTables } from './scope'
import { loadConsentChain, loadTombstones } from './withdrawal'
import {
  ConsentFeatureDisabledError,
  type ConsentDb,
  type ConsentEventRow,
  type ConsentRow,
  type DeletionDisputeRow,
  type ExclusionRow,
  type TombstoneRow,
} from './types'

export const SUBJECT_EXPORT_MANIFEST_VERSION = 'subject-export-manifest/v1'

export type ExportAudience = 'subject' | 'reviewer'

export interface DataInventoryEntry {
  table_name: string
  row_count: number
}

export interface SubjectExportManifest {
  manifest_version: typeof SUBJECT_EXPORT_MANIFEST_VERSION
  generated_at: string
  audience: ExportAudience
  chart: {
    chart_id: string
    name: string | null
    subject_name: string | null
    birth_date: string | null
    birth_place: string | null
    owner_id: string | null
    role: string | null
    /** true when `audience: 'reviewer'` + `anonymization_choice: 'anonymous'`. */
    identifying_fields_redacted: boolean
  }
  subject_status: {
    subject_kind: string | null
    consent_state: string | null
    anonymization_choice: string | null
    vulnerable_exclusion_flag: boolean | null
    is_minor: boolean | null
    subject_age_years: number | null
    verified_deletion_at: string | null
  }
  consent_record: ConsentRow | null
  consent_chain: {
    events: ConsentEventRow[]
    verification: ChainVerification
  }
  exclusion_register: ExclusionRow[]
  deletion_tombstones: TombstoneRow[]
  deletion_disputes: DeletionDisputeRow[]
  data_inventory: {
    tables_scanned: number
    total_rows: number
    entries: DataInventoryEntry[]
  }
  notes: string[]
}

export interface BuildManifestArgs {
  chartId: string
  db: ConsentDb
  audience?: ExportAudience
  asOf?: Date
}

const REDACTED = '[REDACTED — subject elected anonymous disclosure (§3.5.D.3)]'

/**
 * Assemble the subject-access manifest.
 * Throws `ConsentFeatureDisabledError` while the flag is OFF.
 */
export async function buildSubjectExportManifest(
  args: BuildManifestArgs,
): Promise<SubjectExportManifest> {
  if (!isConsentEnforcementEnabled()) throw new ConsentFeatureDisabledError('buildSubjectExportManifest')
  const { chartId, db, audience = 'subject', asOf = new Date() } = args

  const chart = await loadChartSubject(db, chartId)
  const consent = await loadConsentRow(db, chartId)
  const events = (await loadConsentChain(db, chartId)) as ConsentEventRow[]
  const exclusions = await listExclusionHistory(db, chartId)
  const tombstones = await loadTombstones(db, chartId)
  const { rows: disputes } = await db.query<DeletionDisputeRow>(
    `SELECT * FROM chart_subject_deletion_disputes WHERE chart_id = $1 ORDER BY opened_at`,
    [chartId],
  )

  const anonymize = audience === 'reviewer' && consent?.anonymization_choice === 'anonymous'

  // Inventory over the SAME discovered scope the deletion sweep uses, so
  // "what you hold" and "what withdrawal destroys" cannot silently diverge.
  const tables = await discoverSubjectScopedTables(db)
  const entries: DataInventoryEntry[] = []
  let totalRows = 0
  for (const table of tables) {
    assertSafeTableIdentifier(table)
    const { rows } = await db.query<{ n: number }>(
      `SELECT count(*)::int AS n FROM "${table}" WHERE chart_id::text = $1`,
      [chartId],
    )
    const n = Number(rows[0]?.n ?? 0)
    if (n > 0) {
      entries.push({ table_name: table, row_count: n })
      totalRows += n
    }
  }

  const notes: string[] = [
    'This manifest inventories WHERE data about the subject is held; it does not inline row ' +
      'bodies. Per-table contents are retrievable from the table list above.',
    'Sealed-reading renderings are exported separately (§4) and are referenced by conversation ' +
      'id, not duplicated here.',
    'The inventory covers the L2+ interpretive corpus — the same scope a withdrawal destroys. ' +
      'L1 Gaṇita computation and build bookkeeping are deliberately outside that scope ' +
      '(§8/A9); a subject who disputes that boundary opens a deletion-scope dispute.',
  ]
  if (anonymize) {
    notes.push(
      'Identifying fields are redacted: this is a reviewer-audience export and the subject ' +
        'elected anonymous disclosure (§3.5.D.3, PPR-24).',
    )
  }
  if (events.length === 0) {
    notes.push(
      'The consent chain is empty, so its verification is vacuous — it is not evidence that ' +
        'anything was checked.',
    )
  }

  return {
    manifest_version: SUBJECT_EXPORT_MANIFEST_VERSION,
    generated_at: asOf.toISOString(),
    audience,
    chart: {
      chart_id: chartId,
      name: anonymize ? REDACTED : (chart?.name ?? null),
      subject_name: anonymize ? REDACTED : (chart?.subject_name ?? null),
      // Birth data is analytically load-bearing and cannot be redacted; §6 says
      // so honestly in the consent document rather than pretending otherwise.
      birth_date: chart?.birth_date ?? null,
      birth_place: anonymize ? REDACTED : (chart?.birth_place ?? null),
      owner_id: anonymize ? REDACTED : (chart?.owner_id ?? null),
      role: chart?.role ?? null,
      identifying_fields_redacted: anonymize,
    },
    subject_status: {
      subject_kind: consent?.subject_kind ?? null,
      consent_state: consent?.consent_state ?? null,
      anonymization_choice: consent?.anonymization_choice ?? null,
      vulnerable_exclusion_flag: consent?.vulnerable_exclusion_flag ?? null,
      is_minor: isMinorSubject(chart?.birth_date ?? null, asOf),
      subject_age_years: computeAgeYears(chart?.birth_date ?? null, asOf),
      verified_deletion_at: consent?.verified_deletion_at ?? null,
    },
    consent_record: consent,
    consent_chain: { events, verification: verifyConsentChain(events) },
    exclusion_register: exclusions,
    deletion_tombstones: tombstones,
    deletion_disputes: disputes,
    data_inventory: { tables_scanned: tables.length, total_rows: totalRows, entries },
    notes,
  }
}

/** The manifest as the bytes a subject actually receives. */
export function serializeSubjectExportManifest(manifest: SubjectExportManifest): string {
  return JSON.stringify(manifest, null, 2)
}
