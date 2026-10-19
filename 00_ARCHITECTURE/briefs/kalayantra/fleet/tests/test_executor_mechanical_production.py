"""OWNER-MINIMAL-PROTECTION-NOW-20261018 (SR-MINIMAL-PROTECTION §2): a production WRITE is accepted MECHANICALLY by the executor, without a V1 signer, when
  (1) its bytes equal a verified pack fill, (2) its kind's dry run COMPLETED OK for the same request identity (read from the executor's own receipts),
  (3) the lease is live. Deletions (every *_teardown) and serving changes (publish_head, layer_publish, rollback_head, layer_rollback) — and
  measuring_cancel, held with them (I) — keep requiring the V1 signer exactly as before. The record is acceptance/<op>.json, by executor-mechanical.

One doctrine-grounded oracle per distinct production claim (owner decision D-OWNER-TESTS-20261016; root CLAUDE.md §N.8 — a signal is computed by a detector
that can read false; §B.10 — nothing here invents a value). Each oracle passes on the real executor and FAILS on a copy of executor.py with that ONE claim's
line reverted (the planted reversion). The real validate / mechanical_pre_acceptance run against a temporary KY_ROOT and a temporary git origin
(test_executor_table.World); nothing here touches a credential, a database or the running executor.

  X1 a deletion (*_teardown) is never mechanical            X2 a serving change / measuring_cancel is never mechanical     X3 the table classifies every production kind
  A1 a fill + passed dry run + live lease is admitted and recorded (by executor-mechanical, request + evidence digests)
  A2 backup_snapshot (no dry-run kind exists) is admitted on pack fill + lease alone
  P1 a manifest not on the verified-pack allow-list is refused (and so is a missing list)   P2 an allow-list entry that is not ACCEPTED is refused
  P3 a template the verified pack does not list for this kind is refused (the request cannot bring its own)   P4 a template that fills kind / chart_id / reviewed_commit / requested_by is refused
  P5 a request whose fixed field differs from the template is refused    P6 a request carrying a field the template does not define is refused
  P7 a fill whose digest the executor cannot re-derive is refused
  D1 a failed dry run is refused (a missing citation too)   D2 a dry run for a different request identity is refused   D3 a receipt that differs from its
  cited sha256 is refused   D4 a receipt not bound to its archived request is refused   D5 a dry-run output that differs from the receipt's digest is refused
  L1 a dead lease is refused (validate, and mechanical_pre_acceptance on its own)
  B1 a signer-accepted request is judged by its signer whatever else it carries (back-compat)   R1 a record that does not bind this request is never reused
"""
import datetime as dt
import hashlib
import json
from pathlib import Path

import pytest

import test_executor_table as TT
from test_executor_table import ALL_CAPS, CANONICAL_CHART, OPS_FILE, World

EXECUTOR_SRC = TT.EXECUTOR_PY            # the real file; a planted reversion is a copy of it
MANIFEST = hashlib.sha256(b"pack-manifest-fixture").hexdigest()
OTHER_MANIFEST = hashlib.sha256(b"another-pack-manifest").hexdigest()
KIND = "scheduler_resume"               # a non-exempt production kind with a dry-run kind whose admission needs no reviewed-source policy
SERVING = ("publish_head", "layer_publish", "rollback_head", "layer_rollback")


def sha(data):
    return hashlib.sha256(data if isinstance(data, bytes) else data.encode()).hexdigest()


def csha(value):
    return sha(json.dumps(value, sort_keys=True, separators=(",", ":")))


def iso(**delta):
    return (dt.datetime.now(dt.timezone.utc) + dt.timedelta(**delta)).isoformat(timespec="seconds")


def build(tmp_path, monkeypatch, mutation=None):
    if mutation:
        old, new = mutation
        text = EXECUTOR_SRC.read_text()
        if text.count(old) != 1:
            raise RuntimeError(f"mutation anchor not unique: {old!r}")      # a bad anchor must never read as a failed oracle
        mutated = tmp_path / "executor_mutated.py"
        mutated.write_text(text.replace(old, new))
        monkeypatch.setattr(TT, "EXECUTOR_PY", mutated)
    w = World(tmp_path, monkeypatch, OPS_FILE.read_text())
    for d in (w.mod.REC, w.mod.DONE, w.mod.ACC):
        d.mkdir(parents=True, exist_ok=True)
    return w, w.table()


