import Link from "next/link";
import { PageTitle, type PageName } from "@/components/journey1/Titles";
import { AccountNav } from "./AccountNav";
import { CockpitNav } from "./CockpitNav";
import { getFlag } from "@/lib/config";
export function AccountHeading({
  name,
  cockpit = false,
  consoleEnabled = getFlag("AI_CONSOLE_BYOK"),
}: {
  name: PageName;
  cockpit?: boolean;
  consoleEnabled?: boolean;
}) {
  return (
    <header className="j5-heading">
      <Link className="j5-back" href={cockpit ? "/account" : "/dashboard"}>
        {cockpit ? "← Back to My Account" : "← Back to Birth Charts"}
      </Link>
      <p className="j5-eyebrow">
        {cockpit ? "My Account · AI Cockpit" : "Personal"}
      </p>
      <PageTitle name={name} />
      {cockpit ? <CockpitNav active={name} consoleEnabled={consoleEnabled} /> : <AccountNav active={name} />}
    </header>
  );
}
