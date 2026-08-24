import type { Metadata } from 'next'
import { NirmanaElevationTracker } from '@/components/nirmana-elevation/NirmanaElevationTracker'

export const dynamic = 'force-dynamic'

export const metadata: Metadata = {
  title: 'Nirmāṇa Elevation Tracker — MARSYS-JIS Admin',
}

/** The admin layout applies the authenticated super_admin gate. */
export default function NirmanaElevationPage() {
  return <NirmanaElevationTracker />
}
