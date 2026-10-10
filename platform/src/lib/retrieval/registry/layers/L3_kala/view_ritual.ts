import { makeView } from './view_common'

export const ritualViewCapability = makeView({
  name: 'ritual',
  description: 'Stored ritual assertions and negative-space release predicates for an explicit rite and horizon; no invented ritual recommendation.',
  sources: ['kala_darshana', 'kala_obstruction'],
  required: ['event_class', 'date_from', 'date_to'],
})
