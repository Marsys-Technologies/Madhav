import { AccountHeading } from "@/components/account/AccountHeading";
import { PersonalActivity } from "@/components/account/PersonalActivity";
export default function MyObservatoryPage() {
  return (
    <>
      <AccountHeading name="myObservatory" cockpit />
      <PersonalActivity view="observatory" />
    </>
  );
}
