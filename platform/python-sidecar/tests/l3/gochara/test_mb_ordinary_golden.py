"""An ordinary (markerless) build is observably identical to its accepted parent: P06's final-rules build on current main, before P06b's near-miss seal integration.

The active golden, `fixtures/mb_ordinary_golden_p06.json`, was produced by this file's capture, run unmodified, on a scratch copy of the merged tree (main plus the
accepted P06 lineage) with the P06b-only production changes reversed; its provenance records the reversed patch's hash and paths. (I) INTERPRETATION: main's
`mb_ordinary_golden_j4p.json` predates P06's final rules, snapshot copies and class census, so it cannot baseline a tree that carries P06; the baseline is re-captured
by the same method and main's fixtures stay byte-for-byte unchanged (the B4 baseline test below still compares them with each other). Every comparison stays strict.

    MB_GOLDEN_OUT=<path> python -m pytest tests/l3/gochara/test_mb_ordinary_golden.py -k capture

It holds, for a markerless run driven through the writer's REAL substeps on the real migration chain (the a55 template), with the real runner's config keys
(`chart_id`, `birth_params`) and an explicit rehearsal horizon:
  * every substep kind (rules, convention, body, manifest, snapshot, inventory, coverage, record, window, verify) and a dry run: its observable outcome (rows inserted
    and notes, or the refusal's type and message), the SQL statements it issued through the connection (whitespace-normalised text and parameter count, kept as a count
    per distinct statement shape plus the sha256 of the ordered sequence), and the row count of every ka_gochara_* / kala_gochara_* table after it;
  * the candidate manifest's input vector, every component.
HEAD must equal it except `implementation.*` (P06b's edited governed sources; the window identity is pinned below) and ONE extra read-only statement on the
new manifest substep: the near-miss layer catalogue probe. The state guard and B5's period guard are in the golden (the parent has them) and compared like every
other statement.
Texts are normalised only for values that differ between two runs of the SAME tree (per-world ids and the digests derived from them, in the notes): hex runs of 12+
characters (or a truncated id before an ellipsis) and UUIDs. Two captures on main agree exactly after that."""
from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path

import pytest

from pipeline.orchestrator.writers import ContextSpec, SubStep
from pipeline.orchestrator.writers import ka_gochara_v5 as writer_mod

from .conftest import EPHE_PATH
from .test_a53_inventory import CHART_ID
from .test_a55_replace_chain import SHORT, _World, template  # noqa: F401

FIXTURES = Path(__file__).resolve().parent / "fixtures"
GOLDEN = FIXTURES / "mb_ordinary_golden_p06.json"
GOLDEN_COMMIT = "p06-parent-merge-2fa1cafdf207d9243f8f89b34b42e15b580a3830"
J4P_GOLDEN = FIXTURES / "mb_ordinary_golden_j4p.json"
J4P_GOLDEN_COMMIT = "2d75833d3963a61544deaa4c36cc8322cb2cdcb5"
# The capture recorded the dasha build then settled (L1_SETTLED v1, 7377833e); the snapshot notes name it as "build <uuid first four groups>-<hex>", and the final
# group is normalised away by `_norm`. A settlement move (dasha_settlement.json) changes only this identity, so the comparison re-points it at the governed record
# instead of re-capturing the golden or pinning a second literal.
GOLDEN_SETTLED_BUILD_PREFIX = "7377833e-5d3b-4e70-8bef-"
# P06b (ruling 18): P06b edits governed sources of all three stages (input_vector / input_vector_verifier feed geometry and evaluation; seal_brief.py and
# verification_job.py feed the window stage), so those three digests MUST differ from the parent's. The window identity is pinned exactly (computed from this tree with
# implementation_registry.compute()), so another window-code change requires review; geometry and evaluation are pinned by the parent comparison only.
P06B_WINDOW_IMPLEMENTATION = "2809556a4535d722803abae7f701712ed79e2d7571225018229c28d214e0112c"
# the REAL runner's birth parameters shape (birth_params._to_birth_params): main ignores them, an ordinary HEAD build must too
BIRTH_PARAMS = {"datetime_iso": "1984-02-05T10:43:00", "latitude_deg": 20.2961, "longitude_deg": 85.8245, "tz_offset_hours": 5.5, "place_name": "Bhubaneswar",
                "subject_label": "native"}
CLASS = "marriage"
GUARD_SELECT = "SELECT state FROM public.asset_throughput WHERE chart_id = %s AND asset_id = %s"
LAYER_SELECT = ("SELECT to_regclass('public.ka_gochara_near_miss') IS NOT NULL AND "
                "to_regclass('public.ka_gochara_near_miss_search') IS NOT NULL AND "
                "to_regclass('public.ka_gochara_near_miss_object') IS NOT NULL")
