"""
build_registry_from_db.py — Build CLASSICAL_ATTRIBUTION_REGISTRY and FINDINGS files
from the current state of the classical_attributions DB table.

Runs standalone after run_attribution_pass.py has populated ≥400 rows.
M8-E-S1 2026-05-14.
"""

from __future__ import annotations

import json
import os
import sys
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Generator

import psycopg2
import psycopg2.extras

REPO_ROOT  = Path(__file__).parents[4]
OUTPUT_DIR = REPO_ROOT / "08_CLASSICAL_CROSS_REFERENCE"
REGISTRY_JSON = OUTPUT_DIR / "CLASSICAL_ATTRIBUTION_REGISTRY_v1_0.json"
REGISTRY_MD   = OUTPUT_DIR / "CLASSICAL_ATTRIBUTION_REGISTRY_v1_0.md"
FINDINGS_CROSS = OUTPUT_DIR / "FINDINGS_M5_CROSS_REF_v1_0.md"
FINDINGS_CLAIM = OUTPUT_DIR / "FINDINGS_CLASSICAL_CLAIM_v1_0.md"


@contextmanager
def get_db() -> Generator[psycopg2.extensions.connection, None, None]:
    url = os.environ["DATABASE_URL"]
    conn = psycopg2.connect(url)
    try:
        yield conn
    finally:
        conn.close()


def fetch_all_attributions(conn: psycopg2.extensions.connection) -> list[dict[str, Any]]:
    sql = """
        SELECT
            ca.id::text                         AS attribution_id,
            ca.msr_signal_id                    AS signal_id,
            ct.text_key,
            ct.title,
            ct.author,
            ct.tradition,
            cc.chapter,
            cc.verse_range,
            cc.content,
            ca.attribution_type,
            ca.confidence,
            ca.confidence_tier,
            ca.derivation_notes
        FROM classical_attributions ca
        JOIN classical_chunks cc ON cc.id = ca.chunk_id
        JOIN classical_texts ct ON ct.id = cc.text_id
        ORDER BY ca.msr_signal_id, ca.confidence DESC
    """
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(sql)
        return [dict(r) for r in cur.fetchall()]


