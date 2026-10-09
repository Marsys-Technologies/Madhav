"""Freeze exception 2/2: service-probe output fingerprint.

An unchanged probe result must record output_changed=False (so staleness.py
does not stale dependents); a changed result, a missing prior fingerprint, or
any error path must stay fail-open (propagate).
"""
import sys
import pathlib
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from pipeline.orchestrator import asset_runner as ar  # noqa: E402
from pipeline.orchestrator import provenance, staleness  # noqa: E402
from pipeline.orchestrator.service_probes import probe_output_fingerprint  # noqa: E402

SPEC = {"probe_type": "ephemeris_engine", "jd": 2445000.5}


def _result(sha="a" * 64, **extra):
    return {
        "status": "GREEN", "message": "All checks passed",
        "checks": [{"check": "ephemeris_corpus_sha256", "passed": True, "sha": sha, **extra}],
    }


# ── fingerprint is a real detector ───────────────────────────────────────────

def test_fingerprint_stable_and_ignores_volatile_fields():
    a = probe_output_fingerprint("bg_x", SPEC, _result(duration_ms=3, timestamp="t1", run_id="r1"))
    b = probe_output_fingerprint("bg_x", SPEC, _result(duration_ms=99, timestamp="t2", run_id="r2"))
    assert a == b


def test_fingerprint_changes_when_result_changes():
    base = probe_output_fingerprint("bg_x", SPEC, _result())
    assert base != probe_output_fingerprint("bg_x", SPEC, _result(sha="b" * 64))
    assert base != probe_output_fingerprint("bg_x", {**SPEC, "jd": 1.0}, _result())
    assert base != probe_output_fingerprint("bg_y", SPEC, _result())


# ── receipt persistence returns output_changed ───────────────────────────────

def _persist(prior, fingerprint):
    cur = MagicMock()
    captured = {}
    with patch.object(ar, "load_upstream_receipts", return_value=[]), \
         patch.object(ar, "compute_upstream_hash", return_value="u"), \
         patch.object(ar, "get_writer_source_hash", return_value="c"), \
         patch.object(provenance, "previous_output_digest", return_value=prior), \
         patch.object(provenance, "capture_and_persist_receipt",
                      side_effect=lambda cur, **k: captured.update(k)):
        changed = ar._persist_probe_receipt(
            cur, run_id="r", chart_id="c1", asset_id="bg_x", declared_deps=[],
            natural_key_partition=None, has_cowriters=False, probe_config={},
            result_message="m", output_fingerprint=fingerprint,
        )
    return changed, captured["output_digest"]


def test_persist_unchanged_fingerprint_is_not_changed():
    fp = probe_output_fingerprint("bg_x", SPEC, _result())
    _, digest = _persist(None, fp)
    changed, digest2 = _persist(digest, fp)
    assert changed is False and digest2 == digest


def test_persist_changed_fingerprint_propagates():
    _, digest = _persist(None, probe_output_fingerprint("bg_x", SPEC, _result()))
    changed, _ = _persist(digest, probe_output_fingerprint("bg_x", SPEC, _result(sha="b" * 64)))
    assert changed is True


def test_persist_no_prior_fingerprint_propagates():
    changed, _ = _persist(None, probe_output_fingerprint("bg_x", SPEC, _result()))
    assert changed is True


def test_persist_legacy_prior_digest_propagates():
    changed, _ = _persist("legacy-run-id-digest", probe_output_fingerprint("bg_x", SPEC, _result()))
    assert changed is True


# ── end-to-end through _run_service_health_probe ─────────────────────────────

def _run(result=None, persist_ret=True, persist_exc=None, probe_exc=None):
    conn, cur = MagicMock(), MagicMock()
    rp = MagicMock(return_value=result) if probe_exc is None else MagicMock(side_effect=probe_exc)
    pr = MagicMock(return_value=persist_ret, side_effect=persist_exc)
    with patch.object(ar, "emit_event"), patch.object(ar, "mark_asset_error") as err, \
         patch.object(ar, "_persist_probe_receipt", pr), \
         patch("pipeline.orchestrator.service_probes.run_health_probe", rp):
        ar._run_service_health_probe(conn, cur, "run1", "c1", "bg_x", SPEC)
    sqls = [c.args for c in cur.execute.call_args_list if "output_changed" in c.args[0]]
    return sqls, err, pr


