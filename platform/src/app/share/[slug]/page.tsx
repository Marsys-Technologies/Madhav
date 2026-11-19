import { notFound } from 'next/navigation'
import type { Metadata } from 'next'
import { requireActiveUserPage } from '@/lib/auth/active-user-page-guard'
import { readSharedConversationView } from '@/lib/share/sharedConversationView'
import { renderSharedReading } from './renderSharedReading'

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

  return renderSharedReading({
    title: view.title,
    optionalChartName: view.optionalChartName,
    visibleMessages: view.visibleMessages,
  })
}
