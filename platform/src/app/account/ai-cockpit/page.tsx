import { AccountHeading } from "@/components/account/AccountHeading";
import { CockpitIndex } from "@/components/account/CockpitIndex";
import { getFlag } from "@/lib/config";
export default function CockpitPage() {
  const consoleEnabled = getFlag("AI_CONSOLE_BYOK");
  return (
    <>
      <AccountHeading name="aiCockpit" cockpit consoleEnabled={consoleEnabled} />
      <CockpitIndex consoleEnabled={consoleEnabled} />
    </>
  );
}
