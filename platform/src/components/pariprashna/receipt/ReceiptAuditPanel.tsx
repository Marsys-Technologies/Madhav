'use client'

import type { AcharyaReadingReceipt } from '@/lib/pariprashna/receipt/schema'

/**
 * ReceiptAuditPanel — the G3-A (PPR-01) audit affordance.
 *
 * Presentational only: takes an already-fetched `AcharyaReadingReceipt` as a
 * prop and renders it. Deliberately does NOT fetch its own data — the D-16
 * provenance stamp this receipt sits alongside is audit-drawer-only by
 * design (never on the live SSE wire; DB-only, PB-1 ruling 8c), and this
 * panel follows the same discipline: whatever surface eventually mounts it
 * (an audit drawer, a per-message detail view) is responsible for resolving
 * a receipt via `getLastTurnReceipt` / `getTurnReceiptByMessageId`
 * (`lib/pariprashna/receipt/store.ts`) server-side and passing the result
 * down. No data-fetching route is wired by this lane — see the G3-A report
 * for the disclosed scope boundary.
 *
 * Every section renders the honest state the receipt itself carries: a
 * `status: 'measured'` field shows its data; a `status: 'unavailable'` field
 * shows its `unavailable_reason`, never a blank space pretending to be zero
 * findings (§N.7 item 6).
 */
export function ReceiptAuditPanel({ receipt }: { receipt: AcharyaReadingReceipt }) {
  return (
    <div
      className="font-mono"
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: '14px',
        padding: '14px',
        background: 'var(--pp-surface)',
        border: '1px solid var(--pp-rule)',
        borderRadius: '8px',
        fontSize: '10.5px',
        lineHeight: 1.6,
        color: 'var(--pp-gold-dim)',
      }}
    >
      <Header receipt={receipt} />
      <Section title="Coverage">
        {receipt.coverage.status === 'measured' ? (
          <div>
            {receipt.coverage.served}/{receipt.coverage.floor_item_total} floor items served
            {' · '}
            {receipt.coverage.empty} empty · {receipt.coverage.dark} dark
            {receipt.coverage.channel_note ? <Note text={receipt.coverage.channel_note} /> : null}
          </div>
        ) : (
          <Unavailable reason={receipt.coverage.unavailable_reason} />
        )}
      </Section>

      <Section title={`Facts consumed (${receipt.facts_consumed.length})`}>
        {receipt.facts_consumed.length === 0 ? (
          <Empty label="no facts cited this turn" />
        ) : (
          <ul style={{ margin: 0, paddingLeft: '16px' }}>
            {receipt.facts_consumed.map((f) => (
              <li key={`${f.index}-${f.ref}`}>
                [{f.index}] {f.ref} ({f.layer})
              </li>
            ))}
          </ul>
        )}
      </Section>

      <Section title="Cross-domain">
        {receipt.cross_domain.status === 'measured' ? (
          <div>{receipt.cross_domain.domains?.join(', ') || '(no domains authorized)'}</div>
        ) : (
          <Unavailable reason={receipt.cross_domain.unavailable_reason} />
        )}
      </Section>

      <Section title="Evidence grades">
        {receipt.evidence_grades.status === 'measured' && receipt.evidence_grades.grade_counts ? (
          <div>
            primary {receipt.evidence_grades.grade_counts.primary} · supporting{' '}
            {receipt.evidence_grades.grade_counts.supporting} · contextual{' '}
            {receipt.evidence_grades.grade_counts.contextual} · unverified{' '}
            {receipt.evidence_grades.grade_counts.unverified} · prior_reading{' '}
            {receipt.evidence_grades.grade_counts.prior_reading}
            {' · '}
            hallucinations {receipt.evidence_grades.hallucination_count}
          </div>
        ) : (
          <Unavailable reason={receipt.evidence_grades.unavailable_reason} />
        )}
      </Section>

      <Section title="Honest gaps">
        {receipt.honest_gaps.status === 'measured' && receipt.honest_gaps.gaps ? (
          receipt.honest_gaps.gaps.length === 0 ? (
            <Empty label="no unserved floor items" />
          ) : (
            <ul style={{ margin: 0, paddingLeft: '16px' }}>
              {receipt.honest_gaps.gaps.map((g) => (
                <li key={g.floor_item_id}>
                  [{g.kind}] {g.floor_item_id} — {g.reason}
                </li>
              ))}
            </ul>
          )
        ) : (
          <Unavailable reason={receipt.honest_gaps.unavailable_reason} />
        )}
      </Section>

      <Section title="Safety decision">
        {receipt.safety_decision.status === 'measured' ? (
          <div>
            enforced={String(receipt.safety_decision.enforced)} severity={receipt.safety_decision.severity}{' '}
            action={receipt.safety_decision.action}
            {receipt.safety_decision.classes_detected && receipt.safety_decision.classes_detected.length > 0
              ? ` · classes: ${receipt.safety_decision.classes_detected.join(', ')}`
              : ''}
          </div>
        ) : (
          <Unavailable reason={receipt.safety_decision.unavailable_reason} />
        )}
      </Section>

      <Section title="Calibration disclosure">
        <div>{receipt.calibration_disclosure.disclosure_note}</div>
      </Section>

      <Section title="Prose binding">
        <div>
          {receipt.prose_binding.blocks.length} block(s) · {receipt.prose_binding.accumulated_char_count} chars ·
          sha256 {receipt.prose_binding.accumulated_text_sha256.slice(0, 16)}…
        </div>
      </Section>

      <Section title="Provenance">
        <div>
          build_id={receipt.provenance.build_id ?? '(none)'} priors_version={receipt.provenance.priors_version}{' '}
          now={receipt.provenance.now_context_date}
        </div>
      </Section>

      <div style={{ opacity: 0.6, fontSize: '9px' }}>receipt_hash {receipt.receipt_hash.slice(0, 24)}…</div>
    </div>
  )
}

function Header({ receipt }: { receipt: AcharyaReadingReceipt }) {
  return (
    <div style={{ color: 'var(--pp-gold)', fontSize: '9.5px', letterSpacing: '0.08em', textTransform: 'uppercase' }}>
      Acharya Reading Receipt v{receipt.receipt_schema_version} · turn {receipt.turn_id.slice(0, 8)} ·{' '}
      {receipt.generated_at}
    </div>
  )
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <div style={{ color: 'var(--pp-gold-tertiary)', fontSize: '9px', textTransform: 'uppercase', marginBottom: '4px' }}>
        {title}
      </div>
      {children}
    </div>
  )
}

function Unavailable({ reason }: { reason: string | null }) {
  return <div style={{ opacity: 0.7 }}>— unavailable: {reason ?? '(no reason recorded)'}</div>
}

function Empty({ label }: { label: string }) {
  return <div style={{ opacity: 0.7 }}>— {label}</div>
}

function Note({ text }: { text: string }) {
  return (
    <div style={{ opacity: 0.7, marginTop: '2px' }}>
      {text}
    </div>
  )
}