def template_for(w, kind, dry=True):
    return {"kind": kind,
            "fixed": {"kind": kind, "item_id": "J-3c", "requested_by": "adhikarin", "kyd": "KYD-1", "args": {}, "chart_id": CANONICAL_CHART, "reviewed_commit": w.reviewed},
            "fill": ["operation_id", "idempotency_key", "lease_id"] + (["dryrun_receipt"] if dry else [])}


def publish(w, templates, manifest=MANIFEST, verdict="ACCEPTED", verify_job="verify-1"):
    """What the cockpit writes from an ACCEPTED verify job: the pack manifest digest and the digest of every template the manifest covers."""
    entry = {"pack_manifest_sha256": manifest, "verify_job": verify_job, "verdict": verdict, "accepted_at": iso(),
             "templates": {csha(t): t["kind"] for t in templates}}
    w.mod.PACK_ALLOWLIST.write_text(json.dumps({"schema": "ky.pack_allowlist/1", "packs": [entry]}))


def dry_run(w, kind, oid="dry-1", status="COMPLETED", exit_code=0, args=None):
    """A `<kind>_dryrun` request archived in done/, its output and the receipt the executor would have written (same digests)."""
    dreq = {"operation_id": oid, "kind": kind + "_dryrun", "item_id": "J-3c", "idempotency_key": "k-" + oid, "requested_by": "adhikarin", "kyd": "KYD-1",
            "args": {} if args is None else args, "chart_id": CANONICAL_CHART, "reviewed_commit": w.reviewed}
    (w.mod.DONE / f"{oid}.json").write_text(json.dumps(dreq))
    output = "dry run planned the call\n"
    (w.mod.REC / f"{oid}.output.txt").write_text(output)
    record = {"operation_id": oid, "kind": dreq["kind"], "item_id": "J-3c", "status": status, "reason": "", "exit_code": exit_code, "ts": iso(seconds=-30),
              "reviewed_commit": w.reviewed, "request_sha256": w.mod.request_digest(dreq), "output_sha256": sha(output)}
    body = json.dumps(record, indent=1).encode()
    (w.mod.REC / f"{oid}.json").write_bytes(body)
    return {"name": f"{oid}.json", "sha256": sha(body)}


def fill_request(w, template, oid="mech-1", dry=None, lease=None, **tweak):
    req = {**template["fixed"], "operation_id": oid, "idempotency_key": "k-" + oid, "lease_id": lease or w.lease_id, "expires_at": iso(hours=1)}
    if dry is not None:
        req["dryrun_receipt"] = dry
    fill = {k: req[k] for k in sorted(template["fill"]) if k in req}
    req["pack_fill"] = {"pack_manifest_sha256": MANIFEST, "template": template, "fill_sha256": csha(fill)}
    req.update(tweak)
    return req


def scenario(w, kind=KIND, oid="mech-1", with_dry_run=True):
    """The pack lists the template, the dry run completed, the lease is live: a request that is a verified pack fill."""
    template = template_for(w, kind, dry=with_dry_run)
    publish(w, [template])
    dry = dry_run(w, kind) if with_dry_run else None
    return fill_request(w, template, oid, dry=dry), template, dry


def record_of(w, oid="mech-1"):
    return json.loads((w.mod.ACC / f"{oid}.json").read_text())


# ───────────────────────────── X: what never goes mechanical ─────────────────────────────

def oracle_x1_deletions(w, table):
    control, _, _ = scenario(w, oid="mech-control")
    assert w.mod.validate(control, table, ALL_CAPS) is None, "control failed — the refusals below would be vacuous"
    for n, kind in enumerate(("smalltest_teardown", "measuring_teardown")):
        template = template_for(w, kind); publish(w, [template])
        req = fill_request(w, template, f"mech-del-{n}", dry=dry_run(w, kind, f"dry-del-{n}"))
        why, _ = w.mod.mechanical_problem(req, table)
        assert why and "deletion or serving change" in why, (kind, why)
        assert w.mod.validate(req, table, ALL_CAPS) is not None and not (w.mod.ACC / f"mech-del-{n}.json").exists(), kind


