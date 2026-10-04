"""Test helper — what the SEPARATE VERIFICATION JOB persists, for fixtures that connect as a superuser.

Since R9-6.1 the builder never writes a verification row; the verifier principal's job does (`verification_job.verify_class`,
which also certifies contact geometry against a full ephemeris — unrealistic for the small stand-in worlds most suites use).
This helper performs exactly the WINDOW half of that persistence (member support + member geometry + window semantics, then
the generation-bound 1240 row) for each included P1–P4 grain, so a suite can build a world and then 'run the verifier' on it.
The real job, identity self-check and all, is tested in test_a53_verification_job.py."""
from __future__ import annotations

from services.gochara_kernel import window_gate as wg
from services.gochara_kernel import window_verifier as wv

from .test_a53_inventory import CHART_ID


def persist_window_verification(conn, writer_mod, *, event_class, generation, paths=("P1", "P2", "P3", "P4"),
                                chart_id=CHART_ID, report_overrides=None):
    pins = [tuple(r) for r in conn.execute(
        "SELECT path_id, rule_version FROM public.ka_gochara_search_path_pin WHERE chart_id = %s AND generation = %s"
        " AND event_class = %s AND disposition = 'included' AND path_id = ANY(%s) ORDER BY 1, 2",
        (chart_id, generation, event_class, list(paths))).fetchall()]
    snap = conn.execute("SELECT input_digest FROM public.ka_gochara_search_input_snapshot WHERE chart_id = %s"
                        " AND generation = %s", (chart_id, generation)).fetchone()[0]

    def position_at(body, t):
        jd = t.timestamp() / 86400.0 + 2440587.5
        return writer_mod.calc_sidereal_lon(body.title(), jd, None)[0]
    store = writer_mod.RuleRegistryStore(conn)
    out = {}
    for path_id, version in pins:
        grain = dict(chart_id=chart_id, generation=generation, event_class=event_class, path_id=path_id,
                     rule_version=version)
        wv.verify_member_support(conn, **grain)
        wv.verify_member_geometry(conn, position_at=position_at, **grain)
        report = wv.verify_window_semantics(
            conn, factor_rows=store.bound_factor_rows(path_id, version),
            drishti_bound=writer_mod.DRISHTI_SOURCE is not None, vedha_bound=writer_mod.VEDHA_SOURCE is not None, **grain)
        report = {**report, **(report_overrides or {})}
        with conn.transaction():
            conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (chart_id,))
            conn.execute("SELECT public.ka_gochara_lock_global_shared()")
            wg.record_verification(conn, report=report, input_digest=snap, **grain)
        out[path_id] = report
    return out
