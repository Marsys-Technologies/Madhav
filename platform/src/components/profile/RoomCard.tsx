import Link from 'next/link'
import { cn } from '@/lib/utils'

interface RoomCardCTA {
  label: string
  href: string
  disabled?: boolean
  tooltip?: string
}

interface RoomCardProps {
  title: string
  description?: string
  cta: RoomCardCTA
  children?: React.ReactNode
  className?: string
}

export function RoomCard({ title, description, cta, children, className }: RoomCardProps) {
  return (
    <div
      className={cn(
        'flex flex-col gap-4 rounded-lg border p-5',
        'border-[rgba(var(--brand-gold-rgb),0.2)]',
        'bg-[#191408]',
        className,
      )}
    >
      <div className="flex flex-col gap-1">
        <h2
          className="text-base font-semibold"
          style={{ color: 'var(--brand-gold-cream)' }}
        >
          {title}
        </h2>
        {description && (
          <p className="text-xs" style={{ color: 'var(--brand-gold)', opacity: 0.6 }}>
            {description}
          </p>
        )}
      </div>

      {children && <div className="flex-1">{children}</div>}

      <div className="mt-auto">
        {cta.disabled ? (
          <span
            title={cta.tooltip}
            aria-disabled="true"
            className="inline-flex min-h-[44px] cursor-not-allowed items-center gap-1 py-2 text-xs opacity-60"
            style={{ color: 'var(--brand-gold)' }}
          >
            {cta.label}
          </span>
        ) : (
          <Link
            href={cta.href}
            className="inline-flex min-h-[44px] items-center gap-1 py-2 text-sm font-medium transition-opacity hover:opacity-80"
            style={{ color: 'var(--brand-gold)' }}
          >
            {cta.label} →
          </Link>
        )}
      </div>
    </div>
  )
}