def oracle_x2_serving_and_cancel(w, table):
    control, _, _ = scenario(w, oid="mech-control")
    assert w.mod.mechanical_problem(control, table)[0] is None, "control failed — the refusals below would be vacuous"
    enabled = {**table, **{k: dict(table[k], enabled=True, script="platform/scripts/fixture.py") for k in (*SERVING, "measuring_cancel")}}
    for n, kind in enumerate((*SERVING, "measuring_cancel")):
        template = template_for(w, kind); publish(w, [template])
        req = fill_request(w, template, f"mech-srv-{n}", dry=dry_run(w, kind, f"dry-srv-{n}"))
        why, _ = w.mod.mechanical_problem(req, enabled)
        assert why and "deletion or serving change" in why, (kind, why)


def test_x3_every_production_kind_of_the_real_table_is_classified(tmp_path):
    """A production kind added to the table later is neither exempt nor listed here until someone classifies it (the signal reads false by default)."""
    mod = TT._load_executor(tmp_path)
    table = json.loads(OPS_FILE.read_text())["ops"]
    production = {k for k, v in table.items() if v.get("production")}
    exempt = {k for k in production if mod.mechanical_exempt(k)}
    assert exempt == {"smalltest_teardown", "measuring_teardown", "publish_head", "rollback_head", "layer_publish", "layer_rollback", "measuring_cancel"}
    assert production - exempt == {"backup_snapshot", "backup_restore_verify", "smalltest_dispatch", "measuring_dispatch", "verification_job", "century_dispatch",
                                   "orchestrator_rebuild", "layer_verify", "scheduler_pause", "scheduler_resume", "protected_window_dispatch", "gochara_role_provisioning_dispatch"}   # U-M-01 / U-M-03: a dispatch, neither a deletion nor a serving change, so mechanical-eligible with a dry run
    assert mod.NO_DRYRUN_KINDS == {"backup_snapshot", "backup_restore_verify"} and all(k + "_dryrun" in table for k in {"smalltest_dispatch", "measuring_dispatch", "scheduler_pause", "scheduler_resume", "protected_window_dispatch", "gochara_role_provisioning_dispatch"})


# ───────────────────────────── A: admitted, and recorded ─────────────────────────────

def oracle_a1_admitted_and_recorded(w, table):
    req, template, dry = scenario(w)
    assert w.mod.validate(req, table, ALL_CAPS) is None
    assert (w.mod.ACC / "mech-1.json").exists(), "an admitted request left no acceptance record"
    doc = record_of(w)
    assert (doc["schema"], doc["phase"], doc["by"], doc["result"], doc["operation_id"], doc["kind"]) == ("ky.mechanical_acceptance/1", "pre", "executor-mechanical", "ACCEPTED", "mech-1", KIND)
    assert doc["request_sha256"] == w.mod.request_digest(req) and doc["reviewed_commit"] == w.reviewed and doc["lease_id"] == w.lease_id and doc["ts"]
    assert doc["evidence"]["pack"] == {"pack_manifest_sha256": MANIFEST, "template_sha256": csha(template), "fill_sha256": req["pack_fill"]["fill_sha256"], "verify_job": "verify-1"}
    assert doc["evidence"]["dry_run"]["receipt_sha256"] == dry["sha256"] and doc["evidence"]["dry_run"]["output_sha256"] == sha("dry run planned the call\n")
    assert doc["checks"] and all(v is True for v in doc["checks"].values()) and "dry_run_completed_ok_for_same_identity" in doc["checks"]
    assert w.mod.validate(req, table, ALL_CAPS, reserved=True) is None, "the re-validation before execution must find its own record"


def oracle_a2_backup_needs_no_dry_run(w, table):
    template = template_for(w, "backup_snapshot", dry=False)
    template["fixed"]["args"] = {"label": "w4r1_20261018", "scope": "small_test"}
    publish(w, [template])
    req = fill_request(w, template)
    assert w.mod.validate(req, table, ALL_CAPS) is None
    assert "dry_run_not_applicable_to_kind" in record_of(w)["checks"] and record_of(w)["evidence"]["dry_run"] is None


