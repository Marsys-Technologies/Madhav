"""The ONE definition of the deterministic chart_vichara citation token (N-143 option B, SS 2026-10-05).

WHY. `chart_vichara.id` is a bigserial: a ga_vichara rebuild (DELETE + INSERT) renumbers every row, so an L2 row that
cites it dangles after the next L1 rebuild (and already dangles after S-L1). L2 therefore cites a DETERMINISTIC TOKEN
re-derivable by anyone from the vichara row itself, never a serialized row id (CLAUDE.md N.5, B.3).

THE TOKEN.  token = sha256(canonical JSON of the vichara natural key)[:16]   (16 hex chars, 64 bits)

The natural key is, in this fixed order (production is unique on exactly this: 7,774 rows = 7,774 distinct on the
canonical chart; `constituent_facts_array` is part of the key, so a row whose cited L1 facts change gets a NEW token):

    ayanamsha_id, vichara_family, subject, actor, target, domain, varga_id, varga,
    value_text, value_num, value_jsonb, constituent_facts_array

CANONICAL JSON (positional, compact, one fixed rule per field; the SQL resolver `public.chart_vichara_token` in
migration 1295 implements the SAME rules and is generated from `TOKEN_SQL_TEMPLATE` below):

    '[' + ',' .join(f_1 .. f_12) + ']'   encoded as UTF-8, no spaces between elements
    text fields   JSON string (escapes: \\" \\\\ \\b \\f \\n \\r \\t, other control characters < 0x20 as \\u00xx
                  lowercase hex, everything else raw, i.e. ensure_ascii=False); SQL NULL -> null
    value_num     the numeric with trailing fractional zeros removed (PostgreSQL trim_scale), written as a bare
                  JSON number, never through a float; SQL NULL -> null; NaN -> "NaN" (a string)
    value_jsonb   PostgreSQL's OWN canonical text of the jsonb value (`value_jsonb::text`; keys ordered by length then
                  bytes, ", " and ": " separators). The caller passes that text; this module never re-serializes
                  jsonb. SQL NULL -> null. (A JSON null scalar also renders as null: production has none; a test
                  pins it.)
    constituent_facts_array  JSON array of strings (compact, no spaces; a NULL element -> null); SQL NULL -> null; empty -> []

Floats are REFUSED for value_num: formatting a float is the canonicalization trap this definition exists to avoid.
Pass the numeric's text (`value_num::text`) or a Decimal.

Every L2 writer that CITES a chart_vichara row (bo_karanajala, bo_upaya; bo_yantra_mechanism carries the edges' tokens)
selects `VICHARA_KEY_SELECT_SQL` and calls `vichara_token_from_row`. A reader that only uses a row's values cites nothing and
needs neither.
"""
from __future__ import annotations

import hashlib
import json
import re
from decimal import Decimal
from typing import Any, Mapping, Sequence

TOKEN_HEX_CHARS = 16

#: Natural-key field order (the canonical JSON array order). One list, used by every function below.
VICHARA_KEY_FIELDS: tuple[str, ...] = (
    "ayanamsha_id", "vichara_family", "subject", "actor", "target", "domain", "varga_id", "varga",
    "value_text", "value_num", "value_jsonb", "constituent_facts_array",
)

#: The SELECT list every L2 reader of chart_vichara uses. Aliases are the row keys `vichara_token_from_row` reads;
#: numeric and jsonb arrive as their PostgreSQL text so nothing is re-rendered through float or a json round trip.
VICHARA_KEY_SELECT_SQL = (
    "ayanamsha_id, vichara_family, subject, actor, target, domain, varga_id, varga, value_text, "
    "value_num::text AS value_num_text, value_jsonb::text AS value_jsonb_text, constituent_facts_array"
)
_ROW_KEYS: tuple[str, ...] = (
    "ayanamsha_id", "vichara_family", "subject", "actor", "target", "domain", "varga_id", "varga",
    "value_text", "value_num_text", "value_jsonb_text", "constituent_facts_array",
)

#: The SQL expression of the SAME token over named inputs. Placeholders {ayanamsha_id} .. {constituent_facts_array}
#: are replaced by a parameter name (function body in migration 1295) or by a column reference (`v.col`, the inline
#: read-only measurement). One template, so the SQL and Python definitions cannot drift apart silently; a test
#: renders migration 1295's function from it and compares byte for byte.
TOKEN_SQL_TEMPLATE = """left(encode(sha256(convert_to(
    '[' || concat_ws(',',
      coalesce(to_json({ayanamsha_id})::text, 'null'),
      coalesce(to_json({vichara_family})::text, 'null'),
      coalesce(to_json({subject})::text, 'null'),
      coalesce(to_json({actor})::text, 'null'),
      coalesce(to_json({target})::text, 'null'),
      coalesce(to_json({domain})::text, 'null'),
      coalesce(to_json({varga_id})::text, 'null'),
      coalesce(to_json({varga})::text, 'null'),
      coalesce(to_json({value_text})::text, 'null'),
      CASE WHEN {value_num} IS NULL THEN 'null'
           WHEN {value_num} = 'NaN'::numeric THEN '"NaN"'
           ELSE trim_scale({value_num})::text END,
      coalesce({value_jsonb}::text, 'null'),
      coalesce(to_json({constituent_facts_array})::text, 'null')
    ) || ']', 'UTF8')), 'hex'), 16)"""


def token_sql(**names: str) -> str:
    """TOKEN_SQL_TEMPLATE with every field bound to `names[field]` (all twelve required)."""
    missing = [f for f in VICHARA_KEY_FIELDS if f not in names]
    if missing or len(names) != len(VICHARA_KEY_FIELDS):
        raise ValueError(f"token_sql needs exactly {VICHARA_KEY_FIELDS}; missing={missing}")
    return TOKEN_SQL_TEMPLATE.format(**names)