PERIOD_GUARD_SELECT = " ".join("""
    WITH governed_chart_dashas AS (
        SELECT * FROM public.chart_dashas
        WHERE chart_id = %s AND ayanamsha_id = %s AND build_id = %s
          AND system_id = ANY(%s) AND level_n BETWEEN 1 AND 4
          AND (verification_pass_status = %s
               OR (system_id = %s AND level_n = %s AND verification_pass_status = ANY(%s))
               OR (system_id = %s AND level_n = %s AND verification_pass_status = ANY(%s))))
    SELECT dasha_row_id, start_iso, end_iso FROM governed_chart_dashas
    WHERE start_iso IS NULL OR end_iso IS NULL OR end_iso <= start_iso LIMIT 1
""".split())


class _Rec:
    """A recording view of the connection: every `execute` is noted (whitespace-normalised SQL, parameter count) and delegated unchanged; everything else passes through."""

    def __init__(self, conn):
        self._c, self.statements = conn, []

    def execute(self, sql, params=None, *a, **k):
        self.statements.append([" ".join(str(sql).split()), 0 if params is None else len(params)])
        return self._c.execute(sql, *((params,) if params is not None else ()), *a, **k)

    def __getattr__(self, name):
        return getattr(self._c, name)


_HEX = re.compile(r"\b[0-9a-f]{12,}\b|\b[0-9a-f]{8,}(?=\u2026)")          # a long hex run, or a truncated id ("candidate manifest 11d2af0c\u2026")
_UUID = re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b")


def _norm(text):
    return None if text is None else _UUID.sub("<uuid>", _HEX.sub("<hex>", str(text)))


def _summarise(statements) -> dict:
    """A compact, order-sensitive summary of the statements: how many, how often each distinct shape ran, and the sha256 of the ordered sequence."""
    shapes: dict = {}
    for sql, n in statements:
        shapes[f"{n}|{sql}"] = shapes.get(f"{n}|{sql}", 0) + 1
    seq = hashlib.sha256("\n".join(f"{n}|{sql}" for sql, n in statements).encode("utf-8")).hexdigest()
    return {"count": len(statements), "shapes": dict(sorted(shapes.items())), "sequence_sha256": seq}


def _counts(conn):
    names = [r[0] for r in conn.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE' AND (table_name LIKE 'ka\\_gochara\\_%' "
        "OR table_name LIKE 'kala\\_gochara\\_%') ORDER BY 1").fetchall()]
    return {t: conn.execute(f'SELECT count(*) FROM public."{t}"').fetchone()[0] for t in names}


def _keys():
    wp = [p for p in ("P2", "P3") if p in writer_mod.WINDOW_PATHS]
    return ([writer_mod.RULES_SUBSTEP, writer_mod.CONVENTION_SUBSTEP, f"{writer_mod.BODY_SUBSTEP_PREFIX}{writer_mod.SUBSTRATE_BODIES[0]}", writer_mod.MANIFEST_SUBSTEP,
             writer_mod.SNAPSHOT_SUBSTEP, f"{writer_mod.INVENTORY_SUBSTEP_PREFIX}{CLASS}", f"{writer_mod.COVERAGE_SUBSTEP_PREFIX}{CLASS}"]
            + [f"{writer_mod.RECORD_SUBSTEP_PREFIX}{CLASS}:{p}" for p in ("P2", "P3")] + [f"{writer_mod.WINDOW_SUBSTEP_PREFIX}{CLASS}:{p}" for p in wp]
            + [f"{writer_mod.VERIFY_SUBSTEP_PREFIX}{CLASS}"])


