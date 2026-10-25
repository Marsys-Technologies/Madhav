"""TR_GAPS B4.3 — the trial database carries the L0 P1 seeds + 1401 + 1402 (and 1403 where its table exists), and the TRIAL_READY/1 evaluator is handed the lane and the live
trial database.  One oracle per distinct claim; each fails on its single planted reversion (the reversion is named in each docstring).  §N.8: every effect read-back below is
a detector that can read false.  No test here needs a database except the last, which skips when the lane database is unreachable."""
import os
import subprocess
import sys
from pathlib import Path

import pytest

import trial_slice as ts

HERE = Path(__file__).resolve().parent
VENDOR = HERE / "vendor"


def _files(tmp_path, names):
    for n in names:
        (tmp_path / n).write_text("-- stub\n")
    return tmp_path


ALL = [f for f, _m, _t in ts.OVERLAY_MIGRATIONS]


# ── claim 1: order.  Migration 1401's own guard RAISES unless the 250 rows (9 dignity, 72 friendship) are already there, and 1402's CHECK is applied last ────────────────────

def test_overlay_order_is_250_then_1401_then_1402(tmp_path):
    """Reversion: put 1401 before 250 in OVERLAY_MIGRATIONS (1401.sql: "n_dig <> 9 ... RAISE EXCEPTION")."""
    todo, skipped = ts.plan_overlay(_files(tmp_path, ALL), lambda t: True)
    assert [f.split("_", 1)[0] for f in todo] == ["250", "1401", "1402", "1403", "1410"]       # 1410 (the build ledger) is the highest number and last
    assert skipped == {}


# ── claim 2: a lane without the mandatory files cannot run the merged P1 code ───────────────────────────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("missing", ["250_bg_dignity_reference.sql", "1401_l0_node_dignity_friendship.sql", "1402_gochara_qualification_provenance_certificate.sql"])
def test_missing_mandatory_overlay_file_refuses(tmp_path, missing):
    """Reversion: treat a mandatory file as optional (it would be skipped and the trial DB would raise UndefinedTable inside the build instead of refusing up front)."""
    with pytest.raises(ts.Refused):
        ts.plan_overlay(_files(tmp_path, [f for f in ALL if f != missing]), lambda t: True)


# ── claim 3: 1403 edits the ka_gochara_v5 asset_registry row; the AM5 stub has no asset_registry → skipped BY NAME, never silently, and never a failure ───────────────────────

def test_1403_is_skipped_by_name_when_its_table_is_absent_and_applied_when_present(tmp_path):
    """Reversion: apply 1403 unconditionally (the stub has no asset_registry: its DO block raises 'ka_gochara_v5 row absent' and the whole trial setup dies)."""
    d = _files(tmp_path, ALL)
    todo, skipped = ts.plan_overlay(d, lambda t: False)
    assert "1403_ka_gochara_v5_depends_on_l0_dignity.sql" not in todo
    assert list(skipped) == ["1403_ka_gochara_v5_depends_on_l0_dignity.sql"] and "asset_registry" in skipped["1403_ka_gochara_v5_depends_on_l0_dignity.sql"]
    todo, skipped = ts.plan_overlay(d, lambda t: t == "asset_registry")
    assert "1403_ka_gochara_v5_depends_on_l0_dignity.sql" in todo and skipped == {}


def test_1403_absent_from_the_checkout_is_recorded_not_fatal(tmp_path):
    """1403 reaches the integration head only with the k8edge merge; before that the overlay must still build (reversion: make 1403 mandatory → Refused here)."""
    todo, skipped = ts.plan_overlay(_files(tmp_path, [f for f in ALL if not f.startswith("1403_")]), lambda t: True)
    assert [f.split("_", 1)[0] for f in todo] == ["250", "1401", "1402", "1410"]
    assert skipped == {"1403_ka_gochara_v5_depends_on_l0_dignity.sql": "absent in the checkout"}


# ── claim 4: every overlay file has an effect read-back that can read false (N.8) ───────────────────────────────────────────────────────────────────────────────────────────────

def test_every_overlay_file_has_an_effect_detector():
    """Reversion: drop OVERLAY_EFFECTS['1402'] (setup_lane would KeyError on the first overlay file with no detector — and a missing key must not be a silent pass)."""
    assert {f.split("_", 1)[0] for f in ALL} == set(ts.OVERLAY_EFFECTS)
    assert all(isinstance(sql, str) and sql.lstrip().upper().startswith("SELECT") for sql in ts.OVERLAY_EFFECTS.values())


def test_the_1401_effect_detector_is_the_registry_T10_claim_plus_the_taurus_scorpio_exaltation():
    """BPHS 3.55 translator note (chunk bphs:PG40:C1) five pairs; BPHS ch.47 Rahu MT Gemini / Ketu MT Sagittarius; Rahu exalted Taurus, Ketu Scorpio (1401 guard text)."""
    sql = ts.OVERLAY_EFFECTS["1401"]
    for needle in ("('Rahu','Mercury','neutral')", "('Rahu','Mars','enemy')", "('Rahu','Jupiter','friend')", "('Ketu','Sun','enemy')", "('Ketu','Moon','enemy')",
                   "('Rahu','Gemini')", "('Ketu','Sagittarius')", "('Rahu','Taurus')", "('Ketu','Scorpio')"):
        assert needle in sql


# ── claim 5: the lane database is named, and only a ky_lane_* name can be handed to the evaluator ─────────────────────────────────────────────────────────────────────────────

