import { redirect } from "next/navigation";
import { readAccountProfile } from "@/lib/account/profile";
import { AccountHeading } from "@/components/account/AccountHeading";
import { ProfileForm } from "@/components/account/ProfileForm";
export default async function ProfilePage() {
  const profile = await readAccountProfile();
  if (!profile) redirect("/login");
  return (
    <>
      <AccountHeading name="profile" />
      <div className="j5-narrow">
        <ProfileForm initial={profile} />
      </div>
    </>
  );
}
