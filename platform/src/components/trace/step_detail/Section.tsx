export function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <h3 className="text-[10px] font-semibold uppercase tracking-widest text-[var(--folio-action)] mb-2">
        {title}
      </h3>
      {children}
    </div>
  )
}
