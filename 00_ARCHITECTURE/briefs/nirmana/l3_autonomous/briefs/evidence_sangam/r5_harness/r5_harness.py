"""R-5 disposable harness: schema-faithful SQLite mirror + five-rule rebuild.

Schema mirrors the real cascade graph (companion brief SANGAM_ELEVATION_BRIEF
§5.2; migrations 245/247/249/331/332/334/339/363) so real CASCADE / SET NULL
semantics fire under PRAGMA foreign_keys=ON:

    kala_convergence      (chart PK id, contact_uuid UNIQUE, chart_id,
                           method_contract_version, content_hash, content,
                           peak_date, generation)          + harness columns
    kala_obstruction      convergence_id ON DELETE CASCADE    (245)
    kala_darshana         convergence_id ON DELETE CASCADE    (247)
    kala_bhavishya        convergence_id ON DELETE SET NULL   (249)
                          claim_content, outcome_recorded, outcome_notes
                          (original history immutable — the real columns)
    phala_anchors         convergence_id ON DELETE CASCADE    (363)
    phala_suddha_sodhana  anchor_id ON DELETE CASCADE         (334)
    phala_muhurta         anchor_id ON DELETE SET NULL        (331)
    phala_mitigation      anchor_id ON DELETE SET NULL        (332)
    phala_phaladesa       top_anchor_id INTEGER — FK-free, no constraint (339)
    contact_relations     old/new contact_uuid, relation_type IN
                          ('supersedes','split_from','merged_into','reattached')
    rebuild_journal       interrupt/resume journal (D-R5-1 rule 5)
    rebuild_flags         fail-closed adjudication flags

Rebuild/mapping implements D-R5-1's five rules:
  1. candidate uuid + identical content-hash -> no-op
  2. candidate uuid + different content     -> supersede (version+1, edge)
  3. new candidate, no uuid match           -> geometry match against unmatched
     originals (same target fact, angle, frame, overlapping orb): exactly one
     decisive match -> reattach; zero or >1 -> AMBIGUOUS: original retained,
     claim NOT reattached (fail-closed), flagged ambiguous_needs_adjudication —
     never silently re-pointed. FAIL_CLOSED_AMBIGUOUS is read at decision time;
     S14's NEG control flips it (evidence-bearing mutation of this rule).
  4. original with no successor, no explicit withdrawal -> retained (nothing
     deletes implicitly); explicit withdrawal -> withdrawn with recorded
     reason, claims mapped only to an authorized successor, else flagged.
  5. decisions journaled; resume replays the journal; exactly-once effects.

Harness columns beyond the brief's mirror (content_version, exposure, status,
withdrawal_reason, computed_at, generation_head_id) exist to *exercise* the
identity design: computed_at / generation_head_id are named in
r5_identity.FIELD_EXCLUSIONS so the RRV-09 exclusion list is load-bearing.

Design strengthening vs the D-R5-1 text (recorded, not silent): geometry match
additionally requires same chart_id and method_contract_version — a contact
from another chart or contract version can never be the same testimony. Splits
and merges arrive as adjudications (declared authorized successors), matching
attack specs 3/4; the adjudicated reattachment path resolves an ambiguous
candidate exactly when a successor is declared (attack 5, phase 2).
"""

from __future__ import annotations

import datetime
import json
import sqlite3

import r5_identity as I

# Rule 3 fail-closed switch. S14's negative control sets this False so the
# ambiguous candidate silently re-attaches — a genuine mutation of the
# evidence-bearing decision logic (RRV-15 discipline).
FAIL_CLOSED_AMBIGUOUS = True

