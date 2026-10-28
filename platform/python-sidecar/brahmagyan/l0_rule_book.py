"""
brahmagyan.l0_rule_book — the L0 rule-book store (Rule Book engine, packet E2).

AUTHORITY: OWNER-APPROVAL-ENGINE-NATIVE-ITEMS-20261028 item (1): a new L0 asset
``bg_rule_book`` and its tables, locked and versioned, with the FROZEN
orchestrator contract unchanged (ENGINE_PLAN_v0_2 §1, §5; migration 1413).

What it does, in order (nothing is written unless every step passes):

1. Reads a committed version MANIFEST and the CARD FILE it names, and verifies
   the card file's bytes against ``card_file_sha256`` and every card against
   its ``card_sha256`` (canonical JSON, the compiler's own ``sha256_hex``).
2. Refuses a FIXTURE manifest unless the caller opts in (tests only).
3. Licence (M5, Q7): runs the compiler's ``lint_licence`` on every card as
   committed. Any quote text for an edition outside the public-domain
   allowlist refuses the WHOLE version — nothing is written.
4. Redaction map: verifies that every path the manifest says was redacted
   holds no quote text, and that an empty map means ratification_sha256 ==
   card_sha256 (nothing redacted → the stored card IS the ratified card).
5. Compiles every card with ``services.rulebook.compiler.compile_card`` and
   runs the compiler's lints. A ``build_fail`` lint (P4, testimony counting)
   refuses the version. A ``panel_return`` lint (vedha clause, frame) stores
   the card as ``quarantined_not_evaluable`` with the lint code as the reason:
   a card owed back to the panel is never counted.
6. Locks the version row, refuses a FROZEN version (the DB trigger refuses it
   too), then upserts the version and its cards ON CONFLICT DO UPDATE and
   replaces the version's class rows and drops cards no longer in the
   manifest — a rerun replaces, never accretes (§N.3).

L0 is chart-agnostic: no chart_id or birth data is read. The writer runs on
the caller's connection and never commits, rolls back or closes it.
"""
from __future__ import annotations

import copy
import hashlib
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from psycopg.types.json import Jsonb

from services.rulebook import constants as RC
from services.rulebook import schema as rb_schema
from services.rulebook.compiler import CompileResult, compile_card, sha256_hex
from services.rulebook.lints import BUILD_FAIL, PANEL_RETURN, lint_licence, run_lints

logger = logging.getLogger(__name__)

MANIFEST_SCHEMA = "rule-book-manifest-v1"
CARD_FILE_SCHEMA = "rule-book-card-file-v1"
DATA_DIR = Path(__file__).resolve().parent / "rule_book"
# The production source. Not committed yet: only the FIXTURE pair is.
DEFAULT_MANIFEST = DATA_DIR / "rule_book_manifest.json"
FIXTURE_MANIFEST = DATA_DIR / "FIXTURE_rule_book_manifest.json"
FIXTURE_PREFIX = "FIXTURE-"

STATUS_ACTIVE = "active"
STATUS_QUARANTINED = "quarantined_not_evaluable"
STATUS_WITHDRAWN = "withdrawn"
VERDICT_BY_PROVENANCE = {"verse_cited": "scored", "commentarial_practice": "testimony"}


# ── errors (each refuses the whole version; nothing is written) ────────────
class RuleBookError(RuntimeError):
    """Base: the rule-book source or target refuses this build."""


class RuleBookSourceError(RuleBookError):
    """Manifest / card file missing, malformed, or failing its hashes."""


class RuleBookLicenceRefused(RuleBookError):
    """A card carries quote text for an edition outside the public-domain allowlist."""


class RuleBookBuildLintRefused(RuleBookError):
    """A build_fail lint (P4, testimony counting) fired on a card."""


class RuleBookFrozenError(RuleBookError):
    """The target version is frozen; its rows can no longer change."""


# ── canonical redacted form ────────────────────────────────────────────────
def _resolve(card: Any, path: str) -> Any:
    """Resolve a JSON-pointer-like path ('/field1_citation', '/field6_exceptions/0/citation')."""
    node = card
    for part in [p for p in path.split("/") if p != ""]:
        if isinstance(node, list):
            node = node[int(part)]
        elif isinstance(node, Mapping):
            node = node[part]
        else:
            raise KeyError(path)
    return node


