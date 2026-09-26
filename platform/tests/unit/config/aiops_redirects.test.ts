import { describe, expect, it } from 'vitest'
import nextConfig from '../../../next.config'

describe('AIOps route compatibility', () => {
  it('sends retired AIOps URLs to the maintained Observatory surface', async () => {
    const redirects = await nextConfig.redirects?.()

    expect(redirects).toEqual(expect.arrayContaining([
      {
        source: '/aiops',
        destination: '/observatory',
        permanent: false,
      },
      {
        source: '/aiops/:path*',
        destination: '/observatory',
        permanent: false,
      },
    ]))
  })
})
