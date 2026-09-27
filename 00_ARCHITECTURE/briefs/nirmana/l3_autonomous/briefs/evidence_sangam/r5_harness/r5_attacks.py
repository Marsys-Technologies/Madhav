"""The seven §6.3 preservation attacks on the R-5 disposable harness.

Each attack builds a fresh disposable DB (PRAGMA foreign_keys=ON), runs the
attack, and asserts the manifest-level outcome. Every attack returns a list of
(name, condition, detail) assertion triples; run_all_attacks() runs all seven.
Standalone: exits 0 iff every assertion holds.
"""

from __future__ import annotations

import sys

import r5_identity as I
import r5_harness as H

FRAME = I.frame_vector("LAHIRI", "SWIEPH", "J2000", "apparent_sidereal",
                       "MEAN_NODE", "PLACIDUS")
V = "sangam-m1v1"
CH = "CH-001"


# ---------------------------------------------------------------- fixtures

def cand_a(peak="2027-03-15"):
    return H.make_candidate(
        chart_id=CH, method_contract_version=V, graha="Saturn",
        target_fact_id="F-MOON-001", directed_angle_deg=180, frame_vector=FRAME,
        orb_deg=5.0, contact_kind="exact_contact", peak_date=peak,
        claim={"peak_phase": "exact", "factors": ["lord_transit", "benefic_dristi"]},
        exposure="30y")


def cand_b(peak="2027-06-01"):
    return H.make_candidate(
        chart_id=CH, method_contract_version=V, graha="Jupiter",
        target_fact_id="F-SUN-002", directed_angle_deg=120, frame_vector=FRAME,
        orb_deg=6.0, contact_kind="exact_contact", peak_date=peak,
        claim={"peak_phase": "exact", "factors": ["C9_current"]}, exposure="30y")


def cand_c(peak="2027-05-05"):
    return H.make_candidate(
        chart_id=CH, method_contract_version=V, graha="Mars",
        target_fact_id="F-MARS-004", directed_angle_deg=90, frame_vector=FRAME,
        orb_deg=5.0, contact_kind="exact_contact", peak_date=peak,
        claim={"peak_phase": "exact", "factors": ["lord_transit"]}, exposure="30y")


def build_world(db, with_c=False):
    """Two contacts with full dependent chains and issued claims/outcomes."""
    A, B = cand_a(), cand_b()
    idA = H.insert_contact(db, A)
    idB = H.insert_contact(db, B)
    H.add_obstruction(db, idA, "Saturn-Moon vedha active at peak")
    H.add_obstruction(db, idB, "Jupiter-Sun current active")
    H.add_darshana(db, idA, "peak visible in darshana window")
    cA1 = H.add_claim(db, idA, {"text": "Saturn opp Moon: pressure window",
                                "route": "E1-moon-vedha"},
                      outcome=b"hit", notes=b"observed within +/-5d of peak")
    cA2 = H.add_claim(db, idA, {"text": "Saturn opp Moon: second issued claim",
                                "route": "E1-moon-vedha"},
                      outcome=b"miss", notes=b"no event inside window")
    cB1 = H.add_claim(db, idB, {"text": "Jupiter trine Sun: support window",
                                "route": "E1-graha-drishti"},
                      outcome=b"ambiguous", notes=b"partial witness only")
    aA = H.add_anchor(db, idA, {"signal": "career", "domain": "10th"})
    aB = H.add_anchor(db, idB, {"signal": "wealth", "domain": "11th"})
    H.add_suddha(db, aA, "sodhana applied to career anchor")
    H.add_muhurta(db, aA, "muhurta elects anchor window")
    H.add_mitigation(db, aA, "mitigation bound to career anchor")
    ph = H.add_phaladesa(db, aA, "phaladesa verdict on top anchor")
    ids = {"A": A["contact_uuid"], "B": B["contact_uuid"], "idA": idA, "idB": idB,
           "cA1": cA1, "cA2": cA2, "cB1": cB1, "aA": aA, "aB": aB, "ph": ph}
    if with_c:
        C = cand_c()
        ids["idC"] = H.insert_contact(db, C)
        ids["cC1"] = H.add_claim(db, ids["idC"],
                                 {"text": "Mars square Mars: drive window",
                                  "route": "E1-graha-drishti"},
                                 outcome=b"hit", notes=b"confirmed")
        ids["C"] = C["contact_uuid"]
    return ids


# ------------------------------------------------------------- attack 1