def capture(template_db, raw: dict | None = None) -> dict:
    """Drive the markerless run's substeps through the real writer on a clone of the template; return the observable record. Identical code runs on main and on HEAD.
    `raw`, when given, receives each substep's unsummarised statement list (HEAD's comparison removes the state guard's statement before summarising)."""
    w = _World(template_db)
    try:
        # The immutable main capture used this session zone. PostgreSQL renders
        # timestamptz refusals and convention JSON in the session zone.
        w.conn.execute("SET TIME ZONE 'Asia/Kolkata'")
        # the orchestrator's `asset_throughput` row of a healthy run (`building`); main never reads it, HEAD's state guard does
        w.conn.execute("CREATE TABLE public.asset_throughput (chart_id uuid, asset_id text, state text, last_built_at timestamptz, rows_written integer, last_error text)")
        w.conn.execute("INSERT INTO public.asset_throughput VALUES (%s::uuid, %s, 'building', now(), 0, NULL)", (CHART_ID, writer_mod.ASSET_ID))
        rec = _Rec(w.conn)
        out = {"golden_commit": GOLDEN_COMMIT, "horizon": [x.isoformat() for x in SHORT], "substeps": []}

        def run(key, dry_run=False):
            rec.statements.clear()
            ctx = ContextSpec(asset_id=writer_mod.ASSET_ID, build_id="b-golden", db_conn=rec, dry_run=dry_run,
                              config={"chart_id": CHART_ID, "birth_params": BIRTH_PARAMS, "horizon": SHORT, "ephe_path": EPHE_PATH})
            try:
                with w.conn.transaction():
                    res = writer_mod.GocharaV5Writer().run_substep(ctx, SubStep(key=key, label=key))
                outcome = {"rows_inserted": res.rows_inserted, "notes": _norm(res.notes)}
            except Exception as exc:  # noqa: BLE001 - a refusal is an observable outcome too
                outcome = {"error": type(exc).__name__, "message": _norm(exc)}
            label = key + (" [dry_run]" if dry_run else "")
            if raw is not None:
                raw[label] = [list(s) for s in rec.statements]
            out["substeps"].append({"key": label, "outcome": outcome, "statements": _summarise(rec.statements), "counts": _counts(w.conn)})
        run(writer_mod.RULES_SUBSTEP, dry_run=True)
        for key in _keys():
            run(key)
            if key == writer_mod.MANIFEST_SUBSTEP:
                row = w.conn.execute("SELECT input_generation_vector FROM public.kala_gochara_publication WHERE chart_id = %s AND generation = %s",
                                     (CHART_ID, writer_mod.GENERATION)).fetchone()
                out["manifest_vector"] = row[0] if isinstance(row[0], dict) else json.loads(row[0])
        return out
    finally:
        w.close()


def test_capture_the_markerless_run(template):
    """Writes the capture to $MB_GOLDEN_OUT (how the golden was generated, on main); without it, only checks the capture is repeatable."""
    got = capture(template)
    dest = os.environ.get("MB_GOLDEN_OUT")
    if dest:
        Path(dest).write_text(json.dumps(got, indent=1, sort_keys=True), encoding="utf-8")
    assert got["substeps"] and "manifest_vector" in got


# ── the comparison (HEAD against the P06 parent golden) ───────────────────────────────────────────────────────────────────────

def _load():
    assert GOLDEN.exists(), f"the P06 parent golden ({GOLDEN_COMMIT}) is missing: {GOLDEN}"
    golden = json.loads(GOLDEN.read_text(encoding="utf-8"))
    assert golden["golden_commit"] == GOLDEN_COMMIT
    assert golden["provenance"]["sql_adaptations"] == {}, "the P06 parent golden is an unadapted capture"
    return golden


def _load_j4p():
    assert J4P_GOLDEN.exists(), f"the pre-B4 golden ({J4P_GOLDEN_COMMIT}) is missing: {J4P_GOLDEN}"
    golden = json.loads(J4P_GOLDEN.read_text(encoding="utf-8"))
    assert golden["golden_commit"] == J4P_GOLDEN_COMMIT
    assert golden["provenance"]["sql_adaptations"] == {
        "state_guard_selects_removed": 12,
        "b4_cte_positive_bounds_predicates_removed": 1,
    }
    return golden


def _follow_settlement(golden: dict) -> dict:
    """The golden with its one settled-build identity re-pointed at the governed settlement record.

    Only the dasha build named in the snapshot notes moves; the golden must carry that identity exactly once (so the
    re-pointing is never silent or vacuous) and every other field stays strictly compared.
    """
    from services.gochara_kernel import dasha_read

    run_id = dasha_read.load_dasha_settlement(CHART_ID)["run_id"]
    settled_prefix = run_id.rsplit("-", 1)[0] + "-"
    text = json.dumps(golden, sort_keys=True)
    assert text.count(GOLDEN_SETTLED_BUILD_PREFIX) == 1, "the golden names its settled dasha build exactly once"
    return json.loads(text.replace(GOLDEN_SETTLED_BUILD_PREFIX, settled_prefix))