SCHEMA = """
CREATE TABLE kala_convergence (
  id INTEGER PRIMARY KEY,
  contact_uuid TEXT UNIQUE NOT NULL,
  chart_id TEXT NOT NULL,
  method_contract_version TEXT NOT NULL,
  content_hash TEXT NOT NULL,
  content TEXT NOT NULL,
  peak_date TEXT NOT NULL,
  generation INTEGER NOT NULL DEFAULT 1,
  content_version INTEGER NOT NULL DEFAULT 1,
  exposure TEXT NOT NULL DEFAULT 'undeclared',
  status TEXT NOT NULL DEFAULT 'active',
  withdrawal_reason TEXT,
  computed_at TEXT,
  generation_head_id INTEGER
);
CREATE TABLE kala_obstruction (
  id INTEGER PRIMARY KEY,
  convergence_id INTEGER NOT NULL REFERENCES kala_convergence(id) ON DELETE CASCADE,
  note TEXT NOT NULL
);
CREATE TABLE kala_darshana (
  id INTEGER PRIMARY KEY,
  convergence_id INTEGER NOT NULL REFERENCES kala_convergence(id) ON DELETE CASCADE,
  note TEXT NOT NULL
);
CREATE TABLE kala_bhavishya (
  id INTEGER PRIMARY KEY,
  convergence_id INTEGER REFERENCES kala_convergence(id) ON DELETE SET NULL,
  claim_content TEXT NOT NULL,
  version INTEGER NOT NULL DEFAULT 1,
  exposure TEXT NOT NULL DEFAULT 'undeclared',
  outcome_recorded BLOB,
  outcome_notes BLOB
);
CREATE TABLE phala_anchors (
  id INTEGER PRIMARY KEY,
  convergence_id INTEGER NOT NULL REFERENCES kala_convergence(id) ON DELETE CASCADE,
  anchor_content TEXT NOT NULL
);
CREATE TABLE phala_suddha_sodhana (
  id INTEGER PRIMARY KEY,
  anchor_id INTEGER NOT NULL REFERENCES phala_anchors(id) ON DELETE CASCADE,
  note TEXT NOT NULL
);
CREATE TABLE phala_muhurta (
  id INTEGER PRIMARY KEY,
  anchor_id INTEGER REFERENCES phala_anchors(id) ON DELETE SET NULL,
  note TEXT NOT NULL
);
CREATE TABLE phala_mitigation (
  id INTEGER PRIMARY KEY,
  anchor_id INTEGER REFERENCES phala_anchors(id) ON DELETE SET NULL,
  note TEXT NOT NULL
);
CREATE TABLE phala_phaladesa (
  id INTEGER PRIMARY KEY,
  top_anchor_id INTEGER,          -- FK-free: no constraint, silent-orphan class
  note TEXT NOT NULL
);
CREATE TABLE contact_relations (
  id INTEGER PRIMARY KEY,
  old_contact_uuid TEXT NOT NULL,
  new_contact_uuid TEXT NOT NULL,
  relation_type TEXT NOT NULL CHECK (relation_type IN
    ('supersedes','split_from','merged_into','reattached')),
  generation INTEGER NOT NULL
);
CREATE TABLE rebuild_journal (
  seq INTEGER PRIMARY KEY,
  run_id INTEGER NOT NULL,
  op_index INTEGER NOT NULL,
  action TEXT NOT NULL,
  payload TEXT NOT NULL,
  applied INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE rebuild_flags (
  contact_uuid TEXT NOT NULL,
  flag TEXT NOT NULL,
  detail TEXT,
  PRIMARY KEY (contact_uuid, flag)
);
"""

GENERATION = 1  # the disposable harness runs a single candidate generation


def fresh_db(path=":memory:") -> sqlite3.Connection:
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    db.executescript(SCHEMA)
    return db


# ---------------------------------------------------------------- identities

def make_candidate(*, chart_id, method_contract_version, graha, target_fact_id,
                   directed_angle_deg, frame_vector, orb_deg, contact_kind,
                   peak_date, claim, exposure="undeclared") -> dict:
    """A candidate contact from the (simulated) algorithm output. `claim` is the
    algorithm-versioned content (peak phase, factors...); peak_date is content,
    NOT identity — a moved peak keeps the uuid and bumps the version."""
    identity = {
        "chart_id": chart_id,
        "method_contract_version": method_contract_version,
        "graha": graha,
        "target_fact_id": target_fact_id,
        "directed_angle_deg": directed_angle_deg,
        "frame_vector": list(frame_vector),
        "orb_deg": orb_deg,
        "contact_kind": contact_kind,
    }
    content = {"identity": identity, "claim": claim, "peak_date": peak_date}
    return {
        "contact_uuid": I.contact_uuid(
            chart_id, method_contract_version, graha, target_fact_id,
            directed_angle_deg, frame_vector, orb_deg, contact_kind),
        "content": content,
        "content_hash": I.content_hash(content),
        "peak_date": peak_date,
        "exposure": exposure,
    }


