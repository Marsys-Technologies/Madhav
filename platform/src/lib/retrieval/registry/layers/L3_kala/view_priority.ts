import { makeView } from './view_common'

export const priorityViewCapability = makeView({
  name: 'priority',
  description: 'Published conclusions with convergence context, with confirmed findings ahead of testimony and catalogs; no local ranking score.',
  sources: ['kala_darshana', 'kala_convergence'],
  required: [],
})
