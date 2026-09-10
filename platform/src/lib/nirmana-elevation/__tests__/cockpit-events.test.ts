import { afterEach, describe, expect, it, vi } from 'vitest'

const publishMessage = vi.fn().mockResolvedValue(undefined)
const topic = vi.fn(() => ({ publishMessage }))
class MockPubSub {
  topic = topic
}
vi.mock('@google-cloud/pubsub', () => ({ PubSub: MockPubSub }))

describe('publishCockpitEvent', () => {
  afterEach(() => {
    vi.unstubAllEnvs()
    publishMessage.mockClear()
  })

  it('no-ops when GOOGLE_CLOUD_PROJECT is unset', async () => {
    vi.stubEnv('GOOGLE_CLOUD_PROJECT', '')
    const { publishCockpitEvent } = await import('../cockpit-events')
    await publishCockpitEvent({ type: 'nirmana.capsule_accepted' })
    expect(publishMessage).not.toHaveBeenCalled()
  })

  it('no-ops when PUBSUB_DISABLED is set', async () => {
    vi.stubEnv('GOOGLE_CLOUD_PROJECT', 'test-project')
    vi.stubEnv('PUBSUB_DISABLED', '1')
    const { publishCockpitEvent } = await import('../cockpit-events')
    await publishCockpitEvent({ type: 'nirmana.capsule_accepted' })
    expect(publishMessage).not.toHaveBeenCalled()
  })

  it('publishes with the canonical chart_id attribute when configured', async () => {
    vi.stubEnv('GOOGLE_CLOUD_PROJECT', 'test-project')
    vi.stubEnv('PUBSUB_DISABLED', '')
    const { publishCockpitEvent } = await import('../cockpit-events')
    await publishCockpitEvent({ type: 'nirmana.capsule_accepted', asset_id: 'bg_vedha_malefic_scale' })
    expect(publishMessage).toHaveBeenCalledWith(expect.objectContaining({
      attributes: { chart_id: '482012f1-710e-4a25-994a-93821f5871aa', type: 'nirmana.capsule_accepted' },
    }))
  })

  it('never throws when publishMessage rejects', async () => {
    vi.stubEnv('GOOGLE_CLOUD_PROJECT', 'test-project')
    publishMessage.mockRejectedValueOnce(new Error('boom'))
    const { publishCockpitEvent } = await import('../cockpit-events')
    await expect(publishCockpitEvent({ type: 'x' })).resolves.toBeUndefined()
  })
})
