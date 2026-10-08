import { makeView } from './view_common'

export const electViewCapability = makeView({
  name: 'elect',
  description: 'Stored election assertions, obstruction states and their contacts for an explicit event class and horizon; no calendar recomputation.',
  sources: ['kala_darshana', 'kala_obstruction', 'kala_gochara_contacts'],
  required: ['event_class', 'date_from', 'date_to'],
})