def _quote_mappings(obj: Any, path: str = "") -> List[Tuple[str, Mapping[str, Any]]]:
    out: List[Tuple[str, Mapping[str, Any]]] = []
    if isinstance(obj, Mapping):
        q = obj.get("quote")
        if isinstance(q, str) and q.strip():
            out.append((path or "/", obj))
        for k, v in obj.items():
            if k != "quote":
                out.extend(_quote_mappings(v, f"{path}/{k}"))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            out.extend(_quote_mappings(v, f"{path}/{i}"))
    return out


def redact_card(
    full_card: Mapping[str, Any], allowlist: Optional[Mapping[str, Any]] = None
) -> Tuple[Dict[str, Any], List[Dict[str, Any]], str]:
    """The canonical redacted form of a ratified card.

    Every quote the compiler's licence lint flags (an edition outside the
    public-domain allowlist, or no identifiable edition) is removed; its
    sha256 goes into the redaction map with the path it was removed from.
    Public-domain quotes stay. Returns (redacted_card, redaction_map,
    ratification_sha256), where ratification_sha256 is over the FULL card.

    Used where the full text exists (the owner's session at ratification);
    the committed file holds only the redacted form.
    """
    ratification_sha256 = sha256_hex(full_card)
    redacted = copy.deepcopy(dict(full_card))
    redaction_map: List[Dict[str, Any]] = []
    for path, mapping in _quote_mappings(redacted):
        probe = {"card_id": redacted.get("card_id"), "field1_citation": {}, "q": dict(mapping)}
        top = (redacted.get("field1_citation") or {}).get("text_id")
        if top and "text_id" not in mapping:
            probe["q"]["text_id"] = top
        if not lint_licence(probe, allowlist):
            continue  # public domain: the quote may stay
        quote = mapping["quote"]
        target = _resolve(redacted, path)
        del target["quote"]
        redaction_map.append(
            {
                "path": path,
                "quote_sha256": hashlib.sha256(quote.encode("utf-8")).hexdigest(),
                "text_id": mapping.get("text_id") or top,
            }
        )
    redaction_map.sort(key=lambda e: e["path"])
    return redacted, redaction_map, ratification_sha256


def restore_card(redacted: Mapping[str, Any], redaction_map: Sequence[Mapping[str, Any]], bank: Mapping[str, str]) -> Dict[str, Any]:
    """Re-insert redacted quotes from a local bank {quote_sha256: text}; raises if a text does not hash to its entry."""
    full = copy.deepcopy(dict(redacted))
    for entry in redaction_map:
        text = bank[entry["quote_sha256"]]
        if hashlib.sha256(text.encode("utf-8")).hexdigest() != entry["quote_sha256"]:
            raise RuleBookSourceError(f"bank text for {entry['path']} does not hash to its redaction entry")
        _resolve(full, entry["path"])["quote"] = text
    return full


# ── source loading and verification ────────────────────────────────────────
@dataclass
class CardRow:
    card_id: str
    card: Dict[str, Any]
    card_sha256: str
    ratification_sha256: str
    redaction_map: List[Dict[str, Any]]
    result: CompileResult
    status: str
    quarantine_reason: Optional[str]
    category: str
    polarity: str
    provenance: str
    verdict: str
    passage_ids: List[str]
    class_groups: List[str]


@dataclass
class RuleBookSource:
    manifest_path: Path
    manifest: Dict[str, Any]
    manifest_sha256: str
    card_file_sha256: str
    rulebook_version: str
    change_register_ids: List[str]
    is_fixture: bool
    rows: List[CardRow] = field(default_factory=list)


def _read_json(path: Path) -> Tuple[Any, bytes]:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise RuleBookSourceError(f"cannot read {path}: {exc}") from exc
    try:
        return json.loads(raw.decode("utf-8")), raw
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuleBookSourceError(f"{path} is not UTF-8 JSON: {exc}") from exc


def _quarantine_reason(result: CompileResult) -> str:
    parts = []
    for f in result.findings:
        oid = f"[{f.operand_id}]" if f.operand_id else ""
        parts.append(f"{f.reason.value}{oid}: {f.detail}")
    return " | ".join(parts) if parts else "compiler: not evaluable (no IR)"


