import Link from 'next/link'
import { fetchBuildState } from '@/lib/build/dataSource'
import { parseUsageFilter, usageSummary } from '@/lib/metering/queries'
import { meteringEnabled } from '@/lib/metering/types'
import { getFlag } from '@/lib/config'

export const dynamic = 'force-dynamic'

export default async function BuildCockpitPage() {
  const now = new Date()
  let activity: Awaited<ReturnType<typeof usageSummary>> | null = null
  let feed: 'current' | 'delayed' = 'delayed'
  if (meteringEnabled()) {
    try {
      const filter = parseUsageFilter(new URL('https://local.invalid/?view=summary&from=' + encodeURIComponent(new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate())).toISOString()) + '&to=' + encodeURIComponent(now.toISOString())), { ownerId: null })
      activity = await usageSummary(filter, { ownerId: null })
    } catch { /* A failed data source is not a zero. */ }
  }
  try { await fetchBuildState(); feed = 'current' } catch { /* The main Cockpit remains available. */ }
  const calls = activity ? Number(activity.transport_attempts) : null
  const complete = activity && calls ? Math.round(Number(activity.complete_usage) / calls * 100) : null
  const failures = activity ? Number(activity.transport_failed) : null
  return <main className="mx-auto max-w-6xl space-y-8 px-4 py-8 text-[#e8dfc9] sm:px-8" style={{ fontFamily: 'var(--font-sans), sans-serif' }}>
    <div><p className="text-xs uppercase tracking-[0.17em] text-[#ac8a48]">AI operations</p><h1 className="mt-1 text-5xl text-[#d2a23c]" style={{ fontFamily: 'var(--font-cormorant), Georgia, serif', fontVariant: 'small-caps', letterSpacing: '.05em' }}>Cockpit</h1><p className="mt-2 text-sm text-[#a99c82]">A starting point for model configuration and observed activity.</p></div>
    <div className="grid gap-4 md:grid-cols-2">
      {getFlag('AI_CONSOLE_BYOK') && <Link href="/ai-console" className="rounded-xl border border-[#57401c] bg-[#14110b] p-6 transition-colors hover:border-[#d2a23c]"><p className="text-xs uppercase tracking-[0.17em] text-[#ac8a48]">Configuration</p><h2 className="mt-2 text-3xl text-[#ecc56a]" style={{ fontFamily: 'var(--font-cormorant), Georgia, serif' }}>AI Console</h2><p className="mt-3 text-sm text-[#b8aa8d]">Models, access, routing, and provider checks.</p><p className="mt-6 text-sm text-[#d2a23c]">Open AI Console →</p></Link>}
      <Link href="/observatory" className="rounded-xl border border-[#57401c] bg-[#14110b] p-6 transition-colors hover:border-[#d2a23c]"><p className="text-xs uppercase tracking-[0.17em] text-[#ac8a48]">Activity</p><h2 className="mt-2 text-3xl text-[#ecc56a]" style={{ fontFamily: 'var(--font-cormorant), Georgia, serif' }}>Observatory</h2><p className="mt-3 text-sm text-[#b8aa8d]">Overview, analytics, and conversation-level consumption.</p><p className="mt-6 text-sm text-[#d2a23c]">Open Observatory →</p></Link>
    </div>
    <section aria-label="Today at a glance" className="grid gap-3 sm:grid-cols-3">
      <Link href="/observatory" className="rounded-xl border border-[#382b18] bg-[#14110b] p-5"><p className="text-xs uppercase tracking-widest text-[#ac8a48]">Calls today · UTC</p><p className="mt-2 text-3xl text-[#ecc56a] tabular-nums">{calls == null ? 'Not reported' : calls.toLocaleString('en-IN')}</p></Link>
      <Link href="/observatory/analytics" className="rounded-xl border border-[#382b18] bg-[#14110b] p-5"><p className="text-xs uppercase tracking-widest text-[#ac8a48]">Call health</p><p className="mt-2 text-3xl text-[#ecc56a] tabular-nums">{failures == null ? 'Not reported' : failures === 0 ? 'No failed calls' : `${failures} failed`}</p></Link>
      <Link href="/observatory/consumption" className="rounded-xl border border-[#382b18] bg-[#14110b] p-5"><p className="text-xs uppercase tracking-widest text-[#ac8a48]">Usage evidence</p><p className="mt-2 text-3xl text-[#ecc56a] tabular-nums">{calls === 0 ? 'No calls' : complete == null ? 'Not reported' : `${complete}% complete`}</p></Link>
    </section>
    {feed === 'delayed' && <p className="text-xs text-[#a99c82]">Build status feed delayed. The AI Console and Observatory remain available.</p>}
  </main>
}
