import { EntryShell } from "@/components/journey1/EntryShell";
import { RecoveryForm } from "@/components/auth/ForgotPasswordModal";
export const metadata = { title: "Account Recovery — Madhav" };
export default function Page() {
  return (
    <EntryShell name="recovery">
      <RecoveryForm />
    </EntryShell>
  );
}
