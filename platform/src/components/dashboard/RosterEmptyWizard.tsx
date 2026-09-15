import Link from 'next/link'
import { Navagraha } from '@/components/brand/Navagraha'

export function RosterEmptyWizard() {
  return (
    <div className="relative flex min-h-[420px] items-center justify-center overflow-hidden rounded-xl bg-[radial-gradient(ellipse_at_50%_50%,rgba(13,10,5,0.4)_0%,rgba(2,2,1,0.9)_100%)] border border-[rgba(212,175,55,0.15)]">
      {/* Navagraha backdrop */}
      <Navagraha
        size={480}
        opacity={0.22}
        className="pointer-events-none absolute inset-0 m-auto"
      />

      {/* Content */}
      <div className="relative z-10 flex flex-col items-center gap-6 text-center">
        <h2 className="bt-heading text-[#fce29a]">
          Welcome. Begin with your first chart.
        </h2>
        <p className="text-sm text-[rgba(212,175,55,0.45)] max-w-xs">
          Each chart is a native&apos;s complete Jyotish record — facts, build corpus, and conversation history.
        </p>
        <Link href="/clients/new" className="brand-cta text-sm rounded-lg px-6 py-3 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--brand-gold)]">
          + Add first chart
        </Link>
      </div>
    </div>
  )
}
