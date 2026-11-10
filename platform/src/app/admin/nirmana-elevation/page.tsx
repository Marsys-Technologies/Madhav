import type { Metadata } from 'next'
import { NirmanaElevationTracker } from '@/components/nirmana-elevation/NirmanaElevationTracker'

export const dynamic = 'force-dynamic'

export const metadata: Metadata = {
  title: 'Nirmāṇa Elevation Tracker — MARSYS-JIS Admin',
}

/** The admin layout applies the authenticated super_admin gate. */
export default function NirmanaElevationPage() {
  return (
    <div className="min-w-0 rounded-xl border border-brand-border bg-brand-bg px-4 text-brand-text-1">
      <NirmanaElevationTracker />
    </div>
  )
}
