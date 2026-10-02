"""A5.3 — independent review F-R13-9: what the SEALING transaction and the state-digest function COST at all-NULL-candidate volume.

NOT part of CI (no `test_` file name — run it explicitly, ONE narrow command, on a local disposable server):

    GOCHARA_PERF_FACTOR=10 python -m pytest tests/l3/gochara/perf_a53_seal_cost.py -q -s -k replicated

It builds the faithful disposable world (real 1204…1241 chain, one event class, 4 verified grains), then REPLICATES it to N event classes
(the real candidate has 26 scored classes) times a density factor: every class-keyed table (records, prerequisites, windows, member links,
path pins, inventory header, obligations, intervals, both verification tables, coverage) is cloned per pseudo-class under
`session_replication_role = replica`; contacts and the search-input snapshot are shared (geometry is class-independent). The clones are NOT a
consistent candidate (the gate would refuse them) — the measurement is of READ cost, which is what every sealing step does:
`ka_gochara_brief_state_digest` (SQL), the generation-wide output identity, the publication content digest, the combined candidate gate,
the whole `build_payload`; and (`-k end_to_end`) ONE real end-to-end seal at the unreplicated size as the real sealer role, timed phase by phase.
Prints a table; asserts nothing about speed.
"""
from __future__ import annotations

import os
import statistics
import time

from services.gochara_kernel import candidate_boundary as cb
from services.gochara_kernel import seal_brief as sb
from services.gochara_kernel import seal_flow as sf

from .test_a53_inventory import CHART_ID
from .test_a53_p1_support import GEN
from .test_a53_r10_complete_records import built, rworld  # noqa: F401
from .test_a53_r11_seal_brief import _brief_as_verifier, _sealer_stand_ins, _verified  # noqa: F401
from .test_a53_window_verification_gate import SPANS, _boot_p3  # noqa: F401
from .test_a53_window_verification_roles import _consistent_sky  # noqa: F401

CLASSES = 26


def _timed(fn, reps=3):
    xs = []
    for _ in range(reps):
        t = time.perf_counter()
        fn()
        xs.append(time.perf_counter() - t)
    return statistics.median(xs)


def _scored_classes(conn) -> list[str]:
    """The 26 scored event classes — read from the relationship-record CHECK (27 names there; birth_anchor is not scored)."""
    import re
    d = conn.execute("SELECT pg_get_constraintdef(oid) FROM pg_constraint WHERE conname = 'kgrr_event_class_ck'").fetchone()[0]
    return [c for c in re.findall(r"'([a-z_]+)'", d) if c != "birth_anchor"]      # (birth_anchor is the anchor class, not a scored one)


