import { EntryShell } from "@/components/journey1/EntryShell";
import { RequestAccessForm } from "@/components/auth/RequestAccessModal";
export const metadata = { title: "Request Access — Madhav" };
export default function Page() {
  return (
    <EntryShell name="request">
      <RequestAccessForm />
    </EntryShell>
  );
}
