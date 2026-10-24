"""SR-NEARMISS-DOMAIN-TAIL-AMEND-3 finding 2 — the report-level near-miss disclosure COUNT, measured through the real verifier on a real database.

A Saturn-slow rootless stretch whose station (1997-12-17) lies BEFORE the identity domain (opens 1998-01-01) and whose tail runs 7 days into it is not
stored (the builder's arc index cannot see it) and not refused: `verify_generation` DISCLOSES it. `test_nm_identity_domain_tail.py` pins the pieces
(`split_identity_domain_tails`, `tail_record`, `tail_disclosure`) on their own; nothing there pins that `verify_generation`'s RESULT carries the disclosure, nor
that the job's fresh near-miss pass stores that result as `report["near_miss"]`. Dropping the merge left every pre-existing test green.

Claim (one oracle, two stages of one chain):
  * `verify_generation` returns `identity_domain_tail_count == 1` and the tail's object id, body, relation and dates (`**tail_disclosure(edge_tails)` in its return);
  * `verification_job.run`'s fresh pass (nothing persisted yet) stores that same dict as `report["near_miss"]`.
Reversion: drop `**tail_disclosure(edge_tails)` from `verify_generation`'s return -> this fails (KeyError on the count).

The curve is the analytic parabola of `test_nm_identity_domain_tail.py` (edge speed ~0.03 deg/day, band left 22 days after the station), capped so it is flat
once far from the band; every other body is untouched (this world has a Saturn obligation only). The database is the p06b chain (migrations 1305/1306/1308/1381
on a guarded `create_am5_database`), the horizon the template of `test_a_stationless_contact_root_outside_the_domain_is_followed_not_called_a_near_miss`."""
from __future__ import annotations

from datetime import timedelta

import pytest

from services.gochara_kernel import near_miss_verifier as nv
from services.gochara_kernel.near_miss_verifier import utc

from .test_p06b_near_miss_integration import _apply, chain  # noqa: F401  (the fixture and its migration helper are this oracle's database)

STATION = utc(1997, 12, 17)                                          # 15 days before the domain opens (1998-01-01)
HORIZON = (utc(1998, 1, 1), utc(1998, 1, 5))                         # the tail (1998-01-01 -> ~1998-01-08) overlaps it
ORB, CENTRE, C = 1.0, 100.0, 0.5
K = (ORB - C) / 22.0 ** 2                                            # the band is left 22 days after the station, i.e. 7 days into the domain
REASON = "rootless_stretch_crosses_identity_domain"


def _saturn_slow(body, t):
    """Saturn: the parabola about the station (flat 60 degrees out, so no second crossing in the 87-year domain); the other bodies are not searched in this world."""
    assert body == "saturn", body
    d = (t - STATION).total_seconds() / 86400.0
    return (CENTRE + C + min(K * d * d, 60.0)) % 360.0


def test_verify_generation_carries_the_tail_count_and_the_fresh_job_pass_stores_it_in_the_report(chain, monkeypatch):    # noqa: F811
    from services.gochara_kernel import inventory as inv, near_miss as builder, verification_job as vj
    from services.gochara_kernel import numerical_window_gate as nwg
    from services.gochara_kernel.inventory_store import InventoryStore
    from .test_a53_inventory import CHART_ID, FACT_IDS

    c = chain
    _apply(c)
    sky = c.execute("SELECT sky_convention_id FROM ka_gochara_convention_bridge").fetchone()[0]
    target = f"point:{CENTRE:.6f}"
    with c.transaction():
        vj.take_locks(c, CHART_ID)
        c.execute("UPDATE kala_gochara_publication SET horizon=tstzrange(%s,%s,'[)'),input_generation_vector=input_generation_vector || "
                  "jsonb_build_object('near_miss_layer_version',1,'sky_convention',jsonb_build_object('id',%s::text))", (*HORIZON, sky))
        c.execute("UPDATE chart_dashas SET start_iso=start_iso-interval '27 years',end_iso=end_iso-interval '27 years'")
        ids = [r[0] for r in c.execute("SELECT dasha_row_id FROM chart_dashas WHERE start_iso<%s AND end_iso>%s", (HORIZON[1], HORIZON[0]))]
        store = InventoryStore(c)
        inp = store.insert_snapshot(chart_id=CHART_ID, generation="5.0", convention_id=sky, consumed_fact_ids=FACT_IDS, consumed_dasha_row_ids=ids)
        ob = inv.Obligation("marriage", "P3", "1.0.0", "saturn", "conjunction", "natal_planet", target, "natal", "native")
        store.write_class_inventory(chart_id=CHART_ID, generation="5.0", input_digest=inp, plan=inv.ClassInventory(
            "marriage", HORIZON, (inv.PinPlan("P3", "1.0.0", "included", (ob,)),), (inv.IntervalPlan(ob.ob_id, *HORIZON, inv.STATE_COMPLETE),)))
        obj = builder.NearMissObject("saturn", "conjunction", target, "orb_conj_slow:1.000000", sky)
        builder.NearMissStore(c).write_object(chart_id=CHART_ID, generation="5.0", obj=obj, horizon=HORIZON, near_misses=[], dasha_rows=[])
    monkeypatch.setattr(nv, "_ephemeris_position", lambda ephe_path: _saturn_slow)

    # 1. the verifier's own result: one tail, with its object id, body, relation and dates, and the count a reader compares with zero
    with c.transaction():
        vj.take_locks(c, CHART_ID)
        result = nv.verify_generation(c, chart_id=CHART_ID, generation="5.0", ephe_path="unused", persist=False)
    assert result["status"] == "VERIFIED" and result["objects"] == 1
    assert result["identity_domain_tail_count"] == 1 == len(result["identity_domain_tails"])
    (tail,) = result["identity_domain_tails"]
    assert tail["object_id"] == str(obj.uuid) and tail["body"] == "saturn" and tail["relation"] == "conjunction"
    assert tail["reason"] == REASON and tail["station_in_domain"] is False
    assert tail["t_in"].startswith("1998-01-01")                                                            # the clipped piece: the domain's first instant ...
    assert utc(1998, 1, 1) + timedelta(days=6) < nv.datetime.fromisoformat(tail["t_out"]) < utc(1998, 1, 1) + timedelta(days=8)       # ... to ~1998-01-08

    # 2. the job's fresh pass (nothing persisted yet) stores exactly that dict as report["near_miss"]; the other stages are held at their own matching values
    monkeypatch.setattr(vj, "check_preconditions", lambda *a, **kw: {"classes": []})
    monkeypatch.setattr(vj, "precondition_fingerprint", lambda *a: "same")
    monkeypatch.setattr(vj, "near_miss_verified_for_state", lambda *a: None)
    monkeypatch.setattr(vj, "candidate_gate_on_candidate_manifest", lambda *a: [])
    monkeypatch.setattr(nwg, "generation_verdict", lambda *a, **kw: {"status": nwg.NOT_APPLICABLE, "policy": None, "problems": []})
    report = vj.run(c, chart_id=CHART_ID, generation="5.0", position_at=None, ephe_path="unused", modules={"known": ()},
                    configured_selection_for=lambda cls: {}, path_rulings={}, h_unknown={}, moon_scope_domain=False, factor_rows_for=lambda *a: [],
                    drishti_bound=False, vedha_bound=False, report_only=True, enforce_identity=False)
    assert report["near_miss"] == result
    assert report["near_miss"]["identity_domain_tail_count"] == 1 and report["near_miss"]["identity_domain_tails"] == [tail]