def _replicate(conn, base_class: str, factor: int) -> None:
    """Make the world `factor` times the size of ALL 26 scored classes: the class-keyed small tables (pins, inventory header, both
    verification tables, coverage) are cloned once per other class; the volume tables (records, prerequisites, windows, member links,
    obligations, intervals) are cloned per (class, salt) so that every class carries `factor` copies of the base class' rows."""
    classes = _scored_classes(conn)
    assert len(classes) == CLASSES, classes
    conn.execute("DROP TABLE IF EXISTS _cls")
    conn.execute("CREATE TEMP TABLE _cls (cls text, salt int)")
    for cls in classes:
        for salt in range(factor):
            if not (cls == base_class and salt == 0):                      # (the base class' salt-0 copy IS the original rows)
                conn.execute("INSERT INTO _cls VALUES (%s, %s)", (cls, salt))
    conn.execute("DROP TABLE IF EXISTS _cls0")
    conn.execute("CREATE TEMP TABLE _cls0 AS SELECT DISTINCT cls FROM _cls WHERE salt = 0 AND cls <> %s", (base_class,))
    # the cloned rows are NOT a consistent candidate (their content-derived ids/bytes no longer match): drop the derived-value CHECKs of the
    # volume tables on this THROWAWAY database so the rows can exist — only READ cost is measured
    for t in ("ka_gochara_search_obligation", "ka_gochara_search_interval", "ka_gochara_relationship_record", "ka_gochara_eval_window",
              "ka_gochara_eval_window_record", "ka_gochara_record_prerequisite"):
        for (cn,) in conn.execute("SELECT conname FROM pg_constraint WHERE conrelid = %s::regclass AND contype = 'c'",
                                  (f"public.{t}",)).fetchall():
            conn.execute(f'ALTER TABLE public.{t} DROP CONSTRAINT "{cn}"')
    with conn.transaction():
        conn.execute("SET LOCAL session_replication_role = replica")
        key = "md5(%s || _cls.cls || _cls.salt::text)::uuid"

        def clone(table, overrides_sql, src=None, where=None, cross="_cls"):
            conn.execute(
                f"INSERT INTO public.{table} SELECT (jsonb_populate_record(NULL::public.{table}, to_jsonb(x) || ({overrides_sql}))).*"
                f" FROM {src or 'public.' + table} x CROSS JOIN {cross} WHERE {where or 'x.event_class = %s'}", (base_class,))
        rid, wid, oid = (key % f"x.{c}::text" for c in ("record_id", "window_id", "ob_id"))
        clone("ka_gochara_relationship_record", f"jsonb_build_object('event_class', _cls.cls, 'record_id', {rid})")
        conn.execute(
            "INSERT INTO public.ka_gochara_record_prerequisite SELECT (jsonb_populate_record(NULL::public.ka_gochara_record_prerequisite,"
            f" to_jsonb(p) || jsonb_build_object('record_id', {key % 'p.record_id::text'}))).*".replace("_cls.cls", "_cls.cls") +
            " FROM public.ka_gochara_record_prerequisite p JOIN public.ka_gochara_relationship_record x ON x.record_id = p.record_id"
            " CROSS JOIN _cls WHERE x.event_class = %s", (base_class,))
        clone("ka_gochara_eval_window", f"jsonb_build_object('event_class', _cls.cls, 'window_id', {wid})")
        clone("ka_gochara_eval_window_record",
              f"jsonb_build_object('event_class', _cls.cls, 'window_id', {key % 'x.window_id::text'}, 'record_id', {key % 'x.record_id::text'})")
        clone("ka_gochara_search_obligation", f"jsonb_build_object('event_class', _cls.cls, 'ob_id', {oid})")
        clone("ka_gochara_search_interval", f"jsonb_build_object('event_class', _cls.cls, 'ob_id', {oid})")
        for t in ("ka_gochara_search_path_pin", "ka_gochara_search_inventory", "ka_gochara_eval_window_verification",
                  "ka_gochara_search_inventory_verification"):
            clone(t, "jsonb_build_object('event_class', _cls0.cls)", cross="_cls0")
        conn.execute(
            "INSERT INTO public.kala_gochara_coverage SELECT (jsonb_populate_record(NULL::public.kala_gochara_coverage,"
            " to_jsonb(c) || jsonb_build_object('partition_key', _cls0.cls))).* FROM public.kala_gochara_coverage c CROSS JOIN _cls0"
            " WHERE c.partition_kind = 'event_class' AND c.partition_key = %s", (base_class,))


def _row_counts(conn):
    return {t: conn.execute(f"SELECT count(*) FROM public.{t}").fetchone()[0] for t in sb.OUTPUT_TABLES}


