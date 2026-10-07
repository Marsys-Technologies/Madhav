/** Component-browser test host. Browser-check.mts supplies synthetic HTTP data. */
import { createRoot } from 'react-dom/client'
import '@/app/globals.css'
import '@/app/journey1.css'
import { JourneyShell } from '@/components/journey1/JourneyShell'
import { PariprashnaApp } from '@/components/pariprashna/PariprashnaApp'
const chart='22222222-2222-4222-8222-222222222222',thread='11111111-1111-4111-8111-111111111111'
createRoot(document.getElementById('root')!).render(<JourneyShell chartId={chart} user={{uid:'journey2-owner',name:'Synthetic user'}} role="guest"><PariprashnaApp chartId={chart} initialThread={thread} chartPin={{name:'Synthetic Journey Two',bornLine:'Synthetic test data'}} byokEnabled={false}/></JourneyShell>)
