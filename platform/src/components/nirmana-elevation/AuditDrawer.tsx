'use client'

import type { RefObject } from 'react'
import { FileSearch, X } from 'lucide-react'
import type { NirmanaElevationSnapshotV2 } from '@/lib/nirmana-elevation/types'
import {
  Sheet,
  SheetClose,
  SheetContent,
  SheetDescription,
  SheetTitle,
  SheetTrigger,
} from '@/components/ui/sheet'

function formatTime(value: string | null): string {
  if (!value) return 'Unknown'
  const date = new Date(value)
  if (Number.isNaN(date.valueOf())) return 'Unknown'
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: 'medium',
    timeStyle: 'medium',
  }).format(date)
}

function evidenceFor(snapshot: NirmanaElevationSnapshotV2, assetId: string | null) {
  const assets = assetId
    ? snapshot.assets.filter((asset) => asset.asset_id === assetId)
    : snapshot.assets
  return assets.flatMap((asset) => asset.evidence_refs.map((reference) => ({
    assetId: asset.asset_id,
    reference,
  })))
}

function receiptsFor(snapshot: NirmanaElevationSnapshotV2, assetId: string | null) {
  return assetId
    ? snapshot.audit.receipts.filter((receipt) => receipt.related_asset_ids.includes(assetId))
    : snapshot.audit.receipts
}

function ledgerReferencesFor(
  snapshot: NirmanaElevationSnapshotV2,
  assetId: string | null,
  receipts: NirmanaElevationSnapshotV2['audit']['receipts'],
) {
  if (!assetId) return snapshot.audit.raw_ledger_refs
  const campaignEventRefs = new Set(receipts.map((receipt) => receipt.ledger_ref))
  const buildRunRefs = new Set(receipts.map((receipt) => receipt.source_ref).filter((reference) => reference.startsWith('build_run:')))
  return snapshot.audit.raw_ledger_refs.filter((reference) => reference.ledger_kind === 'campaign_event'
    ? campaignEventRefs.has(reference.ledger_ref)
    : buildRunRefs.has(reference.ledger_ref))
}

