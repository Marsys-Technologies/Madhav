import { redirect } from "next/navigation";
import { getServerUserWithProfile } from "@/lib/auth/access-control";
import { JourneyShell } from "@/components/journey1/JourneyShell";
import { ObservatoryScope } from "@/components/observatory/ObservatoryScope";
import "@/app/journey1.css";
import "./account.css";
export const metadata = { title: "My Account — Madhav" };
export default async function AccountLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const ctx = await getServerUserWithProfile();
  if (!ctx || ctx.profile.status !== "active") redirect("/login");
  return (
    <JourneyShell user={ctx.user} role={ctx.profile.role}>
      <ObservatoryScope admin={false} userId={ctx.user.uid}>
        <div className="j5-account">{children}</div>
      </ObservatoryScope>
    </JourneyShell>
  );
}