def attack_1_empty_rebuild():
    """Empty rebuild — zero candidates: every original claim/binding/content
    byte-identical; nothing orphaned."""
    db = H.fresh_db()
    ids = build_world(db)
    before = I.manifest_digest(db)
    H.run_rebuild(db, [])          # zero candidates, empty partition = explicit
    after = I.manifest_digest(db)
    m = I.manifest(db)
    orphans = db.execute(
        "SELECT (SELECT count(*) FROM kala_obstruction o LEFT JOIN "
        "kala_convergence c ON o.convergence_id=c.id WHERE c.id IS NULL)"
        "+ (SELECT count(*) FROM kala_darshana o LEFT JOIN kala_convergence c "
        "ON o.convergence_id=c.id WHERE c.id IS NULL)"
        "+ (SELECT count(*) FROM phala_anchors o LEFT JOIN kala_convergence c "
        "ON o.convergence_id=c.id WHERE c.id IS NULL)"
        "+ (SELECT count(*) FROM phala_suddha_sodhana o LEFT JOIN phala_anchors a "
        "ON o.anchor_id=a.id WHERE a.id IS NULL)"
        "+ (SELECT count(*) FROM phala_muhurta o LEFT JOIN phala_anchors a "
        "ON o.anchor_id=a.id WHERE o.anchor_id IS NOT NULL AND a.id IS NULL)"
        "+ (SELECT count(*) FROM phala_mitigation o LEFT JOIN phala_anchors a "
        "ON o.anchor_id=a.id WHERE o.anchor_id IS NOT NULL AND a.id IS NULL)"
        "+ (SELECT count(*) FROM phala_phaladesa p LEFT JOIN phala_anchors a "
        "ON p.top_anchor_id=a.id WHERE p.top_anchor_id IS NOT NULL AND a.id IS NULL)"
    ).fetchone()[0]
    return [
        ("empty rebuild leaves every claim/binding/content byte-identical",
         before == after, "manifest digest unchanged"),
        ("no relations published for an empty rebuild",
         H.rel_count(db) == 0, f"relations={H.rel_count(db)}"),
        ("nothing orphaned (CASCADE children, SET NULL parents, FK-free anchor)",
         orphans == 0, f"orphaned references={orphans}"),
        ("no detached claims/bindings", m["__detached__"] == {
            "kala_bhavishya": [], "phala_muhurta": [], "phala_mitigation": [],
            "phala_phaladesa": []}, "detached buckets empty"),
        ("FK-free phaladesa resolved semantically to anchor content",
         len(m[f"contact:{ids['A']}"]["bindings"]["phala_phaladesa"]) == 1
         and "resolved_anchor_content" in
         m[f"contact:{ids['A']}"]["bindings"]["phala_phaladesa"][0],
         "top_anchor_id resolved by anchor content, not surrogate id"),
    ]


# ------------------------------------------------------------- attack 2

def attack_2_moved_date():
    """Moved date — the algorithm moves a peak 3 days within the same contract
    version: same contact_uuid, content version+1, supersession edge, claim
    content bytes unchanged, binding intact."""
    db = H.fresh_db()
    ids = build_world(db)
    A = ids["A"]
    before = I.manifest(db)
    moved = cand_a(peak="2027-03-18")      # +3 days, identity tuple unchanged
    assert moved["contact_uuid"] == A, "peak_date must not enter identity"
    H.run_rebuild(db, [moved])
    row = H.conv_row(db, A)
    after = I.manifest(db)
    claim_keys = [k for k in before if k.startswith("claim:")]
    claims_unchanged = all(before[k] == after[k] for k in claim_keys)
    bindings_intact = (before[f"contact:{A}"]["bindings"]
                       == after[f"contact:{A}"]["bindings"])
    r = {"id": 7, "computed_at": "t1", "generation_head_id": 3}
    r2 = {"id": 8, "computed_at": "t2", "generation_head_id": 9,
          "peak_date": "2027-03-18", "content_hash": "x"}
    return [
        ("same contact_uuid across a 3-day peak move", row is not None
         and row["contact_uuid"] == A, "uuid stable"),
        ("content version bumped +1", row["content_version"] == 2,
         f"version={row['content_version']}"),
        ("supersession edge exists (self-successor)",
         H.rel_count(db, old=A, new=A, rtype="supersedes") == 1,
         f"supersedes edges={H.rel_count(db, old=A, new=A, rtype='supersedes')}"),
        ("issued claim content bytes unchanged",
         claims_unchanged, f"{len(claim_keys)} claims compared"),
        ("every dependent binding intact", bindings_intact,
         "obstruction/darshana/anchors/phaladesa bindings identical"),
        ("exposure retained on contact and claims",
         after[f"contact:{A}"]["exposure"] == "30y"
         and all(after[k]["exposure"] == "30y" for k in claim_keys), "30y"),
        ("canonical field-exclusion list is load-bearing (RRV-09)",
         I.canonical_serialize(r) == I.canonical_serialize(
             {"id": 999, "computed_at": "t9",
              "generation_head_id": 1})
         and I.canonical_serialize(r) != I.canonical_serialize(r2),
         "id/computed_at/generation-head-pointer excluded; content fields kept"),
    ]


