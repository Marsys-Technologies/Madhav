"""SR-OD1 R8 (RECONCILIATION R-8; ruling SR-R8-SHARDED) — class-sharded verification and the generation-wide AGGREGATE the brief and the seal read.

One whole-generation verification of the 26 classes cannot fit the job's 28,800 s task timeout, so a launch verifies ONE SHARD (`--class` repeated) and persists, per grain, a
PASSED attestation whose 1240 row carries the shard stamp (generation, head, image digest, execution, classes). `numerical_window_gate.generation_verdict(classes=None)` is the
AGGREGATE: the seal brief (`seal_brief._numerical_gate_entry`) and the sealing job (`require_passed`) read only it, and it checks COVERAGE, not presence.

Claims — each has ONE oracle here and the single planted reversion that must make it fail (the reversion is applied to a copy under the job folder; see result.json):
  A1 a class with NO attestation (every row of it gone) is refused by the aggregate, naming the grain                         — revert: no "no window verification row" problem
  A2 a pinned scored class with no search-path pin at all is refused (coverage is judged against the manifest's pinned list)  — revert: drop the pinned-vs-pinned-rows comparison
  A3 two shards that attested at different heads are refused, naming both heads (R10-2: a run before a rebuild is void)       — revert: drop the single-head comparison
  A4 a row written by code other than the code the manifest pins is refused (a shard run before a rebuild changed the code)   — revert: drop the implementation-digest comparison
  A5 a row with no shard stamp is refused; a stamp of another generation is refused                                            — revert: skip the stamp check
  A6 shards on different images are refused                                                                                    — revert: drop the single-image comparison
  A7 a real shard run persists a stamp with generation / head / image digest / execution / classes, and the aggregate reads it — revert: do not stamp (run passes no shard)
  A8 the seal brief and the seal read the aggregate: a tampered stamp stops both                                               — revert: read the subset verdict in the brief entry
  A10 a row attested before a rebuild (another build epoch) is void                                                            — revert: drop the epoch comparison
  A11 a pinned class whose inventory is missing or not independently re-derived is refused (expected grains come from the inventories) — revert: drop the inventory comparison
  A12 a shard that names no immutable image digest / execution is refused (every attestation is bound to image and head)          — revert: drop the image check
  A13 the generation-wide near-miss pass runs once per epoch: a later shard reuses it, a changed near-miss state runs it again     — revert: always run it
  A9 a persisting launch that cannot name its image and execution refuses before it writes anything                            — revert: drop the producer check in the entry point
Doctrine (SR-A10-1 B3 extensions: A10-A13): root CLAUDE.md §N.8 (a green is computed by a detector that can read false), §N.7.6 (honest null: an unnamed image is None and is reported, never invented), the owner
ruling R10-2 (every class is re-verified after the last build; a run before a rebuild is void) and SR-R8-SHARDED (a)-(e).
"""
from __future__ import annotations

import json

import pytest

from pipeline.orchestrator import verification_job as entry
from services.gochara_kernel import numerical_window_gate as nwg
from services.gochara_kernel import seal_brief as sb
from services.gochara_kernel import verification_job as vj

from .test_a53_inventory import CHART_ID
from .test_a53_p1_support import GEN
from .test_a53_r10_complete_records import CLS, _bypass, _run, built, login, rworld  # noqa: F401
from .test_a53_r11_seal_brief import _brief_as_verifier, _verified  # noqa: F401
from .test_a53_r12_seal_job import built_numbers  # noqa: F401
from .test_a53_verification_job import PASSWORD

# G8: the one-class world's manifest pins all 26 classes, so the JOB's own census refusal is set aside BY NAME (conftest.g8_job_census_only, closed list + this reason) — but, unlike the older
# job-mechanics suites (the full opt-out), the AGGREGATE's coverage is NOT: each test narrows the pinned universe itself after the run (`_pin_universe`), and A2 shows that a pinned
# class with nothing built refuses.
G8_JOB_CENSUS_ONLY_REASON = "the aggregate's own coverage check is under test on a deliberate one-class marriage world, so only the job's census refusal is set aside"
pytestmark = pytest.mark.usefixtures("g8_job_census_only")


def _pin_universe(w, classes=(CLS,)):
    _bypass(w, ("UPDATE public.kala_gochara_publication SET input_generation_vector = jsonb_set(input_generation_vector, '{scored_classes}', %s::jsonb)", (json.dumps(list(classes)),)))


