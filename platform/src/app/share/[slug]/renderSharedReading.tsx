import Link from 'next/link'
import type { ShareViewMessage } from '@/lib/share/shareView'
import { SharedConversation } from './SharedConversation'
import styles from './folio.module.css'

export function renderSharedReading({
  title, optionalChartName, visibleMessages,
}: {
  title: string | null
  optionalChartName?: string | null
  visibleMessages: ShareViewMessage[]
}) {
  return (
    <div className={styles.page}>
      <div className={styles.reading}>
        {/* X-S9: @media print — inline style ensures ≥12pt body text in print context */}
        <style>{`@media print { body { font-size: 12pt; } }`}</style>

        <header className={`mb-6 border-b border-border pb-4 print:border-b-0 print:mb-4 ${styles.header}`}>
          {/* "Shared conversation" label is UI chrome — hidden in print */}
          <p className="text-[11px] font-medium uppercase tracking-widest text-muted-foreground print:hidden">
            Shared conversation
          </p>
          <h1 className="mt-1 font-heading text-2xl font-semibold text-foreground print:text-black print:mt-0">
            {title ?? 'Untitled chat'}
          </h1>
          {optionalChartName && (
            <p className="mt-1 text-sm text-muted-foreground print:text-gray-600">{optionalChartName}</p>
          )}
        </header>
        <main className={`flex-1 print:text-black ${styles.transcript}`}>
          <SharedConversation messages={visibleMessages} />
        </main>
        {/* Footer is navigation chrome — hidden in print */}
        <footer className="mt-8 border-t border-border pt-4 text-center text-xs text-muted-foreground print:hidden">
          <Link href="/" className={`hover:text-foreground ${styles.homeLink}`}>
            MARSYS-JIS
          </Link>
        </footer>
      </div>
    </div>
  )
}
