import { describe, expect, it } from 'vitest'
import { describePrimFailure } from '../tools/register_p1_aliases.js'
import { describeProxyFailure } from '../tools/registry_bridge.js'

const DENIAL = JSON.stringify({
  error: { class: 'entitlement_denied', message: 'access denied' },
  denial: { chart_id: 'aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee', permission_required: 'view' },
})

describe('F-39 — entitlement denial narration', () => {
  it.each([
    ['registry bridge', describeProxyFailure],
    ['alias primitive proxy', describePrimFailure],
  ])('%s does not assert that a denied chart exists', (_surface, describeFailure) => {
    const message = describeFailure('test_tool', 403, DENIAL)

    expect(message).toContain('ENTITLEMENT_DENIED')
    expect(message).toContain('does not determine whether the chart exists')
    expect(message).not.toContain('this chart exists but you are not granted')
  })
})
