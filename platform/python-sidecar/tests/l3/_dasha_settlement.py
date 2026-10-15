"""Synthetic settlement receipts for isolated SQL fixtures, never live chart evidence."""
import json


def settle_fixture_chart(tmp_path, monkeypatch, *, chart_id, build_id):
    """Exercise the real receipt parser and guards for the fixture's chart/run.

    Every provenance/fingerprint below is explicitly synthetic; no production
    receipt is changed and no population or projection check is bypassed.
    """
    from services.gochara_kernel import dasha_read

    prefix = str(build_id)[:8]
    record = {
        "schema": "gochara_dasha_settlement/1",
        "header_comment": "Synthetic test fixture only; reviewed PR policy shape.",
        "utc": "2000-01-01T00:00:00Z", "pos_build": prefix,
        "dash_build": prefix, "natal_fp": "00000000", "vim13_fp": "00000000",
        "vim13_rows": 1, "dash_all_fp": "00000000",
        "run_id": str(build_id), "chart_id": str(chart_id),
        "provenance": {
            "source": "origin/campaign-coordination:00_ARCHITECTURE/briefs/CAMPAIGN_COORDINATION.md",
            "commit": "0" * 40, "heading": "L1_SETTLED v1",
            "release_receipt": "synthetic-test-fixture", "rebuild_run": str(build_id),
        },
    }
    record["line"] = (
        f"L1_SETTLED v1 utc={record['utc']} pos_build={prefix} dash_build={prefix} "
        "natal_fp=00000000 vim13_fp=00000000 vim13_rows=1 dash_all_fp=00000000"
    )
    path = tmp_path / "synthetic-dasha-settlement.json"
    path.write_text(json.dumps(record), encoding="utf-8")
    monkeypatch.setattr(dasha_read, "SETTLEMENT_PATH", path)
    return path
