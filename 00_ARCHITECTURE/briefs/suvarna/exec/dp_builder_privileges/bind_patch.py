"""B3 (migration number 1272): the text transformation of bind_l2_exact_inputs(uuid, jsonb). Pure: no database, no credential.

WHAT IT FIXES. bind_l2_exact_inputs() is SECURITY DEFINER (owner data_plane_l2_owner). It creates, with CREATE TEMP TABLE ... ON COMMIT DROP, one
`pg_temp` shadow per protected table (named like the table) holding only the rows of the exact input generations. The shadows therefore belong to
data_plane_l2_owner and carry no ACL, so the pipeline login data_plane_builder, whose writers read those names unqualified (pg_temp is searched
first), gets `permission denied for table chart_facts` on its first read. Reproduced on a disposable PostgreSQL 15 with the production schema, owners
and ACLs (BO_UUID_FIX_REPORT_2.md B3).

THE MINIMAL CORRECT CHANGE (one hunk). After both shadow loops, before the bind receipt is created: GRANT SELECT on every shadow THIS function created
(owned by the function owner; never a temp table the caller made) to data_plane_builder, the one login this function already requires
(session_user = 'data_plane_builder' is checked at its top). Not granted: the bind receipt (open_l2_data_plane_generation() trusts it only when it is
owned by the function owner; the builder has no reason to read it), any other role, any other privilege. Temp tables are
visible only through their session's pg_temp schema and drop at commit, so no other session or role gains access to anything.
"""
from __future__ import annotations

import difflib
import hashlib

HUNK_NAME = "B3_grant_select_on_shadows_to_the_builder"
HUNK_OLD = "  v_vector_digest := encode(digest(p_dependency_vector::text, 'sha256'), 'hex');\n  DROP TABLE IF EXISTS pg_temp.l2_data_plane_bind_receipt;"
HUNK_NEW = (
    "  -- 1272: the pipeline login must be able to READ the shadows this function creates (they are owned by the function owner and carry no ACL).\n"
    "  -- The grant goes to the one login this function already requires (session_user = data_plane_builder); other sessions cannot see these temp\n"
    "  -- tables and they drop at commit. The bind receipt is NOT granted.\n"
    "  FOR v_table IN\n"
    "    SELECT c.relname FROM pg_class c\n"
    "    WHERE c.relnamespace = pg_my_temp_schema() AND c.relkind = 'r'\n"
    "      AND pg_get_userbyid(c.relowner) = current_user\n"
    "      AND c.relname <> 'l2_data_plane_bind_receipt'\n"
    "    ORDER BY c.relname\n"
    "  LOOP\n"
    "    EXECUTE format('GRANT SELECT ON pg_temp.%I TO data_plane_builder', v_table);\n"
    "  END LOOP;\n"
    "  v_vector_digest := encode(digest(p_dependency_vector::text, 'sha256'), 'hex');\n"
    "  DROP TABLE IF EXISTS pg_temp.l2_data_plane_bind_receipt;"
)
BIND_HUNKS = ((HUNK_NAME, HUNK_OLD, HUNK_NEW),)


def apply_hunks(definition: str, hunks) -> str:
    """Replace each hunk's old text by its new text. Each old text must occur exactly once and its new text not at all."""
    out = definition
    for name, old, new in hunks:
        n = out.count(old)
        if n != 1:
            raise ValueError(f"hunk {name}: old text occurs {n} times (expected exactly 1)")
        if new in out:
            raise ValueError(f"hunk {name}: new text is already present (already patched?)")
        out = out.replace(old, new)
    return out


def unified_hunks(before: str, after: str) -> list[str]:
    """Zero-context unified diff of two function definitions, one string per hunk (header lines dropped)."""
    lines = list(difflib.unified_diff(before.splitlines(True), after.splitlines(True), fromfile="live", tofile="patched", n=0))
    hunks: list[list[str]] = []
    for ln in lines[2:]:
        if ln.startswith("@@"):
            hunks.append([])
        hunks[-1].append(ln if ln.endswith("\n") else ln + "\n")
    return ["".join(h) for h in hunks]


def diff_digest(before: str, after: str) -> str:
    return hashlib.sha256("".join(unified_hunks(before, after)).encode("utf-8")).hexdigest()