export function AuditDrawer({ snapshot, assetId, open, onOpenChange, finalFocus }: {
  snapshot: NirmanaElevationSnapshotV2
  assetId: string | null
  open: boolean
  onOpenChange: (open: boolean) => void
  finalFocus: RefObject<HTMLElement | null>
}) {
  const evidence = evidenceFor(snapshot, assetId)
  const receipts = receiptsFor(snapshot, assetId)
  const ledgerReferences = ledgerReferencesFor(snapshot, assetId, receipts)

  return <Sheet open={open} onOpenChange={onOpenChange}>
    <div className="flex justify-end">
      <SheetTrigger className="inline-flex items-center gap-2 rounded-lg border border-brand-border bg-brand-surface px-3 py-2 text-xs font-medium text-brand-text-2 transition-colors hover:border-brand-gold-1 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-gold-1">
        <FileSearch aria-hidden="true" className="size-4 text-brand-gold-2" />
        Audit evidence · {evidence.length} {evidence.length === 1 ? 'reference' : 'references'} · {snapshot.data_quality.verdict}
      </SheetTrigger>
    </div>
    <SheetContent side="right" showCloseButton={false} finalFocus={finalFocus} className="w-full max-w-lg gap-0 overflow-y-auto border-brand-border bg-brand-bg p-0 text-brand-text-2 shadow-2xl sm:max-w-lg">
      <header className="sticky top-0 flex items-start justify-between gap-3 border-b border-brand-border bg-brand-bg px-4 py-3">
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-brand-gold-1">Read-only evidence</p>
          <SheetTitle className="mt-1 text-lg font-semibold text-brand-text-1">Campaign evidence audit</SheetTitle>
          <SheetDescription className="mt-1 text-xs text-brand-text-3">{assetId ? <>Filtered to <span className="font-mono">{assetId}</span></> : 'All campaign assets'} · Data quality: <span className="capitalize">{snapshot.data_quality.verdict}</span></SheetDescription>
        </div>
        <SheetClose aria-label="Close audit drawer" className="rounded p-1.5 text-brand-text-3 transition-colors hover:bg-brand-surface hover:text-brand-text-1 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-gold-1"><X aria-hidden="true" className="size-4" /></SheetClose>
      </header>

      <div className="space-y-5 px-4 py-4 text-sm text-brand-text-2">
        <section aria-labelledby="audit-sources-heading">
          <h3 id="audit-sources-heading" className="text-xs font-semibold uppercase tracking-[0.14em] text-brand-text-1">Source provenance and observation</h3>
          <ul className="mt-2 space-y-2">{snapshot.sources.map((source) => <li key={source.source_id} className="rounded-lg border border-brand-border bg-brand-surface p-3">
            <div className="flex flex-wrap items-center justify-between gap-2"><span className="font-mono text-xs text-brand-gold-2">{source.source_id}</span><span className="text-xs capitalize text-brand-text-3">{source.state}</span></div>
            <p className="mt-1">{source.provenance}</p>
            <p className="mt-1 text-xs text-brand-text-3">Observed <time dateTime={source.observed_at ?? undefined}>{formatTime(source.observed_at)}</time>{source.age_seconds === null ? '' : ` · ${source.age_seconds}s old`}</p>
            {source.error_code && <p className="mt-1 font-mono text-xs text-brand-err">{source.error_code}</p>}
            {source.error_message && <p className="mt-1 text-xs text-brand-err">{source.error_message}</p>}
          </li>)}</ul>
        </section>

        <section aria-labelledby="audit-release-heading">
          <h3 id="audit-release-heading" className="text-xs font-semibold uppercase tracking-[0.14em] text-brand-text-1">Release observation</h3>
          <dl className="mt-2 grid gap-2 rounded-lg border border-brand-border bg-brand-surface p-3 sm:grid-cols-2">
            <div><dt className="text-xs text-brand-text-3">Main SHA</dt><dd className="mt-1 break-all font-mono text-xs text-brand-text-1">{snapshot.release.main_sha ?? 'Unknown'}</dd></div>
            <div><dt className="text-xs text-brand-text-3">Deployed SHA</dt><dd className="mt-1 break-all font-mono text-xs text-brand-text-1">{snapshot.release.deployed_sha ?? 'Unknown'}</dd></div>
            <div><dt className="text-xs text-brand-text-3">Deployed revision</dt><dd className="mt-1 break-all font-mono text-xs text-brand-text-1">{snapshot.release.deployed_revision ?? 'Unknown'}</dd></div>
            <div><dt className="text-xs text-brand-text-3">Production / main</dt><dd className="mt-1 text-brand-text-1">{snapshot.release.production_in_sync === true ? 'In sync' : snapshot.release.production_in_sync === false ? 'Out of sync' : 'Unknown'}</dd></div>
            <div className="sm:col-span-2"><dt className="text-xs text-brand-text-3">Observed</dt><dd className="mt-1 text-brand-text-1"><time dateTime={snapshot.release.observed_at ?? undefined}>{formatTime(snapshot.release.observed_at)}</time></dd></div>
          </dl>
        </section>

        <section aria-labelledby="audit-contradictions-heading">
          <h3 id="audit-contradictions-heading" className="text-xs font-semibold uppercase tracking-[0.14em] text-brand-text-1">Contradictions and gaps</h3>
          {[...snapshot.data_quality.contradictions, ...snapshot.data_quality.gaps].length > 0
            ? <ul className="mt-2 list-disc space-y-1 rounded-lg border border-brand-warn/50 bg-brand-warn/10 px-7 py-3">{[...snapshot.data_quality.contradictions, ...snapshot.data_quality.gaps].map((item) => <li key={item}>{item}</li>)}</ul>
            : <p className="mt-2 rounded-lg border border-brand-border bg-brand-surface p-3 text-brand-text-3">None recorded.</p>}
        </section>

        <section aria-labelledby="audit-evidence-heading">
          <h3 id="audit-evidence-heading" className="text-xs font-semibold uppercase tracking-[0.14em] text-brand-text-1">Evidence references · {evidence.length}</h3>
          {evidence.length > 0
            ? <ul className="mt-2 space-y-2">{evidence.map((item, index) => <li key={`${item.assetId}:${item.reference}:${index}`} className="rounded-lg border border-brand-border bg-brand-surface p-3"><p className="font-mono text-[10px] text-brand-text-3">{item.assetId}</p><p className="mt-1 break-all font-mono text-xs text-brand-text-1">{item.reference}</p></li>)}</ul>
            : <p className="mt-2 rounded-lg border border-brand-border bg-brand-surface p-3 text-brand-text-3">No evidence references recorded for this selection.</p>}
        </section>

        <section aria-labelledby="audit-receipts-heading">
          <h3 id="audit-receipts-heading" className="text-xs font-semibold uppercase tracking-[0.14em] text-brand-text-1">Accepted receipt provenance · {receipts.length}</h3>
          {receipts.length > 0
            ? <ul className="mt-2 space-y-2">{receipts.map((receipt) => <li key={receipt.ledger_ref} className="rounded-lg border border-brand-border bg-brand-surface p-3">
              <dl className="grid gap-2 sm:grid-cols-2">
                <div><dt className="text-xs text-brand-text-3">Receipt type</dt><dd className="mt-1 break-all font-mono text-xs text-brand-text-1">{receipt.event_type}</dd></div>
                <div><dt className="text-xs text-brand-text-3">Entity</dt><dd className="mt-1 break-all font-mono text-xs text-brand-text-1">{receipt.entity_type}:{receipt.entity_id}</dd></div>
                <div><dt className="text-xs text-brand-text-3">Source kind</dt><dd className="mt-1 break-all font-mono text-xs text-brand-text-1">{receipt.source_kind}</dd></div>
                <div><dt className="text-xs text-brand-text-3">Layer</dt><dd className="mt-1 text-xs text-brand-text-1">{receipt.layer ?? 'Campaign-wide'}</dd></div>
                <div className="sm:col-span-2"><dt className="text-xs text-brand-text-3">Source reference</dt><dd className="mt-1 break-all font-mono text-xs text-brand-text-1">{receipt.source_ref}</dd></div>
                <div><dt className="text-xs text-brand-text-3">Observed</dt><dd className="mt-1 text-xs text-brand-text-1"><time dateTime={receipt.observed_at}>{formatTime(receipt.observed_at)}</time></dd></div>
                <div><dt className="text-xs text-brand-text-3">Recorded</dt><dd className="mt-1 text-xs text-brand-text-1"><time dateTime={receipt.recorded_at}>{formatTime(receipt.recorded_at)}</time></dd></div>
                <div className="sm:col-span-2"><dt className="text-xs text-brand-text-3">Accepted payload SHA-256</dt><dd className="mt-1 break-all font-mono text-xs text-brand-text-1">{receipt.payload_sha256}</dd></div>
                <div className="sm:col-span-2"><dt className="text-xs text-brand-text-3">Ledger reference</dt><dd className="mt-1 break-all font-mono text-xs text-brand-text-1">{receipt.ledger_ref}</dd></div>
              </dl>
            </li>)}</ul>
            : <p className="mt-2 rounded-lg border border-brand-border bg-brand-surface p-3 text-brand-text-3">No accepted receipts recorded for this selection.</p>}
        </section>

        <section aria-labelledby="audit-ledgers-heading">
          <h3 id="audit-ledgers-heading" className="text-xs font-semibold uppercase tracking-[0.14em] text-brand-text-1">Raw ledger references · {ledgerReferences.length}</h3>
          {ledgerReferences.length > 0
            ? <ul className="mt-2 space-y-2">{ledgerReferences.map((reference) => <li key={`${reference.ledger_kind}:${reference.ledger_ref}`} className="rounded-lg border border-brand-border bg-brand-surface p-3"><span className="font-mono text-[10px] uppercase text-brand-text-3">{reference.ledger_kind}</span><p className="mt-1 break-all font-mono text-xs text-brand-text-1">{reference.ledger_ref}</p></li>)}</ul>
            : <p className="mt-2 rounded-lg border border-brand-border bg-brand-surface p-3 text-brand-text-3">No raw ledger references recorded.</p>}
        </section>
      </div>
    </SheetContent>
  </Sheet>
}
