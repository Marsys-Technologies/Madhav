"""ledger_r81_migration.py — R80/R81 (NIKASHA_CHANGE_REGISTER_v2_0.md, D4 ruling).

R80: adds `superseded_by` to the `_schema` row's own field-list documentation, so folding a
duplicate sets it on the thinner (superseded) row while the ledger stays append-only.
`emit_gaps()` (asset_census.py) already reads and honours `superseded_by` at runtime (an
"ever_superseded" row is never resurrected) — R80 is documentation catching up to a mechanism the
census already implements, not a behaviour change.

R81 (added in the next commit): the reviewed migration folding the 11 hand<->census overlap pairs
measured in T5_LEDGER_DRIFT.md §A.

Both operations are pure functions proven idempotent on a COPY (this module never opens the real
ledger itself — the caller decides which file to point at) before either is ever run against the
real `00_ARCHITECTURE/control/asset_gaps.jsonl`. See __tests__/test_r80_schema_superseded_by_field.py
and __tests__/test_r81_ledger_overlap_fold.py.
"""
from __future__ import annotations

import json

_FIELDS_ANCHOR = "gate, state (OPEN|IN_PROGRESS|CLOSED|WITHDRAWN), ts."
_FIELDS_REPLACEMENT = (
    "gate, state (OPEN|IN_PROGRESS|CLOSED|WITHDRAWN), ts, superseded_by (optional, R80)."
)
_SUPERSEDED_BY_CLAUSE = (
    " `superseded_by` (R80): set on a row whose identity has been folded into another — the row "
    "is never edited or deleted (append-only), but the gap_id it names carries the fold going "
    "forward and the superseded row's own identity is never resurrected by a later measurement "
    "(emit_gaps() already enforces this at runtime, across the id's whole history, not only its "
    "latest row — F5, A_REVIEW.md)."
)


def add_superseded_by_to_schema_doc(doc: str) -> str:
    """Idempotent: inserts `superseded_by` into the Fields: list (right after `gate, state (...),
    ts.`) and appends `_SUPERSEDED_BY_CLAUSE`, unless the field is already documented — running
    this twice on its own output makes no further change."""
    if "superseded_by" in doc:
        return doc
    if _FIELDS_ANCHOR not in doc:
        raise ValueError("schema doc's Fields: list has drifted — expected anchor text not found; "
                          "review before migrating")
    return doc.replace(_FIELDS_ANCHOR, _FIELDS_REPLACEMENT, 1) + _SUPERSEDED_BY_CLAUSE


def migrate_schema_line(schema_row: dict) -> dict:
    """Returns a NEW dict (never mutates the input) with `_doc` migrated. Idempotent: applying
    this to its own output is a no-op (the returned dict compares equal)."""
    row = dict(schema_row)
    row["_doc"] = add_superseded_by_to_schema_doc(row["_doc"])
    return row


def is_schema_row(row: dict) -> bool:
    return row.get("asset") == "_schema"


