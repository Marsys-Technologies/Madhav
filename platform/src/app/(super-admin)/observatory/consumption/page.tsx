import { ObservatoryDashboard } from '@/components/observatory/ObservatoryDashboard'
export const dynamic = 'force-dynamic'
export default async function ObservatoryConsumptionPage({ searchParams }: {
  searchParams: Promise<Record<string, string | string[] | undefined>>
}) {
  const raw = await searchParams
  const initialFilters: Record<string, string> = {}
  for (const key of ['from', 'to', 'channel', 'provider', 'model', 'purpose']) {
    const value = raw[key]
    if (typeof value === 'string') initialFilters[key] = value
  }
  return <ObservatoryDashboard view="consumption" initialFilters={initialFilters} />
}
