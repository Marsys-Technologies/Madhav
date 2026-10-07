"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
const items = [
  ["Overview", "/account"],
  ["Profile", "/account/profile"],
  ["Security", "/account/security"],
  ["Preferences", "/account/preferences"],
  ["AI Cockpit", "/account/ai-cockpit"],
] as const;
export function AccountNav() {
  const path = usePathname();
  return (
    <nav aria-label="Account sections" className="j5-tabs">
      {items.map(([label, href]) => (
        <Link
          key={href}
          href={href}
          aria-current={
            path === href ||
            (href === "/account/ai-cockpit" && path.startsWith(href + "/"))
              ? "page"
              : undefined
          }
        >
          {label}
        </Link>
      ))}
    </nav>
  );
}