# ─────────────────────────── R81: the 11 hand<->census overlap pairs (T5_LEDGER_DRIFT.md §A) ───────────────────────────
#
# D4 ruling (adopted 2026-09-27): the derived id is `<asset>-<Gate>.<check>` — never a hand
# G-numbered id kept as the survivor. Five pairs (1/2/3/5/6 below) already have a matching
# derived-form id sitting right there as the census's own row (same criterion, or the criterion
# the family alias resolves to) — that id is preserved, its `what` enriched with the hand row's
# extra detail, and the OLD hand id is superseded onto it. The other six (4/7/9/10/11 specific;
# 8 partial) mint a genuinely NEW derived id from the hand row's own, more specific criterion
# (already registered in CRITERION_REGISTRY with detector NONE — R78), superseding BOTH old ids
# (hand and, where one was folded, census) onto it. Group 8 is the one partial overlap: per D4,
# `bg_panchanga-G01` becomes its own criterion `Earn.service_state`, never folded onto a timing
# id — its census siblings (`Earn.build_record`, `Cost.baseline`) are untouched, unsuperseded.
# E6.4 amendment (SS N-97(4)): that rule is superseded for the four info prefixes (Cost., Count., Complete., Reach.): once the E6.4
# migration (ledger_e6_4_info_rekey.py) is applied, `bg_panchanga-Cost.baseline` is superseded BY its `#info` id. The R81 fold itself still
# never touches it; `bg_panchanga-Earn.build_record` (a gate criterion) stays unsuperseded.
#
# The four family aliases named in R79/D4 (Vocab.rule1.alias->Vocab.alias,
# Dens.density_contract->Dens.served, Carr.D1|D2|D3->Carr.detector, Completeness.*->Complete.*)
# are consumed here, once, as the crosswalk between a hand row's pre-registry criterion string and
# its now-registered form — never as a runtime alias table (nothing outside this migration ever
# resolves one criterion string to another).
OVERLAP_PAIRS = [
    # pair 1 — bg_ontology build record / earn (same criterion already)
    dict(n=1, asset="bg_ontology", criterion="Earn.build_record",
         hand_old_id="bg_ontology-G02", census_old_id="bg_ontology-Earn.build_record",
         winner_is_census_id=True),
    # pair 2 — bg_ontology alias sets (Vocab.rule1.alias -> Vocab.alias, family alias)
    dict(n=2, asset="bg_ontology", criterion="Vocab.alias",
         hand_old_id="bg_ontology-G07", census_old_id="bg_ontology-Vocab.alias",
         winner_is_census_id=True),
    # pair 3 — bg_ontology density contracts (Dens.density_contract -> Dens.served, family alias)
    dict(n=3, asset="bg_ontology", criterion="Dens.served",
         hand_old_id="bg_ontology-G10", census_old_id="bg_ontology-Dens.served",
         winner_is_census_id=True),
    # pair 4 — bg_ontology carrier/source-correspondence (Carr.D1, distinct from Carr.detector)
    dict(n=4, asset="bg_ontology", criterion="Carr.D1",
         hand_old_id="bg_ontology-G05", census_old_id="bg_ontology-Carr.detector",
         winner_is_census_id=False),
    # pair 5 — bg_ephemeris build record (same criterion already)
    dict(n=5, asset="bg_ephemeris", criterion="Earn.build_record",
         hand_old_id="bg_ephemeris-G03", census_old_id="bg_ephemeris-Earn.build_record",
         winner_is_census_id=True),
    # pair 6 — bg_ephemeris density contracts (family alias)
    dict(n=6, asset="bg_ephemeris", criterion="Dens.served",
         hand_old_id="bg_ephemeris-G05", census_old_id="bg_ephemeris-Dens.served",
         winner_is_census_id=True),
    # pair 7 — bg_ephemeris re-derivation detector (Carr.D3, distinct from Carr.detector)
    dict(n=7, asset="bg_ephemeris", criterion="Carr.D3",
         hand_old_id="bg_ephemeris-G02", census_old_id="bg_ephemeris-Carr.detector",
         winner_is_census_id=False),
    # pair 8 — bg_panchanga liveness/build signal (PARTIAL — never folded onto a timing id)
    dict(n=8, asset="bg_panchanga", criterion="Earn.service_state",
         hand_old_id="bg_panchanga-G01", census_old_id=None,
         winner_is_census_id=False),
    # pair 9 — bg_panchanga re-derivation detector (Carr.D3, distinct from Carr.detector)
    dict(n=9, asset="bg_panchanga", criterion="Carr.D3",
         hand_old_id="bg_panchanga-G02", census_old_id="bg_panchanga-Carr.detector",
         winner_is_census_id=False),
    # pair 10 — bg_rules source correspondence (Carr.D1, distinct from Carr.detector)
    dict(n=10, asset="bg_rules", criterion="Carr.D1",
         hand_old_id="bg_rules-G03", census_old_id="bg_rules-Carr.detector",
         winner_is_census_id=False),
    # pair 11 — bg_rules dasha_system_id never populated (Completeness.* -> Complete.*, family alias,
    # but D4 keeps the specific form distinct: Completeness.depth.dasha_link != Complete.depth)
    dict(n=11, asset="bg_rules", criterion="Completeness.depth.dasha_link",
         hand_old_id="bg_rules-G06", census_old_id="bg_rules-Complete.depth",
         winner_is_census_id=False),
]


