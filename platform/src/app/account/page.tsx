import { redirect } from "next/navigation";
import { readAccountProfile } from "@/lib/account/profile";
import { AccountOverview } from "@/components/account/AccountOverview";
export default async function AccountPage() {
  const profile = await readAccountProfile();
  if (!profile) redirect("/login");
  return <AccountOverview profile={profile} />;
}