# ───────────────────────────── P: the request equals a VERIFIED pack fill ─────────────────────────────

def oracle_p1_manifest_must_be_listed(w, table):
    req, template, _ = scenario(w)
    assert w.mod.validate(req, table, ALL_CAPS) is None, "control failed"
    publish(w, [template], manifest=OTHER_MANIFEST)                      # a verified pack exists, but not the one this request names
    assert "allow-list" in (w.mod.mechanical_problem(req, table)[0] or "ADMITTED")
    w.mod.PACK_ALLOWLIST.unlink()
    assert "allow-list" in (w.mod.mechanical_problem(req, table)[0] or "ADMITTED"), "a missing allow-list must fail closed"


def oracle_p2_entry_must_be_accepted(w, table):
    req, template, _ = scenario(w)
    for verdict in ("REJECTED", "PENDING", None):
        publish(w, [template], verdict=verdict)
        assert "allow-list" in (w.mod.mechanical_problem(req, table)[0] or "ADMITTED"), verdict


def oracle_p3_template_is_the_packs_not_the_requesters(w, table):
    req, template, dry = scenario(w)
    forged = {**template, "fixed": {**template["fixed"], "kyd": "FORGED"}}      # a template that matches ITS OWN request bytes, but that the pack never listed
    assert w.mod.mechanical_problem(fill_request(w, forged, "mech-forged", dry=dry), table)[0] == "the pack template is not one the verified pack lists for this kind"
    publish(w, [template]); w.mod.PACK_ALLOWLIST.write_text(w.mod.PACK_ALLOWLIST.read_text().replace(f'"{KIND}"', '"backup_snapshot"'))   # listed, but for another kind
    assert w.mod.mechanical_problem(req, table)[0] == "the pack template is not one the verified pack lists for this kind"


def oracle_p4_template_never_fills_identity(w, table):
    template = template_for(w, KIND)
    loose = {**template, "fixed": {k: v for k, v in template["fixed"].items() if k != "reviewed_commit"}, "fill": template["fill"] + ["reviewed_commit"]}
    publish(w, [loose])
    req = fill_request(w, loose, dry=dry_run(w, KIND), reviewed_commit=w.reviewed)       # the commit arrives as a FILL the pack never pinned
    req["pack_fill"]["fill_sha256"] = csha({k: req[k] for k in sorted(loose["fill"]) if k in req})
    assert w.mod.mechanical_problem(req, table)[0] == "the pack template may not fill kind, chart_id, reviewed_commit, requested_by or an approval field"


def oracle_p5_fixed_field_differs(w, table):
    req, template, _ = scenario(w)
    assert w.mod.validate(req, table, ALL_CAPS) is None, "control failed"
    changed = dict(req, kyd="KYD-OTHER", operation_id="mech-2", idempotency_key="k-mech-2")     # kyd is fixed by the pack; operation_id / key are fills
    changed["pack_fill"] = dict(req["pack_fill"], fill_sha256=csha({k: changed[k] for k in sorted(template["fill"]) if k in changed}))
    assert w.mod.mechanical_problem(changed, table)[0] == "the request differs from the verified pack template at fixed field kyd"


def oracle_p6_extra_field(w, table):
    req, _, _ = scenario(w)
    why = w.mod.mechanical_problem(dict(req, source_binding={"anything": "else"}), table)[0]
    assert why and "does not define" in why and "source_binding" in why


def oracle_p7_fill_digest(w, table):
    req, _, _ = scenario(w)
    tampered = dict(req, idempotency_key="k-tampered-after-the-fill")
    assert w.mod.mechanical_problem(tampered, table)[0] == "fill_sha256 does not equal the digest re-derived from the request bytes"


# ───────────────────────────── D: the kind's dry run completed OK for the same identity ─────────────────────────────

