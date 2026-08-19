/**
 * P1 G1-B — DB-integration suite for the consent lane.
 *
 * SKIPPED unless `CONSENT_DB_TEST=1` AND `CONSENT_DATABASE_URL` is set. It needs
 * a live Postgres and it DELETES rows, so it must run against a THROWAWAY /
 * local database and NEVER against the shared production DB. It builds its own
 * fixture tables (`charts` stub + two synthetic L2 tables) and applies migration
 * 575 itself, so it is self-contained.
 *
 *   createdb g1b_scratch
 *   CONSENT_DB_TEST=1 CONSENT_DATABASE_URL=postgres://postgres@127.0.0.1:5599/g1b_scratch \
 *     npx vitest run src/lib/pariprashna/consent/__tests__/consent.db.test.ts
 *
 * It talks to `pg` directly rather than through `@/lib/db/client`, so it cannot
 * accidentally inherit a `DATABASE_URL` pointing at anything real — the
 * connection string must be named explicitly, in its own variable.
 */

import { readFileSync } from 'node:fs'
import path from 'node:path'

import { afterAll, beforeAll, beforeEach, describe, expect, it } from 'vitest'
import { Pool } from 'pg'

import { configService } from '@/lib/config'

import { verifyConsentChain } from '../hash_chain'
import { listOpenExclusions, registerExclusion } from '../register'
import { CONSENT_FLAG } from '../flag'
import { resolveSubjectConsent } from '../resolve'
import { discoverSubjectScopedTables } from '../scope'
import { appendConsentEvent, loadConsentChain, loadTombstones, withdrawConsentAndDelete } from '../withdrawal'
import { openDeletionScopeDispute, resolveDeletionScopeDispute } from '../dispute'
import { buildSubjectExportManifest } from '../export_manifest'
import type { ConsentDb, ConsentQueryable } from '../types'

const URL = process.env.CONSENT_DATABASE_URL
const ENABLED = process.env.CONSENT_DB_TEST === '1' && !!URL

const MIGRATION = path.resolve(
  __dirname,
  '../../../../../supabase/migrations/575_pariprashna_chart_subject_consent.sql',
)

const CHART = '11111111-2222-3333-4444-555555555555'
const OTHER_CHART = '99999999-8888-7777-6666-555555555555'

let pool: Pool
let db: ConsentDb

