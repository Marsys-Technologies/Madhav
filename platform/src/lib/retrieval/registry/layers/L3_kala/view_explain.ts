import { makeView } from './view_common'

export const explainViewCapability = makeView({
  name: 'explain',
  description: 'Pinned assertion or context-record provenance, source roots, coverage and un-netted effective states.',
  sources: ['kala_darshana', 'kala_obstruction', 'kala_gochara_contacts', 'kala_bhavishya', 'kala_convergence', 'kala_jivana_parva'],
  required: ['assertion_id'],
})
