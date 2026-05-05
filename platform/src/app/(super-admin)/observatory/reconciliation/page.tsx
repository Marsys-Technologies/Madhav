// Observatory Reconciliation history page (server component shell). AuthGate
// is enforced by the parent layout. Provider tabs are URL-driven via the
// `provider` search param; the loader handles the optional filter.

import {
  ReconciliationHistoryView,
  loadReconciliationHistory,
} from '@/lib/components/observatory/reconciliation'

export const dynamic = 'force-dynamic'

const VALID_PROVIDERS = new Set(['anthropic', 'openai', 'gemini', 'deepseek', 'nim'])

interface PageProps {
  searchParams?: Promise<{ provider?: string }>
}

export default async function ObservatoryReconciliationPage({
  searchParams,
}: PageProps) {
  const sp = (await searchParams) ?? {}
  const provider =
    typeof sp.provider === 'string' && VALID_PROVIDERS.has(sp.provider)
      ? sp.provider
      : null

  const { rows, total } = await loadReconciliationHistory({
    provider: provider ?? undefined,
    limit: 50,
  })

  return (
    <div className="min-h-full bg-[var(--brand-charcoal,oklch(0.10_0.012_70))]">
      <div className="p-6">
        <ReconciliationHistoryView
          selectedProvider={provider}
          rows={rows}
          total={total}
        />
      </div>
    </div>
  )
}
