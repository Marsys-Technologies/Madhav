// Observatory Reconciliation history page (server component shell). AuthGate
// is enforced by the parent layout. Provider tabs are URL-driven via the
// `provider` search param; the loader handles the optional filter.
// OBS-UX-S5: ObsPageShell wrapper.

import {
  ReconciliationHistoryView,
  loadReconciliationHistory,
} from '@/lib/components/observatory/reconciliation'
import { ObsPageShell } from '@/lib/components/observatory/shared'

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

  const subtitle =
    `Per-provider cost reconciliation against authoritative billing · ${total} total run${total === 1 ? '' : 's'}`

  return (
    <ObsPageShell title="Reconciliation" subtitle={subtitle}>
      <ReconciliationHistoryView
        selectedProvider={provider}
        rows={rows}
        total={total}
      />
    </ObsPageShell>
  )
}
