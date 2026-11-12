import { notFound } from 'next/navigation'
import Link from 'next/link'
import type { Metadata } from 'next'
import { requireActiveUserPage } from '@/lib/auth/active-user-page-guard'
import { readSharedConversationView } from '@/lib/share/sharedConversationView'
import { SharedConversation } from './SharedConversation'
import styles from './folio.module.css'

export const dynamic = 'force-dynamic'

// SS N-376 / PR-S4: a shared conversation is never indexed and never leaks its URL
// (the slug) through a Referer header. next.config.ts sends the matching
// X-Robots-Tag / Referrer-Policy / Cache-Control response headers.
export const metadata: Metadata = {
  robots: { index: false, follow: false },
  referrer: 'no-referrer',
}

const SLUG_SHAPE = /^[A-Za-z0-9]{10}$/

function loginPathFor(slug: string): string {
  return SLUG_SHAPE.test(slug)
    ? `/login?next=${encodeURIComponent(`/share/${slug}`)}`
    : '/login'
}

export default async function SharedConversationPage({
  params,
}: {
  params: Promise<{ slug: string }>
}) {
  const { slug } = await params

  // SS N-376 / PR-S4: share links are authenticated BY DESIGN. proxy.ts only checks
  // the cookie's shape, so verify the session here (firebase-admin
  // verifySessionCookie with revocation check + an ACTIVE profile) before ANY read
  // of the share, conversation, chart or messages. Any verified, active user who
  // holds the slug may view: no owner check, that is the point of a share link.
  // SS N-379: a refused visitor goes to /login?next=/share/<slug> so the login page
  // can bring them back (it re-validates `next` with safeNextPath). The slug is
  // only echoed when it has the exact minted shape; otherwise plain /login.
  const viewer = await requireActiveUserPage(loginPathFor(slug))
  const view = await readSharedConversationView({ slug, verifiedViewerUid: viewer.user.uid })
  if (!view) notFound()

  return (
    <div className="mx-auto flex min-h-[100dvh] max-w-3xl flex-col px-4 py-6 print:max-w-none print:px-0 print:py-0">
      {/* X-S9: @media print — inline style ensures ≥12pt body text in print context */}
      <style>{`@media print { body { font-size: 12pt; } }`}</style>

      <header className={`mb-6 border-b border-border pb-4 print:border-b-0 print:mb-4 ${styles.header}`}>
        {/* "Shared conversation" label is UI chrome — hidden in print */}
        <p className="text-[11px] font-medium uppercase tracking-widest text-muted-foreground print:hidden">
          Shared conversation
        </p>
        <h1 className="mt-1 font-heading text-2xl font-semibold text-foreground print:text-black print:mt-0">
          {view.title ?? 'Untitled chat'}
        </h1>
        {view.optionalChartName && (
          <p className="mt-1 text-sm text-muted-foreground print:text-gray-600">{view.optionalChartName}</p>
        )}
      </header>
      <main className={`flex-1 print:text-black ${styles.transcript}`}>
        <SharedConversation messages={view.visibleMessages} />
      </main>
      {/* Footer is navigation chrome — hidden in print */}
      <footer className="mt-8 border-t border-border pt-4 text-center text-xs text-muted-foreground print:hidden">
        <Link href="/" className={`hover:text-foreground ${styles.homeLink}`}>
          MARSYS-JIS
        </Link>
      </footer>
    </div>
  )
}
