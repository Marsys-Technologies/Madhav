# FAIL fixture — local DIGNITY_TABLE dict (ga_vargas_writer._compute_dignity pattern)
# Defect: file-local DIGNITY_TABLE mapping planet -> {exalt, debil, mt, own}.

DIGNITY_TABLE = {
    "Sun":     {"exalt": 0, "debil": 6,  "mt": 4,   "own": [4]},
    "Moon":    {"exalt": 1, "debil": 7,  "mt": None, "own": [3]},
    "Mars":    {"exalt": 9, "debil": 3,  "mt": 0,   "own": [0, 7]},
    "Mercury": {"exalt": 5, "debil": 11, "mt": 5,   "own": [2, 5]},
    "Jupiter": {"exalt": 3, "debil": 9,  "mt": 8,   "own": [8, 11]},
    "Venus":   {"exalt": 11, "debil": 5, "mt": 6,   "own": [1, 6]},
    "Saturn":  {"exalt": 6, "debil": 0,  "mt": 10,  "own": [9, 10]},
}


def _compute_dignity(body: str, sign_idx: int) -> str:
    if body not in DIGNITY_TABLE:
        return "Unknown"
    d = DIGNITY_TABLE[body]
    if sign_idx == d["exalt"]:
        return "Exalted"
    if sign_idx == d["debil"]:
        return "Debilitated"
    if d["mt"] is not None and sign_idx == d["mt"]:
        return "Moolatrikona"
    if sign_idx in d.get("own", []):
        return "Own"
    return "Neutral"