def token_sql_for_alias(alias: str) -> str:
    """The inline SQL expression of the token over a chart_vichara row aliased `alias` (read-only measurements)."""
    return token_sql(**{f: f"{alias}.{f}" for f in VICHARA_KEY_FIELDS})


def _json_text(value: str | None) -> str:
    if value is None:
        return "null"
    if not isinstance(value, str):
        raise TypeError(f"text field must be str or None, got {type(value).__name__}")
    return json.dumps(value, ensure_ascii=False)


def _num_text(value: Any) -> str:
    """trim_scale(value)::text for a numeric given as its text or a Decimal; never a float."""
    if value is None:
        return "null"
    if isinstance(value, bool) or isinstance(value, float):
        raise TypeError("value_num must be the numeric's text or a Decimal, never a float/bool "
                        "(float formatting is the canonicalization trap)")
    if isinstance(value, int):
        value = Decimal(value)
    if isinstance(value, str):
        value = Decimal(value)
    if not isinstance(value, Decimal):
        raise TypeError(f"value_num must be str/Decimal/int/None, got {type(value).__name__}")
    if value.is_nan():
        return '"NaN"'
    if not value.is_finite():
        raise ValueError("value_num is infinite; PostgreSQL numeric has no infinity")
    # Exact (no context rounding): render positionally, then strip trailing FRACTIONAL zeros only, which is
    # PostgreSQL's trim_scale()::text (100 stays 100; 1.50 -> 1.5; 0.00 -> 0).
    text = format(value, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    if text in ("-0", ""):
        text = "0"
    return text


def canonical_vichara_key_json(
    ayanamsha_id: str | None, vichara_family: str | None, subject: str | None,
    actor: str | None, target: str | None, domain: str | None,
    varga_id: str | None, varga: str | None, value_text: str | None,
    value_num: Any, value_jsonb_text: str | None,
    constituent_facts_array: Sequence[str] | None,
) -> str:
    """The canonical JSON of one vichara natural key (see the module docstring for the rules)."""
    if constituent_facts_array is None:
        facts = "null"
    else:
        if isinstance(constituent_facts_array, (str, bytes)):
            raise TypeError("constituent_facts_array must be a sequence of str, not a single string")
        if any(x is not None and not isinstance(x, str) for x in constituent_facts_array):
            raise TypeError("constituent_facts_array elements must be str (or None: a NULL element renders as null)")
        facts = json.dumps(list(constituent_facts_array), ensure_ascii=False, separators=(",", ":"))
    if value_jsonb_text is not None and not isinstance(value_jsonb_text, str):
        raise TypeError("value_jsonb_text must be the jsonb's PostgreSQL text (value_jsonb::text) or None")
    parts = [
        _json_text(ayanamsha_id), _json_text(vichara_family), _json_text(subject), _json_text(actor),
        _json_text(target), _json_text(domain), _json_text(varga_id), _json_text(varga), _json_text(value_text),
        _num_text(value_num),
        "null" if value_jsonb_text is None else value_jsonb_text,
        facts,
    ]
    return "[" + ",".join(parts) + "]"


def vichara_token(
    ayanamsha_id: str | None, vichara_family: str | None, subject: str | None,
    actor: str | None, target: str | None, domain: str | None,
    varga_id: str | None, varga: str | None, value_text: str | None,
    value_num: Any, value_jsonb_text: str | None,
    constituent_facts_array: Sequence[str] | None,
) -> str:
    """sha256(canonical JSON of the natural key)[:16]. See the module docstring."""
    canon = canonical_vichara_key_json(
        ayanamsha_id, vichara_family, subject, actor, target, domain, varga_id, varga, value_text,
        value_num, value_jsonb_text, constituent_facts_array,
    )
    return hashlib.sha256(canon.encode("utf-8")).hexdigest()[:TOKEN_HEX_CHARS]


_TOKEN_RE = re.compile(r"^[0-9a-f]{%d}$" % TOKEN_HEX_CHARS)


def is_vichara_token(value: Any) -> bool:
    """True for a well-formed token (16 lowercase hex chars). A bigserial id ('167204') is NOT one."""
    return isinstance(value, str) and _TOKEN_RE.match(value) is not None


def assert_vichara_tokens(values: Sequence[Any] | None, where: str = "") -> None:
    """Raise if any element of a constituent_ga_vichara_ids_array is not a vichara token (e.g. a serial id).

    A real detector for the claim 'this column holds deterministic tokens' (CLAUDE.md N.8): it can fail."""
    for v in values or []:
        if not is_vichara_token(v):
            raise ValueError(
                f"{where or 'vichara citation'}: {v!r} is not a vichara token "
                f"({TOKEN_HEX_CHARS} lowercase hex chars); a chart_vichara serial id must never be cited (N-143)"
            )


def vichara_token_from_row(row: Mapping[str, Any] | Sequence[Any]) -> str:
    """Token of a row selected with `VICHARA_KEY_SELECT_SQL` (dict row, or a sequence starting with those 12 columns)."""
    if isinstance(row, Mapping):
        try:
            vals = [row[k] for k in _ROW_KEYS]
        except KeyError as exc:
            raise KeyError(f"vichara row lacks {exc}; select VICHARA_KEY_SELECT_SQL") from exc
    else:
        if len(row) < len(_ROW_KEYS):
            raise ValueError(f"vichara row has {len(row)} columns; need the {len(_ROW_KEYS)} of VICHARA_KEY_SELECT_SQL first")
        vals = list(row[: len(_ROW_KEYS)])
    return vichara_token(*vals)
