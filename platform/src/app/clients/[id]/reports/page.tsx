import Link from "next/link";
import { PageTitle } from "@/components/journey1/Titles";
export const metadata = { title: "Reports — Madhav" };
export default async function Page({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return (
    <div className="j1-container">
      <Link href={`/clients/${id}`}>← Chart overview</Link>
      <section className="j1-panel" style={{ marginTop: 24 }}>
        <PageTitle name="reports" />
        <p className="j1-note" style={{ marginTop: 20 }}>
          Detailed reports for each domain of life will be available here. This
          feature is planned.
        </p>
      </section>
    </div>
  );
}