def load_source(
    manifest_path: Path,
    *,
    allow_fixture: bool = False,
    allowlist: Optional[Mapping[str, Any]] = None,
) -> RuleBookSource:
    """Read, verify, licence-check and compile a version. Pure: touches no database."""
    manifest, _ = _read_json(manifest_path)
    if not isinstance(manifest, dict) or manifest.get("manifest_schema") != MANIFEST_SCHEMA:
        raise RuleBookSourceError(f"{manifest_path}: manifest_schema must be {MANIFEST_SCHEMA!r}")
    version = manifest.get("rulebook_version")
    if not isinstance(version, str) or not version:
        raise RuleBookSourceError("manifest has no rulebook_version")
    has_prefix = version.upper().startswith(FIXTURE_PREFIX)  # the DB check is case-insensitive too
    is_fixture = bool(manifest.get("fixture")) or has_prefix
    if is_fixture and not (version.startswith(FIXTURE_PREFIX) and manifest.get("fixture") is True):
        raise RuleBookSourceError(f"fixture manifest must set fixture=true AND a {FIXTURE_PREFIX!r} version (got {version!r})")
    if is_fixture and not allow_fixture:
        raise RuleBookSourceError(f"{version} is a FIXTURE; refused outside tests (allow_fixture is not set)")

    card_file = manifest_path.parent / str(manifest.get("card_file") or "")
    if card_file.parent != manifest_path.parent or not manifest.get("card_file"):
        raise RuleBookSourceError("card_file must name a file beside the manifest")
    card_doc, card_bytes = _read_json(card_file)
    card_file_sha256 = hashlib.sha256(card_bytes).hexdigest()
    if card_file_sha256 != manifest.get("card_file_sha256"):
        raise RuleBookSourceError(
            f"card file sha256 {card_file_sha256} != manifest card_file_sha256 {manifest.get('card_file_sha256')}"
        )
    if not isinstance(card_doc, dict) or card_doc.get("card_file_schema") != CARD_FILE_SCHEMA:
        raise RuleBookSourceError(f"{card_file}: card_file_schema must be {CARD_FILE_SCHEMA!r}")
    if card_doc.get("rulebook_version") != version:
        raise RuleBookSourceError("card file rulebook_version differs from the manifest")
    cards = card_doc.get("cards")
    entries = manifest.get("cards")
    if not isinstance(cards, list) or not isinstance(entries, list):
        raise RuleBookSourceError("cards must be lists in both files")

    by_id: Dict[str, Dict[str, Any]] = {}
    for c in cards:
        cid = c.get("card_id") if isinstance(c, dict) else None
        if not isinstance(cid, str) or not cid:
            raise RuleBookSourceError("a card has no card_id")
        if cid in by_id:
            raise RuleBookSourceError(f"duplicate card_id {cid} in the card file")
        by_id[cid] = c
    entry_ids = [e.get("card_id") for e in entries]
    if len(set(entry_ids)) != len(entry_ids) or set(entry_ids) != set(by_id):
        raise RuleBookSourceError("manifest cards and card-file cards are not the same set of unique card_ids")

    # licence first, over every card as committed: one breach refuses the version
    breaches = []
    for cid in sorted(by_id):
        for f in lint_licence(by_id[cid], allowlist):
            breaches.append(f"{cid}: {f.code}: {f.detail}")
    if breaches:
        raise RuleBookLicenceRefused("licence lint refused the version; nothing written:\n  " + "\n  ".join(breaches))

    src = RuleBookSource(
        manifest_path=manifest_path,
        manifest=manifest,
        manifest_sha256=sha256_hex(manifest),
        card_file_sha256=card_file_sha256,
        rulebook_version=version,
        change_register_ids=[str(x) for x in manifest.get("change_register_ids") or []],
        is_fixture=is_fixture,
    )
    build_fail: List[str] = []
    for entry in sorted(entries, key=lambda e: e["card_id"]):
        cid = entry["card_id"]
        card = by_id[cid]
        card_sha = sha256_hex(card)
        if card_sha != entry.get("card_sha256"):
            raise RuleBookSourceError(f"{cid}: card_sha256 {card_sha} != manifest {entry.get('card_sha256')}")
        rat_sha = entry.get("ratification_sha256")
        rmap = entry.get("redaction_map")
        if not isinstance(rmap, list) or not isinstance(rat_sha, str):
            raise RuleBookSourceError(f"{cid}: manifest entry needs ratification_sha256 and a redaction_map list")
        if not rmap and rat_sha != card_sha:
            raise RuleBookSourceError(f"{cid}: nothing redacted, so ratification_sha256 must equal card_sha256")
        if rmap and rat_sha == card_sha:
            raise RuleBookSourceError(f"{cid}: a redacted card cannot hash equal to its full ratified form")
        for e in rmap:
            try:
                target = _resolve(card, str(e["path"]))
            except (KeyError, IndexError, ValueError) as exc:
                raise RuleBookSourceError(f"{cid}: redaction path {e.get('path')!r} does not resolve") from exc
            if not isinstance(target, Mapping) or (isinstance(target.get("quote"), str) and target["quote"].strip()):
                raise RuleBookSourceError(f"{cid}: redaction path {e['path']} still carries quote text")
            if not isinstance(e.get("quote_sha256"), str) or len(e["quote_sha256"]) != 64:
                raise RuleBookSourceError(f"{cid}: redaction entry {e['path']} has no quote_sha256")

        result = compile_card(card)
        lints = run_lints(card, result, allowlist=allowlist)
        for lf in lints:
            if lf.severity == BUILD_FAIL:
                build_fail.append(f"{cid}: {lf.code}: {lf.detail}")
        panel = [lf for lf in lints if lf.severity == PANEL_RETURN]

        scope = card.get("field2_target_scope") or {}
        provenance = card.get("provenance")
        if provenance not in VERDICT_BY_PROVENANCE:
            raise RuleBookSourceError(f"{cid}: provenance {provenance!r} is not storable")
        if entry.get("verdict") is not None and entry["verdict"] != VERDICT_BY_PROVENANCE[provenance]:
            raise RuleBookSourceError(f"{cid}: manifest verdict {entry['verdict']!r} contradicts provenance {provenance!r}")
        groups = sorted(set(rb_schema.class_groups(card) or []))
        if not groups or not set(groups) <= set(RC.CLASS_GROUPS):
            raise RuleBookSourceError(f"{cid}: class groups {groups} not in the {len(RC.CLASS_GROUPS)} CLASS_GROUPS")

        if entry.get("status") == STATUS_WITHDRAWN:
            reason = str(entry.get("withdrawn_reason") or "").strip()
            if not reason:
                raise RuleBookSourceError(f"{cid}: a withdrawn card needs withdrawn_reason")
            status, why = STATUS_WITHDRAWN, f"withdrawn: {reason}"
        elif entry.get("status") not in (None, STATUS_ACTIVE):
            raise RuleBookSourceError(f"{cid}: manifest status {entry.get('status')!r} not allowed (only withdrawn may be declared)")
        elif result.status != STATUS_ACTIVE:
            status, why = STATUS_QUARANTINED, _quarantine_reason(result)
        elif panel:
            status = STATUS_QUARANTINED
            why = " | ".join(f"PANEL_RETURN:{lf.code}: {lf.detail}" for lf in panel)
        else:
            status, why = STATUS_ACTIVE, None

        src.rows.append(
            CardRow(
                card_id=cid,
                card=card,
                card_sha256=card_sha,
                ratification_sha256=rat_sha,
                redaction_map=list(rmap),
                result=result,
                status=status,
                quarantine_reason=why,
                category=scope.get("category"),
                polarity=card.get("polarity"),
                provenance=provenance,
                verdict=VERDICT_BY_PROVENANCE[provenance],
                passage_ids=list((card.get("field1_citation") or {}).get("passage_ids") or []),
                class_groups=groups,
            )
        )
    if build_fail:
        raise RuleBookBuildLintRefused("build_fail lint(s) refused the version; nothing written:\n  " + "\n  ".join(build_fail))
    return src


