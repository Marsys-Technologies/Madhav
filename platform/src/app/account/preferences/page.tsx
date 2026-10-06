import { AccountHeading } from "@/components/account/AccountHeading";
import { PreferencesForm } from "@/components/account/PreferencesForm";
export default function PreferencesPage() {
  return (
    <>
      <AccountHeading name="preferences" />
      <PreferencesForm />
    </>
  );
}
