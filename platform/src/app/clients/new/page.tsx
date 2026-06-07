import { NewClientForm } from '@/components/clients/NewClientForm'

// Force server-side render on every request so Next never bakes a stale static
// document for this route after a deploy. /clients/new is an authenticated
// form page with no static content — there is no value in pre-rendering it.
export const dynamic = 'force-dynamic'

export const metadata = {
  title: 'New Client Chart — MARSYS',
}

export default function NewClientPage() {
  return <NewClientForm />
}
