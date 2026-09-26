import { describe, expect, it } from 'vitest'
import nextConfig from '../../../next.config'

describe('retired Cockpit sections', () => {
  it('returns old secondary-section URLs to the main Cockpit', async () => {
    const redirects = await nextConfig.redirects?.()
    const retiredSections = [
      'plan',
      'sessions',
      'registry',
      'interventions',
      'parallel',
      'health',
      'activity',
    ]

    for (const section of retiredSections) {
      expect(redirects).toContainEqual({
        source: `/cockpit/${section}/:path*`,
        destination: '/cockpit',
        permanent: false,
      })
    }
  })
})