describe.skipIf(!ENABLED)('consent lane — live Postgres', () => {
  beforeAll(async () => {
    pool = new Pool({ connectionString: URL })
    db = {
      async query(sql, params) {
        const r = await pool.query(sql as string, params as unknown[])
        return { rows: r.rows as never[] }
      },
      async withTransaction(fn) {
        const client = await pool.connect()
        try {
          await client.query('BEGIN')
          const tx: ConsentQueryable = {
            async query(sql, params) {
              const r = await client.query(sql as string, params as unknown[])
              return { rows: r.rows as never[] }
            },
          }
          const out = await fn(tx)
          await client.query('COMMIT')
          return out
        } catch (e) {
          await client.query('ROLLBACK')
          throw e
        } finally {
          client.release()
        }
      },
    }

    // Fixture schema: a `charts` stub matching 001_baseline's shape, plus two
    // synthetic L2 tables — one prefix-matched (in scope), one L1-named (out of
    // scope), so the sweep's BOUNDARY is exercised and not just its happy path.
    await pool.query(`
      CREATE TABLE IF NOT EXISTS charts (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        name TEXT NOT NULL, birth_date DATE NOT NULL, birth_time TIME NOT NULL,
        birth_place TEXT NOT NULL, owner_id TEXT, subject_name TEXT,
        role TEXT NOT NULL DEFAULT 'native', timezone_id TEXT,
        created_at TIMESTAMPTZ DEFAULT NOW()
      );
      CREATE TABLE IF NOT EXISTS bodha_g1b_fixture_signals (
        signal_id BIGSERIAL PRIMARY KEY, chart_id UUID NOT NULL, body TEXT NOT NULL
      );
      CREATE TABLE IF NOT EXISTS kala_g1b_fixture_windows (
        window_id BIGSERIAL PRIMARY KEY, chart_id UUID NOT NULL, body TEXT NOT NULL
      );
      CREATE TABLE IF NOT EXISTS ganita_g1b_fixture_positions (
        position_id BIGSERIAL PRIMARY KEY, chart_id UUID NOT NULL, body TEXT NOT NULL
      );
    `)
    await pool.query(readFileSync(MIGRATION, 'utf8'))
  })

  afterAll(async () => {
    await pool?.end()
  })

  beforeEach(async () => {
    configService.setFlag(CONSENT_FLAG, true)
    // Full reset. Tombstones/events are append-only by TRIGGER, which blocks
    // DELETE — TRUNCATE is DDL and bypasses row triggers, which is exactly why
    // the trigger test below asserts on DELETE rather than trusting this.
    await pool.query(`
      TRUNCATE chart_subject_deletion_disputes, chart_subject_deletion_tombstones,
               chart_subject_exclusions, chart_subject_consent_events,
               chart_subject_consent RESTART IDENTITY CASCADE;
      TRUNCATE bodha_g1b_fixture_signals, kala_g1b_fixture_windows,
               ganita_g1b_fixture_positions RESTART IDENTITY;
      DELETE FROM charts WHERE id IN ('${CHART}', '${OTHER_CHART}');
    `)
    for (const id of [CHART, OTHER_CHART]) {
      await pool.query(
        `INSERT INTO charts (id, name, birth_date, birth_time, birth_place, owner_id, role)
         VALUES ($1, 'Fixture', DATE '1984-02-05', TIME '10:43', 'Bhubaneswar', 'uid-native', 'native')`,
        [id],
      )
      for (const t of [
        'bodha_g1b_fixture_signals',
        'kala_g1b_fixture_windows',
        'ganita_g1b_fixture_positions',
      ]) {
        await pool.query(
          `INSERT INTO ${t} (chart_id, body) SELECT $1, 'row-' || g FROM generate_series(1, 3) g`,
          [id],
        )
      }
    }
  })

  // ── schema ────────────────────────────────────────────────────────────────

  it('migration 575 applied: all five tables exist', async () => {
    const { rows } = await pool.query<{ table_name: string }>(
      `SELECT table_name FROM information_schema.tables
        WHERE table_schema='public' AND table_name LIKE 'chart_subject%' ORDER BY 1`,
    )
    expect(rows.map((r) => r.table_name)).toEqual([
      'chart_subject_consent',
      'chart_subject_consent_events',
      'chart_subject_deletion_disputes',
      'chart_subject_deletion_tombstones',
      'chart_subject_exclusions',
    ])
  })

  it('anonymization_choice DEFAULTS to anonymous', async () => {
    await pool.query(
      `INSERT INTO chart_subject_consent (chart_id, subject_kind, subject_principal_id, granted_at)
       VALUES ($1, 'native_self', 'uid-native', now())`,
      [CHART],
    )
    const { rows } = await pool.query(
      `SELECT anonymization_choice, vulnerable_exclusion_flag, consent_state, redaction_requests
         FROM chart_subject_consent WHERE chart_id=$1`,
      [CHART],
    )
    expect(rows[0].anonymization_choice).toBe('anonymous')
    expect(rows[0].vulnerable_exclusion_flag).toBe(false)
    expect(rows[0].consent_state).toBe('granted')
    expect(rows[0].redaction_requests).toEqual([])
  })

  it('a cohort row without a consent document is rejected by the DB, not merely by code', async () => {
    await expect(
      pool.query(
        `INSERT INTO chart_subject_consent (chart_id, subject_kind, granted_at)
         VALUES ($1, 'cohort', now())`,
        [CHART],
      ),
    ).rejects.toThrow(/chart_subject_consent_cohort_document_chk/)
  })

  it('a native_self row with no named subject is rejected by the DB', async () => {
    await expect(
      pool.query(
        `INSERT INTO chart_subject_consent (chart_id, subject_kind, granted_at)
         VALUES ($1, 'native_self', now())`,
        [CHART],
      ),
    ).rejects.toThrow(/chart_subject_consent_native_self_subject_chk/)
  })

  it('the excluded-subject register keeps ONE open row per (chart, reason)', async () => {
    await registerExclusion(db, { chartId: CHART, reason: 'minor', detector: 'test', subjectAgeYears: 9 })
    await registerExclusion(db, { chartId: CHART, reason: 'minor', detector: 'test', subjectAgeYears: 10 })
    const open = await listOpenExclusions(db, CHART)
    expect(open).toHaveLength(1)
    expect(open[0].subject_age_years).toBe(10) // refreshed, not duplicated
  })

  // ── append-only ───────────────────────────────────────────────────────────

  it('consent events are APPEND-ONLY: UPDATE and DELETE both raise', async () => {
    await db.withTransaction((tx) =>
      appendConsentEvent(tx, {
        chartId: CHART,
        eventKind: 'granted',
        actorPrincipalId: 'uid-native',
        payload: { document_ref: 'consent/x.pdf' },
      }),
    )
    await expect(
      pool.query(`UPDATE chart_subject_consent_events SET event_kind='withdrawn' WHERE chart_id=$1`, [CHART]),
    ).rejects.toThrow(/APPEND_ONLY_VIOLATION/)
    await expect(
      pool.query(`DELETE FROM chart_subject_consent_events WHERE chart_id=$1`, [CHART]),
    ).rejects.toThrow(/APPEND_ONLY_VIOLATION/)
  })

  it('the stored chain verifies against re-derivation', async () => {
    await db.withTransaction(async (tx) => {
      await appendConsentEvent(tx, { chartId: CHART, eventKind: 'granted', actorPrincipalId: 'uid-native' })
      await appendConsentEvent(tx, {
        chartId: CHART,
        eventKind: 'anonymization_changed',
        actorPrincipalId: 'uid-native',
        payload: { to: 'attributed' },
      })
    })
    const events = await loadConsentChain(db, CHART)
    expect(events).toHaveLength(2)
    expect(verifyConsentChain(events)).toMatchObject({ ok: true, links_checked: 2 })
  })

  // ── withdrawal → verified deletion ────────────────────────────────────────

  async function grantConsent(chartId: string) {
    await pool.query(
      `INSERT INTO chart_subject_consent (chart_id, subject_kind, subject_principal_id, granted_at)
       VALUES ($1, 'native_self', 'uid-native', now())`,
      [chartId],
    )
  }

  it('withdrawal DELETES the in-scope corpus, leaves L1 alone, and tombstones what it removed', async () => {
    await grantConsent(CHART)

    const scope = await discoverSubjectScopedTables(db)
    expect(scope).toContain('bodha_g1b_fixture_signals')
    expect(scope).toContain('kala_g1b_fixture_windows')
    expect(scope).not.toContain('ganita_g1b_fixture_positions')

    // Capture the expected digest BEFORE the sweep so the tombstone can be
    // checked against an independently-computed value, not against itself.
    const { rows: pre } = await pool.query<{ h: string }>(
      `SELECT encode(sha256(convert_to(coalesce(string_agg(d,'' ORDER BY d),''),'UTF8')),'hex') AS h
         FROM (SELECT md5(t.*::text) AS d FROM bodha_g1b_fixture_signals t WHERE t.chart_id::text=$1) s`,
      [CHART],
    )

    const result = await withdrawConsentAndDelete({
      chartId: CHART,
      db,
      actorPrincipalId: 'uid-native',
      note: 'subject request',
    })

    expect(result.status).toBe('deleted')
    expect(result.rows_deleted).toBe(6) // 3 bodha + 3 kala
    expect(result.verified_deletion_at).not.toBeNull()

    // The data is really gone…
    const remaining = await pool.query(
      `SELECT (SELECT count(*) FROM bodha_g1b_fixture_signals WHERE chart_id=$1) AS bodha,
              (SELECT count(*) FROM kala_g1b_fixture_windows  WHERE chart_id=$1) AS kala,
              (SELECT count(*) FROM ganita_g1b_fixture_positions WHERE chart_id=$1) AS ganita`,
      [CHART],
    )
    expect(Number(remaining.rows[0].bodha)).toBe(0)
    expect(Number(remaining.rows[0].kala)).toBe(0)
    expect(Number(remaining.rows[0].ganita)).toBe(3) // L1: deliberately untouched

    // …and the OTHER chart is untouched (subject-scoped, not global).
    const other = await pool.query(
      `SELECT count(*) AS n FROM bodha_g1b_fixture_signals WHERE chart_id=$1`,
      [OTHER_CHART],
    )
    expect(Number(other.rows[0].n)).toBe(3)

    // The tombstone proves what was removed without holding any of it.
    const tombstones = await loadTombstones(db, CHART)
    const bodhaStone = tombstones.find((t) => t.table_name === 'bodha_g1b_fixture_signals')!
    expect(bodhaStone.row_count).toBe(3)
    expect(bodhaStone.verified_empty).toBe(true)
    expect(bodhaStone.content_hash).toMatch(/^[0-9a-f]{64}$/)
    expect(bodhaStone.content_hash).toBe(pre[0].h)
    // Nothing in the receipt is a row body.
    expect(JSON.stringify(bodhaStone)).not.toContain('row-1')
  })

  it('tombstones cannot be deleted (append-only)', async () => {
    await grantConsent(CHART)
    await withdrawConsentAndDelete({ chartId: CHART, db, actorPrincipalId: 'uid-native' })
    await expect(
      pool.query(`DELETE FROM chart_subject_deletion_tombstones WHERE chart_id=$1`, [CHART]),
    ).rejects.toThrow(/APPEND_ONLY_VIOLATION/)
  })

  it('after a verified deletion the subject is refused at entitlement resolution', async () => {
    await grantConsent(CHART)
    await withdrawConsentAndDelete({ chartId: CHART, db, actorPrincipalId: 'uid-native' })
    const d = await resolveSubjectConsent({ chartId: CHART, principalId: 'uid-native', db })
    expect(d.outcome).toBe('refuse')
    expect(d.reason).toBe('subject_deleted')
    const open = await listOpenExclusions(db, CHART)
    expect(open.map((e) => e.exclusion_reason)).toContain('subject_deleted')
  })

  it('an open deletion-scope dispute BLOCKS the sweep; resolving it unblocks', async () => {
    await grantConsent(CHART)
    const dispute = await openDeletionScopeDispute(db, {
      chartId: CHART,
      openedBySession: 'Madhav_P1_G1B_Consent',
      parties: ['subject', 'native-arbitrator'],
      description: 'Subject asserts L1 facts must also be destroyed.',
      requestedScope: ['bodha_g1b_fixture_signals', 'ganita_g1b_fixture_positions'],
      appliedScope: ['bodha_g1b_fixture_signals', 'kala_g1b_fixture_windows'],
    })
    expect(dispute.status).toBe('open')
    expect(dispute.dr_id).toBeNull()
    expect(dispute.dr_entry_yaml).toContain('class: deletion_scope_dispute')

    const blocked = await withdrawConsentAndDelete({ chartId: CHART, db, actorPrincipalId: 'uid-native' })
    expect(blocked.status).toBe('blocked_by_dispute')
    expect(blocked.blocking_dispute_ids).toContain(Number(dispute.dispute_id))
    // Withdrawal is RECORDED even though destruction waits.
    const { rows: c } = await pool.query(`SELECT consent_state FROM chart_subject_consent WHERE chart_id=$1`, [CHART])
    expect(c[0].consent_state).toBe('withdrawn')
    // Nothing was destroyed.
    const still = await pool.query(`SELECT count(*) AS n FROM bodha_g1b_fixture_signals WHERE chart_id=$1`, [CHART])
    expect(Number(still.rows[0].n)).toBe(3)

    await resolveDeletionScopeDispute(db, {
      disputeId: Number(dispute.dispute_id),
      chartId: CHART,
      drId: 'DIS.042',
      resolution: 'Native arbitration: L2+ scope stands; L1 is computation.',
    })
    const after = await withdrawConsentAndDelete({ chartId: CHART, db, actorPrincipalId: 'uid-native' })
    expect(after.status).toBe('deleted')
  })

  // ── export manifest ───────────────────────────────────────────────────────

  it('the export manifest inventories what exists, without inlining row bodies', async () => {
    await grantConsent(CHART)
    await db.withTransaction((tx) =>
      appendConsentEvent(tx, { chartId: CHART, eventKind: 'granted', actorPrincipalId: 'uid-native' }),
    )
    const m = await buildSubjectExportManifest({ chartId: CHART, db })

    expect(m.manifest_version).toBe('subject-export-manifest/v1')
    expect(m.audience).toBe('subject')
    expect(m.chart.chart_id).toBe(CHART)
    expect(m.chart.identifying_fields_redacted).toBe(false)
    expect(m.subject_status.subject_kind).toBe('native_self')
    expect(m.subject_status.is_minor).toBe(false)
    expect(m.consent_record).not.toBeNull()
    expect(m.consent_chain.verification.ok).toBe(true)
    expect(m.consent_chain.verification.links_checked).toBe(1)

    const tables = m.data_inventory.entries.map((e) => e.table_name)
    expect(tables).toContain('bodha_g1b_fixture_signals')
    expect(tables).toContain('kala_g1b_fixture_windows')
    expect(tables).not.toContain('ganita_g1b_fixture_positions')
    expect(m.data_inventory.total_rows).toBe(6)
    expect(JSON.stringify(m)).not.toContain('row-1') // inventory, not a dump
  })

  it('the reviewer-audience manifest honors an anonymous election; the subject one does not', async () => {
    await grantConsent(CHART)
    const forSubject = await buildSubjectExportManifest({ chartId: CHART, db, audience: 'subject' })
    expect(forSubject.chart.name).toBe('Fixture')
    expect(forSubject.chart.owner_id).toBe('uid-native')

    const forReviewer = await buildSubjectExportManifest({ chartId: CHART, db, audience: 'reviewer' })
    expect(forReviewer.chart.identifying_fields_redacted).toBe(true)
    expect(forReviewer.chart.name).toMatch(/REDACTED/)
    expect(forReviewer.chart.owner_id).toMatch(/REDACTED/)
    // Birth data is load-bearing and is NOT redacted — §6 says so honestly.
    expect(forReviewer.chart.birth_date).toBe('1984-02-05')
  })

  it('the manifest reflects a completed deletion, tombstones and all', async () => {
    await grantConsent(CHART)
    await withdrawConsentAndDelete({ chartId: CHART, db, actorPrincipalId: 'uid-native' })
    const m = await buildSubjectExportManifest({ chartId: CHART, db })
    expect(m.subject_status.consent_state).toBe('withdrawn')
    expect(m.subject_status.verified_deletion_at).not.toBeNull()
    expect(m.data_inventory.total_rows).toBe(0)
    expect(m.deletion_tombstones.length).toBeGreaterThan(0)
    expect(m.consent_chain.verification.ok).toBe(true)
  })
})
