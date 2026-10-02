import { afterEach, describe, expect, it, vi } from 'vitest'
import { anthropicAdapter } from '../anthropic'

const fixtureKey = 'fixture-key-not-a-real-key'
const controller = () => new AbortController().signal
const listed = (capabilities?: unknown) => ({ id: 'claude-new-model', display_name: 'Claude New Model',
  ...(capabilities === undefined ? {} : { capabilities }) })
afterEach(() => vi.unstubAllGlobals())

async function discover(rows: unknown[]) {
  const http = vi.fn().mockResolvedValue(Response.json({ data: rows, has_more: false }))
  vi.stubGlobal('fetch', http)
  return anthropicAdapter.discover(fixtureKey, controller())
}

describe('Anthropic advertised effort capabilities', () => {
  it('retains exact advertised effort levels for an unseen model without family inference', async () => {
    const [model] = await discover([listed({ effort: { supported: true, low: { supported: true },
      medium: { supported: true }, high: { supported: true }, xhigh: { supported: true }, max: { supported: true } },
      structured_outputs: { supported: true } })])
    expect(model).toMatchObject({ modelId: 'claude-new-model', supportedEfforts: ['low', 'medium', 'high', 'xhigh', 'max'],
      defaultEffort: null, supportsStructuredOutput: true,
      compatibleRoles: ['synthesizer', 'planner', 'deep_planner', 'worker'] })
  })

  it('allows only known levels with literal boolean supported=true', async () => {
    const [model] = await discover([listed({ effort: { supported: true, low: { supported: 'true' },
      medium: { supported: false }, high: { supported: true }, xhigh: true,
      max: { supported: 1 }, ultra: { supported: true }, default: 'high' } })])
    expect(model.supportedEfforts).toEqual(['high'])
    expect(model.defaultEffort).toBeNull()
  })

  it.each([{ supported: false, high: { supported: true } }, { supported: true }, {},
    { supported: true, unknown: { supported: true } }])('retains explicit no-supported-level evidence', async effort => {
    const [model] = await discover([listed({ effort })])
    expect(model.supportedEfforts).toEqual([])
    expect(model.defaultEffort).toBeNull()
  })

  it.each([undefined, null, {}, { effort: null }, { effort: [] }, { effort: 'high' }])('leaves unadvertised capabilities unknown', async capabilities => {
    const [model] = await discover([listed(capabilities)])
    expect(model).not.toHaveProperty('supportedEfforts')
    expect(model).not.toHaveProperty('defaultEffort')
  })

  it('merges paginated efforts using the same last-row semantics as catalogue filtering', async () => {
    const http = vi.fn()
      .mockResolvedValueOnce(Response.json({ data: [listed({ effort: { high: { supported: true } } })],
        has_more: true, last_id: 'claude-new-model' }))
      .mockResolvedValueOnce(Response.json({ data: [listed({ effort: { low: { supported: true } } })], has_more: false }))
    vi.stubGlobal('fetch', http)
    const [model] = await anthropicAdapter.discover(fixtureKey, controller())
    expect(model.supportedEfforts).toEqual(['low'])
    expect(http).toHaveBeenCalledTimes(2)
    expect(http.mock.calls.every(([, init]) => init.method === 'GET' && init.body === undefined)).toBe(true)
  })

  it('does not admit retired models while attaching efforts', async () => {
    expect(await discover([{ ...listed({ effort: { high: { supported: true } } }), retired: true }])).toEqual([])
  })
})
