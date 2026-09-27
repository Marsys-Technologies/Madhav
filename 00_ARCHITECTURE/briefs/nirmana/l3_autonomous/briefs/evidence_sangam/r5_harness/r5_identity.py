"""R-5 identity + preservation-manifest library.

Implements design D-R5-1 (SANGAM_STAGE3_STATE.md, Phase 1) and the §6.3 manifest
spec (SANGAM_ALGORITHM_ELEVATION_PLAN_v1_0.md, as amended per RRV-09):

- contact_uuid  = UUIDv5 over (chart_id, method_contract_version, graha,
  target_fact_id, directed_angle_deg, frame_vector(6-tuple), orb_deg, contact_kind)
- episode_uuid  = UUIDv5 over (chart_id, method_contract_version, graha,
  target_fact_id, directed_angle_deg, frame_vector, sha256 of the sorted member
  contact_uuid list)
- canonical serialization = JSON with sorted keys over the record MINUS the
  explicit FIELD_EXCLUSIONS list below. Without the exclusion list the §6.3
  comparison either fails benign rebuilds (timestamps, head pointers) or
  loosens until a content swap passes (the unframed-hash attack one level up).
- manifest(db)  = dict keyed by stable id (contact:<contact_uuid> /
  claim:<claim id>): full claim content (canonical serialization), version,
  exposure, outcome bytes verbatim (outcome_recorded/outcome_notes — the real
  columns), every dependent binding resolved semantically INCLUDING the FK-free
  phala_phaladesa.top_anchor_id (resolved by matching anchor content, not by
  surrogate id), and successor mappings.

Python 3 stdlib only. Disposable-harness code — not production.
"""

from __future__ import annotations

import base64
import hashlib
import json
import sqlite3
import uuid

R5_NAMESPACE = uuid.UUID("7b2e1c4a-9f3d-4e8b-9a1c-5d6e7f809102")

# --- Explicit field-exclusion list (plan §6.3 as amended per RRV-09) ---------
# These fields are write metadata or selection state — never identity- or
# content-bearing — and are stripped before canonical serialization:
FIELD_EXCLUSIONS = [
    "id",                       # surrogate row id — sequence bigint, never identity-bearing
    "computed_at",              # write timestamp — provenance metadata, not claim content
    "generation_head_id",       # generation head pointer — selection state, not content
    "generation_head_pointer",  # generation head pointer (writer alias) — selection state
]

# Surrogate FK bindings are likewise not content: a claim's bytes must not
# change because a binding was re-pointed. They are dropped from canonical
# content and re-expressed semantically (bound_contact_uuid / anchor content).
SURROGATE_BINDINGS = ("convergence_id", "anchor_id")


def frame_vector(ayanamsha_id, ephemeris_backend, epoch_convention,
                 ayanamsa_application, node_convention, house_frame):
    """R-3 convention vector — six components; two frames never coalesce."""
    return (ayanamsha_id, ephemeris_backend, epoch_convention,
            ayanamsa_application, node_convention, house_frame)


