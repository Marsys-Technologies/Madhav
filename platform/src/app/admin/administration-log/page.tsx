import { Suspense } from 'react'
import { AdministrationLog } from '@/components/admin/AdministrationLog'
export default function Page() { return <Suspense fallback={<p>Loading…</p>}><AdministrationLog /></Suspense> }