# ------------------------------------------------------------- attack 3

def attack_3_one_to_many_split():
    """One-to-many split — one contact becomes two candidates: both exist,
    split_from edges from the original, original withdrawn with reason, its
    claims mapped to the declared authorized successor only."""
    db = H.fresh_db()
    ids = build_world(db)
    A, idA = ids["A"], ids["idA"]
    c1 = H.make_candidate(chart_id=CH, method_contract_version=V, graha="Saturn",
                          target_fact_id="F-MOON-001", directed_angle_deg=180,
                          frame_vector=FRAME, orb_deg=4.5,
                          contact_kind="exact_contact", peak_date="2027-03-14",
                          claim={"peak_phase": "ingress", "factors": ["lord_transit"]},
                          exposure="30y")
    c2 = H.make_candidate(chart_id=CH, method_contract_version=V, graha="Saturn",
                          target_fact_id="F-MOON-001", directed_angle_deg=180,
                          frame_vector=FRAME, orb_deg=5.5,
                          contact_kind="exact_contact", peak_date="2027-03-16",
                          claim={"peak_phase": "exact", "factors": ["benefic_dristi"]},
                          exposure="30y")
    H.run_rebuild(db, [], adjudications={"splits": {A: {
        "children": [c1, c2], "successor": c2["contact_uuid"],
        "reason": "station loop resolved into ingress + exact child"}}})
    old = H.conv_row(db, A)
    succ_claims = H.claims_of(db, c2["contact_uuid"])
    other_claims = H.claims_of(db, c1["contact_uuid"])
    m = I.manifest(db)
    return [
        ("both split candidates exist",
         H.conv_row(db, c1["contact_uuid"]) is not None
         and H.conv_row(db, c2["contact_uuid"]) is not None, "2 new rows"),
        ("split_from edges from the original (one per child)",
         H.rel_count(db, old=A, rtype="split_from") == 2,
         f"split_from={H.rel_count(db, old=A, rtype='split_from')}"),
        ("original withdrawn with recorded reason",
         old["status"] == "withdrawn"
         and "station loop" in (old["withdrawal_reason"] or ""), old["status"]),
        ("claims mapped to the declared authorized successor only",
         len(succ_claims) == 2 and {c["id"] for c in succ_claims}
         == {ids["cA1"], ids["cA2"]}, f"successor holds {len(succ_claims)} claims"),
        ("non-successor child holds none of the original claims",
         len(other_claims) == 0, f"other child holds {len(other_claims)}"),
        ("successor mapping published in the manifest",
         any(r["new_contact_uuid"] == c2["contact_uuid"]
             and r["relation_type"] == "split_from"
             for r in m[f"contact:{A}"]["successor_mappings"]), "manifest edge"),
    ]


# ------------------------------------------------------------- attack 4

