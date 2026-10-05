import Link from "next/link";
import { redirect } from "next/navigation";
import { query } from "@/lib/db/client";
import { resolveChartPageAccess } from "@/lib/auth/chart-page-guard";
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
import { formatDate } from "@/lib/utils/date";
import { ChartReadinessBand } from "@/components/profile/ChartReadinessBand";
import { ChartActionsMenu } from "@/components/profile/ChartActionsMenu";
import { PageTitle } from "@/components/journey1/Titles";
import { VargaChart } from "@/components/journey1/VargaChart";
import { ActivationTimeline } from "@/components/journey1/ActivationTimeline";
import { ChartNav } from "@/components/journey1/ChartNav";
import "@/components/profile/jataka-workspace.css";

export default async function ClientPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const access = await resolveChartPageAccess(id);
  if (!access) redirect("/login");
  if (access.permission === "deny") redirect("/dashboard");
  const { rows } = await query<{
    id: string;
    name: string;
    birth_date: string;
    birth_time: string;
    birth_place: string;
    timezone_id: string | null;
    ayanamsa: string | null;
  }>(
    `SELECT id,name,birth_date::text,birth_time::text,birth_place,timezone_id,ayanamsa FROM charts WHERE id=$1`,
    [id],
  );
  const chart = rows[0];
  if (!chart) redirect("/dashboard");
  const frame = journey1Frame(chart.ayanamsa);
  const [readinessMap, summary, extra] = await Promise.all([
    getChartReadinessMap([id]),
    getChartWorkspaceSummary(id, frame),
    getJourney1ChartData(id, frame),
  ]);
  const readiness = readinessMap.get(id) ?? emptyChartReadiness();
  const isSuperAdmin = access.role === "super_admin";
  return (
    <div className="j1 j1-container" data-permission={access.permission}>
      <Link href="/dashboard" className="j1-note">
        ← Birth charts
      </Link>
      <section className="j1-chart-hero" aria-label="Chart identity">
        <VargaChart
          charts={[summary.d1, extra.d9, extra.d10]}
          ayanamsha={journey1FrameLabel(frame)}
        />
        <div className="j1-chart-info">
          <PageTitle name="overview" />
          <h2>{chart.name}</h2>
          <p className="j1-note">
            {formatDate(chart.birth_date)} · {chart.birth_time?.slice(0, 5)}{" "}
            {chart.timezone_id} <br />
            {chart.birth_place}
          </p>
          <p>
            {summary.d1.isEmpty
              ? "Lagna not yet computed"
              : `Lagna · ${summary.d1.lagnaSign} ${summary.d1.lagnaDegreeDms}`}
          </p>
          <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
            <Link
              href={`/clients/${id}/pariprashna`}
              className="j1-btn"
              data-testid="consult-room-card"
            >
              <PageTitle name="consultation" as="span" compact />
            </Link>
            <ChartActionsMenu
              chartId={id}
              chartName={chart.name}
              canBuild={access.canBuild}
              isSuperAdmin={isSuperAdmin}
              canShare={isSuperAdmin}
            />
          </div>
        </div>
      </section>
      <ChartNav chartId={id} canBuild={access.canBuild} />
      <ChartReadinessBand
        readiness={readiness}
        chartId={id}
        canBuild={access.canBuild}
      />
      <div className="j1-summary-grid" style={{ marginTop: 24 }}>
        <section className="j1-panel">
          <PageTitle name="review" as="h2" compact />
          <p className="j1-note">Qualified transit activation windows</p>
          {extra.windows.length ? (
            <ActivationTimeline windows={extra.windows} />
          ) : (
            <p className="j1-note" style={{ marginBlock: 16 }}>
              {extra.flags.includes("windows_unavailable")
                ? "Activation windows are temporarily unavailable."
                : "No qualified upcoming activation windows are available for this chart."}
            </p>
          )}
          <Link href={`/clients/${id}/samiksha`}>Open prediction review →</Link>
        </section>
        <section className="j1-panel">
          <PageTitle name="periods" as="h2" compact />
          <dl>
            <div>
              <dt>Current daśā</dt>
              <dd>
                {summary.currentDasha
                  ? `${summary.currentDasha.md} mahādaśā · ${summary.currentDasha.ad} antardaśā`
                  : "Not yet computed"}
              </dd>
              {summary.currentDasha && (
                <dd className="j1-note">
                  Antardaśā until {formatDate(summary.currentDasha.adEnd)}
                </dd>
              )}
            </div>
            <div>
              <dt>Transit timing</dt>
              <dd>
                {extra.windows.length
                  ? `${extra.windows.length} upcoming or active recorded windows shown. `
                  : "No transit timing summary available."}
              </dd>
            </div>
            <div>
              <dt>Confirmed yogas</dt>
              <dd>
                {summary.confirmedYogas.length
                  ? summary.confirmedYogas.map((y) => y.name).join(" · ")
                  : summary.flags.includes("yogas_unresolved")
                    ? "Temporarily unavailable"
                    : "None confirmed yet"}
              </dd>
            </div>
          </dl>
        </section>
        <section className="j1-panel">
          <PageTitle name="preparation" as="h2" compact />
          <p>{readiness.label}</p>
          <p className="j1-note">
            {readiness.lastActivity
              ? `Last activity ${formatDate(readiness.lastActivity)}`
              : "No computed data yet"}
          </p>
          {access.canBuild && (
            <Link href={`/clients/${id}/nirmana`} data-testid="build-room-card">
              Open chart preparation →
            </Link>
          )}
        </section>
        <section className="j1-panel">
          <PageTitle name="almanac" as="h2" compact />
          <p className="j1-note">
            Chart context: {chart.birth_place}. The daily almanac and its
            chart-specific interpretation are not yet integrated.
          </p>
          <Link
            href={`/clients/${id}/panchang`}
            data-testid="panchang-room-card"
          >
            Open personal almanac →
          </Link>
        </section>
      </div>
      <footer className="j1-footer">Marsys Jyotish Intelligence System</footer>
    </div>
  );
}