def insert_contact(db, cand, generation=GENERATION, computed_at="fixture"):
    ident = cand["content"]["identity"]
    cur = db.execute(
        "INSERT INTO kala_convergence (contact_uuid, chart_id, "
        "method_contract_version, content_hash, content, peak_date, generation, "
        "content_version, exposure, status, computed_at, generation_head_id) "
        "VALUES (?,?,?,?,?,?,?,1,?,'active',?,NULL)",
        (cand["contact_uuid"], ident["chart_id"],
         ident["method_contract_version"], cand["content_hash"],
         I.canonical_json(cand["content"]), cand["peak_date"], generation,
         cand.get("exposure", "undeclared"), computed_at))
    db.commit()
    return cur.lastrowid


def _identity_of(conv_row) -> dict:
    return json.loads(conv_row["content"])["identity"]


def _peak_of(conv_row) -> str:
    return json.loads(conv_row["content"])["peak_date"]


def _d(iso_date) -> datetime.date:
    return datetime.date.fromisoformat(iso_date)


def geometry_plausible(orig_row, cand) -> bool:
    """D-R5-1 rule-3 geometry match: same target fact, angle, frame, overlapping
    orb. Strengthened (recorded in module docstring): same chart and contract
    version. Orb overlap = the two contact windows intersect."""
    oi = _identity_of(orig_row)
    ci = cand["content"]["identity"]
    if oi["chart_id"] != ci["chart_id"]:
        return False
    if oi["method_contract_version"] != ci["method_contract_version"]:
        return False
    if oi["target_fact_id"] != ci["target_fact_id"]:
        return False
    if float(oi["directed_angle_deg"]) != float(ci["directed_angle_deg"]):
        return False
    if list(oi["frame_vector"]) != list(ci["frame_vector"]):
        return False
    gap = abs((_d(_peak_of(orig_row)) - _d(cand["peak_date"])).days)
    return gap <= float(oi["orb_deg"]) + float(ci["orb_deg"])


# ------------------------------------------------------------- rebuild rules

def _reattach_ops(old_u: str, cand: dict) -> list:
    """Decisive/adjudicated reattachment: insert candidate, publish relation,
    withdraw original with reason, re-point its claims, clear any ambiguity flag."""
    new_u = cand["contact_uuid"]
    return [
        {"op": "insert_contact", "candidate": cand},
        {"op": "add_relation", "old": old_u, "new": new_u, "type": "reattached"},
        {"op": "withdraw", "uuid": old_u, "reason": "decisive_geometry_reattach"},
        {"op": "reattach_claims", "from_uuid": old_u, "to_uuid": new_u},
        {"op": "clear_flag", "contact_uuid": old_u,
         "flag": "ambiguous_needs_adjudication"},
    ]


