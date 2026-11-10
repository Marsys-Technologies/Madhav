import { AccountHeading } from "@/components/account/AccountHeading";
import { CockpitIndex } from "@/components/account/CockpitIndex";
import { getFlag } from "@/lib/config";
export default function CockpitPage() {
  return (
    <>
      <AccountHeading name="aiCockpit" cockpit />
      <CockpitIndex consoleEnabled={getFlag("AI_CONSOLE_BYOK")} />
    </>
  );
}
