import "server-only";
import { getServerUserWithProfile } from "@/lib/auth/access-control";
import { query } from "@/lib/db/client";
export type AccountProfile = {
  name: string | null;
  email: string;
  username: string | null;
  role?: string;
};
export async function readAccountProfile(): Promise<AccountProfile | null> {
  const ctx = await getServerUserWithProfile();
  if (!ctx || ctx.profile.status !== "active") return null;
  const { rows } = await query<AccountProfile>(
    "SELECT name,email,username,role FROM profiles WHERE id=$1 AND status='active'",
    [ctx.user.uid],
  );
  return rows[0] ?? null;
}
