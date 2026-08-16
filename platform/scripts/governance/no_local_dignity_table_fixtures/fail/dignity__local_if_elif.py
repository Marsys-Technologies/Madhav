# FAIL fixture — local if/elif dignity classification (ga_structural_writer pattern)
# Defect: dignity is computed inline with a local 4-way if/elif chain.
# Fix: import and call the shared oracle in brahmagyan/dignity_oracle.py.

EXALTATION_SIGNS = {"Sun": "Aries", "Moon": "Taurus", "Mars": "Capricorn"}
DEBILITATION_SIGNS = {"Sun": "Libra", "Moon": "Scorpio", "Mars": "Cancer"}
OWN_SIGNS = {"Sun": ["Leo"], "Moon": ["Cancer"], "Mars": ["Aries", "Scorpio"]}


def compute_dignity_inline(graha: str, sign: str) -> str:
    # BAD: file-local dignity classification — should use shared oracle
    if EXALTATION_SIGNS.get(graha) == sign:
        dignity = "exalted"
    elif DEBILITATION_SIGNS.get(graha) == sign:
        dignity = "debilitated"
    elif sign in OWN_SIGNS.get(graha, []):
        dignity = "own"
    else:
        dignity = "neutral"
    return dignity
