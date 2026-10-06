import { AccountHeading } from "@/components/account/AccountHeading";
import { CockpitIndex } from "@/components/account/CockpitIndex";
export default function CockpitPage() {
  return (
    <>
      <AccountHeading name="aiCockpit" cockpit />
      <CockpitIndex />
    </>
  );
}
