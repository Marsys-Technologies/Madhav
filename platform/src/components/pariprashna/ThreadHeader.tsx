"use client";
import Link from "next/link";
import { ArrowLeft, History, PanelRight } from "lucide-react";
import { PageTitle } from "@/components/journey1/Titles";
import { useOptionalDockController } from "./dock/DockController";
export interface ChartPin {
  name: string;
  bornLine: string;
}
export function ThreadHeader({
  chartPin,
  chartId,
}: {
  chartPin: ChartPin;
  chartId?: string;
}) {
  const dock = useOptionalDockController();
  return (
    <header className="pp-page-header">
      <div className="pp-page-identity">
        {chartId && (
          <Link
            className="pp-icon-button"
            href={`/clients/${chartId}`}
            aria-label="Back to Chart Overview"
          >
            <ArrowLeft size={20} />
          </Link>
        )}
        <PageTitle name="consultation" />
        <div className="pp-chart-identity">
          <strong>{chartPin.name}</strong>
          <small>{chartPin.bornLine}</small>
        </div>
      </div>
      {dock && (
        <div className="pp-page-actions">
          <button
            type="button"
            className="pp-icon-button"
            aria-label="Open conversation history"
            aria-expanded={dock.leftOpen}
            onClick={() => dock.setLeftOpen(!dock.leftOpen)}
          >
            <History size={19} />
          </button>
          <button
            type="button"
            className="pp-icon-button"
            aria-label="Open evidence"
            aria-expanded={dock.open}
            onClick={() => dock.setOpen(!dock.open)}
          >
            <PanelRight size={19} />
          </button>
        </div>
      )}
    </header>
  );
}
