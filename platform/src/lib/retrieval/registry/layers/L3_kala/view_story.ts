import { makeView } from './view_common'

export const storyViewCapability = makeView({
  name: 'story',
  description: 'Published temporal assertions with stored biographical chapter context.',
  sources: ['kala_darshana', 'kala_jivana_parva'],
  required: [],
})