def compute_decisions(db, candidates, generation, adjudications) -> list:
    """Pure decision phase (D-R5-1 rules 1-4) over the pre-rebuild snapshot.
    The op list is journaled; application is a separate, resumable phase."""
    adjudications = adjudications or {}
    originals = {r["contact_uuid"]: dict(r)
                 for r in db.execute(
                     "SELECT * FROM kala_convergence WHERE status='active'")}
    matched_orig = set()
    consumed = set()
    ops = []

    # Rule 1/2 — uuid match: no-op or supersede.
    for ci, c in enumerate(candidates):
        u = c["contact_uuid"]
        if u in originals:
            consumed.add(ci)
            matched_orig.add(u)
            if originals[u]["content_hash"] == c["content_hash"]:
                ops.append({"op": "no_op", "uuid": u})
            else:
                ops.append({"op": "supersede", "uuid": u, "content": c["content"],
                            "content_hash": c["content_hash"],
                            "peak_date": c["peak_date"]})
                ops.append({"op": "add_relation", "old": u, "new": u,
                            "type": "supersedes"})

    # Rule 3 (adjudicated) — declared successor resolves an ambiguous candidate.
    cand_by_uuid = {c["contact_uuid"]: (ci, c) for ci, c in enumerate(candidates)}
    for cand_u, old_u in adjudications.get("reattachments", {}).items():
        if cand_u in cand_by_uuid:
            ci, c = cand_by_uuid[cand_u]
            if ci in consumed:
                continue
            consumed.add(ci)
            matched_orig.add(old_u)
            ops.extend(_reattach_ops(old_u, c))

    # Adjudicated splits (attack 3): children + split_from edges, original
    # withdrawn with reason, claims mapped to the declared authorized successor
    # ONLY; a split without a successor flags the claims, never orphans them.
    for old_u, spec in adjudications.get("splits", {}).items():
        matched_orig.add(old_u)
        child_uuids = []
        for cc in spec["children"]:
            ops.append({"op": "insert_contact", "candidate": cc})
            child_uuids.append(cc["contact_uuid"])
            ops.append({"op": "add_relation", "old": old_u,
                        "new": cc["contact_uuid"], "type": "split_from"})
        ops.append({"op": "withdraw", "uuid": old_u, "reason": spec["reason"]})
        succ = spec.get("successor")
        if succ and succ in child_uuids:
            ops.append({"op": "reattach_claims", "from_uuid": old_u, "to_uuid": succ})
        else:
            ops.append({"op": "set_flag", "contact_uuid": old_u,
                        "flag": "claims_unmapped",
                        "detail": "split without authorized successor"})

    # Adjudicated merges (attack 4): one candidate, two (or more) originals.
    for new_u, spec in adjudications.get("merges", {}).items():
        ops.append({"op": "insert_contact", "candidate": spec["candidate"]})
        for old_u in spec["originals"]:
            matched_orig.add(old_u)
            ops.append({"op": "add_relation", "old": old_u, "new": new_u,
                        "type": "merged_into"})
            ops.append({"op": "withdraw", "uuid": old_u, "reason": spec["reason"]})
            ops.append({"op": "reattach_claims", "from_uuid": old_u,
                        "to_uuid": new_u})

    # Rule 3 (automatic) — geometry match for remaining candidates.
    for ci, c in enumerate(candidates):
        if ci in consumed:
            continue
        plausible = [u for u in sorted(originals)
                     if u not in matched_orig
                     and geometry_plausible(originals[u], c)]
        if len(plausible) == 1:
            old_u = plausible[0]
            consumed.add(ci)
            matched_orig.add(old_u)
            ops.extend(_reattach_ops(old_u, c))
        elif len(plausible) == 0:
            consumed.add(ci)
            # candidate addition — explicit expected delta, not an implicit edit
            ops.append({"op": "insert_contact", "candidate": c})
        else:
            consumed.add(ci)
            if FAIL_CLOSED_AMBIGUOUS:
                for u in plausible:
                    ops.append({"op": "set_flag", "contact_uuid": u,
                                "flag": "ambiguous_needs_adjudication",
                                "detail": (f"candidate {c['contact_uuid']} "
                                           f"plausibly matches {len(plausible)} originals")})
            else:
                # NEG control only: silently re-attach to the first plausible
                # original — exactly the silent re-pointing rule 3 forbids.
                old_u = plausible[0]
                matched_orig.add(old_u)
                ops.extend(_reattach_ops(old_u, c))

    # Rule 4 — explicit withdrawals; unmatched originals are retained (no op:
    # nothing deletes implicitly).
    for old_u, spec in adjudications.get("withdrawals", {}).items():
        matched_orig.add(old_u)
        ops.append({"op": "withdraw", "uuid": old_u, "reason": spec["reason"]})
        succ = spec.get("successor")
        if succ:
            ops.append({"op": "reattach_claims", "from_uuid": old_u,
                        "to_uuid": succ})
        else:
            ops.append({"op": "set_flag", "contact_uuid": old_u,
                        "flag": "claims_unmapped",
                        "detail": "withdrawn without authorized successor"})
    return ops


