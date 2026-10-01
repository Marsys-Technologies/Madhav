import { notFound } from 'next/navigation'
import { meteringEnabled } from '@/lib/metering/types'
import { UsageDashboard } from '@/components/metering/UsageDashboard'
export const dynamic='force-dynamic'
export default function MeteringPage() {
 if(!meteringEnabled()||process.env.MARSYS_FLAG_OBSERVATORY_ENABLED!=='true')notFound()
 return <UsageDashboard admin/>
}
