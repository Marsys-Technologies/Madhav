export function ProvenanceChip({ kind }: { kind: 'repo_declared' | 'evidence_derived' }) {
  const label = kind === 'repo_declared' ? 'Repo-declared' : 'Evidence-derived'
  const className = kind === 'repo_declared'
    ? 'border-brand-warn/60 text-brand-warn'
    : 'border-brand-ok/50 text-brand-ok'
  return <span
    className={`inline-flex items-center rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.1em] ${className}`}
    title={kind === 'repo_declared' ? 'Sourced from the committed programme manifest, not the evidence ledger' : 'Derived from accepted campaign evidence'}
  >{label}</span>
}
