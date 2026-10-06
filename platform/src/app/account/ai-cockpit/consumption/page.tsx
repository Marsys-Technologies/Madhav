import { AccountHeading } from "@/components/account/AccountHeading";
import { PersonalActivity } from "@/components/account/PersonalActivity";
export default function ConsumptionPage() {
  return (
    <>
      <AccountHeading name="consumption" cockpit />
      <PersonalActivity view="consumption" />
    </>
  );
}
