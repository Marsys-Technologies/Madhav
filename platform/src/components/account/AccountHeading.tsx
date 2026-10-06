import Link from "next/link";
import { PageTitle, type PageName } from "@/components/journey1/Titles";
import { AccountNav } from "./AccountNav";
import { CockpitNav } from "./CockpitNav";
export function AccountHeading({
  name,
  cockpit = false,
}: {
  name: PageName;
  cockpit?: boolean;
}) {
  return (
    <>
      <Link className="j5-back" href={cockpit ? "/account" : "/dashboard"}>
        {cockpit ? "← Back to My Account" : "← Back to Birth Charts"}
      </Link>
      <p className="j5-eyebrow">
        {cockpit ? "My Account · AI Cockpit" : "Personal"}
      </p>
      <PageTitle name={name} />
      {cockpit ? <CockpitNav /> : <AccountNav />}
    </>
  );
}
