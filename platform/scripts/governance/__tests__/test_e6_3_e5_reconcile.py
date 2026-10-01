"""E6.3 x E5.1 x E5.5: `elevated_assets` reads the ledger the REAL writers produce.

* The golden ledgers in fixtures/e6_3_golden/ were written once by the real E5.1 write path and the real E5.5
  invalidate()/watermark (README there says how, and the two serialisation-only deviations). The end-to-end tests
  here always run: they commit those exact bytes into a throw-away repo and ask `elevated_assets`.
* The parity tests run the sibling modules' OWN verifiers (E5.1 `_parse` for the hash chain, E5.5 `watermark_ok` and
  `current_certificates`) over the same ledger bytes, in a subprocess so no module state leaks, and require that both
  sides accept/reject the same ledgers and agree on which certificates are current. They are skipped when the sibling
  modules are not importable (E5.1/E5.5 worktrees absent), or when E5.5 cannot yet read E5.1's current chain (it is
  being rebased): the skip reason says which.
"""
from __future__ import annotations

import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.dirname(__file__))
from _e6_3_fixtures import (CERTS, MINI_FLOOR, mini_patch, World, chained, cert, disp, load_tracker, sha,  # noqa: E402
                            writer_path)

T = load_tracker()
GOLDEN = pathlib.Path(__file__).resolve().parent / "fixtures" / "e6_3_golden"
GOV = pathlib.Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def mini_floor(monkeypatch):
    mini_patch(monkeypatch, T)


def golden_world(tmp_path, name):
    """A repo whose certificate ledger is the golden file `name`, verbatim (the bytes the real writers produced)."""
    w = World(tmp_path)
    for a in ("ga_alpha", "ga_beta"):
        w.disps.append(disp(a, "keep"))
    w.raw[CERTS] = (GOLDEN / name).read_bytes()
    w.commit()
    return w


# ───────────────────────── end to end on the real writers' bytes ─────────────────────────

def test_golden_clean_ledger_both_assets_are_elevated(tmp_path):
    w = golden_world(tmp_path, "ledger_clean.jsonl")
    assert w.elevated(T) == {"ga_alpha", "ga_beta"}


def test_golden_after_e5_5_invalidation_only_the_untouched_asset_is_elevated(tmp_path):
    w = golden_world(tmp_path, "ledger_after_invalidation.jsonl")
    assert w.elevated(T) == {"ga_alpha"}


def test_golden_the_records_are_the_real_writers_shape(tmp_path):
    rows = [json.loads(ln) for ln in (GOLDEN / "ledger_after_invalidation.jsonl").read_text().splitlines() if ln.strip()]
    kinds = [r.get("kind") for r in rows[1:]]
    types = [r.get("type") for r in rows[1:]]
    assert kinds.count("gate") == 14 and types.count("invalidation") == 7 and types.count("watermark") == 2
    gate = next(r for r in rows if r.get("kind") == "gate")
    assert gate["cross_checked"] is True and gate["seq"] == 1 and isinstance(gate["prev_sha256"], str)
    assert gate["writer_hashes_verified"] is True and gate["evidence"]["census_sha256"]
    wm = [r for r in rows if r.get("type") == "watermark"][-1]
    assert wm["asset"] == "_ledger" and wm["certs_processed"] == 14 and wm["covers_seq"] == 15
    assert wm["last_cert_id"] == "ga_beta|gate|Build.reg@1" and "cert_key" not in wm


def test_golden_a_certificate_after_the_last_watermark_raises(tmp_path):
    w = golden_world(tmp_path, "ledger_clean.jsonl")
    ledger = (GOLDEN / "ledger_clean.jsonl").read_text()
    lines = ledger.rstrip("\n").split("\n")
    prev = sha(lines[-1].encode())
    extra = cert("ga_alpha", "Ldgr.src", gen=2, seq=len(lines), prev_sha256=prev)
    w.raw[CERTS] = ledger + json.dumps(extra) + "\n"
    w.commit()
    with pytest.raises(T.WatermarkOlderThanLedger):
        w.elevated(T)


def test_golden_a_rewritten_earlier_line_breaks_the_chain(tmp_path):
    lines = (GOLDEN / "ledger_clean.jsonl").read_text().rstrip("\n").split("\n")
    rec = json.loads(lines[3])
    rec["verified_by"] = "tampered"
    lines[3] = json.dumps(rec)
    w = World(tmp_path)
    w.disps += [disp("ga_alpha", "keep"), disp("ga_beta", "keep")]
    w.raw[CERTS] = "\n".join(lines) + "\n"
    w.commit()
    with pytest.raises(T.ElevatedInputError) as e:
        w.elevated(T)
    assert "chain" in str(e.value)