def oracle_d1_failed_dry_run(w, table):
    template = template_for(w, KIND); publish(w, [template])
    assert w.mod.mechanical_problem(fill_request(w, template, "m-none"), table)[0] == "dryrun_receipt {name, sha256} citing this kind's completed dry run is required"
    for n, (status, code) in enumerate((("FAILED", 1), ("COMPLETED", 1), ("REFUSED", None))):
        ref = dry_run(w, KIND, f"dry-bad-{n}", status=status, exit_code=code)
        why = w.mod.mechanical_problem(fill_request(w, template, f"m-bad-{n}", dry=ref), table)[0]
        assert why and "did not COMPLETE OK" in why, (status, code, why)


def oracle_d2_other_identity(w, table):
    template = template_for(w, KIND); publish(w, [template])
    assert w.mod.mechanical_problem(fill_request(w, template, "m-ok", dry=dry_run(w, KIND, "dry-ok")), table)[0] is None, "control failed"
    other = dry_run(w, KIND, "dry-other", args={"job": "watchdog-reaper"})           # it completed, but for different args than this request
    why = w.mod.mechanical_problem(fill_request(w, template, "m-other", dry=other), table)[0]
    assert why and "did not COMPLETE OK" in why


def oracle_d3_receipt_bytes(w, table):
    template = template_for(w, KIND); publish(w, [template])
    ref = dry_run(w, KIND)
    path = w.mod.REC / ref["name"]
    path.write_text(json.dumps(dict(json.loads(path.read_text()), note="edited after it was cited")))
    assert w.mod.mechanical_problem(fill_request(w, template, dry=ref), table)[0] == "the dry-run receipt differs from its cited sha256"


def oracle_d4_receipt_bound_to_archived_request(w, table):
    template = template_for(w, KIND); publish(w, [template])
    ref = dry_run(w, KIND)
    archived = w.mod.DONE / "dry-1.json"
    archived.write_text(json.dumps(dict(json.loads(archived.read_text()), kyd="EDITED-AFTER-THE-RUN")))
    why = w.mod.mechanical_problem(fill_request(w, template, dry=ref), table)[0]
    assert why and "did not COMPLETE OK" in why


def oracle_d5_output_bytes(w, table):
    template = template_for(w, KIND); publish(w, [template])
    ref = dry_run(w, KIND)
    (w.mod.REC / "dry-1.output.txt").write_text("a different output")
    why = w.mod.mechanical_problem(fill_request(w, template, dry=ref), table)[0]
    assert why and "did not COMPLETE OK" in why


# ───────────────────────────── L: the lease ─────────────────────────────

def oracle_l1_dead_lease(w, table):
    req, template, dry = scenario(w)
    assert w.mod.mechanical_pre_acceptance(req, table) is None, "control failed"
    dead = fill_request(w, template, "mech-dead", dry=dry, lease="lease-dead")
    assert w.mod.mechanical_pre_acceptance(dead, table) == "lease is not the single unexpired ACTIVE row on origin/campaign-coordination"
    assert not (w.mod.ACC / "mech-dead.json").exists(), "a dead lease must leave no acceptance record"
    assert w.mod.validate(dead, table, ALL_CAPS) == "lease is not the single unexpired ACTIVE row on origin/campaign-coordination"


# ───────────────────────────── B / R: back-compat and record integrity ─────────────────────────────

def oracle_b1_signer_route_is_untouched(w, table):
    template = template_for(w, KIND)
    publish(w, [template], manifest=OTHER_MANIFEST)                       # the pack this request names is NOT verified: the mechanical route would refuse it
    signed = w.accept(fill_request(w, template, "mech-signed", dry=None), checks={"dry_run_passed": True})
    assert w.mod.mechanical_problem(signed, table)[0] is not None, "premise: the mechanical route refuses this request"
    assert w.mod.validate(signed, table, ALL_CAPS) is None, "a signer-accepted request must be judged by its signer, whatever else it carries"
    assert json.loads(Path(signed["acceptance_receipt"]).read_text())["by"] == "v1", "the signer's record is never replaced by a mechanical one"
    teardown = w.accept(w.production_request("smalltest_teardown", operation_id="op-td"), checks={"backup_taken": True, "dry_run_passed": True})
    assert w.mod.signer_acceptance_problem(teardown) is None, "a deletion is still accepted through its V1 signer"
    unsigned = w.production_request("scheduler_resume", operation_id="op-nosign")
    assert w.mod.validate(unsigned, table, ALL_CAPS) == "pre-acceptance receipt missing (must live under run/ops/acceptance/)"


