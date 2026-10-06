import { Suspense } from 'react'
import { OperatorActivity } from '@/components/admin/OperatorActivity'
export default function Page() { return <Suspense fallback={<p>Loading…</p>}><OperatorActivity view="consumption" /></Suspense> }