def _latest_and_superseded(rows: list[dict]) -> tuple[dict[str, dict], set[str]]:
    """Same convention as asset_census.emit_gaps: last row in file order wins per gap_id;
    `superseded_by` is permanent once set on ANY row for a gid, across its whole history (F5)."""
    latest: dict[str, dict] = {}
    ever_superseded: set[str] = set()
    for r in rows:
        gid = r.get("gap_id")
        if not gid:
            continue
        latest[gid] = r
        if r.get("superseded_by"):
            ever_superseded.add(gid)
    return latest, ever_superseded


def _gap_id_for(asset: str, criterion: str) -> str:
    return f"{asset}-{criterion}"


def fold_overlap_pairs(rows: list[dict], ts: str) -> list[dict]:
    """Returns the list of NEW rows to APPEND (never mutates or removes anything from `rows`).
    Idempotent: a pair whose hand_old_id is already superseded (from a prior run) is skipped
    entirely, so running this against its own prior output produces an empty list.

    `ts` is the migration's own timestamp (ISO, matching the format the rest of the ledger uses),
    supplied by the caller so this function has no wall-clock dependency and is trivially testable.
    """
    latest, ever_superseded = _latest_and_superseded(rows)
    new_rows: list[dict] = []

    for pair in OVERLAP_PAIRS:
        hand_id = pair["hand_old_id"]
        if hand_id in ever_superseded:
            continue  # already migrated — idempotent no-op
        hand_row = latest.get(hand_id)
        if hand_row is None:
            raise KeyError(f"R81 pair {pair['n']}: expected hand row {hand_id!r} not found in the ledger")

        census_id = pair["census_old_id"]
        census_row = latest.get(census_id) if census_id else None
        if census_id and census_row is None:
            raise KeyError(f"R81 pair {pair['n']}: expected census row {census_id!r} not found in the ledger")

        final_criterion = pair["criterion"]
        final_id = census_id if pair["winner_is_census_id"] else _gap_id_for(pair["asset"], final_criterion)

        if census_row is not None:
            folded_what = (f"{hand_row['what']} || folded census measurement (R81, superseded "
                           f"{census_id}): {census_row['what']}")
        else:
            folded_what = hand_row["what"]  # pair 8: re-keyed, nothing folded in (partial overlap)

        # The surviving/updated row — append-only: a NEW line under `final_id`, carrying the
        # hand row's own annotations forward (D4: "hand change/owner/gate carried onto the new
        # row"), enriched with the folded measurement.
        new_rows.append(dict(
            asset=pair["asset"], gap_id=final_id, kind=hand_row.get("kind", "gap"),
            criterion=final_criterion, what=folded_what,
            change=hand_row.get("change", ""), detector=hand_row.get("detector", ""),
            owner=hand_row.get("owner", "asset_census"),
            gate=hand_row.get("gate", "this asset's certification"),
            state=hand_row.get("state", "OPEN"), ts=ts,
        ))

        # Supersede the old hand id, unless it IS the final id (never happens here — every pair's
        # hand id is a G-numbered id, never itself in derived <asset>-<Gate>.<check> form).
        if hand_id != final_id:
            superseded_hand = dict(hand_row)
            superseded_hand["superseded_by"] = final_id
            superseded_hand["ts"] = ts
            new_rows.append(superseded_hand)

        # Supersede the old census id too, unless it already IS the final id (the five pairs where
        # winner_is_census_id=True — that id is simply enriched above, not superseded).
        if census_row is not None and census_id != final_id:
            superseded_census = dict(census_row)
            superseded_census["superseded_by"] = final_id
            superseded_census["ts"] = ts
            new_rows.append(superseded_census)

    return new_rows
