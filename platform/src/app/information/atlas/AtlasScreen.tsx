import Link from 'next/link'
import { ArrowUpRight } from 'lucide-react'
import { AtlasView, type AtlasAsset } from '@/components/build/AtlasView'
import { PageTitle } from '@/components/journey1/Titles'
import styles from './atlas.module.css'

const destinations = [
  { title: 'Birth Charts', href: '/dashboard', description: 'Open a chart to reach its overview, consultation, prediction review, almanac and life events.' },
  { title: 'My Account', href: '/account', description: 'Manage your profile, security and reading preferences.' },
  { title: 'Consumption', href: '/account/ai-cockpit/consumption', description: 'Inspect your own recorded usage, from a conversation to an individual call.' },
  { title: 'Administration', href: '/admin', description: 'Manage access and review portal activity, system health and build evidence.' },
] as const

const layers = [
  ['Brahmagyan', 'Reference sources and rules', '#d2a23c'],
  ['Gaṇita', 'Chart facts and calculations', '#5b7fb5'],
  ['Bodha', 'Chart analysis and synthesis', '#4e9a98'],
  ['Kāla', 'Periods, transits and timing windows', '#9a84bc'],
  ['Phala', 'Readings and predictions', '#5fa37a'],
  ['Mīmāṃsā', 'Outcome review and calibration', '#b5565e'],
] as const

export function AtlasScreen({ assets, defaultChartId }: { assets: AtlasAsset[]; defaultChartId: string }) {
  return (
    <div className={styles.atlas}>
      <header className={styles.heading}>
        <PageTitle name="atlas" />
        <p>Find your way around Madhav and see how the six layers fit together.</p>
      </header>

      <section className={styles.section}>
        <h2>Portal guide</h2>
        <ul className={styles.guide}>
          {destinations.map(({ title, href, description }) => (
            <li key={href}>
              <Link href={href} className={styles.destination}>
                <span>{title}</span>
                <ArrowUpRight size={17} aria-hidden="true" />
                <p>{description}</p>
              </Link>
            </li>
          ))}
        </ul>
      </section>

      <div className={styles.referenceGrid}>
        <section className={styles.section}>
          <h2>The six layers</h2>
          <dl className={styles.layers}>
            {layers.map(([name, description, color]) => (
              <div key={name}>
                <dt><i aria-hidden="true" style={{ backgroundColor: color }} />{name}</dt>
                <dd>{description}</dd>
              </div>
            ))}
          </dl>
        </section>
        <section className={styles.section}>
          <h2>Updated destinations</h2>
          <ul className={styles.redirects}>
            <li><span>Earlier Asset Atlas link</span><a href="#asset-catalog">Asset Atlas below</a></li>
            <li><span>Earlier Persona settings</span><Link href="/account/ai-cockpit/personas">AI Personas</Link></li>
            <li><span>Earlier Usage page</span><Link href="/account/ai-cockpit/consumption">Consumption</Link></li>
          </ul>
        </section>
      </div>

      <section id="asset-catalog" className={styles.catalog}>
        <div className={styles.catalogHeading}>
          <h2>Asset Atlas</h2>
          <p>{assets.length} {assets.length === 1 ? 'asset' : 'assets'}</p>
        </div>
        <AtlasView assets={assets} defaultChartId={defaultChartId} />
      </section>
    </div>
  )
}
