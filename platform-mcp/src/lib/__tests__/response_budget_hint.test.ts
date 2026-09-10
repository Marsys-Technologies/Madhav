import { autoDetectTrimmableSections } from '../response_budget'

test('autoDetectTrimmableSections hint does not assert specific parameter names', () => {
  const content = { items: Array.from({ length: 20 }, (_, i) => i) }
  const sections = autoDetectTrimmableSections(content, 'phala_outlook_get')
  expect(sections[0].recover.hint).not.toMatch(/date_range|top_k|limit/)
})