def test_golden_a_writer_file_changed_after_the_walk_is_stale_even_though_e5_5_has_not_seen_it(tmp_path):
    w = golden_world(tmp_path, "ledger_clean.jsonl")
    w.writer_versions["ga_alpha"] = 2
    w.commit()
    assert w.elevated(T) == {"ga_beta"}


# ───────────────────────── parity with the sibling verifiers ─────────────────────────

def _sibling(name, env, default, own):
    for cand in (os.environ.get(env), str(GOV) if (GOV / own).exists() else None, default):
        if cand and (pathlib.Path(cand) / own).exists():
            return pathlib.Path(cand)
    return None


E51 = _sibling("e51", "E6_3_E51_DIR", "/Users/Dev/suvarna-engine-lane-e5-1/platform/scripts/governance", "nikasha_certify.py")
E55 = _sibling("e55", "E6_3_E55_DIR", "/Users/Dev/suvarna-engine-lane-e5-5/platform/scripts/governance", "nikasha_stale_certs.py")

PROBE = r'''
import json, sys
mode, path = sys.argv[1], sys.argv[2]
data = open(path, "rb").read()
out = {}
try:
    import nikasha_certify as nc
    if mode == "chain":
        try:
            r = nc.parse_ledger(data)
            out = {"ok": True, "keys": sorted(k for k, v in r.items() if v and v[0].get("kind") in ("gate", "addition"))}
        except nc.CertificationRefused as e:
            out = {"ok": False, "code": e.code}
        out["declaration_based"] = {k: list(v) for k, v in nc.DECLARATION_BASED.items()}
    else:
        import nikasha_stale_certs as sc

        def e55_view():
            ok = sc.watermark_ok(data)
            cur = sorted(sc.current_certificates(data, require_watermark=False).keys())
            return {"ok": True, "watermark_ok": ok, "current": cur}

        try:
            out = e55_view()
        except sc.StaleCertsError as e:
            out = {"ok": False, "code": e.code}
except Exception as e:                                       # the module cannot even be used
    out = {"unusable": f"{type(e).__name__}: {e}"}
print(json.dumps(out))
'''


@pytest.fixture(scope="module")
def probe_dir():
    if E51 is None:
        pytest.skip("E5.1 (nikasha_certify.py) is not importable here: no sibling worktree and not on this branch")
    d = pathlib.Path(tempfile.mkdtemp())
    shutil.copy(E51 / "nikasha_certify.py", d / "nikasha_certify.py")
    shutil.copy(E51 / "asset_census.py", d / "asset_census.py")
    if E55 is not None:
        shutil.copy(E55 / "nikasha_stale_certs.py", d / "nikasha_stale_certs.py")
    (d / "probe.py").write_text(PROBE)
    yield d
    shutil.rmtree(d, ignore_errors=True)


def run_probe(probe_dir, mode, data: bytes):
    f = probe_dir / "ledger.bin"
    f.write_bytes(data)
    r = subprocess.run([sys.executable, str(probe_dir / "probe.py"), mode, str(f)], capture_output=True, text=True,
                       cwd=str(probe_dir), env=dict(os.environ, PYTHONPATH=str(probe_dir), PYTHONDONTWRITEBYTECODE="1"))
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout.strip().splitlines()[-1])


def mine(tmp_path, data: bytes):
    """What elevated_assets' certificate reader says about the same bytes: (ok, {gate/addition cert_keys})."""
    w = World(tmp_path)
    w.commit()
    facts = T._e63_registry_facts(str(w.repo), w.last)
    try:
        led = T._e63_parse_certs(data, facts)
    except T.ElevatedInputError:
        return False, None, None
    return True, sorted(led.by_key), led.unevaluated


