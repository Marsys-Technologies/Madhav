"use client";
import Link from "next/link";
import { PageTitle, type PageName } from "./Titles";
export function ChartNav({
  chartId,
  canBuild,
  active = "overview",
}: {
  chartId: string;
  canBuild: boolean;
  active?: PageName;
}) {
  const base = `/clients/${chartId}`;
  const tabs: { name: PageName; href: string }[] = [
    { name: "overview", href: base },
    { name: "consultation", href: `${base}/pariprashna` },
    { name: "review", href: `${base}/samiksha` },
  ];
  if (canBuild) tabs.push({ name: "preparation", href: `${base}/nirmana` });
  tabs.push(
    { name: "almanac", href: `${base}/panchang` },
    { name: "events", href: `${base}/timeline` },
    { name: "reports", href: `${base}/reports` },
  );
  return (
    <nav className="j1-chart-tabs" aria-label="Chart workspace">
      {tabs.map((t) => (
        <Link
          key={t.name}
          href={t.href}
          aria-current={active === t.name ? "page" : undefined}
        >
          <PageTitle name={t.name} as="span" compact />
        </Link>
      ))}
    </nav>
  );
}
