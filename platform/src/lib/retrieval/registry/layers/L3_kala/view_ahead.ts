import { makeView } from './view_common'

export const aheadViewCapability = makeView({
  name: 'ahead',
  description: 'Upcoming assertions, projected context and contact geometry in the requested horizon.',
  sources: ['kala_darshana', 'kala_bhavishya', 'kala_gochara_contacts'],
  required: ['date_from', 'date_to'],
})
