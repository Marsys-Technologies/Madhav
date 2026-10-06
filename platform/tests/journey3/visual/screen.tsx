import { createRoot } from 'react-dom/client'
import { JourneyShell } from '@/components/journey1/JourneyShell'
import { PageTitle } from '@/components/journey1/Titles'
import { ChartNav } from '@/components/journey1/ChartNav'
import { CockpitShell } from '@/lib/components/cockpit/v2/CockpitShell'
import '@/app/globals.css'
import '@/lib/styles/marsys-theme.css'
import '@/app/journey1.css'
createRoot(document.getElementById('root')!).render(<JourneyShell user={{ uid: 'fixture', name: 'Fictional User' }} role="super_admin" chartId="fictional-chart">
  <div className="j1-container"><p className="j1-note">Component verification · fictional data · execution disabled</p>
  <ChartNav chartId="fictional-chart" canBuild active="preparation" />
  <PageTitle name="preparation" />
  <p className="j1-note" style={{ margin: '12px 0 24px' }}>Each layer builds on the one beneath it. Partial readiness is normal; Consultation identifies any additional preparation a question needs.</p>
  <CockpitShell chartId="fictional-chart" initialChartMeta={{ subject_name: 'Fictional Native', birth_date: '1990-01-01', birth_place: 'Fictional birthplace' }} variant="preparation" />
</div></JourneyShell>)