def test_unchanged_probe_records_output_changed_false():
    sqls, err, pr = _run(_result(), persist_ret=False)
    assert sqls and sqls[0][1][0] is False
    assert pr.call_args.kwargs["output_fingerprint"] == probe_output_fingerprint("bg_x", SPEC, _result())


def test_changed_probe_records_output_changed_true():
    sqls, _, _ = _run(_result(), persist_ret=True)
    assert sqls and sqls[0][1][0] is True


def test_probe_error_does_not_write_output_changed():
    sqls, err, pr = _run(probe_exc=RuntimeError("boom"))
    assert not sqls and err.called and not pr.called


def test_persist_error_marks_error_and_no_false_signal():
    sqls, err, _ = _run(_result(), persist_exc=RuntimeError("db"))
    assert err.called and not sqls


# ── downstream staling decision (staleness.py reads the recorded flag) ───────

def _propagate(output_changed):
    conn, cur = MagicMock(), MagicMock()
    cur.fetchone.return_value = (output_changed,)
    cur.fetchall.return_value = []
    events = []
    with patch.object(staleness, "compute_downstream_ids", return_value={"dep"}) as cd:
        staleness.propagate_downstream_staleness(
            conn, cur, "c1", "bg_x", set(), [], events.append, "run1",
        )
    return cd, events


def test_false_does_not_stale_dependents():
    cd, events = _propagate(False)
    assert not cd.called
    assert [e["type"] for e in events] == ["asset.refreshed_no_delta"]


def test_true_and_null_still_stale_dependents():
    for flag in (True, None):
        cd, _ = _propagate(flag)
        assert cd.called


# ── review follow-ups ────────────────────────────────────────────────────────

def _run_stateful(results, store, fp_exc=None):
    """Run _run_service_health_probe once against a stateful fake DB: the real
    _persist_probe_receipt / previous_output_digest / fingerprint run; only the
    cursor and the receipt UPSERT are faked."""
    out = {"changed": []}

    class Cur:
        def __init__(self):
            self.last = None
        def execute(self, sql, params=None):
            self.last = sql
            if "SET output_digest = NULL" in sql:
                store["digest"] = None
            if "output_changed" in sql:
                out["changed"].append(params[0])
        def fetchone(self):
            if self.last and "SELECT output_digest" in self.last:
                return {"output_digest": store["digest"]} if store["digest"] else None
            return None

    def capture(cur, **k):
        store["digest"] = k["output_digest"]

    patches = [
        patch.object(ar, "emit_event"), patch.object(ar, "mark_asset_error"),
        patch.object(ar, "load_upstream_receipts", return_value=[]),
        patch.object(ar, "compute_upstream_hash", return_value="u"),
        patch.object(ar, "get_writer_source_hash", return_value="c"),
        patch.object(provenance, "capture_and_persist_receipt", side_effect=capture),
        patch("pipeline.orchestrator.service_probes.run_health_probe", return_value=results),
    ]
    if fp_exc:
        patches.append(patch("pipeline.orchestrator.service_probes.probe_output_fingerprint",
                             side_effect=fp_exc))
    for p_ in patches:
        p_.start()
    try:
        ar._run_service_health_probe(MagicMock(), Cur(), "run", "c1", "bg_x", SPEC,
                                     declared_deps=[], natural_key_partition=None, has_cowriters=False)
    finally:
        patch.stopall()
    return out["changed"]


def test_real_path_unchanged_then_changed():
    store = {"digest": None}
    assert _run_stateful(_result(), store) == [True]            # no prior -> propagate
    assert _run_stateful(_result(), store) == [False]           # identical -> no stale
    assert _run_stateful(_result(sha="b" * 64), store) == [True]  # changed -> propagate


def test_green_red_green_flap_propagates():
    store = {"digest": None}
    _run_stateful(_result(), store)
    _run_stateful({"status": "down", "message": "x", "checks": []}, store)
    assert store["digest"] is None                              # invalidated by RED
    assert _run_stateful(_result(), store) == [True]            # recovery must stale dependents


def test_fingerprint_raising_leaves_output_changed_unset():
    store = {"digest": None}
    assert _run_stateful(_result(), store, fp_exc=RuntimeError("boom")) == []