# ------------------------------------------------------- journaled execution

def _journal(db, run_id, op_index, action, payload):
    db.execute("INSERT INTO rebuild_journal (run_id, op_index, action, payload, applied) "
               "VALUES (?,?,?,?,1)", (run_id, op_index, action, I.canonical_json(payload)))
    db.commit()


def _load_journaled_decisions(db):
    row = db.execute("SELECT payload FROM rebuild_journal WHERE op_index=-1 "
                     "ORDER BY seq DESC LIMIT 1").fetchone()
    if row is None:
        raise RuntimeError("resume requested but no journaled decisions found")
    payload = json.loads(row["payload"])
    return payload["run_id"], payload["ops"]


def _apply_op(db, op, generation):
    t = op["op"]
    if t == "no_op":
        return
    if t == "insert_contact":
        c = op["candidate"]
        ident = c["content"]["identity"]
        db.execute(
            "INSERT INTO kala_convergence (contact_uuid, chart_id, "
            "method_contract_version, content_hash, content, peak_date, "
            "generation, content_version, exposure, status, computed_at, "
            "generation_head_id) VALUES (?,?,?,?,?,?,?,1,?,'active',?,NULL)",
            (c["contact_uuid"], ident["chart_id"],
             ident["method_contract_version"], c["content_hash"],
             I.canonical_json(c["content"]), c["peak_date"], generation,
             c.get("exposure", "undeclared"), f"rebuild-g{generation}"))
    elif t == "supersede":
        # same row, new content version; computed_at / generation_head_id move
        # — both are in FIELD_EXCLUSIONS, so benign rebuilds do not diff.
        db.execute(
            "UPDATE kala_convergence SET content=?, content_hash=?, peak_date=?, "
            "content_version=content_version+1, computed_at=? "
            "WHERE contact_uuid=?",
            (I.canonical_json(op["content"]), op["content_hash"],
             op["peak_date"], f"rebuild-g{generation}", op["uuid"]))
    elif t == "add_relation":
        db.execute("INSERT INTO contact_relations (old_contact_uuid, "
                   "new_contact_uuid, relation_type, generation) VALUES (?,?,?,?)",
                   (op["old"], op["new"], op["type"], generation))
    elif t == "withdraw":
        db.execute("UPDATE kala_convergence SET status='withdrawn', "
                   "withdrawal_reason=? WHERE contact_uuid=?",
                   (op["reason"], op["uuid"]))
    elif t == "reattach_claims":
        db.execute(
            "UPDATE kala_bhavishya SET convergence_id="
            "(SELECT id FROM kala_convergence WHERE contact_uuid=?) "
            "WHERE convergence_id="
            "(SELECT id FROM kala_convergence WHERE contact_uuid=?)",
            (op["to_uuid"], op["from_uuid"]))
    elif t == "set_flag":
        db.execute("INSERT OR REPLACE INTO rebuild_flags (contact_uuid, flag, "
                   "detail) VALUES (?,?,?)",
                   (op["contact_uuid"], op["flag"], op.get("detail", "")))
    elif t == "clear_flag":
        db.execute("DELETE FROM rebuild_flags WHERE contact_uuid=? AND flag=?",
                   (op["contact_uuid"], op["flag"]))
    else:
        raise ValueError(f"unknown op {t}")
    db.commit()