def test_lane_dsn_default_is_loopback_ky_lane_head_without_credential(monkeypatch):
    monkeypatch.delenv("TRIAL_LANE_DB", raising=False)
    dsn = ts.lane_dsn()
    assert dsn == "postgresql://postgres@127.0.0.1:55433/ky_lane_head"
    assert "@" in dsn and ":" not in dsn.split("@")[0].split("//")[1]            # a user, never a password


@pytest.mark.parametrize("bad", ["ky_trial_a309a4de", "postgres", "ky_b1", "ky_lane_", "ky_lane_x;drop", "KY_LANE_HEAD", "ky_lane_head/../x"])
def test_lane_dsn_refuses_any_other_database(bad):
    """Reversion: drop the LANE_DB_RE check (a typo could point the evaluator at a trial, test or foreign database)."""
    with pytest.raises(ts.Refused):
        ts.lane_dsn(bad)


def test_lane_dsn_reads_the_environment_name(monkeypatch):
    monkeypatch.setenv("TRIAL_LANE_DB", "ky_lane_head2")
    assert ts.lane_dsn().endswith("/ky_lane_head2")


# ── claim 6: the evaluator is handed both DSNs while the trial DB exists, only then, and the caller's environment is restored ───────────────────────────────────────────────

def test_dsns_are_exported_around_the_stage_and_restored(monkeypatch):
    """Reversion: do not restore the environment in `finally` (the variables would leak into the report/EQ stages and into a later run)."""
    monkeypatch.delenv("TRIAL_READY_LANE_DSN", raising=False)
    monkeypatch.delenv("TRIAL_READY_TRIAL_DSN", raising=False)
    monkeypatch.delenv("TRIAL_LANE_DB", raising=False)          # the TR stage exports its own lane DB name; this test asserts the default
    with ts.trial_ready_dsns({"db": "ky_trial_abcd1234"}) as labels:
        assert os.environ["TRIAL_READY_LANE_DSN"].endswith("/ky_lane_head")
        assert os.environ["TRIAL_READY_TRIAL_DSN"] == "postgresql://postgres@127.0.0.1:55433/ky_trial_abcd1234"
        assert labels == {"TRIAL_READY_LANE_DSN": "db:127.0.0.1:55433/ky_lane_head", "TRIAL_READY_TRIAL_DSN": "db:127.0.0.1:55433/ky_trial_abcd1234"}
    assert "TRIAL_READY_LANE_DSN" not in os.environ and "TRIAL_READY_TRIAL_DSN" not in os.environ


@pytest.mark.parametrize("state", [{"db": None}, {"db": "ky_trial_abcd1234", "dropped": True}, {}])
def test_no_trial_dsn_without_a_live_trial_database_and_a_stale_caller_value_is_removed(monkeypatch, state):
    """Reversion: export the trial DSN from state['db'] even when dropped / absent, or keep the caller's value (a stale DSN would stand in for the live trial DB)."""
    monkeypatch.setenv("TRIAL_READY_TRIAL_DSN", "postgresql://postgres@127.0.0.1:55433/ky_trial_stale0000")
    with ts.trial_ready_dsns(state) as labels:
        assert "TRIAL_READY_TRIAL_DSN" not in os.environ and "TRIAL_READY_TRIAL_DSN" not in labels
        assert "TRIAL_READY_LANE_DSN" in os.environ
    assert os.environ["TRIAL_READY_TRIAL_DSN"].endswith("ky_trial_stale0000")      # restored for the caller


def test_the_exported_dsns_are_accepted_by_the_merged_evaluators_loopback_check(monkeypatch):
    """Cross-check against the vendored merged evaluator: `_loopback_dsn` returns a DSN (not None) for both names; reversion: a non-loopback host in dsn_for → 'refuses a non-loopback database'."""
    sys.path.insert(0, str(VENDOR))
    try:
        import trial_ready as tr
    finally:
        sys.path.remove(str(VENDOR))
    with ts.trial_ready_dsns({"db": "ky_trial_abcd1234"}):
        for name in ("TRIAL_READY_LANE_DSN", "TRIAL_READY_TRIAL_DSN"):
            dsn, label, why = tr._loopback_dsn({"dsn_env": name})
            assert dsn is not None and why == "ok", (name, label, why)


# ── claim 7 (live, skipped without the cluster): the named lane database reads true for the registry's T10 lane part and has the 250/1401/1402 effects ──────────────────────────

def _lane_reachable():
    try:
        import psycopg
        with psycopg.connect(ts.lane_dsn(), connect_timeout=2):
            return True
    except Exception:           # noqa: BLE001
        return False


@pytest.mark.skipif(not _lane_reachable(), reason="the named lane database is not reachable on 127.0.0.1:55433")
def test_lane_database_has_the_250_1401_1402_effects_and_c_collation():
    """The effect SQL is the SAME text the trial setup uses; a lane built without 250/1401/1402 reads false here (the F2 stale-ky_b1 case: 0 rows)."""
    import psycopg
    with psycopg.connect(ts.lane_dsn(), connect_timeout=2, options="-c default_transaction_read_only=on") as conn:
        for num in ("250", "1401", "1402"):
            assert conn.execute(ts.OVERLAY_EFFECTS[num]).fetchone()[0] is True, num
        assert conn.execute("SELECT datcollate = 'C' AND datctype = 'C' FROM pg_database WHERE datname = current_database()").fetchone()[0] is True