IMAGE = "sha256:" + "1" * 64
EXECUTION = "projects/p/locations/l/jobs/gochara-verification-job/executions/e1"


def _stamps(w):
    return [r[0] if isinstance(r[0], dict) else json.loads(r[0]) for r in w.conn.execute(
        "SELECT runner_identity FROM public.ka_gochara_eval_window_verification ORDER BY path_id").fetchall()]


def _verified_shard(w, monkeypatch):
    monkeypatch.setenv("GOCHARA_RUNNER_IMAGE_DIGEST", IMAGE)
    monkeypatch.setenv("CLOUD_RUN_EXECUTION", EXECUTION)
    report = _run(w)                                                    # classes=["marriage"]: a SHARD run of the one-class world
    assert report["status"] == "VERIFIED", report["classes"]
    _pin_universe(w)
    return report


def _patch_rows(w, expr):
    """Rewrite every 1240 row's runner_identity with a SQL jsonb expression over `runner_identity` (a trigger-bypassing tamper, like the other suites)."""
    _bypass(w, (f"UPDATE public.ka_gochara_eval_window_verification SET runner_identity = {expr}", ()))


def test_a7_a_shard_run_stamps_every_row_and_the_aggregate_reads_the_stamps(built_numbers, monkeypatch):
    w = built_numbers
    report = _verified_shard(w, monkeypatch)
    rows = _stamps(w)
    head, epoch = rows[0]["commit"], nwg.current_epoch(w.conn, CHART_ID, GEN)
    assert len(epoch) == 64
    assert len(rows) == 4 and all(r[nwg.SHARD_KEY] == {"generation": GEN, "epoch": epoch, "head": head, "image_digest": IMAGE, "execution_id": EXECUTION, "classes": [CLS]} for r in rows), rows
    assert report["shard"] == rows[0][nwg.SHARD_KEY]
    verdict = nwg.generation_verdict(w.conn, CHART_ID, GEN)
    assert verdict["status"] == "PASSED", verdict["problems"]
    assert verdict["aggregate"] == {"head": head, "image_digest": IMAGE, "epoch": epoch, "classes_attested": [CLS],
                                    "executions": [{"execution_id": EXECUTION, "head": head, "image_digest": IMAGE, "classes": [CLS]}]}      # the execution history the aggregate reads
    # the shard's own report says what the aggregate reads NOW: this world's manifest pins all 26 classes and one shard attested one of them (pins + inventories missing for the other 25)
    assert report["aggregate"]["status"] == "FAILED" and report["aggregate"]["classes_attested"] == [CLS] and report["aggregate"]["problem_count"] == 50
    assert all(not p.startswith(f"{CLS}:") for p in report["aggregate"]["problems"])


def test_a1_a_class_with_no_attestation_is_refused_by_the_aggregate(built_numbers, monkeypatch):
    w = built_numbers
    _verified_shard(w, monkeypatch)
    _bypass(w, ("DELETE FROM public.ka_gochara_eval_window_verification WHERE path_id = 'P3'", ()))
    verdict = nwg.generation_verdict(w.conn, CHART_ID, GEN)
    assert verdict["status"] == "FAILED" and any(f"{CLS}/P3" in p and "no window verification row" in p for p in verdict["problems"]), verdict["problems"]
    with pytest.raises(nwg.NumericalGateNotPassed):                         # the sealing job's own read
        nwg.require_passed(w.conn, CHART_ID, GEN)


def test_a2_a_pinned_class_with_no_search_path_pin_is_refused(built_numbers, monkeypatch):
    w = built_numbers
    _verified_shard(w, monkeypatch)
    _pin_universe(w, (CLS, "ghost_class"))
    verdict = nwg.generation_verdict(w.conn, CHART_ID, GEN)
    assert verdict["status"] == "FAILED" and any(p.startswith("ghost_class:") and "no search-path pin" in p for p in verdict["problems"]), verdict["problems"]


def test_a3_two_shards_at_different_heads_are_refused_naming_both(built_numbers, monkeypatch):
    w = built_numbers
    _verified_shard(w, monkeypatch)
    head = _stamps(w)[0]["commit"]
    other = "f" * 40
    _bypass(w, ("UPDATE public.ka_gochara_eval_window_verification SET runner_identity = jsonb_set(jsonb_set(runner_identity, '{commit}', to_jsonb(%s::text)),"
                " '{verification_shard,head}', to_jsonb(%s::text)) WHERE path_id = 'P4'", (other, other)))
    verdict = nwg.generation_verdict(w.conn, CHART_ID, GEN)
    msg = [p for p in verdict["problems"] if "different heads" in p]
    assert verdict["status"] == "FAILED" and msg and head in msg[0] and other in msg[0], verdict["problems"]
    assert verdict["aggregate"]["head"] is None                              # there is no single head to report
    assert nwg.generation_verdict(w.conn, CHART_ID, GEN, head=head)["status"] == "FAILED"


