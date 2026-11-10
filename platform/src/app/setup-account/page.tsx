import { redirect } from "next/navigation";
import { getServerUserWithProfile } from "@/lib/auth/access-control";
import { safeNextPath } from "@/lib/auth/safe_next";
import { query } from "@/lib/db/client";
import { EntryShell } from "@/components/journey1/EntryShell";
import { UsernameSetup } from "@/components/auth/UsernameSetup";
export const metadata = { title: "Account Setup — Madhav" };
export default async function Page({
  searchParams,
}: {
  searchParams: Promise<{ next?: string | string[] }>;
}) {
  const { next } = await searchParams;
  const returnPath = safeNextPath(typeof next === "string" ? next : null);
  const loginPath = returnPath
    ? `/login?setup=1&next=${encodeURIComponent(returnPath)}`
    : "/login?setup=1";
  const ctx = await getServerUserWithProfile();
  if (!ctx || ctx.profile.status !== "active") redirect(loginPath);
  const { rows } = await query<{ username: string | null; email: string }>(
    "SELECT username,email FROM profiles WHERE id=$1",
    [ctx.user.uid],
  );
  if (!rows[0]) redirect(loginPath);
  return (
    <EntryShell name="account">
      <UsernameSetup
        initialUsername={rows[0].username}
        email={rows[0].email}
        returnPath={returnPath}
      />
    </EntryShell>
  );
}
