import { redirect } from "next/navigation";
import { resolveChartPageAccess } from "@/lib/auth/chart-page-guard";
import { readFolioChartIdentity } from "@/lib/charts/folioIdentity";
import {
  emptyChartReadiness,
  getChartReadinessMap,
} from "@/lib/charts/readiness";
import { getChartWorkspaceSummary } from "@/lib/charts/workspaceSummary";
import {
  getJourney1ChartData,
  journey1Frame,
  journey1FrameLabel,
} from "@/lib/charts/journey1";

import { ChartOverviewView } from "./ChartOverviewView";

export default async function ClientPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const access = await resolveChartPageAccess(id);
  if (!access) redirect("/login");
  if (access.permission === "deny") redirect("/dashboard");
  const chart = await readFolioChartIdentity(id);
  if (!chart) redirect("/dashboard");
  const frame = journey1Frame(chart.ayanamsa);
  const [readinessMap, summary, extra] = await Promise.all([
    getChartReadinessMap([id]).catch(() => null),
    getChartWorkspaceSummary(id, frame),
    getJourney1ChartData(id, frame),
  ]);
  const readiness = readinessMap === null ? null : readinessMap.get(id) ?? emptyChartReadiness();
  return (
    <ChartOverviewView
      id={id}
      chart={chart}
      summary={summary}
      extra={extra}
      readiness={readiness}
      permission={access.permission}
      canBuild={access.canBuild}
      isSuperAdmin={access.role === "super_admin"}
      frameLabel={journey1FrameLabel(frame)}
    />
  );
}
