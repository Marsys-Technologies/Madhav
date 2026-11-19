import Link from "next/link";
import type { PageName } from "@/components/journey1/Titles";
const items = [
  ["Overview", "/account", "account"],
  ["Profile", "/account/profile", "profile"],
  ["Security", "/account/security", "security"],
  ["Preferences", "/account/preferences", "preferences"],
  ["AI Cockpit", "/account/ai-cockpit", "aiCockpit"],
] as const;
export function AccountNav({ active }: { active: PageName }) {
  return (
    <nav aria-label="Account sections" className="j5-tabs">
      {items.map(([label, href, name]) => (
        <Link
          key={href}
          href={href}
          aria-current={active === name ? "page" : undefined}
        >
          {label}
        </Link>
      ))}
    </nav>
  );
}