def attack_4_many_to_one_merge():
    """Many-to-one merge — two originals become one candidate: merged_into
    edges, both originals withdrawn, claims of BOTH mapped to the successor,
    no claim orphaned."""
    db = H.fresh_db()
    ids = build_world(db)
    A, B = ids["A"], ids["B"]
    merged = H.make_candidate(chart_id=CH, method_contract_version=V,
                              graha="Jupiter-Saturn", target_fact_id="F-SUN-002",
                              directed_angle_deg=120, frame_vector=FRAME,
                              orb_deg=6.0, contact_kind="exact_contact",
                              peak_date="2027-06-02",
                              claim={"peak_phase": "exact",
                                     "factors": ["C9_current", "lord_transit"]},
                              exposure="30y")
    H.run_rebuild(db, [], adjudications={"merges": {merged["contact_uuid"]: {
        "candidate": merged, "originals": [A, B],
        "reason": "duplicate geometry at different orbs merged"}}})
    rA, rB = H.conv_row(db, A), H.conv_row(db, B)
    mclaims = H.claims_of(db, merged["contact_uuid"])
    all_claims = db.execute("SELECT * FROM kala_bhavishya").fetchall()
    bound = sum(1 for c in all_claims if c["convergence_id"] is not None)
    return [
        ("merged candidate exists", H.conv_row(db, merged["contact_uuid"])
         is not None, "1 new row"),
        ("merged_into edges from both originals",
         H.rel_count(db, old=A, new=merged["contact_uuid"], rtype="merged_into") == 1
         and H.rel_count(db, old=B, new=merged["contact_uuid"],
                         rtype="merged_into") == 1, "2 edges"),
        ("both originals withdrawn with reason",
         rA["status"] == "withdrawn" and rB["status"] == "withdrawn"
         and rA["withdrawal_reason"] and rB["withdrawal_reason"], "withdrawn"),
        ("claims of BOTH originals mapped to the successor",
         len(mclaims) == 3 and {c["id"] for c in mclaims}
         == {ids["cA1"], ids["cA2"], ids["cB1"]},
         f"successor holds {len(mclaims)} claims"),
        ("no claim orphaned (every claim bound to a live contact)",
         bound == len(all_claims), f"{bound}/{len(all_claims)} bound"),
    ]


# ------------------------------------------------------------- attack 5

def attack_5_ambiguous_match():
    """Ambiguous match — one candidate plausibly matches two originals (same
    target fact, angle, frame, overlapping orb): NO automatic reattachment;
    both originals retained; their claims still bound; ambiguous flag present;
    a re-run after adjudication (declared successor) reattaches exactly then."""
    def ambiguous_world():
        db = H.fresh_db()
        a1 = H.make_candidate(chart_id=CH, method_contract_version=V,
                              graha="Mercury", target_fact_id="F-MERC-003",
                              directed_angle_deg=60, frame_vector=FRAME,
                              orb_deg=5.0, contact_kind="exact_contact",
                              peak_date="2027-01-10",
                              claim={"peak_phase": "exact", "factors": ["f1"]})
        a2 = H.make_candidate(chart_id=CH, method_contract_version=V,
                              graha="Mercury", target_fact_id="F-MERC-003",
                              directed_angle_deg=60, frame_vector=FRAME,
                              orb_deg=5.5, contact_kind="exact_contact",
                              peak_date="2027-01-12",
                              claim={"peak_phase": "exact", "factors": ["f2"]})
        assert a1["contact_uuid"] != a2["contact_uuid"]
        i1 = H.insert_contact(db, a1)
        i2 = H.insert_contact(db, a2)
        k1 = H.add_claim(db, i1, {"text": "Mercury sextile: window one"},
                         outcome=b"hit", notes=b"n1")
        k2 = H.add_claim(db, i2, {"text": "Mercury sextile: window two"},
                         outcome=b"miss", notes=b"n2")
        return db, a1, a2, k1, k2

    # candidate overlaps BOTH originals (|11-10|<=5+4, |11-12|<=5.5+4)
    amb = H.make_candidate(chart_id=CH, method_contract_version=V,
                           graha="Mercury", target_fact_id="F-MERC-003",
                           directed_angle_deg=60, frame_vector=FRAME,
                           orb_deg=4.0, contact_kind="exact_contact",
                           peak_date="2027-01-11",
                           claim={"peak_phase": "exact", "factors": ["f3"]})
    out = []
    db, a1, a2, k1, k2 = ambiguous_world()
    u1, u2 = a1["contact_uuid"], a2["contact_uuid"]
    H.run_rebuild(db, [amb])                     # NO adjudication declared
    r1, r2 = H.conv_row(db, u1), H.conv_row(db, u2)
    out += [
        ("no automatic reattachment on ambiguity",
         H.conv_row(db, amb["contact_uuid"]) is None
         and H.rel_count(db, rtype="reattached") == 0,
         f"reattached edges={H.rel_count(db, rtype='reattached')}"),
        ("both originals retained (active)",
         r1["status"] == "active" and r2["status"] == "active", "retained"),
        ("claims still bound to their original contacts",
         [c["id"] for c in H.claims_of(db, u1)] == [k1]
         and [c["id"] for c in H.claims_of(db, u2)] == [k2], "claims unmoved"),
        ("ambiguous_needs_adjudication flag present on both originals",
         H.flag_present(db, u1, "ambiguous_needs_adjudication")
         and H.flag_present(db, u2, "ambiguous_needs_adjudication"), "flagged"),
    ]
    # re-run AFTER adjudication: declared successor = original 1
    H.run_rebuild(db, [amb], adjudications={"reattachments":
                                            {amb["contact_uuid"]: u1}})
    r1b, r2b = H.conv_row(db, u1), H.conv_row(db, u2)
    out += [
        ("adjudicated re-run reattaches the declared successor",
         r1b["status"] == "withdrawn"
         and [c["id"] for c in H.claims_of(db, amb["contact_uuid"])] == [k1],
         "exactly original 1's claims moved"),
        ("the other original stays active with its claims",
         r2b["status"] == "active"
         and [c["id"] for c in H.claims_of(db, u2)] == [k2], "untouched"),
        ("exactly one reattached edge, published",
         H.rel_count(db, rtype="reattached") == 1, "1 edge"),
    ]
    return out


