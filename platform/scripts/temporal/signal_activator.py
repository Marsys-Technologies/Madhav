"""
Signal activator v1 — date-indexed lit/dormant/ripening surface for MSR signals.

M3-W2-B2 deliverable. Joins (a) the active Vimshottari Mahadasha + Antardasha
at a query_date with (b) the transit state for that date and (c) each signal's
`entities_involved` list, then emits one signal_states-shaped row per signal
whose state can be decided.

v1 logic — deterministic, rule-based, simple:
  * "lit" — the active Vimshottari MD lord OR AD lord is a planet listed in
    the signal's `entities_involved`. Strongest activation indicator.
  * "ripening" — the next AD lord (within 90 days of arriving) is in
    `entities_involved`, OR a current transit planet currently sits in a
    sign listed in `entities_involved`. Secondary indicator.
  * "dormant" — neither.

A flat confidence of 0.6 is emitted with every row to mark v1 as deterministic
rule-based (not calibrated). Future iterations may calibrate per-signal.

Signals consumed: parsed directly from 025_HOLISTIC_SYNTHESIS/MSR_v3_0.md
(no DB call). The MSR markdown carries one YAML-block per signal beginning
`SIG.MSR.NNN:` with an `entities_involved: [...]` field.

CLI:
    python3 platform/scripts/temporal/signal_activator.py \\
        --chart-id <chart-uuid> \\
        --birth <ISO8601-birth-datetime-with-offset> \\
        --date 2026-05-01 \\
        --output 05_TEMPORAL_ENGINES/transit/lit_states_sample_M3B_v1_0.json

Per CLAUDE.md §I B.10: this script does no chart-numerical computation; it
delegates to compute_transits.get_transit_states (which itself wraps swisseph)
and reads pre-computed Vimshottari rows from the engine output JSON.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

# Local import — the script lives in platform/scripts/temporal/.
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from compute_transits import get_transit_states, parse_iso8601, SIGNS  # noqa: E402

ROOT = SCRIPT_DIR.parents[2]
DEFAULT_VIMSHOTTARI_RAW = ROOT / "05_TEMPORAL_ENGINES/dasha/vimshottari/VIMSHOTTARI_RAW_v1_0.json"
DEFAULT_MSR = ROOT / "025_HOLISTIC_SYNTHESIS/MSR_v3_0.md"

PLANET_TO_PLN = {
    "Sun": "PLN.SUN", "Moon": "PLN.MOON", "Mars": "PLN.MARS",
    "Mercury": "PLN.MERCURY", "Jupiter": "PLN.JUPITER",
    "Venus": "PLN.VENUS", "Saturn": "PLN.SATURN",
    "Rahu": "PLN.RAHU", "Ketu": "PLN.KETU",
}
SIGN_TO_SGN = {s: f"SGN.{s.upper()}" for s in SIGNS}


def parse_msr_signals(msr_path: Path) -> list[dict]:
    """
    Light-weight parser for the SIG.MSR.NNN blocks in MSR_v3_0.md.

    Extracts:
      - signal_id (e.g. 'SIG.MSR.001')
      - signal_name
      - entities_involved (list of strings)
      - temporal_activation
      - domains_affected
    """
    text = msr_path.read_text(encoding="utf-8")
    blocks = re.split(r"\n(?=SIG\.MSR\.\d+:\s*\n)", text)

    signals: list[dict] = []
    for block in blocks:
        m = re.match(r"^(SIG\.MSR\.\d+):\s*\n", block)
        if not m:
            continue
        sid = m.group(1)
        # Parse a few simple top-level keys via regex against the block body.
        def _val(key: str) -> str | None:
            mm = re.search(rf"^\s{{2}}{re.escape(key)}:\s*(.+?)\s*$", block, re.MULTILINE)
            return mm.group(1) if mm else None

        def _list(key: str) -> list[str]:
            mm = re.search(rf"^\s{{2}}{re.escape(key)}:\s*\[(.*?)\]\s*$", block, re.MULTILINE)
            if not mm:
                return []
            return [x.strip() for x in mm.group(1).split(",") if x.strip()]

        signals.append({
            "signal_id": sid,
            "signal_name": (_val("signal_name") or "").strip('"'),
            "entities_involved": _list("entities_involved"),
            "temporal_activation": _val("temporal_activation"),
            "domains_affected": _list("domains_affected"),
        })
    return signals


def load_active_vimshottari(raw_path: Path, query_date: date) -> dict:
    """
    Find the active Vimshottari MD + AD rows that contain query_date.
    Returns {'md': planet, 'ad': planet, 'next_ad': planet, 'next_ad_starts': iso}
    """
    data = json.loads(raw_path.read_text())
    md_lord = ad_lord = None
    next_ad_lord = None
    next_ad_starts = None

    md_rows = sorted(
        [r for r in data["rows"] if r["dasha_level"] == "M"],
        key=lambda r: r["start_date"],
    )
    for r in md_rows:
        s, e = date.fromisoformat(r["start_date"]), date.fromisoformat(r["end_date"])
        if s <= query_date < e:
            md_lord = r["planet"]
            break

    ad_rows = sorted(
        [r for r in data["rows"] if r["dasha_level"] == "A"],
        key=lambda r: r["start_date"],
    )
    for i, r in enumerate(ad_rows):
        s, e = date.fromisoformat(r["start_date"]), date.fromisoformat(r["end_date"])
        if s <= query_date < e:
            ad_lord = r["planet"]
            if i + 1 < len(ad_rows):
                nxt = ad_rows[i + 1]
                next_ad_lord = nxt["planet"]
                next_ad_starts = nxt["start_date"]
            break

    return {
        "md": md_lord,
        "ad": ad_lord,
        "next_ad": next_ad_lord,
        "next_ad_starts": next_ad_starts,
    }


def decide_state(
    signal: dict,
    *,
    md_lord: str | None,
    ad_lord: str | None,
    next_ad_lord: str | None,
    next_ad_starts: str | None,
    transit_signs_by_planet: dict,
    query_date: date,
) -> str:
    """Return one of 'lit' | 'ripening' | 'dormant'."""
    eis = set(signal.get("entities_involved", []))

    # LIT: any active dasha lord (MD or AD) matches an entity.
    for lord in (md_lord, ad_lord):
        if lord and PLANET_TO_PLN.get(lord) in eis:
            return "lit"
    # LIT: a current transit planet sits in a sign explicitly named in entities.
    for tplanet, tsign in transit_signs_by_planet.items():
        if SIGN_TO_SGN.get(tsign) in eis:
            return "lit"

    # RIPENING: next AD lord matches and arrives within 90 days.
    if next_ad_lord and PLANET_TO_PLN.get(next_ad_lord) in eis and next_ad_starts:
        nxt = date.fromisoformat(next_ad_starts)
        if 0 <= (nxt - query_date).days <= 90:
            return "ripening"

    return "dormant"


def activate(
    *,
    chart_id: str,
    query_date: date,
    birth_dt: datetime,
    msr_path: Path,
    vimshottari_raw_path: Path,
    ayanamsha: str = "lahiri",
    confidence: float = 0.6,
) -> dict:
    signals = parse_msr_signals(msr_path)
    if not signals:
        raise RuntimeError(f"No SIG.MSR.* signals parsed from {msr_path}")

    dasha = load_active_vimshottari(vimshottari_raw_path, query_date)
    transit = get_transit_states(birth_dt, query_date, ayanamsha=ayanamsha)
    transit_signs_by_planet = {p: v["sign"] for p, v in transit["planets"].items()}

    rows: list[dict] = []
    summary = {"lit": 0, "ripening": 0, "dormant": 0}
    for sig in signals:
        state = decide_state(
            sig,
            md_lord=dasha["md"],
            ad_lord=dasha["ad"],
            next_ad_lord=dasha["next_ad"],
            next_ad_starts=dasha["next_ad_starts"],
            transit_signs_by_planet=transit_signs_by_planet,
            query_date=query_date,
        )
        summary[state] += 1
        rows.append({
            "chart_id": chart_id,
            "signal_id": sig["signal_id"],
            "query_date": query_date.isoformat(),
            "state": state,
            "confidence": confidence,
            "dasha_system": "vimshottari",
            "computed_by": "signal_activator",
            "ayanamsha": ayanamsha,
            "diagnostics": {
                "signal_name": sig["signal_name"],
                "entities_involved": sig["entities_involved"],
                "active_md": dasha["md"],
                "active_ad": dasha["ad"],
                "next_ad": dasha["next_ad"],
                "next_ad_starts": dasha["next_ad_starts"],
                "transit_signs": transit_signs_by_planet,
            },
        })

    return {
        "schema_version": "1.0",
        "chart_id": chart_id,
        "query_date": query_date.isoformat(),
        "ayanamsha": ayanamsha,
        "computed_by": "signal_activator",
        "v1_logic_note": (
            "v1 deterministic rule-based; flat confidence=0.6. "
            "lit=active MD/AD lord OR transit-planet-in-named-sign matches "
            "entities_involved; ripening=next AD lord arriving within 90 days "
            "matches entities_involved; otherwise dormant."
        ),
        "active_dasha": dasha,
        "transit_summary": {
            "sade_sati": transit["sade_sati"],
            "eclipse_proximity": transit["eclipse_proximity"],
            "transit_signs": transit_signs_by_planet,
        },
        "signal_count": len(signals),
        "state_summary": summary,
        "signals": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--chart-id", required=True,
                        help="Chart UUID (the charts.chart_id of the chart under test). REQUIRED.")
    parser.add_argument(
        "--birth", required=True,
        help="ISO8601 birth datetime of the chart under test (timezone-aware), from its `charts` row. REQUIRED: no birth datetime is embedded in this script.",
    )
    parser.add_argument(
        "--date", default=date.today().isoformat(),
        help="Query date YYYY-MM-DD (default: today).",
    )
    parser.add_argument(
        "--msr", default=str(DEFAULT_MSR),
        help="Path to MSR_v3_0.md.",
    )
    parser.add_argument(
        "--vimshottari-raw", default=str(DEFAULT_VIMSHOTTARI_RAW),
        help="Path to VIMSHOTTARI_RAW_v1_0.json.",
    )
    parser.add_argument(
        "--output",
        default="05_TEMPORAL_ENGINES/transit/lit_states_sample_M3B_v1_0.json",
    )
    parser.add_argument("--ayanamsha", default="lahiri")
    args = parser.parse_args()

    birth_dt = parse_iso8601(args.birth)
    query_date = date.fromisoformat(args.date)

    payload = activate(
        chart_id=args.chart_id,
        query_date=query_date,
        birth_dt=birth_dt,
        msr_path=Path(args.msr),
        vimshottari_raw_path=Path(args.vimshottari_raw),
        ayanamsha=args.ayanamsha,
    )

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2))
    print(
        f"Wrote {payload['signal_count']} signal-state rows for {query_date} "
        f"to {out_path}"
    )
    print(f"  state_summary: {payload['state_summary']}")
    print(f"  active_dasha: {payload['active_dasha']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
