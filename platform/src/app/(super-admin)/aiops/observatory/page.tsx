// /aiops/observatory is a permanent redirect to /observatory, which is the
// canonical full-featured Observatory route (with ObservatorySubNav and
// the AIOps tab strip applied via observatory/layout.tsx).
import { redirect } from 'next/navigation'

export default function AiopsObservatoryRedirect(): never {
  redirect('/observatory')
}
