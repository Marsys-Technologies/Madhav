import { makeView } from './view_common'

export const nowViewCapability = makeView({
  name: 'now',
  description: 'Current assertions and negative-space effective states at the requested instant.',
  sources: ['kala_darshana', 'kala_obstruction'],
  required: ['at'],
})