# ── database write (caller-owned connection; never commits) ────────────────
_UPSERT_VERSION = """
INSERT INTO l0_rule_book_versions
  (rulebook_version, manifest_sha256, card_file_sha256, card_count, change_register_ids, build_id)
VALUES (%(v)s, %(m)s, %(f)s, %(n)s, %(cr)s, %(b)s)
ON CONFLICT (rulebook_version) DO UPDATE SET
  manifest_sha256 = EXCLUDED.manifest_sha256,
  card_file_sha256 = EXCLUDED.card_file_sha256,
  card_count = EXCLUDED.card_count,
  change_register_ids = EXCLUDED.change_register_ids,
  build_id = EXCLUDED.build_id
WHERE l0_rule_book_versions.frozen_at IS NULL
"""

_UPSERT_CARD = """
INSERT INTO l0_rule_book_cards
  (rulebook_version, card_id, card_json, card_sha256, ratification_sha256, redaction_map_json,
   ir_json, ir_sha256, category, polarity, provenance, verdict, passage_ids, status, quarantine_reason, build_id)
VALUES (%(v)s, %(card_id)s, %(card_json)s, %(card_sha256)s, %(rat)s, %(rmap)s,
        %(ir_json)s, %(ir_sha256)s, %(category)s, %(polarity)s, %(provenance)s, %(verdict)s, %(passage_ids)s,
        %(status)s, %(reason)s, %(b)s)
ON CONFLICT (rulebook_version, card_id) DO UPDATE SET
  card_json = EXCLUDED.card_json, card_sha256 = EXCLUDED.card_sha256,
  ratification_sha256 = EXCLUDED.ratification_sha256, redaction_map_json = EXCLUDED.redaction_map_json,
  ir_json = EXCLUDED.ir_json, ir_sha256 = EXCLUDED.ir_sha256, category = EXCLUDED.category,
  polarity = EXCLUDED.polarity, provenance = EXCLUDED.provenance, verdict = EXCLUDED.verdict,
  passage_ids = EXCLUDED.passage_ids, status = EXCLUDED.status, quarantine_reason = EXCLUDED.quarantine_reason,
  build_id = EXCLUDED.build_id, written_at = now()
RETURNING (xmax = 0) AS inserted
"""