# ------------------------------------------------------------- attack 6

def attack_6_interrupted_resumed():
    """Interrupted/resumed rebuild — journal replay: kill mid-rebuild, resume,
    final manifest byte-identical to the uninterrupted run; no double effects."""
    candidates_maker = lambda: [cand_a(peak="2027-03-18"),   # supersede
                                cand_d(),                    # new addition
                                cand_e()]                    # decisive reattach
    adjud = lambda: {"splits": {cand_b()["contact_uuid"]: {
        "children": [cand_b1(), cand_b2()],
        "successor": cand_b2()["contact_uuid"],
        "reason": "station loop split"}}}

    db1 = H.fresh_db()
    build_world(db1, with_c=True)
    ops = H.compute_decisions(db1, candidates_maker(), H.GENERATION, adjud())
    try:
        H.run_rebuild(db1, candidates_maker(), adjudications=adjud(),
                      interrupt_after=5)
        interrupted = False
    except RuntimeError:
        interrupted = True
    H.run_rebuild(db1, resume=True)
    resumed = I.manifest_digest(db1)

    db2 = H.fresh_db()
    build_world(db2, with_c=True)
    H.run_rebuild(db2, candidates_maker(), adjudications=adjud())
    uninterrupted = I.manifest_digest(db2)

    def state_counts(db):
        return {
            "relations": db.execute("SELECT count(*) FROM contact_relations").fetchone()[0],
            "withdrawn": db.execute("SELECT count(*) FROM kala_convergence "
                                    "WHERE status='withdrawn'").fetchone()[0],
            "claims": db.execute("SELECT count(*) FROM kala_bhavishya").fetchone()[0],
            "flags": db.execute("SELECT count(*) FROM rebuild_flags").fetchone()[0],
        }
    j = db1.execute("SELECT count(*) c, count(DISTINCT op_index) d "
                    "FROM rebuild_journal WHERE op_index>=0").fetchone()
    return [
        ("the simulated crash actually fired mid-rebuild", interrupted, "killed"),
        ("resumed manifest byte-identical to the uninterrupted run",
         resumed == uninterrupted, f"{len(ops)} ops compared"),
        ("no double effects (relations/withdrawals/claims counted)",
         state_counts(db1) == state_counts(db2),
         f"resumed={state_counts(db1)} uninterrupted={state_counts(db2)}"),
        ("journal replay applied each op exactly once",
         j["c"] == len(ops) and j["d"] == len(ops),
         f"journaled {j['c']}/{len(ops)} distinct {j['d']}/{len(ops)}"),
    ]


def cand_d():
    return H.make_candidate(chart_id=CH, method_contract_version=V,
                            graha="Venus", target_fact_id="F-VEN-005",
                            directed_angle_deg=0, frame_vector=FRAME,
                            orb_deg=3.0, contact_kind="ingress",
                            peak_date="2027-08-20",
                            claim={"peak_phase": "ingress", "factors": ["f"]})


def cand_e():
    """Same target/angle/frame as world contact C, new orb -> decisive single
    geometry match (rule 3 positive path exercised inside the mix)."""
    return H.make_candidate(chart_id=CH, method_contract_version=V,
                            graha="Mars", target_fact_id="F-MARS-004",
                            directed_angle_deg=90, frame_vector=FRAME,
                            orb_deg=4.0, contact_kind="exact_contact",
                            peak_date="2027-05-06",
                            claim={"peak_phase": "exact", "factors": ["f"]})