def run_rebuild(db, candidates=None, generation=GENERATION, adjudications=None,
                interrupt_after=None, resume=False) -> list:
    """Five-rule rebuild with journaled, resumable application (D-R5-1 rule 5).
    interrupt_after=N simulates a crash after N applied ops; resume=True
    replays the journaled decisions and applies only the unapplied remainder —
    exactly-once effects. `candidates` is not needed on resume."""
    if resume:
        run_id, ops = _load_journaled_decisions(db)
    else:
        run_id = db.execute("SELECT COALESCE(MAX(run_id),0)+1 FROM rebuild_journal"
                            ).fetchone()[0]
        ops = compute_decisions(db, candidates or [], generation,
                                adjudications or {})
        _journal(db, run_id, -1, "decisions",
                 {"ops": ops, "generation": generation, "run_id": run_id})
    applied = {r["op_index"] for r in db.execute(
        "SELECT op_index FROM rebuild_journal WHERE applied=1 AND op_index>=0 "
        "AND run_id=?", (run_id,))}
    done = 0
    for i, op in enumerate(ops):
        if i in applied:
            continue
        _apply_op(db, op, generation)
        _journal(db, run_id, i, op["op"], op)
        done += 1
        if interrupt_after is not None and done >= interrupt_after:
            raise RuntimeError(
                f"simulated crash after {done} applied op(s) "
                f"({len(ops) - i - 1} remaining)")
    return ops


# ------------------------------------------------------------- fixture tools

def add_obstruction(db, conv_id, note):
    db.execute("INSERT INTO kala_obstruction (convergence_id, note) VALUES (?,?)",
               (conv_id, note))
    db.commit()


def add_darshana(db, conv_id, note):
    db.execute("INSERT INTO kala_darshana (convergence_id, note) VALUES (?,?)",
               (conv_id, note))
    db.commit()


def add_claim(db, conv_id, claim_content: dict, exposure="30y",
              outcome=b"", notes=b"") -> int:
    cur = db.execute(
        "INSERT INTO kala_bhavishya (convergence_id, claim_content, version, "
        "exposure, outcome_recorded, outcome_notes) VALUES (?,?,1,?,?,?)",
        (conv_id, I.canonical_json(claim_content), exposure, outcome, notes))
    db.commit()
    return cur.lastrowid


def add_anchor(db, conv_id, anchor_content: dict) -> int:
    cur = db.execute(
        "INSERT INTO phala_anchors (convergence_id, anchor_content) VALUES (?,?)",
        (conv_id, I.canonical_json(anchor_content)))
    db.commit()
    return cur.lastrowid


def add_suddha(db, anchor_id, note):
    db.execute("INSERT INTO phala_suddha_sodhana (anchor_id, note) VALUES (?,?)",
               (anchor_id, note))
    db.commit()


def add_muhurta(db, anchor_id, note):
    db.execute("INSERT INTO phala_muhurta (anchor_id, note) VALUES (?,?)",
               (anchor_id, note))
    db.commit()


def add_mitigation(db, anchor_id, note):
    db.execute("INSERT INTO phala_mitigation (anchor_id, note) VALUES (?,?)",
               (anchor_id, note))
    db.commit()


def add_phaladesa(db, top_anchor_id, note):
    cur = db.execute(
        "INSERT INTO phala_phaladesa (top_anchor_id, note) VALUES (?,?)",
        (top_anchor_id, note))
    db.commit()
    return cur.lastrowid


def conv_row(db, contact_uuid):
    return db.execute("SELECT * FROM kala_convergence WHERE contact_uuid=?",
                      (contact_uuid,)).fetchone()


def claims_of(db, contact_uuid):
    return [dict(r) for r in db.execute(
        "SELECT b.* FROM kala_bhavishya b JOIN kala_convergence c "
        "ON b.convergence_id=c.id WHERE c.contact_uuid=?", (contact_uuid,))]


def rel_count(db, old=None, new=None, rtype=None) -> int:
    q, args = "SELECT count(*) FROM contact_relations WHERE 1=1", []
    if old is not None:
        q += " AND old_contact_uuid=?"; args.append(old)
    if new is not None:
        q += " AND new_contact_uuid=?"; args.append(new)
    if rtype is not None:
        q += " AND relation_type=?"; args.append(rtype)
    return db.execute(q, args).fetchone()[0]


def flag_present(db, contact_uuid, flag) -> bool:
    return db.execute("SELECT 1 FROM rebuild_flags WHERE contact_uuid=? AND flag=?",
                      (contact_uuid, flag)).fetchone() is not None