def test_b4_baseline_preserves_final_main_settlement_amendments():
    """Keep final J-4p's outcomes and transcript alongside B4's baseline.

    B4 deliberately removes one positive-bounds SQL predicate; B5's additional
    guard is counted separately below. No other main SQL shape may change.
    """
    main = json.loads(FIXTURES.joinpath("mb_ordinary_golden_main.json").read_text())
    b4 = _load_j4p()
    assert [s["key"] for s in b4["substeps"]] == [s["key"] for s in main["substeps"]]
    for got, want in zip(b4["substeps"], main["substeps"]):
        assert got["outcome"] == want["outcome"], want["key"]
        assert got["counts"] == want["counts"], want["key"]
        if want["key"] == "inventory:marriage":
            shapes = want["statements"]["shapes"]
            assert sum(n for sql, n in shapes.items()
                       if "AND start_iso < end_iso AND" in sql) == 1
            assert got["statements"]["shapes"] == {
                sql.replace("AND start_iso < end_iso AND", "AND"): n
                for sql, n in shapes.items()
            }
            assert got["statements"]["count"] == want["statements"]["count"]
        else:
            assert got["statements"] == want["statements"], want["key"]
    assert b4["manifest_vector"]["implementation"]["window"] == (
        "beaa23107518458b89bb8fe498a8b3682ffe67fb08951196a69c7b18db123aa4")
    # The two immutable captures used different local Swiss library builds;
    # their corpus, version and numerical probe must still agree exactly.
    for key, value in main["manifest_vector"].items():
        if key == "implementation":
            continue
        if key == "ephemeris":
            value = {k: v for k, v in value.items() if k != "library_sha256"}
            actual = {k: v for k, v in b4["manifest_vector"][key].items()
                      if k != "library_sha256"}
        else:
            actual = b4["manifest_vector"][key]
        assert actual == value, key


@pytest.fixture(scope="module")
def head(template):
    raw: dict = {}
    return capture(template, raw), raw


def test_every_substep_kind_of_a_markerless_run_equals_its_parent_except_the_one_read_only_layer_probe(head):
    got, raw = head
    want = _follow_settlement(_load())
    assert [s["key"] for s in got["substeps"]] == [s["key"] for s in want["substeps"]]
    kinds = {s["key"].split(":")[0].split(" ")[0] for s in want["substeps"]}
    assert kinds >= {"rules", "convention", "body", "manifest", "snapshot", "inventory", "coverage", "record", "window", "verify"}, kinds
    for g, m in zip(got["substeps"], want["substeps"]):
        key = m["key"]
        assert g["outcome"] == m["outcome"], f"{key}: the observable outcome differs from the P06 parent"
        assert g["counts"] == m["counts"], f"{key}: the table row counts differ from the P06 parent"
        guard = [s for s in raw[key] if s == [GUARD_SELECT, 2]]
        period_guard = [s for s in raw[key] if s == [PERIOD_GUARD_SELECT, 11]]
        assert len(period_guard) == (1 if key == "inventory:marriage" else 0), f"{key}: expected the B5 period guard exactly once before the inventory projection"
        assert len(guard) == (0 if "[dry_run]" in key else 1), f"{key}: expected exactly one state-guard SELECT per non-dry-run substep, saw {len(guard)}"
        # P06b adds only this catalogue probe while creating a NEW manifest. Replay restates the stored pin without probing.
        layer = [s for s in raw[key] if s == [LAYER_SELECT, 0]]
        assert len(layer) == (1 if key == "manifest" else 0), (key, layer)
        rest = [s for s in raw[key] if s != [LAYER_SELECT, 0]]
        assert _summarise(rest) == m["statements"], f"{key}: the statements other than the one authorized read-only probe differ from the P06 parent"


def test_the_ordinary_manifest_vector_equals_its_parent_in_every_component_except_the_implementation_identity(head):
    """Every component of the stored vector of a markerless run equals the parent's, except `implementation.*` (P06b's edited governed sources: those digests MUST differ,
    the window stage is pinned exactly). No `horizon_basis` and no `test_slice` component may appear in an ordinary run."""
    got, want = head[0]["manifest_vector"], _load()["manifest_vector"]
    assert "horizon_basis" not in got and "test_slice" not in got

    same_host = got["ephemeris"]["platform"] == want["ephemeris"]["platform"]
    host_bound = () if same_host else ("platform", "library_sha256", "probe_digest")
    # the golden was generated on `want['ephemeris']['platform']`: the host library's own identity (its artifact hash, platform string and numerical probe digest) is a
    # property of the MACHINE, not of the repository's code, so on another host those three are not compared; every other component is, exactly

    def comparable(v):
        out = {k: x for k, x in v.items() if k != "implementation"}
        out["ephemeris"] = {k: x for k, x in v["ephemeris"].items() if k not in host_bound}
        return out
    assert comparable(got) == comparable(want), "non-implementation components equal the P06 parent (excluding another host's library identity)"
    assert set(got["implementation"]) == set(want["implementation"])
    differing = sorted(st for st in got["implementation"] if got["implementation"][st] != want["implementation"][st])
    assert differing == ["evaluation", "geometry", "window"], differing
    assert got["implementation"]["window"] == P06B_WINDOW_IMPLEMENTATION