def write_source(conn: Any, src: RuleBookSource, *, build_id: Optional[str] = None, dry_run: bool = False) -> Dict[str, int]:
    """Upsert one verified version on ``conn``. Refuses a frozen version. Never commits."""
    counts = {"inserted": 0, "updated": 0, "deleted": 0, "class_rows": 0}
    with conn.cursor() as cur:
        cur.execute(
            "SELECT frozen_at FROM l0_rule_book_versions WHERE rulebook_version = %s FOR UPDATE",
            (src.rulebook_version,),
        )
        row = cur.fetchone()
        if row is not None and row[0] is not None:
            raise RuleBookFrozenError(
                f"rule-book version {src.rulebook_version} was frozen at {row[0]}; a frozen version is never rewritten "
                "(write a new version instead)"
            )
        if dry_run:
            counts["inserted"] = len(src.rows)
            return counts
        cur.execute(
            _UPSERT_VERSION,
            {
                "v": src.rulebook_version,
                "m": src.manifest_sha256,
                "f": src.card_file_sha256,
                "n": len(src.rows),
                "cr": src.change_register_ids,
                "b": build_id,
            },
        )
        if cur.rowcount != 1:
            raise RuleBookFrozenError(f"rule-book version {src.rulebook_version} could not be upserted (frozen concurrently?)")
        keep = [r.card_id for r in src.rows]
        cur.execute(
            "DELETE FROM l0_rule_book_card_classes WHERE rulebook_version = %s",
            (src.rulebook_version,),
        )
        cur.execute(
            "DELETE FROM l0_rule_book_cards WHERE rulebook_version = %s AND NOT (card_id = ANY(%s))",
            (src.rulebook_version, keep),
        )
        counts["deleted"] = cur.rowcount
        for r in src.rows:
            ir = r.result.ir
            cur.execute(
                _UPSERT_CARD,
                {
                    "v": src.rulebook_version,
                    "card_id": r.card_id,
                    "card_json": Jsonb(r.card),
                    "card_sha256": r.card_sha256,
                    "rat": r.ratification_sha256,
                    "rmap": Jsonb(r.redaction_map),
                    "ir_json": Jsonb(ir) if ir is not None else None,
                    "ir_sha256": r.result.ir_sha256 if ir is not None else None,
                    "category": r.category,
                    "polarity": r.polarity,
                    "provenance": r.provenance,
                    "verdict": r.verdict,
                    "passage_ids": r.passage_ids,
                    "status": r.status,
                    "reason": r.quarantine_reason,
                    "b": build_id,
                },
            )
            counts["inserted" if cur.fetchone()[0] else "updated"] += 1
            for g in r.class_groups:
                cur.execute(
                    "INSERT INTO l0_rule_book_card_classes (rulebook_version, card_id, class_group) VALUES (%s, %s, %s)",
                    (src.rulebook_version, r.card_id, g),
                )
                counts["class_rows"] += 1
    logger.info(
        "bg_rule_book %s: %d inserted, %d updated, %d dropped, %d class rows",
        src.rulebook_version, counts["inserted"], counts["updated"], counts["deleted"], counts["class_rows"],
    )
    return counts


def seed_rule_book(
    conn: Any,
    *,
    manifest_path: Optional[Path] = None,
    build_id: Optional[str] = None,
    dry_run: bool = False,
    allow_fixture: bool = False,
    allowlist: Optional[Mapping[str, Any]] = None,
) -> Tuple[RuleBookSource, Dict[str, int]]:
    path = Path(manifest_path) if manifest_path is not None else DEFAULT_MANIFEST
    if not path.exists():
        raise RuleBookSourceError(
            f"no rule-book manifest at {path}; only the FIXTURE pair is committed until a ratified version lands"
        )
    src = load_source(path, allow_fixture=allow_fixture, allowlist=allowlist)
    return src, write_source(conn, src, build_id=build_id, dry_run=dry_run)
