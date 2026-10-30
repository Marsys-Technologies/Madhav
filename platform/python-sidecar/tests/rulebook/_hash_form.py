"""Synthetic hash-form (schema v1.2 quote_form "sha256") conversion for tests.

Mirrors the harness rule (CR-006 §2.5): tokens are [a-z0-9]+ | Devanagari runs over the
lower-cased passage; a witness is {passage_id, token_start, token_end} (end exclusive);
quote_sha256 is sha256 of the witness tokens joined by single spaces. The "bank" here is
built from the card's own invented quote, so no real passage text is involved.
"""

from __future__ import annotations

import copy
import hashlib
import re
from typing import Any, Callable, Dict, List, Mapping, Tuple

TOKEN_RE = re.compile(r"[a-z0-9]+|[ऀ-ॿ]+")


def tokens(text: str) -> List[str]:
    return TOKEN_RE.findall(text.lower())


def _find(hay: List[str], needle: List[str]) -> int:
    for i in range(len(hay) - len(needle) + 1):
        if hay[i : i + len(needle)] == needle:
            return i
    raise ValueError(f"term not located: {needle}")


def to_hash_form(card: Mapping[str, Any]) -> Tuple[Dict[str, Any], Callable[[Mapping[str, Any]], str]]:
    """Return (hash-form card, witness_text resolver over a synthetic bank of the card's quotes)."""
    card = copy.deepcopy(dict(card))
    card["schema_version"] = "rule-card-v1.2"
    bank: Dict[str, List[str]] = {}

    def hash_cite(cite: Dict[str, Any]) -> None:
        pid = cite["passage_ids"][0]
        toks = tokens(cite.pop("quote"))
        bank.setdefault(pid, toks)
        w = {"passage_id": pid, "token_start": 0, "token_end": len(toks)}
        cite.update(quote_form="sha256", quote_sha256=hashlib.sha256(" ".join(toks).encode()).hexdigest(), witnesses=[w])

    cite = card["field1_citation"]
    pid = cite["passage_ids"][0]
    hash_cite(cite)

    f3 = card.get("field3_reference_frame") or {}
    fc = f3.get("frame_citation")
    if fc and fc.get("quote"):
        hash_cite(fc)
    frame_pids = list((fc or {}).get("passage_ids") or [])

    def witness(term: str, pids: List[str] = ()) -> Dict[str, Any]:
        t = tokens(term)
        for p in list(pids) + [pid]:
            try:
                s = _find(bank[p], t)
            except (ValueError, KeyError):
                continue
            return {"passage_id": p, "token_start": s, "token_end": s + len(t)}
        raise ValueError(f"term not located: {t}")

    ops = list(card.get("field5_typed_operands") or [])
    for exc in card.get("field6_exceptions") or []:
        ops.extend(exc.get("operands") or [])
    for op in ops:
        op["quote_terms"] = [witness(t) for t in op.get("quote_terms") or []]
    if f3.get("frame_terms"):
        f3["frame_terms"] = [witness(t, frame_pids) for t in f3["frame_terms"]]

    def witness_text(w: Mapping[str, Any]) -> str:
        return " ".join(bank[w["passage_id"]][w["token_start"] : w["token_end"]])

    return card, witness_text