def oracle_r1_foreign_record_never_reused(w, table):
    req, _, _ = scenario(w)
    (w.mod.ACC / "mech-1.json").write_text(json.dumps({"by": "executor-mechanical", "result": "ACCEPTED", "request_sha256": "0" * 64}))
    assert w.mod.validate(req, table, ALL_CAPS) == "an acceptance record for this operation already exists and does not bind this request"


ORACLES = {
    "x1": (oracle_x1_deletions, ('return kind.endswith("_teardown") or kind in SIGNED_ONLY_KINDS', 'return kind in SIGNED_ONLY_KINDS')),
    "x2": (oracle_x2_serving_and_cancel, ('SIGNED_ONLY_KINDS = frozenset({"publish_head", "layer_publish", "rollback_head", "layer_rollback", "measuring_cancel"})', 'SIGNED_ONLY_KINDS = frozenset()')),
    "a1": (oracle_a1_admitted_and_recorded, ("    if write_new_json(path, document): return None\n", "    if True: return None\n")),
    "a2": (oracle_a2_backup_needs_no_dry_run, ("    if kind in NO_DRYRUN_KINDS: return None, None\n", "    if False: return None, None\n")),
    "p1": (oracle_p1_manifest_must_be_listed, ('isinstance(p, dict) and p.get("pack_manifest_sha256") == manifest)', "isinstance(p, dict))")),
    "p2": (oracle_p2_entry_must_be_accepted, ('entry.get("verdict") != "ACCEPTED"', "False")),
    "p3": (oracle_p3_template_is_the_packs_not_the_requesters, ('templates.get(template_sha) == req.get("kind")', "True")),
    "p4": (oracle_p4_template_never_fills_identity, ("    if set(fill) & PACK_NEVER_FILLED: return", "    if False: return")),
    "p5": (oracle_p5_fixed_field_differs, ("if not clock(k) and (k not in req or canonical_sha(req[k]) != canonical_sha(v)):", "if False:")),
    "p6": (oracle_p6_extra_field, ("    if extra: return f", "    if False: return f")),
    "p7": (oracle_p7_fill_digest, ("not clock(k)}) != declared:", "not clock(k)}) != declared and False:")),
    "d1": (oracle_d1_failed_dry_run, ('rec.get("status") == "COMPLETED" and type(rec.get("exit_code")) is int and rec["exit_code"] == 0', "True")),
    "d2": (oracle_d2_other_identity, ("and all(canonical_sha(archived.get(f)) == canonical_sha(req.get(f)) for f in DRYRUN_IDENTITY_FIELDS))", "and True)")),
    "d3": (oracle_d3_receipt_bytes, ('if digest_bytes(body) != ref["sha256"]: return', 'if False: return')),
    "d4": (oracle_d4_receipt_bound_to_archived_request, ('and request_digest(archived) == rec.get("request_sha256")', "and True")),
    "d5": (oracle_d5_output_bytes, ('and "lane_target" not in rec and digest_bytes(output) == rec.get("output_sha256")', 'and "lane_target" not in rec')),
    "l1": (oracle_l1_dead_lease, ('    if not lease: return "lease is not', '    if False: return "lease is not')),
    "b1": (oracle_b1_signer_route_is_untouched, ('if not req.get("acceptance_receipt") and req.get("pack_fill") is not None:', 'if req.get("pack_fill") is not None:')),
    "r1": (oracle_r1_foreign_record_never_reused, ('existing.get("request_sha256") == digest: return None', "True: return None")),
}


@pytest.mark.parametrize("claim", sorted(ORACLES))
def test_oracle_passes_on_the_real_executor(tmp_path, monkeypatch, claim):
    w, table = build(tmp_path, monkeypatch)
    ORACLES[claim][0](w, table)


@pytest.mark.parametrize("claim", sorted(ORACLES))
def test_oracle_fails_on_its_planted_reversion(tmp_path, monkeypatch, claim):
    oracle, mutation = ORACLES[claim]
    w, table = build(tmp_path, monkeypatch, mutation)
    with pytest.raises(AssertionError):
        oracle(w, table)
