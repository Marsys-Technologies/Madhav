"""Shared fixture for the owner-go gate (OWNER-BUILD-GO-REQUIRED-20261023): the owner's go file, bound to one request as the owner surrogate writes it."""
import datetime as dt
import json


def owner_go_document(mod, req, **over):
    go = {"schema": "ky.owner_go/1", "operation_id": req["operation_id"], "kind": req["kind"], "item_id": req["item_id"], "request_sha256": mod.request_digest(req),
          "reviewed_commit": req.get("reviewed_commit"), "owner_yes": True, "owner_words": "start the build", "transcript_citation": "session 2026-10-23T14:02:11Z, owner message 7",
          "written_by": "madhav-44 (owner surrogate)", "written_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}
    go.update(over)
    return go


def write_owner_go(mod, req, **over):
    """Write run/ops/owner_go/<operation_id>.json for `req` (any field overridable; a field set to None is dropped) and return the request unchanged."""
    mod.OPS.joinpath("owner_go").mkdir(parents=True, exist_ok=True)
    go = {k: v for k, v in owner_go_document(mod, req, **over).items() if v is not None}
    (mod.OPS / "owner_go" / f"{req['operation_id']}.json").write_text(json.dumps(go))
    return req