def test_a4_a_row_written_by_other_code_than_the_manifest_pins_is_void(built_numbers, monkeypatch):
    w = built_numbers
    _verified_shard(w, monkeypatch)
    _patch_rows(w, "jsonb_set(runner_identity, '{implementation_digest}', to_jsonb(repeat('0', 64)))")
    verdict = nwg.generation_verdict(w.conn, CHART_ID, GEN)
    assert verdict["status"] == "FAILED" and any("other than the code the manifest pins" in p for p in verdict["problems"]), verdict["problems"]


@pytest.mark.parametrize("expr,needle", [
    ("runner_identity - 'verification_shard'", "carries no shard stamp"),
    ("jsonb_set(runner_identity, '{verification_shard,generation}', '\"4.1\"')", "attested generation"),
])
def test_a5_a_row_without_a_shard_stamp_or_for_another_generation_is_refused(built_numbers, monkeypatch, expr, needle):
    w = built_numbers
    _verified_shard(w, monkeypatch)
    _patch_rows(w, expr)
    verdict = nwg.generation_verdict(w.conn, CHART_ID, GEN)
    assert verdict["status"] == "FAILED" and any(needle in p for p in verdict["problems"]), verdict["problems"]


def test_a6_shards_on_different_images_are_refused(built_numbers, monkeypatch):
    w = built_numbers
    _verified_shard(w, monkeypatch)
    _bypass(w, ("UPDATE public.ka_gochara_eval_window_verification SET runner_identity = jsonb_set(runner_identity, '{verification_shard,image_digest}',"
                " to_jsonb(%s::text)) WHERE path_id = 'P4'", ("sha256:" + "2" * 64,)))
    verdict = nwg.generation_verdict(w.conn, CHART_ID, GEN)
    assert verdict["status"] == "FAILED" and any("different images" in p for p in verdict["problems"]), verdict["problems"]


def test_a8_the_brief_and_the_seal_read_the_aggregate_not_a_shards_own_verdict(built_numbers, monkeypatch):
    w = built_numbers
    _verified_shard(w, monkeypatch)
    _patch_rows(w, "runner_identity - 'verification_shard'")                  # every grain keeps its PASSED attestation: only the aggregate sees the missing stamps
    assert nwg.generation_verdict(w.conn, CHART_ID, GEN, classes=[CLS])["status"] == "PASSED"      # a shard's own (subset) verdict is blind to it
    with pytest.raises(sb.BriefRefused) as exc:
        _brief_as_verifier(w, sealing_commit="c" * 40)
    assert exc.value.code == "candidate_not_approvable" and any("shard stamp" in v for v in exc.value.violations), exc.value.violations
    with pytest.raises(nwg.NumericalGateNotPassed) as seal:
        nwg.require_passed(w.conn, CHART_ID, GEN)
    assert any("shard stamp" in p for p in seal.value.problems)


def test_a9_a_persisting_launch_that_cannot_name_its_image_and_execution_refuses_before_writing(built_numbers, monkeypatch, capsys):
    w = built_numbers
    monkeypatch.delenv("GOCHARA_RUNNER_IMAGE_DIGEST", raising=False)
    monkeypatch.delenv("CLOUD_RUN_EXECUTION", raising=False)
    w.conn.execute(f"ALTER ROLE gochara_verifier LOGIN PASSWORD '{PASSWORD}'")
    try:
        from psycopg.conninfo import make_conninfo
        monkeypatch.setenv(entry.ENV_URL, make_conninfo(w.dsn, user="gochara_verifier", password=PASSWORD))
        assert entry.main(["--chart", CHART_ID, "--class", CLS]) == vj.EXIT_REFUSED
        out = json.loads(capsys.readouterr().out)
        assert out["code"] == "producer_identity_absent" and "GOCHARA_RUNNER_IMAGE_DIGEST" in out["detail"], out
        assert w.conn.execute("SELECT count(*) FROM public.ka_gochara_eval_window_verification").fetchone()[0] == 0
    finally:
        w.conn.execute("ALTER ROLE gochara_verifier NOLOGIN PASSWORD NULL")


