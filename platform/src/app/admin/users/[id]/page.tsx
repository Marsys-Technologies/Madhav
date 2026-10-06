import { UserDetails } from '@/components/admin/UserDetails'
export default async function Page({params}:{params:Promise<{id:string}>}) {const {id}=await params;return <UserDetails selectedId={id} />}
