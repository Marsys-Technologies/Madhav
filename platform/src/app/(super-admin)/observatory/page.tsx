import {redirectLegacyActivity,type ActivitySearch} from '@/lib/admin/legacy-activity'
export const dynamic='force-dynamic'
export default async function LegacyActivityPage({searchParams}:{searchParams:Promise<ActivitySearch>}){
  await redirectLegacyActivity('observatory',await searchParams)
}
