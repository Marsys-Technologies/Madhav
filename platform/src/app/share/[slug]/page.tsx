import { notFound } from 'next/navigation'
import Link from 'next/link'
import { publicReading } from '@/lib/share/publicReading'
import { ReadingView, PrintReadingButton } from '@/components/chat/ReadingView'
export const dynamic = 'force-dynamic'

export default async function SharedConversationPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params
  const reading = await publicReading(slug)
  if (reading.state === 'missing') notFound()
  if (reading.state === 'unavailable') return <main className="dark mx-auto min-h-dvh max-w-3xl bg-background px-4 py-10 text-foreground"><h1 className="text-2xl font-heading">This reading is no longer available</h1><p className="mt-3">The link has expired, was revoked, or access has changed.</p></main>
  return <main className="dark mx-auto min-h-dvh max-w-3xl bg-background px-4 py-8 text-foreground print:max-w-none print:bg-white print:text-black">
    <style>{`@media print { body { background:white!important; color:black!important; font-size:12pt } details { display:none } }`}</style>
    <p className="mb-2 text-xs text-muted-foreground print:hidden">Shared reading · read-only</p>
    <h1 className="mb-6 text-2xl font-heading">{reading.title}</h1>
    <PrintReadingButton />
    <ReadingView messages={reading.messages} />
    <footer className="mt-8 print:hidden"><Link href={`/share/${encodeURIComponent(slug)}/print`}>Open print view</Link></footer>
  </main>
}