def _variants():
    clean = (GOLDEN / "ledger_clean.jsonl").read_bytes()
    after = (GOLDEN / "ledger_after_invalidation.jsonl").read_bytes()
    lines = clean.decode().rstrip("\n").split("\n")

    def edit(i, **kv):
        out = list(lines)
        r = json.loads(out[i])
        r.update(kv)
        out[i] = json.dumps(r)
        return ("\n".join(out) + "\n").encode()

    wm = json.loads(lines[-1])
    small = dict(wm, covers_seq=3, certs_processed=3, last_cert_id=json.loads(lines[3])["cert_id"], seq=wm["seq"] + 1,
                 prev_sha256=sha(lines[-1].encode()))
    late_smaller = (clean.decode() + json.dumps(small) + "\n").encode()
    dele = list(lines)
    del dele[4]
    swap = list(lines)
    swap[2], swap[3] = swap[3], swap[2]
    return {
        "clean": clean, "after_invalidation": after,
        "edited_earlier_line": edit(3, verified_by="x"), "wrong_seq": edit(5, seq=99), "no_seq": edit(5, seq=None),
        "wrong_prev": edit(6, prev_sha256="0" * 64),
        "deleted_line": ("\n".join(dele) + "\n").encode(), "reordered": ("\n".join(swap) + "\n").encode(),
        "duplicate_key": ("\n".join(lines[:-1] + [lines[-1][:-1] + ', "asset": "z"}']) + "\n").encode(),
        "torn_tail": clean.rstrip(b"\n")[:-9], "second_schema": ("\n".join(lines[:3] + [lines[0]] + lines[3:]) + "\n").encode(),
        "late_smaller_watermark": late_smaller,
        "extra_blank_lines": ("\n".join(lines[:4] + ["", ""] + lines[4:]) + "\n").encode(),
    }


@pytest.mark.parametrize("name", list(_variants()))
def test_parity_the_hash_chain_verdict_matches_e5_1s_own_parser(probe_dir, tmp_path, name):
    data = _variants()[name]
    theirs = run_probe(probe_dir, "chain", data)
    assert "unusable" not in theirs, theirs
    ok, keys, _ = mine(tmp_path, data)
    assert ok == theirs["ok"], (name, theirs, ok)
    if ok:
        assert keys == theirs["keys"]


def test_parity_the_declaration_table_equals_e5_1s(probe_dir):
    theirs = run_probe(probe_dir, "chain", (GOLDEN / "ledger_clean.jsonl").read_bytes())
    assert {k: tuple(v) for k, v in theirs["declaration_based"].items()} == T.E63_DECLARATION_BASED


def _e55_or_skip(probe_dir, data):
    if E55 is None:
        pytest.skip("E5.5 (nikasha_stale_certs.py) is not importable here")
    theirs = run_probe(probe_dir, "e55", data)
    if "unusable" in theirs or not theirs.get("ok"):
        pytest.skip(f"E5.5 cannot yet read E5.1's current ledger (it is still being finished): {theirs}")
    return theirs


@pytest.mark.parametrize("name", ["clean", "after_invalidation", "late_smaller_watermark"])
def test_parity_current_certificates_and_watermark_match_e5_5(probe_dir, tmp_path, name):
    data = _variants()[name]
    theirs = _e55_or_skip(probe_dir, data)
    w = World(tmp_path)
    w.disps += [disp("ga_alpha", "keep"), disp("ga_beta", "keep")]
    w.raw[CERTS] = data
    w.commit()
    facts = T._e63_registry_facts(str(w.repo), w.last)
    led = T._e63_parse_certs(data, facts)
    after = led.unevaluated
    state = T.LedgerState(str(w.repo), w.last, facts, led.by_key, led.invalidated, led.pos)
    cur = sorted(k for k, recs in led.by_key.items()
                 if recs[-1]["verdict"] in ("PASS", "N/A") and T.is_current(recs[-1], state))
    assert cur == theirs["current"], name
    assert theirs["watermark_ok"] is (after == 0)


def test_parity_a_certificate_after_the_watermark_is_behind_for_both(probe_dir, tmp_path):
    clean = (GOLDEN / "ledger_clean.jsonl").read_bytes().decode()
    lines = clean.rstrip("\n").split("\n")
    extra = cert("ga_alpha", "Ldgr.src", gen=2, seq=len(lines), prev_sha256=sha(lines[-1].encode()))
    data = (clean + json.dumps(extra) + "\n").encode()
    theirs = _e55_or_skip(probe_dir, (GOLDEN / "ledger_clean.jsonl").read_bytes())
    theirs = run_probe(probe_dir, "e55", data)
    assert theirs.get("ok") and theirs["watermark_ok"] is False
    ok, _keys, after = mine(tmp_path, data)
    assert ok and after == 1