def test_a10_a_row_attested_before_a_rebuild_is_void(built_numbers, monkeypatch):
    w = built_numbers
    _verified_shard(w, monkeypatch)
    _bypass(w, ("UPDATE public.ka_gochara_search_input_snapshot SET input_digest = repeat('9', 64)", ()))      # the build's input identity changed: another epoch
    verdict = nwg.generation_verdict(w.conn, CHART_ID, GEN)
    assert verdict["status"] == "FAILED" and any("build epoch" in p for p in verdict["problems"]), verdict["problems"]


def test_a11_a_pinned_class_without_a_re_derived_inventory_is_refused(built_numbers, monkeypatch):
    w = built_numbers
    _verified_shard(w, monkeypatch)
    _bypass(w, ("DELETE FROM public.ka_gochara_search_inventory_verification", ()))
    verdict = nwg.generation_verdict(w.conn, CHART_ID, GEN)
    assert verdict["status"] == "FAILED" and any(p.startswith(f"{CLS}:") and "independent re-derivation" in p for p in verdict["problems"]), verdict["problems"]


def test_a12_a_shard_that_names_no_image_or_execution_is_refused(built_numbers, monkeypatch):
    w = built_numbers
    monkeypatch.delenv("GOCHARA_RUNNER_IMAGE_DIGEST", raising=False)
    monkeypatch.delenv("CLOUD_RUN_EXECUTION", raising=False)
    assert _run(w)["status"] == "VERIFIED"                                   # the library run stamps what it can name: image and execution are None, not invented
    _pin_universe(w)
    assert all(r[nwg.SHARD_KEY]["image_digest"] is None and r[nwg.SHARD_KEY]["execution_id"] is None for r in _stamps(w))
    verdict = nwg.generation_verdict(w.conn, CHART_ID, GEN)
    assert verdict["status"] == "FAILED" and any("no immutable image digest" in p for p in verdict["problems"]) and any("names no execution" in p for p in verdict["problems"]), verdict["problems"]


class _FakeConn:
    """Answers the three reads of `near_miss_verified_for_state` from a dict: table present?, the stored verification digest, the digest of the stored state now."""

    def __init__(self, table=True, stored=None, now="a" * 64):
        self.table, self.stored, self.now = table, stored, now

    def execute(self, sql, params=()):
        rows = {"to_regclass": [(self.table,)], "SELECT near_miss_digest": [] if self.stored is None else [(self.stored,)], "ka_gochara_near_miss_digest": [(self.now,)]}
        key = next(k for k in rows if k in sql)
        rows_ = rows[key]
        return type("R", (), {"fetchone": lambda _s: rows_[0] if rows_ else None})()


def test_a13_a_persisted_near_miss_verification_is_reused_only_while_it_matches_the_stored_state():
    reuse = vj.near_miss_verified_for_state
    assert reuse(_FakeConn(stored="a" * 64), CHART_ID, GEN) == "a" * 64                  # the first shard's result, still the digest of the stored state
    assert reuse(_FakeConn(stored="b" * 64), CHART_ID, GEN) is None                      # the state changed (a rebuild): verify again
    assert reuse(_FakeConn(stored=None), CHART_ID, GEN) is None                          # nothing persisted yet: the first shard runs the pass
    assert reuse(_FakeConn(table=False), CHART_ID, GEN) is None                          # no near-miss layer in the database


def test_a13_the_second_shard_of_an_epoch_does_not_run_the_near_miss_pass_again(built_numbers, monkeypatch):
    from services.gochara_kernel import near_miss_verifier as nmv
    w = built_numbers
    monkeypatch.setenv("GOCHARA_RUNNER_IMAGE_DIGEST", IMAGE)
    monkeypatch.setenv("CLOUD_RUN_EXECUTION", EXECUTION)
    calls = []

    def fake(conn, *, chart_id, generation, ephe_path, persist=False):
        calls.append(persist)
        return {"status": "VERIFIED", "digest": "c" * 64, "objects": 0, "persisted": persist}
    monkeypatch.setattr(nmv, "verify_generation", fake)
    first = _run(w)                                                                      # no persisted verification yet: this shard runs the pass
    monkeypatch.setattr(vj, "near_miss_verified_for_state", lambda conn, chart_id, generation: "c" * 64)    # …and persisted it: the next shard of the epoch finds it
    second = _run(w)
    assert calls == [True] and "reused" not in first["near_miss"] and second["near_miss"] == {"status": "VERIFIED", "digest": "c" * 64, "persisted": True, "reused": True}