def cand_b1():
    return H.make_candidate(chart_id=CH, method_contract_version=V,
                            graha="Jupiter", target_fact_id="F-SUN-002",
                            directed_angle_deg=120, frame_vector=FRAME,
                            orb_deg=5.5, contact_kind="exact_contact",
                            peak_date="2027-05-30",
                            claim={"peak_phase": "ingress", "factors": ["f"]})


def cand_b2():
    return H.make_candidate(chart_id=CH, method_contract_version=V,
                            graha="Jupiter", target_fact_id="F-SUN-002",
                            directed_angle_deg=120, frame_vector=FRAME,
                            orb_deg=6.5, contact_kind="exact_contact",
                            peak_date="2027-06-02",
                            claim={"peak_phase": "exact", "factors": ["f"]})


# ------------------------------------------------------------- attack 7

def attack_7_unchanged_count_content_swap():
    """Unchanged-count content-swap — rebuild produces the SAME row count with
    one claim's content secretly altered (same byte length): the count/hash
    design misses it; the manifest comparison catches the per-id difference."""
    db = H.fresh_db()
    ids = build_world(db)
    before = I.manifest(db)

    def naive_counts(d):
        return ({t: d.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
                 for t in ("kala_convergence", "kala_bhavishya",
                           "kala_obstruction", "kala_darshana", "phala_anchors",
                           "phala_suddha_sodhana", "phala_muhurta",
                           "phala_mitigation", "phala_phaladesa")},
                d.execute("SELECT sum(length(claim_content)), count(*) "
                          "FROM kala_bhavishya").fetchone())

    n_before = naive_counts(db)
    H.run_rebuild(db, [cand_a()])                # benign no-op rebuild
    # the attack: one claim's content altered mid-generation, same length
    row = db.execute("SELECT claim_content FROM kala_bhavishya WHERE id=?",
                     (ids["cA1"],)).fetchone()
    tampered = row["claim_content"].replace("pressure", "pleasure", 1)
    assert len(tampered) == len(row["claim_content"])
    db.execute("UPDATE kala_bhavishya SET claim_content=? WHERE id=?",
               (tampered, ids["cA1"]))
    db.commit()

    n_after = naive_counts(db)
    diffs = I.compare_manifests(before, I.manifest(db))
    return [
        ("row counts AND total claim bytes unchanged (the naive check misses it)",
         n_before == n_after, f"naive snapshot identical: {n_before == n_after}"),
        ("manifest comparison fires exactly one per-id diff",
         len(diffs) == 1, f"diffs={[(k, f) for k, f, _, _ in diffs]}"),
        ("the diff names the tampered claim id and the claim_content field",
         len(diffs) == 1 and diffs[0][0] == f"claim:{ids['cA1']}"
         and diffs[0][1] == "claim_content",
         f"key={diffs[0][0]} field={diffs[0][1]}" if diffs else "no diff"),
        ("outcome bytes and bindings of the tampered claim are still compared",
         len(diffs) == 1 and before[f"claim:{ids['cA1']}"]["outcome_recorded"]
         == I.manifest(db)[f"claim:{ids['cA1']}"]["outcome_recorded"]
         and "bound" not in diffs[0][1], "verbatim outcome bytes intact"),
    ]


# ------------------------------------------------------------------ runner

ATTACKS = [
    ("attack 1 — empty rebuild", attack_1_empty_rebuild),
    ("attack 2 — moved date (same contract version)", attack_2_moved_date),
    ("attack 3 — one-to-many split", attack_3_one_to_many_split),
    ("attack 4 — many-to-one merge", attack_4_many_to_one_merge),
    ("attack 5 — ambiguous match (fail-closed)", attack_5_ambiguous_match),
    ("attack 6 — interrupted/resumed rebuild", attack_6_interrupted_resumed),
    ("attack 7 — unchanged-count content-swap", attack_7_unchanged_count_content_swap),
]


def run_all_attacks():
    return [(name, fn()) for name, fn in ATTACKS]


if __name__ == "__main__":
    ok = True
    for name, assertions in run_all_attacks():
        print("=" * 78 + f"\n{name}\n" + "=" * 78)
        for pname, cond, detail in assertions:
            print(f"  {'PASS' if cond else 'FAIL'}  {pname}"
                  + (f"  — {detail}" if detail else ""))
            ok = ok and cond
    print(f"VERDICT: {'PASS' if ok else 'FAIL'}")
    sys.exit(0 if ok else 1)
