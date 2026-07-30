# FAIL fixture — the constant-FOLDED forms, not just the bare literals. Each
# expression below references no name, attribute, subscript or call, so its value
# is decided at edit time exactly as `True` would be. Wrapping an unearned green
# in an expression must not launder it past the lint.
# EXPECT-VIOLATIONS: 5
def scorecard():
    return {
        "views_verified": True and True,
        "reachability_pass": 0 == 0,
        "verification_pass_status": f"PASS",
        "coverage_ok": not False,
        "leak_count": 1 - 1,
    }