def test_measure_replicated_read_cost(built):
    """Read cost of every sealing step at CLASSES x GOCHARA_PERF_FACTOR pseudo-classes (default 1)."""
    w = built
    _verified(w)
    factor = int(os.environ.get("GOCHARA_PERF_FACTOR", "1"))
    base_class = w.conn.execute("SELECT event_class FROM public.ka_gochara_search_inventory").fetchone()[0]
    _replicate(w.conn, base_class, factor)
    w.conn.execute("ANALYZE")                      # (production tables carry statistics; an un-analysed clone would mislead the planner)
    c = _row_counts(w.conn)
    t_state = _timed(lambda: w.conn.execute("SELECT public.ka_gochara_brief_state_digest(%s::uuid, %s)", (CHART_ID, GEN)).fetchone())
    t_ident = _timed(lambda: sb.generation_output_identity(w.conn, CHART_ID, GEN))
    t_pub = _timed(lambda: cb.publication_content_digest(w.conn, CHART_ID, GEN))
    t_gate = _timed(lambda: w.conn.execute("SELECT count(*) FROM public.ka_gochara_candidate_gate_violations(%s::uuid, %s)",
                                           (CHART_ID, GEN)).fetchone())
    t_payload = _timed(lambda: sb.build_payload(w.conn, CHART_ID, GEN, sealing_commit="0" * 40), reps=1)
    print("\nPERF  classes  factor | obligations  records  intervals | state_digest  output_identity  publication_digest  gate  build_payload  (s)")
    print(f"PERF  {CLASSES * factor:>7}  x{factor:<5} | {c['ka_gochara_search_obligation']:>11}  {c['ka_gochara_relationship_record']:>7}  "
          f"{c['ka_gochara_search_interval']:>9} | {t_state:>12.3f}  {t_ident:>15.3f}  {t_pub:>18.3f}  {t_gate:>4.3f}  {t_payload:>13.3f}")
    # (R13-2 cost review) memory/bytes: the OLD state digest string_agg'd every row's whole JSON text; the CURRENT one aggregates a 64-hex hash per row.
    import subprocess

    import psycopg

    def fresh_backend_rss(sql, params):
        """RSS (MB) of a FRESH backend before and after running `sql` once — peak memory attributable to that statement."""
        with psycopg.connect(w.dsn, autocommit=True) as c:
            pid = c.execute("SELECT pg_backend_pid()").fetchone()[0]
            rss = lambda: int(subprocess.run(["ps", "-o", "rss=", "-p", str(pid)], capture_output=True, text=True).stdout.strip() or 0) / 1024
            before = rss()
            t0 = time.perf_counter()
            c.execute(sql, params).fetchone()
            return before, rss(), time.perf_counter() - t0
    sizes = {t: w.conn.execute(f"SELECT count(*), coalesce(sum(length((to_jsonb(x) - 'created_at')::text)), 0) FROM public.{t} x"
                               f" WHERE chart_id = %s AND generation = %s", (CHART_ID, GEN)).fetchone()
             for t in sb.OUTPUT_TABLES + sb._VERIFICATION_TABLES}
    biggest = max(sizes, key=lambda t: sizes[t][1])
    rows, old_bytes = sizes[biggest]
    old_sql = (f"SELECT encode(sha256(convert_to(string_agg(j::text, E'\\n' ORDER BY j::text COLLATE \"C\"), 'UTF8')), 'hex') FROM"
               f" (SELECT to_jsonb(x) - 'created_at' AS j FROM public.{biggest} x WHERE x.chart_id = %s AND x.generation = %s) s")
    new_sql = (f"SELECT encode(sha256(convert_to(string_agg(h, E'\\n' ORDER BY h COLLATE \"C\"), 'UTF8')), 'hex') FROM"
               f" (SELECT encode(sha256(convert_to((to_jsonb(x) - 'created_at')::text, 'UTF8')), 'hex') AS h FROM public.{biggest} x"
               f" WHERE x.chart_id = %s AND x.generation = %s) s")
    ob, oa, ot = fresh_backend_rss(old_sql, (CHART_ID, GEN))
    nb, na, nt = fresh_backend_rss(new_sql, (CHART_ID, GEN))
    print(f"PERF  largest table {biggest}: {rows} rows. OLD (whole-row text aggregated): one field of {old_bytes / 1e6:.1f} MB "
          f"(PG caps a field at 1 GB = ~{1e9 / max(old_bytes / max(rows, 1), 1):,.0f} rows of this width), {ot:.2f}s, backend RSS {ob:.0f}->{oa:.0f} MB. "
          f"NEW (per-row hash): one field of {rows * 65 / 1e6:.2f} MB (64 hex + separator per row, whatever the row width), {nt:.2f}s, RSS {nb:.0f}->{na:.0f} MB")
    print("PERF  statement_timeout of this session:", w.conn.execute("SHOW statement_timeout").fetchone()[0], "(0 = none; the jobs set none)")


def test_measure_end_to_end_seal_as_the_real_sealer(built, monkeypatch):
    """ONE real seal (recompute -> publish -> authoritative seal -> receipt -> post-publication re-check) as `gochara_sealer`, per phase."""
    from psycopg.conninfo import make_conninfo
    import psycopg
    from .test_a53_verification_job import PASSWORD
    w = built
    _verified(w)
    digest = _brief_as_verifier(w, sealing_commit="0" * 40)["sha256"]
    _sealer_stand_ins(w)
    w.conn.execute(f"ALTER ROLE gochara_sealer LOGIN PASSWORD '{PASSWORD}'")
    try:
        t0 = time.perf_counter()
        with psycopg.connect(make_conninfo(w.dsn, user="gochara_sealer", password=PASSWORD), autocommit=True) as conn:
            marks = {}
            real_build, real_publish = sb.build_payload, sf.gk_ledger.publish

            def build(*a, **k):
                t = time.perf_counter()
                r = real_build(*a, **k)
                marks.setdefault("build_payload", []).append(time.perf_counter() - t)
                return r

            def publish(*a, **k):
                t = time.perf_counter()
                r = real_publish(*a, **k)
                marks["publish"] = time.perf_counter() - t
                return r
            monkeypatch.setattr(sb, "build_payload", build)
            monkeypatch.setattr(sf.gk_ledger, "publish", publish)
            sf.execute_seal(conn, chart_id=CHART_ID, generation=GEN,
                            approval={"brief_digest": digest, "run_id": 1, "run_attempt": 1, "approver_login": "x",
                                      "approved_by_note": "ruling:perf; actor:perf"},
                            run_id=1, run_attempt=1, sealing_commit="0" * 40, triggering_actor="perf")
            total = time.perf_counter() - t0
        print(f"\nPERF end-to-end seal (1 class, 4 grains): total {total:.3f}s incl. connect + identity check; "
              f"build_payload x{len(marks['build_payload'])}: " + ", ".join(f"{x:.3f}" for x in marks["build_payload"]) +
              f"; publish {marks['publish']:.3f}s")
    finally:
        w.conn.execute("ALTER ROLE gochara_sealer NOLOGIN PASSWORD NULL")
