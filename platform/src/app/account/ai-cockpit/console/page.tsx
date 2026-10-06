import { notFound } from "next/navigation";
import { getFlag } from "@/lib/config";
import { AccountHeading } from "@/components/account/AccountHeading";
import { AIConsole } from "@/components/ai-console/AIConsole";
export default function ConsolePage() {
  if (!getFlag("AI_CONSOLE_BYOK")) notFound();
  return (
    <>
      <AccountHeading name="aiConsole" cockpit />
      <AIConsole embedded />
    </>
  );
}
