# PASS fixture — uses the canonical dignity oracle import.
# No local DIGNITY_TABLE or if/elif dignity chain.

from brahmagyan.dignity_oracle import classify_dignity  # noqa: F401


def compute_dignity(graha: str, sign_idx: int, degree: float) -> str:
    return classify_dignity(graha, sign_idx, degree)