def build_registry(records: list[dict[str, Any]]) -> None:
    type_counts: dict[str, int] = {}
    tier_counts: dict[str, int] = {}
    text_counts: dict[str, int] = {}

    for r in records:
        type_counts[r["attribution_type"]] = type_counts.get(r["attribution_type"], 0) + 1
        tier = r.get("confidence_tier") or "LOW"
        tier_counts[tier] = tier_counts.get(tier, 0) + 1
        text_counts[r["text_key"]] = text_counts.get(r["text_key"], 0) + 1

    registry = {
        "artifact": "CLASSICAL_ATTRIBUTION_REGISTRY_v1_0.json",
        "version": "1.0",
        "canonical_id": "CLASSICAL_ATTRIBUTION_REGISTRY",
        "status": "CURRENT",
        "layer": "L8",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "total_signals": 514,
        "total_attributions": len(records),
        "coverage_by_tier": tier_counts,
        "attribution_type_summary": type_counts,
        "attributions": [
            {
                "signal_id":        r["signal_id"],
                "text_key":         r["text_key"],
                "chapter":          r.get("chapter"),
                "verse_range":      r.get("verse_range"),
                "attribution_type": r["attribution_type"],
                "confidence":       float(r["confidence"]),
                "confidence_tier":  r.get("confidence_tier") or "LOW",
                "derivation_notes": r.get("derivation_notes") or "",
            }
            for r in records
        ],
    }

    REGISTRY_JSON.write_text(json.dumps(registry, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Written {REGISTRY_JSON} ({len(records)} records)")

    # Markdown companion
    lines = [
        "---",
        "artifact: CLASSICAL_ATTRIBUTION_REGISTRY_v1_0.md",
        "version: \"1.0\"",
        "canonical_id: CLASSICAL_ATTRIBUTION_REGISTRY",
        "status: CURRENT",
        "layer: L8",
        f"generated_at: {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}",
        f"total_attributions: {len(records)}",
        "---",
        "",
        "# CLASSICAL_ATTRIBUTION_REGISTRY v1.0",
        "",
        f"Total attribution records: **{len(records)}**",
        "",
        "## Attribution Type Breakdown",
        "",
        "| Attribution Type | Count |",
        "|---|---|",
    ]
    for t, c in sorted(type_counts.items()):
        lines.append(f"| {t} | {c} |")

    lines += [
        "",
        "## Confidence Tier Breakdown",
        "",
        "| Tier | Count |",
        "|---|---|",
    ]
    for tier, c in sorted(tier_counts.items()):
        lines.append(f"| {tier} | {c} |")

    lines += ["", "## Per-Text Attribution Counts", "", "| Text Key | Attributions |", "|---|---|"]
    for tk, c in sorted(text_counts.items(), key=lambda x: -x[1]):
        lines.append(f"| {tk} | {c} |")

    lines += ["", "## Sample Attribution Records (first 50)", ""]
    for r in records[:50]:
        cv = f"Ch.{r.get('chapter','?')}" if r.get("chapter") else "—"
        if r.get("verse_range"):
            cv += f" v.{r['verse_range']}"
        lines.append(
            f"**{r['signal_id']}** × `{r['text_key']}` {cv} — "
            f"{r['attribution_type']} (conf {float(r['confidence']):.2f}) — {(r.get('derivation_notes') or '')[:80]}"
        )

    REGISTRY_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"Written {REGISTRY_MD}")


def build_findings_cross_ref(records: list[dict[str, Any]]) -> None:
    # Group by signal
    sig_map: dict[str, list[dict[str, Any]]] = {}
    for r in records:
        sig_map.setdefault(r["signal_id"], []).append(r)

    # Rank by confirms+partial count
    def rank(sid: str) -> int:
        return sum(1 for r in sig_map[sid] if r["attribution_type"] in ("confirms", "partial", "extends"))

    top10 = sorted(sig_map.keys(), key=rank, reverse=True)[:10]

    lines = [
        "---",
        "artifact: FINDINGS_M5_CROSS_REF_v1_0.md",
        "version: \"1.0\"",
        "status: CURRENT",
        "layer: L8",
        f"generated_at: {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}",
        "---",
        "",
        "# FINDINGS: Top-10 MSR Signals × Classical Cross-Reference",
        "",
        "Ranked by count of `confirms` + `partial` + `extends` attributions.",
        f"Based on {len(records)} attribution records across {len(sig_map)} attributed signals.",
        "",
    ]

    for rank_idx, sid in enumerate(top10, 1):
        recs = sig_map[sid]
        lines += [
            f"## {rank_idx}. {sid}",
            "",
            "| Text | Chapter/Verse | Type | Confidence | Notes |",
            "|---|---|---|---|---|",
        ]
        for r in sorted(recs, key=lambda x: -float(x["confidence"]))[:5]:
            cv = f"Ch.{r.get('chapter','?')}" if r.get("chapter") else "—"
            if r.get("verse_range"):
                cv += f" v.{r['verse_range']}"
            lines.append(
                f"| {r['text_key']} | {cv} | {r['attribution_type']} | "
                f"{float(r['confidence']):.2f} | {(r.get('derivation_notes') or '')[:80]} |"
            )
        lines.append("")

    FINDINGS_CROSS.write_text("\n".join(lines), encoding="utf-8")
    print(f"Written {FINDINGS_CROSS}")


def build_findings_claim(records: list[dict[str, Any]]) -> None:
    text_stats: dict[str, dict[str, int]] = {}
    for r in records:
        tk = r["text_key"]
        if tk not in text_stats:
            text_stats[tk] = {"confirms": 0, "contradicts": 0, "partial": 0, "extends": 0, "silent": 0}
        text_stats[tk][r["attribution_type"]] = text_stats[tk].get(r["attribution_type"], 0) + 1

    lines = [
        "---",
        "artifact: FINDINGS_CLASSICAL_CLAIM_v1_0.md",
        "version: \"1.0\"",
        "status: CURRENT",
        "layer: L8",
        f"generated_at: {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}",
        "---",
        "",
        "# FINDINGS: Classical Claim Inventory",
        "",
        "| Text Key | confirms | contradicts | partial | extends | silent | total |",
        "|---|---|---|---|---|---|---|",
    ]

    total = {"confirms": 0, "contradicts": 0, "partial": 0, "extends": 0, "silent": 0}
    for tk, counts in sorted(text_stats.items()):
        row_total = sum(counts.values())
        lines.append(
            f"| {tk} | {counts['confirms']} | {counts['contradicts']} | "
            f"{counts['partial']} | {counts['extends']} | {counts['silent']} | {row_total} |"
        )
        for k in total:
            total[k] += counts.get(k, 0)

    grand = sum(total.values())
    lines.append(
        f"| **TOTAL** | **{total['confirms']}** | **{total['contradicts']}** | "
        f"**{total['partial']}** | **{total['extends']}** | **{total['silent']}** | **{grand}** |"
    )
    lines += [
        "",
        "## Interpretation",
        "",
        f"- **confirms**: {total['confirms']} attributions where classical text directly validates the MSR signal",
        f"- **contradicts**: {total['contradicts']} attributions where classical text opposes the signal",
        f"- **partial**: {total['partial']} attributions with partial classical support",
        f"- **extends**: {total['extends']} attributions where classical text adds nuance",
        f"- **silent**: {total['silent']} attributions where classical text is unrelated",
    ]

    FINDINGS_CLAIM.write_text("\n".join(lines), encoding="utf-8")
    print(f"Written {FINDINGS_CLAIM}")


def main() -> None:
    with get_db() as conn:
        records = fetch_all_attributions(conn)

    print(f"Fetched {len(records)} attribution records from DB")
    if len(records) < 400:
        print(f"WARNING: Only {len(records)} rows — AC.M8E.3 requires ≥400", file=sys.stderr)

    build_registry(records)
    build_findings_cross_ref(records)
    build_findings_claim(records)

    type_counts: dict[str, int] = {}
    for r in records:
        type_counts[r["attribution_type"]] = type_counts.get(r["attribution_type"], 0) + 1

    print("=== SUMMARY ===")
    for t, c in sorted(type_counts.items()):
        print(f"  {t:12}: {c}")
    print(f"  TOTAL       : {len(records)}")


if __name__ == "__main__":
    main()
