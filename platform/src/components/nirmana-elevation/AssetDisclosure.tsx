import type { NirmanaElevationSnapshotV2 } from '@/lib/nirmana-elevation/types'

function ReferenceList({ label, values }: { label: string; values: string[] }) {
  return <section>
    <h5 className="text-xs font-medium text-brand-text-2">{label}</h5>
    {values.length > 0
      ? <ul className="mt-1 flex flex-wrap gap-1.5">{values.map((value) => <li key={value} className="rounded bg-brand-bg px-1.5 py-0.5 font-mono text-xs text-brand-text-2">{value}</li>)}</ul>
      : <p className="mt-1 text-xs text-brand-text-3">None recorded</p>}
  </section>
}

export function AssetDisclosure({ asset, onOpenAudit }: { asset: NirmanaElevationSnapshotV2['assets'][number]; onOpenAudit: (assetId: string) => void }) {
  return <div className="space-y-3 border-t border-brand-border pt-3 text-sm text-brand-text-2">
    <div className="grid gap-3 sm:grid-cols-2">
      <section>
        <h5 className="text-xs font-medium text-brand-text-2">Current action</h5>
        <p className="mt-1">{asset.current_action ?? 'No current action recorded'}</p>
      </section>
      <section>
        <h5 className="text-xs font-medium text-brand-text-2">Next action</h5>
        <p className="mt-1">{asset.next_action ?? 'No next action recorded'}</p>
      </section>
      <section>
        <h5 className="text-xs font-medium text-brand-text-2">Blocker</h5>
        <p className={`mt-1 ${asset.blocker ? 'text-brand-err' : 'text-brand-text-3'}`}>{asset.blocker ?? 'No blocker recorded'}</p>
      </section>
      <section>
        <h5 className="text-xs font-medium text-brand-text-2">Producer inheritance</h5>
        <p className="mt-1">{asset.producer_id ? <>Inherited from <span className="font-mono">{asset.producer_id}</span></> : 'No producer inheritance recorded'}</p>
      </section>
    </div>
    <div className="grid gap-3 sm:grid-cols-2">
      <ReferenceList label="Dependencies" values={asset.depends_on} />
      <ReferenceList label="Unlocks" values={asset.unlocks} />
    </div>
    <button type="button" onClick={() => onOpenAudit(asset.asset_id)} className="rounded border border-brand-border px-2.5 py-1.5 text-xs font-medium text-brand-gold-2 transition-colors hover:border-brand-gold-1 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-gold-1">
      Audit details
    </button>
  </div>
}
