'use client'

import { useState } from 'react'
import { ChevronDown, ChevronRight } from 'lucide-react'
import type { NirmanaElevationSnapshotV2 } from '@/lib/nirmana-elevation/types'
import { AssetDisclosure } from './AssetDisclosure'
import { MilestoneBar } from './MilestoneBar'

function identityValue(value: string | null): string {
  return value ?? 'Not yet catalogued'
}

export function AssetCard({ asset, onOpenAudit }: { asset: NirmanaElevationSnapshotV2['assets'][number]; onOpenAudit: (assetId: string) => void }) {
  const [expanded, setExpanded] = useState(false)
  const disclosureId = `asset-disclosure-${asset.asset_id}`

  return <article className="min-w-0 rounded-lg border border-brand-border bg-brand-surface p-3">
    <div className="flex items-start justify-between gap-3">
      <div className="min-w-0 space-y-1">
        <h4 className="font-mono text-sm font-semibold text-brand-gold-2">{asset.asset_id}</h4>
        <p className="text-sm text-brand-text-1">{identityValue(asset.sanskrit_name)}</p>
        <p className="text-sm font-medium text-brand-text-1">{identityValue(asset.english_name)}</p>
        <p className="text-xs text-brand-text-2">{identityValue(asset.description)}</p>
      </div>
      <span className="shrink-0 rounded border border-brand-border px-1.5 py-0.5 text-[10px] capitalize text-brand-text-3">{asset.campaign_state}</span>
    </div>

    {asset.legacy_aliases.length > 0 && <div className="mt-2 space-y-1 border-l border-brand-border pl-2 text-xs text-brand-text-3">
      {asset.legacy_aliases.map((alias) => <p key={alias.asset_id}><span className="font-medium text-brand-text-2">Legacy alias</span> <span className="font-mono">{alias.asset_id}</span>{alias.sanskrit_name && <> · {alias.sanskrit_name}</>}{alias.english_name && <> · {alias.english_name}</>}</p>)}
    </div>}

    <div className="mt-3"><MilestoneBar asset={asset} /></div>

    <div className="mt-3 flex flex-wrap gap-2">
      <button type="button" aria-expanded={expanded} aria-controls={disclosureId} onClick={() => setExpanded((open) => !open)} className="inline-flex items-center gap-1 rounded border border-brand-border px-2.5 py-1.5 text-xs font-medium text-brand-text-2 transition-colors hover:border-brand-gold-1 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-gold-1">
        {expanded ? <ChevronDown aria-hidden="true" className="size-3.5" /> : <ChevronRight aria-hidden="true" className="size-3.5" />}
        {expanded ? 'Hide details' : 'Show details'} for {asset.asset_id}
      </button>
      <button type="button" aria-label={`Audit details for ${asset.asset_id}`} onClick={() => onOpenAudit(asset.asset_id)} className="rounded border border-brand-border px-2.5 py-1.5 text-xs font-medium text-brand-gold-2 transition-colors hover:border-brand-gold-1 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-gold-1">
        Audit details
      </button>
    </div>
    {expanded && <div id={disclosureId} className="mt-3"><AssetDisclosure asset={asset} onOpenAudit={onOpenAudit} /></div>}
  </article>
}
