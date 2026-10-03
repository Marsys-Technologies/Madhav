"""B3 (migration number 1272): the text transformation of bind_l2_exact_inputs(uuid, jsonb). Pure: no database, no credential.

WHAT IT FIXES. bind_l2_exact_inputs() is SECURITY DEFINER (owner data_plane_l2_owner). It creates, with CREATE TEMP TABLE ... ON COMMIT DROP, one
`pg_temp` shadow per protected table (named like the table) holding only the rows of the exact input generations. The shadows therefore belong to
data_plane_l2_owner and carry no ACL, so the pipeline login data_plane_builder, whose writers read those names unqualified (pg_temp is searched
first), gets `permission denied for table chart_facts` on its first read. Reproduced on a disposable PostgreSQL 15 with the production schema, owners
and ACLs (BO_UUID_FIX_REPORT_2.md B3).

THE MINIMAL CORRECT CHANGE (two hunks, one statement each). Immediately after each of the function's two CREATE TEMP TABLE loops creates a shadow, GRANT
SELECT on THAT shadow, BY NAME (the loop variable the function has just used to create it), to data_plane_builder, the one login this function already
requires (session_user = 'data_plane_builder' is checked at its top). Review LOW-4: the first draft granted on every temp table the function owner owned in
the session's temp schema; a pre-existing owner-owned temp table (for example l2_data_plane_msr_delete_receipt, created by assert_l2_msr_delete_safe) would
have been granted too. Granting by name right after each CREATE can only ever touch a table this very call created (the function DROPs any same-named temp
table first). Not granted: the bind receipt (open_l2_data_plane_generation() trusts it only when it is owned by the function owner; the builder has no reason
to read it), any other role, any other privilege. Temp tables are visible only through their session's pg_temp schema and drop at commit, so no other
session or role gains access to anything.
"""
from __future__ import annotations

import difflib
import hashlib

_GRANT = "EXECUTE format('GRANT SELECT ON pg_temp.%I TO data_plane_builder', v_table);\n"
HUNK_NAME_A = "B3_grant_select_on_each_l1_shadow_the_moment_it_is_created"
HUNK_OLD_A = "    END IF;\n  END LOOP;\n\n  FOR v_table IN\n    SELECT DISTINCT source_table"
HUNK_NEW_A = (
    "    END IF;\n"
    "    -- 1272: the pipeline login must be able to READ the shadow this loop pass has just created (owned by the function owner, no ACL).\n"
    "    -- Granted BY NAME, to the one login this function already requires (session_user = data_plane_builder); nothing pre-existing is touched.\n"
    "    " + _GRANT +
    "  END LOOP;\n\n  FOR v_table IN\n    SELECT DISTINCT source_table"
)
HUNK_NAME_B = "B3_grant_select_on_each_l2_shadow_the_moment_it_is_created"
HUNK_OLD_B = "    );\n  END LOOP;\n  v_vector_digest := encode(digest(p_dependency_vector::text, 'sha256'), 'hex');"
HUNK_NEW_B = (
    "    );\n"
    "    -- 1272: as above, for the L2 shadows. The bind receipt created below is NOT granted.\n"
    "    " + _GRANT +
    "  END LOOP;\n  v_vector_digest := encode(digest(p_dependency_vector::text, 'sha256'), 'hex');"
)
BIND_HUNKS = ((HUNK_NAME_A, HUNK_OLD_A, HUNK_NEW_A), (HUNK_NAME_B, HUNK_OLD_B, HUNK_NEW_B))


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