def canonical_json(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def contact_uuid(chart_id, method_contract_version, graha, target_fact_id,
                 directed_angle_deg, frame_vector6, orb_deg, contact_kind) -> str:
    """D-R5-1 contact identity. Deliberately EXCLUDES peak_date, interval
    endpoints and orb shoulders — algorithm-versioned content, not identity."""
    payload = {
        "chart_id": chart_id,
        "method_contract_version": method_contract_version,
        "graha": graha,
        "target_fact_id": target_fact_id,
        "directed_angle_deg": directed_angle_deg,
        "frame_vector": list(frame_vector6),
        "orb_deg": orb_deg,
        "contact_kind": contact_kind,
    }
    return str(uuid.uuid5(R5_NAMESPACE, canonical_json(payload)))


def episode_uuid(chart_id, method_contract_version, graha, target_fact_id,
                 directed_angle_deg, frame_vector6, member_contact_uuids) -> str:
    """D-R5-1 episode identity: deterministic, rebuild-stable when membership is
    unchanged; membership changes produce split/merge edges from the old episode."""
    set_hash = hashlib.sha256(
        "|".join(sorted(member_contact_uuids)).encode("utf-8")).hexdigest()
    payload = {
        "chart_id": chart_id,
        "method_contract_version": method_contract_version,
        "graha": graha,
        "target_fact_id": target_fact_id,
        "directed_angle_deg": directed_angle_deg,
        "frame_vector": list(frame_vector6),
        "member_set_hash": set_hash,
    }
    return str(uuid.uuid5(R5_NAMESPACE, canonical_json(payload)))


def canonical_serialize(record: dict) -> str:
    """Canonical serialization: JSON sorted-keys over the record minus
    FIELD_EXCLUSIONS (RRV-09 — the list is named in code so the test greps it)."""
    return canonical_json({k: v for k, v in record.items()
                           if k not in FIELD_EXCLUSIONS})


def content_hash(record: dict) -> str:
    return hashlib.sha256(canonical_serialize(record).encode("utf-8")).hexdigest()


def _jsonable(obj):
    """Bytes -> tagged base64 so the manifest can be digest-compared as JSON.
    Outcome bytes are kept verbatim in the manifest itself (bytes objects)."""
    if isinstance(obj, (bytes, bytearray)):
        return {"__bytes_b64__": base64.b64encode(bytes(obj)).decode("ascii")}
    if isinstance(obj, dict):
        return {k: _jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_jsonable(v) for v in obj]
    return obj


def _canon_row(row: dict, drop=()) -> str:
    banned = set(FIELD_EXCLUSIONS) | set(drop)
    return canonical_json({k: v for k, v in row.items() if k not in banned})


def manifest(db: sqlite3.Connection) -> dict:
    """Preservation manifest keyed by stable id.

    Per id: full claim content (canonical serialization), version, exposure,
    outcome bytes verbatim, every dependent binding resolved semantically
    (incl. the FK-free phala_phaladesa.top_anchor_id, resolved by matching
    anchor content), and successor mappings from contact_relations."""
    db.row_factory = sqlite3.Row
    conv_rows = [dict(r) for r in db.execute("SELECT * FROM kala_convergence")]
    by_id = {r["id"]: r for r in conv_rows}
    conv_uuid_by_id = {r["id"]: r["contact_uuid"] for r in conv_rows}
    anchors = [dict(r) for r in db.execute("SELECT * FROM phala_anchors")]
    anchors_by_id = {a["id"]: a for a in anchors}

    m = {}

    # --- issued claims (kala_bhavishya — original history immutable) --------
    for r in db.execute("SELECT * FROM kala_bhavishya"):
        b = dict(r)
        bound = by_id.get(b["convergence_id"])
        m[f"claim:{b['id']}"] = {
            "kind": "claim",
            "stable_id": f"claim:{b['id']}",
            "claim_content": _canon_row(b, drop=SURROGATE_BINDINGS
                                        + ("outcome_recorded", "outcome_notes")),
            "version": b["version"],
            "exposure": b["exposure"],
            "outcome_recorded": bytes(b["outcome_recorded"]) if b["outcome_recorded"] is not None else None,
            "outcome_notes": bytes(b["outcome_notes"]) if b["outcome_notes"] is not None else None,
            # semantic binding — never the surrogate convergence_id
            "bound_contact_uuid": bound["contact_uuid"] if bound else None,
        }

    # --- contacts + every dependent binding, resolved semantically ----------
    for row in conv_rows:
        cuuid = row["contact_uuid"]
        bindings = {"kala_obstruction": [], "kala_darshana": [],
                    "phala_anchors": [], "phala_phaladesa": []}
        for t in ("kala_obstruction", "kala_darshana"):
            for r in db.execute(f"SELECT * FROM {t} WHERE convergence_id=?", (row["id"],)):
                bindings[t].append(_canon_row(dict(r), drop=SURROGATE_BINDINGS))
        for a in anchors:
            if a["convergence_id"] != row["id"]:
                continue
            entry = {"anchor_content": _canon_row(a, drop=SURROGATE_BINDINGS),
                     "phala_suddha_sodhana": [], "phala_muhurta": [],
                     "phala_mitigation": []}
            for t in ("phala_suddha_sodhana", "phala_muhurta", "phala_mitigation"):
                for r in db.execute(f"SELECT * FROM {t} WHERE anchor_id=?", (a["id"],)):
                    entry[t].append(_canon_row(dict(r), drop=SURROGATE_BINDINGS))
            bindings["phala_anchors"].append(entry)
        # FK-free phala_phaladesa.top_anchor_id: resolved by matching anchor
        # CONTENT, not by surrogate id — a dangling pointer is surfaced, not
        # silently followed or silently dropped.
        for r in db.execute("SELECT * FROM phala_phaladesa"):
            p = dict(r)
            anchor = anchors_by_id.get(p["top_anchor_id"])
            if anchor is not None and anchor["convergence_id"] == row["id"]:
                bindings["phala_phaladesa"].append({
                    "phaladesa_content": _canon_row(p, drop=("top_anchor_id",)),
                    "resolved_anchor_content": _canon_row(anchor, drop=SURROGATE_BINDINGS),
                })
        successors = [{"new_contact_uuid": r["new_contact_uuid"], "relation_type": r["relation_type"]}
                      for r in db.execute(
                          "SELECT new_contact_uuid, relation_type FROM contact_relations "
                          "WHERE old_contact_uuid=?", (cuuid,))]
        predecessors = [{"old_contact_uuid": r["old_contact_uuid"], "relation_type": r["relation_type"]}
                        for r in db.execute(
                            "SELECT old_contact_uuid, relation_type FROM contact_relations "
                            "WHERE new_contact_uuid=?", (cuuid,))]
        flags = sorted(r["flag"] for r in db.execute(
            "SELECT flag FROM rebuild_flags WHERE contact_uuid=?", (cuuid,)))
        m[f"contact:{cuuid}"] = {
            "kind": "contact",
            "stable_id": cuuid,
            "claim_content": canonical_serialize(row),
            "version": row["content_version"],
            "exposure": row["exposure"],
            "status": row["status"],
            "withdrawal_reason": row["withdrawal_reason"],
            "claim_ids": sorted(k for k in m if k.startswith("claim:")
                                and m[k]["bound_contact_uuid"] == cuuid),
            "bindings": bindings,
            "successor_mappings": successors,
            "predecessor_mappings": predecessors,
            "flags": flags,
        }

    # --- detached (SET NULL landed) rows — explicit, never silently dropped --
    m["__detached__"] = {
        "kala_bhavishya": [_canon_row(dict(r), drop=SURROGATE_BINDINGS)
                           for r in db.execute(
                               "SELECT * FROM kala_bhavishya WHERE convergence_id IS NULL")],
        "phala_muhurta": [_canon_row(dict(r), drop=SURROGATE_BINDINGS)
                          for r in db.execute(
                              "SELECT * FROM phala_muhurta WHERE anchor_id IS NULL")],
        "phala_mitigation": [_canon_row(dict(r), drop=SURROGATE_BINDINGS)
                             for r in db.execute(
                                 "SELECT * FROM phala_mitigation WHERE anchor_id IS NULL")],
        "phala_phaladesa": [
            {"phaladesa_content": _canon_row(dict(r), drop=("top_anchor_id",)),
             "dangling_top_anchor_id": r["top_anchor_id"]}
            for r in db.execute("SELECT * FROM phala_phaladesa")
            if r["top_anchor_id"] is None or r["top_anchor_id"] not in anchors_by_id
            or anchors_by_id[r["top_anchor_id"]]["convergence_id"] not in conv_uuid_by_id],
    }
    return m


def manifest_digest(db: sqlite3.Connection) -> str:
    """Byte-identity comparison frame for interrupt/resume and empty-rebuild."""
    return canonical_json(_jsonable(manifest(db)))


def compare_manifests(m1: dict, m2: dict) -> list:
    """Per-stable-id, per-field comparison — exact content per id, never counts
    or unframed hashes. Returns [(key, field, before, after), ...]."""
    diffs = []
    for key in sorted(set(m1) | set(m2)):
        if key not in m1:
            diffs.append((key, "added", None, canonical_json(_jsonable(m2[key]))))
            continue
        if key not in m2:
            diffs.append((key, "removed", canonical_json(_jsonable(m1[key])), None))
            continue
        e1, e2 = m1[key], m2[key]
        if e1 == e2:
            continue
        for f in sorted(set(e1) | set(e2)):
            if e1.get(f) != e2.get(f):
                diffs.append((key, f, e1.get(f), e2.get(f)))
    return diffs
